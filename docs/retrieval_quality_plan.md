# Retrieval Quality Plan — Post-Chunk-Cleanup Work

**Status**: Phase 1 + 2 + 2.5 COMPLETE (2026-05-04). Architecture deployed stack-wide: voyage-context-3 mode A (sections) + voyage-4-large (broad tier). All 4 production sources re-embedded; no voyage-3 vectors remain. Phase 3 (hybrid search) is next — needs design discussion before code.
**Context**: All four sources (OLG, CMR, FNS, CFR) are now cleanly chunked and embedded. This document captures the next arc of work — measuring retrieval quality, evaluating architectural improvements, and protecting the cleanup work — *before* moving on to calibrating the consumers (synthesis, comparator, author, QC analyzer) of the RAG.
**Cost**: Modest. Re-embeds are ~$0.30 each. Reranker and judge calls are pennies-per-query.

## Strategy update (2026-05-04): CMR-first

After establishing the CMR judge-baseline (57% Rel@1), the decision is to **stick with CMR through Phase 2 (embedding model evaluation) before authoring OLG/FNS/CFR benchmarks.** The reasoning: validate that the methodology has predictive power and that an embedding swap actually moves the numbers meaningfully, before investing in three more benchmark authoring efforts.

If Phase 2 on CMR shows a meaningful win (e.g., voyage-context-3 lifts Rel@1 from 57% → 70%), that's evidence the methodology + lever combination is worth scaling to other sources. If Phase 2 shows no movement, the OLG/FNS/CFR benchmark authoring is wasted effort under this configuration.

## Phase 1 + Phase 2 results (CMR — all variants)

| Metric | voyage-3 baseline | voyage-4-large | **vctx3 mode A (with prefix)** | vctx3 mode B (no prefix) |
|---|---|---|---|---|
| **Relevance@1** | 21/37 (57%) | 22/37 (59%) | **24/37 (65%)** | 22/37 (59%) |
| **Relevant@5 (avg)** | 1.57 / 5 | 1.51 / 5 | **1.78 / 5** | 1.62 / 5 |
| **Useful@5 (avg)** | 4.54 / 5 | 4.68 / 5 | 4.62 / 5 | 4.54 / 5 |
| **Mean rank-weighted** | 1.766 | 1.799 | **1.861** | 1.780 |

**Winner: voyage-context-3 mode A (with context prefix retained).** +8pp Rel@1, +18% Relevant@5, +5% rank-weighted vs voyage-3 baseline.

Reports:
- `docs/retrieval_benchmarks/cmr_judge-baseline_2026-05-04_1025.md`
- `docs/retrieval_benchmarks/cmr_voyage-4-large_2026-05-04_1141.md`
- `docs/retrieval_benchmarks/cmr_voyage-context-3-modeA_2026-05-04_1241.md`
- `docs/retrieval_benchmarks/cmr_voyage-context-3-modeB-noprefix_2026-05-04_1318.md`

**Findings**:
- Context prefix and neighbor-aware embedding are **complementary, not redundant**. Mode B regressed back to ~voyage-4-large levels — the prefix was pulling weight all along.
- Adversarial queries (section numbers, acronyms) still weak across all dense variants. Phase 3 (hybrid search) remains the lever.
- voyage-context-3 has a 32K-token per-doc context window. Some CMR chapter chunks exceed it; chapter-tier embedding fails. Use voyage-4-large for broad-tier (option A from CMR analysis).
- Methodology shifted from prefix-match (v1) to LLM-as-judge (v2) during Phase 1. Methodology is sound — produces stable rankings.

**Notable findings** captured during baseline:
- Useful@5 ≫ Relevant@5 (4.54 vs 1.57): retrieval lands in the right neighborhood but rarely surfaces the most direct answer first. This is the lever reranking is supposed to pull.
- Adversarial section-number lookup (cmr_031) failed as predicted — hybrid search prediction validated.
- One real data quality bug surfaced: CMR 704.135 doubled-character artifact (logged in `docs/data_quality_issues.md`).

---

## Why this exists

The cleanup arc just finished raised chunk quality across all four sources to a consistent bar. But "cleaner chunks" is not the same as "better retrieval." The CMR cleanup is the only source with measured before/after numbers (Top-1 55%→70%, miss rate 15%→5%). OLG, FNS, and CFR have no measured retrieval baselines — only chunk-level validation (no mid-word breaks, position metadata, etc.).

Before we start tuning the agents and tools that consume RAG results, we need to:

1. Make the cleanup work durable (un-gitignore the manual edits)
2. Clear out stale artifacts (old comparator results, search history)
3. Establish measured retrieval baselines for all four sources
4. Investigate three architectural levers that are known to lift retrieval quality
5. Then decide what to keep, based on data

---

## Phase 0 — Protect & clean up

Quick housekeeping. Should land before any retrieval research starts.

### 0.1 Un-gitignore parsed_sections JSONs

Today, `index/cfr/parsed_sections/*.json` and `index/fns/parsed_sections/*.json` are gitignored. They contain irreplaceable manual work:

- **CFR**: 16 hand-rewritten multi-column tables in 273.18 / 275.3 / 275.11. Procedure to redo them is documented in `docs/cfr_pipeline.md` but it's a real chunk of work to recover.
- **FNS**: 56 sections re-written by the Pass 1 LLM column cleanup ($0.30 to re-run) plus 8 sections deduped by Pass 2.

A `git clean -fdx` or fresh checkout drops all of this on the floor. **Action**: amend `.gitignore` to track `index/{cfr,fns,olg,cmr}/parsed_sections/*.json` while keeping the chunk outputs and ChromaDB binaries gitignored. Parser JSONs are no longer "regenerable" once they have manual edits — the argument for ignoring them has flipped.

### 0.2 Clear stale search history

`output/search_history.db` has Ask-tab evidence captured against old chunk IDs and old corpus state. Some chunks no longer exist (Phase 3 OLG exclusions removed pages); others have new IDs. **Action**: clear the database, or add a "re-embedded since" marker to old entries. Easiest: clear it and treat it as fresh after the cleanup arc.

### Comparator re-run is NOT in Phase 0

The 270-section comparator output is stale (generated against the OLD FNS chunks pre-cleanup). It is *not* being re-run as part of this plan. Comparator re-run only happens after:

1. This entire retrieval quality plan is complete (Phases 0-5)
2. The comparator code itself has been reviewed and updated to use the new metadata appropriately

Re-running comparator now would just produce another set of stale results once we change the retrieval stack underneath. Wait until the system is settled.

---

## Phase 1 — Build the retrieval benchmarks

**This is the prerequisite for everything else.** Without measured baselines, every architecture change is faith-based.

### What a benchmark looks like

A benchmark is a JSON file per source with ~15-25 questions. Each entry:

```json
{
  "question": "What proofs does someone need to verify identity for SNAP?",
  "expected_section": "VC-1 Verification Chart Identity row",
  "expected_chunk_id": "sec__VerifChart__topical_identity__000",
  "notes": "Identity is required for SNAP, EAEDC; optional for TAFDC"
}
```

Per source. CMR's 20-question set (`docs/cmr_cleanup/retrieval_benchmark.md`) is the model. The questions should:

- Mix easy (specific section number) and hard (semantic question requiring synthesis)
- Cover the corpus breadth — not just SNAP, not just one chapter
- Include known-tricky cases: acronyms, defined terms, cross-references
- Have a clear "right answer" chunk so retrieval can be scored mechanically

### Scoring

For each question:
- **Top-1 hit**: expected chunk in position 1
- **Top-3 hit**: expected chunk in top 3 results
- **Top-5 hit**: expected chunk in top 5
- **Miss**: not in top 5

Optionally: track "near miss" cases where the right *section* hits top-K but the wrong chunk-of-that-section came back first. With our `chunk_n`/`chunk_total` metadata, this is now distinguishable.

### Test rig must be clean

The benchmark tests **raw retrieval quality** — embedding + similarity ranking, nothing else. The harness must NOT include consumer-side enhancements that obscure what's being measured:

- **No auto-neighbor pulling** — return the chunks ChromaDB ranks, not chunks-plus-their-neighbors. (Auto-neighbor-pulling is its own planned feature; it goes through the consumer-calibration arc, not the retrieval-architecture arc.)
- **No silent program filters** — every program tag must be explicitly opted in via the test config. No "default to SNAP" surprises.
- **No synthesis call** — synthesis can mask retrieval problems by reasoning around them. Score the raw chunk ranking only.
- **No reranking unless explicitly testing rerank** — reranking is a measurable variant, not a baseline default.

Reason: if the test rig hides retrieval flaws by smoothing them over with downstream enhancements, we can't tell whether a change to the retrieval architecture actually moved the needle. The benchmark answers one question at a time: *given a query, which chunks does the vector store return, in what order?* Everything else is a separate experiment.

### Establishing the baseline

Run all four benchmarks against today's system (`voyage-3` dense-only, no rerank). Record numbers in `docs/retrieval_baselines.md`. These are the comparison point for every change that comes after.

---

## Phase 2 — Embedding model evaluation

Once benchmarks exist, swap the model and re-run.

### Models to test

| Model | What's interesting | Cost |
|---|---|---|
| `voyage-3` (current) | Baseline | — |
| `voyage-3-large` | Generally 2-5 points better on retrieval tasks. Same 1024 dim. | ~3-5x voyage-3 to embed |
| `voyage-context-3` | Embeds chunks WITH neighbor awareness. May make some of our context-prefix engineering redundant. **Most interesting for our use case.** | Similar to voyage-3 |

**Open question**: Voyage may have released newer models since the January 2026 training cutoff. Live research session needed to check the current model lineup before committing to a test plan.

### Why `voyage-context-3` is the wildcard

We spent significant cleanup energy building hierarchical context prefixes (`"FNS 310 > Chapter 10 > 1045.2 ..."`) so each chunk's embedding "knows" where it sits in the document. `voyage-context-3` does something similar automatically by letting the embedder see neighboring chunks during encoding. If it works well on our data, the prefix engineering becomes partially redundant — *and* the model might capture document structure better than we can by hand.

This isn't a pure substitution though — our prefixes also help **synthesis** (Claude reads them as citation context), not just embedding. So even if `voyage-context-3` makes the prefix unnecessary for embedding, we may still want a similar string for the LLM.

**Test variant: re-chunked without prefixes.** If `voyage-context-3` is the right tool, its job is exactly what our prefixes were trying to do manually — and a separately-planned auto-neighbor-pulling consumer enhancement was also going to address. We should test the model in both modes:

- **Mode A**: today's chunks (with prefix) embedded by `voyage-context-3` — measures whether the new model improves retrieval *on top of* our hand-crafted prefix.
- **Mode B**: re-chunked chunks WITHOUT the prefix line, embedded by `voyage-context-3` — measures whether the model can replace our prefix engineering entirely.

If Mode B matches or beats Mode A, that's a meaningful architectural simplification — embedder owns context, chunker stays minimal, and the prefix string can either be dropped entirely or kept just for synthesis display (smaller scope).

**Architectural intuition behind this**: neighboring chunks are critical for appreciating the context of any retrieved chunk. A standalone chunk reads with less information than a chunk-in-context. We had been planning to address this consumer-side via auto-neighbor-pulling at query time. `voyage-context-3` may be a cleaner solution — bake the context into the embedding once, no per-query expansion needed. Fewer moving parts, less per-query latency, and the search engine itself returns chunks that are already context-aware.

This is potentially a bigger architectural decision than the model swap itself.

### Other providers (sanity check only)

Worth one comparison run against a non-Voyage option (OpenAI `text-embedding-3-large`, Cohere `embed-v4`, or Google `gemini-embedding-001`) just to verify we're not stuck in a Voyage-specific local optimum. Anthropic recommends Voyage as their preferred partner, and Voyage tends to do well on legal/policy text, but data > vendor preference.

### Decision criteria

Pick the model that wins on the average of the four source benchmarks, not on any single source. If two models are within 1-2 points, prefer the cheaper / simpler one.

---

## Phase 3 — Hybrid search

Add BM25 alongside dense retrieval.

### Why this is high-value for our domain

Pure dense retrieval is weakest where our domain is densest: **specific tokens that ARE the meaning**. Examples staff actually type:

- `364.990` — section number, the string IS the answer
- `VC-1` — form name
- `EAEDC`, `TAFDC`, `AORD` — acronyms (Voyage saw these few or never)
- `Martinez test` — defined term
- `MIA-22-12` — transmittal ID

Dense embeddings only return these chunks if surrounding semantic context happens to match. BM25 finds them by exact token match. Hybrid combines both rankings.

### Implementation shape

For our corpus size (~12k chunks total across all sources and tiers), this is a few-hundred-line change, not infrastructure work:

1. Build a BM25 index alongside ChromaDB using `rank_bm25` (in-memory Python library). Index build is seconds, query is sub-millisecond.
2. Same chunk text fed to both indexes — keep them in sync at embed time.
3. At query time: run dense and BM25 in parallel, fuse the rankings via Reciprocal Rank Fusion (RRF):

   ```python
   final_score(doc) = 1/(k + rank_dense) + 1/(k + rank_bm25)   # k=60 is conventional
   ```

4. Implement once in `rag/query.py`. Every consumer benefits without code changes.

### Decision criteria

Re-run benchmarks. Hybrid should help measurably on the queries containing section numbers, acronyms, or defined terms. If it doesn't, something's wrong with the implementation. If it helps but not much, may not be worth the maintenance cost — but I'd be surprised if our domain didn't benefit.

### Caveats

- BM25 needs the same chunk text as dense — keep them synchronized when re-embedding.
- BM25 has tokenization choices (stemming, stopwords) that affect quality. Defaults are fine for v1; don't tune until benchmarks say to.
- Storage cost is small (an in-memory BM25 index for 12k chunks is megabytes).

---

## Phase 4 — Reranking

Add a Voyage `rerank-2` (or current equivalent) call between retrieval and synthesis.

### How it fits

```
query → [hybrid retrieval: dense + BM25 → RRF top-20] → [rerank to top-5] → synthesis
```

Reranking is **per-query cost**. Every search runs:
1. Hybrid retrieval gets top-20 (no extra cost)
2. Reranker scores all 20 against the query — **this is the new cost**
3. Take new top-K (5), feed to synthesis as today

### Cost & latency

- Cost: pennies per thousand queries. Small relative to the synthesis call already in the flow.
- Latency: +200-500ms per query.
- Cost mental model: same as "should the search make an LLM call at all" — yes, because quality justifies it. Reranking is a smaller, more focused LLM-ish call inside that flow.

### When reranking isn't worth it

For programmatic / agentic use that fires dozens of searches per task — the comparator runs ~5 searches × 270 sections, for example. For agents, want a clean opt-out: `search(rerank=False)` for cheap exploration, `rerank=True` for the final answer. Not a hard tradeoff, just an API consideration.

### Decision criteria

Re-run benchmarks. Reranking should help measurably on semantically ambiguous queries — questions that have multiple plausible chunks where understanding *which* one answers requires reading both query and chunk together.

### Open question: rerank API choice

Voyage `rerank-2.5` is one option. Cohere has rerank too. May want to benchmark briefly. Live research needed for current state of reranker offerings.

---

## Phase 5 — Decide what to keep

After all the data is in, decide:

| Lever | Keep if... | Drop if... |
|---|---|---|
| New embedding model | Wins benchmark by ≥ 2 points and re-embed cost is a one-time hit | Marginal gain |
| Hybrid search | Helps measurably on token-heavy queries | No measurable lift (would be surprising) |
| Reranking | Helps measurably on semantic queries AND query-time cost is acceptable | Cost outweighs lift, or you mostly query for exact tokens (already covered by hybrid) |

You may find one lever gives 90% of the lift and the others are marginal. The benchmarks tell you, not vibes. **The whole point of Phase 1 is to make this decision data-driven.**

---

## What comes after this plan

This plan ends at "we have a measured, calibrated retrieval system." The next arc is **calibrating the consumers** — making sure each tool/agent that uses the RAG actually exploits the new metadata and retrieval quality:

- `tools/synthesis.py` — does Claude actually see and use `parent_heading`, `chunk_n`/`chunk_total`, `hierarchy_path` in the citation block?
- Author research — does it pull adjacent chunks when relevant? Does it know to look up definitions?
- Comparator — does L1/L3 read the new metadata when classifying findings?
- QC analyzer — same question
- UI — does the result display make the new metadata navigable for human users?

That work has its own plan, captured separately when this one's done.

---

## Sequencing (revised 2026-05-04, end-of-day)

```
Phase 0 (cleanup)                              ← still pending
  └→ un-gitignore parsed_sections, clear stale caches

Phase 1 (CMR benchmark + harness)              ← COMPLETE
  └→ judge-based methodology, CMR baseline at 57% Rel@1

Phase 2 (CMR embedding model evaluation)       ← COMPLETE
  └→ voyage-4-large: marginal lift (+2pp Rel@1)
  └→ voyage-context-3 mode A (with prefix): +8pp Rel@1, +18% Rel@5 — WINNER
  └→ voyage-context-3 mode B (no prefix): regressed; prefix pulls weight

Phase 2.5 (validate on OLG, deploy stack-wide)  ← COMPLETE
  └→ benchmarks/olg.json authored (24 questions, mixed difficulty)
  └→ OLG voyage-3 baseline: 42% Rel@1, 4.83 Useful@5
  └→ OLG vctx3 mode A: 62% Rel@1 (+20pp), 4.96 Useful@5 — bigger lift than CMR
  └→ Production swap (rename CMR + OLG variants → production names; fresh embed FNS + CFR)
  └→ config.ini model = voyage-context-3
  └→ Eval collections + artifact JSON dropped
  └→ Smoke-tested on all 4 sources

Phase 3 (hybrid search)                        ← NEXT (design discussion first)
  └→ user wants extended discussion on practical implementation before code
  └→ targets the 9/24 OLG questions still at rel@5=0 (acronyms, section numbers, terse adversarial)

Phase 4 (reranking)                            ← deferred to last; per-query cost

Phase 5 (decide & commit)
  └→ already partially done (architecture committed, CLAUDE.md updated, experimentation cruft killed)
```

**Open architectural decisions made at end of Phase 2**:
- Section tier: voyage-context-3 (mode A — keep context prefix in chunker)
- Broad tier (chapters/pages/parts): voyage-4-large (32K context handles them; their vectors are barely used anyway, just for ID-lookup of parent context)
- Don't drop prefix engineering; it's complementary to neighbor-aware embedding, not redundant

Each phase ends with re-runnable benchmarks, so progress is measurable end-to-end. The CMR-first gating before scaling to other sources is new — the original plan assumed all four benchmarks would be authored upfront.

---

## Open research questions

Things to check via WebFetch / WebSearch in the actual research sessions, since training cutoff is January 2026 and current state may have moved:

1. What's Voyage's current model lineup? (`voyage-3-large`, `voyage-context-3`, anything newer?)
2. What's the current state of Voyage's reranker offerings and pricing?
3. Has Cohere released anything new in this space worth comparing?
4. Any new fusion techniques beyond RRF worth considering for hybrid (e.g., learned fusion)?
5. Has ChromaDB added native hybrid search since we last looked? (would simplify implementation)
