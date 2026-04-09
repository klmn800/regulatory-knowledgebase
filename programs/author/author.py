"""
OLG Policy Authoring Agent — research, draft, and format OLG pages.

Three independent tools:
  1. Research: Multi-source RAG synthesis with structured evidence output
  2. Draft:   Claude Code CLI drafts OLG-voice content (session resumable)
  3. Format:  Draft markdown → styled .docx via OLG template

Each function takes explicit paths — no implicit "latest" or top-level copies.

Usage:
    python programs/author/author.py "Consolidate VC-1 scripts" --name vc1_scripts
    python programs/author/author.py "Find VC-1 scripts" --name vc1_scripts --research-only
    python programs/author/author.py --name vc1_scripts --draft-only
    python programs/author/author.py --name vc1_scripts --resume
"""

import argparse
import configparser
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
REFERENCES_DIR = Path(__file__).resolve().parent / "references"
DATA_DIR = PROJECT_ROOT / "output" / "author"
SHARED_PROMPTS_DIR = PROJECT_ROOT / "prompts"
CONFIG_FILE = PROJECT_ROOT / "config.ini"

sys.path.insert(0, str(PROJECT_ROOT))
from tools.synthesis import run_synthesis, SynthesisResult


# ============================================================
# CONFIGURATION
# ============================================================

def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_text(filepath: Path) -> str | None:
    """Load a text file, returning None if it doesn't exist."""
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return None


def get_default_research_prompt() -> str:
    """Return the default research prompt text."""
    return load_text(SHARED_PROMPTS_DIR / "author_research.md") or ""


def get_default_draft_prompt() -> str:
    """Return the default draft prompt text (just the instructions part)."""
    return load_text(PROMPTS_DIR / "author_draft.md") or ""


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

def get_output_dir(name: str) -> Path:
    """Get or create the output directory for an assignment."""
    output_dir = DATA_DIR / name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# ============================================================
# PHASE 1: RESEARCH
# ============================================================

def run_research(
    assignment: str,
    prompt_text: str,
    version_dir: Path,
    config: configparser.ConfigParser,
) -> SynthesisResult:
    """Run the research phase — deep RAG synthesis with structured output.

    Args:
        assignment: The assignment text.
        prompt_text: The research prompt instructions to use.
        version_dir: Where to write all outputs (report.md, evidence.json, meta.json, prompt.md).
        config: App configuration.
    """
    model = config.get("author", "research_model",
                        fallback="claude-sonnet-4-5-20250929")
    max_searches = config.getint("author", "research_max_searches", fallback=12)
    results_per_search = config.getint("author", "research_results_per_search",
                                        fallback=8)
    max_tokens = config.getint("author", "research_max_tokens", fallback=4096)

    sources = ["olg", "cmr", "fns"]

    print(f"\n{'='*60}")
    print("PHASE 1: RESEARCH")
    print(f"{'='*60}")
    print(f"  Assignment: {assignment[:100]}{'...' if len(assignment) > 100 else ''}")
    print(f"  Sources: {', '.join(sources)}")
    print(f"  Model: {model}")
    print(f"  Search budget: {max_searches}")
    print(f"  Output: {version_dir}")
    print()

    result = run_synthesis(
        question=assignment,
        sources=sources,
        deep=True,
        max_searches=max_searches,
        prompt_name="author_research",
        config_overrides={
            "model": model,
            "max_tokens": max_tokens,
            "results_per_search": results_per_search,
        },
    )

    # Save prompt used
    (version_dir / "prompt.md").write_text(prompt_text, encoding="utf-8")

    # Save research report
    report_text = (
        f"# Research Report\n\n"
        f"**Assignment:** {assignment}\n\n"
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"**Sources:** {', '.join(sources)}\n\n"
        f"**Searches performed:** {len(result.search_queries)}\n\n"
        f"---\n\n"
        f"{result.answer}"
    )
    (version_dir / "report.md").write_text(report_text, encoding="utf-8")
    print(f"\n  Research report saved: {version_dir / 'report.md'}")

    # Save structured evidence
    evidence_data = {
        "assignment": assignment,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": result.model,
        "search_queries": result.search_queries,
        "tokens": {
            "input": result.input_tokens,
            "output": result.output_tokens,
        },
        "cost": result.cost,
        "duration_seconds": result.duration_seconds,
        "evidence": {},
    }
    for source_key, results_list in result.evidence.items():
        evidence_data["evidence"][source_key] = [
            {
                "rank": r.get("rank"),
                "score": r.get("score"),
                "text": r.get("text"),
                "metadata": r.get("metadata", {}),
                "id": r.get("id"),
            }
            for r in results_list
        ]
    (version_dir / "evidence.json").write_text(
        json.dumps(evidence_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Save metadata
    meta = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": round(result.duration_seconds, 1),
        "cost": round(result.cost, 4),
        "searches": len(result.search_queries),
        "model": result.model,
    }
    (version_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(f"  Cost: ${result.cost:.4f}")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print(f"  Searches: {len(result.search_queries)}")

    return result


# ============================================================
# PHASE 2: DRAFT (Claude Code CLI)
# ============================================================

def compose_draft_prompt(
    instructions: str,
    research_paths: list[Path],
    assignment: str,
    config: configparser.ConfigParser,
    draft_file: Path,
) -> str:
    """Assemble the full draft prompt from parts.

    Args:
        instructions: The editable draft instructions (from textarea or default).
        research_paths: List of research version directories to include.
        assignment: The assignment text.
        config: App configuration.
        draft_file: Where Claude should write the draft.

    Returns:
        The complete assembled prompt string.
    """
    # Load style guide
    style_guide_path = config.get("author", "style_guide",
                                   fallback="programs/author/references/olg_style_guide.md")
    style_guide = load_text(PROJECT_ROOT / style_guide_path)

    # Load research reports from selected versions
    research_texts = []
    for rpath in research_paths:
        report_file = rpath / "report.md"
        if report_file.exists():
            research_texts.append(report_file.read_text(encoding="utf-8"))

    if not research_texts:
        combined_research = "(No research was selected. Use the search tools to find relevant content.)"
    else:
        combined_research = "\n\n---\n\n".join(research_texts)

    # Assemble: instructions → assignment → research → style guide → output path
    parts = []

    parts.append(instructions)
    parts.append("\n\n---\n\n")

    parts.append("## Assignment\n\n")
    parts.append(assignment)
    parts.append("\n\n---\n\n")

    parts.append("## Research Findings\n\n")
    parts.append(combined_research)
    parts.append("\n\n---\n\n")

    if style_guide:
        parts.append("## OLG Style Guide\n\n")
        parts.append(style_guide)
        parts.append("\n\n---\n\n")

    parts.append("## Output Instructions\n\n")
    parts.append(f"Write your draft to: `{draft_file}`\n\n")
    parts.append(
        "Use the Write tool to create the file. Write clean markdown "
        "with proper heading hierarchy.\n\n"
        "At the end of the draft, include a `---` separator followed by "
        "a brief **Author's Notes** section with:\n"
        "- Any areas where you had to make judgment calls about structure or content\n"
        "- Any gaps you couldn't fill from available sources\n"
        "- Suggestions for the reviewer (content that should be verified, links to add, etc.)\n"
        "- Any system improvement suggestions (see the prompt above)\n"
    )

    return "".join(parts)


def launch_draft(
    full_prompt: str,
    draft_dir: Path,
    instructions: str,
    config: configparser.ConfigParser,
    name: str,
    session_id: str,
    based_on: list[str],
) -> None:
    """Save draft metadata and launch Claude Code in a terminal window.

    Args:
        full_prompt: The complete assembled prompt.
        draft_dir: The version directory for this draft.
        instructions: The editable instructions portion (saved as prompt.md).
        config: App configuration.
        name: Assignment name (for window title).
        session_id: Pre-generated session UUID.
        based_on: List of research version labels (e.g. ["research/001", "research/002"]).
    """
    import subprocess

    draft_file = draft_dir / "draft.md"

    # Save prompt and full prompt
    (draft_dir / "prompt.md").write_text(instructions, encoding="utf-8")
    (draft_dir / "full_prompt.md").write_text(full_prompt, encoding="utf-8")

    # Save session ID
    (draft_dir / "session_id.txt").write_text(session_id, encoding="utf-8")

    # Save metadata
    meta = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "based_on": based_on,
        "session_id": session_id,
    }
    (draft_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    # Write prompt to a temp file for Claude to read
    prompt_file = DATA_DIR / ".draft_prompt.md"
    prompt_file.write_text(full_prompt, encoding="utf-8")
    prompt_path = str(prompt_file.resolve())

    initial_msg = (
        f"Your full assignment is in {prompt_path} — it has the research findings, "
        f"style guide, and output instructions. Please read it and take it from there."
    )

    bat_file = DATA_DIR / ".run_draft.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {PROJECT_ROOT}\n'
        f'title Claude Code - {name}\n'
        f'echo.\n'
        f'echo  Authoring: {name}\n'
        f'echo  Draft output: {draft_file}\n'
        f'echo  Session ID: {session_id}\n'
        f'echo.\n'
        f'claude --session-id {session_id} "{initial_msg}"\n'
        f'echo.\n'
        f'echo  === Draft session complete ===\n'
        f'echo.\n'
        f'pause\n',
        encoding="utf-8",
    )

    subprocess.Popen(
        ["cmd", "/c", str(bat_file)],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def launch_resume(
    session_id: str,
    name: str,
) -> None:
    """Launch a Claude Code resume terminal for an existing session."""
    import subprocess

    bat_file = DATA_DIR / ".run_resume.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {PROJECT_ROOT}\n'
        f'title Claude Code Resume - {name}\n'
        f'echo.\n'
        f'echo  Resuming session: {session_id}\n'
        f'echo.\n'
        f'claude --resume {session_id}\n'
        f'echo.\n'
        f'pause\n',
        encoding="utf-8",
    )

    subprocess.Popen(
        ["cmd", "/c", str(bat_file)],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


# ============================================================
# PHASE 3: FORMAT (.docx)
# ============================================================

def run_format(
    draft_path: Path,
    output_path: Path,
    config: configparser.ConfigParser,
) -> Path | None:
    """Convert a draft markdown file to styled .docx.

    Args:
        draft_path: Path to the draft.md to format.
        output_path: Path where the .docx should be written.
        config: App configuration.

    Returns:
        Path to the generated .docx, or None on failure.
    """
    print(f"\n{'='*60}")
    print("PHASE 3: FORMAT (.docx)")
    print(f"{'='*60}")

    if not draft_path.exists():
        print(f"  ERROR: No draft found at {draft_path}")
        return None

    try:
        from tools.docx_writer import generate_docx
    except ImportError:
        print("  SKIPPED: docx_writer not available.")
        return None

    template_path = config.get("author", "template_docx",
                                fallback="programs/author/references/2026 OLG Template.docx")
    template_file = PROJECT_ROOT / template_path

    if not template_file.exists():
        print(f"  SKIPPED: OLG template not found at {template_file}")
        return None

    draft_text = draft_path.read_text(encoding="utf-8")
    generate_docx(draft_text, output_path, template_file)
    print(f"  .docx saved: {output_path}")
    return output_path


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="OLG Policy Authoring Agent — research, draft, and format OLG pages"
    )
    parser.add_argument(
        "assignment", nargs="?", default=None,
        help="The assignment text (what OLG content to create)"
    )
    parser.add_argument(
        "--name", "-n", required=True,
        help="Short name for this assignment (used for output directory)"
    )
    parser.add_argument(
        "--research-only", action="store_true",
        help="Run only the research phase"
    )
    parser.add_argument(
        "--draft-only", action="store_true",
        help="Run only the authoring phase, using existing research"
    )
    parser.add_argument(
        "--no-docx", action="store_true",
        help="Skip .docx generation"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume a previous Claude Code authoring session"
    )
    parser.add_argument(
        "--assignment-file", "-f", default=None,
        help="Read assignment text from a file instead of the command line"
    )
    args = parser.parse_args()

    # Handle resume mode
    if args.resume:
        output_dir = get_output_dir(args.name)
        # Find latest draft with a session ID
        from ui.versioning import list_versions, _parse_version_num
        drafts = list_versions(output_dir, "drafts")
        session_id = None
        for d in reversed(drafts):
            sid_file = d / "session_id.txt"
            if sid_file.exists():
                session_id = sid_file.read_text(encoding="utf-8").strip()
                break
        if not session_id:
            print(f"ERROR: No session ID found for '{args.name}'")
            sys.exit(1)
        print(f"\nResuming Claude Code session: {session_id}")
        launch_resume(session_id, args.name)
        return

    # Load assignment text
    assignment = args.assignment
    if args.assignment_file:
        assignment = Path(args.assignment_file).read_text(encoding="utf-8").strip()
    elif not assignment and not args.draft_only:
        saved = get_output_dir(args.name) / "assignment.txt"
        if saved.exists():
            assignment = saved.read_text(encoding="utf-8").strip()
            print(f"Using saved assignment from {saved}")
        else:
            print("ERROR: No assignment provided.")
            sys.exit(1)

    config = load_config()
    output_dir = get_output_dir(args.name)

    print(f"\n{'='*60}")
    print(f"OLG AUTHORING PIPELINE: {args.name}")
    print(f"{'='*60}")

    start = time.time()

    # Phase 1: Research
    if not args.draft_only:
        from ui.versioning import next_version_dir
        research_dir = next_version_dir(output_dir, "research")
        prompt_text = get_default_research_prompt()
        run_research(assignment, prompt_text, research_dir, config)

    # Phase 2: Draft
    if not args.research_only:
        import uuid
        from ui.versioning import next_version_dir, list_versions

        if args.draft_only and not assignment:
            saved = output_dir / "assignment.txt"
            if saved.exists():
                assignment = saved.read_text(encoding="utf-8").strip()
            else:
                print("ERROR: No assignment found.")
                sys.exit(1)

        # Use all research versions
        research_versions = list_versions(output_dir, "research")
        draft_dir = next_version_dir(output_dir, "drafts")
        draft_file = draft_dir / "draft.md"
        session_id = str(uuid.uuid4())
        instructions = get_default_draft_prompt()

        full_prompt = compose_draft_prompt(
            instructions=instructions,
            research_paths=research_versions,
            assignment=assignment,
            config=config,
            draft_file=draft_file,
        )

        based_on = [f"research/{d.name.split('_')[0]}" for d in research_versions]

        launch_draft(
            full_prompt=full_prompt,
            draft_dir=draft_dir,
            instructions=instructions,
            config=config,
            name=args.name,
            session_id=session_id,
            based_on=based_on,
        )

        print(f"\n  Claude Code terminal launched.")
        print(f"  Draft will be written to: {draft_file}")
        print(f"  Session ID: {session_id}")

        if not args.no_docx:
            print("\n  Run format after the draft is complete:")
            print(f"    python programs/author/author.py --name {args.name} --format-draft {draft_dir}")

    elapsed = time.time() - start
    print(f"\n  Total duration: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
