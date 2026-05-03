"""
FNS Handbook side-by-side column-extraction cleanup.

The FNS parser does column-aware extraction for ~56 PDF pages with two-column
layouts (policy text + example boxes). Heuristic extraction handles most of these,
but a long tail of edge cases produces:

  - Stranded fragments in example_text that actually belong in the heading or prose
    (e.g. "This section provides the" floating alone in §1170.5's example_text)
  - Cross-references like "(See Section 621.)" leading example_text instead of inline
  - Stray bullet glyphs on what should be plain sub-headings
  - Runaway whitespace runs from word-position-based column splits
  - Multi-section pages duplicating the same example_text onto every section that
    shares the page (Pass 2 dedup, separate from per-section LLM cleanup)

This script does Pass 1 (per-section LLM cleanup via Haiku) and writes cleaned
values back to the parsed JSONs with a column_cleanup_applied flag for idempotency.

Usage:
  python tools/fns_column_cleanup.py --only 1170.5 --dry-run     # sanity check one section
  python tools/fns_column_cleanup.py --only 1170.5               # apply to one section
  python tools/fns_column_cleanup.py --limit 5                   # first 5 unprocessed
  python tools/fns_column_cleanup.py                             # all unprocessed
  python tools/fns_column_cleanup.py --force                     # re-run already-applied
"""

import argparse
import configparser
import json
import re
import sys
import time
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.ini"
PARSED_DIR = PROJECT_ROOT / "index" / "fns" / "parsed_sections"
FINDINGS_PATH = PROJECT_ROOT / "docs" / "fns_cleanup" / "column_cleanup_findings.md"

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096
PRICE_INPUT_PER_MTOK = 1.00
PRICE_OUTPUT_PER_MTOK = 5.00


SYSTEM_PROMPT = """You are cleaning up text extracted by a PDF parser from a two-column layout in the FNS Handbook 310. Each section has two fields:

- text: main policy prose from the LEFT column
- example_text: example boxes from the RIGHT column

The PDF column extraction got most of it right but produced these recurring artifacts:

1. STRANDED FRAGMENTS: a phrase from the heading or the lead paragraph of `text` ended up alone at the top or middle of `example_text`. Common case: heading line is broken so `text` reads "Section Title. <verb-ish phrase>" while `example_text` opens with "<noun-phrase>" that should fill in between. You must move stranded fragments back into `text` where they grammatically belong.

2. CROSS-REFERENCES IN EXAMPLE_TEXT: a parenthetical like "(See Section 621.)" or "(See Chapter 9.)" sometimes leads `example_text`. These belong inline in `text`. Move them.

3. STRAY BULLET GLYPHS ON SUB-HEADINGS: a line like "• Reported Medical Expenses." in `text` is actually a sub-heading (sibling to other sub-headings without bullets in the same section). Drop the leading "• ". Only do this when the line is clearly heading-like (short, ends with period, capitalized, and other parallel lines in the section are plain sub-headings).

4. WHITESPACE RUNS: long runs of spaces (10+) inside sentences are column-extraction artifacts. Collapse to single space.

5. SOFT-WRAPPED LINES INSIDE EXAMPLES: example_text often has mid-sentence line breaks. Flatten them when the next character is lowercase or continues a sentence. Preserve real paragraph breaks (sentence end + capital start).

PRESERVE every factual sentence. Do not summarize. Do not reword. Move and re-stitch only — your job is mechanical reassembly, not editing. If a sentence appears in BOTH text and example_text (rare but possible), keep it only in the field it grammatically belongs to and note it in `concerns`.

Return your output as JSON with this exact shape:

{
  "cleaned_text": "...",
  "cleaned_example_text": "...",
  "moves": ["short description of each move you made"],
  "concerns": ["anything you couldn't confidently fix or that looked weird"]
}

Always return both fields even if unchanged. Empty example_text is "". Do not include any text before or after the JSON."""


USER_TEMPLATE = """Section: {section_number} {section_title} (Chapter {chapter}: {chapter_title})

CURRENT text:
<<<TEXT>>>
{text}
<<<END>>>

CURRENT example_text:
<<<EXAMPLE>>>
{example}
<<<END>>>

Return cleaned versions as JSON."""


def load_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE, encoding="utf-8")
    return cfg


def find_target_files(only: str | None, force: bool, limit: int | None) -> list[Path]:
    targets = []
    for p in sorted(PARSED_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if "side_by_side_page" not in d.get("flags", []):
            continue
        if only is not None and d.get("section_number") != only:
            continue
        if not force and d.get("column_cleanup_applied"):
            continue
        targets.append(p)
        if limit is not None and len(targets) >= limit:
            break
    return targets


def call_haiku(client: anthropic.Anthropic, section: dict) -> tuple[dict, dict]:
    """Returns (parsed_response, usage_dict). Raises on parse error."""
    user = USER_TEMPLATE.format(
        section_number=section.get("section_number", "?"),
        section_title=section.get("section_title", "?"),
        chapter=section.get("chapter", "?"),
        chapter_title=section.get("chapter_title", "?"),
        text=section.get("text", ""),
        example=section.get("example_text", ""),
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    raw = resp.content[0].text.strip()
    # Strip ```json fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```\s*$", "", raw)
    parsed = json.loads(raw)
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return parsed, usage


def estimate_cost(usage_total: dict) -> float:
    return (
        usage_total["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_MTOK
        + usage_total["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_MTOK
    )


def show_diff(before: str, after: str, label: str, head: int = 600) -> None:
    print(f"--- BEFORE {label} (first {head} chars) ---")
    print(before[:head])
    print(f"--- AFTER {label} (first {head} chars) ---")
    print(after[:head])
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="Process only this section number (e.g. 1170.5)")
    ap.add_argument("--limit", type=int, help="Stop after N sections")
    ap.add_argument("--dry-run", action="store_true", help="Print results, don't write JSONs")
    ap.add_argument("--force", action="store_true", help="Re-run sections already marked column_cleanup_applied")
    ap.add_argument("--quiet", action="store_true", help="Skip per-section diff output")
    args = ap.parse_args()

    cfg = load_config()
    api_key = cfg["api"]["anthropic_api_key"]
    client = anthropic.Anthropic(api_key=api_key)

    targets = find_target_files(args.only, args.force, args.limit)
    if not targets:
        print("No sections to process. Use --force to re-run already-cleaned sections.")
        return 0

    print(f"Targets: {len(targets)} section(s)")
    if args.dry_run:
        print("(DRY RUN — JSONs will not be modified)")
    print()

    findings = []
    usage_total = {"input_tokens": 0, "output_tokens": 0}
    success = 0
    failed = 0

    for i, path in enumerate(targets, 1):
        section = json.loads(path.read_text(encoding="utf-8"))
        sec_id = f"§{section.get('section_number')} {section.get('section_title','')}"
        print(f"[{i}/{len(targets)}] {sec_id}")

        try:
            parsed, usage = call_haiku(client, section)
        except json.JSONDecodeError as e:
            print(f"  JSON decode error: {e}")
            failed += 1
            continue
        except anthropic.APIError as e:
            print(f"  API error: {e}")
            failed += 1
            continue

        usage_total["input_tokens"] += usage["input_tokens"]
        usage_total["output_tokens"] += usage["output_tokens"]

        before_text = section.get("text", "")
        before_ex = section.get("example_text", "")
        after_text = parsed.get("cleaned_text", before_text)
        after_ex = parsed.get("cleaned_example_text", before_ex)
        moves = parsed.get("moves", [])
        concerns = parsed.get("concerns", [])

        text_changed = before_text != after_text
        ex_changed = before_ex != after_ex

        if not args.quiet:
            print(f"  text changed: {text_changed} ({len(before_text)} -> {len(after_text)} chars)")
            print(f"  example changed: {ex_changed} ({len(before_ex)} -> {len(after_ex)} chars)")
            if moves:
                print(f"  moves:")
                for m in moves:
                    print(f"    - {m}")
            if concerns:
                print(f"  concerns:")
                for c in concerns:
                    print(f"    - {c}")
            if text_changed:
                show_diff(before_text, after_text, "TEXT")
            if ex_changed:
                show_diff(before_ex, after_ex, "EXAMPLE")

        findings.append({
            "section_number": section.get("section_number"),
            "section_title": section.get("section_title"),
            "chapter": section.get("chapter"),
            "text_changed": text_changed,
            "example_changed": ex_changed,
            "text_len_before": len(before_text),
            "text_len_after": len(after_text),
            "example_len_before": len(before_ex),
            "example_len_after": len(after_ex),
            "moves": moves,
            "concerns": concerns,
        })
        success += 1

        if not args.dry_run:
            section["text"] = after_text
            section["example_text"] = after_ex
            section["column_cleanup_applied"] = True
            section["column_cleanup_moves"] = moves
            if concerns:
                section["column_cleanup_concerns"] = concerns
            path.write_text(json.dumps(section, indent=2, ensure_ascii=False), encoding="utf-8")

    cost = estimate_cost(usage_total)
    print()
    print(f"Done. Success: {success}, Failed: {failed}")
    print(f"Tokens: {usage_total['input_tokens']:,} in / {usage_total['output_tokens']:,} out")
    print(f"Estimated cost: ${cost:.4f}")

    if not args.dry_run and findings:
        write_findings(findings, cost, usage_total)
        print(f"Findings written to: {FINDINGS_PATH.relative_to(PROJECT_ROOT)}")

    return 0 if failed == 0 else 1


def write_findings(findings: list[dict], cost: float, usage: dict) -> None:
    FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# FNS Column Cleanup Findings (Pass 1 — per-section LLM)")
    lines.append("")
    lines.append(f"**Run timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Sections processed**: {len(findings)}")
    lines.append(f"**Tokens**: {usage['input_tokens']:,} in / {usage['output_tokens']:,} out")
    lines.append(f"**Cost**: ${cost:.4f}")
    lines.append("")
    lines.append("| Section | Title | Text Δ | Example Δ | # Moves | # Concerns |")
    lines.append("|---|---|---|---|---|---|")
    for f in findings:
        td = "yes" if f["text_changed"] else "no"
        ed = "yes" if f["example_changed"] else "no"
        lines.append(
            f"| {f['section_number']} | {f['section_title']} | {td} | {ed} | {len(f['moves'])} | {len(f['concerns'])} |"
        )
    lines.append("")
    lines.append("## Per-section detail")
    lines.append("")
    for f in findings:
        lines.append(f"### §{f['section_number']} {f['section_title']} (Ch {f['chapter']})")
        lines.append("")
        lines.append(f"- text: {f['text_len_before']} → {f['text_len_after']} chars")
        lines.append(f"- example: {f['example_len_before']} → {f['example_len_after']} chars")
        if f["moves"]:
            lines.append("- moves:")
            for m in f["moves"]:
                lines.append(f"  - {m}")
        if f["concerns"]:
            lines.append("- concerns:")
            for c in f["concerns"]:
                lines.append(f"  - {c}")
        lines.append("")
    FINDINGS_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
