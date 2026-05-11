"""Inspect a single QC investigate finding in depth.

Run from the project root:
    python tools/qc_audit/inspect_finding.py <analysis_name> <row> <finding>

Example:
    python tools/qc_audit/inspect_finding.py Oct-2025-QC-Report_2026-05-07_1428 5 3
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


def inspect(analysis_dir, row_num, finding_idx, by_url, by_title):
    p = analysis_dir / "results" / f"row_{row_num:03d}.json"
    d = json.load(open(p, encoding="utf-8"))
    f = d["findings"][finding_idx - 1]

    print(f"═══ Row {row_num} Finding {finding_idx} ═══")
    print(f'Review #: {d.get("review_number")}, Det: {d.get("determination")}')
    print("Narrative (full):")
    print(d.get("finding_narrative", ""))
    print()
    print(f'POLICY ISSUES: {f.get("policy_issues")}')
    print()
    print("EXTRACTOR QUERIES:")
    for q in f.get("search_queries", []):
        print(f"  - {q}")
    print()
    print("ALL QUERIES (extractor + judge):")
    for q in f.get("all_search_queries", []):
        print(f"  - {q}")
    print()
    print(f'Searches performed: {f.get("searches_performed")} / budget')
    print(f'Coverage: {f.get("coverage")} / Confidence: {f.get("confidence")}')
    print()
    print("REASONING:")
    print(f.get("reasoning", "")[:3000])
    print()
    print("GAP DESCRIPTION:")
    print(f.get("gap_description", ""))
    print()
    print(f'OLG REFERENCES ({len(f.get("olg_references", []))}):')
    trace_urls = set()
    trace_titles = set()
    for t in f.get("judge_trace", []):
        for tr in t.get("tool_results", []):
            for r in tr.get("results", []):
                if r.get("url"):
                    trace_urls.add(r["url"])
                if r.get("page_title"):
                    trace_titles.add(r["page_title"])
    for ref in f.get("olg_references", []):
        m = re.search(r"\(https?://[^\)]+\)\s*$", ref)
        url = m.group(0)[1:-1] if m else None
        title = ref[:m.start()].strip() if m else ref
        if url and url in trace_urls:
            tag = "IN_TRACE"
        elif url and url in by_url:
            tag = "IN_CORPUS_only"
        elif title.split(" > ")[0] in by_title:
            tag = "IN_CORPUS_by_title"
        else:
            tag = "UNVERIFIED"
        print(f"  [{tag}] {ref}")
    print()
    print(f'JUDGE TRACE ({len(f.get("judge_trace", []))} turns):')
    for t in f.get("judge_trace", []):
        print(f'  --- turn {t["turn"]} ({t.get("stop_reason")}) tokens={t.get("tokens")} ---')
        rsn = (t.get("reasoning") or "")
        if rsn:
            print(f"    REASONING: {rsn[:600]}")
        for tc in t.get("tool_calls", []):
            print(f'    Q: "{tc.get("query")}"')
        for tr in t.get("tool_results", []):
            print(f'    {tr.get("result_count")} results:')
            for r in tr.get("results", [])[:5]:
                score = r.get("score")
                score_s = f"{score:.3f}" if isinstance(score, (int, float)) else "?"
                print(f'      [{score_s}] {r.get("page_title")} > {r.get("section_heading")}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("analysis", help="Analysis folder name under output/qc_analysis/")
    ap.add_argument("row", type=int)
    ap.add_argument("finding", type=int)
    args = ap.parse_args()

    analysis_dir = QC_DIR / args.analysis
    if not analysis_dir.exists():
        print(f"Not found: {analysis_dir}", file=sys.stderr)
        sys.exit(1)

    by_url, by_title = build_corpus_indexes()
    inspect(analysis_dir, args.row, args.finding, by_url, by_title)


if __name__ == "__main__":
    main()
