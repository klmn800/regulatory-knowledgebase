"""
Compare two snapshots of `index/olg/scraped_pages/` and report what
changed. Built for verifying the Phase 6 re-scrape.

Per-page report (only pages with notable changes shown):
  - section count delta
  - last_updated change
  - View/Hide artifact count delta
  - "recently added" boilerplate count delta
  - related_pages presence (pre-Phase 1 backups won't have it)
  - text size delta (rough proxy for content rewrite)

Summary aggregates at the end:
  - pages added / removed / changed
  - total View/Hide artifacts removed
  - total boilerplate occurrences removed
  - pages with section-count changes (likely DTA rewrites)

Usage:
    python docs/olg_cleanup/rescrape_diff.py \\
        --before index/olg/scraped_pages_pre_phase1 \\
        --after  index/olg/scraped_pages

    # Limit per-page output to top N most-changed pages
    python docs/olg_cleanup/rescrape_diff.py \\
        --before <dir> --after <dir> --top 20

    # Only show summary
    python docs/olg_cleanup/rescrape_diff.py \\
        --before <dir> --after <dir> --summary-only
"""

import argparse
import json
import re
import sys
from pathlib import Path

VIEW_HIDE_RE = re.compile(r"View/Hide", re.IGNORECASE)
BOILERPLATE_RE = re.compile(
    r"This topic has been recently added to the Online Guide",
    re.IGNORECASE,
)


def _count_artifacts(page: dict, pattern: re.Pattern) -> int:
    n = 0
    for s in page.get("sections", []):
        n += len(pattern.findall(s.get("text", "")))
    return n


def _total_text_size(page: dict) -> int:
    return sum(len(s.get("text", "")) for s in page.get("sections", []))


def _section_count(page: dict) -> int:
    return len(page.get("sections", []))


def _safe_load(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  !! failed to load {path}: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def diff_one(before: dict, after: dict) -> dict:
    """Return a diff record. All deltas are after - before (positive means
    after has more)."""
    return {
        "section_count_before": _section_count(before),
        "section_count_after": _section_count(after),
        "section_count_delta": _section_count(after) - _section_count(before),
        "last_updated_before": before.get("last_updated"),
        "last_updated_after": after.get("last_updated"),
        "view_hide_before": _count_artifacts(before, VIEW_HIDE_RE),
        "view_hide_after": _count_artifacts(after, VIEW_HIDE_RE),
        "boilerplate_before": _count_artifacts(before, BOILERPLATE_RE),
        "boilerplate_after": _count_artifacts(after, BOILERPLATE_RE),
        "related_pages_before": len(before.get("related_pages", []) or []),
        "related_pages_after": len(after.get("related_pages", []) or []),
        "text_size_before": _total_text_size(before),
        "text_size_after": _total_text_size(after),
        "text_size_delta": _total_text_size(after) - _total_text_size(before),
    }


def _is_notable(d: dict) -> bool:
    return (
        d["section_count_delta"] != 0
        or d["last_updated_before"] != d["last_updated_after"]
        or d["view_hide_before"] != d["view_hide_after"]
        or d["boilerplate_before"] != d["boilerplate_after"]
        or d["related_pages_before"] != d["related_pages_after"]
        or abs(d["text_size_delta"]) > 200
    )


def _change_score(d: dict) -> int:
    """Sort key for 'most-changed' ranking."""
    return (
        abs(d["section_count_delta"]) * 1000
        + abs(d["text_size_delta"])
        + d["view_hide_before"] * 50
        + d["boilerplate_before"] * 50
    )


def format_one(name: str, d: dict) -> str:
    lines = [f"  {name}"]
    if d["section_count_delta"] != 0:
        lines.append(
            f"    sections: {d['section_count_before']} -> {d['section_count_after']} "
            f"({d['section_count_delta']:+d})"
        )
    if d["last_updated_before"] != d["last_updated_after"]:
        lines.append(
            f"    last_updated: {d['last_updated_before']!r} -> {d['last_updated_after']!r}"
        )
    if d["view_hide_before"] != d["view_hide_after"]:
        lines.append(
            f"    View/Hide artifacts: {d['view_hide_before']} -> {d['view_hide_after']}"
        )
    if d["boilerplate_before"] != d["boilerplate_after"]:
        lines.append(
            f"    boilerplate: {d['boilerplate_before']} -> {d['boilerplate_after']}"
        )
    if d["related_pages_before"] != d["related_pages_after"]:
        lines.append(
            f"    related_pages: {d['related_pages_before']} -> {d['related_pages_after']}"
        )
    if abs(d["text_size_delta"]) > 200:
        lines.append(
            f"    text size: {d['text_size_before']} -> {d['text_size_after']} "
            f"({d['text_size_delta']:+d} chars)"
        )
    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", required=True, type=Path,
                    help="Path to old scraped_pages dir (backup)")
    ap.add_argument("--after", required=True, type=Path,
                    help="Path to new scraped_pages dir")
    ap.add_argument("--top", type=int, default=0,
                    help="Show only top N most-changed pages (0 = show all notable)")
    ap.add_argument("--summary-only", action="store_true",
                    help="Skip per-page output, show only aggregates")
    args = ap.parse_args()

    if not args.before.exists():
        print(f"!! --before path does not exist: {args.before}", file=sys.stderr)
        sys.exit(1)
    if not args.after.exists():
        print(f"!! --after path does not exist: {args.after}", file=sys.stderr)
        sys.exit(1)

    before_files = {p.name: p for p in args.before.glob("*.json")}
    after_files = {p.name: p for p in args.after.glob("*.json")}

    only_in_before = sorted(set(before_files) - set(after_files))
    only_in_after = sorted(set(after_files) - set(before_files))
    in_both = sorted(set(before_files) & set(after_files))

    diffs: list[tuple[str, dict]] = []
    failed = 0
    for name in in_both:
        before = _safe_load(before_files[name])
        after = _safe_load(after_files[name])
        if before is None or after is None:
            failed += 1
            continue
        diffs.append((name, diff_one(before, after)))

    notable = [(n, d) for n, d in diffs if _is_notable(d)]
    notable.sort(key=lambda x: _change_score(x[1]), reverse=True)

    # Per-page output
    if not args.summary_only:
        print("=" * 78)
        print("Per-page changes (most-changed first)")
        print("=" * 78)
        to_show = notable if args.top == 0 else notable[: args.top]
        for name, d in to_show:
            print(format_one(name, d))
        print()
        if args.top and len(notable) > args.top:
            print(f"  (... {len(notable) - args.top} more notable pages omitted)")
            print()

    # Aggregates
    print("=" * 78)
    print("Summary")
    print("=" * 78)
    print(f"  Pages in --before only: {len(only_in_before)}")
    if only_in_before:
        for n in only_in_before[:10]:
            print(f"    - {n}")
        if len(only_in_before) > 10:
            print(f"    (... {len(only_in_before) - 10} more)")
    print(f"  Pages in --after only: {len(only_in_after)}")
    if only_in_after:
        for n in only_in_after[:10]:
            print(f"    + {n}")
        if len(only_in_after) > 10:
            print(f"    (... {len(only_in_after) - 10} more)")
    if failed:
        print(f"  Failed to load: {failed}")
    print(f"  Pages compared: {len(diffs)}")
    print(f"  Pages with notable changes: {len(notable)}")
    print()

    total_vh_before = sum(d["view_hide_before"] for _, d in diffs)
    total_vh_after = sum(d["view_hide_after"] for _, d in diffs)
    total_bp_before = sum(d["boilerplate_before"] for _, d in diffs)
    total_bp_after = sum(d["boilerplate_after"] for _, d in diffs)
    total_rp_before = sum(d["related_pages_before"] for _, d in diffs)
    total_rp_after = sum(d["related_pages_after"] for _, d in diffs)
    total_text_delta = sum(d["text_size_delta"] for _, d in diffs)

    sec_changed = [(n, d) for n, d in diffs if d["section_count_delta"] != 0]
    last_updated_changed = [
        (n, d) for n, d in diffs
        if d["last_updated_before"] != d["last_updated_after"]
    ]

    print(f"  Total View/Hide artifacts: {total_vh_before} -> {total_vh_after} "
          f"({total_vh_after - total_vh_before:+d})")
    print(f"  Total 'recently added' boilerplate: {total_bp_before} -> "
          f"{total_bp_after} ({total_bp_after - total_bp_before:+d})")
    print(f"  Total related_pages: {total_rp_before} -> {total_rp_after} "
          f"({total_rp_after - total_rp_before:+d})")
    print(f"  Total text size delta: {total_text_delta:+,d} chars")
    print(f"  Pages with section_count change: {len(sec_changed)}")
    print(f"  Pages with last_updated change:  {len(last_updated_changed)}")

    if last_updated_changed[:10]:
        print()
        print("  Last-updated changes (first 10 — DTA content rewrites):")
        for n, d in last_updated_changed[:10]:
            print(f"    {n}: {d['last_updated_before']!r} -> {d['last_updated_after']!r}")


if __name__ == "__main__":
    main()
