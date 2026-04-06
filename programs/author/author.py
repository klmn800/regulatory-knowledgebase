"""
OLG Policy Authoring Agent — research, draft, and format OLG pages.

Three-phase pipeline:
  1. Research: Multi-source RAG synthesis with structured evidence output
  2. Author:  Claude Code CLI drafts OLG-voice content (session resumable)
  3. Format:  Draft markdown → styled .docx via OLG template

Usage:
    python agents/author.py "Consolidate all VC-1 user entered field scripts" --name vc1_scripts
    python agents/author.py "Find VC-1 scripts" --name vc1_scripts --research-only
    python agents/author.py --name vc1_scripts --draft-only
    python agents/author.py --name vc1_scripts --resume
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
from tools.claude_code_runner import run_claude_task


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
    name: str,
    config: configparser.ConfigParser,
) -> SynthesisResult:
    """Run the research phase — deep RAG synthesis with structured output."""
    output_dir = get_output_dir(name)

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

    # Save research report (narrative)
    report_file = output_dir / "research_report.md"
    report_file.write_text(
        f"# Research Report\n\n"
        f"**Assignment:** {assignment}\n\n"
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"**Sources:** {', '.join(sources)}\n\n"
        f"**Searches performed:** {len(result.search_queries)}\n\n"
        f"---\n\n"
        f"{result.answer}",
        encoding="utf-8",
    )
    print(f"\n  Research report saved: {report_file}")

    # Save structured evidence (JSON)
    evidence_file = output_dir / "research_evidence.json"
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

    evidence_file.write_text(
        json.dumps(evidence_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Evidence saved: {evidence_file}")

    # Save assignment text
    assignment_file = output_dir / "assignment.txt"
    assignment_file.write_text(assignment, encoding="utf-8")

    print(f"\n  Cost: ${result.cost:.4f}")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print(f"  Searches: {len(result.search_queries)}")

    return result


# ============================================================
# PHASE 2: AUTHOR (Claude Code CLI)
# ============================================================

def compose_authoring_prompt(
    assignment: str,
    name: str,
    config: configparser.ConfigParser,
) -> str:
    """Compose the full prompt for the Claude Code authoring session."""
    output_dir = get_output_dir(name)
    draft_file = output_dir / "draft.md"

    # Load prompt components
    preamble = load_text(SHARED_PROMPTS_DIR / "domain_preamble.md") or ""
    author_prompt = load_text(PROMPTS_DIR / "author_draft.md") or ""

    # Load style guide if available
    style_guide_path = config.get("author", "style_guide",
                                   fallback="agents/references/olg_style_guide.md")
    style_guide = load_text(PROJECT_ROOT / style_guide_path)

    # Load research report
    research_report = load_text(output_dir / "research_report.md")
    if not research_report:
        print("  WARNING: No research report found. Running draft without research.")
        research_report = "(No research was conducted. Use the search tools to find relevant content.)"

    # Compose the full prompt
    parts = [preamble, "\n\n---\n\n"]

    if style_guide:
        parts.append("## OLG Style Guide\n\n")
        parts.append(style_guide)
        parts.append("\n\n---\n\n")

    parts.append(author_prompt)
    parts.append("\n\n---\n\n")

    parts.append("## Assignment\n\n")
    parts.append(assignment)
    parts.append("\n\n---\n\n")

    parts.append("## Research Findings\n\n")
    parts.append(research_report)
    parts.append("\n\n---\n\n")

    parts.append(f"## Output Instructions\n\n")
    parts.append(f"Write your draft to: `{draft_file}`\n\n")
    parts.append(
        "Use the Write tool to create the file. Write clean markdown.\n"
        "Include the Author's Notes section at the end after a `---` separator."
    )

    return "".join(parts)


def run_author(
    assignment: str,
    name: str,
    config: configparser.ConfigParser,
) -> dict:
    """Run the authoring phase — Claude Code CLI drafts the OLG page."""
    output_dir = get_output_dir(name)
    draft_file = output_dir / "draft.md"
    timeout = config.getint("author", "claude_code_timeout", fallback=600)

    print(f"\n{'='*60}")
    print("PHASE 2: AUTHOR (Claude Code CLI)")
    print(f"{'='*60}")

    prompt = compose_authoring_prompt(assignment, name, config)

    print(f"  Prompt length: {len(prompt):,} chars")
    print(f"  Draft output: {draft_file}")
    print(f"  Timeout: {timeout}s")
    print()

    result = run_claude_task(
        prompt=prompt,
        result_file=draft_file,
        timeout=timeout,
        cwd=PROJECT_ROOT,
        log_dir=output_dir / "sessions",
        task_id=name,
        parse_json=False,
    )

    # Save session ID for resume
    if result.get("session_id"):
        session_file = output_dir / "session_id.txt"
        session_file.write_text(result["session_id"], encoding="utf-8")
        print(f"\n  Session ID: {result['session_id']}")
        print(f"  Resume with: claude --resume {result['session_id']}")
    else:
        print("\n  WARNING: No session ID captured (windowed mode or error)")

    if result["success"]:
        # The draft was written as a file (not JSON), so read it directly
        if draft_file.exists():
            draft_text = draft_file.read_text(encoding="utf-8")
            print(f"  Draft saved: {draft_file} ({len(draft_text):,} chars)")
        else:
            print(f"  WARNING: Draft file not found at {draft_file}")
    else:
        print(f"  ERROR: {result.get('error', 'Unknown error')}")

    print(f"  Duration: {result['elapsed']:.1f}s")

    return result


# ============================================================
# PHASE 3: FORMAT (.docx)
# ============================================================

def run_format(name: str, config: configparser.ConfigParser) -> Path | None:
    """Run the formatting phase — convert draft markdown to styled .docx."""
    output_dir = get_output_dir(name)
    draft_file = output_dir / "draft.md"
    docx_file = output_dir / "output.docx"

    print(f"\n{'='*60}")
    print("PHASE 3: FORMAT (.docx)")
    print(f"{'='*60}")

    if not draft_file.exists():
        print(f"  ERROR: No draft found at {draft_file}")
        print("  Run the authoring phase first, or provide a draft file.")
        return None

    try:
        from tools.docx_writer import generate_docx
    except ImportError:
        print("  SKIPPED: docx_writer not yet implemented.")
        print("  The draft is available as markdown at:")
        print(f"    {draft_file}")
        return None

    template_path = config.get("author", "template_docx",
                                fallback="agents/references/olg_template.docx")
    template_file = PROJECT_ROOT / template_path

    if not template_file.exists():
        print(f"  SKIPPED: OLG template not found at {template_file}")
        print("  Provide the template .docx to enable formatting.")
        return None

    draft_text = draft_file.read_text(encoding="utf-8")
    generate_docx(draft_text, docx_file, template_file)
    print(f"  .docx saved: {docx_file}")
    return docx_file


# ============================================================
# RESUME
# ============================================================

def run_resume(name: str):
    """Resume a previous Claude Code authoring session."""
    output_dir = get_output_dir(name)
    session_file = output_dir / "session_id.txt"

    if not session_file.exists():
        print(f"ERROR: No session ID found at {session_file}")
        print(f"  Has the authoring phase been run for '{name}'?")
        sys.exit(1)

    session_id = session_file.read_text(encoding="utf-8").strip()
    print(f"\nResuming Claude Code session: {session_id}")
    print(f"Assignment directory: {output_dir}")
    print()
    print(f"Run this command to resume interactively:")
    print(f"  claude --resume {session_id}")
    print()

    # Offer to launch it
    try:
        response = input("Launch now? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if response == "y":
        import subprocess
        subprocess.run(
            ["claude", "--resume", session_id],
            cwd=str(PROJECT_ROOT),
        )


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
        help="Run only the research phase (Phase 1)"
    )
    parser.add_argument(
        "--draft-only", action="store_true",
        help="Run only the authoring phase (Phase 2), using existing research"
    )
    parser.add_argument(
        "--no-docx", action="store_true",
        help="Skip .docx generation (Phase 3)"
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
        run_resume(args.name)
        return

    # Load assignment text
    assignment = args.assignment
    if args.assignment_file:
        assignment = Path(args.assignment_file).read_text(encoding="utf-8").strip()
    elif not assignment and not args.draft_only:
        # Check for saved assignment
        saved = get_output_dir(args.name) / "assignment.txt"
        if saved.exists():
            assignment = saved.read_text(encoding="utf-8").strip()
            print(f"Using saved assignment from {saved}")
        else:
            print("ERROR: No assignment provided. Pass text, --assignment-file, or --draft-only.")
            sys.exit(1)

    config = load_config()

    print(f"\n{'='*60}")
    print(f"OLG AUTHORING PIPELINE: {args.name}")
    print(f"{'='*60}")

    start = time.time()
    research_result = None

    # Phase 1: Research
    if not args.draft_only:
        research_result = run_research(assignment, args.name, config)

    # Phase 2: Author
    if not args.research_only:
        # Load assignment from saved file if in draft-only mode
        if args.draft_only and not assignment:
            saved = get_output_dir(args.name) / "assignment.txt"
            if saved.exists():
                assignment = saved.read_text(encoding="utf-8").strip()
            else:
                print("ERROR: No assignment found. Run the full pipeline first.")
                sys.exit(1)

        author_result = run_author(assignment, args.name, config)

        # Phase 3: Format
        if not args.no_docx and author_result.get("success"):
            run_format(args.name, config)

    # Summary
    elapsed = time.time() - start
    output_dir = get_output_dir(args.name)
    print(f"\n{'='*60}")
    print("COMPLETE")
    print(f"{'='*60}")
    print(f"  Output directory: {output_dir}")
    print(f"  Total duration: {elapsed:.1f}s")

    # List deliverables
    deliverables = [
        ("Research report", output_dir / "research_report.md"),
        ("Research evidence", output_dir / "research_evidence.json"),
        ("Draft", output_dir / "draft.md"),
        ("Formatted doc", output_dir / "output.docx"),
        ("Session ID", output_dir / "session_id.txt"),
    ]
    print("\n  Deliverables:")
    for label, path in deliverables:
        status = "READY" if path.exists() else "---"
        print(f"    [{status:>5}] {label}: {path.name}")


if __name__ == "__main__":
    main()
