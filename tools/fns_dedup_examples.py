"""
FNS Pass 2: cross-section example_text dedup.

When sections share a PDF page that has a side-by-side example box, the parser
duplicates the example_text onto every section that shares the page. Pass 1 (LLM
cleanup) already removed many of these as part of per-section reasoning, but
some byte-identical duplicates remain.

This pass deterministically picks one owner per duplicate group and clears
example_text on the others, recording the attribution in `example_text_origin`.

Heuristic for owner selection (when multiple sections share an identical
example_text):
1. If example length is below `JUNK_THRESHOLD` (60 chars), it's an extraction
   fragment — drop from all sections.
2. Score each candidate section by:
   - +100 if its text contains "example", "shows how", "follow", or "see"
     (indicates the section is the example introducer)
   - +1 per character of text length (prefer substantive sections, with
     example-language signal still dominating)
3. Tie-break: the section whose number sorts LAST (examples typically follow
   the policy in FNS).

Run AFTER fns_column_cleanup.py.

Usage:
  python tools/fns_dedup_examples.py --dry-run
  python tools/fns_dedup_examples.py
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSED_DIR = PROJECT_ROOT / "index" / "fns" / "parsed_sections"

JUNK_THRESHOLD = 60

# Manual overrides for cases where heuristic picks the wrong owner.
# Key: example_text content prefix (first 60 chars). Value: section number to use as owner,
# or "DROP" to clear from all sections.
MANUAL_OWNER_OVERRIDES = {
    "Element Codes 100s 200s 300s 500s and above": "DROP",
    "Examples of Allowing a Deductible Expense as Billed, not as Paid": "1110",
}


def section_sort_key(section_number: str) -> tuple:
    """Sort §1130.2 before §1130.10 properly."""
    parts = section_number.split(".")
    return tuple(int(p) if p.isdigit() else 0 for p in parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Show planned changes, don't write")
    args = ap.parse_args()

    by_page = defaultdict(list)
    for p in sorted(PARSED_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if "side_by_side_page" not in d.get("flags", []):
            continue
        ex = d.get("example_text", "").strip()
        if not ex:
            continue
        pages = tuple(d.get("pdf_pages", []))
        by_page[pages].append((d, p))

    dedup_decisions = []
    junk_decisions = []

    for pages, members in sorted(by_page.items()):
        if len(members) < 2:
            continue
        by_ex = defaultdict(list)
        for d, path in members:
            by_ex[d["example_text"].strip()].append((d, path))
        for ex, group in by_ex.items():
            if len(group) <= 1:
                continue
            override = None
            for prefix, target in MANUAL_OWNER_OVERRIDES.items():
                if ex.startswith(prefix):
                    override = target
                    break
            if override == "DROP" or len(ex) < JUNK_THRESHOLD:
                junk_decisions.append((pages, [g[0]["section_number"] for g in group], len(ex), group))
                continue
            if override is not None:
                owner = next((gp for gp in group if gp[0]["section_number"] == override), None)
                if owner is None:
                    print(f"  WARN: override target §{override} not found in group {[g[0]['section_number'] for g in group]}; falling back to heuristic")
                else:
                    losers = [gp for gp in group if gp is not owner]
                    dedup_decisions.append((pages, owner, losers, len(ex)))
                    continue
            ranked = sorted(
                group,
                key=lambda gp: (len(gp[0].get("text", "")), section_sort_key(gp[0]["section_number"])),
                reverse=True,
            )
            owner = ranked[0]
            losers = ranked[1:]
            dedup_decisions.append((pages, owner, losers, len(ex)))

    print(f"Duplicate groups (>= {JUNK_THRESHOLD} chars, attributing to one owner): {len(dedup_decisions)}")
    for pages, owner, losers, exlen in dedup_decisions:
        print(f"  pages {pages} ({exlen}-char example):")
        print(f"    OWNER:  §{owner[0]['section_number']} {owner[0]['section_title']} (text {len(owner[0]['text'])} chars)")
        for d, _ in losers:
            print(f"    CLEAR:  §{d['section_number']} {d['section_title']}")

    print()
    print(f"Junk groups (< {JUNK_THRESHOLD} chars, dropping from all sections): {len(junk_decisions)}")
    for pages, secs, exlen, _ in junk_decisions:
        print(f"  pages {pages}: dropping {exlen}-char fragment from {secs}")

    if args.dry_run:
        print()
        print("(DRY RUN — no files modified)")
        return 0

    # Apply
    cleared = 0
    for pages, owner, losers, _ in dedup_decisions:
        owner_num = owner[0]["section_number"]
        for d, path in losers:
            d["example_text"] = ""
            d["example_text_origin"] = owner_num
            path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            cleared += 1
    for pages, secs, exlen, group in junk_decisions:
        for d, path in group:
            d["example_text"] = ""
            d["example_text_origin"] = "junk_fragment_dropped"
            path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            cleared += 1

    print()
    print(f"Cleared example_text on {cleared} section(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
