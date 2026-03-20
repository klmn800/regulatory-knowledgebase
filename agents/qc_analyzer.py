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
    python qc_analyzer.py source_files/Q2-2025-QC-Report.csv
    python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --sample 4
    python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --rows 1,9,10,15
    python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --dry-run
    python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --resume
"""

import argparse
import configparser
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.query import create_client, search_with_client


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.ini"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "data" / "qc_analysis"
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
        preamble_path = PROMPTS_DIR / "domain_preamble.md"
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
    Handles UTF-8 BOM encoding."""
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    return fieldnames, rows


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
                  cost_tracker: CostTracker = None) -> dict:
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
            return extract_json(text, fallback_classification="Partial")
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
              cost_tracker: CostTracker = None) -> dict:
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

        if response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use" and block.name == "search_olg":
                    query = block.input.get("query", "")

                    if searches_performed >= max_searches:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": (
                                f"Search budget exhausted ({searches_performed} "
                                f"searches used). Please provide your final "
                                f"assessment now based on all results seen."
                            ),
                        })
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

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            continue

        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text = block.text.strip()
                break

        result = extract_json(text, fallback_classification="Partial")
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

        # === Call 1: Extractor ===
        print(f"  Extractor...", end="", flush=True)
        extractor_input = build_extractor_input(row)
        extractor_result = run_extractor(
            extractor_input, claude, extractor_model, extractor_prompt,
            cost_tracker=cost_tracker
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

        # === Call 2: Judge ===
        print(f"  Judge", end="", flush=True)
        judge_result = run_judge(
            row, extractor_result, seed_results, olg_clients,
            claude, judge_model, judge_prompt,
            max_searches=max_judge_searches,
            results_per_search=olg_results_per_search,
            cost_tracker=cost_tracker,
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

        processed_indices.add(row_idx)
        save_checkpoint(sorted(processed_indices), output_rows, str(csv_path))
        print()

    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60

    if sample or row_indices:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        suffix = f"_sample{len(selected)}_{timestamp}"
    else:
        suffix = ""

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
  python qc_analyzer.py source_files/Q2-2025-QC-Report.csv
  python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --sample 4
  python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --rows 1,9,10,15
  python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --dry-run
  python qc_analyzer.py source_files/Q2-2025-QC-Report.csv --resume
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
