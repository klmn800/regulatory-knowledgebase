"""
QC Gap Analyzer — Identify OLG guidance gaps from QC error findings.

Reads monthly QC error report CSVs and analyzes each finding against
the DTA Online Guide (OLG) to determine whether adequate policy and
procedure guidance exists. Two-call architecture:

  Call 1 (Haiku):  Extractor — distill abstract policy/procedure
                   issues from QC finding narratives.
  Call 2 (Sonnet): Judge — agentic OLG search with iterative tool
                   use. Assesses coverage as Adequate/Partial/Gap.

Output: original CSV with appended analysis columns.

Usage:
    python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv
    python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --sample 4
    python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --rows 1,9,10,15
    python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --dry-run
    python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --resume
"""

import argparse
import configparser
import csv
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rag.query import create_client, search_with_client


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


# ============================================================
# COST TRACKING
# ============================================================

# Per-million-token rates (USD)
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250805": {"input": 5.00, "output": 25.00},
}


class CostTracker:
    """Accumulate API token usage and calculate costs."""

    def __init__(self):
        self.extractor_input = 0
        self.extractor_output = 0
        self.judge_input = 0
        self.judge_output = 0
        self.extractor_model = None
        self.judge_model = None

    def add_extractor(self, response):
        self.extractor_input += response.usage.input_tokens
        self.extractor_output += response.usage.output_tokens

    def add_judge(self, response):
        self.judge_input += response.usage.input_tokens
        self.judge_output += response.usage.output_tokens

    def _cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = MODEL_PRICING.get(model, {"input": 3.00, "output": 15.00})
        return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000

    def extractor_cost(self) -> float:
        return self._cost(self.extractor_model, self.extractor_input, self.extractor_output)

    def judge_cost(self) -> float:
        return self._cost(self.judge_model, self.judge_input, self.judge_output)

    def total_cost(self) -> float:
        return self.extractor_cost() + self.judge_cost()

    def total_input(self) -> int:
        return self.extractor_input + self.judge_input

    def total_output(self) -> int:
        return self.extractor_output + self.judge_output

    def summary(self) -> str:
        lines = [
            f"  Cost breakdown:",
            f"    Extractor ({self.extractor_model}):",
            f"      Input:  {self.extractor_input:>10,} tokens",
            f"      Output: {self.extractor_output:>10,} tokens",
            f"      Cost:   ${self.extractor_cost():>8.4f}",
            f"    Judge ({self.judge_model}):",
            f"      Input:  {self.judge_input:>10,} tokens",
            f"      Output: {self.judge_output:>10,} tokens",
            f"      Cost:   ${self.judge_cost():>8.4f}",
            f"    Total:",
            f"      Input:  {self.total_input():>10,} tokens",
            f"      Output: {self.total_output():>10,} tokens",
            f"      Cost:   ${self.total_cost():>8.4f}",
        ]
        return "\n".join(lines)


# ============================================================
# TRACE LOGGING
# ============================================================

class TraceLogger:
    """Captures the full reasoning trace for each row — every API call,
    tool use, search result, and intermediate reasoning step. Writes
    one JSONL file alongside the output CSV for post-hoc review."""

    def __init__(self, trace_path: Path):
        self.trace_path = trace_path
        self.current_row = None
        self._logger = logging.getLogger("qc_trace")
        self._logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(trace_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)
        self._logger.propagate = False

    def start_row(self, row_index: int, review_number: str, tao: str):
        self.current_row = {
            "row_index": row_index,
            "review_number": review_number,
            "tao": tao,
            "timestamp_start": datetime.now().isoformat(),
            "extractor": None,
            "seed_search": None,
            "judge": None,
            "final_result": None,
        }

    def log_extractor(self, input_text: str, response_text: str,
                      parsed_result: dict, tokens_in: int, tokens_out: int):
        self.current_row["extractor"] = {
            "input": input_text,
            "raw_response": response_text,
            "parsed": parsed_result,
            "tokens": {"input": tokens_in, "output": tokens_out},
        }

    def log_seed_search(self, queries: list[str], result_count: int,
                        results_summary: list[dict]):
        self.current_row["seed_search"] = {
            "queries": queries,
            "total_results": result_count,
            "results": results_summary,
        }

    def start_judge(self, user_message: str, tokens_in: int, tokens_out: int):
        self.current_row["judge"] = {
            "initial_prompt_length": len(user_message),
            "turns": [],
            "total_tokens": {"input": tokens_in, "output": tokens_out},
        }

    def log_judge_turn(self, turn_number: int, reasoning_text: str,
                       tool_calls: list[dict], tool_results: list[dict],
                       tokens_in: int, tokens_out: int, stop_reason: str):
        turn = {
            "turn": turn_number,
            "stop_reason": stop_reason,
            "tokens": {"input": tokens_in, "output": tokens_out},
            "reasoning": reasoning_text,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
        }
        self.current_row["judge"]["turns"].append(turn)
        total = self.current_row["judge"]["total_tokens"]
        total["input"] += tokens_in
        total["output"] += tokens_out

    def log_final_result(self, result: dict):
        self.current_row["final_result"] = result
        self.current_row["timestamp_end"] = datetime.now().isoformat()

    def flush_row(self):
        if self.current_row:
            self._logger.debug(json.dumps(self.current_row, ensure_ascii=False))
            self.current_row = None


def _summarize_seed_results(results: list[dict]) -> list[dict]:
    """Compact summary of seed search results for the trace."""
    summaries = []
    for r in results:
        meta = r.get("metadata", {})
        summaries.append({
            "id": r.get("id", ""),
            "score": round(r.get("score", 0), 3),
            "page_title": meta.get("page_title", meta.get("title", "")),
            "section_heading": meta.get("section_heading", ""),
            "url": meta.get("url", ""),
            "text_preview": r.get("text", "")[:200],
        })
    return summaries


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


def format_olg_results_for_prompt(results: list[dict]) -> str:
    """Format OLG search results for inclusion in a prompt."""
    if not results:
        return "No OLG matches found."

    parts = []
    for i, result in enumerate(results):
        meta = result["metadata"]
        page_title = meta.get("page_title", meta.get("title", ""))
        heading = meta.get("section_heading", "")
        breadcrumb = meta.get("breadcrumb", "")
        url = meta.get("url", "")
        score = result["score"]
        text = result["text"][:1000]

        header = f"[OLG Match {i+1}] Score: {score:.2f}"
        if page_title:
            header += f" | Page: {page_title}"
        if heading:
            header += f" | Section: {heading}"
        if breadcrumb:
            header += f"\n  Path: {breadcrumb}"
        if url:
            header += f"\n  URL: {url}"

        parts.append(f"{header}\n{text}")
        if len(result["text"]) > 1000:
            parts.append("... (truncated)")
        parts.append("")

    return "\n".join(parts)


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


def write_output_csv(fieldnames: list[str], rows: list[dict],
                     filepath: Path) -> None:
    """Write output CSV with original + appended columns."""
    all_fields = fieldnames + APPENDED_COLUMNS
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# CHECKPOINT / RESUME
# ============================================================

def save_checkpoint(processed_indices: list[int], output_rows: list[dict],
                    source_file: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "source_file": source_file,
        "processed_indices": processed_indices,
        "row_count": len(output_rows),
        "timestamp": datetime.now().isoformat(),
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def load_checkpoint() -> dict | None:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


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
                  cost_tracker: CostTracker = None,
                  trace: TraceLogger = None) -> dict:
    """Call 1: Extract policy issues and search queries from a QC finding."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=400,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            if cost_tracker:
                cost_tracker.add_extractor(response)
            text = response.content[0].text.strip()
            parsed = extract_json(text, fallback_classification="Partial")
            if trace:
                trace.log_extractor(
                    input_text=user_message,
                    response_text=text,
                    parsed_result=parsed,
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens,
                )
            return parsed
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"\n    Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except anthropic.APIError as e:
            if attempt < max_retries - 1:
                print(f"\n    API error: {e}, retrying...")
                time.sleep(5)
            else:
                return {
                    "policy_issues": "Extraction failed due to API error.",
                    "search_queries": [user_message[:200]],
                }


# ============================================================
# SEED SEARCH
# ============================================================

def run_seed_searches(queries: list[str], olg_clients: dict,
                      results_per_query: int = 5) -> list[dict]:
    """Run extractor's queries against OLG and deduplicate results."""
    seen_ids = set()
    all_results = []

    for query in queries:
        if not query or not query.strip():
            continue
        response = search_with_client(
            query, olg_clients,
            collection="sections",
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

SEARCH_OLG_TOOL = {
    "name": "search_olg",
    "description": (
        "Search the Massachusetts DTA Online Guide (OLG) for policy content. "
        "Returns the most relevant sections matching your query. "
        "Try different queries to search from different angles: specific policy "
        "terms, BEACON procedures, broader topic areas, synonyms, related topics."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query for OLG content",
            },
        },
        "required": ["query"],
    },
}


def run_judge(row: dict, extractor_result: dict, seed_results: list[dict],
              olg_clients: dict, client: anthropic.Anthropic,
              model: str, system_prompt: str,
              max_searches: int = 10,
              results_per_search: int = 5,
              cost_tracker: CostTracker = None,
              trace: TraceLogger = None) -> dict:
    """Call 2: Agentic OLG coverage assessment with iterative search."""

    seed_formatted = format_olg_results_for_prompt(seed_results)
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

    if trace:
        trace.start_judge(user_message, tokens_in=0, tokens_out=0)

    for turn in range(max_turns):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
                tools=[SEARCH_OLG_TOOL],
            )
            if cost_tracker:
                cost_tracker.add_judge(response)
        except anthropic.RateLimitError:
            print(f"\n    Rate limited, waiting 60s...")
            time.sleep(60)
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=messages,
                    tools=[SEARCH_OLG_TOOL],
                )
                if cost_tracker:
                    cost_tracker.add_judge(response)
            except anthropic.APIError as e:
                return {
                    "coverage": "Partial",
                    "olg_references": [],
                    "gap_description": f"Judge API error: {e}",
                    "confidence": "LOW",
                    "reasoning": "Analysis incomplete due to API error.",
                    "searches_performed": searches_performed,
                    "all_search_queries": all_search_queries,
                }
        except anthropic.APIError as e:
            return {
                "coverage": "Partial",
                "olg_references": [],
                "gap_description": f"Judge API error: {e}",
                "confidence": "LOW",
                "reasoning": "Analysis incomplete due to API error.",
                "searches_performed": searches_performed,
                "all_search_queries": all_search_queries,
            }

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
                        top_n=results_per_search,
                        threshold=0.0,
                    )

                    formatted = format_olg_results_for_prompt(
                        search_response["results"]
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

            if trace:
                trace.log_judge_turn(
                    turn_number=turn + 1,
                    reasoning_text=reasoning_text,
                    tool_calls=trace_tool_calls,
                    tool_results=trace_tool_results,
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens,
                    stop_reason="tool_use",
                )

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            continue

        if trace:
            trace.log_judge_turn(
                turn_number=turn + 1,
                reasoning_text=reasoning_text,
                tool_calls=[],
                tool_results=[],
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                stop_reason=response.stop_reason,
            )

        result = extract_json(reasoning_text, fallback_classification="Partial")
        result["searches_performed"] = searches_performed
        result["all_search_queries"] = all_search_queries
        return result

    return {
        "coverage": "Partial",
        "olg_references": [],
        "gap_description": "Judge exhausted maximum turns without conclusion.",
        "confidence": "LOW",
        "reasoning": "Maximum conversation turns reached.",
        "searches_performed": searches_performed,
        "all_search_queries": all_search_queries,
    }


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

    cost_tracker = CostTracker()
    cost_tracker.extractor_model = extractor_model

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
    meta["cost"]["extractor"] = round(cost_tracker.extractor_cost(), 4)
    meta["extract_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(findings),
        "model": extractor_model,
        "tokens_in": cost_tracker.extractor_input,
        "tokens_out": cost_tracker.extractor_output,
        "cost": round(cost_tracker.extractor_cost(), 4),
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

    cost_tracker = CostTracker()
    cost_tracker.judge_model = judge_model

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
        )

        # Judge
        judge_result = run_judge(
            original_row, extractor_result, seed_results, olg_clients,
            claude, judge_model, judge_prompt,
            max_searches=max_judge_searches,
            results_per_search=olg_results_per_search,
            cost_tracker=cost_tracker,
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
    meta["cost"]["judge"] = round(cost_tracker.judge_cost(), 4)
    meta["investigate_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(results),
        "model": judge_model,
        "tokens_in": cost_tracker.judge_input,
        "tokens_out": cost_tracker.judge_output,
        "cost": round(cost_tracker.judge_cost(), 4),
    }
    save_meta(analysis_dir, meta)

    return results


# ============================================================
# CROSS-CHECK FUNCTIONS (CMR / FNS)
# ============================================================

def _format_source_results_for_prompt(results: list[dict], source: str) -> str:
    """Format CMR or FNS search results for inclusion in a cross-check prompt."""
    if not results:
        return f"No {source.upper()} matches found."

    parts = []
    for i, result in enumerate(results):
        meta = result["metadata"]
        if source == "cmr":
            sec_num = meta.get("section_number", "")
            sec_title = meta.get("section_title", "")
            label = f"{sec_num} {sec_title}".strip()
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


def run_cmr_check(analysis_dir: Path, row_indices: list[int] = None,
                  config: configparser.ConfigParser = None) -> list[dict]:
    """Run CMR cross-check on investigated findings.

    Args:
        analysis_dir: Path to the analysis directory.
        row_indices: Optional list of 1-based row indices. Defaults to
                     all Partial/Gap findings.
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of updated finding dicts with _cmr_check added.
    """
    if config is None:
        config = load_config()

    model = config.get("qc_analyzer", "cmr_check_model",
                       fallback="claude-haiku-4-5-20251001")
    prompt = load_prompt("qc_cmr_check", with_preamble=True)

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    cmr_clients = create_client(source="cmr")

    # Default to Partial/Gap findings if no indices given
    if row_indices is None:
        all_findings = load_all_findings(analysis_dir)
        row_indices = [
            f["row_index"] for f in all_findings
            if f.get("coverage") in ("Partial", "Gap")
        ]

    results = []
    for row_idx in row_indices:
        finding = load_finding(analysis_dir, row_idx)
        if not finding:
            continue

        # Search CMR using the finding's policy issues
        query = finding.get("policy_issues", "")
        if not query:
            continue

        search_response = search_with_client(
            query, cmr_clients,
            collection="sections",
            top_n=5,
            threshold=0.0,
        )

        formatted = _format_source_results_for_prompt(
            search_response["results"], "cmr"
        )
        user_message = _build_crosscheck_user_message(finding, formatted, "CMR")

        response = claude.messages.create(
            model=model,
            max_tokens=500,
            system=prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        text = response.content[0].text.strip()
        check_result = extract_json(text, fallback_classification="cmr_silent")

        # Normalize the result
        cmr_check = {
            "classification": check_result.get("classification", "cmr_silent"),
            "cmr_sections": check_result.get("cmr_sections", []),
            "note": check_result.get("note", ""),
        }

        finding["_cmr_check"] = cmr_check
        save_finding(analysis_dir, row_idx, finding)
        results.append(finding)

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"]["cmr_checked"] = True
    save_meta(analysis_dir, meta)

    return results


def run_fns_check(analysis_dir: Path, row_indices: list[int] = None,
                  config: configparser.ConfigParser = None) -> list[dict]:
    """Run FNS cross-check on investigated findings.

    Args:
        analysis_dir: Path to the analysis directory.
        row_indices: Optional list of 1-based row indices. Defaults to
                     all Partial/Gap findings.
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of updated finding dicts with _fns_check added.
    """
    if config is None:
        config = load_config()

    model = config.get("qc_analyzer", "fns_check_model",
                       fallback="claude-haiku-4-5-20251001")
    prompt = load_prompt("qc_fns_check", with_preamble=True)

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    fns_clients = create_client(source="fns")

    # Default to Partial/Gap findings if no indices given
    if row_indices is None:
        all_findings = load_all_findings(analysis_dir)
        row_indices = [
            f["row_index"] for f in all_findings
            if f.get("coverage") in ("Partial", "Gap")
        ]

    results = []
    for row_idx in row_indices:
        finding = load_finding(analysis_dir, row_idx)
        if not finding:
            continue

        query = finding.get("policy_issues", "")
        if not query:
            continue

        search_response = search_with_client(
            query, fns_clients,
            collection="sections",
            top_n=5,
            threshold=0.0,
        )

        formatted = _format_source_results_for_prompt(
            search_response["results"], "fns"
        )
        user_message = _build_crosscheck_user_message(finding, formatted, "FNS")

        response = claude.messages.create(
            model=model,
            max_tokens=500,
            system=prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        text = response.content[0].text.strip()
        check_result = extract_json(text, fallback_classification="fns_silent")

        fns_check = {
            "classification": check_result.get("classification", "fns_silent"),
            "fns_sections": check_result.get("fns_sections", []),
            "note": check_result.get("note", ""),
        }

        finding["_fns_check"] = fns_check
        save_finding(analysis_dir, row_idx, finding)
        results.append(finding)

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"]["fns_checked"] = True
    save_meta(analysis_dir, meta)

    return results


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def analyze_csv(
    csv_path: Path,
    sample: int = None,
    row_indices: list[int] = None,
    dry_run: bool = False,
    resume: bool = False,
) -> None:
    """Run the QC gap analysis pipeline on a CSV file."""
    config = load_config()

    extractor_model = config.get("qc_analyzer", "extractor_model")
    judge_model = config.get("qc_analyzer", "judge_model")
    max_judge_searches = config.getint("qc_analyzer", "max_judge_searches",
                                       fallback=10)
    olg_results_per_search = config.getint("qc_analyzer",
                                           "olg_results_per_search",
                                           fallback=5)
    seed_results_per_query = config.getint("qc_analyzer",
                                           "seed_results_per_query",
                                           fallback=5)

    extractor_prompt = load_prompt("qc_extractor", with_preamble=True)
    judge_prompt = load_prompt("qc_judge", with_preamble=True)

    fieldnames, all_rows = load_csv(csv_path)

    print(f"QC Gap Analyzer")
    print(f"{'=' * 55}")
    print(f"  Source:           {csv_path.name}")
    print(f"  Total rows:       {len(all_rows)}")
    print(f"  Extractor model:  {extractor_model}")
    print(f"  Judge model:      {judge_model}")
    print(f"  Max searches:     {max_judge_searches}")
    print(f"  Results/search:   {olg_results_per_search}")
    print()

    selected = select_rows(all_rows, sample=sample, row_indices=row_indices)
    print(f"  Rows to process:  {len(selected)}")

    if dry_run:
        print(f"\nDry run -- rows that would be processed:\n")
        for idx, row in selected:
            review = row.get("Review Number", "?")
            tao = row.get("TAO", "?")
            determination = row.get("Food Stamp Determination", "?")
            error_type = row.get("Type Of Errors", "").replace(";", ", ").strip(", ")
            amount = row.get("Error Amount", "?")
            finding_preview = row.get("QC Findings", "")[:80]
            print(f"  Row {idx:2d}: Review #{review} | {tao}")
            print(f"          {determination} | ${amount} | {error_type}")
            print(f"          {finding_preview}...")
            print()
        return

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)

    print("\nInitializing OLG search client...")
    olg_clients = create_client(source="olg")
    print("  OLG client ready.\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if sample or row_indices:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        trace_suffix = f"_sample{len(selected)}_{timestamp}"
    else:
        trace_suffix = f"_{datetime.now().strftime('%Y%m%d_%H%M')}"

    trace_path = OUTPUT_DIR / f"{csv_path.stem}_trace{trace_suffix}.jsonl"
    trace = TraceLogger(trace_path)
    print(f"  Trace log:        {trace_path.name}")
    print()

    processed_indices = set()
    output_rows = []
    if resume:
        checkpoint = load_checkpoint()
        if checkpoint and checkpoint.get("source_file") == str(csv_path):
            processed_indices = set(checkpoint["processed_indices"])
            print(f"  Resuming -- {len(processed_indices)} rows already processed")

    start_time = time.time()
    coverage_counts = {"Adequate": 0, "Partial": 0, "Gap": 0}
    cost_tracker = CostTracker()
    cost_tracker.extractor_model = extractor_model
    cost_tracker.judge_model = judge_model

    for progress_idx, (row_idx, row) in enumerate(selected):
        if row_idx in processed_indices:
            continue

        review = row.get("Review Number", "?")
        tao = row.get("TAO", "?")
        pct = (progress_idx + 1) / len(selected) * 100
        print(f"[{progress_idx + 1}/{len(selected)}] ({pct:.0f}%) "
              f"Row {row_idx}: Review #{review} ({tao})")

        findings = row.get("QC Findings", "").strip()
        if not findings:
            print(f"  SKIP: empty QC Findings field")
            continue

        trace.start_row(row_idx, review, tao)

        # === Call 1: Extractor ===
        print(f"  Extractor...", end="", flush=True)
        extractor_input = build_extractor_input(row)
        extractor_result = run_extractor(
            extractor_input, claude, extractor_model, extractor_prompt,
            cost_tracker=cost_tracker, trace=trace,
        )
        policy_issues = extractor_result.get("policy_issues", "extraction failed")
        queries = extractor_result.get("search_queries", [])
        if not isinstance(queries, list):
            queries = [str(queries)]
        extractor_result["search_queries"] = queries
        print(f" {len(queries)} queries")
        print(f"    Issues: {policy_issues[:100]}")

        # === Seed search ===
        print(f"  Seed search...", end="", flush=True)
        seed_results = run_seed_searches(
            queries, olg_clients, results_per_query=seed_results_per_query
        )
        print(f" {len(seed_results)} OLG results")
        trace.log_seed_search(
            queries=queries,
            result_count=len(seed_results),
            results_summary=_summarize_seed_results(seed_results),
        )

        # === Call 2: Judge ===
        print(f"  Judge", end="", flush=True)
        judge_result = run_judge(
            row, extractor_result, seed_results, olg_clients,
            claude, judge_model, judge_prompt,
            max_searches=max_judge_searches,
            results_per_search=olg_results_per_search,
            cost_tracker=cost_tracker,
            trace=trace,
        )
        coverage = judge_result.get("coverage", "Unknown")
        searches = judge_result.get("searches_performed", 0)
        coverage_counts[coverage] = coverage_counts.get(coverage, 0) + 1
        print(f" -> {coverage} ({searches} searches)")

        reasoning = judge_result.get("reasoning", "")
        if reasoning:
            print(f"    {reasoning[:120]}")

        gap_desc = judge_result.get("gap_description", "")
        if gap_desc and coverage != "Adequate":
            print(f"    Gap: {gap_desc[:120]}")

        refs = judge_result.get("olg_references", [])
        if refs:
            ref_str = "; ".join(str(r) for r in refs[:3])
            print(f"    Refs: {ref_str}")

        output_row = build_output_row(row, extractor_result, judge_result)
        output_rows.append(output_row)

        trace.log_final_result({
            "coverage": judge_result.get("coverage", "Unknown"),
            "searches_performed": judge_result.get("searches_performed", 0),
            "olg_references": judge_result.get("olg_references", []),
            "gap_description": judge_result.get("gap_description", ""),
        })
        trace.flush_row()

        processed_indices.add(row_idx)
        save_checkpoint(sorted(processed_indices), output_rows, str(csv_path))
        print()

    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60

    suffix = trace_suffix
    stem = csv_path.stem
    output_path = OUTPUT_DIR / f"{stem}_analyzed{suffix}.csv"
    write_output_csv(fieldnames, output_rows, output_path)

    print(f"{'=' * 55}")
    print(f"Analysis complete! ({elapsed_min:.1f} minutes)")
    print(f"  Rows analyzed: {len(output_rows)}")
    for cov, count in sorted(coverage_counts.items()):
        if count > 0:
            print(f"    {cov:12s} {count}")
    print()
    print(cost_tracker.summary())
    if len(output_rows) > 0:
        print(f"    Avg cost/row: ${cost_tracker.total_cost() / len(output_rows):.4f}")
    print(f"\n  Output: {output_path}")
    print(f"  Trace:  {trace_path}")

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print(f"  Checkpoint cleared.")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze QC error findings against OLG guidance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv
  python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --sample 4
  python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --rows 1,9,10,15
  python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --dry-run
  python programs/qc/qc_analyzer.py programs/qc/inputs/Q2-2025-QC-Report.csv --resume
        """,
    )
    parser.add_argument(
        "csv_path", type=Path,
        help="Path to QC report CSV file",
    )
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Process only the first N rows (for testing)",
    )
    parser.add_argument(
        "--rows", type=str, default=None,
        help="Comma-separated 1-based row indices to process (e.g., 1,9,10,15)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be processed without running",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last checkpoint",
    )
    args = parser.parse_args()

    csv_path = args.csv_path
    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    row_indices = None
    if args.rows:
        row_indices = [int(r.strip()) for r in args.rows.split(",")]

    analyze_csv(
        csv_path=csv_path,
        sample=args.sample,
        row_indices=row_indices,
        dry_run=args.dry_run,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
