"""
Comparator Agent — Cross-source policy analysis.

Compares FNS Handbook 310 (federal SNAP standard) against the
Massachusetts DTA Online Guide (OLG) to identify gaps, differences,
and missing procedures. Three-layer architecture:

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
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.query import create_client, search_with_client


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


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_prompt(name: str) -> str:
    filepath = PROMPTS_DIR / f"{name}.md"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


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
            program="SNAP",
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

def format_fns_for_prompt(section: dict) -> str:
    """Format an FNS section for inclusion in a prompt."""
    lines = [
        f"FNS Section {section['section_number']}: {section['section_title']}",
        f"Chapter {section['chapter']}: {section['chapter_title']}",
        "",
        section["text"][:3000],
    ]
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
               system_prompt: str) -> dict:
    """Run Layer 1 triage on a single FNS section."""
    user_message = (
        f"## FNS Requirement\n\n"
        f"{format_fns_for_prompt(fns_section)}\n\n"
        f"## OLG Matches\n\n"
        f"{format_olg_results_for_prompt(olg_results)}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()
    return extract_json(text, fallback_classification="no_match")


# ============================================================
# LAYER 2: DEEP INVESTIGATION
# ============================================================

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
               max_results: int = 10) -> dict:
    """
    Run Layer 2 agentic investigation. Claude can use the search_olg
    tool to query the OLG multiple times.
    """
    user_message = (
        f"## FNS Requirement\n\n"
        f"{format_fns_for_prompt(fns_section)}\n\n"
        f"## Layer 1 Finding\n\n"
        f"Classification: {layer1_result['classification']}\n"
        f"Confidence: {layer1_result['confidence']}\n"
        f"Note: {layer1_result['note']}\n\n"
        f"Please investigate this further using the search_olg tool."
    )

    messages = [{"role": "user", "content": user_message}]

    max_turns = 15
    for _ in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system_prompt,
            messages=messages,
            tools=[SEARCH_OLG_TOOL],
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use" and block.name == "search_olg":
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
# LAYER 3: CMR CROSS-CHECK
# ============================================================

def run_layer3(fns_section: dict, layer2_result: dict,
               cmr_results: list[dict], client: anthropic.Anthropic,
               model: str, system_prompt: str) -> dict:
    """Run Layer 3 CMR cross-check for a confirmed gap."""
    user_message = (
        f"## FNS Requirement\n\n"
        f"{format_fns_for_prompt(fns_section)}\n\n"
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
]


def build_csv_row(fns_section: dict, layer1: dict,
                  olg_results: list[dict],
                  layer2: dict | None = None,
                  layer3: dict | None = None) -> dict:
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
        "fns_title": fns_section["section_title"],
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
    }


def write_csv(rows: list[dict], filepath: Path) -> None:
    """Write results to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def run_comparison(
    chapters: list[int],
    layer1_only: bool = False,
    dry_run: bool = False,
    resume: bool = False,
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

    layer1_prompt = load_prompt("layer1_triage")
    layer2_prompt = load_prompt("layer2_investigation")
    layer3_prompt = load_prompt("layer3_validation")

    print(f"SNAP Policy Comparator — FNS vs OLG")
    print(f"=" * 50)
    print(f"FNS chapters: {chapters}")
    print(f"Layer 1 model: {layer1_model}")
    print(f"Layer 2 model: {layer2_model}")
    print(f"Layer 3 model: {layer3_model}")
    print(f"OLG similarity threshold: {similarity_threshold}")
    print(f"Escalate on confidence: {escalate_levels}")
    print()

    fns_sections = load_fns_sections(chapters)
    print(f"Loaded {len(fns_sections)} FNS sections")

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

        layer1 = run_layer1(fns_section, olg_results, claude,
                            layer1_model, layer1_prompt)
        cls = layer1["classification"]
        conf = layer1["confidence"]
        layer1_counts[cls] = layer1_counts.get(cls, 0) + 1
        print(f"  L1: {cls} ({conf}) — {layer1['note'][:80]}")

        layer2 = None
        layer3 = None

        needs_escalation = (
            not layer1_only
            and cls in ("partial_match", "no_match")
            or conf in escalate_levels
        )
        skip_escalation = cls == "not_applicable" or (cls == "match" and conf == "HIGH")

        if needs_escalation and not skip_escalation:
            layer2_count += 1
            print(f"  L2: Investigating...")
            layer2 = run_layer2(fns_section, layer1, olg_clients,
                                claude, layer2_model, layer2_prompt,
                                max_results=olg_max_results)
            l2_cls = layer2["classification"]
            searches = layer2.get("searches_performed", "?")
            print(f"  L2: {l2_cls} ({searches} searches) — {layer2['note'][:80]}")

            needs_layer3 = l2_cls in (
                "confirmed_gap", "different_standard",
                "policy_present_procedures_missing", "partial_match",
            )
            if needs_layer3 and cmr_clients:
                layer3_count += 1
                print(f"  L3: Checking CMR...")
                cmr_results = query_cmr(fns_section, cmr_clients, cmr_max_results)
                layer3 = run_layer3(fns_section, layer2, cmr_results,
                                    claude, layer3_model, layer3_prompt)
                action = layer3.get("action_recommended", "?")
                priority = layer3.get("priority", "?")
                print(f"  L3: {layer3['classification']} — {action} ({priority})")

        row = build_csv_row(fns_section, layer1, olg_results, layer2, layer3)
        all_rows.append(row)

        processed_ids.add(sec_id)
        save_checkpoint(all_rows, processed_ids)

        if (idx + 1) % 20 == 0:
            interim_path = OUTPUT_DIR / "comparison_interim.csv"
            write_csv(all_rows, interim_path)
            print(f"\n  Interim results saved ({len(all_rows)} rows)")

    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60

    csv_path = OUTPUT_DIR / "fns_vs_olg_snap_comparison.csv"
    write_csv(all_rows, csv_path)

    print(f"\n{'=' * 50}")
    print(f"Comparison complete!")
    print(f"{'=' * 50}")
    print(f"  Sections processed: {len(all_rows)}")
    print(f"  Time: {elapsed_min:.1f} minutes")
    print()
    print(f"  Layer 1 classifications:")
    for cls, count in sorted(layer1_counts.items()):
        print(f"    {cls:25s} {count}")
    print(f"  Escalated to Layer 2: {layer2_count}")
    print(f"  Escalated to Layer 3: {layer3_count}")
    print()
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
  python comparator.py                    # Full run, chapters 7-11
  python comparator.py --chapter 10       # One chapter only
  python comparator.py --layer1-only      # Triage only
  python comparator.py --dry-run          # Preview sections
  python comparator.py --resume           # Resume interrupted run
        """,
    )
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Process only this FNS chapter",
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
    args = parser.parse_args()

    config = load_config()

    if args.chapter:
        chapters = [args.chapter]
    else:
        chapters_str = config.get("comparator", "fns_chapters_to_compare",
                                  fallback="7,8,9,10,11")
        chapters = [int(c.strip()) for c in chapters_str.split(",")]

    run_comparison(
        chapters=chapters,
        layer1_only=args.layer1_only,
        dry_run=args.dry_run,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
