"""Compact per-finding view for batch audit reading.

Run from the project root:
    python tools/qc_audit/inspect_compact.py <analysis_name> <row.finding> [<row.finding> ...]

Example:
    python tools/qc_audit/inspect_compact.py Oct-2025-QC-Report_2026-05-07_1428 5.3 9.1 11.2
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QC_DIR = PROJECT_ROOT / "output" / "qc_analysis"
CORPUS = PROJECT_ROOT / "index" / "olg" / "section_chunks.json"


def build_corpus_indexes():
    chunks = json.load(open(CORPUS, encoding="utf-8"))
    by_url, by_title = {}, {}
    for c in chunks:
        md = c.get("metadata", {})
        if md.get("url"):
            by_url.setdefault(md["url"], []).append(c)
        if md.get("page_title"):
            by_title.setdefault(md["page_title"], []).append(c)
    return by_url, by_title


def view(analysis_dir, row_num, finding_idx, by_url, by_title,
         narrative_chars=2000, reasoning_chars=2500):
    p = analysis_dir / "results" / f"row_{row_num:03d}.json"
    d = json.load(open(p, encoding="utf-8"))
    f = d["findings"][finding_idx - 1]

    print(f'═══ Row {row_num}.{finding_idx} ═══ Review #{d.get("review_number")}, Det:{d.get("determination")}, ${d.get("error_amount")}')
    print(f'NARRATIVE: {(d.get("finding_narrative", "") or "")[:narrative_chars]}')
    print(f'\nPOLICY ISSUE: {f.get("policy_issues")}')
    print("\nEXTRACTOR Qs:")
    for q in f.get("search_queries", []):
        print(f"  - {q}")
    judge_qs = f.get("all_search_queries", [])[3:]
    print(f"\nJUDGE FOLLOW-UPS ({len(judge_qs)}):")
    for q in judge_qs:
        print(f"  - {q}")
    print(f'\nVERDICT: {f.get("coverage")} / {f.get("confidence")} ({f.get("searches_performed")} searches)')
    print("\nREASONING:")
    print((f.get("reasoning") or "")[:reasoning_chars])
    if f.get("gap_description"):
        print(f'\nGAP: {f.get("gap_description")[:1500]}')

    trace_urls = set()
    trace_titles = set()
    top_chunks_per_query = []
    for t in f.get("judge_trace", []):
        for tr in t.get("tool_results", []):
            qres = []
            for r in tr.get("results", []):
                if r.get("url"):
                    trace_urls.add(r["url"])
                if r.get("page_title"):
                    trace_titles.add(r["page_title"])
                qres.append((r.get("score"), r.get("page_title"), r.get("section_heading")))
            top_chunks_per_query.append(qres)
    print("\nCITATIONS:")
    for ref in f.get("olg_references", []):
        m = re.search(r"\(https?://[^\)]+\)\s*$", ref)
        url = m.group(0)[1:-1] if m else None
        title = ref[:m.start()].strip() if m else ref
        if url and url in trace_urls:
            tag = "IN_TRACE"
        elif url and url in by_url:
            tag = "IN_CORPUS"
        elif title.split(" > ")[0] in by_title:
            tag = "IN_CORPUS_title"
        else:
            tag = "UNVERIFIED"
        print(f"  [{tag}] {ref}")
    print("\nTOP RESULTS PER SEARCH (compact):")
    for i, qres in enumerate(top_chunks_per_query):
        scores = ", ".join(
            f"{s:.2f}" if isinstance(s, (int, float)) else "?"
            for s, _, _ in qres[:3]
        )
        titles = " | ".join(
            f"{p}>{(sh or '')[:40]}"
            for _, p, sh in qres[:3]
        )
        print(f"  search{i+1} [{scores}]: {titles}")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("analysis", help="Analysis folder name under output/qc_analysis/")
    ap.add_argument("findings", nargs="+", help="One or more <row>.<finding> identifiers")
    args = ap.parse_args()

    analysis_dir = QC_DIR / args.analysis
    if not analysis_dir.exists():
        print(f"Not found: {analysis_dir}", file=sys.stderr)
        sys.exit(1)

    by_url, by_title = build_corpus_indexes()
    for arg in args.findings:
        try:
            row, fi = arg.split(".")
        except ValueError:
            print(f"Bad identifier {arg!r}; expected row.finding (e.g. 5.3)", file=sys.stderr)
            continue
        view(analysis_dir, int(row), int(fi), by_url, by_title)
        print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    main()
