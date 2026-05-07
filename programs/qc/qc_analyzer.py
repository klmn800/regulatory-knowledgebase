"""
QC Gap Analyzer — Identify OLG guidance gaps from QC error findings.

Reads QC error report CSVs and analyzes each finding against the DTA
Online Guide (OLG) to determine whether adequate policy and procedure
guidance exists. Extractor (Haiku) distills the policy/procedure issue;
Judge (Sonnet) does an agentic OLG search and rates coverage as
Adequate / Partial / Gap. Optional CMR / FNS / CFR cross-checks then
locate the underlying regulation for findings the OLG didn't cover.

Driven by the FastAPI UI (ui/app.py) — no CLI entry point.
"""

import configparser
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rag.query import create_client, search_with_client
from tools.cost_tracker import Tracker
from tools.policy_tools import SEARCH_OLG_TOOL
from tools.result_formatters import format_results_for_prompt
from tools.retry import with_rate_limit_retry


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config.ini"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "output" / "qc_analysis"
ANALYSIS_DIR = OUTPUT_DIR  # alias for UI imports
CHECKPOINT_FILE = OUTPUT_DIR / "qc_checkpoint.json"

APPENDED_COLUMNS = [
    "Policy_Issues",
    "OLG_Coverage",
    "OLG_References",
    "Gap_Description",
    "Search_Queries_Used",
    "Searches_Performed",
]


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_prompt(name: str, with_preamble: bool = False) -> str:
    filepath = PROMPTS_DIR / f"{name}.md"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if with_preamble:
        preamble_path = PROJECT_ROOT / "prompts" / "domain_preamble.md"
        if preamble_path.exists():
            with open(preamble_path, "r", encoding="utf-8") as f:
                preamble = f.read()
            content = preamble + "\n\n---\n\n" + content
    return content


FILTER_SOURCES = ("olg", "cmr", "fns", "cfr")


def _load_filters(config: configparser.ConfigParser) -> dict:
    """Read per-source program filter lists from [qc_analyzer]. Returns
    {source: {"include": [...], "exclude": [...]}}. Both lists are
    informational; the include list is the active whitelist."""
    filters = {}
    for src in FILTER_SOURCES:
        include_raw = config.get("qc_analyzer", f"{src}_include", fallback="")
        exclude_raw = config.get("qc_analyzer", f"{src}_exclude", fallback="")
        filters[src] = {
            "include": [p.strip() for p in include_raw.split(",") if p.strip()],
            "exclude": [p.strip() for p in exclude_raw.split(",") if p.strip()],
        }
    return filters


# ============================================================
# UTILITIES
# ============================================================

def extract_json(text: str, fallback_classification: str = "Partial") -> dict:
    """Extract a JSON object from a response that may contain surrounding
    prose or markdown. Tries multiple strategies."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if text.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", text)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "coverage": fallback_classification,
        "confidence": "LOW",
        "reasoning": text[:300],
    }


# ============================================================
# CSV I/O
# ============================================================

def load_csv(filepath: Path) -> tuple[list[str], list[dict]]:
    """Load QC report CSV. Returns (fieldnames, rows_as_dicts).
    Tries UTF-8 (with BOM), falls back to cp1252 for Windows-exported CSVs."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(filepath, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames)
                rows = list(reader)
            return fieldnames, rows
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {filepath.name} as UTF-8 or CP1252")


def select_rows(rows: list[dict], sample: int = None,
                row_indices: list[int] = None) -> list[tuple[int, dict]]:
    """Select which rows to process. Returns list of (1-based-index, row)."""
    if row_indices:
        return [(i, rows[i - 1]) for i in row_indices if 1 <= i <= len(rows)]
    if sample:
        return [(i + 1, row) for i, row in enumerate(rows[:sample])]
    return [(i + 1, row) for i, row in enumerate(rows)]


# ============================================================
# PER-ANALYSIS DIRECTORY MANAGEMENT
# ============================================================

def get_analysis_dir(name: str) -> Path:
    """Return (and create) the directory for a named analysis."""
    d = ANALYSIS_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "results").mkdir(exist_ok=True)
    return d


def save_finding(analysis_dir: Path, row_index: int, data: dict) -> Path:
    """Write a per-finding JSON to results/row_NNN.json."""
    path = analysis_dir / "results" / f"row_{row_index:03d}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_finding(analysis_dir: Path, row_index: int) -> dict | None:
    """Read a single finding JSON. Returns None if not found."""
    path = analysis_dir / "results" / f"row_{row_index:03d}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_all_findings(analysis_dir: Path) -> list[dict]:
    """Read all finding JSONs, sorted by row_index."""
    results_dir = analysis_dir / "results"
    if not results_dir.exists():
        return []
    findings = []
    for path in sorted(results_dir.glob("row_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            findings.append(json.load(f))
    findings.sort(key=lambda f: f.get("row_index", 0))
    return findings


def save_meta(analysis_dir: Path, meta: dict) -> None:
    """Write meta.json for an analysis."""
    path = analysis_dir / "meta.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def load_meta(analysis_dir: Path) -> dict | None:
    """Read meta.json. Returns None if not found."""
    path = analysis_dir / "meta.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_summary_csv(analysis_dir: Path) -> Path:
    """Build a summary CSV from all finding JSONs."""
    findings = load_all_findings(analysis_dir)
    if not findings:
        return None

    csv_path = analysis_dir / "summary.csv"

    summary_columns = [
        "row_index", "review_number", "tao", "error_amount",
        "determination", "error_type", "policy_issues", "coverage",
        "confidence", "gap_description", "olg_references",
        "searches_performed",
    ]
    # Add cross-check columns if present
    if any("_cmr_check" in f for f in findings):
        summary_columns.extend([
            "cmr_classification", "cmr_sections", "cmr_note",
        ])
    if any("_fns_check" in f for f in findings):
        summary_columns.extend([
            "fns_classification", "fns_sections", "fns_note",
        ])

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=summary_columns,
                                extrasaction="ignore")
        writer.writeheader()
        for finding in findings:
            row = {k: finding.get(k, "") for k in summary_columns}
            # Flatten list fields
            refs = finding.get("olg_references", [])
            if isinstance(refs, list):
                row["olg_references"] = "; ".join(str(r) for r in refs)
            # Flatten cross-check fields
            cmr = finding.get("_cmr_check", {})
            if cmr:
                row["cmr_classification"] = cmr.get("classification", "")
                secs = cmr.get("cmr_sections", [])
                row["cmr_sections"] = "; ".join(secs) if isinstance(secs, list) else str(secs)
                row["cmr_note"] = cmr.get("note", "")
            fns = finding.get("_fns_check", {})
            if fns:
                row["fns_classification"] = fns.get("classification", "")
                secs = fns.get("fns_sections", [])
                row["fns_sections"] = "; ".join(secs) if isinstance(secs, list) else str(secs)
                row["fns_note"] = fns.get("note", "")
            writer.writerow(row)

    return csv_path


# ============================================================
# CALL 1: EXTRACTOR
# ============================================================

def build_extractor_input(row: dict) -> str:
    """Assemble the input for the Extractor from a QC CSV row."""
    parts = []

    findings = row.get("QC Findings", "").strip()
    if findings:
        parts.append(f"## QC Finding Narrative\n{findings}")

    determination = row.get("Food Stamp Determination", "").strip()
    error_type = row.get("Type Of Errors", "").strip()
    if determination:
        parts.append(f"Determination: {determination}")
    if error_type:
        parts.append(f"Error Type: {error_type}")

    qc_comments = row.get("QC Comments", "").strip()
    if qc_comments:
        parts.append(f"## QC Comments\n{qc_comments}")

    disagree = row.get("Disagree Specific Reason(s)", "").strip()
    if disagree:
        parts.append(f"## Disagree Reason\n{disagree}")

    non_concur = row.get("Non-Concur Reason", "").strip()
    if non_concur:
        parts.append(f"## Non-Concur Reason\n{non_concur}")

    return "\n\n".join(parts)


def run_extractor(user_message: str, client: anthropic.Anthropic,
                  model: str, system_prompt: str,
                  cost_tracker: Tracker | None = None) -> dict:
    """Call 1: Extract policy issues and search queries from a QC finding."""

    @with_rate_limit_retry()
    def _do_extractor_call():
        return client.messages.create(
            model=model,
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

    try:
        response = _do_extractor_call()
    except anthropic.APIError:
        return {
            "policy_issues": "Extraction failed due to API error.",
            "search_queries": [user_message[:200]],
        }

    if cost_tracker:
        cost_tracker.record("extractor", model, response.usage)
    text = response.content[0].text.strip()
    return extract_json(text, fallback_classification="Partial")


# ============================================================
# SEED SEARCH
# ============================================================

def run_seed_searches(queries: list[str], olg_clients: dict,
                      results_per_query: int = 5,
                      programs: list[str] | None = None) -> list[dict]:
    """Run extractor's queries against OLG and deduplicate results."""
    seen_ids = set()
    all_results = []

    for query in queries:
        if not query or not query.strip():
            continue
        response = search_with_client(
            query, olg_clients,
            collection="sections",
            programs=programs,
            top_n=results_per_query,
            threshold=0.0,
        )
        for result in response["results"]:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                all_results.append(result)

    all_results.sort(key=lambda r: r["score"], reverse=True)
    return all_results


# ============================================================
# CALL 2: JUDGE (AGENTIC)
# ============================================================

def run_judge(row: dict, extractor_result: dict, seed_results: list[dict],
              olg_clients: dict, client: anthropic.Anthropic,
              model: str, system_prompt: str,
              max_searches: int = 10,
              results_per_search: int = 5,
              cost_tracker: Tracker | None = None,
              olg_programs: list[str] | None = None) -> tuple[dict, list[dict]]:
    """Call 2: Agentic OLG coverage assessment with iterative search.

    Returns (result, judge_trace) — the final classification dict plus an
    array of per-turn entries (turn / stop_reason / tokens / reasoning /
    tool_calls / tool_results). The trace is appended to the per-finding
    JSON so prompt-tuning consumers can see how the judge reasoned.
    """

    seed_formatted = format_results_for_prompt(seed_results, "olg")
    extractor_queries = extractor_result.get("search_queries", [])

    user_message = (
        f"## QC Finding\n\n"
        f"{row.get('QC Findings', '').strip()}\n\n"
        f"## Extracted Policy Issues\n\n"
        f"{extractor_result.get('policy_issues', 'Not available')}\n\n"
        f"## Initial OLG Search Results\n\n"
        f"The following results were found using {len(extractor_queries)} "
        f"automated search queries:\n\n"
        f"{seed_formatted}\n\n"
        f"## Your Search Budget\n\n"
        f"You have {max_searches} search_olg calls available. "
        f"Review the seed results above, then plan and execute your "
        f"search strategy to assess OLG coverage."
    )

    messages = [{"role": "user", "content": user_message}]

    searches_performed = 0
    all_search_queries = list(extractor_queries)
    max_turns = max_searches + 5
    judge_trace: list[dict] = []

    def _api_error_result(error: Exception) -> dict:
        return {
            "coverage": "Partial",
            "olg_references": [],
            "gap_description": f"Judge API error: {error}",
            "confidence": "LOW",
            "reasoning": "Analysis incomplete due to API error.",
            "searches_performed": searches_performed,
            "all_search_queries": all_search_queries,
        }

    @with_rate_limit_retry()
    def _do_judge_call():
        return client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_prompt,
            messages=messages,
            tools=[SEARCH_OLG_TOOL],
        )

    for turn in range(max_turns):
        try:
            response = _do_judge_call()
        except anthropic.APIError as e:
            return _api_error_result(e), judge_trace

        if cost_tracker:
            cost_tracker.record("judge", model, response.usage)

        reasoning_text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text.strip():
                reasoning_text = block.text.strip()

        if response.stop_reason == "tool_use":
            tool_results = []
            trace_tool_calls = []
            trace_tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use" and block.name == "search_olg":
                    query = block.input.get("query", "")

                    if searches_performed >= max_searches:
                        budget_msg = (
                            f"Search budget exhausted ({searches_performed} "
                            f"searches used). Please provide your final "
                            f"assessment now based on all results seen."
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": budget_msg,
                        })
                        trace_tool_calls.append({"query": query, "budget_exhausted": True})
                        trace_tool_results.append({"status": "budget_exhausted"})
                        continue

                    searches_performed += 1
                    all_search_queries.append(query)
                    print(f".", end="", flush=True)

                    search_response = search_with_client(
                        query, olg_clients,
                        collection="sections",
                        programs=olg_programs,
                        top_n=results_per_search,
                        threshold=0.0,
                    )

                    formatted = format_results_for_prompt(
                        search_response["results"], "olg"
                    )
                    remaining = max_searches - searches_performed
                    formatted += f"\n\n[{remaining} searches remaining]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": formatted,
                    })

                    trace_tool_calls.append({
                        "query": query,
                        "search_number": searches_performed,
                    })
                    trace_tool_results.append({
                        "result_count": len(search_response["results"]),
                        "results": _summarize_search_results(search_response["results"]),
                    })

            judge_trace.append({
                "turn": turn + 1,
                "stop_reason": "tool_use",
                "tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                "reasoning": reasoning_text,
                "tool_calls": trace_tool_calls,
                "tool_results": trace_tool_results,
            })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            continue

        judge_trace.append({
            "turn": turn + 1,
            "stop_reason": response.stop_reason,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
            "reasoning": reasoning_text,
            "tool_calls": [],
            "tool_results": [],
        })

        result = extract_json(reasoning_text, fallback_classification="Partial")
        result["searches_performed"] = searches_performed
        result["all_search_queries"] = all_search_queries
        return result, judge_trace

    return {
        "coverage": "Partial",
        "olg_references": [],
        "gap_description": "Judge exhausted maximum turns without conclusion.",
        "confidence": "LOW",
        "reasoning": "Maximum conversation turns reached.",
        "searches_performed": searches_performed,
        "all_search_queries": all_search_queries,
    }, judge_trace


def _summarize_search_results(results: list[dict]) -> list[dict]:
    """Compact summary of OLG search results for the trace log."""
    summaries = []
    for r in results:
        meta = r.get("metadata", {})
        summaries.append({
            "id": r.get("id", ""),
            "score": round(r.get("score", 0), 3),
            "page_title": meta.get("page_title", meta.get("title", "")),
            "section_heading": meta.get("section_heading", ""),
            "url": meta.get("url", ""),
            "text_preview": r.get("text", "")[:300],
        })
    return summaries


# ============================================================
# OUTPUT ROW BUILDING
# ============================================================

def build_output_row(original_row: dict, extractor_result: dict,
                     judge_result: dict) -> dict:
    """Merge original CSV row with analysis columns."""
    output = dict(original_row)

    output["Policy_Issues"] = extractor_result.get("policy_issues", "")
    output["OLG_Coverage"] = judge_result.get("coverage", "Unknown")

    refs = judge_result.get("olg_references", [])
    if isinstance(refs, list):
        output["OLG_References"] = "; ".join(str(r) for r in refs)
    else:
        output["OLG_References"] = str(refs)

    gap_desc = judge_result.get("gap_description", "")
    reasoning = judge_result.get("reasoning", "")
    if gap_desc and reasoning:
        output["Gap_Description"] = f"{gap_desc} || Reasoning: {reasoning}"
    elif reasoning:
        output["Gap_Description"] = reasoning
    else:
        output["Gap_Description"] = gap_desc

    queries = judge_result.get("all_search_queries", [])
    output["Search_Queries_Used"] = " | ".join(str(q) for q in queries)
    output["Searches_Performed"] = str(judge_result.get("searches_performed", 0))

    return output


# ============================================================
# UI-FACING PIPELINE FUNCTIONS
# ============================================================

def run_extract(analysis_dir: Path, rows: list[dict],
                config: configparser.ConfigParser = None) -> list[dict]:
    """Run the Extractor on CSV rows and save per-finding JSONs.

    Args:
        analysis_dir: Path to the analysis directory (from get_analysis_dir).
        rows: List of CSV row dicts (from load_csv).
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of extracted finding dicts.
    """
    if config is None:
        config = load_config()

    extractor_model = config.get("qc_analyzer", "extractor_model")
    extractor_prompt = load_prompt("qc_extractor", with_preamble=True)

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)

    cost_tracker = Tracker(
        stages=["extractor", "judge", "cmr_check", "fns_check", "cfr_check"]
    )

    start_time = time.time()
    findings = []
    for row_idx, row in enumerate(rows, start=1):
        findings_text = row.get("QC Findings", "").strip()
        if not findings_text:
            continue

        extractor_input = build_extractor_input(row)
        extractor_result = run_extractor(
            extractor_input, claude, extractor_model, extractor_prompt,
            cost_tracker=cost_tracker,
        )

        queries = extractor_result.get("search_queries", [])
        if not isinstance(queries, list):
            queries = [str(queries)]

        # Clean parenthetical noise from determination
        det = row.get("Food Stamp Determination", "")
        det = re.sub(r"\s*\(Complete [^)]+\)", "", det).strip()

        raw_error_type = row.get("Type Of Errors", "")
        error_type = " / ".join(p.strip() for p in raw_error_type.split(";") if p.strip())

        finding = {
            "row_index": row_idx,
            "review_number": row.get("Review Number", ""),
            "apid": row.get("APID", ""),
            "tao": row.get("TAO", ""),
            "error_amount": row.get("Error Amount", ""),
            "determination": det,
            "error_type": error_type,
            "finding_narrative": findings_text,
            "non_concur_reason": row.get("Non-Concur Reason", "").strip(),
            "policy_issues": extractor_result.get("policy_issues", ""),
            "search_queries": queries,
            "phase": "extracted",
        }
        save_finding(analysis_dir, row_idx, finding)
        findings.append(finding)

    elapsed = round(time.time() - start_time, 1)

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"]["extracted"] = True
    if "cost" not in meta:
        meta["cost"] = {}
    if "filter_snapshot" not in meta:
        meta["filter_snapshot"] = _load_filters(config)
    extractor_data = cost_tracker.by_stage()["extractor"]
    meta["cost"]["extractor"] = round(extractor_data["cost"], 4)
    meta["extract_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(findings),
        "model": extractor_model,
        "tokens_in": extractor_data["input_tokens"],
        "tokens_out": extractor_data["output_tokens"],
        "cost": round(extractor_data["cost"], 4),
    }
    save_meta(analysis_dir, meta)

    return findings


def run_investigate(analysis_dir: Path, row_indices: list[int] = None,
                    config: configparser.ConfigParser = None) -> list[dict]:
    """Run Seed Search + Judge on extracted findings.

    Args:
        analysis_dir: Path to the analysis directory.
        row_indices: Optional list of 1-based row indices to investigate.
                     Defaults to all extracted findings.
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of updated finding dicts with investigation results.
    """
    if config is None:
        config = load_config()

    judge_model = config.get("qc_analyzer", "judge_model")
    max_judge_searches = config.getint("qc_analyzer", "max_judge_searches",
                                       fallback=10)
    olg_results_per_search = config.getint("qc_analyzer",
                                           "olg_results_per_search",
                                           fallback=5)
    seed_results_per_query = config.getint("qc_analyzer",
                                           "seed_results_per_query",
                                           fallback=5)
    judge_prompt = load_prompt("qc_judge", with_preamble=True)

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    olg_clients = create_client(source="olg")

    # Load upload.csv to get full row data for the judge
    csv_path = analysis_dir / "upload.csv"
    if csv_path.exists():
        _, all_rows = load_csv(csv_path)
    else:
        all_rows = []

    # Determine which findings to investigate
    if row_indices is None:
        all_findings = load_all_findings(analysis_dir)
        row_indices = [f["row_index"] for f in all_findings
                       if f.get("phase") == "extracted"]

    cost_tracker = Tracker(
        stages=["extractor", "judge", "cmr_check", "fns_check", "cfr_check"]
    )

    olg_programs = _load_filters(config)["olg"]["include"] or None

    start_time = time.time()
    results = []
    for row_idx in row_indices:
        finding = load_finding(analysis_dir, row_idx)
        if not finding:
            continue

        # Get original CSV row for the judge (provides full finding narrative)
        if 1 <= row_idx <= len(all_rows):
            original_row = all_rows[row_idx - 1]
        else:
            original_row = {"QC Findings": finding.get("finding_narrative", "")}

        extractor_result = {
            "policy_issues": finding.get("policy_issues", ""),
            "search_queries": finding.get("search_queries", []),
        }

        # Seed search
        seed_results = run_seed_searches(
            extractor_result["search_queries"], olg_clients,
            results_per_query=seed_results_per_query,
            programs=olg_programs,
        )

        # Judge
        judge_result, judge_trace = run_judge(
            original_row, extractor_result, seed_results, olg_clients,
            claude, judge_model, judge_prompt,
            max_searches=max_judge_searches,
            results_per_search=olg_results_per_search,
            cost_tracker=cost_tracker,
            olg_programs=olg_programs,
        )

        # Update finding with judge results
        finding["phase"] = "investigated"
        finding["coverage"] = judge_result.get("coverage", "Unknown")
        finding["confidence"] = judge_result.get("confidence", "LOW")
        finding["olg_references"] = judge_result.get("olg_references", [])
        finding["gap_description"] = judge_result.get("gap_description", "")
        finding["reasoning"] = judge_result.get("reasoning", "")
        finding["searches_performed"] = judge_result.get("searches_performed", 0)
        finding["all_search_queries"] = judge_result.get("all_search_queries", [])
        finding["judge_trace"] = judge_trace

        save_finding(analysis_dir, row_idx, finding)
        results.append(finding)

    elapsed = round(time.time() - start_time, 1)

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"]["investigated"] = True
    meta["investigated_rows"] = row_indices
    if "cost" not in meta:
        meta["cost"] = {}
    judge_data = cost_tracker.by_stage()["judge"]
    meta["cost"]["judge"] = round(judge_data["cost"], 4)
    meta["investigate_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(results),
        "model": judge_model,
        "tokens_in": judge_data["input_tokens"],
        "tokens_out": judge_data["output_tokens"],
        "cost": round(judge_data["cost"], 4),
    }
    save_meta(analysis_dir, meta)

    return results


# ============================================================
# CROSS-CHECK FUNCTIONS (CMR / FNS)
# ============================================================

def _format_source_results_for_prompt(results: list[dict], source: str) -> str:
    """Format CMR / FNS / CFR search results for inclusion in a cross-check prompt."""
    if not results:
        return f"No {source.upper()} matches found."

    parts = []
    for i, result in enumerate(results):
        meta = result["metadata"]
        if source == "cmr":
            sec_num = meta.get("section_number", "")
            sec_title = meta.get("section_title", "")
            label = f"{sec_num} {sec_title}".strip()
        elif source == "cfr":
            sec_num = meta.get("section_number", "")
            sec_title = meta.get("section_title", "")
            hierarchy = meta.get("hierarchy_full_path") or meta.get("hierarchy_path", "")
            label = f"§ {sec_num} {sec_title}".strip()
            if hierarchy:
                label = f"{label} {hierarchy}"
        else:
            sec_num = meta.get("section_number", meta.get("title", ""))
            sec_title = meta.get("section_title", "")
            label = f"{sec_num} {sec_title}".strip()

        score = result["score"]
        text = result["text"][:1000]

        header = f"[{source.upper()} Match {i+1}] Score: {score:.2f} | {label}"
        parts.append(f"{header}\n{text}")
        if len(result["text"]) > 1000:
            parts.append("... (truncated)")
        parts.append("")

    return "\n".join(parts)


def _build_crosscheck_user_message(finding: dict, source_results_formatted: str,
                                   source: str) -> str:
    """Build the user message for a CMR or FNS cross-check call."""
    parts = [
        f"## QC Error\n",
        f"Review #{finding.get('review_number', '?')} ({finding.get('tao', '?')})",
        f"Determination: {finding.get('determination', '?')}",
        f"Error Type: {finding.get('error_type', '?')}",
        f"Narrative: {finding.get('finding_narrative', 'N/A')}",
        f"",
        f"## Extracted Policy Issue\n",
        f"{finding.get('policy_issues', 'N/A')}",
        f"",
        f"## OLG Coverage Finding\n",
        f"Coverage: {finding.get('coverage', 'Unknown')}",
    ]
    gap = finding.get("gap_description", "")
    if gap:
        parts.append(f"Gap: {gap}")
    reasoning = finding.get("reasoning", "")
    if reasoning:
        parts.append(f"Reasoning: {reasoning}")

    parts.extend([
        f"",
        f"## {source.upper()} Search Results\n",
        source_results_formatted,
    ])
    return "\n".join(parts)


# SOURCE_CHECK_CONFIG drives run_source_check. Each entry collapses what
# was once a near-duplicate run_X_check function into a single row in this
# table. Program filtering is driven uniformly through [qc_analyzer]
# {source}_include / {source}_exclude config keys (see _load_filters).
SOURCE_CHECK_CONFIG = {
    "cmr": {
        "prompt_name": "qc_cmr_check",
        "model_config_key": "cmr_check_model",
        "fallback_classification": "cmr_silent",
        "result_key": "_cmr_check",
        "sections_key": "cmr_sections",
        "phase_name": "cmr_checked",
    },
    "fns": {
        "prompt_name": "qc_fns_check",
        "model_config_key": "fns_check_model",
        "fallback_classification": "fns_silent",
        "result_key": "_fns_check",
        "sections_key": "fns_sections",
        "phase_name": "fns_checked",
    },
    "cfr": {
        "prompt_name": "qc_cfr_check",
        "model_config_key": "cfr_check_model",
        "fallback_classification": "cfr_silent",
        "result_key": "_cfr_check",
        "sections_key": "cfr_sections",
        "phase_name": "cfr_checked",
    },
}


@with_rate_limit_retry()
def _do_crosscheck_call(claude, model: str, system_prompt: str,
                        user_message: str):
    """Single Anthropic message call for a cross-check row.

    Wrapped with retry so transient rate-limit / overload errors don't kill
    a multi-row check. Per QC F7 — cross-checks previously had zero retry
    coverage.
    """
    return claude.messages.create(
        model=model,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )


def run_source_check(source: str, analysis_dir: Path,
                     row_indices: list[int] = None,
                     config: configparser.ConfigParser = None) -> list[dict]:
    """Run a CMR / FNS / CFR cross-check on investigated findings.

    For each Partial/Gap finding (or row in `row_indices`), searches the
    chosen source for the policy topic and asks Haiku to classify whether
    the source addresses it (`{source}_covers_topic` / `{source}_silent` /
    `{source}_differs`). Result is attached to the finding under the
    source-specific key (`_cmr_check`, `_fns_check`, `_cfr_check`).

    Args:
        source: One of "cmr", "fns", "cfr".
        analysis_dir: Path to the analysis directory.
        row_indices: Optional list of 1-based row indices. Defaults to
                     all Partial/Gap findings.
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of updated finding dicts with the source-specific key added.
    """
    if source not in SOURCE_CHECK_CONFIG:
        raise ValueError(
            f"Unknown source {source!r}; valid sources are "
            f"{list(SOURCE_CHECK_CONFIG)}"
        )
    spec = SOURCE_CHECK_CONFIG[source]

    if config is None:
        config = load_config()

    model = config.get("qc_analyzer", spec["model_config_key"],
                       fallback="claude-haiku-4-5-20251001")
    prompt = load_prompt(spec["prompt_name"], with_preamble=True)

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    clients = create_client(source=source)

    # Default to Partial/Gap findings if no indices given
    if row_indices is None:
        all_findings = load_all_findings(analysis_dir)
        row_indices = [
            f["row_index"] for f in all_findings
            if f.get("coverage") in ("Partial", "Gap")
        ]

    source_programs = _load_filters(config)[source]["include"] or None

    search_kwargs = {
        "collection": "sections",
        "programs": source_programs,
        "top_n": 5,
        "threshold": 0.0,
    }

    cost_stage = f"{source}_check"
    cost_tracker = Tracker(stages=[cost_stage])

    start_time = time.time()
    results = []
    for row_idx in row_indices:
        finding = load_finding(analysis_dir, row_idx)
        if not finding:
            continue

        query = finding.get("policy_issues", "")
        if not query:
            continue

        search_response = search_with_client(query, clients, **search_kwargs)

        formatted = format_results_for_prompt(
            search_response["results"], source
        )
        user_message = _build_crosscheck_user_message(
            finding, formatted, source.upper()
        )

        response = _do_crosscheck_call(claude, model, prompt, user_message)
        cost_tracker.record(cost_stage, model, response.usage)

        text = response.content[0].text.strip()
        check_result = extract_json(
            text, fallback_classification=spec["fallback_classification"]
        )

        check_block = {
            "classification": check_result.get(
                "classification", spec["fallback_classification"]
            ),
            spec["sections_key"]: check_result.get(spec["sections_key"], []),
            "note": check_result.get("note", ""),
        }

        finding[spec["result_key"]] = check_block
        save_finding(analysis_dir, row_idx, finding)
        results.append(finding)

    elapsed = round(time.time() - start_time, 1)

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"][spec["phase_name"]] = True
    if "cost" not in meta:
        meta["cost"] = {}
    stage_data = cost_tracker.by_stage()[cost_stage]
    meta["cost"][cost_stage] = round(stage_data["cost"], 4)
    meta[f"{cost_stage}_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(results),
        "model": model,
        "tokens_in": stage_data["input_tokens"],
        "tokens_out": stage_data["output_tokens"],
        "cost": round(stage_data["cost"], 4),
    }
    save_meta(analysis_dir, meta)

    return results


