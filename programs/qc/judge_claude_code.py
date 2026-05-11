"""
QC Gap Analyzer — Judge engine that runs via Claude Code CLI.

Alternative to the API-based judge in qc_analyzer.run_judge(). Same
signature, same canonical (result, judge_trace) return shape — see the
canonical judge trace schema in qc_analyzer.py just above run_judge().

Why Claude Code:
- Subscription-billed (no per-token cost when the user is on Claude Pro/Max).
- Each finding gets its own session_id, persisted alongside the row JSON,
  so the user can `claude --resume <UUID>` to push back on any verdict
  after the fact.
- Same toolset access (rag/query.py via Bash) as the comparator's L2.

The agent self-reports its search trace into the result JSON. That trace
is then translated into the canonical schema so the audit walker,
inspect_finding.py, and the recurring-gap heuristic stay engine-agnostic.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.claude_code_runner import run_claude_task
from tools.result_formatters import format_results_for_prompt


PROMPT_PATH = PROJECT_ROOT / "programs" / "qc" / "prompts" / "qc_judge_claude_code.md"
DOMAIN_PREAMBLE_PATH = PROJECT_ROOT / "prompts" / "domain_preamble.md"


def _build_prompt(row: dict, extractor_result: dict, seed_results: list[dict],
                  result_file: Path, max_searches: int) -> str:
    domain_preamble = DOMAIN_PREAMBLE_PATH.read_text(encoding="utf-8")
    instructions = PROMPT_PATH.read_text(encoding="utf-8").replace(
        "{max_searches}", str(max_searches)
    )

    seed_formatted = format_results_for_prompt(seed_results, "olg")
    extractor_queries = extractor_result.get("search_queries", [])
    extractor_query_lines = "\n".join(f"- {q}" for q in extractor_queries) or "(none)"

    return (
        f"{domain_preamble}\n\n"
        f"---\n\n"
        f"{instructions}\n\n"
        f"---\n\n"
        f"## QC Finding\n\n"
        f"{(row.get('QC Findings', '') or '').strip()}\n\n"
        f"## Extracted Policy Issues\n\n"
        f"{extractor_result.get('policy_issues', 'Not available')}\n\n"
        f"## Seed Search Queries (already run)\n\n"
        f"{extractor_query_lines}\n\n"
        f"## Initial OLG Search Results (from seed queries)\n\n"
        f"{seed_formatted}\n\n"
        f"## Your Task\n\n"
        f"Investigate whether the OLG adequately covers the policy issue "
        f"above. You have {max_searches} additional OLG searches available "
        f"beyond what is shown in the seed results.\n\n"
        f"Write your result as JSON to: {result_file}\n"
    )


def _agent_trace_to_canonical(agent_trace: list[dict],
                              extractor_queries: list[str],
                              seed_results: list[dict]) -> list[dict]:
    """Translate agent self-reported trace into canonical judge_trace.

    See the canonical judge trace schema in qc_analyzer.py. Each entry
    in agent_trace becomes one turn (numbered from 1). A synthetic
    turn 0 captures the seed search so audits can verify seed-only
    citations.
    """
    canonical: list[dict] = [{
        "turn": 0,
        "stop_reason": "seed",
        "tokens": {"input": 0, "output": 0},
        "reasoning": "",
        "tool_calls": [
            {"query": q, "search_number": 0} for q in extractor_queries
        ],
        "tool_results": [{
            "result_count": len(seed_results),
            "results": _summarize_results(seed_results),
        }],
    }]

    for i, entry in enumerate(agent_trace, start=1):
        results = entry.get("results") or []
        canonical.append({
            "turn": i,
            "stop_reason": "tool_use",
            "tokens": {"input": 0, "output": 0},
            "reasoning": entry.get("reasoning", "") or "",
            "tool_calls": [{
                "query": entry.get("query", ""),
                "search_number": i,
            }],
            "tool_results": [{
                "result_count": len(results),
                "results": _summarize_results(results),
            }],
        })

    if canonical and canonical[-1]["turn"] > 0:
        canonical[-1]["stop_reason"] = "end_turn"

    return canonical


def _summarize_results(results: list[dict]) -> list[dict]:
    """Normalize result records to the canonical result_summary shape."""
    out = []
    for r in results or []:
        if not isinstance(r, dict):
            continue
        text_preview = r.get("text_preview")
        if text_preview is None:
            text_preview = (r.get("text") or "")[:300]
        out.append({
            "id": r.get("id", ""),
            "score": r.get("score"),
            "page_title": r.get("page_title", ""),
            "section_heading": r.get("section_heading", ""),
            "url": r.get("url", ""),
            "text_preview": text_preview,
        })
    return out


def run_judge_claude_code(
    row: dict,
    extractor_result: dict,
    seed_results: list[dict],
    analysis_dir: Path,
    row_index: int,
    finding_index: int,
    max_searches: int = 7,
    timeout: int = 1800,
    model: str | None = None,
) -> tuple[dict, list[dict]]:
    """Run the judge phase for a single finding via Claude Code CLI.

    Returns (verdict_dict, judge_trace). On failure, verdict_dict has
    coverage="Error" so the caller's normal error handling kicks in.

    Args:
        row:               Original QC row (with `QC Findings` text).
        extractor_result:  Extractor output for this finding (policy_issues,
                           search_queries).
        seed_results:      OLG search results from the extractor's seed
                           queries (deduped + score-sorted).
        analysis_dir:      output/qc_analysis/{name}/ — judge artifacts go
                           into a `judge_sessions/` subdir.
        row_index, finding_index:
                           For artifact naming and task IDs.
        max_searches:      Soft search budget surfaced in the prompt.
        timeout:           Subprocess timeout in seconds.
        model:             Optional CC model alias/ID (e.g. "sonnet", "opus",
                           "claude-sonnet-4-6"). None / empty = let Claude
                           Code pick its own default.
    """
    sessions_dir = analysis_dir / "judge_sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    task_id = f"row{row_index:03d}_finding{finding_index}"
    result_file = sessions_dir / f"{task_id}.json"

    prompt = _build_prompt(row, extractor_result, seed_results,
                           result_file, max_searches)

    extractor_queries = extractor_result.get("search_queries", [])

    task_result = run_claude_task(
        prompt=prompt,
        result_file=result_file,
        timeout=timeout,
        cwd=PROJECT_ROOT,
        log_dir=sessions_dir,
        task_id=task_id,
        windowed=False,
        model=model,
    )

    if not task_result["success"]:
        # Fail the same way the API engine does so the upstream
        # _api_error_result-style fallback in qc_analyzer kicks in.
        seed_only_trace = _agent_trace_to_canonical(
            [], extractor_queries, seed_results
        )
        return (
            {
                "coverage": "Error",
                "confidence": "N/A",
                "olg_references": [],
                "gap_description": (
                    f"Claude Code judge session failed: "
                    f"{task_result.get('error') or 'unknown error'}"
                ),
                "reasoning": "Investigation incomplete due to session error.",
                "error": task_result.get("error"),
                "searches_performed": 0,
                "all_search_queries": list(extractor_queries),
                "_session_id": task_result.get("session_id"),
                "_engine": "claude-code",
                "_model": model or "",
                "_elapsed": task_result.get("elapsed"),
            },
            seed_only_trace,
        )

    parsed = task_result["result"] or {}
    agent_trace = parsed.get("trace") or []
    judge_trace = _agent_trace_to_canonical(
        agent_trace, extractor_queries, seed_results
    )

    judge_queries = [
        (entry.get("query") or "").strip()
        for entry in agent_trace
        if (entry.get("query") or "").strip()
    ]
    all_search_queries = list(extractor_queries) + judge_queries

    return (
        {
            "coverage": parsed.get("coverage", "Unknown"),
            "confidence": parsed.get("confidence", "LOW"),
            "olg_references": parsed.get("olg_references", []),
            "gap_description": parsed.get("gap_description", ""),
            "reasoning": parsed.get("reasoning", ""),
            "agent_notes": parsed.get("agent_notes", ""),
            "searches_performed": len(judge_queries),
            "all_search_queries": all_search_queries,
            "_session_id": task_result.get("session_id"),
            "_engine": "claude-code",
            "_model": model or "",
            "_elapsed": task_result.get("elapsed"),
        },
        judge_trace,
    )


def launch_judge_resume(session_id: str, label: str) -> None:
    """Launch a Claude Code resume terminal for a QC judge session.

    Mirrors programs/author/author.py:launch_resume — writes a single
    shared .bat under the analysis output area and spawns it in a new
    console window.
    """
    import subprocess

    bat_dir = PROJECT_ROOT / "output" / "qc_analysis"
    bat_dir.mkdir(parents=True, exist_ok=True)
    bat_file = bat_dir / ".run_judge_resume.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {PROJECT_ROOT}\n'
        f'title Claude Code Resume - {label}\n'
        f'echo.\n'
        f'echo  Resuming QC judge session: {session_id}\n'
        f'echo  Finding: {label}\n'
        f'echo.\n'
        f'claude --permission-mode auto --resume {session_id}\n',
        encoding="utf-8",
    )

    subprocess.Popen(
        ["cmd", "/c", str(bat_file)],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
