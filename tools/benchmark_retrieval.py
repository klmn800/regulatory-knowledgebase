"""
Retrieval Quality Benchmark Harness — LLM-as-judge edition.

Loads a benchmark JSON file, runs raw vector search per question, has
Claude Haiku judge whether each retrieved chunk actually helps answer
the question, scores the run on judge ratings, and writes a
timestamped markdown report.

Design principles:
- RAW retrieval only. No synthesis. No reranking. No auto-neighbor
  pulling. No silent program filters. Only what was explicitly asked
  for in the benchmark JSON.
- Scoring is LLM-as-judge. For each (question, chunk) pair we ask a
  cheap model to label the chunk RELEVANT / PARTIAL / IRRELEVANT.
- `expected_section` is informational only — surfaced in the report
  for human cross-check, not used to compute metrics.
- Output is committed markdown for diff history across runs.

Usage:
    python tools/benchmark_retrieval.py --source cmr
    python tools/benchmark_retrieval.py --source cmr --label judge-baseline
"""

import argparse
import configparser
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rag.query import create_client, search_with_client


BENCHMARK_DIR = PROJECT_ROOT / "benchmarks"
REPORT_DIR = PROJECT_ROOT / "docs" / "retrieval_benchmarks"
CONFIG_FILE = PROJECT_ROOT / "config.ini"

DEFAULT_TOP_N = 5
JUDGE_MODEL = "claude-haiku-4-5-20251001"
JUDGE_MAX_TOKENS = 200
RANK_WEIGHTS = [1.0, 0.7, 0.5, 0.3, 0.2]
CATEGORY_SCORES = {"RELEVANT": 1.0, "PARTIAL": 0.5, "IRRELEVANT": 0.0}

JUDGE_SYSTEM_PROMPT = (
    "You are evaluating whether a retrieved policy text helps answer "
    "a user's question about Massachusetts DTA (Department of "
    "Transitional Assistance) policy. The user is searching the "
    "regulatory corpus and got back a chunk of policy text. Your job: "
    "judge how relevant the chunk is to the question."
)

JUDGE_USER_TEMPLATE = """Question: {question}

Retrieved chunk:
{chunk_text}

Categorize the chunk:
- RELEVANT: directly addresses the question; would help the user answer it
- PARTIAL: related topic / shares keywords but doesn't actually answer the specific question
- IRRELEVANT: off-topic, wrong area of policy

Respond with JSON only: {{"category": "RELEVANT"|"PARTIAL"|"IRRELEVANT", "reason": "<one short sentence>"}}"""


def load_benchmark(source: str) -> dict:
    path = BENCHMARK_DIR / f"{source}.json"
    if not path.exists():
        print(f"Error: benchmark file not found: {path}")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    if not config.has_option("api", "anthropic_api_key"):
        print(f"Error: No anthropic_api_key found in {CONFIG_FILE}")
        sys.exit(1)
    return config


def _section_field(benchmark: dict) -> str:
    return benchmark.get("matching", {}).get("section_field", "section_number")


def _parse_judge_response(text: str) -> dict:
    text = text.strip()
    if not text:
        return {"category": "IRRELEVANT", "reason": "parse error: empty response"}

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {"category": "IRRELEVANT",
                "reason": f"parse error: no JSON found in: {text[:120]}"}

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        return {"category": "IRRELEVANT",
                "reason": f"parse error: {e}"}

    cat = str(data.get("category", "")).strip().upper()
    if cat not in CATEGORY_SCORES:
        return {"category": "IRRELEVANT",
                "reason": f"parse error: unknown category '{cat}'"}

    reason = str(data.get("reason", "")).strip() or "(no reason given)"
    return {"category": cat, "reason": reason}


def judge_chunk(client: anthropic.Anthropic, question: str,
                chunk_text: str) -> dict:
    user_msg = JUDGE_USER_TEMPLATE.format(
        question=question, chunk_text=chunk_text
    )
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=JUDGE_MAX_TOKENS,
                temperature=0,
                system=JUDGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(
                getattr(b, "text", "") for b in resp.content
                if getattr(b, "type", None) == "text"
            )
            return _parse_judge_response(text)
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"    [rate limit, waiting {wait}s]", flush=True)
            time.sleep(wait)
            continue
        except anthropic.APIError as e:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"    [API error {e}, retry in {wait}s]", flush=True)
                time.sleep(wait)
                continue
            return {"category": "IRRELEVANT", "reason": f"API error: {e}"}
        except Exception as e:
            return {"category": "IRRELEVANT", "reason": f"unexpected error: {e}"}

    return {"category": "IRRELEVANT",
            "reason": "rate limited beyond retry budget"}


def score_question(judged: list[dict]) -> dict:
    judged_top5 = judged[:5]
    rank1_cat = judged_top5[0]["judge"]["category"] if judged_top5 else None

    relevant_count = sum(
        1 for j in judged_top5 if j["judge"]["category"] == "RELEVANT"
    )
    useful_count = sum(
        1 for j in judged_top5
        if j["judge"]["category"] in ("RELEVANT", "PARTIAL")
    )

    rank_weighted = 0.0
    for i, j in enumerate(judged_top5):
        if i >= len(RANK_WEIGHTS):
            break
        cat_score = CATEGORY_SCORES.get(j["judge"]["category"], 0.0)
        rank_weighted += RANK_WEIGHTS[i] * cat_score

    return {
        "rank1_category": rank1_cat,
        "relevant_at_5": relevant_count,
        "useful_at_5": useful_count,
        "rank_weighted": rank_weighted,
    }


def summarize(scored: list[dict]) -> dict:
    valid = [s for s in scored if "error" not in s]
    total = len(valid)
    if total == 0:
        return {"total": 0}

    rel_at_1 = sum(
        1 for s in valid if s["scores"]["rank1_category"] == "RELEVANT"
    )
    avg_rel_at_5 = sum(s["scores"]["relevant_at_5"] for s in valid) / total
    avg_useful_at_5 = sum(s["scores"]["useful_at_5"] for s in valid) / total
    avg_rank_weighted = sum(s["scores"]["rank_weighted"] for s in valid) / total

    return {
        "total": total,
        "rel_at_1": rel_at_1,
        "rel_at_1_pct": 100.0 * rel_at_1 / total,
        "avg_rel_at_5": avg_rel_at_5,
        "avg_useful_at_5": avg_useful_at_5,
        "avg_rank_weighted": avg_rank_weighted,
    }


def run_benchmark(
    source: str,
    top_n: int,
    label: str,
    model_override: str | None = None,
    collection_suffix: str | None = None,
) -> dict:
    benchmark = load_benchmark(source)
    section_field = _section_field(benchmark)
    config = load_config()
    api_key = config.get("api", "anthropic_api_key")
    judge_client = anthropic.Anthropic(api_key=api_key)

    print(f"Loaded {len(benchmark['questions'])} questions for source={source}")
    if model_override:
        print(f"  Model override: {model_override}")
    if collection_suffix:
        print(f"  Collection suffix: _{collection_suffix}")
    print(f"Initializing retrieval client...", flush=True)
    clients = create_client(
        source=source,
        model_override=model_override,
        collection_suffix=collection_suffix,
    )

    print(f"Running queries (top_n={top_n}) and judging...", flush=True)

    scored = []
    for q in benchmark["questions"]:
        program_filter = q.get("program_filter")
        try:
            response = search_with_client(
                q["question"], clients,
                programs=program_filter,
                top_n=top_n,
            )
            results = response["results"]
        except Exception as e:
            print(f"  [{q['id']}] RETRIEVAL ERROR: {e}", flush=True)
            scored.append({
                "question": q,
                "error": f"retrieval: {e}",
                "judged": [],
                "scores": None,
            })
            continue

        judged = []
        for r in results[:top_n]:
            verdict = judge_chunk(judge_client, q["question"], r.get("text", ""))
            judged.append({
                "rank": r["rank"],
                "score": r["score"],
                "id": r["id"],
                "metadata": r["metadata"],
                "text": r.get("text", ""),
                "judge": verdict,
            })

        scores = score_question(judged)
        scored.append({
            "question": q,
            "judged": judged,
            "scores": scores,
        })

        topic = (q.get("topic", "") or "")[:30]
        rank1 = scores["rank1_category"] or "?"
        rel5 = scores["relevant_at_5"]
        useful5 = scores["useful_at_5"]
        rw = scores["rank_weighted"]
        print(f"  [{q['id']}] r1={rank1:11s}  rel@5={rel5}  useful@5={useful5}  "
              f"rw={rw:.2f}  {topic}", flush=True)

    summary = summarize(scored)

    return {
        "source": source,
        "label": label,
        "top_n": top_n,
        "judge_model": JUDGE_MODEL,
        "embedding_model": clients.get("model", ""),
        "collection_suffix": collection_suffix or "",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "benchmark_meta": {
            "description": benchmark.get("description", ""),
            "established": benchmark.get("established", ""),
            "section_field": section_field,
        },
        "summary": summary,
        "scored": scored,
    }


def _md_escape_cell(text: str) -> str:
    if text is None:
        return ""
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict) -> str:
    lines = []
    s = report["source"].upper()
    label = report["label"]
    ts = report["timestamp"]
    benchmark = report["scored"]

    lines.append(f"# {s} Retrieval Benchmark — {label}")
    lines.append("")
    lines.append(f"**Run**: {ts}  ")
    lines.append(f"**Source**: {report['source']}  ")
    lines.append(f"**Label**: {label}  ")
    lines.append(f"**Top-N retrieved + judged**: {report['top_n']}  ")
    embed_model = report.get("embedding_model", "")
    if embed_model:
        lines.append(f"**Embedding model**: `{embed_model}`  ")
    coll_suffix = report.get("collection_suffix", "")
    if coll_suffix:
        lines.append(f"**Collection suffix**: `_{coll_suffix}`  ")
    lines.append(f"**Judge model**: `{report['judge_model']}`  ")
    lines.append(f"**Methodology**: LLM-as-judge — Claude Haiku rates each "
                 f"chunk RELEVANT / PARTIAL / IRRELEVANT.  ")
    lines.append(f"**Benchmark**: {report['benchmark_meta'].get('description', '')}  ")
    lines.append("")

    summary = report["summary"]
    if summary.get("total", 0) > 0:
        total = summary["total"]
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value | Notes |")
        lines.append("|---|---|---|")
        lines.append(f"| Relevance@1 | {summary['rel_at_1']}/{total} "
                     f"({summary['rel_at_1_pct']:.0f}%) | "
                     f"Did rank 1 = RELEVANT? |")
        lines.append(f"| Relevant@5 (avg) | {summary['avg_rel_at_5']:.2f} / 5 | "
                     f"Avg # of RELEVANT chunks in top 5 |")
        lines.append(f"| Useful@5 (avg) | {summary['avg_useful_at_5']:.2f} / 5 | "
                     f"Avg # of (RELEVANT or PARTIAL) chunks in top 5 |")
        lines.append(f"| Mean rank-weighted score | {summary['avg_rank_weighted']:.3f} "
                     f"/ 2.7 | "
                     f"Sum of (weight × score) over top 5; weights "
                     f"[1.0, 0.7, 0.5, 0.3, 0.2]; "
                     f"score RELEVANT=1.0 / PARTIAL=0.5 / IRRELEVANT=0.0 |")
        lines.append("")

    lines.append("## Quick Summary Table")
    lines.append("")
    lines.append("| # | ID | Topic | Rank-1 Judge | Rank-1 Sim Score | "
                 "Relevant@5 | Useful@5 | RW |")
    lines.append("|---|---|---|---|---|---|---|---|")

    for i, score in enumerate(benchmark, start=1):
        q = score["question"]
        if "error" in score:
            lines.append(
                f"| {i} | {q['id']} | "
                f"{_md_escape_cell(q.get('topic', ''))} | "
                f"**ERROR** | - | - | - | - |"
            )
            continue

        scores = score["scores"]
        judged = score["judged"]
        rank1_cat = scores["rank1_category"] or "?"
        rank1_sim = judged[0]["score"] if judged else None
        sim_str = f"{rank1_sim:.3f}" if rank1_sim is not None else "-"
        rank1_md = (f"**{rank1_cat}**"
                    if rank1_cat in ("PARTIAL", "IRRELEVANT", "?")
                    else rank1_cat)
        lines.append(
            f"| {i} | {q['id']} | "
            f"{_md_escape_cell(q.get('topic', ''))} | "
            f"{rank1_md} | {sim_str} | "
            f"{scores['relevant_at_5']} | "
            f"{scores['useful_at_5']} | "
            f"{scores['rank_weighted']:.2f} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Per-Question Detail")
    lines.append("")
    lines.append("Top 5 results per question with judge verdicts and full "
                 "chunk text. Use this to spot-check whether the judge's "
                 "rating makes sense.")
    lines.append("")

    section_field = report["benchmark_meta"].get("section_field", "section_number")

    for score in benchmark:
        q = score["question"]
        rank1_cat = (score["scores"]["rank1_category"]
                     if score.get("scores") else None)

        header_status = rank1_cat or "ERROR"
        lines.append(f"### {q['id']} — {q.get('topic', '')} "
                     f"(rank-1: {header_status})")
        lines.append("")
        lines.append(f"**Question**: {q['question']}  ")

        prog_filter = q.get("program_filter")
        if prog_filter:
            lines.append(f"**Program filter**: `{prog_filter}`  ")
        else:
            lines.append("**Program filter**: (none)  ")

        expected = q.get("expected_section")
        if expected:
            judged_list = score.get("judged") or []
            top1 = judged_list[0] if judged_list else None
            if top1 and rank1_cat == "RELEVANT":
                got_section = top1["metadata"].get(section_field, "")
                matches = (got_section
                           and str(got_section).startswith(expected))
                marker = ("section-author intuition agrees" if matches
                          else "section-author intuition disagrees with judge")
                lines.append(
                    f"**Expected section (for reference)**: "
                    f"`{expected}` — judge picked rank-1 RELEVANT chunk "
                    f"in section `{got_section}` ({marker})  "
                )
            else:
                lines.append(
                    f"**Expected section (for reference)**: `{expected}`  "
                )

        if q.get("notes"):
            lines.append(f"**Notes**: {q['notes']}  ")

        if "error" in score:
            lines.append("")
            lines.append(f"**ERROR**: {score['error']}")
            lines.append("")
            continue

        scores_d = score["scores"]
        lines.append(f"**Scores**: Relevant@5 = {scores_d['relevant_at_5']}, "
                     f"Useful@5 = {scores_d['useful_at_5']}, "
                     f"rank-weighted = {scores_d['rank_weighted']:.2f}  ")
        lines.append("")

        for j in score["judged"]:
            meta = j["metadata"]
            sec = meta.get(section_field, "")
            sec_title = meta.get("section_title", "")
            verdict = j["judge"]
            cat = verdict["category"]
            reason = verdict["reason"]

            if cat == "RELEVANT":
                badge = "RELEVANT"
            elif cat == "PARTIAL":
                badge = "PARTIAL"
            else:
                badge = "IRRELEVANT"

            lines.append(f"#### Rank {j['rank']} — {badge} "
                         f"(sim {j['score']:.3f})")
            lines.append("")
            lines.append(f"- **Chunk ID**: `{j['id']}`")
            lines.append(f"- **Section**: `{sec}` — {sec_title}")
            chunk_n = meta.get("chunk_n")
            chunk_total = meta.get("chunk_total")
            if chunk_n is not None and chunk_total and chunk_total > 1:
                lines.append(f"- **Chunk position**: {chunk_n} / {chunk_total}")
            program = meta.get("program")
            if program:
                lines.append(f"- **Program**: {program}")
            hierarchy_path = meta.get("hierarchy_path", "")
            if hierarchy_path:
                lines.append(f"- **Hierarchy**: {hierarchy_path}")
            lines.append(f"- **Judge reason**: {reason}")
            lines.append("")
            lines.append("```")
            lines.append(j["text"])
            lines.append("```")
            lines.append("")

        lines.append("")

    return "\n".join(lines)


def write_report(report: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    label = report["label"]
    fname = f"{report['source']}_{label}_{ts}.md"
    out_path = REPORT_DIR / fname

    md = render_markdown(report)
    out_path.write_text(md, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Run a retrieval benchmark using LLM-as-judge scoring.",
    )
    parser.add_argument(
        "--source", required=True,
        choices=["olg", "fns", "cmr", "cfr"],
        help="Source to benchmark",
    )
    parser.add_argument(
        "--top-n", type=int, default=DEFAULT_TOP_N,
        help=f"Top-N results per question to retrieve and judge "
             f"(default: {DEFAULT_TOP_N}).",
    )
    parser.add_argument(
        "--label", default="judge-baseline",
        help="Configuration label for the output filename "
             "(e.g., 'judge-baseline', 'judge-rerank'). "
             "Default: judge-baseline.",
    )
    parser.add_argument(
        "--model",
        help="Override the embedding model from config.ini (must match the "
             "model used to embed the target collection). For evaluation runs.",
    )
    parser.add_argument(
        "--collection-suffix",
        help="Append '_<suffix>' to collection names so this run queries "
             "side-by-side variant collections (e.g., voyage4large).",
    )
    parser.add_argument(
        "--no-write", action="store_true",
        help="Print results to stdout but don't write a report file.",
    )
    args = parser.parse_args()

    report = run_benchmark(
        args.source, args.top_n, args.label,
        model_override=args.model,
        collection_suffix=args.collection_suffix,
    )

    summary = report["summary"]
    if summary.get("total", 0) > 0:
        print()
        print(f"=== Summary ({args.source} / {args.label}) ===")
        total = summary["total"]
        print(f"  Relevance@1:           {summary['rel_at_1']}/{total} "
              f"({summary['rel_at_1_pct']:.0f}%)")
        print(f"  Relevant@5 (avg):      {summary['avg_rel_at_5']:.2f} / 5")
        print(f"  Useful@5 (avg):        {summary['avg_useful_at_5']:.2f} / 5")
        print(f"  Mean rank-weighted:    {summary['avg_rank_weighted']:.3f} / 2.7")

    if not args.no_write:
        out_path = write_report(report)
        print(f"\nReport written: {out_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
