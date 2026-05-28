"""
Phase 1 sanity test: re-fetch a handful of representative OLG pages,
re-parse with the updated parser, and re-chunk with the updated chunker.

Test pages were chosen because they exercise the three Phase 1 changes:
  - View/Hide artifact stripping (BPov_AU_Mass_Assign — heavy View/Hide)
  - "Click here" hyperlink target capture (Bene_EffDeatesOtherStates)
  - Related Topics lifted to metadata (BPp_RecCalls_PQ)
  - Combo (BPov_NG_Overview — multiple sections, varied content)

Output: prints diffs in the relevant fields so we can eyeball the result
before committing to a full re-scrape.

Run from project root: python docs/olg_cleanup/test_phase1.py
"""

import json
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rag" / "olg"))

import parser as olg_parser
import chunker as olg_chunker

USER_AGENT = "DTAPolicyScraper/1.0 (RAG pipeline; respectful crawling)"

TEST_PAGES = [
    ("BP__Overview__BPov_AU_Mass_Assign.json", "View/Hide artifacts"),
    ("BP__Procedures__BPp_RecCalls_PQ.json", "Related Topics block"),
    ("SNAP__Bene_EffDeatesOtherStates.json", "click here links"),
    ("BP__Overview__BPov_NG_Overview.json", "mixed: tables + lists + artifacts"),
]


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_existing_metadata(scraped_filename: str) -> dict:
    """Get program / breadcrumb from the existing scraped JSON."""
    path = PROJECT_ROOT / "index" / "olg" / "scraped_pages" / scraped_filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_one(scraped_filename: str, why: str):
    print("=" * 78)
    print(f"TEST: {scraped_filename}")
    print(f"  reason: {why}")
    print("=" * 78)

    existing = load_existing_metadata(scraped_filename)
    url = existing["url"]
    print(f"  URL: {url}")
    print()

    html = fetch_html(url)
    parsed = olg_parser.parse_page(html, page_url=url)

    page_data = {
        "url": url,
        "title": parsed["title"] or existing.get("title", ""),
        "program": existing["program"],
        "breadcrumb": existing["breadcrumb"],
        "last_updated": parsed["last_updated"],
        "sections": parsed["sections"],
        "tables": parsed["tables"],
        "internal_links": parsed["internal_links"],
        "related_pages": parsed.get("related_pages", []),
    }

    print(f"  Section count: old={len(existing.get('sections', []))} new={len(page_data['sections'])}")
    print(f"  Related pages lifted: {len(page_data['related_pages'])}")
    if page_data["related_pages"]:
        for rp in page_data["related_pages"]:
            print(f"    - {rp['text']!r} → {rp['href'][-60:]}")
    print()

    # Run chunker
    sections_with_tables = olg_chunker.inline_tables(
        page_data["sections"], page_data["tables"]
    )
    page_doc = olg_chunker.create_page_document(page_data, sections_with_tables)
    chunks = olg_chunker.create_section_chunks(page_data, sections_with_tables)

    # Show every section chunk's text + outbound_links
    for ch in chunks:
        meta = ch["metadata"]
        print(f"  --- {ch['chunk_id']} ({len(ch['text'])} chars) ---")
        print(f"    heading: {meta['section_heading']!r}")
        outbound = meta.get("outbound_links", [])
        print(f"    outbound_links: {len(outbound)}")
        for link in outbound:
            print(f"      → {link['text']!r} = {link['href'][-60:]}")
        # Print head and tail of text
        text = ch["text"]
        if len(text) > 600:
            head = text[:300]
            tail = text[-300:]
            print(f"    text head: {head!r}")
            print(f"    text tail: {tail!r}")
        else:
            print(f"    text: {text!r}")
        print()

    # Validate: any UI artifacts left?
    artifact_hits = []
    for ch in chunks:
        for pat in ["View/Hide", "view/hide", "Show All", "Hide All",
                    "Print Topic", "Loading..."]:
            if pat in ch["text"]:
                artifact_hits.append((ch["chunk_id"], pat))
    if artifact_hits:
        print("  ! UI ARTIFACTS REMAINING:")
        for cid, pat in artifact_hits:
            print(f"    {cid}: {pat!r}")
    else:
        print("  ✓ No UI artifacts in any chunk")

    # Validate: Related Topics still in any chunk?
    rt_in_chunk = [ch["chunk_id"] for ch in chunks
                   if ch["metadata"].get("section_heading", "")
                   and "related topic" in (ch["metadata"].get("section_heading") or "").lower()]
    if rt_in_chunk:
        print("  ! RELATED TOPICS STILL IN CHUNK:")
        for cid in rt_in_chunk:
            print(f"    {cid}")
    else:
        print("  ✓ No Related Topics sections appear as chunks")

    print()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for fn, why in TEST_PAGES:
        try:
            run_one(fn, why)
        except Exception as e:
            print(f"  !! {fn} failed: {type(e).__name__}: {e}")
            print()


if __name__ == "__main__":
    main()
