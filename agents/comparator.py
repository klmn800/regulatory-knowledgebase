"""
Comparator Agent — Cross-source policy analysis.

Compares FNS Handbook 310 (federal SNAP standard) against the
Massachusetts DTA Online Guide (OLG) to identify gaps, differences,
and missing procedures. Four-layer architecture:

  Layer 0 (Haiku):  Pre-classification — filter out non-policy FNS
                    sections (QC procedures, overviews, glossaries).
  Layer 1 (Haiku):  Bulk triage — classify each FNS section against
                    pre-fetched OLG matches. Fast, cheap.
  Layer 2 (Sonnet): Deep investigation — agentic search of OLG for
                    escalated items. Uses search tool iteratively.
  Layer 3 (Sonnet): CMR cross-check — regulatory context for confirmed
                    gaps. Checks if state regulation requires it.

Output: CSV report with classifications, notes, and action items.

Usage:
    python comparator.py                          # Full run, chapters 7-11
    python comparator.py --chapter 10             # One chapter only
    python comparator.py --classify               # Run Layer 0 classification only
    python comparator.py --classify --force       # Re-classify all sections
    python comparator.py --sync                   # Rebuild JSON from edited CSV
    python comparator.py --layer1-only            # Triage only, skip layers 2-3
    python comparator.py --dry-run                # Show what would be processed
    python comparator.py --resume                 # Resume from last checkpoint
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
from core.claude_code_runner import run_claude_task


def extract_json(text: str, fallback_classification: str = "no_match") -> dict:
    """
    Extract a JSON object from a response that may contain surrounding
    prose or markdown. Tries multiple strategies.
    """
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
        "classification": fallback_classification,
        "confidence": "LOW",
        "note": text[:300],
    }


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.ini"
FNS_PARSED_DIR = PROJECT_ROOT / "data" / "fns" / "parsed_sections"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "data" / "comparator"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
CLASSIFY_CSV = OUTPUT_DIR / "layer0_classifications.csv"
CLASSIFY_JSON = OUTPUT_DIR / "layer0_classifications.json"

# Haiku pricing per million tokens (as of 2025)
PRICING = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
}


class TokenTracker:
    """Tracks API token usage and estimated cost per section and overall."""

    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.section_input = 0
        self.section_output = 0

    def record(self, response):
        self.total_input += response.usage.input_tokens
        self.total_output += response.usage.output_tokens
        self.section_input += response.usage.input_tokens
        self.section_output += response.usage.output_tokens

    def reset_section(self):
        self.section_input = 0
        self.section_output = 0

    def _estimate_cost(self, input_tokens, output_tokens, model=None):
        rates = PRICING.get(model, {"input": 0.80, "output": 4.00})
        return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000

    def section_cost(self, model=None):
        return self._estimate_cost(self.section_input, self.section_output, model)

    def total_cost(self, model=None):
        return self._estimate_cost(self.total_input, self.total_output, model)

    def section_summary(self):
        return f"{self.section_input:,} in / {self.section_output:,} out"

    def total_summary(self, model=None):
        cost = self.total_cost(model)
        return (f"{self.total_input:,} in / {self.total_output:,} out "
                f"(${cost:.4f})")


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_prompt(name: str, with_preamble: bool = False) -> str:
    filepath = PROMPTS_DIR / f"{name}.md"
    with open(filepath, "r", encoding="utf-8") as f:
        prompt = f.read()
    if with_preamble:
        preamble_path = PROMPTS_DIR / "domain_preamble.md"
        with open(preamble_path, "r", encoding="utf-8") as f:
            preamble = f.read()
        prompt = preamble + "\n\n---\n\n" + prompt
    return prompt


# ============================================================
# FNS SECTION LOADING
# ============================================================

def load_fns_sections(chapters: list[int]) -> list[dict]:
    """Load FNS parsed sections for the specified chapters."""
    sections = []
    for filepath in sorted(FNS_PARSED_DIR.glob("*.json")):
        with open(filepath, "r", encoding="utf-8") as f:
            section = json.load(f)
        if section["chapter"] in chapters:
            sections.append(section)
    return sections


# ============================================================
# LAYER 0: PRE-CLASSIFICATION
# ============================================================

CLASSIFY_CSV_COLUMNS = [
    "section", "title", "chapter", "chapter_title", "label", "reason",
]


def _build_section_families(sections: list[dict]) -> dict:
    """Build a lookup of section families: {parent_number: [child_sections]}.
    Also index by section_number for quick parent lookup."""
    by_number = {s["section_number"]: s for s in sections}
    children = {}
    for s in sections:
        parent = s.get("parent_section")
        if parent:
            children.setdefault(parent, []).append(s)
    return by_number, children


def _format_section_context(section: dict, by_number: dict,
                            children: dict) -> str:
    """Format a section with its parent and sibling context for Layer 0."""
    sec_num = section["section_number"]
    parent_num = section.get("parent_section")

    # Find the family: parent + all children of that parent
    family = []
    if parent_num and parent_num in by_number:
        family.append(by_number[parent_num])
        for child in children.get(parent_num, []):
            family.append(child)
    else:
        # This section IS the parent — show it + its children
        family.append(section)
        for child in children.get(sec_num, []):
            family.append(child)

    # Build the context block
    parts = []
    parts.append(f"Chapter {section['chapter']}: {section['chapter_title']}")
    parts.append("")

    if len(family) > 1:
        parts.append("## Full Section (for context — do NOT classify these)")
        parts.append("")
        for member in family:
            m_num = member["section_number"]
            m_title = member["section_title"]
            m_text = member["text"][:1500]
            if m_num == sec_num:
                continue
            parts.append(f"  {m_num}: {m_title}")
            parts.append(f"  {m_text}")
            if len(member["text"]) > 1500:
                parts.append("  ... (truncated)")
            parts.append("")

    parts.append("## Classify This Section")
    parts.append("")
    parts.append(f"Section {sec_num}: {section['section_title']}")
    parts.append("")
    parts.append(section["text"][:3000])
    if len(section["text"]) > 3000:
        parts.append("... (truncated)")

    return "\n".join(parts)


def run_layer0(fns_section: dict, client: anthropic.Anthropic,
               model: str, system_prompt: str,
               by_number: dict = None, children: dict = None) -> dict:
    """Classify a single FNS section as compare/skip/reference."""
    if by_number and children:
        user_message = _format_section_context(
            fns_section, by_number, children)
    else:
        user_message = (
            f"Section {fns_section['section_number']}: "
            f"{fns_section['section_title']}\n"
            f"Chapter {fns_section['chapter']}: "
            f"{fns_section['chapter_title']}\n\n"
            f"{fns_section['text'][:3000]}"
        )
        if len(fns_section["text"]) > 3000:
            user_message += "\n... (truncated)"

    response = client.messages.create(
        model=model,
        max_tokens=200,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()
    result = extract_json(text, fallback_classification="compare")
    if "label" not in result:
        result["label"] = result.pop("classification", "compare")
    if "reason" not in result:
        result["reason"] = result.pop("note", "")
    return result


def classify_sections(chapters: list[int], dry_run: bool = False,
                      force: bool = False) -> None:
    """Run Layer 0 classification on FNS sections. Writes CSV + JSON."""
    config = load_config()
    layer0_model = config.get("comparator", "layer0_model")

    fns_sections = load_fns_sections(chapters)
    print(f"Layer 0: FNS Section Pre-Classification")
    print(f"=" * 50)
    print(f"Chapters: {chapters}")
    print(f"Model: {layer0_model}")
    print(f"Sections loaded: {len(fns_sections)}")

    existing = {}
    if CLASSIFY_CSV.exists() and not force:
        with open(CLASSIFY_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["section"]] = row
        print(f"Existing classifications: {len(existing)}")

    to_classify = [s for s in fns_sections
                   if s["section_number"] not in existing]
    print(f"Sections to classify: {len(to_classify)}")

    if dry_run:
        print("\nDry run — sections that would be classified:")
        for s in to_classify:
            print(f"  {s['section_number']}: {s['section_title']}")
        print(f"\nTotal: {len(to_classify)} sections")
        if existing:
            print(f"Already classified: {len(existing)} (use --force to redo)")
        return

    if not to_classify:
        print("\nAll sections already classified. Use --force to re-classify.")
        return

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    layer0_prompt = load_prompt("layer0_classify")

    by_number, children_map = _build_section_families(fns_sections)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    counts = {"compare": 0, "skip": 0, "reference": 0}
    start_time = time.time()

    for idx, section in enumerate(to_classify):
        sec_num = section["section_number"]
        pct = (idx + 1) / len(to_classify) * 100
        print(f"  [{idx+1}/{len(to_classify)}] ({pct:.0f}%) "
              f"{sec_num}: {section['section_title'][:50]}",
              end="", flush=True)

        result = run_layer0(section, claude, layer0_model, layer0_prompt,
                            by_number, children_map)
        label = result.get("label", "compare")
        reason = result.get("reason", "")
        counts[label] = counts.get(label, 0) + 1

        print(f" -> {label}")

        existing[sec_num] = {
            "section": sec_num,
            "title": section["section_title"],
            "chapter": section["chapter"],
            "chapter_title": section["chapter_title"],
            "label": label,
            "reason": reason,
        }

    _write_classification_files(existing)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 50}")
    print(f"Classification complete! ({elapsed:.1f}s)")
    print(f"  Newly classified: {len(to_classify)}")
    for label, count in sorted(counts.items()):
        print(f"    {label:12s} {count}")
    total_all = len(existing)
    total_compare = sum(1 for r in existing.values() if r["label"] == "compare")
    total_skip = sum(1 for r in existing.values() if r["label"] == "skip")
    total_ref = sum(1 for r in existing.values() if r["label"] == "reference")
    print(f"  Total classifications: {total_all}")
    print(f"    compare:   {total_compare}")
    print(f"    skip:      {total_skip}")
    print(f"    reference: {total_ref}")
    print(f"\n  CSV: {CLASSIFY_CSV}")
    print(f"  JSON: {CLASSIFY_JSON}")


def _write_classification_files(classifications: dict) -> None:
    """Write both CSV and JSON from a {section_number: row_dict} mapping.
    Also saves a timestamped archive copy of the CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sorted_rows = sorted(classifications.values(),
                         key=lambda r: (int(r["chapter"]), r["section"]))

    with open(CLASSIFY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLASSIFY_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(sorted_rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    archive_csv = OUTPUT_DIR / f"layer0_classifications_{timestamp}.csv"
    with open(archive_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLASSIFY_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(sorted_rows)

    json_data = {row["section"]: {"label": row["label"], "reason": row["reason"]}
                 for row in sorted_rows}
    with open(CLASSIFY_JSON, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print(f"  Archive: {archive_csv}")


def load_classifications() -> dict:
    """Load Layer 0 classifications from JSON. Returns {section_number: {label, reason}}."""
    if CLASSIFY_JSON.exists():
        with open(CLASSIFY_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def sync_csv_to_json() -> None:
    """Regenerate JSON from CSV after manual edits."""
    if not CLASSIFY_CSV.exists():
        print(f"No CSV found at {CLASSIFY_CSV}")
        return

    classifications = {}
    with open(CLASSIFY_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            classifications[row["section"]] = row

    json_data = {}
    for sec_num, row in classifications.items():
        json_data[sec_num] = {"label": row["label"], "reason": row["reason"]}

    with open(CLASSIFY_JSON, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    counts = {}
    for entry in json_data.values():
        counts[entry["label"]] = counts.get(entry["label"], 0) + 1

    print(f"Synced {len(json_data)} classifications from CSV to JSON")
    for label, count in sorted(counts.items()):
        print(f"  {label:12s} {count}")
    print(f"\n  JSON: {CLASSIFY_JSON}")


# ============================================================
# RAG RETRIEVAL
# ============================================================

def multi_query_olg(fns_section: dict, olg_clients: dict,
                    max_results: int = 10,
                    similarity_threshold: float = 0.20) -> list[dict]:
    """
    Run multiple RAG queries against OLG for a single FNS section
    to maximize recall. Deduplicate results across queries.
    """
    queries = []

    title = fns_section.get("section_title", "")
    if title:
        queries.append(title)

    text = fns_section.get("text", "")
    sentences = text.split(".")
    substantive = [s.strip() for s in sentences if len(s.strip()) > 40]
    if substantive:
        queries.append(substantive[0][:200])

    chapter_title = fns_section.get("chapter_title", "")
    if chapter_title and title:
        queries.append(f"SNAP {chapter_title} {title}")

    seen_ids = set()
    all_results = []

    for query in queries:
        response = search_with_client(
            query, olg_clients,
            collection="sections",
            exclude_programs=["TAFDC", "EAEDC"],
            top_n=max_results,
            threshold=similarity_threshold,
        )
        for result in response["results"]:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                all_results.append(result)

    all_results.sort(key=lambda r: r["score"], reverse=True)
    return all_results[:max_results]


def query_cmr(fns_section: dict, cmr_clients: dict,
              max_results: int = 5) -> list[dict]:
    """Query CMR for sections relevant to an FNS requirement."""
    title = fns_section.get("section_title", "")
    text = fns_section.get("text", "")
    query = f"{title} {text[:200]}"

    response = search_with_client(
        query, cmr_clients,
        collection="sections",
        program="SNAP",
        top_n=max_results,
    )
    return response["results"]


# ============================================================
# RESULT FORMATTING FOR PROMPTS
# ============================================================

def format_fns_for_prompt(section: dict, fns_by_number: dict = None) -> str:
    """Format an FNS section for inclusion in a prompt.
    If fns_by_number is provided and the section has a parent, includes the
    parent section title for context."""
    lines = [
        f"FNS Section {section['section_number']}: {section['section_title']}",
    ]
    parent_num = section.get("parent_section")
    if parent_num and fns_by_number and parent_num in fns_by_number:
        parent = fns_by_number[parent_num]
        lines.append(f"Parent: {parent_num} {parent['section_title']}")
    lines.append(f"Chapter {section['chapter']}: {section['chapter_title']}")
    lines.append("")
    lines.append(section["text"][:3000])
    if len(section["text"]) > 3000:
        lines.append("... (truncated)")
    return "\n".join(lines)


def format_olg_results_for_prompt(results: list[dict]) -> str:
    """Format OLG search results for inclusion in a prompt."""
    if not results:
        return "No OLG matches found."

    parts = []
    for i, result in enumerate(results):
        meta = result["metadata"]
        page_title = meta.get("page_title", meta.get("title", ""))
        heading = meta.get("section_heading", "")
        score = result["score"]
        text = result["text"][:1000]

        header = f"[OLG Match {i+1}] Score: {score:.2f}"
        if page_title:
            header += f" | Page: {page_title}"
        if heading:
            header += f" | Section: {heading}"

        parts.append(f"{header}\n{text}")
        if len(result["text"]) > 1000:
            parts.append("... (truncated)")
        parts.append("")

    return "\n".join(parts)


def format_cmr_results_for_prompt(results: list[dict]) -> str:
    """Format CMR search results for inclusion in a prompt."""
    if not results:
        return "No CMR matches found."

    parts = []
    for i, result in enumerate(results):
        meta = result["metadata"]
        sec_num = meta.get("section_number", "")
        sec_title = meta.get("section_title", "")
        score = result["score"]
        text = result["text"][:1000]

        header = f"[CMR Match {i+1}] Score: {score:.2f} | {sec_num} {sec_title}"
        parts.append(f"{header}\n{text}")
        if len(result["text"]) > 1000:
            parts.append("... (truncated)")
        parts.append("")

    return "\n".join(parts)


# ============================================================
# LAYER 1: BULK TRIAGE
# ============================================================

def run_layer1(fns_section: dict, olg_results: list[dict],
               client: anthropic.Anthropic, model: str,
               system_prompt: str, fns_by_number: dict = None,
               tracker: TokenTracker = None) -> dict:
    """Run Layer 1 triage on a single FNS section."""
    user_message = (
        f"## FNS Requirement\n\n"
        f"{format_fns_for_prompt(fns_section, fns_by_number)}\n\n"
        f"## OLG Matches\n\n"
        f"{format_olg_results_for_prompt(olg_results)}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    if tracker:
        tracker.record(response)

    text = response.content[0].text.strip()
    return extract_json(text, fallback_classification="no_match")


# ============================================================
# LAYER 2: DEEP INVESTIGATION
# ============================================================

def lookup_fns_section(section_number: str) -> dict | None:
    """Load a single FNS section by number from parsed JSON files."""
    normalized = section_number.replace(".", "_")
    matches = list(FNS_PARSED_DIR.glob(f"ch*_{normalized}.json"))
    if not matches:
        return None
    with open(matches[0], "r", encoding="utf-8") as f:
        return json.load(f)


LOOKUP_FNS_TOOL = {
    "name": "lookup_fns_section",
    "description": (
        "Look up a specific FNS Handbook 310 section by its number. "
        "Use this when the section you're analyzing cross-references "
        "another FNS section (e.g., 'See Section 512'). Returns the "
        "full text of that section."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "section_number": {
                "type": "string",
                "description": "The FNS section number to look up (e.g., '512', '1021.1')",
            },
        },
        "required": ["section_number"],
    },
}

SEARCH_OLG_TOOL = {
    "name": "search_olg",
    "description": (
        "Search the Massachusetts DTA Online Guide (OLG) for SNAP policy content. "
        "Returns the most relevant sections. Use different queries to search "
        "from different angles — try synonyms, broader/narrower terms, "
        "specific policy language, or BEACON system references."
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


def run_layer2(fns_section: dict, layer1_result: dict,
               olg_clients: dict, client: anthropic.Anthropic,
               model: str, system_prompt: str,
               max_results: int = 10,
               fns_by_number: dict = None,
               tracker: TokenTracker = None,
               olg_results: list[dict] = None) -> dict:
    """
    Run Layer 2 agentic investigation. Claude can use the search_olg
    tool to query the OLG and lookup_fns_section to follow cross-references.
    """
    parts = [
        f"## FNS Requirement\n\n"
        f"{format_fns_for_prompt(fns_section, fns_by_number)}\n\n"
        f"## Layer 1 Finding\n\n"
        f"Classification: {layer1_result['classification']}\n"
        f"Confidence: {layer1_result['confidence']}\n"
        f"Note: {layer1_result['note']}",
    ]
    if olg_results:
        parts.append(
            f"\n\n## OLG Content Already Found\n\n"
            f"{format_olg_results_for_prompt(olg_results)}\n\n"
            f"The above OLG matches were already retrieved. Use them as a "
            f"starting point — search for additional angles the initial "
            f"queries may have missed."
        )
    else:
        parts.append(
            "\n\nPlease investigate this further using the search_olg tool."
        )
    user_message = "".join(parts)

    messages = [{"role": "user", "content": user_message}]
    tools = [SEARCH_OLG_TOOL, LOOKUP_FNS_TOOL]

    max_turns = 15
    for _ in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system_prompt,
            messages=messages,
            tools=tools,
        )
        if tracker:
            tracker.record(response)

        if response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type != "tool_use":
                    continue

                if block.name == "search_olg":
                    query = block.input.get("query", "")
                    search_response = search_with_client(
                        query, olg_clients,
                        collection="sections",
                        program="SNAP",
                        top_n=max_results,
                    )
                    formatted = format_olg_results_for_prompt(
                        search_response["results"]
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": formatted,
                    })

                elif block.name == "lookup_fns_section":
                    sec_num = block.input.get("section_number", "")
                    fns_ref = lookup_fns_section(sec_num)
                    if fns_ref:
                        formatted = format_fns_for_prompt(fns_ref, fns_by_number)
                    else:
                        formatted = f"Section {sec_num} not found."
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

        return extract_json(text, fallback_classification="confirmed_gap")

    return {
        "classification": "confirmed_gap",
        "confidence": "LOW",
        "note": "Layer 2 exhausted maximum tool-use turns without conclusion.",
        "olg_pages_found": [],
        "searches_performed": max_turns,
    }


# ============================================================
# LAYER 2 (CLAUDE CODE): CLI-BASED INVESTIGATION
# ============================================================

RESULTS_DIR = OUTPUT_DIR / "results"
SESSIONS_DIR = OUTPUT_DIR / "sessions"


def run_layer2_claude_code(
    fns_section: dict,
    layer1_result: dict,
    olg_results: list[dict],
    fns_by_number: dict = None,
    windowed: bool = False,
) -> dict:
    """
    Run Layer 2 investigation via Claude Code CLI instead of the API.

    Builds a self-contained prompt with domain preamble, investigation
    instructions, and all context. The Claude Code session uses the
    project's query.py and file system to search autonomously.

    Returns the parsed result dict, or an error fallback.
    """
    domain_preamble = load_prompt("domain_preamble")
    l2_instructions = load_prompt("layer2_claude_code")

    sec_num = fns_section["section_number"]
    result_file = RESULTS_DIR / f"{sec_num}.json"

    fns_block = format_fns_for_prompt(fns_section, fns_by_number)
    olg_block = format_olg_results_for_prompt(olg_results)

    l1_summary = (
        f"Layer 1 Classification: {layer1_result['classification']}\n"
        f"Confidence: {layer1_result['confidence']}\n"
        f"Note: {layer1_result['note']}"
    )

    prompt = (
        f"{domain_preamble}\n\n"
        f"---\n\n"
        f"{l2_instructions}\n\n"
        f"---\n\n"
        f"## FNS Requirement\n\n"
        f"{fns_block}\n\n"
        f"## Layer 1 Finding\n\n"
        f"{l1_summary}\n\n"
        f"## OLG Content Already Found (Layer 1)\n\n"
        f"{olg_block}\n\n"
        f"The above OLG matches were already retrieved. Use them as a "
        f"starting point — search for additional angles the initial "
        f"queries may have missed.\n\n"
        f"## Your Task\n\n"
        f"Investigate whether the OLG adequately covers this FNS requirement.\n"
        f"Write your result as JSON to: {result_file}\n"
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    task_result = run_claude_task(
        prompt=prompt,
        result_file=result_file,
        timeout=1800,
        cwd=PROJECT_ROOT,
        log_dir=SESSIONS_DIR,
        task_id=f"L2_{sec_num}",
        windowed=windowed,
    )

    if task_result["success"]:
        result = task_result["result"]
        result["_elapsed"] = task_result["elapsed"]
        result["_session_id"] = task_result.get("session_id")
        # Write session_id back to the result file for compile_results()
        if task_result.get("session_id"):
            result_file.write_text(
                json.dumps(result, indent=4), encoding="utf-8"
            )
        return result

    return {
        "classification": "error",
        "confidence": "LOW",
        "note": f"Claude Code session failed: {task_result['error']}",
        "olg_pages_found": [],
        "searches_performed": 0,
        "_elapsed": task_result["elapsed"],
        "_error": task_result["error"],
    }


# ============================================================
# LAYER 2: UNIFIED DISPATCH
# ============================================================

def investigate_section(
    fns_section: dict,
    layer1_result: dict,
    olg_results: list[dict],
    engine: str = "api",
    olg_clients: dict = None,
    client: anthropic.Anthropic = None,
    model: str = None,
    system_prompt: str = None,
    max_results: int = 10,
    fns_by_number: dict = None,
    tracker: TokenTracker = None,
    windowed: bool = False,
) -> dict:
    """
    Run Layer 2 investigation for a single section.

    Checks for a cached result file first (shared for both engines).
    On cache miss, dispatches to the API tool-use loop or Claude Code CLI.
    Writes result to RESULTS_DIR/{section_number}.json for both engines.

    Returns the L2 result dict. Metadata fields:
        _session_id  — Claude Code session UUID, or "" for API
        _cached      — True if loaded from existing result file
        _elapsed     — Wall-clock seconds (fresh Claude Code runs)
        _error       — Error message (failed runs only)
    """
    sec_id = fns_section["section_number"]
    result_file = RESULTS_DIR / f"{sec_id}.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Check cache — shared for both engines
    if result_file.exists():
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            cached["_cached"] = True
            return cached
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt file — fall through to fresh run

    # Dispatch to engine
    if engine == "claude-code":
        result = run_layer2_claude_code(
            fns_section, layer1_result, olg_results,
            fns_by_number=fns_by_number,
            windowed=windowed,
        )
        # run_layer2_claude_code() writes the result file and sets
        # _session_id, _elapsed, _error
    else:
        result = run_layer2(
            fns_section, layer1_result, olg_clients,
            client, model, system_prompt,
            max_results=max_results,
            fns_by_number=fns_by_number,
            tracker=tracker,
            olg_results=olg_results,
        )
        result["_session_id"] = ""
        result_file.write_text(
            json.dumps(result, indent=4), encoding="utf-8"
        )

    result["_cached"] = False
    return result


# ============================================================
# LAYER 3: CMR CROSS-CHECK
# ============================================================

def run_layer3(fns_section: dict, layer2_result: dict,
               cmr_results: list[dict], client: anthropic.Anthropic,
               model: str, system_prompt: str,
               fns_by_number: dict = None,
               tracker: TokenTracker = None) -> dict:
    """Run Layer 3 CMR cross-check for a confirmed gap."""
    user_message = (
        f"## FNS Requirement\n\n"
        f"{format_fns_for_prompt(fns_section, fns_by_number)}\n\n"
        f"## Gap Finding (Layer 2)\n\n"
        f"Classification: {layer2_result['classification']}\n"
        f"Note: {layer2_result['note']}\n\n"
        f"## CMR Matches\n\n"
        f"{format_cmr_results_for_prompt(cmr_results)}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    if tracker:
        tracker.record(response)

    text = response.content[0].text.strip()
    return extract_json(text, fallback_classification="state_silent")


# ============================================================
# CHECKPOINT / RESUME
# ============================================================

def save_checkpoint(results: list[dict], processed_ids: set[str]) -> None:
    """Save progress for resume capability."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "processed_ids": sorted(processed_ids),
        "result_count": len(results),
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def load_checkpoint() -> set[str]:
    """Load previously processed section IDs."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("processed_ids", []))
    return set()


# ============================================================
# CSV OUTPUT
# ============================================================

CSV_COLUMNS = [
    "fns_chapter",
    "fns_section",
    "fns_title",
    "fns_summary",
    "classification",
    "confidence",
    "olg_matches",
    "olg_urls",
    "layer1_note",
    "layer2_note",
    "layer3_note",
    "cmr_section",
    "action_needed",
    "priority",
    "session_id",
    "tokens_in",
    "tokens_out",
    "est_cost",
]


def _build_display_title(section: dict, fns_by_number: dict = None) -> str:
    """Build a human-readable title that includes parent context for subsections."""
    title = section["section_title"]
    parent_num = section.get("parent_section")
    if parent_num and fns_by_number and parent_num in fns_by_number:
        parent_title = fns_by_number[parent_num]["section_title"]
        title = f"{parent_title} > {title}"
    return title


def build_csv_row(fns_section: dict, layer1: dict,
                  olg_results: list[dict],
                  layer2: dict | None = None,
                  layer3: dict | None = None,
                  fns_by_number: dict = None,
                  tracker: TokenTracker = None) -> dict:
    """Build a CSV row dict from layer results."""
    olg_titles = []
    olg_urls = []
    for r in olg_results[:5]:
        meta = r["metadata"]
        title = meta.get("page_title", meta.get("title", ""))
        url = meta.get("url", "")
        if title:
            olg_titles.append(title)
        if url:
            olg_urls.append(url)

    final_classification = layer1["classification"]
    final_confidence = layer1["confidence"]
    action = "none"
    priority = "LOW"

    if layer2:
        final_classification = layer2["classification"]
        final_confidence = layer2.get("confidence", final_confidence)

    if layer3:
        action = layer3.get("action_recommended", "investigate")
        priority = layer3.get("priority", "MEDIUM")
    elif final_classification in ("confirmed_gap", "different_standard"):
        action = "investigate"
        priority = "HIGH"
    elif final_classification == "policy_present_procedures_missing":
        action = "write_procedure"
        priority = "MEDIUM"
    elif final_classification == "partial_match":
        action = "update_olg"
        priority = "MEDIUM"

    return {
        "fns_chapter": fns_section["chapter"],
        "fns_section": fns_section["section_number"],
        "fns_title": _build_display_title(fns_section, fns_by_number),
        "fns_summary": fns_section["text"][:200].replace("\n", " "),
        "classification": final_classification,
        "confidence": final_confidence,
        "olg_matches": "; ".join(olg_titles),
        "olg_urls": "; ".join(olg_urls),
        "layer1_note": layer1.get("note", ""),
        "layer2_note": layer2.get("note", "") if layer2 else "",
        "layer3_note": layer3.get("note", "") if layer3 else "",
        "cmr_section": "; ".join(layer3.get("cmr_sections", [])) if layer3 else "",
        "action_needed": action,
        "priority": priority,
        "session_id": layer2.get("_session_id", "") if layer2 else "",
        "tokens_in": tracker.section_input if tracker else "",
        "tokens_out": tracker.section_output if tracker else "",
        "est_cost": f"${tracker.section_cost():.4f}" if tracker else "",
    }


def write_csv(rows: list[dict], filepath: Path) -> None:
    """Write results to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# COMPILE RESULTS FROM RESULT JSONs
# ============================================================

def compile_results(chapters: list[int] = None) -> None:
    """
    Compile individual result JSONs into a CSV.

    Each file in data/comparator/results/{section_number}.json contains
    the Layer 2 verdict for that section (from any engine). This function
    loads them all, enriches with FNS metadata, and produces a comparison CSV.
    """
    if not RESULTS_DIR.exists():
        print(f"No results directory found at {RESULTS_DIR}")
        return

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        print(f"No result files found in {RESULTS_DIR}")
        return

    config = load_config()
    if chapters is None:
        chapters_str = config.get("comparator", "fns_chapters_to_compare",
                                  fallback="7,8,9,10,11")
        chapters = [int(c.strip()) for c in chapters_str.split(",")]

    fns_sections = load_fns_sections(chapters)
    fns_by_number = {s["section_number"]: s for s in fns_sections}

    rows = []
    counts = {}
    errors = 0

    for filepath in result_files:
        sec_num = filepath.stem
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                result = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  WARNING: Could not read {filepath.name}: {e}")
            errors += 1
            continue

        fns_section = fns_by_number.get(sec_num)
        if not fns_section:
            print(f"  WARNING: No FNS section found for {sec_num}, skipping")
            continue

        cls = result.get("classification", "error")
        counts[cls] = counts.get(cls, 0) + 1

        # Read L3 results if persisted
        layer3 = result.get("_layer3")

        action = "none"
        priority = "LOW"
        if layer3:
            action = layer3.get("action_recommended", "investigate")
            priority = layer3.get("priority", "MEDIUM")
        elif cls in ("confirmed_gap", "different_standard"):
            action = "investigate"
            priority = "HIGH"
        elif cls == "policy_present_procedures_missing":
            action = "write_procedure"
            priority = "MEDIUM"
        elif cls == "partial_match":
            action = "update_olg"
            priority = "MEDIUM"

        olg_pages = result.get("olg_pages_found", [])

        row = {
            "fns_chapter": fns_section["chapter"],
            "fns_section": sec_num,
            "fns_title": _build_display_title(fns_section, fns_by_number),
            "fns_summary": fns_section["text"][:200].replace("\n", " "),
            "classification": cls,
            "confidence": result.get("confidence", ""),
            "olg_matches": "; ".join(olg_pages),
            "olg_urls": "",
            "layer1_note": "",
            "layer2_note": result.get("note", ""),
            "layer3_note": layer3.get("note", "") if layer3 else "",
            "cmr_section": "; ".join(layer3.get("cmr_sections", [])) if layer3 else "",
            "action_needed": action,
            "priority": priority,
            "session_id": result.get("_session_id", ""),
            "tokens_in": "",
            "tokens_out": "",
            "est_cost": "$0.0000",
        }
        rows.append(row)

    rows.sort(key=lambda r: (int(r["fns_chapter"]), r["fns_section"]))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = OUTPUT_DIR / f"comparison_compiled_{timestamp}.csv"
    write_csv(rows, csv_path)

    print(f"\nCompile Results")
    print(f"{'=' * 50}")
    print(f"  Result files found: {len(result_files)}")
    print(f"  Rows written: {len(rows)}")
    if errors:
        print(f"  Errors: {errors}")
    print(f"\n  Classifications:")
    for cls, count in sorted(counts.items()):
        print(f"    {cls:35s} {count}")
    print(f"\n  Report: {csv_path}")


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def run_comparison(
    chapters: list[int],
    layer1_only: bool = False,
    dry_run: bool = False,
    resume: bool = False,
    section_filter: set[str] = None,
    engine: str = "api",
    windowed: bool = False,
) -> None:
    """Run the full comparison pipeline."""
    config = load_config()

    layer1_model = config.get("comparator", "layer1_model")
    layer2_model = config.get("comparator", "layer2_model")
    layer3_model = config.get("comparator", "layer3_model")
    similarity_threshold = config.getfloat("comparator", "olg_similarity_threshold",
                                           fallback=0.20)
    olg_max_results = config.getint("comparator", "olg_max_results", fallback=10)
    cmr_max_results = config.getint("comparator", "cmr_max_results", fallback=5)
    escalate_conf = config.get("comparator", "escalate_confidence",
                               fallback="MEDIUM,LOW")
    escalate_levels = set(s.strip() for s in escalate_conf.split(","))

    layer1_prompt = load_prompt("layer1_triage", with_preamble=True)
    layer2_prompt = load_prompt("layer2_investigation", with_preamble=True)
    layer3_prompt = load_prompt("layer3_validation", with_preamble=True)

    print(f"SNAP Policy Comparator — FNS vs OLG")
    print(f"=" * 50)
    print(f"FNS chapters: {chapters}")
    print(f"Layer 2 engine: {engine}")
    print(f"Layer 1 model: {layer1_model}")
    if engine == "api":
        print(f"Layer 2 model: {layer2_model}")
    else:
        print(f"Layer 2: Claude Code CLI (subscription)")
    print(f"Layer 3 model: {layer3_model}")
    print(f"OLG similarity threshold: {similarity_threshold}")
    print(f"Escalate on confidence: {escalate_levels}")
    print()

    fns_sections = load_fns_sections(chapters)
    fns_by_number = {s["section_number"]: s for s in fns_sections}
    print(f"Loaded {len(fns_sections)} FNS sections")

    classifications = load_classifications()
    if classifications:
        before = len(fns_sections)
        unclassified = []
        filtered_sections = []
        for s in fns_sections:
            sec_num = s["section_number"]
            if sec_num not in classifications:
                unclassified.append(sec_num)
                filtered_sections.append(s)
            elif classifications[sec_num]["label"] == "compare":
                filtered_sections.append(s)
        skipped = before - len(filtered_sections)
        print(f"Layer 0 filter: {len(filtered_sections)} compare, "
              f"{skipped} skipped/reference")
        if unclassified:
            print(f"  WARNING: {len(unclassified)} unclassified sections "
                  f"included by default")
        fns_sections = filtered_sections
    else:
        print("No Layer 0 classifications found — processing all sections")
        print("  (Run --classify first to filter non-policy sections)")

    if section_filter:
        fns_sections = [s for s in fns_sections
                        if s["section_number"] in section_filter]
        print(f"Section filter: {len(fns_sections)} sections selected")

    if dry_run:
        print("\nDry run — sections that would be processed:")
        for s in fns_sections:
            print(f"  {s['section_number']}: {s['section_title']}")
        print(f"\nTotal: {len(fns_sections)} sections")
        return

    processed_ids = load_checkpoint() if resume else set()
    if processed_ids:
        print(f"Resuming — {len(processed_ids)} sections already processed")

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)

    print("Initializing RAG clients...")
    olg_clients = create_client(source="olg")
    cmr_clients = create_client(source="cmr") if not layer1_only else None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = []
    layer1_counts = {"match": 0, "partial_match": 0, "no_match": 0, "not_applicable": 0}
    layer2_count = 0
    layer3_count = 0
    tracker = TokenTracker()

    total = len(fns_sections)
    start_time = time.time()

    for idx, fns_section in enumerate(fns_sections):
        sec_id = fns_section["section_number"]

        if sec_id in processed_ids:
            continue

        pct = (idx + 1) / total * 100
        print(f"\n[{idx+1}/{total}] ({pct:.0f}%) {sec_id}: {fns_section['section_title'][:50]}")

        olg_results = multi_query_olg(
            fns_section, olg_clients,
            max_results=olg_max_results,
            similarity_threshold=similarity_threshold,
        )
        print(f"  RAG: {len(olg_results)} OLG matches")

        tracker.reset_section()
        layer1 = run_layer1(fns_section, olg_results, claude,
                            layer1_model, layer1_prompt, fns_by_number,
                            tracker)
        cls = layer1["classification"]
        conf = layer1["confidence"]
        layer1_counts[cls] = layer1_counts.get(cls, 0) + 1
        print(f"  L1: {cls} ({conf}) — {layer1['note'][:80]}")

        layer2 = None
        layer3 = None

        needs_escalation = (
            not layer1_only
            and (cls in ("partial_match", "no_match")
                 or (cls == "match" and conf in escalate_levels))
        )
        skip_escalation = cls in ("not_applicable", "match") and conf == "HIGH"

        if needs_escalation and not skip_escalation:
            layer2_count += 1
            layer2 = investigate_section(
                fns_section, layer1, olg_results,
                engine=engine,
                olg_clients=olg_clients,
                client=claude,
                model=layer2_model,
                system_prompt=layer2_prompt,
                max_results=olg_max_results,
                fns_by_number=fns_by_number,
                tracker=tracker,
                windowed=windowed,
            )

            l2_cls = layer2["classification"]
            searches = layer2.get("searches_performed", "?")
            if layer2.get("_cached"):
                print(f"  L2: {l2_cls} ({searches} searches) — cached")
            else:
                l2_elapsed = layer2.get("_elapsed")
                l2_error = layer2.get("_error")
                if l2_elapsed is not None:
                    status = "OK" if not l2_error else f"FAILED: {l2_error}"
                    print(f"  L2: {l2_cls} ({searches} searches, "
                          f"{l2_elapsed:.0f}s) — {status}")
                else:
                    print(f"  L2: {l2_cls} ({searches} searches)")
                l2_session = layer2.get("_session_id")
                if l2_session:
                    print(f"  L2 session: {l2_session}")
            print(f"  L2: {layer2['note'][:100]}")

            needs_layer3 = l2_cls in (
                "confirmed_gap", "different_standard",
                "policy_present_procedures_missing",
            )
            if needs_layer3 and cmr_clients:
                layer3_count += 1
                print(f"  L3: Checking CMR...")
                cmr_results = query_cmr(fns_section, cmr_clients, cmr_max_results)
                layer3 = run_layer3(fns_section, layer2, cmr_results,
                                    claude, layer3_model, layer3_prompt,
                                    fns_by_number, tracker)
                action = layer3.get("action_recommended", "?")
                priority = layer3.get("priority", "?")
                print(f"  L3: {layer3['classification']} — {action} ({priority})")

                # Persist L3 results into the result JSON
                result_file = RESULTS_DIR / f"{sec_id}.json"
                if result_file.exists():
                    try:
                        data = json.loads(result_file.read_text(encoding="utf-8"))
                        data["_layer3"] = layer3
                        result_file.write_text(
                            json.dumps(data, indent=4), encoding="utf-8"
                        )
                    except (json.JSONDecodeError, OSError):
                        pass

        print(f"  API tokens: {tracker.section_summary()} (${tracker.section_cost():.4f})")

        row = build_csv_row(fns_section, layer1, olg_results, layer2, layer3,
                            fns_by_number, tracker)
        all_rows.append(row)

        processed_ids.add(sec_id)
        save_checkpoint(all_rows, processed_ids)

        if (idx + 1) % 20 == 0:
            interim_path = OUTPUT_DIR / "comparison_interim.csv"
            write_csv(all_rows, interim_path)
            print(f"\n  Interim results saved ({len(all_rows)} rows)")

    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    csv_path = OUTPUT_DIR / f"comparison_{engine}_{timestamp}.csv"
    write_csv(all_rows, csv_path)

    print(f"\n{'=' * 50}")
    print(f"Comparison complete!")
    print(f"{'=' * 50}")
    print(f"  Engine: {engine}")
    print(f"  Sections processed: {len(all_rows)}")
    print(f"  Time: {elapsed_min:.1f} minutes")
    print()
    print(f"  Layer 1 classifications:")
    for cls, count in sorted(layer1_counts.items()):
        print(f"    {cls:25s} {count}")
    print(f"  Escalated to Layer 2: {layer2_count}")
    print(f"  Escalated to Layer 3: {layer3_count}")
    print()
    print(f"  API tokens: {tracker.total_summary()}")
    if engine == "claude-code":
        print(f"  L2 cost: $0 (Claude Code subscription)")
    print(f"  Report: {csv_path}")

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print(f"  Checkpoint cleared.")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Compare FNS Handbook 310 against DTA Online Guide (SNAP).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python comparator.py                              # Full run, chapters 7-11
  python comparator.py --chapter 10                 # One chapter only
  python comparator.py --classify                   # Layer 0: classify sections
  python comparator.py --classify --force           # Re-classify all sections
  python comparator.py --sync                       # Rebuild JSON from edited CSV
  python comparator.py --layer1-only                # Triage only
  python comparator.py --dry-run                    # Preview sections
  python comparator.py --resume                     # Resume interrupted run
  python comparator.py --engine claude-code         # L2 via Claude Code CLI
  python comparator.py --compile                    # Compile result JSONs to CSV
        """,
    )
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Process only this FNS chapter",
    )
    parser.add_argument(
        "--classify", action="store_true",
        help="Run Layer 0 pre-classification only",
    )
    parser.add_argument(
        "--sync", action="store_true",
        help="Regenerate JSON from manually edited CSV",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-classify all sections (with --classify)",
    )
    parser.add_argument(
        "--layer1-only", action="store_true",
        help="Run Layer 1 triage only (no deep investigation)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show sections that would be processed",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--sections", type=str, default=None,
        help="Comma-separated section numbers to process (e.g., '1013.4,1021.1,1042')",
    )
    parser.add_argument(
        "--engine", type=str, default="api", choices=["api", "claude-code"],
        help="Layer 2 engine: 'api' (Anthropic API) or 'claude-code' (CLI sessions)",
    )
    parser.add_argument(
        "--windowed", action="store_true",
        help="Open each Claude Code session in a visible console window (with --engine claude-code)",
    )
    parser.add_argument(
        "--compile", action="store_true",
        help="Compile result JSONs from Claude Code sessions into CSV",
    )
    args = parser.parse_args()

    if args.compile:
        config = load_config()
        if args.chapter:
            chapters = [args.chapter]
        else:
            chapters_str = config.get("comparator", "fns_chapters_to_compare",
                                      fallback="7,8,9,10,11")
            chapters = [int(c.strip()) for c in chapters_str.split(",")]
        compile_results(chapters)
        return

    if args.sync:
        sync_csv_to_json()
        return

    config = load_config()

    if args.chapter:
        chapters = [args.chapter]
    else:
        chapters_str = config.get("comparator", "fns_chapters_to_compare",
                                  fallback="7,8,9,10,11")
        chapters = [int(c.strip()) for c in chapters_str.split(",")]

    section_filter = None
    if args.sections:
        section_filter = set(s.strip() for s in args.sections.split(","))

    if args.classify:
        classify_sections(chapters, dry_run=args.dry_run, force=args.force)
        return

    run_comparison(
        chapters=chapters,
        layer1_only=args.layer1_only,
        dry_run=args.dry_run,
        resume=args.resume,
        section_filter=section_filter,
        engine=args.engine,
        windowed=args.windowed,
    )


if __name__ == "__main__":
    main()
