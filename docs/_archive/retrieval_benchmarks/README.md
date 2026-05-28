# Retrieval Benchmarks

Benchmark datasets and reports for measuring retrieval quality across the four sources (OLG, CMR, FNS, CFR).

**Why this exists**: We need measured baselines so architectural changes (new embedding models, hybrid search, reranking) can be evaluated against data, not vibes. See `docs/retrieval_quality_plan.md` for the broader plan.

---

## Methodology

The harness runs raw vector search per question, then asks a cheap LLM (Claude Haiku) to label each retrieved chunk as **RELEVANT**, **PARTIAL**, or **IRRELEVANT** with respect to the question. Scores are computed from those labels.

This replaces the v1 prefix-match approach (`expected_section` against returned `section_number` metadata). The old approach required a domain expert to author one "right" section per question, which was labor-intensive and arbitrary — many real questions have multiple legitimate answers across multiple sections. Judge-based scoring measures retrieval quality more honestly without that labeling burden.

`expected_section` is still kept on each question as informational, surfaced in reports for human cross-check (does the judge's RELEVANT rank-1 chunk land in the section the author guessed?), but it is **not** used to compute metrics.

---

## File layout

```
benchmarks/                                  ← question definitions (input)
  cmr.json
  olg.json
  fns.json
  cfr.json

tools/benchmark_retrieval.py                 ← the harness

docs/retrieval_benchmarks/                   ← reports (output)
  README.md                                  ← this file
  {source}_{label}_{YYYY-MM-DD_HHMM}.md      ← per-run timestamped report
```

---

## Question schema

Each entry in a benchmark JSON file:

```json
{
  "id": "cmr_001",
  "question": "How much can a SNAP household have in bank accounts",
  "topic": "asset limits",
  "difficulty": "narrow",
  "category": "natural",
  "expected_section": "363.110",
  "expected_chunk_id": null,
  "program_filter": ["SNAP"],
  "validated_by": null,
  "notes": "363.110 Asset Eligibility Limits"
}
```

### Required fields

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Stable, unique within source. Format `{source}_{number}` e.g. `cmr_001`. |
| `question` | string | The natural-language question to retrieve against. |
| `program_filter` | list[str] \| null | Programs to include in the search filter. Empty list or null = no filter. |

### Optional but recommended

| Field | Type | Purpose |
|---|---|---|
| `topic` | string | Short label shown in report quick-summary tables. |
| `difficulty` | "broad" / "narrow" / "adversarial" | Difficulty tag (see below). |
| `category` | "natural" / "section_number" / "acronym" / "defined_term" | What kind of query this is. Used for hybrid-search testing. |
| `expected_section` | string \| null | **Informational only.** Section-number prefix the question author guessed would answer the question. Surfaced in reports as a sanity-check column. Not used to compute metrics in v2. |
| `expected_chunk_id` | string \| null | **Informational only.** Same idea, chunk-level. |
| `validated_by` | string | Who signed off on the question. Empty = not validated. |
| `notes` | string | Free-text context — why this question exists, edge cases, known regressions. |

---

## Difficulty tagging

Three tiers, each with a different role:

### `broad`

The question covers a broad area of policy (chapter-level rather than section-specific). Many chunks across multiple sections may legitimately answer it. **Tests: did retrieval land in the right neighborhood.**

Example: "What are the SNAP recertification rules" — many chunks across chapter 366 (and 365) plausibly help.

### `narrow`

The question targets a specific policy point that should map to one or two sections. **Tests: did retrieval find the specific right thing.**

Most questions should be narrow. They're the real test of retrieval quality.

### `adversarial`

Designed to test specific failure modes:
- **Section-number queries**: "What does 364.400 say?" — tests exact-token retrieval (→ hybrid search).
- **Acronym queries**: "What is the VC-1 form?" — tests rare-token handling.
- **Defined-term queries**: "What is the Martinez test?" — tests defined-term retrieval.
- **Cross-program queries**: "Which programs have asset limits?" — tests synthesis-style breadth.

Adversarial cases are where pure dense retrieval is *expected* to struggle. Their value is measuring how much hybrid search / reranking helps.

**Target mix**: roughly 60% narrow, 25% broad, 15% adversarial.

---

## Coverage requirements

Every benchmark should cover the corpus's structural breadth:

- **CMR**: at least one question per chapter (327, 343, 360-367, 701-708 = 18 chapters)
- **CFR**: at least one question per part (271-275, 280, 292 = 7 parts)
- **FNS**: at least one question per chapter (1-14)
- **OLG**: at least one question per major book (SNAP, TAFDC, EAEDC, BP, Cross-Programs, Verification Chart, Forms)

Missing coverage = blind spots. If a configuration silently breaks retrieval for a chapter we don't test, this benchmark won't catch it.

---

## Validation workflow

Validation in v2 is lighter than v1 because we no longer rely on a single "right" section. The remaining concern is whether the question is well-formed and faithfully reflects something a real user would ask.

**Workflow**:

1. **Draft** — Claude (or whoever) writes initial questions. Mark `validated_by: null`.
2. **Review** — Ben (domain expert) reads each question. Pushes back on anything that's not a real question or is ambiguous.
3. **Sign off** — set `validated_by: "ben"` once approved.
4. **Run baseline** — once questions are validated, run the harness. The report can be committed regardless because the judge produces the score, not the author's guess.

For modifications to existing questions: any wording change should reset `validated_by` and re-trigger review.

---

## Running a benchmark

```bash
# Default — runs against current corpus, label "judge-baseline"
python tools/benchmark_retrieval.py --source cmr

# Custom label for testing a configuration variant
python tools/benchmark_retrieval.py --source cmr --label voyage-3-large
python tools/benchmark_retrieval.py --source cmr --label rerank-on
python tools/benchmark_retrieval.py --source cmr --label hybrid+rerank

# Don't write a report file (for quick iteration during drafting)
python tools/benchmark_retrieval.py --source cmr --no-write
```

Reports are written to `docs/retrieval_benchmarks/{source}_{label}_{timestamp}.md`. Commit them — they're the diff history of retrieval quality across changes.

**Cost**: each question fires top-N Haiku judge calls. For CMR (37 questions × top-5) that's ~185 Haiku calls per run, costing pennies.

---

## What the harness does NOT do

The harness is intentionally minimal. It does NOT:

- Call the synthesis layer (no LLM-summarized answer)
- Pull neighboring chunks (`fetch_chunks_by_id` with `neighbors > 0`)
- Apply silent program filters (only filters explicitly listed in the question)
- Rerank, hybrid-search, or use any non-baseline retrieval mode (those are added as flags only when implemented)

**Why**: the benchmark measures **raw retrieval quality** — what comes back from the vector store given a query. Consumer-side enhancements (synthesis, neighbor pulling, etc.) can mask retrieval flaws by smoothing them over downstream. If we want to measure whether the retrieval architecture is good, the harness has to test retrieval and only retrieval.

When new retrieval modes are added (hybrid, rerank, etc.), they go in as explicit `--rerank` / `--hybrid` flags, and each variant gets its own labeled report. The "judge-baseline" label always refers to the dumbest possible retrieval: dense-only, no enhancements, judged by the standard prompt.

---

## Metrics explained

Per the LLM-as-judge methodology, all metrics are computed from rated chunks. Judge label scoring: **RELEVANT = 1.0**, **PARTIAL = 0.5**, **IRRELEVANT = 0.0**.

### Relevance@1

Did rank 1 = RELEVANT? Yes/no, aggregated as a percentage across questions.

This is the headline number. If the user only ever read the first result, what fraction of the time would it actually be useful?

### Relevant@5 (avg)

Average count of RELEVANT chunks in the top 5 results, across questions. Range 0.0 – 5.0.

Tells you the density of strict hits in the top results.

### Useful@5 (avg)

Average count of (RELEVANT or PARTIAL) chunks in the top 5 results, across questions. Range 0.0 – 5.0.

Tells you the density of "this is worth showing the user" hits.

### Mean rank-weighted score

For each question, sum over top-5 of (weight × score) where:

- weight = `[1.0, 0.7, 0.5, 0.3, 0.2]` for ranks 1-5
- score = 1.0 / 0.5 / 0.0 for RELEVANT / PARTIAL / IRRELEVANT

Then average across questions. Range 0.0 – 2.7. (This is essentially DCG with discrete relevance.)

A perfect 2.7 means every question's top-5 was [RELEVANT, RELEVANT, RELEVANT, RELEVANT, RELEVANT]. A useful chunk ranked higher pays more — moving a result from rank 4 to rank 2 measurably improves this score even if the Top-K bucket doesn't change.

### Interpreting judge ratings

The judge categorizes chunks RELEVANT / PARTIAL / IRRELEVANT, but the *meaning* of these ratings has nuance worth preserving when reading reports:

- **RELEVANT**: chunk directly contains the answer or substantively addresses the question.
- **PARTIAL** can mean several things — distinguishing them is human work:
  - *Right area, wrong specifics*: chunk discusses the topic but doesn't answer the specific question (e.g., asset *transfer* rules when asked about asset *limit*).
  - *Right answer, deferred to external source*: chunk correctly says "see mass.gov for current dollar amounts" because the value changes yearly. The chunk is doing the right thing for policy reasons, not failing.
  - *Adjacent chunk of same section*: the right section split into multiple chunks, but a sibling chunk would have been the more direct answer.
- **IRRELEVANT**: chunk is in the wrong area of policy entirely.

Don't treat all PARTIALs as failures. When auditing low Relevance@1 scores, read the judge's reason — sometimes the chunk is doing exactly what it should, and the "failure" is actually correct policy design.

### Why not prefix-match scoring (v1)

V1 scored on `section_number` prefix-match against an author-supplied `expected_section`. Two problems:

1. **Author burden**: someone has to pick the "right" section per question. Many questions have multiple legitimate sections that answer them, and the author's guess doesn't necessarily reflect what the user would find most useful.
2. **Reward target mismatch**: prefix-match rewards "the search pulled the section the author guessed," not "the search pulled a chunk that helps the user answer their question." The judge measures the latter directly.

The v1 reports (`*_baseline_*.md`, `*_v2-draft_*.md`) are kept as historical baselines for prefix-match scoring. They are not directly comparable to v2 reports.

---

## Authoring per-source benchmarks

Each source has its own structure. Use these guides when authoring `olg.json`, `fns.json`, or `cfr.json`.

### CMR (already authored — use as the template)

- **Structure**: 18 chapters, ~592 sections. Hierarchical paren markers `(A)→(1)→(a)→1.` within sections.
- **Section identifier**: `section_number` (e.g., `363.140`).
- **Programs**: `SSP`, `Hearings`, `SNAP`, `Program Integrity`, `EA`. All sections tagged. Use these in `program_filter`.
- **Coverage target**: at least 1 question per chapter (327, 343, 360-367, 701-708).
- **Adversarial cases that work**: section number lookups (`"What does 363.140 cover"`), acronyms (ADH, EPSDT), defined terms (Public Assistance household).

### OLG (DTA Online Guide)

- **Structure**: ~1,164 pages, ~6,511 section chunks. Pages are HTML scraped from a MadCap Flare site. Hierarchy is breadcrumb-based, not numeric.
- **Section identifier**: not a `section_number` like CMR. Use `chunk_id` for `expected_chunk_id` (e.g., `sec__SNAP__Eligibility__Stu_Students__035`). The judge methodology doesn't need a section identifier anyway — only the `expected_chunk_id` informational field uses it.
- **Programs**: `SNAP`, `TAFDC`, `EAEDC`, `Cross-Program`, `BP`. Use these in `program_filter`.
- **Coverage target**: at least 1 question per major book (SNAP, TAFDC, EAEDC, BP, Cross-Programs, Verification Chart, Forms).
- **OLG-specific question types worth including**: Verification Chart lookups (e.g., "What proofs are needed for identity"), table-heavy pages (interview process tables), policy procedural questions ("How does an EA worker calculate ABAWD"), VC-1 form references.
- **OLG quirk to test**: Q35-style queries that should hit the manually-overridden Verification Chart chunks (12 topical chunks, not 32 alphabetical). Make sure those score well.

### FNS (Handbook 310)

- **Structure**: 14 chapters, ~860 chunks. Numeric section IDs (e.g., `1045.2`). Chapters 7-11+13 are SNAP policy; rest is QC process.
- **Section identifier**: `section_number` like CMR.
- **Programs**: `SNAP`, `QC_Process`. Most external users only care about SNAP chapters.
- **Coverage target**: at least 1 question per chapter (1-14). Weight SNAP chapters heavier (most policy queries land there).
- **FNS-specific question types worth including**: Numbered step procedures ("Step 2 of evaluating evidence"), example-block reference questions, definitions sections (§130, §1320 NEGATIVE DEFINITIONS), side-by-side example box content.
- **FNS quirk to test**: §1170.5 / §1065.2 / §726.7 / §812.2 — these were canonical sections during cleanup. Make sure questions pulling from them perform well as a regression check.

### CFR (Title 7 SNAP)

- **Structure**: 7 parts (271-275, 280, 292), 118 sections, 1,623 chunks. Hierarchy `(a)→(1)→(i)→(A)`.
- **Section identifier**: `section_number` like CMR (e.g., `273.10`).
- **Programs** (section-level): `SNAP`, `Issuance`, `Administration`, `QC`, `Disaster`, `Summer-EBT`.
- **Coverage target**: at least 1 question per part (271, 272, 273, 274, 275, 280, 292).
- **CFR-specific question types worth including**: Definition lookups (§271.2, §292.2 are dedicated definition sections — each defined term is its own chunk), summer EBT questions (Part 292 was a recent addition), quality control statistical sampling (Part 275).
- **CFR quirk to test**: 16 manually-rewritten tables in 273.18 / 275.3 / 275.11. Questions that should hit those should score well — if they regress, the parsed JSONs may have been clobbered.

### Cross-source considerations

- **Acronym questions are valuable in every benchmark**. Domain has many: TAFDC, EAEDC, AORD, IPV, ADH, ABAWD, EBT, MH, EDP, FEP, ESP, EPSDT, VC-1, etc. These stress dense retrieval and will measure hybrid search wins.
- **Section-number queries** ("What does X say?") should appear in every benchmark — they're the canonical hybrid-search use case.
- **Don't over-fit to known issues** — questions should be realistic, not constructed to pass or fail. The point is measuring retrieval, not curating wins.

---

## Adding a new source: workflow

1. Create `benchmarks/{source}.json` following the schema above
2. Cover all chapters/parts/major books per the coverage requirements
3. Mix difficulty per the 60/25/15 target
4. Mark all questions `validated_by: null` until reviewed
5. Get Ben to validate
6. Run baseline: `python tools/benchmark_retrieval.py --source {source}`
7. Commit benchmark JSON and the resulting report
8. Move on to retrieval-architecture experiments — variant labels (`voyage-3-large`, `rerank-on`, `hybrid+rerank`, etc.)

---

## Benchmark drift / versioning

If a benchmark changes substantively (questions added/removed, expected answers revised), comparison to old reports breaks. Two options:

- **In-place update**: edit `cmr.json`, accept that old reports are no longer directly comparable. Rerun a fresh baseline.
- **Versioned**: rename to `cmr_v2.json`, keep `cmr.json` stable. Two parallel benchmarks track different things.

Default to in-place updates. Versioning only when there's a specific reason to keep both (e.g., we want to track the same questions over years AND have a richer benchmark for current analysis).

When making in-place changes, mention it in the commit message — future-you will appreciate the heads-up that pre-commit reports are baselined against the old questions.
