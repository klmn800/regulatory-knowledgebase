"""
Claude Code Runner — Generic subprocess wrapper for Claude Code CLI.

Spawns Claude Code CLI sessions with a prompt, captures structured results
via a result file written by the session, and returns structured dicts.

Designed as reusable infrastructure: any agent or pipeline can use this
to route expensive LLM work through Claude Code (subscription) instead
of the API (per-token billing).

Usage:
    from tools.claude_code_runner import run_claude_task

    result = run_claude_task(
        prompt="Analyze this data and write JSON to {result_file}",
        result_file=Path("output/result.json"),
        timeout=600,
        log_dir=Path("output/sessions"),
        task_id="analysis_001",
    )
    if result["success"]:
        data = result["result"]  # Parsed JSON from result_file
"""

import json
import shutil
import subprocess
import time
from pathlib import Path


_claude_available = shutil.which("claude") is not None
if not _claude_available:
    import warnings
    warnings.warn(
        "Claude Code CLI ('claude') not found in PATH. "
        "run_claude_task() will fail. Install from https://claude.ai/code",
        stacklevel=2,
    )


def run_claude_task(
    prompt: str,
    result_file: Path,
    timeout: int = 1800,
    cwd: Path = None,
    log_dir: Path = None,
    task_id: str = None,
    windowed: bool = False,
    parse_json: bool = True,
) -> dict:
    """
    Run a task via Claude Code CLI and collect the result.

    The prompt should instruct the session to write its output to
    `result_file`. After the session completes, this function reads
    that file (as JSON if parse_json=True, as plain text otherwise).

    Args:
        prompt:      Full prompt text to send to Claude Code.
        result_file: Path where the session should write its JSON result.
        timeout:     Max seconds to wait for the session (default 1800 = 30 min).
        cwd:         Working directory for the subprocess (default: project root).
        log_dir:     Directory for prompt/session logs (default: no logging).
        task_id:     Identifier for log filenames (default: "task").
        windowed:    If True, open in a visible console window (Windows).
                     Session output streams to the window instead of being
                     captured. Useful for watching sessions in real time.

    Returns:
        dict with keys:
            result       — Parsed JSON from result_file, or None on failure.
            session_id   — Claude Code session UUID (piped mode only), or None.
            session_log  — Full stdout from the CLI session (empty in windowed mode).
            elapsed      — Wall-clock seconds.
            success      — True if result_file was written and parsed.
            error        — Error message string, or None on success.
    """
    if task_id is None:
        task_id = "task"

    result_file = Path(result_file)

    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = (log_dir or Path.cwd()) / f"prompt_{task_id}.txt"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt, encoding="utf-8")

    if cwd is None:
        cwd = Path(__file__).resolve().parents[1]

    start = time.time()

    if windowed:
        return _run_windowed(prompt_file, result_file, timeout, cwd,
                             log_dir, task_id, start, parse_json)
    else:
        return _run_piped(prompt, result_file, timeout, cwd,
                          log_dir, task_id, start, parse_json)


def _run_piped(prompt, result_file, timeout, cwd, log_dir, task_id, start,
               parse_json=True):
    """Run claude in pipe mode — stdout captured as JSON, not visible."""
    try:
        proc = subprocess.run(
            ["claude", "-p", "--output-format", "json",
             "--permission-mode", "auto"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            cwd=str(cwd),
        )
        raw_stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        # Parse JSON output to extract session_id and result text
        session_id = None
        session_log = raw_stdout
        try:
            cli_output = json.loads(raw_stdout)
            session_id = cli_output.get("session_id")
            session_log = cli_output.get("result", raw_stdout)
        except (json.JSONDecodeError, TypeError):
            pass  # Fall back to raw stdout

        if stderr:
            session_log += f"\n\n--- STDERR ---\n{stderr}"

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "result": None,
            "session_id": None,
            "session_log": "",
            "elapsed": elapsed,
            "success": False,
            "error": f"Timeout after {timeout}s",
        }

    except FileNotFoundError:
        elapsed = time.time() - start
        return {
            "result": None,
            "session_id": None,
            "session_log": "",
            "elapsed": elapsed,
            "success": False,
            "error": "Claude Code CLI ('claude') not found in PATH",
        }

    elapsed = time.time() - start

    if log_dir:
        session_file = log_dir / f"session_{task_id}.md"
        session_file.write_text(session_log, encoding="utf-8")

    result = _read_result(result_file, session_log, elapsed, parse_json)
    result["session_id"] = session_id
    return result


def _run_windowed(prompt_file, result_file, timeout, cwd, log_dir, task_id, start,
                  parse_json=True):
    """Run claude in a visible console window — user watches output live.

    Uses the same pattern as the proven autofix system: launches claude
    in interactive mode with @file prompt reference and cmd /k to keep
    the window open. Polls for the result file to detect completion.
    """
    prompt_path = str(prompt_file.resolve())
    bat_dir = log_dir or prompt_file.parent
    bat_file = bat_dir / f"run_{task_id}.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {cwd}\n'
        f'title Claude Code - {task_id}\n'
        f'start "" cmd /k "claude --permission-mode auto'
        f' @{prompt_path}"\n',
        encoding="utf-8",
    )

    try:
        subprocess.run([str(bat_file)], shell=True, cwd=str(cwd))
    except Exception as e:
        elapsed = time.time() - start
        return {
            "result": None,
            "session_id": None,
            "session_log": "",
            "elapsed": elapsed,
            "success": False,
            "error": f"Could not launch batch file: {e}",
        }

    deadline = start + timeout
    poll_interval = 5

    while time.time() < deadline:
        if result_file.exists():
            time.sleep(2)
            break
        time.sleep(poll_interval)
    else:
        elapsed = time.time() - start
        return {
            "result": None,
            "session_id": None,
            "session_log": "(windowed mode — output was in console window)",
            "elapsed": elapsed,
            "success": False,
            "error": f"Timeout after {timeout}s",
        }

    elapsed = time.time() - start
    result = _read_result(
        result_file,
        "(windowed mode — output was in console window)",
        elapsed,
        parse_json,
    )
    result["session_id"] = None  # Not available in windowed mode
    return result


def _read_result(result_file, session_log, elapsed, parse_json=True):
    """Read and parse the result file. Shared by both modes."""
    if not result_file.exists():
        return {
            "result": None,
            "session_log": session_log,
            "elapsed": elapsed,
            "success": False,
            "error": f"Result file not created: {result_file}",
        }

    raw = result_file.read_text(encoding="utf-8")

    if not parse_json:
        return {
            "result": raw,
            "session_log": session_log,
            "elapsed": elapsed,
            "success": True,
            "error": None,
        }

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "result": None,
            "session_log": session_log,
            "elapsed": elapsed,
            "success": False,
            "error": f"Invalid JSON in result file: {e}",
        }

    return {
        "result": parsed,
        "session_log": session_log,
        "elapsed": elapsed,
        "success": True,
        "error": None,
    }
