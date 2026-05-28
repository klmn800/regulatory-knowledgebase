"""
OLG Authoring — Research engine that runs via Claude Code CLI.

Alternative to the API-based research path in author.run_research() (which
uses tools/synthesis.py's deep agentic loop). Same role, different engine.

Why Claude Code:
- Subscription-billed (no per-token cost when on Claude Pro/Max).
- Session is resumable: the user can push back on findings, request
  additional searches, or expand sections via `claude --resume <UUID>`,
  and the agent overwrites report.md in place.
- Windowed terminal lets the user watch the agent work.

The agent runs `python rag/query.py ... --json` for retrieval. Raw search
outputs are captured to <version_dir>/searches/NNN_<source>_<slug>.json
as they happen; evidence.json is assembled mechanically from those files
at the end. This decouples raw evidence (mechanical) from the narrative
report (LLM).

Unlike the API path, this function does NOT block. It writes the
artifacts the UI needs to detect "in progress" (session_id.txt,
meta.json with status=in_progress), spawns the windowed Claude Code
session, and returns immediately. The UI re-renders the panel on
subsequent loads to detect completion via file presence.
"""

import configparser
import json
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DATA_DIR = PROJECT_ROOT / "output" / "author"
SHARED_PROMPTS_DIR = PROJECT_ROOT / "prompts"

sys.path.insert(0, str(PROJECT_ROOT))

from tools.claude_code_runner import run_claude_task


PROMPT_TEMPLATE_PATH = PROMPTS_DIR / "author_research_claude_code.md"
DOMAIN_PREAMBLE_PATH = SHARED_PROMPTS_DIR / "domain_preamble.md"


def _build_prompt(
    assignment: str,
    task_instructions: str,
    version_dir: Path,
    max_searches: int,
) -> str:
    """Render the research prompt with placeholders interpolated.

    Uses .replace() (not .format()) because the template contains literal
    `{` / `}` in JSON examples and bash snippets that .format() would
    misparse.
    """
    template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    domain_preamble = (
        DOMAIN_PREAMBLE_PATH.read_text(encoding="utf-8")
        if DOMAIN_PREAMBLE_PATH.exists()
        else ""
    )

    if task_instructions.strip():
        composed_assignment = (
            f"{assignment}\n\n---\n\n"
            f"Research focus for this run:\n{task_instructions}"
        )
    else:
        composed_assignment = assignment

    body = (
        template
        .replace("{assignment}", composed_assignment)
        .replace("{version_dir}", str(version_dir.resolve()))
        .replace("{max_searches}", str(max_searches))
    )

    if domain_preamble:
        return f"{domain_preamble}\n\n---\n\n{body}"
    return body


def _olg_programs_env(programs_by_source: dict | None) -> dict[str, str]:
    """Build the env dict to inject the OLG program whitelist into the
    spawned subprocess. Returns empty dict when no OLG filter was set.

    The agent shells out to `python rag/query.py --source olg` from
    inside the loop; only env-var enforcement is durable because the
    env var is read in the subprocess at import time (agent can't
    override). See rag/query.py:OLG_PROGRAMS_WHITELIST."""
    olg_programs = (programs_by_source or {}).get("olg")
    if not olg_programs:
        return {}
    return {"OLG_PROGRAMS": ",".join(olg_programs)}


def run_research_claude_code(
    assignment: str,
    task_instructions: str,
    version_dir: Path,
    config: configparser.ConfigParser,
    sources: list[str] | None = None,
    programs_by_source: dict[str, list[str]] | None = None,
) -> dict:
    """Spawn a windowed Claude Code session for the research phase.

    Writes meta.json + session_id.txt + prompt.md + full_prompt.md to
    version_dir BEFORE spawning, so Resume works even if the agent
    window is closed without writing report.md.

    Returns a status dict (not SynthesisResult — that's the API path's
    return type). The UI keys off file presence in version_dir to
    detect completion.

    Args:
        assignment:        The assignment text (stable project description).
        task_instructions: User's per-run focus / constraints (may be empty).
        version_dir:       Where the agent should write report.md,
                           evidence.json, and the searches/ subdir.
        config:            App configuration.
        sources:           Which sources to search (default all four). The
                           prompt names all four explicitly; this is mostly
                           informational for the meta record.
        programs_by_source: Per-source program whitelist (e.g.
                           {"olg": ["SNAP", "Cross-Program"]}). Only OLG
                           is enforced today via the OLG_PROGRAMS env var
                           the spawned subprocess reads at import. Other
                           sources are informational in meta.json.
    """
    if sources is None:
        sources = ["olg", "cmr", "fns", "cfr"]

    max_searches = config.getint("author", "research_max_searches", fallback=12)
    cc_model = config.get(
        "author", "research_cc_model", fallback="claude-sonnet-4-6"
    ).strip()

    # output/author/{name}/research/NNN_timestamp/ → name is parents[1].name
    name = version_dir.parent.parent.name

    full_prompt = _build_prompt(
        assignment=assignment,
        task_instructions=task_instructions,
        version_dir=version_dir,
        max_searches=max_searches,
    )

    session_id = str(uuid.uuid4())

    # Pre-spawn writes: everything the UI needs to recognize an in-progress
    # or interrupted run lives in version_dir before Claude Code launches.
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "session_id.txt").write_text(session_id, encoding="utf-8")
    (version_dir / "prompt.md").write_text(task_instructions, encoding="utf-8")
    (version_dir / "full_prompt.md").write_text(full_prompt, encoding="utf-8")
    (version_dir / "searches").mkdir(exist_ok=True)

    # full_prompt.md is the file the agent reads from (per-run path —
    # no shared scratch file at DATA_DIR/.research_prompt.md anymore).
    prompt_path = (version_dir / "full_prompt.md").resolve()
    initial_msg = (
        f"Your research task is in {prompt_path} — it has the assignment, "
        f"output paths, search-tool instructions, and search budget. "
        f"Read it and take it from there."
    )

    meta = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "engine": "claude-code",
        "model": cc_model or "(CC default)",
        "sources": sources,
        "session_id": session_id,
        "max_searches": max_searches,
        "status": "in_progress",
        "programs_by_source": programs_by_source or {},
    }
    (version_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    run_claude_task(
        result_file=version_dir / "report.md",
        cwd=PROJECT_ROOT,
        log_dir=version_dir,
        task_id=f"research_{name}",
        windowed=True,
        wait_for_result=False,
        model=cc_model or None,
        session_id=session_id,
        initial_msg=initial_msg,
        title=f"Claude Code Research - {name}",
        env=_olg_programs_env(programs_by_source),
    )

    return {
        "status": "spawned",
        "engine": "claude-code",
        "session_id": session_id,
        "version_dir": str(version_dir),
        "model": cc_model or "(CC default)",
        "max_searches": max_searches,
    }


def launch_research_resume(
    session_id: str,
    name: str,
    version_dir: Path | None = None,
    programs_by_source: dict[str, list[str]] | None = None,
) -> None:
    """Launch a Claude Code resume terminal for a research session.

    Re-applies OLG_PROGRAMS env var so the agent's tool calls in the
    resumed session remain bound by the original filter. If
    programs_by_source isn't passed, falls back to meta.json in
    version_dir (so callers without it still get correct enforcement).

    Note: --model is intentionally NOT passed on resume. The CLI inherits
    the model from the original session. If that turns out to be wrong
    in practice, add it here.
    """
    if programs_by_source is None and version_dir is not None:
        meta_file = version_dir / "meta.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                programs_by_source = meta.get("programs_by_source") or None
            except (json.JSONDecodeError, OSError):
                programs_by_source = None

    log_dir = version_dir if version_dir is not None else DATA_DIR
    run_claude_task(
        cwd=PROJECT_ROOT,
        log_dir=log_dir,
        task_id=f"research_resume_{name}",
        windowed=True,
        resume=True,
        session_id=session_id,
        title=f"Claude Code Research Resume - {name}",
        env=_olg_programs_env(programs_by_source),
    )
