"""
Phase 2.6 sanity test: live-fetch a handful of OLG pages and re-parse with
the updated parser to verify two fixes:

  1. Boilerplate "This topic has been recently added..." is stripped
     from section text.
  2. Nested <ol> renders depth-aware markers — outer 1./2./3., inner a./b./c.,
     deeper bullets — instead of restarting at 1./2./3. at every level.

Pages chosen:
  - BPov_TAO_PL_Greet     — boilerplate page (66 pages share the banner)
  - BPp_ProcCase_OOVO     — boilerplate page, second example
  - BPov_AU_Mass_Assign   — three-deep nested ordered list (1 -> 1 -> 1)

Run from project root: python docs/olg_cleanup/test_phase2_6.py
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rag" / "olg"))

import parser as olg_parser

USER_AGENT = "DTAPolicyScraper/1.0 (RAG pipeline; respectful crawling)"

TEST_PAGES = [
    ("BP__Overview__BPov_TAO_PL_Greet.json",
     "boilerplate strip — recently-added banner"),
    ("BP__Procedures__BPp_ProcCase_OOVO.json",
     "boilerplate strip — second example"),
    ("BP__Overview__BPov_AU_Mass_Assign.json",
     "nested-ol depth — outer 1., inner should be a., deeper should be -"),
]

BOILERPLATE_RE = re.compile(
    r"This topic has been recently added to the Online Guide",
    re.IGNORECASE,
)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_existing_metadata(scraped_filename: str) -> dict:
    path = PROJECT_ROOT / "index" / "olg" / "scraped_pages" / scraped_filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_one(scraped_filename: str, why: str) -> dict:
    print("=" * 78)
    print(f"TEST: {scraped_filename}")
    print(f"  reason: {why}")
    print("=" * 78)

    existing = load_existing_metadata(scraped_filename)
    url = existing["url"]
    print(f"  URL: {url}")

    html = fetch_html(url)
    parsed = olg_parser.parse_page(html, page_url=url)

    # Boilerplate check
    boilerplate_hits = []
    for s in parsed["sections"]:
        m = BOILERPLATE_RE.search(s.get("text", ""))
        if m:
            boilerplate_hits.append(
                (s.get("heading"), s["text"][max(0, m.start() - 20):m.end() + 50])
            )
    if boilerplate_hits:
        print("  ! BOILERPLATE STILL PRESENT:")
        for heading, ctx in boilerplate_hits:
            print(f"    section heading={heading!r}")
            print(f"    near: {ctx!r}")
    else:
        print("  ✓ No 'recently added' boilerplate in section text")

    # Nested-ol marker check — look for ordered nesting depth tells:
    # If a parent step like "7. " is followed by "  1. " AGAIN at depth 2,
    # that's the bug we just fixed. With the fix, depth 2 should be "  a. ".
    bad_nested = []
    good_nested = []
    deeper_nested = []
    for s in parsed["sections"]:
        text = s.get("text", "")
        # Count occurrences of "  1. " (two-space indent, digit dot space)
        # — these are depth-2 list items still using digits.
        if re.search(r"^  \d+\.\s+\S", text, re.MULTILINE):
            bad_nested.append(s.get("heading"))
        # Count "  a. " "  b. " etc — depth 2 with letter markers.
        if re.search(r"^  [a-z]\.\s+\S", text, re.MULTILINE):
            good_nested.append(s.get("heading"))
        # Count "    - " — depth 3+ rendered as bullets.
        if re.search(r"^    -\s+\S", text, re.MULTILINE):
            deeper_nested.append(s.get("heading"))

    if bad_nested:
        print(f"  ! NESTED OL STILL USING DIGITS at depth 2 in: {bad_nested}")
    else:
        print("  ✓ No depth-2 ordered list using digits")
    if good_nested:
        print(f"  ✓ Depth-2 letter markers seen in: {good_nested}")
    if deeper_nested:
        print(f"  ✓ Depth-3+ bullet markers seen in: {deeper_nested}")

    # Show the most-nested section as a sanity printout
    candidates = [
        s for s in parsed["sections"]
        if re.search(r"^  [a-z]\.\s+", s.get("text", ""), re.MULTILINE)
        or re.search(r"^    -\s+", s.get("text", ""), re.MULTILINE)
    ]
    if candidates:
        print()
        print("  --- Sample nested-list section text ---")
        sample = candidates[0]
        print(f"  heading: {sample.get('heading')!r}")
        print()
        for line in sample["text"].split("\n"):
            print(f"  | {line}")
        print()

    return {
        "boilerplate_hits": boilerplate_hits,
        "bad_nested": bad_nested,
        "good_nested": good_nested,
        "deeper_nested": deeper_nested,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
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
    print("Phase 2.6 summary")
    print("=" * 78)
    for fn, info in summary.items():
        bp = "PASS" if not info["boilerplate_hits"] else "FAIL"
        nest = "PASS" if not info["bad_nested"] else "FAIL"
        print(f"  {fn}: boilerplate={bp}  nested-ol={nest}")


if __name__ == "__main__":
    main()
