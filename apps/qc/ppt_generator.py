"""
QC PPT generator — orchestration for the PPT presentation arc.

Reads a completed QC analysis, builds the inputs.json contract specified in
apps/qc/prompts/ppt_outline.md, spawns a windowed Claude Code session
that writes outline.json, and (lazily, on demand) formats the outline into
output.pptx via tools/pptx_writer.py.

Design notes:
  - Spawning is non-blocking: returns immediately after launching the Windows
    console. The user watches Claude Code work in the spawned terminal.
  - Formatting is idempotent + lazy: every panel reload calls
    ensure_pptx_built() on each run dir. If outline.json appeared since the
    last reload, it gets validated + formatted in place. Validation errors
    are written to metadata.json so the UI can surface them.
  - PII discipline: review_number, apid, tao, finding_narrative, and
    non_concur_reason are stripped from selected_findings before inputs.json
    is handed to Claude Code. The abstracted policy_issues field is kept
    (the LLM needs the substance).
  - Windowed launch matches apps/author/author.py — pre-generate a
    session UUID, write a .bat file, subprocess.Popen with CREATE_NEW_CONSOLE.

Layout:
  output/qc_analysis/{name_ts}/ppt/
    inputs.json                  ← copy of latest successful run
    outline.json                 ← copy of latest successful run
    output.pptx                  ← copy of latest successful run
    session_id.txt               ← copy of latest successful run
    runs/
      001_<timestamp>/
        inputs.json              ← written by orchestrator
        outline.json             ← written by Claude Code
        output.pptx              ← built by ensure_pptx_built()
        session_id.txt
        metadata.json            ← format_status, format_error, etc.
        kickoff_prompt.md        ← debug copy of the launch message
        .run_new.bat             ← launch script (debug)
"""

import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from apps.qc.qc_analyzer import (
    flatten_findings,
    load_all_findings,
    find_recurring_gaps,
)
from tools.pptx_writer import generate_pptx, validate_outline


PPT_PROMPT_PATH = PROJECT_ROOT / "apps" / "qc" / "prompts" / "ppt_outline.md"

# Stripped from each finding before inputs.json is handed to Claude Code.
# Limited to actual PII / PII-adjacent identifiers — case categorizations
# (error_type, determination) stay in so the LLM can use them for framing
# (e.g., "decks grouped by error_type").
_PII_FIELDS = (
    "review_number", "apid", "tao",
    "finding_narrative", "non_concur_reason",
)

# Bulky/redundant fields the LLM doesn't need on top of the per-row JSONs
# it can open directly. Trimming keeps inputs.json small.
_TRIM_FIELDS = (
    "judge_trace", "all_search_queries", "search_queries", "searches_performed",
)

_TS_SUFFIX_RE = re.compile(r"_(\d{4}-\d{2}-\d{2}_\d{4})$")


def _split_analysis_name(dirname: str) -> tuple[str, str]:
    """'Oct-2025-QC-Report_2026-05-07_1428' → ('Oct-2025-QC-Report', '2026-05-07_1428')."""
    m = _TS_SUFFIX_RE.search(dirname)
    if not m:
        return (dirname, "")
    return (dirname[:m.start()], m.group(1))


# ============================================================
# Inputs construction
# ============================================================

def build_inputs_json(
    analysis_dir: Path,
    classifications: list[str],
    instructions: str,
    filter_state: dict | None = None,
) -> dict:
    """Build the inputs.json contents matching the ppt_outline.md contract.

    Args:
        analysis_dir: Path to output/qc_analysis/{name_ts}/.
        classifications: Coverage values to include
            (subset of {"Gap", "Partial", "Adequate"}).
        instructions: Free-text framing from the user (may be empty).
        filter_state: Pre-computed include_* flags. Derived from
            `classifications` when omitted.
    """
    rows = load_all_findings(analysis_dir)
    flat = flatten_findings(rows) if rows else []
    cls_set = set(classifications or [])
    selected = [f for f in flat if f.get("coverage") in cls_set]

    cleaned = []
    for f in selected:
        entry = {k: v for k, v in f.items()
                 if k not in _PII_FIELDS and k not in _TRIM_FIELDS}
        cleaned.append(entry)

    if filter_state is None:
        filter_state = {
            "include_gap": "Gap" in cls_set,
            "include_partial": "Partial" in cls_set,
            "include_adequate": "Adequate" in cls_set,
        }

    name, ts = _split_analysis_name(analysis_dir.name)

    return {
        "analysis_name": name,
        "analysis_timestamp": ts,
        "selected_findings": cleaned,
        "instructions": (instructions or "").strip(),
        "filter_state": filter_state,
        "recurring_gaps": find_recurring_gaps(flat),
    }


# ============================================================
# Run-dir creation + latest-pointer promotion
# ============================================================

def _ppt_dir(analysis_dir: Path) -> Path:
    return analysis_dir / "ppt"


def _runs_dir(analysis_dir: Path) -> Path:
    return _ppt_dir(analysis_dir) / "runs"


def _next_run_dir(analysis_dir: Path) -> Path:
    runs = _runs_dir(analysis_dir)
    runs.mkdir(parents=True, exist_ok=True)

    nums = []
    for d in runs.iterdir():
        if not d.is_dir():
            continue
        try:
            nums.append(int(d.name.split("_", 1)[0]))
        except (ValueError, IndexError):
            continue
    next_num = (max(nums) if nums else 0) + 1
    timestamp = time.strftime("%Y%m%d-%H%M")
    run_dir = runs / f"{next_num:03d}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _find_run_dir(analysis_dir: Path, version_num: int) -> Path | None:
    runs = _runs_dir(analysis_dir)
    if not runs.exists():
        return None
    for d in sorted(runs.iterdir()):
        if not d.is_dir():
            continue
        try:
            if int(d.name.split("_", 1)[0]) == version_num:
                return d
        except (ValueError, IndexError):
            continue
    return None


def _promote_to_latest(run_dir: Path) -> None:
    """Copy a run's artifacts to ppt/ top-level (latest pointers)."""
    ppt_dir = run_dir.parent.parent  # runs/NNN_ts → runs → ppt
    ppt_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("inputs.json", "outline.json", "output.pptx", "session_id.txt"):
        src = run_dir / fname
        if src.exists():
            shutil.copy2(src, ppt_dir / fname)


# ============================================================
# Metadata helpers
# ============================================================

def _read_metadata(run_dir: Path) -> dict:
    f = run_dir / "metadata.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_metadata(run_dir: Path, meta: dict) -> None:
    (run_dir / "metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8",
    )


def read_metadata(run_dir: Path) -> dict:
    """Public read accessor — used by the UI panel context builder."""
    return _read_metadata(run_dir)


# ============================================================
# Format step (idempotent, lazy)
# ============================================================

def ensure_pptx_built(run_dir: Path) -> dict:
    """Validate outline.json + format to output.pptx if not already built
    (or if outline.json has been rewritten since the last build).

    Idempotent — safe to call on every panel load. Re-runs the format step
    when outline.json is newer than output.pptx, which covers both Resume
    (Claude Code rewrites outline) and direct on-disk edits to outline.json.

    Returns dict:
      {"status": "not_ready" | "already_built" | "built"
                 | "invalid_outline" | "format_error",
       "error": str | None, "warnings": list[str]}
    """
    outline_file = run_dir / "outline.json"
    pptx_file = run_dir / "output.pptx"

    if not outline_file.exists():
        return {"status": "not_ready", "error": None, "warnings": []}
    if pptx_file.exists() and pptx_file.stat().st_mtime >= outline_file.stat().st_mtime:
        return {"status": "already_built", "error": None, "warnings": []}

    try:
        outline = json.loads(outline_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return _record_format_error(run_dir, "invalid_outline",
                                    f"Could not parse outline.json: {e}")

    warnings = validate_outline(outline)
    errors = [w for w in warnings if (
        "missing" in w.lower() or "invalid" in w.lower() or "must be" in w.lower()
    )]
    if errors:
        return _record_format_error(
            run_dir, "invalid_outline",
            "outline.json failed validation:\n" + "\n".join(f"  - {e}" for e in errors),
            warnings=warnings,
        )

    try:
        generate_pptx(outline, pptx_file)
    except Exception as e:
        return _record_format_error(run_dir, "format_error",
                                    f"generate_pptx() failed: {e}",
                                    warnings=warnings)

    meta = _read_metadata(run_dir)
    meta["format_status"] = "built"
    meta["format_warnings"] = warnings
    meta["format_error"] = None
    meta["formatted_at"] = datetime.now().isoformat(timespec="seconds")
    _write_metadata(run_dir, meta)

    _promote_to_latest(run_dir)

    return {"status": "built", "error": None, "warnings": warnings}


def _record_format_error(run_dir: Path, status: str, message: str,
                          warnings: list | None = None) -> dict:
    meta = _read_metadata(run_dir)
    meta["format_status"] = status
    meta["format_error"] = message
    if warnings is not None:
        meta["format_warnings"] = warnings
    _write_metadata(run_dir, meta)
    return {"status": status, "error": message, "warnings": warnings or []}


# ============================================================
# Spawn helpers
# ============================================================

def _build_kickoff_message(inputs_path: Path, outline_path: Path,
                            analysis_dir: Path) -> str:
    """Single-line initial message handed to Claude Code. Points at the
    system prompt, the run inputs, the analysis dir (for per-row JSONs),
    and the output target."""
    return (
        f"Read your full instructions in {PPT_PROMPT_PATH}. "
        f"Then read the run inputs at {inputs_path} for the selected findings "
        f"and user instructions, open per-row JSONs under "
        f"{analysis_dir / 'results'} for any extra detail you need (judge_trace, "
        f"full narrative, etc), and write the slide outline as JSON to "
        f"{outline_path}. Validate before exiting with: "
        f"python tools/pptx_writer.py --validate {outline_path}"
    )


def _launch_windowed(run_dir: Path, session_id: str, kickoff_msg: str,
                      analysis_name: str, mode: str) -> None:
    """Spawn Claude Code in a visible Windows console.

    `mode` controls the Claude Code flag:
      - 'new'    → claude --session-id <uuid> "<kickoff>"
      - 'resume' → claude --resume <session_id>
    """
    bat_file = run_dir / f".run_{mode}.bat"
    if mode == "resume":
        cmd_line = f"claude --permission-mode auto --resume {session_id}"
        title = f"Claude Code Resume - QC PPT - {analysis_name}"
    else:
        # cmd.exe escapes a literal " inside a quoted argument as "" — the
        # message is wrapped in double quotes for the claude --session-id
        # invocation, so any embedded " has to be doubled.
        msg = kickoff_msg.replace('"', '""')
        cmd_line = f'claude --permission-mode auto --session-id {session_id} "{msg}"'
        title = f"Claude Code - QC PPT - {analysis_name}"

    bat_file.write_text(
        f"@echo off\n"
        f"cd /d {PROJECT_ROOT}\n"
        f"title {title}\n"
        f"echo.\n"
        f"echo  QC PPT Generation: {analysis_name}\n"
        f"echo  Run dir: {run_dir}\n"
        f"echo  Session ID: {session_id}\n"
        f"echo.\n"
        f"{cmd_line}\n"
        f"echo.\n"
        f"echo  === Session complete - return to the browser and reload the PPT panel ===\n"
        f"echo.\n"
        f"pause\n",
        encoding="utf-8",
    )

    subprocess.Popen(
        ["cmd", "/c", str(bat_file)],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


# ============================================================
# Public API
# ============================================================

def generate_ppt(
    analysis_dir: Path,
    classifications: list[str],
    instructions: str,
    filter_state: dict | None = None,
) -> dict:
    """Create a new versioned run, write inputs.json, spawn windowed
    Claude Code session.

    Returns immediately. The caller (UI) shows "running" until the user
    reloads the panel; ensure_pptx_built() then validates + formats
    outline.json → output.pptx automatically.

    Returns: {"run_dir", "version_num", "session_id"}.
    """
    inputs = build_inputs_json(analysis_dir, classifications, instructions,
                                filter_state)

    run_dir = _next_run_dir(analysis_dir)
    version_num = int(run_dir.name.split("_", 1)[0])

    inputs_path = run_dir / "inputs.json"
    outline_path = run_dir / "outline.json"

    inputs_path.write_text(
        json.dumps(inputs, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    session_id = str(uuid.uuid4())
    (run_dir / "session_id.txt").write_text(session_id, encoding="utf-8")

    kickoff_msg = _build_kickoff_message(inputs_path, outline_path, analysis_dir)
    (run_dir / "kickoff_prompt.md").write_text(kickoff_msg, encoding="utf-8")

    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session_id": session_id,
        "classifications_included": list(classifications),
        "selected_count": len(inputs["selected_findings"]),
        "instructions": inputs["instructions"],
        "source_analysis": analysis_dir.name,
        "format_status": "pending",
        "format_error": None,
    }
    _write_metadata(run_dir, meta)

    _launch_windowed(run_dir, session_id, kickoff_msg, analysis_dir.name,
                      mode="new")

    return {
        "run_dir": run_dir,
        "version_num": version_num,
        "session_id": session_id,
    }


def resume_ppt(analysis_dir: Path, version_num: int) -> dict:
    """Re-launch a windowed Claude Code session with --resume <session_id>."""
    target = _find_run_dir(analysis_dir, version_num)
    if target is None:
        raise FileNotFoundError(f"PPT run version {version_num} not found")

    sid_file = target / "session_id.txt"
    if not sid_file.exists():
        raise FileNotFoundError(f"No session_id.txt in {target}")
    session_id = sid_file.read_text(encoding="utf-8").strip()

    _launch_windowed(target, session_id, "", analysis_dir.name, mode="resume")
    return {"run_dir": target, "version_num": version_num,
            "session_id": session_id}


def run_ppt_again(analysis_dir: Path, version_num: int) -> dict:
    """Clone a prior run's inputs (classifications + instructions) into a
    new versioned run dir and spawn a fresh Claude Code session.

    Per the author tab pattern: Run Again creates a NEW version, never
    overwrites. The new run has its own session UUID."""
    src = _find_run_dir(analysis_dir, version_num)
    if src is None:
        raise FileNotFoundError(f"PPT run version {version_num} not found")

    src_inputs_file = src / "inputs.json"
    if not src_inputs_file.exists():
        raise FileNotFoundError(f"No inputs.json in {src}")
    src_inputs = json.loads(src_inputs_file.read_text(encoding="utf-8"))

    fs = src_inputs.get("filter_state", {}) or {}
    classifications = []
    if fs.get("include_gap"):
        classifications.append("Gap")
    if fs.get("include_partial"):
        classifications.append("Partial")
    if fs.get("include_adequate"):
        classifications.append("Adequate")

    return generate_ppt(
        analysis_dir,
        classifications=classifications,
        instructions=src_inputs.get("instructions", ""),
        filter_state=fs,
    )
