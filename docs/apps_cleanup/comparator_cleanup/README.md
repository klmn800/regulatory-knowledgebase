# Comparator — Cleanup Notes

Working document. Updated across sessions. See `../README.md` for the cleanup charter and audit methodology.

**Audit status**: Steps 1 (module read-through), 2 (layer mapping), 3 (UI/report surface), 4 (JS surface, subsumed into 3 since the only JS lives inline in `report.py`), 5 (config audit), and **deep architectural findings (F24-F33)** all complete. **Cross-app comparison pass still pending** — see "To do for next session" at the bottom.

## Purpose

The comparator analyzes each FNS Handbook 310 section against the DTA Online Guide (OLG) to identify gaps, differences, and missing procedures. Four layers:

- **L0 Pre-classify** (Haiku, batched once and persisted): filter out non-policy FNS sections (overviews, glossaries, QC procedures) so they're never investigated
- **L1 Triage** (Haiku, per section): pre-fetch OLG matches → quick classification (`match` / `partial_match` / `not_applicable` / etc.)
- **L2 Deep investigation** (per section that escalated): iterative OLG search + FNS cross-reference lookup. **Has two engines**: Anthropic API tool-use loop OR Claude Code CLI subprocess — selected by `--engine api|claude-code`. **Model under API engine = `layer2_model` from config (currently Haiku); model under Claude Code engine = whatever the user's CLI session is set to.**
- **L3 Cross-check** (per confirmed gap): asks "does CMR address this?" and "does CFR address this?" — two separate single-turn calls. **Model = `layer3_model` from config (currently Haiku).**

Output: per-section result JSON at `output/comparator/results/{section_number}.json` (shared cache between engines), compiled into CSV per FNS chapter via `--compile`, then rendered to a single HTML report via `programs/comparator/report.py`.

## File shape

Two files, 2,961 lines total:

- `programs/comparator/comparator.py` — 1,757 lines (the orchestrator)
- `programs/comparator/report.py` — 1,204 lines (HTML report generator, separate concern)

### `comparator.py` banner-separated sections

| Lines | Section |
|---|---|
| 80-155 | CONFIGURATION (paths, `PRICING`, `TokenTracker`, `load_config`, `load_prompt`) |
| 156-170 | FNS SECTION LOADING |
| 171-431 | LAYER 0: PRE-CLASSIFICATION (`run_layer0`, `classify_sections`, CSV/JSON persistence, `sync_csv_to_json`) |
| 432-510 | RAG RETRIEVAL (`multi_query_olg`, `query_cmr`, `query_cfr`) |
| 511-608 | RESULT FORMATTING FOR PROMPTS (`format_fns_for_prompt`, `format_olg_results_for_prompt`, `format_cmr_results_for_prompt`, `format_cfr_results_for_prompt`) |
| 609-637 | LAYER 1: BULK TRIAGE (`run_layer1`) |
| 638-799 | LAYER 2: DEEP INVESTIGATION (`run_layer2` API agentic loop, `lookup_fns_section`, tool definitions) |
| 800-891 | LAYER 2 (CLAUDE CODE): CLI-BASED INVESTIGATION (`run_layer2_claude_code`) |
| 892-963 | LAYER 2: UNIFIED DISPATCH (`investigate_section` with shared cache + engine switch) |
| 964-1029 | LAYER 3: CMR CROSS-CHECK (`run_layer3`, `run_layer3_cfr` — banner says CMR but CFR lives here too) |
| 1030-1053 | CHECKPOINT / RESUME |
| 1054-1166 | CSV OUTPUT (`build_csv_row`, `write_csv`) |
| 1167-1282 | COMPILE RESULTS FROM RESULT JSONs (`compile_results`) |
| 1283-1639 | MAIN ORCHESTRATOR (`run_comparison`) |
| 1640-1757 | CLI (`main`, argparse) |

### `report.py`

HTML report generator. Loads compiled CSVs, builds a single static HTML page with filtering, favorites, expandable details, dark mode. Independent of comparator.py — runs after `--compile`. Equivalent of QC's UI surface, but offline/static (no FastAPI route, no HTMX, no live state).

## Layer mapping

This is the data point that bears on the **A1/A2/B loop-consolidation question**. For each pipeline function, which layer does it touch?

| Function | RAG direct | Synthesis | Claude Code | Anthropic SDK direct |
|---|:---:|:---:|:---:|:---:|
| `run_layer0` (L0 classify) | — | — | — | ✓ Haiku, single-turn |
| `multi_query_olg` (helper) | ✓ `search_with_client` | — | — | — |
| `query_cmr` / `query_cfr` (helpers) | ✓ `search_with_client` | — | — | — |
| `run_layer1` (L1 triage) | — | — | — | ✓ Haiku, single-turn (consumes pre-fetched OLG) |
| **`run_layer2` (L2 API)** | indirectly via tools | — | — | ✓ **Model = `layer2_model` from config (currently Haiku per `config.ini`); tool-use loop** |
| **`run_layer2_claude_code` (L2 CLI)** | indirectly (Claude Code session calls `rag/query.py` itself) | — | ✓ **`run_claude_task`** | — |
| `investigate_section` (dispatch) | — | — | — | — (just routes) |
| `run_layer3` (L3 CMR) | ✓ `search_with_client` | — | — | ✓ Model = `layer3_model` from config (currently Haiku); single-turn |
| `run_layer3_cfr` (L3 CFR) | ✓ `search_with_client` | — | — | ✓ Model = `layer3_model` from config (currently Haiku); single-turn |

**No use of `tools/synthesis.py`.** Comparator never calls into synthesis. Every Anthropic call is hand-rolled.

> **Correction from prior session**: an earlier version of this table said L2/L3 used Sonnet because the module docstring says so (L1-28). Verified during step 5: the docstring is stale; the actual model under API engine is whatever `layer{2,3}_model` resolves to in config, which is currently Haiku for both layers. The Claude Code engine for L2 uses the user's CLI-session model (typically Sonnet or Opus). See **F1**.

### What this means for A1/A2/B

- **`run_layer2` (API mode) is the A2 test case.** It's an agentic tool-use loop, structurally the same family as QC's `run_judge` and synthesis deep-mode. **But it has two tools** (`search_olg` + `lookup_fns_section`), where QC and synthesis have one. A shared `agentic_search_loop` primitive would need to support multi-tool calling to absorb L2.
- **`run_layer2_claude_code` is the engine-routing test case.** Same conceptual operation as `run_layer2`, but routed to Claude Code. The dispatch in `investigate_section` (L896-961) is where the "give me the same operation via either engine" abstraction lives. If we extract a shared primitive, this dispatch shape is what would be parameterized.
- **L1, L3 CMR, L3 CFR are siblings of QC's cross-checks.** Single-turn Haiku/Sonnet with pre-fetched results. Same pattern, three near-identical implementations across files (and likely structurally similar to QC's three near-identical cross-checks).

## Architectural findings

### F1 [outdated, RESOLVED 2026-05-06] Module docstring describes only the Claude Code engine

`comparator.py:L1-28` describes:
- L2 as "Sonnet: Deep investigation"
- L3 as "Sonnet: CMR cross-check"
- Architecture as "four layers: L0/L1/L2/L3" (correct count, but L3 is single-flavor in the docstring)

Reality:
- **L2/L3 API engine runs Haiku** because `config.ini:[comparator]` has `layer2_model = layer3_model = claude-haiku-4-5-20251001` (verified at L1465 → API call site, L1549/L1564 → L3 call sites)
- **L2 Claude Code engine runs whatever the user's CLI is set to** (model not controlled by `layer2_model`) — typically Sonnet or Opus, matching the docstring's "Sonnet" claim incidentally
- L3 has **two flavors** — CMR (`run_layer3`) and CFR (`run_layer3_cfr`)

**User clarification 2026-05-06**: comparator was intended to run on Sonnet, and in practice it does — because the dominant path is Claude Code, which inherits whatever model the user's CLI session is using. The API engine running Haiku is acceptable because the API path is currently only exercised for simple work, not high-stakes agentic L2 runs.

**Resolution**: not a bug. Cleanup action is **documentation only** — expand the module docstring to describe both engines and what governs each engine's model. The current docstring assumes a reader knows the comparator runs through Claude Code by default; new readers won't.

Connects to the broader architecture principle (`memory/architecture_principles.md`): every app must keep an API-only path viable, but Claude Code is the default for agentic work for this user. F22 (four layer-model keys all = Haiku) is acceptable under this principle — the API path is for simple work and the model choice doesn't carry quality risk.

### F2 [outdated] `report.py` module docstring shows a pre-restructure usage path

`report.py:L4-7` shows:
```
python agents/report.py
python agents/report.py -o report.html
python agents/report.py --open
```

Actual path is `programs/comparator/report.py`. The `agents/` prefix predates the directory restructure (memory says 2026-04-06). Trivial fix — same outdated-docstring shape as F1, lower stakes.

### F3 [duplication, cross-app] `extract_json()` near-duplicate of QC's

`comparator.py:L47-77` defines `extract_json()`. `qc_analyzer.py:L250-278` defines its own. Same fallback strategies (raw → strip code fences → regex extract → fallback dict), but **fallback dict shape differs**:

- Comparator: `{classification, confidence, note}` with `note = text[:300]`
- QC: `{coverage, confidence, reasoning}` with parameter for `fallback_classification` (which QC already flagged in F5 as wrong-shaped for cross-checks)

Two near-identical helpers with subtly different output shapes. Candidate for a shared `tools/llm_helpers.py` if a parameterized version exists; otherwise the two callers should keep their own and the cross-app similarity is just a parallel evolution.

### F4 [duplication, cross-app] `TokenTracker` / `PRICING` near-duplicate of QC's `CostTracker` / `MODEL_PRICING`

- `comparator.py:L94-135` defines `PRICING` + `TokenTracker`
- `qc_analyzer.py:L85-146` defines `MODEL_PRICING` + `CostTracker`

Same shape: hardcoded per-model rates dict + a class that accumulates input/output tokens and computes cost. **Different rates** for the same Haiku model ID — see B1 (this is the bug that OBS-C surfaced). **Different class shapes**: comparator's `TokenTracker` has `total/section` accounting; QC's `CostTracker` has `extractor/judge` accounting. The split-by-stage design in QC means it can't directly substitute for comparator's session/total split.

A shared `tools/cost_tracker.py` could absorb both if parameterized with stage names. This is the second cross-app duplicate (with F3 above) that points at a missing `tools/` utility module.

### F5 [intentional / interesting] Shared-cache pattern between L2 engines

`investigate_section` (L896-961) checks the result file at `RESULTS_DIR/{sec_num}.json` *before* dispatching, regardless of engine. Both `run_layer2` (API) and `run_layer2_claude_code` write to the same file. So a partial run under one engine resumes/continues under the other.

This is a real architectural feature, not drift. Worth documenting somewhere visible (currently only inferable from the dispatch code). **Categorize as "intentional deviation" rather than finding** — the pattern is good; it just isn't documented.

### F6 [interesting / under-design] `run_layer2_claude_code` communicates via filesystem

`run_layer2_claude_code` (L800-891) builds the prompt by concatenating `domain_preamble.md` + `layer2_claude_code` prompt + structured context + a "write your result to {result_file}" instruction. The Claude Code session is given the result-file path and told to write JSON there. After the subprocess returns, comparator reads the file.

Compared to the API engine, where the result is the response body, this is a different IPC pattern. **Works but is fragile**: if the Claude Code session crashes mid-run, the file may be partial/missing/corrupt; if it ends without writing, dispatch returns a default. Worth confirming the failure-mode handling during the deep-findings pass.

### F7 [under-design] `--sync` round-trip is undocumented human-in-the-loop

`--sync` (L1654, `sync_csv_to_json` at L431-ish) regenerates the L0 classifications JSON from the edited CSV. Implies humans edit `output/comparator/layer0_classifications.csv` manually and the system round-trips. **Who edits it, when, and why** is unclear from the code alone; this is a feature whose use is in the user's head, not the docs.

### F8 [feature, not finding] `--parallel N` worker pool for L2

L1473-1518 uses `ThreadPoolExecutor` with `--parallel N` workers for L2 investigations, with shared-cache lookup acting as the dedup mechanism (L2 dispatch checks file before running). Real feature. Implementation looks tight — interim CSV is rewritten after each completion (L1510-1518). Worth understanding the rate-limit interaction during deep-findings pass; otherwise a feature, not a finding.

### F9 [duplication] `run_layer3` and `run_layer3_cfr` are near-duplicate

Same shape as QC's F2 (three near-identical cross-check functions). `run_layer3` (CMR, L968-996) and `run_layer3_cfr` (CFR, L997-1029) take the same args (fns_section, layer2, source_results, claude, model, prompt, fns_by_number, tracker), do the same Haiku single-turn classification, and persist into different keys. Differs by source name and result schema (CFR adds `cfr_sections` field).

This + QC's F2 (three) = **five copy-paste cross-check functions across two apps**. Strong cross-app pattern; candidate for a shared `run_source_check(source, ...)` primitive (proposed in QC notes).

---

*Findings F24-F33 added 2026-05-06 after the deep architectural read of L0/L1/L2/L3/orchestrator code. Focus areas per the prior session's plan: retry/rate-limit policy, F6 failure-mode handling, magic numbers, tool definitions, result-shape inconsistencies, print-vs-log.*

### F24 [drift, MAJOR] Zero retry on RateLimitError at any API call site

Every `client.messages.create()` in comparator is unprotected:

| Layer | Site | Retry behavior |
|---|---|---|
| L0 | `run_layer0` (L259-264) | None — exception propagates |
| L1 | `run_layer1` (L625-630) | None — exception propagates |
| L2 API | `run_layer2` agentic loop (L731-737), called up to 15 times per section | None — exception in any turn kills the section |
| L3 CMR | `run_layer3` (L984-989) | None |
| L3 CFR | `run_layer3_cfr` (L1017-1022) | None |

Cross-app comparison (logged as **CA-8** in `../cross_app_findings.md`):

- **Synthesis** (`tools/synthesis.py:L412-448`): explicit retry on `RateLimitError`, `time.sleep(60)`, one retry, falls back to error result on second failure.
- **QC** (qc_analyzer.py F7): mixed — extractor 3 attempts with backoff, judge 1 retry, cross-checks none.
- **Comparator**: zero anywhere.

For an overnight run with parallel L2 workers (used at `--parallel 5`), comparator is the most-fragile of the three apps. A single transient `RateLimitError` in the L2 API loop crashes the section's worker thread; the orchestrator's `future.result()` (L1482) re-raises into the main thread with no try/except, killing the whole run. **The interim CSV (written per-L2-completion at L1517-1518) limits data loss, but the run still has to be restarted.**

The Claude Code engine is unaffected — `run_claude_task` has its own timeout and graceful failure-to-error-dict in `run_layer2_claude_code` (L881-889). So the engine choice has a real reliability dimension that the docstring doesn't mention.

**This is the most-impactful finding of the deep pass.** Latent severity is high; observable severity depends on overnight rate-limit headroom.

### F25 [design-flaw, suspect] Degenerate L2 outcomes get cached as real findings

Two paths in `run_layer2` produce a result that is then cached to `RESULTS_DIR/{sec_num}.json` (via `investigate_section` L955-958) and treated as authoritative on any future run:

1. **Max-turns exhaustion** (L791-797): returns `{"classification": "confirmed_gap", "confidence": "LOW", "note": "Layer 2 exhausted maximum tool-use turns without conclusion.", ...}`. This is a synthetic "gap" — Claude didn't actually conclude that. Caching means subsequent runs adopt that classification permanently unless the user manually deletes the result file.
2. **`extract_json` fallback** (L789): if Claude's final response can't be parsed as JSON, `extract_json(text, fallback_classification="confirmed_gap")` returns a synthetic `confirmed_gap` with `note=text[:300]`. Same cache treatment — a malformed-JSON output becomes a cached "confirmed gap."

**Why it's suspect**: L0/L1/L3 also have `extract_json` fallbacks but those layers don't write to a shared cache; they re-run from scratch every comparison. L2 is the only layer with the cache, and the cache doesn't distinguish between "Claude reached a confident conclusion" and "Claude failed to terminate cleanly."

**Possible designs**: (a) skip caching when classification originated from a fallback path, (b) use a sentinel confidence level that triggers re-investigation, (c) accept the current behavior as deliberate (cheap re-runs are not free, and the user can delete result files manually). Pick one.

### F26 [drift] `similarity_threshold` has three different default values

- `multi_query_olg` function default (L437): `0.20`
- `run_comparison` config fallback (L1303-1304): `0.20`
- `config.ini:[comparator]` value (L39): `0.30`

In production, the config value (`0.30`) is used because the orchestrator reads it. But if the config is missing or the key is removed, both fallback paths quietly drop to `0.20`. Latent regression risk: a missing-config event silently changes retrieval quality without any error.

Either align all three to one number, or remove the function default (function callers must supply explicitly).

### F27 [magic numbers] Multiple unexplained constants

| Constant | Location | Value | Notes |
|---|---|---|---|
| L0 max_tokens | L261 | 200 | Unstated; presumably enough for `{label, reason}` JSON |
| L0 section text truncation | L234, L254 | 3000 chars | Unstated |
| L0 parent context truncation | L221 | 1500 chars | Unstated |
| L1 max_tokens | L627 | 500 | Unstated |
| L2 max_turns | L729 | 15 | **Same value as synthesis L350** — coincidence or deliberate alignment? |
| L2 max_tokens | L733 | 1500 | Unstated |
| L2 result-text truncation | format_*_for_prompt | 1000 chars | Matches synthesis (L134) |
| L2 Claude Code timeout | `run_claude_task` call L863 | 1800 (30 min) | Unstated; deliberately large for deep agentic runs |
| L3 max_tokens | L986, L1019 | 800 | Unstated |
| FNS section text in prompts | L528, L711 | 3000 chars | Unstated |
| `multi_query_olg` query truncation | L453 | 200 chars | Unstated |
| `multi_query_olg` substantive-sentence threshold | L451 | 40 chars | "Substantive" defined as >40 chars; arbitrary |

Eleven+ unexplained constants in a 1,757-line module. Easy cleanup: convert to module-level named constants, one rationale-comment each (e.g., `L2_MAX_TURNS = 15  # search budget + buffer for terminal reasoning`).

### F28 [drift, cross-app] L2 budget is turn-based; synthesis and QC are search-based

- **Comparator L2** (L729): `max_turns = 15`. Each turn is one model call regardless of whether Claude searches or just reasons. Hits the limit at 15 model calls.
- **Synthesis run_deep** (L348-350): `max_searches = 8` (config), `max_turns = 15` (hardcoded). Search budget is enforced *separately* from turn budget — Claude can use up to 8 searches and the loop runs at most 15 turns.
- **QC judge** (qc_analyzer.py:L648 per QC F11): `max_turns = max_searches + 5`. Search budget plus a five-turn buffer.

Three different budget designs across three apps that share the same control structure. **Comparator's design is the most permissive** — Claude can use all 15 turns on searches (the most expensive operation) since there's no separate search cap. **Suspect**: was this deliberate (give L2 maximum search latitude) or an oversight (forgot to add a search cap)?

Logged as **CA-10** in `../cross_app_findings.md`.

### F29 [duplication, cross-app] `SEARCH_OLG_TOOL` exists in both apps with diverged descriptions

- Comparator (L672-690): `"...try synonyms, broader/narrower terms, specific policy language, or BEACON system references."`
- QC (per QC F12, L596-614): mentions "BEACON procedures."

Same conceptual tool, both reference BEACON specifically (Massachusetts case-management system), descriptions evolved separately. Synthesis's `SEARCH_POLICY_TOOL` (synthesis.py:L82-109) is the more general version with a multi-source enum.

Logged as **CA-9** in `../cross_app_findings.md`.

### F30 [drift, retrieval-quality] `format_olg_results_for_prompt` is simpler than synthesis's

Comparator's OLG formatter (L534-558) shows: page_title, section_heading, score, text. That's it.

Synthesis's OLG formatter (synthesis.py:L136-156) shows: page_title, section_heading, **parent_heading, breadcrumb, URL, chunk_n/chunk_total** (multi-part chunk indicator).

Comparator L2 prompts get strictly less context per OLG result. **Could affect L2 retrieval reasoning quality**: parent_heading and breadcrumb help disambiguate sections; chunk_n/total helps Claude understand whether a result is a fragment or a complete answer. The comparator's L2 work is the highest-stakes use of OLG results in the codebase, so it's surprising the formatter is the leanest.

If consolidation lands `format_results_for_prompt` in `tools/` (CA-3 in cross-app), comparator should converge to the richer synthesis version.

### F31 [drift] No shared result schema across L0/L1/L2/L3

Each layer returns a different dict shape:

- L0: `{label, reason}` (after rename from `{classification, note}`)
- L1: `{classification, confidence, note}` (extract_json default)
- L2: `{classification, confidence, note, olg_pages_found, searches_performed, _session_id, _cached, _elapsed, _error}` — varies by engine + cache state
- L3 CMR: `{classification, confidence, note, action_recommended, priority, ...}` — fields read at L1552-1555
- L3 CFR: `{classification, confidence, note, cfr_sections, ...}` — `cfr_sections` read at L1568

Plus the fallback shapes from `extract_json` are skinnier than success shapes (no `action_recommended`, no `cfr_sections`, etc.). Downstream code uses `.get(default)` to navigate this — works, but means a malformed-JSON event causes silent loss of fields that `report.py` then renders as blank.

A typed-dict (or dataclass) per layer would catch the schema drift between prompt expectations and code expectations.

### F32 [inconsistency] Hardcoded "$0" for Claude Code cost reporting

`run_comparison` final summary (L1627-1628):

```python
if engine == "claude-code":
    print(f"  L2 cost: $0 (Claude Code subscription)")
```

The Claude Code subscription is not free — it's a flat fee already paid. Showing "$0" is technically misleading; "incremental cost: $0" or "(billed via Claude Code subscription)" would be more accurate. Cosmetic, but the cost-reporting intersects with the cross-app cost-tracker discussion (CA-1) — when a `tools/cost_tracker.py` lands, it should know how to surface "subscription-billed" runs.

### F33 [intentional, document] L3 phase is sequential while L2 phase is parallel

`run_comparison` runs L2 in `ThreadPoolExecutor` (L1477) but iterates L3 sequentially (L1526). Comment at L1520 acknowledges the choice ("(sequential)").

**Defensible**: L3 is per-confirmed-gap (much smaller volume than L2's per-section), Haiku single-turn (fast), and runs after L2 completes — so parallelism would yield smaller wins. **Worth documenting** as an intentional deviation rather than letting it look accidental, since the asymmetry is the kind of thing a future maintainer would "fix" without understanding why it was a choice.

---

### Notes on items that did NOT need new findings

- **F6 follow-up (Claude Code dies mid-L2)**: verified `investigate_section` L928-935 handles corrupt JSON cache (catches `JSONDecodeError`/`OSError`, falls through to fresh run); `run_claude_task` returns `{success: False, error: ...}` on subprocess failure, which `run_layer2_claude_code` converts to an error-fallback dict that is **not written to the cache** (only successful task_results write at L876-878). So F6 was a real concern but the existing handling is adequate. Worst residual case: Claude Code writes a syntactically valid but logically incomplete JSON, which would cache. Acceptable risk given the prompt is explicit about output shape.
- **Print-vs-log**: the entire orchestrator + every layer uses `print()` for progress. Same shape as QC F14 (already noted). No new finding — same shape, same eventual fix (logger).
- **Duplicated config reads**: F20 (`fns_chapters_to_compare` read 3 times) and F21 (`anthropic_api_key` read 2 times) already covered.

## UI / report findings

`programs/comparator/report.py` is the comparator's user-facing artifact. No FastAPI route, no HTMX — it generates a single static HTML file with inline CSS/JS, written to disk and opened in the browser. Heavy CSS (~315 lines), heavy JS (~322 lines), heavy HTML (~378-line `generate_html`). Features:

- Light/dark mode toggle (localStorage)
- Filters: All / Findings / Needs Attention / Favorites / Has Notes / by Chapter / by Classification
- Per-row star + per-row free-text notes (both localStorage)
- Expandable detail panel with FNS requirement, L1/L2/L3 notes, CMR cross-check, CFR cross-check, OLG links, action/priority badge, session ID with copy-to-clipboard, tokens/cost
- CSV export of currently-filtered rows including notes

### F10 [rollout follow-up, not drift] Methodology footer omits CFR cross-check

`report.py:L1097-1098` describes L3 as "**Layer 3**: CMR cross-check for actionable findings to determine whether gaps are state-level policy decisions." But the report itself renders a CFR cross-check block (L989-999) right above the methodology footer. The rendering was added when CFR L3 was added (per memory: CFR pipeline integrated 2026-04-30), but the methodology paragraph wasn't updated.

**User confirmation 2026-05-06**: known follow-up — CFR was recently added to the RAG and UI integration is still in progress; this footer is part of the not-yet-done CFR rollout, not architectural drift. Cleanup action is **trivial copy update**, not a structural finding.

### F11 [rollout follow-up, not drift] Methodology footer says L2 uses Claude Code only

`report.py:L1095-1096` describes L2 as "**Layer 2**: Agentic investigation using Claude Code CLI sessions." Reality (per F1 and the layer mapping): L2 has two engines.

**User context 2026-05-06**: this is consistent with the design — Claude Code is the dominant path for agentic L2; the API engine exists to keep the system deployable without a Claude Code dependency, but isn't the path users see in the report. The footer copy reflects the dominant path; expanding it to mention the API engine is **trivial copy update**, also low-stakes.

### F12 [under-design] Hardcoded `FINDING_CLASSIFICATIONS` set

`report.py:L715-716` hardcodes the set of "L3-escalated" classifications:
```python
FINDING_CLASSIFICATIONS = {"confirmed_gap", "different_standard",
                           "policy_present_procedures_missing"}
```

This set is duplicated as control-flow logic at `comparator.py:L1532-1535` (the `needs_layer3` check). If the classification taxonomy is extended, both places must be edited. **Same shape twice across the two files** — a shared module/constants source would prevent drift.

### F13 [suspect] localStorage notes keyed by `fns_chapter_section`

`report.py:L730-732` defines `row_key` as `"{fns_chapter}_{fns_section}"`. Notes are persisted in browser localStorage under this key. **Stable enough today** (FNS section numbering is from a published PDF; section IDs don't drift). But: if FNS Handbook 310 is republished and re-parsed and the section numbers shift, every user's notes will silently become orphaned. Worth flagging because the note feature is the most user-investment-heavy element of the report.

### F14 [duplication] CSV export columns hardcoded twice in JS

`report.py:L636-639` (header row) and `L645-649` (field assembly) both list the column names and order. Adding a column requires editing both. Two-point edit hazard, classic copy-paste form.

### F15 [drift / asymmetry] CMR vs CFR detail blocks have different shapes

CMR detail block (L983-987) shows just `l3` (free-text note). CFR detail block (L989-999) shows `cfr_classification` (badge) + optional `cfr_section` + `cfr_note`. The asymmetry reflects that CMR L3 was first and CFR was added later with a richer schema, but it's now baked into the report and the column set. Either CMR should grow the same shape (classification + section + note) or CFR should collapse to a single text field. **Currently neither — they're permanently asymmetric.**

### F16 [cosmetic] `generate_html` is a single ~378-line function

`report.py:L773-1150`. Header / summary / filters / table / per-row main / per-row detail / footer all in one function with `h.append()` accumulator. Decomposable into seven smaller functions; pure cosmetic for now, but any future edit on this function reads scary.

### F17 [drift] `load_csvs` fallback pattern is engine-asymmetric

`report.py:L697-712` prefers `comparison_compiled_*.csv` (output of `--compile`). If no compiled CSV exists, it falls back to `comparison_claude-code_*_FNS-*.csv`. The fallback name is engine-specific — a per-chapter run with `--engine api` would produce `comparison_api_*_FNS-*.csv` (or similar), which the fallback would not match. **Currently latent**: the dominant path is `--compile`, which produces a single `comparison_compiled_*.csv`, so the fallback is rarely exercised. But it represents a hidden dependency on the Claude Code engine name.

## Config findings

`config.ini:[comparator]` (L35-46) has 11 keys. Compared against every `config.get*` call in `comparator.py` (verified via grep):

### F18 [bug-shaped] `queries_per_section = 3` is orphaned

`config.ini:L45` declares `queries_per_section = 3`. **Zero references anywhere in `programs/comparator/`** (grep result empty). Dead config key. Either the feature it served was removed (and the key wasn't), or the key was added in anticipation of a feature that never landed. Either way, every reader will assume it does something.

### F19 [suspect] `layer{0,1,2,3}_model` reads have **no fallback**

`comparator.py:L279, L1300, L1301, L1302` call `config.get("comparator", "layer{N}_model")` with no `fallback=` argument. If the key is removed from config, `KeyError` at runtime. Compare to QC's `cfr_check_model` (qc_analyzer.py:L1325-1326) which uses `fallback="claude-haiku-4-5-20251001"` — that's the pattern that hid B2 in QC notes from anyone reading the config alone. Comparator chose the loud-failure pattern, which is **defensible**, but the fact that it's inconsistent with QC's choice (and with comparator's own use of `fallback=` for `olg_max_results`, `cmr_max_results`, etc. at L1305-1308) is the actual finding. Pick one fallback policy.

### F20 [duplication] `fns_chapters_to_compare` is read three separate times

`comparator.py:L1190, L1717, L1732`. All three reads use the same fallback string `"7,8,9,10,11"` (the literal). Read once, store on a variable, reuse. **Three magic-string fallbacks** is also three places to update if the default changes.

### F21 [duplication] `anthropic_api_key` is read twice

`comparator.py:L313, L1376`. Trivial; should be loaded once and threaded through.

### F22 [premature flexibility] All four layer-model keys point to the same model

`config.ini:L36-38, L46`:
```
layer1_model = claude-haiku-4-5-20251001
layer2_model = claude-haiku-4-5-20251001
layer3_model = claude-haiku-4-5-20251001
layer0_model = claude-haiku-4-5-20251001
```

Four keys, one model. Same shape as QC's F31 (three keys, all Haiku). A single `default_model` key, or two (`triage_model` + `judge_model`) at most, would have served. Symptom of building each layer one at a time without stopping to factor.

**Acceptable under current usage** (per F1 resolution and architecture principles): the API engine isn't the dominant path for agentic L2, so the per-layer Haiku assignment doesn't introduce quality risk today. Worth consolidating during the apps-cleanup arc but not urgent.

### F23 [cosmetic] `layer0_model` is appended at the end of the section

`config.ini:L46`. The other three layers are at L36-38 in order. `layer0_model` is bolted on at the end after the threshold/result-count keys. Pure ordering; suggests L0 was added later and the maintainer didn't reorder.

## Opportunities

*(Empty — populate after deep-findings session. Already on the radar from initial dip:)*

- Cross-app shared utilities: `extract_json`, `TokenTracker`/`PRICING`, `format_*_for_prompt`, prompt-loader, banner-section convention. These are bigger than comparator alone — likely live in `tools/` or a new `tools/llm_helpers.py`.
- L2 API agentic loop: candidate for `agentic_search_loop` primitive (A2 from the QC discussion). Multi-tool support required.
- L2 engine dispatch: pattern for "same operation, two engines, shared cache." Could become a small abstraction if it shows up elsewhere — if not, leaving it in comparator is fine (intentional deviation).
- L3 CMR/CFR near-duplication (F9) + QC's three cross-checks (QC F2): convergence on a shared `run_source_check(source, ...)`.
- Resolve F1: confirm the intended L2/L3 model assignment (Haiku, as config currently states, or Sonnet, as docstring states) and update whichever is wrong.

## Open questions

- F1 root cause: was the L2/L3 model intentionally downgraded to Haiku, or is the docstring just stale? Cost vs. quality tradeoff this hides matters for the cleanup direction.
- F18 root cause: what was `queries_per_section` originally for? `multi_query_olg` (L432-ish) might have used it before being refactored.
- Is the `--sync` round-trip (CSV → JSON) actually used? When? Who edits the CSV manually?
- How does `--parallel N` coordinate with rate limits? (Worker count is unbounded relative to Anthropic concurrency limits.)
- Is `report.py` the *only* consumer of the compiled CSVs, or do humans/tools also read them directly?
- Does any code outside `comparator/` depend on the result JSONs at `output/comparator/results/`? If so, the file format is a contract.

## Decisions log

- **2026-05-06**: F1 resolved as documentation-only finding. Comparator was intended to run on Sonnet for agentic L2 and does so via Claude Code (the dominant path). The API engine running Haiku for L2/L3 is acceptable because the API path is currently used only for simple work; the agentic L2 work is always routed through Claude Code by user preference. Cleanup action is to expand the module docstring to describe both engines, not to change the config.
- **2026-05-06**: F10 / F11 / F23 (and any similar findings about CFR not being fully reflected in user-facing copy) categorized as **rollout follow-up, not architectural drift**. CFR pipeline was integrated 2026-04-30; UI/report copy updates are part of the in-progress rollout. Don't conflate with cleanup arc — these are trivial copy updates that get done as the CFR rollout finishes.

## Bug log

- **B1** (2026-05-06): `comparator.py:L94-97` `PRICING` dict has wrong rates for `claude-haiku-4-5-20251001` — declared as `$0.80 / $4.00` per million tokens. Current Anthropic pricing is **`$1.00 / $5.00`** per million tokens (verified via web search 2026-05-06; matches QC's `MODEL_PRICING` at qc_analyzer.py:L86). The wrong rates appear to be Haiku 3.5 numbers carried forward against the new Haiku 4.5 model ID. Effect: every comparator run reports cost ~20% lower than actual. No user-visible behavior break, but the `est_cost` column in compiled CSVs and the cost displays in `report.py` are systematically under-reported. Cross-app: the existence of two pricing dicts for the same model with different rates is itself the cleanup signal — see F4 opportunity for shared `tools/cost_tracker.py`.

## To do for next session

1. ~~**Deep architectural findings**~~ — **COMPLETE 2026-05-06**. Findings F24-F33 added (zero-retry across all API call sites, L2 cache treats degenerate outcomes as real, multiple magic numbers, schema drift across layers, tool-description divergence with QC, formatter under-context vs synthesis, sequential L3 vs parallel L2). F6 (Claude Code mid-run failure) verified adequate. Three cross-app patterns surfaced: CA-8 (retry-policy divergence), CA-9 (`SEARCH_OLG_TOOL` divergence), CA-10 (three different agentic-loop budgets) — logged in `../cross_app_findings.md`.
2. **Cross-app comparison pass**: with both QC and comparator audited, do a side-by-side of the things that look duplicated:
   - `extract_json` (F3)
   - `TokenTracker` / `CostTracker` and their pricing dicts (F4 + B1)
   - Formatters (`format_*_for_prompt`)
   - Prompt loaders (`load_prompt`)
   - L0/L1 seed-search pattern vs QC's seed search
   - L3 cross-checks (F9) vs QC's cross-checks (QC F2)
   - Banner-section conventions and module-level docstring shape
   This is the data the A1/A2/B decision needs — and after this pass we'll have a concrete list of what would land in a shared `tools/llm_helpers.py` (or `tools/cost_tracker.py` etc.).

3. **Output / presentation shape comparison** (separate concern from #2 — these are user-facing artifacts, not internal duplication):
   - **Static HTML report vs live UI**: comparator emits a standalone HTML file (`report.py` → `report_*.html`) with filtering / favorites / notes / dark mode / CSV export, intended for offline sharing. QC has no analog — its "report" is the live FastAPI tab plus a downloadable `summary.csv`. Both shapes earn their weight (comparator = overnight batch → shareable artifact; QC = iterative phased work → interactive harness), but the asymmetry is undocumented and there's currently no path for "share QC results outside the harness." Decide: stays asymmetric (intentional deviation), QC grows a report, or comparator's report folds into the UI.
   - **CSV output design**: both apps produce CSVs that grew accretively. Comparator: `comparison_compiled_*.csv` + `comparison_interim.csv` + `layer0_classifications.csv` + the HTML report's filtered-rows export. QC: `summary.csv` (UI path, 12 cols + optional cross-check cols) + `{stem}_analyzed{suffix}.csv` (CLI path, original row + 6 appended cols). Columns were tacked on as features were added, not designed end-to-end. **Stop and think about what a deliberately designed spreadsheet output looks like for each app** — what columns, what schema, who reads it, do they need to merge with the source CSV or stand alone? This is bigger than the audit; may warrant its own work item rather than being absorbed into cleanup.
