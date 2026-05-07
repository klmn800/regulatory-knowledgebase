"""Walk every finding in a QC investigate run and validate citations.

Run from the project root:
    python tools/qc_audit/walker.py <analysis_name>

Where <analysis_name> is the folder under output/qc_analysis/, e.g.
"Oct-2025-QC-Report_2026-05-07_1428". Writes audit_walk.json into that
analysis directory and prints high-level stats.

Field path note: chunk URLs and titles live in metadata.url and
metadata.page_title, not at top-level. Don't trust audit code that
uses c.get('url') — it always returns None.
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


def parse_ref(ref_str):
    m = re.search(r"\(https?://[^\)]+\)\s*$", ref_str)
    url = m.group(0)[1:-1] if m else None
    title_part = ref_str[:m.start()].strip() if m else ref_str
    return title_part, url


def validate_citation(ref_str, trace_urls, trace_titles, by_url, by_title):
    """Status: in_trace | in_corpus | unverified.

    in_corpus means the page exists in section_chunks.json but didn't appear
    in the post-seed trace — typically because the seed search retrieved it
    but seed isn't preserved in trace. Use seed-replay (rag.query) to
    confirm before claiming "ungrounded."
    """
    title_part, url = parse_ref(ref_str)
    if url and url in trace_urls:
        return "in_trace", None
    if any(title_part.split(" > ")[0] == t for t in trace_titles):
        return "in_trace", None
    if url and url in by_url:
        return "in_corpus", f"corpus has {len(by_url[url])} chunks at this URL"
    page_title = title_part.split(" > ")[0]
    if page_title in by_title:
        return "in_corpus", f'corpus has page "{page_title}"'
    return "unverified", None


def walk_row(row_path, by_url, by_title):
    d = json.load(open(row_path, encoding="utf-8"))
    out = {
        "row_index": d["row_index"],
        "review_number": d.get("review_number"),
        "apid": d.get("apid"),
        "error_amount": d.get("error_amount"),
        "determination": d.get("determination"),
        "error_type": d.get("error_type"),
        "narrative": d.get("finding_narrative", "")[:500],
        "findings": [],
    }
    for fi, f in enumerate(d.get("findings", []), 1):
        trace_urls = set()
        trace_titles = set()
        for t in f.get("judge_trace", []):
            for tr in t.get("tool_results", []):
                for r in tr.get("results", []):
                    if r.get("url"):
                        trace_urls.add(r["url"])
                    if r.get("page_title"):
                        trace_titles.add(r["page_title"])
        ref_status = []
        for ref in f.get("olg_references", []):
            status, note = validate_citation(
                ref, trace_urls, trace_titles, by_url, by_title
            )
            ref_status.append({"ref": ref, "status": status, "note": note})
        turn_qs = []
        for t in f.get("judge_trace", []):
            for tc in t.get("tool_calls", []):
                turn_qs.append(tc.get("query"))
        out["findings"].append({
            "finding_index": fi,
            "policy_issues": f.get("policy_issues", "")[:400],
            "extractor_queries": f.get("search_queries", []),
            "all_search_queries": f.get("all_search_queries", []),
            "judge_followup_queries": turn_qs,
            "searches_performed": f.get("searches_performed"),
            "coverage": f.get("coverage"),
            "confidence": f.get("confidence"),
            "reasoning": f.get("reasoning", ""),
            "gap_description": f.get("gap_description", ""),
            "olg_refs": ref_status,
            "trace_url_count": len(trace_urls),
            "turns": len(f.get("judge_trace", [])),
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("analysis", help="Analysis folder name under output/qc_analysis/")
    args = ap.parse_args()

    analysis_dir = QC_DIR / args.analysis
    if not analysis_dir.exists():
        print(f"Not found: {analysis_dir}", file=sys.stderr)
        sys.exit(1)

    by_url, by_title = build_corpus_indexes()

    rows = []
    for p in sorted(analysis_dir.glob("results/row_*.json")):
        rows.append(walk_row(p, by_url, by_title))

    out_path = analysis_dir / "audit_walk.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} with {len(rows)} rows")

    total = placeholders = total_refs = 0
    coverage = {}
    conf = {}
    refs = {"in_trace": 0, "in_corpus": 0, "unverified": 0}
    budget = {}

    for r in rows:
        for f in r["findings"]:
            total += 1
            pi = (f["policy_issues"] or "").lower()
            if "extraction returned no findings" in pi or "case is correct" in pi:
                placeholders += 1
            coverage[f["coverage"]] = coverage.get(f["coverage"], 0) + 1
            conf[f["confidence"]] = conf.get(f["confidence"], 0) + 1
            budget[f["searches_performed"]] = budget.get(f["searches_performed"], 0) + 1
            for rs in f["olg_refs"]:
                total_refs += 1
                refs[rs["status"]] += 1

    print(f"\nTotal findings: {total}")
    print(f"Placeholders: {placeholders}")
    print(f"Real findings: {total - placeholders}")
    print(f"Coverage: {coverage}")
    print(f"Confidence: {conf}")
    print(f"Search budget usage: {sorted(budget.items())}")
    print(f"Total citations: {total_refs}")
    print(f"Citation grounding: {refs}")


if __name__ == "__main__":
    main()
