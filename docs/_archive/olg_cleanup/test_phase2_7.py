"""
Phase 2.7 sanity test: verify the indent-aware splitter keeps a parent
list-item with its sub-children when splitting a section larger than
MAX_CHUNK_SIZE.

Primary reproducer:
  BP__Overview__BPov_AU_Mass_Assign — section "How Mass Assign AUs..."
  has steps 1-10 with step 5 owning 3 sub-items and step 7 owning 5
  sub-items + 2 sub-sub-items. Pre-fix, step 7's prose ended chunk 1
  while its sub-items started chunk 2, orphaning them. Post-fix, step 7
  + sub-items + sub-sub-items co-locate in a single chunk.

Regression checks:
  - Stu_Students (53 chunks pre-fix, lots of nested H3s)
  - BPov_NG_Overview (11 chunks pre-fix, large tables)

Pass criteria:
  - Mass_Assign produces 4 chunks total. The chunk containing "7. The Assign
    to AU Manager screen" must also contain at least 4 of step 7's 5
    sub-items (lines starting with "  1. " through "  5. " — the legacy
    scrape uses digits at depth 2 because Phase 2.6 only kicks in on
    re-scrape).
  - Stu_Students and BPov_NG_Overview retain their pre-fix chunk count
    (or close to it — within ±1) and zero mid-word splits.

Run from project root: python docs/olg_cleanup/test_phase2_7.py
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rag" / "olg"))

import chunker as olg_chunker

MASS_ASSIGN = "BP__Overview__BPov_AU_Mass_Assign.json"
STU_STUDENTS = "SNAP__Eligibility__Stu_Students.json"
NG_OVERVIEW = "BP__Overview__BPov_NG_Overview.json"


def chunk_page(filename: str) -> list[dict]:
    path = PROJECT_ROOT / "index" / "olg" / "scraped_pages" / filename
    with open(path, "r", encoding="utf-8") as f:
        page = json.load(f)
    sections_with_tables = olg_chunker.inline_tables(
        page.get("sections", []), page.get("tables", [])
    )
    return olg_chunker.create_section_chunks(page, sections_with_tables)


def test_mass_assign() -> dict:
    print("=" * 78)
    print("TEST: Mass_Assign — parent step 7 + sub-items co-location")
    print("=" * 78)

    chunks = chunk_page(MASS_ASSIGN)
    print(f"  Total chunks: {len(chunks)}")

    # Find the chunk containing step 7's prose
    step7_chunk = None
    for ch in chunks:
        if "7. The" in ch["text"] and "Assign to AU Manager" in ch["text"]:
            step7_chunk = ch
            break

    if step7_chunk is None:
        print("  ! step 7 not found in any chunk — diagnostic failed")
        return {"chunks": len(chunks), "subitems_with_parent": 0,
                "pass": False}

    body = step7_chunk["text"].split("\n\n", 1)[-1]
    # Look for sub-item markers — legacy scrape uses "  1. " "  2. " etc.
    # (Re-scrape will use "  a. " "  b. " etc. after Phase 2.6 lands —
    # detect either pattern here so this test stays valid post re-scrape.)
    legacy = re.findall(r"^  \d+\. ", body, flags=re.MULTILINE)
    new_style = re.findall(r"^  [a-z]\. ", body, flags=re.MULTILINE)
    subitems_in_step7_chunk = len(legacy) + len(new_style)

    meta = step7_chunk["metadata"]
    print(f"  Step 7 chunk: {step7_chunk['chunk_id']} "
          f"({len(step7_chunk['text'])} chars, "
          f"n={meta['chunk_n']}/{meta['chunk_total']})")
    print(f"  Sub-items found in same chunk: {subitems_in_step7_chunk}")
    print(f"    legacy '  N. ' style: {len(legacy)}")
    print(f"    new    '  a. ' style: {len(new_style)}")

    passed = subitems_in_step7_chunk >= 4
    if passed:
        print("  ✓ Step 7 + at least 4 sub-items co-located in same chunk")
    else:
        print("  ! Step 7's sub-items orphaned from parent step")
        print()
        print("  --- step 7 chunk body ---")
        for line in body.split("\n"):
            print(f"    | {line}")

    print()
    return {
        "chunks": len(chunks),
        "subitems_with_parent": subitems_in_step7_chunk,
        "pass": passed,
    }


def _midword_count(chunks: list[dict]) -> int:
    """Count mid-word splits between consecutive chunks of the same page."""
    n = 0
    for i in range(len(chunks) - 1):
        if (chunks[i]["metadata"]["parent_page_id"]
                != chunks[i + 1]["metadata"]["parent_page_id"]):
            continue
        prev = chunks[i]["text"].rstrip()
        nxt_body = chunks[i + 1]["text"]
        nxt_body = nxt_body.split("\n\n", 1)[-1].strip() if "\n\n" in nxt_body else nxt_body
        if not prev or not nxt_body:
            continue
        last_char = prev[-1]
        first_char = nxt_body[0]
        if last_char.isalpha() and first_char.islower():
            n += 1
    return n


def test_regression(filename: str, expected_chunks: int) -> dict:
    print("=" * 78)
    print(f"REGRESSION: {filename}")
    print("=" * 78)
    chunks = chunk_page(filename)
    midword = _midword_count(chunks)
    delta = len(chunks) - expected_chunks
    chunk_ok = abs(delta) <= 1
    midword_ok = midword == 0
    print(f"  Chunks: {len(chunks)} (expected ~{expected_chunks}, delta {delta:+d}) "
          f"{'✓' if chunk_ok else '!'}")
    print(f"  Mid-word splits: {midword} {'✓' if midword_ok else '!'}")
    print()
    return {
        "filename": filename,
        "chunks": len(chunks),
        "expected": expected_chunks,
        "midword": midword,
        "pass": chunk_ok and midword_ok,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    olg_chunker._oversized_line_warnings.clear()

    primary = test_mass_assign()
    regressions = [
        test_regression(STU_STUDENTS, 53),
        test_regression(NG_OVERVIEW, 11),
    ]

    print("=" * 78)
    print("Phase 2.7 summary")
    print("=" * 78)
    print(f"  Mass_Assign: chunks={primary['chunks']}  "
          f"subitems_with_parent={primary['subitems_with_parent']}  "
          f"{'PASS' if primary['pass'] else 'FAIL'}")
    for r in regressions:
        print(f"  {r['filename']}: chunks={r['chunks']} (expect ~{r['expected']})  "
              f"midword={r['midword']}  "
              f"{'PASS' if r['pass'] else 'FAIL'}")

    if olg_chunker._oversized_line_warnings:
        print()
        print(f"  ! {len(olg_chunker._oversized_line_warnings)} oversize warnings:")
        for w in olg_chunker._oversized_line_warnings:
            print(f"    {w}")


if __name__ == "__main__":
    main()
