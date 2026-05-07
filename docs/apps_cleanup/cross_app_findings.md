# Cross-App Findings

Working document for findings that span two or more apps. Populated during the cross-app comparison pass after each app's individual audit is complete.

## Why a separate doc

App-specific cleanup notes (`{app}_cleanup/README.md`) capture findings within a single app. This doc captures **patterns that emerge only when comparing apps side by side** — duplications, drifted helpers, inconsistent retry policies, divergent CSV schemas, etc. Without this doc, the same observation would have to be written into each app's notes, and a future reader would have to reconstruct the cross-cutting picture from fragments.

## Status

- **2026-05-06**: skeleton created. Findings populated as comparator deep findings completed.
- **2026-05-06 (later)**: search audit complete (steps 1-5 + deep findings F1-F24, plus synthesis-interaction findings NS1-NS9). Cross-app comparison pass executed: each CA-N promoted from seed to recommendation with canonical implementation identified, destination module proposed, severity/sequencing assigned. Two new CAs added (CA-11 `do_search` divergence, CA-12 scripted-progress UI patterns). A1/A2/B decision section added with **B (factor only duplicates) as the leading recommendation** — see end of doc.
- **2026-05-06 (final author pass)**: author audit complete (steps 1-5 + deep findings F1-F26 + B1/B2). Three new CAs added from author inputs: CA-13 (Claude Code subprocess duplication), CA-14 (SynthesisResult persistence shapes), CA-15 (load_config × 5 + prompt-loading conventions). Author-side data points added to existing CAs. **All four apps audited; cleanup execution sequencing is ready.**

**Status of cleanup arc**: Four apps audited (QC ✅, comparator ✅, search ✅, author ✅). Cleanup execution begins next.

## How to use this doc

When auditing app N+1, if a finding *also* applies to apps already audited, log it here as a cross-app finding (CA-1, CA-2, ...) with citations to each app. The original app's notes can keep its app-specific finding and link here for the broader pattern.

## Cross-app findings

### CA-1 [recommendation] Cost tracking duplicated across apps with one model dict per app

- `programs/comparator/comparator.py:L94-97` — `PRICING` dict (**wrong rates — B1**)
- `programs/qc/qc_analyzer.py:L85-89` — `MODEL_PRICING` dict (correct rates)
- `tools/synthesis.py:L36-40` — `MODEL_PRICING` dict (correct rates)

**Canonical**: synthesis's `MODEL_PRICING` + `calculate_cost()` (function form, synthesis.py:L217-219). Three sources cross-referenced; only comparator drifted, and the drift is a real cost-reporting bug (~20% under-report).

**Recommendation**: extract to `tools/cost_tracker.py`:
- `MODEL_PRICING` constant (sourced from synthesis)
- `calculate_cost(model, in_tok, out_tok)` primitive (synthesis's exact function)
- `TokenTracker` / `CostTracker` class — keep two purpose-fit class shapes (comparator's session/total vs QC's stage-keyed) since they accumulate differently. Or: parameterize a single `Tracker(stages: list[str])` class. Lean toward parameterized.

**Severity**: medium for extraction; **high for B1 fix** (live cost-reporting bug).

**Sequencing**: B1 fix first (one-line edit), then extraction. Extraction can wait until the second-most-touched cost-tracking change is needed.

### CA-2 [recommendation] `extract_json` / structured-output extraction

- `programs/comparator/comparator.py:L47-77` — `extract_json` with `{classification, confidence, note}` fallback
- `programs/qc/qc_analyzer.py:L250-278` — `extract_json` with `{coverage, confidence, reasoning}` fallback (misleading `fallback_classification` parameter — QC F5/B1)
- `tools/synthesis.py` — does NOT have structured-output extraction; returns markdown

**Canonical**: neither — they serve different result schemas; synthesis doesn't need this at all.

**Recommendation**: **don't consolidate**. The function bodies look duplicate, but their value is in their fallback shape, which is bound to each app's result schema. A parameterized version becomes `_default_or_dict(parse_func, fallback_dict)`, too thin to justify a shared module.

**Cleanup actions**:
- Fix QC F5/B1 (rename or remove `fallback_classification` parameter — it's dead for cross-checks)
- Document each as purpose-fit, not drift
- If a *third* structured-output caller emerges, revisit consolidation

**Severity**: low. Documentation-only.

### CA-3 [recommendation, MAJOR] Result formatting for prompts (Python + template layers)

**Python layer:**
- `tools/synthesis.py:L124-210` — single `format_results_for_prompt(results, source)`, all four sources, richest metadata
- `programs/comparator/comparator.py:L511-608` — four separate functions; OLG formatter is leaner than synthesis's (comparator F30)
- `programs/qc/qc_analyzer.py:L281-311` — single OLG-specific formatter, plus `_format_source_results_for_prompt` (L1067-1100) for cross-checks

**Template layer (search audit added):**
- `ui/templates/partials/result_card.html` — raw search per-source dispatcher
- `ui/templates/partials/answer.html:L31-83` — synthesis evidence per-source dispatcher
- `ui/templates/history_detail.html:L40-56` — history evidence per-source dispatcher (**CFR missing — F5/B1 in search notes**)
- `ui/app.py:_build_export_markdown` (L216-278) — docx-export per-source dispatcher

**Total: nine places dispatch on source key with diverged metadata-field choices.** Adding a fifth source would touch all nine.

**Canonical (Python)**: synthesis's `format_results_for_prompt` (single function, all sources, richest metadata).

**Recommendation**: extract synthesis's version to `tools/result_formatters.py`. Comparator's four functions converge to it. QC's OLG formatter calls into it. Comparator preserves any hand-tuned details by passing options (e.g., `include_url=False` if it doesn't need URLs).

**Template layer is a separate solve** — Python helpers don't share to Jinja directly. Two paths:
1. **One shared partial** (`partials/result_card_evidence.html`) with `verbosity` flag. answer.html / history_detail.html / result_card.html include with different flags. F5/B1 wouldn't have happened if both partials shared a base.
2. **Server-render the per-source markup** in Python and pass it into templates as pre-rendered HTML. Couples templates to Python more than the project currently does.

Lean toward (1).

**Severity**: HIGH. Most-touched cross-app duplication. **F5/B1 is a real bug caused by this pattern.** [Subsumes the original "OBS-J markdown dispatcher" and search F6/F14.]

**Sequencing**: Python layer first (synthesis exports → comparator + QC import); template layer when next CFR-style addition happens or when answer.html / history_detail.html need a coordinated change.

### CA-4 [recommendation, KEY DECISION] Agentic search loop — option B leading

- `tools/synthesis.py:L334-535` — `run_deep`, ONE tool (`search_policy`, multi-source enum)
- `programs/qc/qc_analyzer.py:L617-799` — judge loop, ONE tool (`search_olg`)
- `programs/comparator/comparator.py:L693-799` (L2 API) — TWO tools (`search_olg` + `lookup_fns_section`)

All three share the same control flow. Differences are caller-specific:
- Multi-tool calling (comparator L2 has two)
- Pre-fetched evidence as user message vs. message history (QC injects history; synthesis uses string)
- Markdown text vs. structured JSON output (synthesis text; comparator/QC strict JSON)
- Engine routing API ↔ Claude Code (comparator L2 only)
- Custom result formatter per caller (QC's OLG-specific richer metadata)
- Custom budget design (comparator turn-only, synthesis split, QC formula — see CA-10)
- Custom error-result shape (synthesis returns `answer="error: ..."`, QC returns Partial w/ LOW confidence, comparator returns `confirmed_gap` w/ LOW confidence)

**Seven dimensions of caller-specific flexibility.** A shared primitive must absorb all seven, OR each caller keeps its loop.

**Recommendation: option B (leave loops separate; factor only the duplicates).**

The search audit (synthesis-interaction findings NS1-NS9) clarified that **synthesis is the cleanest of the three loops, and the drift is in QC and comparator drifting from synthesis's idioms, not in synthesis being the wrong shape.** The clean extractions in CA-1, CA-3, CA-8, CA-9, CA-11 deliver ~80% of A2's structural value:
- `tools/cost_tracker.py` (CA-1)
- `tools/result_formatters.py` (CA-3)
- `tools/retry.py` (CA-8)
- `tools/policy_tools.py` (CA-9)
- Shared search client cache via `rag/query.py` (CA-11)

…without requiring the agentic loops to share code. Each app keeps its purpose-fit loop but pulls from the same helper toolbox.

**A2 stays viable** as a longer-term option if a fourth agentic-loop callsite emerges (e.g., a future "compare two policy passages" tool). Until then, the primitive's absorbing scope (7 dimensions) outweighs its value.

**A1 (extend `run_synthesis`) is rejected** — confirmed by search audit. Adding tools-list + extractor + engine-routing + seed-results turns a 9-param function into a 13-param one with most params unused for /ask. Wrong-shaped abstraction.

**Severity**: medium for documentation, low for code change (option B requires no agentic-loop edits).

### CA-5 [recommendation] Outdated docstring usage paths from before directory restructure

- `programs/comparator/comparator.py:L1-28` — model claims (F1, resolved as docs-only)
- `programs/comparator/report.py:L4-7` — `python agents/report.py`
- `tools/synthesis.py:L7-11` — `python agents/synthesis.py`
- `programs/qc/qc_analyzer.py:L1-21` — "Two-call architecture" (QC F4)
- `ui/search.py:L4` — "Wraps core/query.py" (search F1)

**Canonical**: actual current paths from the restructure (2026-04-06). All five docstrings are out-of-date by the same amount — easy chore PR.

**Recommendation**: trivial sweep. One commit updates all five.

**Severity**: trivial. Bundle into the next housekeeping commit.

### CA-6 [recommendation] Output presentation shapes are intentionally asymmetric across apps

- Comparator: standalone HTML file (`report.py`), browser localStorage for favorites/notes
- QC: live FastAPI tab + downloadable `summary.csv`; no standalone artifact
- Author: docx file (the deliverable IS the artifact)
- Search (Ask tab): live UI, SQLite history, docx download per search

**Recommendation**: **document as intentional, do not unify.** Each shape earns its weight:
- Comparator → overnight batch → shareable artifact for review
- QC → iterative phased work → interactive harness with row selection
- Author → final document → docx in OLG template
- Search → live conversation → in-place answers

**Cleanup action**: add a "User-facing artifact" section to each app's notes with a one-line rationale for the chosen shape. Capture asymmetry in the apps_cleanup README so it's not re-asked.

**Open question** (deferred): does QC need a standalone shareable artifact ("here's what the analyzer found")? Probably yes for sharing with leadership. Feature work, not cleanup.

**Severity**: documentation-only.

### CA-7 [recommendation, deferred] Spreadsheet/CSV outputs grew accretively across apps

- Comparator: `comparison_compiled_*.csv` + `comparison_interim.csv` + `layer0_classifications.csv` + HTML report's filtered-rows export
- QC: `summary.csv` (UI, 12 cols + optional cross-check cols) + `{stem}_analyzed{suffix}.csv` (CLI, 6 appended cols)

**Recommendation**: **defer to its own work item, NOT absorbed into cleanup.** This is end-to-end output design, not duplication-elimination. Each app needs:
- What's the deliverable for? (sharing? merging back into source CSV? archival?)
- Who reads it?
- What's the schema? Is it stable across runs?
- Does it need to round-trip into a system of record?

These questions warrant a dedicated design pass, not piecemeal column tweaks.

**Severity**: out of scope for cleanup arc. Logged here so the question doesn't get lost.

### CA-8 [recommendation, MAJOR — top of execution queue] Retry / rate-limit policies diverge wildly

| App | Stage | Retry policy |
|---|---|---|
| Synthesis | `run_deep` | One retry on `RateLimitError` after `time.sleep(60)`; error result on second failure (synthesis.py:L412-448) |
| Synthesis | `run_standard` | **No retry** (synthesis NS6 — search audit) |
| Synthesis | `/ask` route handler | **No try/except** (search F8) |
| Synthesis | `init_clients()` startup | **No try/except**; failure wedges all four apps (search F9) |
| QC | Extractor | 3 attempts, backoff `30 * (attempt+1)`s, synthetic fallback (QC F7) |
| QC | Judge | One retry after 60s; second failure → Partial w/ LOW (QC F7) |
| QC | Cross-checks | **No retry** (QC F7) |
| Comparator | L0, L1, L2 API, L3 CMR, L3 CFR | **No retry anywhere** (comparator F24) |

Search audit added three new bare-handed sites: `run_standard`, `/ask`, `init_clients`. **Synthesis's standard mode is bare-handed despite being the default path.**

**Canonical**: synthesis's `run_deep` retry pattern (60s sleep, one retry, error-result on failure).

**Recommendation**: extract `tools/retry.py` with a single helper. Two API options:
1. Decorator: `@with_rate_limit_retry(max_attempts=2, sleep_seconds=60)` applied at every API call site
2. Function: `with_retry(callable, *, max_attempts=2, sleep_seconds=60)` invoked at every API call site

Lean toward decorator (less callsite editing). Then:
- Apply at synthesis's `run_standard` (bare → covered)
- Apply at every comparator call site (5 sites)
- Apply at QC's cross-check sites (3 sites)
- Apply at QC's existing retry sites (replace handcrafted retry)
- Wrap `/ask` route in try/except returning a partial that shows error in `#answer-area`
- Decide policy for `init_clients` startup failures (fail-fast vs degrade-gracefully)

**Severity**: **HIGH**. **Top of cleanup execution queue.** Production reliability concern, especially for comparator overnight runs with parallel L2 workers.

**Sequencing**: extract `tools/retry.py`, apply to comparator F24 sites first (highest exposure), then QC cross-checks, then synthesis run_standard, then `/ask` route, then `init_clients` decision.

### CA-9 [recommendation] `SEARCH_OLG_TOOL` defined in two apps with diverged descriptions

- `programs/comparator/comparator.py:L672-690` — "BEACON system references"
- `programs/qc/qc_analyzer.py:L596-614` — "BEACON procedures"
- `tools/synthesis.py:L82-109` — `SEARCH_POLICY_TOOL` (multi-source enum, the most general)

**Canonical**: synthesis's `SEARCH_POLICY_TOOL` (single tool with multi-source enum) is the most general shape.

**Recommendation**: extract to `tools/policy_tools.py`:
- `SEARCH_POLICY_TOOL` — synthesis's multi-source version
- `SEARCH_OLG_TOOL` — OLG-only specialization (could be derived from SEARCH_POLICY_TOOL with `enum=["olg"]`)
- `LOOKUP_FNS_SECTION_TOOL` — comparator's L2 second tool (currently defined inline)

Each app imports the constants it needs. Single source of truth for descriptions ("BEACON procedures" — pick the wording, document it once).

**Severity**: medium. Bundle with CA-3's `tools/result_formatters.py` extraction.

### CA-10 [recommendation] Three different agentic-loop budget conceptions

| App | Budget design |
|---|---|
| Synthesis `run_deep` | `max_searches = 8` (config), `max_turns = 15` (hardcoded). Independent caps. |
| QC judge | `max_turns = max_searches + 5`. Formula. |
| Comparator L2 | `max_turns = 15` (hardcoded) only. No separate search cap. |

**Search audit added**: synthesis's `max_turns = 15` hardcode and comparator's hardcoded 15 are the **same magic number** (NS8). Suggests one was modeled on the other, or both converged on "15 feels right." QC's formula is the outlier.

**Canonical**: synthesis's design (separate `max_searches` config + `max_turns` hardcode) is the most disciplined — the apps that *lack* a separate search cap (comparator) are missing it by oversight, not design.

**Recommendation**:
- Convert `max_turns` to config (`[synthesis] max_turns = 15`) so it's tunable
- Comparator L2 grows a separate `max_searches` cap with same semantics as synthesis
- QC's formula stays — it's purpose-fit (judge needs reasoning headroom after final search)

**Severity**: low. Documentation + small config additions; no behavior change for default values.

### CA-11 [recommendation, NEW from search audit] `do_search` divergence and dead-wired UI cache

- `ui/search.py:L94-120` — `do_search(query, source=DEFAULT_SOURCE, ...)`. Eager-init via module-level `_clients` populated at app startup.
- `tools/synthesis.py:L236-251` — `do_search(source, query, ...)`. Lazy-init via module-level `_search_clients` cache.

Same name, same conceptual operation. Subtle differences (search audit NS2):
- Reversed positional args (`query, source` vs `source, query`)
- search.py exposes `threshold`; synthesis hardcodes 0.0 internally

**Critical finding (search NS3)**: `ui/search.py:_clients` is **dead-wired** for the canonical `/ask` path. `/ask` → `run_synthesis` → `synthesis.do_search` → consults synthesis's lazy cache. UI's eager cache is only consulted by `ui/search.py:do_search`, which is only called by the dead `/search` raw endpoint (search F2).

**Canonical**: synthesis's lazy cache + signature.

**Recommendation**: depends on F2 (search's vestigial `/search` endpoint) decision:
- If F2 is killed: drop `ui/search.py:do_search` + `_clients` + `init_clients()` entirely. Synthesis's cache is the only one. Cleanest.
- If F2 is wired up: share the cache via `rag/query.py` or `tools/`. Both apps consume the same cache.

Lean toward dropping F2 (no one's been using it), which collapses CA-11 to a 5-minute cleanup.

**Severity**: medium. Tied to F2 decision in search cleanup.

### CA-12 [recommendation, NEW from search audit] Scripted-progress UI patterns × 4

| Location | Lines | Interval | Purpose |
|---|---|---|---|
| `ui/templates/index.html:L75-122` (inline) | 47 | 3000ms | Ask spinner |
| `ui/static/app.js:authorShowProgress` (L50-72) | 23 | 4000ms | Author spinner |
| `ui/static/app.js:qcShowProgress` (L530-561) | 32 | 4000ms | QC spinner |
| `ui/static/app.js:convertShowProgress` (L772-789) | 18 | 3000ms | Convert spinner |

Same pattern (text array, interval, opacity transition, hide). Inconsistent timings. **All four are scripted theater** (QC F27 already flagged this) — they cycle through messages independent of backend state.

**Canonical**: none of the four — they're all the same shape with different naming.

**Recommendation**: extract a single `showProgress(spinnerEl, steps, intervalMs)` helper in `ui/static/app.js`. Each app's specific text array stays where it is (`RESEARCH_STEPS`, `INVESTIGATE_STEPS`, etc.) — those are domain-specific and shouldn't centralize. The interval/transition/state-management logic centralizes.

**Real long-term solution**: SSE/WebSocket streaming so spinner text reflects actual backend state (QC F21 — "feature work, not cleanup"). Until then, at least the four implementations should converge.

**Severity**: low for cleanup, but a candidate quick win since the savings are visible (~70 lines down to ~20).

### CA-13 [recommendation, NEW from author audit, MAJOR] Claude Code subprocess launching duplicated

- `programs/comparator/comparator.py:L44` — imports `from tools.claude_code_runner import run_claude_task` (canonical wrapper)
- `programs/author/author.py:L300-353` (`launch_draft`) and `L356-381` (`launch_resume`) — hand-rolls `.bat` files + `subprocess.Popen` with `subprocess.CREATE_NEW_CONSOLE`. Does NOT import `claude_code_runner`.

`tools/claude_code_runner.py:L42-78` already supports the visible-terminal use case via `windowed=True` (L66-68): "If True, open in a visible console window (Windows). Session output streams to the window instead of being captured. **Useful for watching sessions in real time.**" — author's exact use case.

**Two independent Claude Code subprocess implementations exist; comparator imports the canonical one, author bypasses it.**

Differences worth noting:
- `claude_code_runner.run_claude_task` uses an explicit per-call `result_file` argument — eliminates author's shared-scratch-file race (B1 in author notes)
- Author needs `--session-id` for resume; current `run_claude_task` doesn't pass it through (mechanical addition)
- Author needs `claude --resume {session_id}` for the resume case; that's a different command shape (the `command` parameter would need extension)

**Canonical**: `tools/claude_code_runner.py` — already exists, already used by comparator.

**Recommendation**: migrate author's `launch_draft` and `launch_resume` to call `run_claude_task(..., windowed=True, ...)`. This requires:
1. Extending `run_claude_task` to accept `session_id` and pass it as `--session-id` to claude
2. Either extending it to support the `--resume` mode or adding a sibling `resume_claude_task(session_id, ...)` helper
3. Migrating author callsites; eliminates B1 (shared scratch file race), F7 (intra-module .bat duplication), and activates F15's dead `claude_code_timeout` config key

**Severity**: medium. Production reliability is fine today (single-user, single-machine), but the duplication is one of the cleanest cross-app extractions — the right module already exists.

**Sequencing**: after CA-8 retry helper. Not blocking. Bundle with author's CLI/UI parity decision (author F3) since both touch author internals.

[Resolves author OBS-C, OBS-H, OBS-L. Author findings F1, F7, F8, F15, F21 all touch this.]

### CA-14 [recommendation, NEW from author audit] SynthesisResult persistence shapes diverge

`run_synthesis()` returns `SynthesisResult` with 8 fields (synthesis.py:L66-75). Each persistence callsite picks a subset:

| Callsite | search_queries | model | tokens | cost | duration | evidence | answer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Author `evidence.json` (author.py:L156-179) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (rank, score, text, metadata, id) | — (separate `report.md`) |
| Search `save_search` (history.py:L80-98) | **✗** | ✓ | ✓ | ✓ | ✓ | ✓ (no rank) | ✓ |
| Search `answer.html` (synthesis evidence section) | count only | tooltip | combined | ✓ | ✓ | ✓ rendered | ✓ markdown |

**Search drops `search_queries` entirely** (search NS1) — exactly what author persists correctly. **Author's pattern is the canonical SynthesisResult-on-disk shape.**

**Canonical**: author's `evidence.json` (author.py:L156-179).

**Recommendation**: search adopts author's persistence pattern.
1. Add `search_queries TEXT` column to SQLite `searches` table (inline ALTER, per existing migration pattern)
2. `save_search` writes the full `result.search_queries` list as JSON
3. `_row_to_dict` reads it back
4. `answer.html` and `history_detail.html` render it as a `<details>` block ("Searches Claude ran")

This is **the cheapest synthesis-side win** — synthesis already produces it, no new computation needed, no API changes.

**Severity**: medium for the search-side fix, low complexity. Sequencing: bundle with B1 fix and CA-1 cost-tracker extraction since all three are SQLite-adjacent.

[Resolves author OBS-F. Search NS1 fix follows author's pattern.]

### CA-15 [recommendation] `load_config` × 5 + prompt-loading conventions

- `programs/author/author.py:L40-43` — own `load_config`
- `programs/comparator/comparator.py` — own `load_config`
- `programs/qc/qc_analyzer.py` — own `load_config`
- `tools/synthesis.py` — own `load_config`
- `ui/app.py:L44-45` re-imports author's via `load_config as load_author_config`, also imports QC's via `load_config as load_qc_config`

**Five+ apps each have their own one-line `load_config`** reading from the same `config.ini` with `configparser`. The function is one line, so the extraction is low-value individually.

Related: prompt-loading conventions diverge:
- Project-shared `prompts/` (synthesis, author research)
- App-local `programs/{app}/prompts/` (comparator, QC, author draft)

Author straddles both (per author F17 / OBS-B): research is project-shared (canonical synthesis), draft is app-local (app-specific).

**Canonical**: no extraction recommended for `load_config` — too thin to justify a shared module. Document the pattern as accepted.

For prompt-loading: keep the split. Project-shared = reusable across synthesis callsites; app-local = app-specific. Author's pattern (using project-shared for the synthesis-prompt and app-local for the agent-specific draft prompt) is the right convention.

**Recommendation**: documentation-only.
1. Add a one-paragraph "configuration access conventions" section to `docs/apps_cleanup/README.md` charter
2. Same for prompt-loading conventions
3. Future apps follow the established pattern

**Severity**: trivial. Bundle with CA-5 docstring sweep.

[Resolves author OBS-A, OBS-B.]

## A1 / A2 / B Decision (refined 2026-05-06; reaffirmed after author audit)

The cross-app comparison pass has enough data to take this decision. Search's synthesis-interaction analysis (search_cleanup NS1-NS9) was the load-bearing input. **Author audit reaffirms B**: author exercises 5 of 9 synthesis params (the deepest synthesis caller in the codebase), uses synthesis as a black box, and works correctly without modification. Synthesis is structurally healthy; the cross-app problem is QC and comparator drifting from synthesis's idioms, not synthesis being the wrong shape — both apps that use synthesis (search and author) get good outcomes from it.

### Recommendation: **B (factor only duplicates) — fully funded**

Extract these to `tools/`:

| Module | Contents | Replaces |
|---|---|---|
| `tools/cost_tracker.py` | `MODEL_PRICING`, `calculate_cost()`, `Tracker` class | comparator PRICING + TokenTracker, QC MODEL_PRICING + CostTracker, synthesis MODEL_PRICING |
| `tools/result_formatters.py` | `format_results_for_prompt(results, source, **opts)`, `SOURCE_LABELS` | synthesis's formatter + 4 comparator fns + QC's OLG fn |
| `tools/retry.py` | `@with_rate_limit_retry` decorator | synthesis run_deep retry, QC's three different retries, comparator's zero retries, search /ask error handling |
| `tools/policy_tools.py` | `SEARCH_POLICY_TOOL`, `SEARCH_OLG_TOOL`, `LOOKUP_FNS_SECTION_TOOL` | comparator's tool defs, QC's tool def, synthesis's SEARCH_POLICY_TOOL |
| (`rag/query.py` extension) | shared client cache module-level | ui/search.py:_clients + synthesis._search_clients |

Each app keeps its purpose-fit agentic loop. Each app pulls from the same helper toolbox.

### Why B over A1 / A2

- **A1 rejected**: extending `run_synthesis()` with tools/extractor/engine/seed-results turns a 9-param function into a 13-param one with most params unused for /ask. Wrong-shaped abstraction.
- **A2 deferred**: a shared `agentic_search_loop` primitive must absorb 7 dimensions of caller-specific flexibility (multi-tool, structured output, engine routing, seed-message-history, custom formatter, custom budget, custom error shape). The primitive becomes ~as complex as the apps that call it. Worth doing IF a fourth agentic-loop callsite emerges; until then, the absorbing scope outweighs the value.
- **B chosen**: synthesis is already the cleanest of the three agentic loops. Drift is in QC and comparator drifting from synthesis's idioms, not in synthesis being the wrong shape. The clean extractions (CA-1, CA-3, CA-8, CA-9) deliver ~80% of A2's structural value with a fraction of the change surface.

### Sequencing for execution

1. **CA-8 retry helper** (production reliability — top of queue). Author adds 4 more bare-handed routes to the catalog (author F4); all five apps now have retry-policy gaps.
2. **B1 fix** (comparator's wrong Haiku rates — one-line)
3. **CA-14 search-history persistence** (low-effort, high-value: search NS1 fixed by adopting author's `evidence.json` shape; bundle with B1 since both are SQLite-adjacent)
4. **CA-1 cost tracker extraction** (after retry, since both touch every API site)
5. **CA-3 result formatters** (Python layer first; template layer when next coordinated change happens)
6. **CA-9 policy tools** (bundled with CA-3 since both move source-related constants)
7. **CA-11** (collapses to nothing if F2 is killed; trivial otherwise)
8. **CA-13 Claude Code subprocess unification** (extends `claude_code_runner.py` to support `--session-id` + resume; migrates author's `launch_draft`/`launch_resume`; eliminates author B1, F7; activates F15's dead `claude_code_timeout` config). Bundle with author's CLI/UI parity decision (author F3).
9. **CA-5 docstring sweep + CA-15 conventions docs** (any housekeeping commit; author F1, qc F4, comparator F1/F2, search F1, synthesis L7-11 all updated together)
10. **CA-12 progress helper** (low-priority quick win)
11. **CA-10 budget convergence** (small config addition, no behavior change)
12. **CA-2 / CA-6 / CA-7** (documentation-only or deferred to own work)

### What's explicitly out of scope for the cleanup arc

- A1 / A2 (loop consolidation) — defer until a fourth callsite emerges
- CA-7 (CSV output redesign) — separate end-to-end design pass
- Streaming progress / SSE (QC F21, comparator equivalent) — feature work
- Engine routing for QC and synthesis (per architecture principles update) — feature work

## To do

- ~~Populate during cross-app comparison pass~~ — **COMPLETE 2026-05-06**. CA-1 through CA-10 promoted from seeds to recommendations; CA-11 and CA-12 added from search audit; A1/A2/B decision recommended (B).
- ~~**Author audit**~~ — **COMPLETE 2026-05-06**. CA-13 (Claude Code subprocess duplication), CA-14 (SynthesisResult persistence shapes), CA-15 (load_config × 5 + prompt-loading conventions) added. Author-side data points added to existing CAs (CA-1, CA-3, CA-8, CA-12). A1/A2/B decision reaffirmed.
- ~~**Synthesis audit**~~ — **COMPLETE 2026-05-06**. 30 findings in `synthesis_review/audit.md`. MAJOR: F3 (run_standard has no retry). Top implications inform CA-1 / CA-3 / CA-8 / CA-9 extractions and the SynthesisResult contract change (add `error: str | None`).
- ~~**Decision pass**~~ — **COMPLETE 2026-05-06**. All 8 open decisions resolved by user. See `execution_plan.md` "Decisions resolved" table for canonical record. Cross-cutting principles surfaced: no silent program filtering anywhere; tool descriptions stay neutral while caller intent lives in prompts; cost-tracking gaps don't halt work.
- ~~**Build shared modules**~~ — **COMPLETE 2026-05-06**. `tools/retry.py`, `tools/cost_tracker.py`, `tools/result_formatters.py`, `tools/policy_tools.py` all built and synthesis fully migrated. Resolves synthesis F3, F6, F11, F15, F22.
- **QC migration** — NEXT. Sequenced into 5 sub-steps; sub-step 1 = delete CLI pipeline. See `execution_plan.md` "QC migration sub-steps".
- **Decisions log** — captured in `execution_plan.md` rather than scattered across per-app notes.
