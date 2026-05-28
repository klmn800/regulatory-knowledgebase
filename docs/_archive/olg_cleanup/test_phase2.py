"""
Phase 2 sanity test: re-chunk a handful of diagnostic OLG pages with the
new hierarchy-aware splitter and cross-level merge protection.

Pages chosen because they exercise the four bugs Phase 2 fixes:
  - Mid-word table cell splits  (BPov_NG_Overview)
  - Mid-word table cell splits  (Stu_Students)
  - Mid-word table cell splits  (Forms_Cross_Programs)
  - §1A subsection-merge contamination  (COVID_ProcPandUCInc)

Output: prints chunk-by-chunk text + metadata, plus a summary of
mid-word splits detected, oversized warnings, and parent_heading coverage.

Run from project root: python docs/olg_cleanup/test_phase2.py
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rag" / "olg"))

import chunker as olg_chunker

# Page filename → reason for selecting it
TEST_PAGES = [
    ("BP__Overview__BPov_NG_Overview.json",
     "mid-word table cell split (yo|u must mention)"),
    ("SNAP__Eligibility__Stu_Students.json",
     "mid-word table cell split (Enr|olled in)"),
    ("Forms__Cross_Programs.json",
     "mid-word table cell split (Reques|t for Deduction)"),
    ("COVID__COVID_ProcPandUCInc.json",
     "subsection-merge contamination (H2 intro absorbing first H3)"),
]


def _looks_like_midword_split(prev_tail: str, next_head: str) -> bool:
    """
    Detect 'foo|bar' style splits by checking that the previous chunk ends
    with letters (no terminating punctuation/space) AND the next chunk
    begins with lowercase letters.
    """
    if not prev_tail or not next_head:
        return False
    last_char = prev_tail[-1]
    first_char = next_head[0]
    return (last_char.isalpha()
            and first_char.islower()
            and last_char.isalpha())


def find_test_page(filename: str) -> Path | None:
    p = PROJECT_ROOT / "index" / "olg" / "scraped_pages" / filename
    if p.exists():
        return p
    # Try a glob match if the exact name didn't pan out
    candidates = list(
        (PROJECT_ROOT / "index" / "olg" / "scraped_pages").glob(
            f"*{filename.split('__')[-1]}"
        )
    )
    if candidates:
        return candidates[0]
    return None


def run_one(filename: str, why: str) -> dict:
    print("=" * 78)
    print(f"TEST: {filename}")
    print(f"  reason: {why}")
    print("=" * 78)

    page_path = find_test_page(filename)
    if page_path is None:
        print(f"  !! could not locate {filename}")
        print()
        return {"midword": [], "oversized": 0, "chunks": 0}

    print(f"  source: {page_path.name}")
    page_data = json.loads(page_path.read_text(encoding="utf-8"))

    sections = page_data.get("sections", [])
    tables = page_data.get("tables", [])

    sections_with_tables = olg_chunker.inline_tables(sections, tables)
    chunks = olg_chunker.create_section_chunks(page_data, sections_with_tables)

    print(f"  Sections in page (raw):  {len(sections)}")
    print(f"  Section-level chunks:    {len(chunks)}")
    print()

    midword_hits = []
    for i in range(len(chunks) - 1):
        prev = chunks[i]["text"]
        nxt = chunks[i + 1]["text"]
        if (chunks[i]["metadata"]["parent_page_id"]
                != chunks[i + 1]["metadata"]["parent_page_id"]):
            continue
        # Use last/first non-prefix line content
        prev_tail = prev.rstrip()[-1:] if prev.strip() else ""
        # Skip context-prefix line on the next chunk by stripping past first \n\n
        nxt_body = nxt.split("\n\n", 1)[-1].strip() if "\n\n" in nxt else nxt
        nxt_head = nxt_body[:1] if nxt_body else ""
        if _looks_like_midword_split(prev_tail, nxt_head):
            # Get more context for the report
            tail_ctx = prev[-30:].replace("\n", " ")
            head_ctx = nxt_body[:30].replace("\n", " ")
            midword_hits.append((chunks[i]["chunk_id"],
                                 chunks[i + 1]["chunk_id"],
                                 tail_ctx, head_ctx))

    for ch in chunks:
        meta = ch["metadata"]
        print(f"  --- {ch['chunk_id']} ({len(ch['text'])} chars) ---")
        print(f"    heading: {meta['section_heading']!r}")
        print(f"    parent : {meta.get('parent_heading')!r}")
        print(f"    chunk_n/total: {meta.get('chunk_n')}/{meta.get('chunk_total')}")
        text = ch["text"]
        # Show head and tail
        if len(text) > 400:
            print(f"    text head: {text[:200]!r}")
            print(f"    text tail: {text[-200:]!r}")
        else:
            print(f"    text     : {text!r}")
        print()

    if midword_hits:
        print("  ! MID-WORD SPLITS detected between consecutive chunks:")
        for prev_id, next_id, tail, head in midword_hits:
            print(f"    {prev_id} → {next_id}")
            print(f"       ...{tail!r} | {head!r}...")
    else:
        print("  ✓ No mid-word splits detected")
    print()

    return {"midword": midword_hits, "chunks": len(chunks)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    olg_chunker._oversized_line_warnings.clear()

    summary = {}
    for fn, why in TEST_PAGES:
        try:
            summary[fn] = run_one(fn, why)
        except Exception as e:
            import traceback
            print(f"  !! {fn} failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            print()

    print("=" * 78)
    print("Phase 2 summary")
    print("=" * 78)
    for fn, info in summary.items():
        print(f"  {fn}: {info['chunks']} chunks, "
              f"{len(info['midword'])} mid-word splits")
    if olg_chunker._oversized_line_warnings:
        print()
        print(f"  ! {len(olg_chunker._oversized_line_warnings)} oversize warnings:")
        for w in olg_chunker._oversized_line_warnings:
            print(f"    {w}")


if __name__ == "__main__":
    main()
