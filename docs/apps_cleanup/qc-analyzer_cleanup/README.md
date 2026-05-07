# QC Analyzer — Cleanup Notes

Working document. Updated across sessions. See `../README.md` for the cleanup charter.

## Purpose of QC Analyzer

QC findings (from external Quality Control sample review CSVs) are processed through a multi-stage pipeline that ends in a coverage assessment per finding:

1. **Extractor** — Haiku distills the finding's narrative into structured policy issues and a list of search queries
2. **Seed search** — runs extractor's queries against OLG, deduplicates results
3. **Judge** — Sonnet agentic loop with a `search_olg` tool; iteratively investigates and classifies coverage as **Adequate / Partial / Gap**, returns OLG references + gap description + confidence + reasoning
4. **Cross-checks** — separate single-turn Haiku classifications for CMR / FNS / CFR (whether each authority addresses the gap found by the judge)

Output: per-finding JSON with full evidence + a CSV row per finding for human review.

> TBD during soup-to-nuts dive: confirm input format, end-user output details, UI vs CLI surface, whether cross-check results are exposed to users.

## Architectural findings

### 1. Judge loop is structurally identical to synthesis deep-mode (2026-05-05)

The QC judge loop and `tools/synthesis.py`'s deep-mode loop are the same control structure:

- Same turn-budget agentic search loop
- Same tool-use termination on `stop_reason`
- Same single-tool design (`search_olg` vs `search_policy`)
- Differences are parameter-bound (turn-count formula, search budget defaults) and instrumentation (QC has TraceLogger, synthesis doesn't)

Source: side-by-side review of `qc_analyzer.py:L617-799` vs `synthesis.py:L401-535`.

### 2. Three blockers prevent the judge from collapsing into `run_synthesis()` as-is

1. **Seed-results injection.** QC injects pre-computed seed results as message history (`qc_analyzer.py:L629-641`); synthesis only uses pre-fetches as a context string (`synthesis.py:L386-392`), not in the agent's message history. The agent perceives seed results differently in each.
2. **Output shape.** QC expects strict JSON `{coverage, olg_references, gap_description, confidence, reasoning}` parsed via `extract_json()`; synthesis returns markdown `answer` text untouched.
3. **Result formatter customization.** QC has OLG-specific formatter with breadcrumb, parent_heading, chunk_n/total (`qc_analyzer.py:L281-311`); synthesis formatter is generic.

### 3. What clearly stays in qc_analyzer regardless of consolidation

- **Extractor stage** (`qc_analyzer.py:L856-942`) — QC-specific preprocessing, no analog in synthesis
- **Seed search stage** (`qc_analyzer.py:L568-589`) — QC-specific orchestration
- **Cross-check stages** (CMR/FNS/CFR, `qc_analyzer.py:L1134-1389`) — single-turn classifications, not agentic loops; not even candidates for the loop-consolidation question

### 4. Engine routing does not apply here [DOWNGRADED 2026-05-06]

QC is API-only. No Claude Code path. ~~The engine-routing question (API vs Claude Code, raised in the broader architecture review) does not affect QC. Clean.~~

**Updated 2026-05-06**: the lack of a Claude Code path is now treated as a **gap, not intentional design** — see decisions log entry of the same date. Engine routing *does* apply here; QC just hasn't been wired through Claude Code yet. Doesn't change anything about the cleanup arc itself (engine routing is feature work, not cleanup) but changes the framing.

## Opportunities (not yet decided)

### Loop consolidation — A1 / A2 / B

| Option | Shape | Tradeoff |
|---|---|---|
| **A1** | Extend `run_synthesis()` with `seed_results`, `result_schema`/`result_extractor`, `result_formatter` parameters so QC judge can call it. | Bloats synthesis with parameters no human-Ask use case needs. Wrong-shaped abstraction. |
| **A2** | Extract a shared `agentic_search_loop` primitive (likely in `tools/`). Both `run_synthesis()` (deep mode) and QC's `run_judge()` call into it. Each stays a thin purpose-fit shell. | Cleanest separation but introduces a new module — only worth it if comparator L2 also fits. |
| **B** | Leave loops separate; factor out only the genuine duplicates (`format_results_for_prompt`, tool definition pattern). | Honest if A2 doesn't generalize, but accepts the structural duplication. |

**Decision deferred** until comparator L2 is reviewed. The strongest test of A2 is whether the primitive can also serve comparator L2 (which has both an API tool-use loop and a Claude Code path).

### Other findings to investigate during the soup-to-nuts dive

- `max_turns = max_searches + 5` (`qc_analyzer.py:L648`) — was this tuned, or a guess? What was the failure mode it's defending against?
- `TraceLogger` per-turn instrumentation (`qc_analyzer.py:L650-784`) — is the trace consumed downstream, or is it dev-time only? If dev-time, should it stay?
- Cross-check classification taxonomies (`cmr_covers_topic / cmr_silent / cmr_differs` and analogs) — are they consistent across CMR/FNS/CFR? Worth aligning to one shape?
- Program filtering — QC passes `None` (no filter). Should it filter to SNAP at minimum, given QC is a SNAP-program quality control?
- Input handling — CSV format, encoding fallback (cp1252 mentioned in memory), failure modes
- Output ergonomics — CSV row + per-finding JSON, who reads which, are both used

## File shape (2026-05-05)

`qc_analyzer.py` is a single 1,658-line module organized into eight sections by comment banner:

1. Configuration (L40-77) — paths, `APPENDED_COLUMNS`, `load_config`, `load_prompt`
2. Cost tracking (L80-146) — hardcoded `MODEL_PRICING` dict, `CostTracker` class
3. Trace logging (L149-243) — `TraceLogger` class + `_summarize_seed_results`
4. Utilities (L246-311) — `extract_json`, `format_olg_results_for_prompt`
5. CSV I/O (L314-351) — `load_csv` (UTF-8/CP1252 fallback), `select_rows`, `write_output_csv`
6. Checkpoint/resume (L354-375) — JSON checkpoint at `output/qc_analysis/qc_checkpoint.json`
7. Per-analysis dir management (L378-485) — `get_analysis_dir`, `save_finding`, `load_finding`, `load_all_findings`, `save_meta`, `load_meta`, `generate_summary_csv`
8. Pipeline stages (L488-1389) — Extractor, Seed search, Judge, Output rows, UI-facing pipeline functions, Cross-checks
9. Main orchestrator + CLI (L1392-1658) — `analyze_csv`, `main`

## Architectural findings — full list

### F1 [MAJOR] Two parallel pipelines, diverged

There are **two complete pipelines** in this file that do nearly the same work but have diverged in I/O patterns, observability, and feature coverage:

| | **CLI pipeline** (`analyze_csv`, L1396-1594) | **UI/phased pipeline** (`run_extract` + `run_investigate` + `run_*_check`) |
|---|---|---|
| Entry point | `analyze_csv()` | UI calls `run_extract()` → `run_investigate()` → `run_{cmr,fns,cfr}_check()` separately |
| State | In-memory rows + `output_rows` list | Per-finding JSONs at `analysis_dir/results/row_NNN.json` + `meta.json` |
| Resumability | `qc_checkpoint.json` (single file, single CSV run) | `phase` field on each finding JSON, plus `meta.json["phases"]` |
| Trace logging | `TraceLogger` writes per-row JSONL | None |
| Cross-checks | **Not invoked** | Available as separate phases |
| Output | `{stem}_analyzed{suffix}.csv` (appended columns) | `summary.csv` (different schema) — generated by `generate_summary_csv()` |
| Progress feedback | Verbose `print()` per row + per stage | Same `print()` calls — but stdout goes to the UI's process |

**Implication**: A user running the CLI gets traces + checkpointing but no CMR/FNS/CFR cross-checks. A user running through the UI gets cross-checks but no traces. Neither path is "complete." The file does not have a single canonical pipeline.

### F2 [MAJOR] Cross-check functions are 99% copy-paste

`run_cmr_check` (L1134-1217), `run_fns_check` (L1220-1301), and `run_cfr_check` (L1304-1389) are structurally identical:

- Same load config / load prompt / create client pattern
- Same `row_indices` defaulting to all Partial/Gap findings
- Same per-row loop: search source → format results → build user message → single Haiku call → parse JSON → save
- Same metadata write at end

**Differences (only):**
- Source name string (`"cmr"`/`"fns"`/`"cfr"`)
- Prompt name (`qc_cmr_check`/`qc_fns_check`/`qc_cfr_check`)
- Model config key + fallback string (e.g., `cmr_check_model`/`cfr_silent`)
- Result field name in the saved finding (`_cmr_check`/`_fns_check`/`_cfr_check`)
- `cmr_sections`/`fns_sections`/`cfr_sections` field name in the parsed result
- **CFR has `program="SNAP"` filter (L1353); CMR and FNS do not** — see F6

This is ~240 lines that could be one parameterized `run_source_check(source, ...)`.

### F3 Two near-identical result summarizers

`_summarize_seed_results` (L230-243) and `_summarize_search_results` (L802-815) are the same function except for text-preview length (200 vs 300 chars). Only one is needed.

### F4 Module docstring is wrong

Top-of-file docstring (L1-21) says **"Two-call architecture: Extractor + Judge"**. The actual pipeline has six stages (extractor, seed search, judge, CMR check, FNS check, CFR check). New readers will form a wrong mental model.

### F5 `extract_json` fallback is wrong-shaped for cross-checks

`extract_json` (L250-278) takes a `fallback_classification` parameter that gets put into a `coverage` field on the fallback dict. Cross-checks pass `fallback_classification="cmr_silent"` (etc.) but then read `check_result.get("classification", "cmr_silent")` (L1201) — they look in `classification`, not `coverage`. The fallback path is functionally **dead** for cross-checks (the `.get()` default catches it), and the parameter is misleading.

### F6 Program filtering inconsistency (also flagged in broader review)

CFR cross-check filters `program="SNAP"` (L1353); CMR and FNS cross-checks pass no filter. CFR has explicit program labels (SNAP / Issuance / Administration / QC / Disaster / Summer-EBT) that make this filter meaningful, but the inconsistency is undocumented.

### F7 Inconsistent retry/rate-limit strategies

| Stage | Retry behavior |
|---|---|
| Extractor (L527-561) | Up to 3 attempts, backoff `30 * (attempt+1)`s, falls back to a synthetic "extraction failed" result |
| Judge (L664-696) | One retry after 60s; second failure returns Partial result with LOW confidence |
| Cross-checks (L1189-1194, etc.) | **No retry logic at all** — a rate limit or API error during cross-check crashes the whole phase |

### F8 [DOWNGRADED] Hardcoded search params in cross-checks

Cross-checks hardcode `top_n=5, threshold=0.0` (L1180-1181, L1265-1266, L1354-1355). Judge uses configurable `olg_results_per_search`. The hardcoded `5` happens to equal the config default for `olg_results_per_search` and `seed_results_per_query`, so it's not disagreeing with config, just inlined. Still cleanup-worthy (config-driven would be cleaner) but lower severity than initially logged.

### F9 Hardcoded model pricing in code

`MODEL_PRICING` dict (L85-89) hardcodes per-million-token rates for three specific dated model versions. Anything else falls back to Sonnet pricing. New models will be silently mis-priced. Belongs in config or a shared cost-tracking module.

### F10 Cross-check query phrasing assumption

All three cross-checks search authority sources using `query = finding["policy_issues"]` (L1173, L1258, L1346) — the extractor's distilled summary. **This was tuned for OLG search**; whether it's also right for CMR / FNS / CFR is an assumption, not a verified design choice. Worth a benchmark.

### F11 Magic-number turn budget

Judge sets `max_turns = max_searches + 5` (L648). The +5 is unexplained. Is it a buffer for trailing reasoning turns after the last tool call? An empirical tuning result? Should probably be either a config knob or a stated constant.

### F12 OLG-specific phrasing in tool description

Judge's `SEARCH_OLG_TOOL` description (L596-614) mentions "BEACON procedures" — a Massachusetts-specific case-management system reference baked into a tool description. Probably correct for this app, but worth flagging if the tool ever gets generalized (per A2 option, the shared `agentic_search_loop` primitive would not include this).

### F13 Cross-check prompt assumes a fixed source-result label format

`_format_source_results_for_prompt` (L1067-1100) has hardcoded per-source label rules. CFR uses `§ {sec_num} {sec_title} {hierarchy}`, CMR/FNS use plain `{sec_num} {sec_title}`. This is small enough to be fine, but worth noting that adding a new source would require editing this function.

### F14 Print-vs-log

Pipeline functions print progress directly to stdout. Fine for CLI; for UI paths the stdout goes wherever the host process captures it. A logger would let UI surface progress more cleanly without changing CLI behavior.

### F15 Two output formats with no shared schema

`write_output_csv` (CLI) writes original-row + 6 appended columns. `generate_summary_csv` (UI/phased) writes a fully reformulated 12-column schema with optional cross-check columns. These represent the same data differently. Consumers downstream of either format would handle different shapes.

## Opportunities (not yet decided)

### Loop consolidation — A1 / A2 / B *(unchanged from prior session)*

| Option | Shape | Tradeoff |
|---|---|---|
| **A1** | Extend `run_synthesis()` with `seed_results`, `result_schema`/`result_extractor`, `result_formatter` parameters so QC judge can call it. | Bloats synthesis with parameters no human-Ask use case needs. Wrong-shaped abstraction. |
| **A2** | Extract a shared `agentic_search_loop` primitive (likely in `tools/`). Both `run_synthesis()` (deep mode) and QC's `run_judge()` call into it. | Cleanest separation but introduces a new module — only worth it if comparator L2 also fits. |
| **B** | Leave loops separate; factor out only the genuine duplicates (`format_results_for_prompt`, tool definition pattern). | Honest if A2 doesn't generalize, but accepts the structural duplication. |

### Pipeline unification (RESOLVED 2026-05-05)

**Decision: phased pipeline is canonical. CLI is legacy.**

Rationale: the phased model is *earning its weight* in the UI:
- Cost gating between Extract (cheap Haiku) and Investigate (expensive Sonnet agentic)
- Row selection for Investigate (user picks which rows to spend money on)
- Conditional cross-checks (run CMR/FNS/CFR only as needed)
- View-before-run on every phase button (peek at prior results without re-running)
- Per-finding JSON state means adding new phases doesn't invalidate prior phases' work

The CLI's `analyze_csv` is a parallel implementation that lacks cross-checks, lacks the view-before-run ergonomics, and uses a less-flexible state model (in-memory list + single checkpoint file). It exists because it was the original entry point; it doesn't have a current-day reason to stay.

**Cleanup actions implied:**
1. Delete `analyze_csv` (L1396-1594), `save_checkpoint`/`load_checkpoint` (L358-375), and the `--resume` CLI flag.
2. Either delete `TraceLogger` (currently CLI-only) or wire it into the phased pipeline. Decision depends on whether traces have audit/debug value to anyone — see open question.
3. Drop the `if __name__ == "__main__"` CLI entirely or shrink it to a debug helper that calls the phased functions directly.

### Cross-check parameterization (NEW, F2)

Collapse the three cross-check functions into one. Sketch:

```python
SOURCE_CHECK_CONFIG = {
    "cmr": {"prompt": "qc_cmr_check", "fallback": "cmr_silent",
            "result_key": "_cmr_check", "sections_key": "cmr_sections",
            "program": None, "model_config_key": "cmr_check_model"},
    "fns": {...},
    "cfr": {..., "program": "SNAP"},
}

def run_source_check(source: str, analysis_dir, row_indices=None, config=None):
    cfg = SOURCE_CHECK_CONFIG[source]
    ...
```

### TraceLogger universalization (NEW, F1)

If TraceLogger is valuable for debugging/audit, the phased pipeline should use it too. If it's dev-time-only, it can move behind a `--trace` flag and not be created by default.

### Move cost tracking out of qc_analyzer (NEW, F9)

`MODEL_PRICING` + `CostTracker` are not QC-specific. A shared `tools/cost_tracker.py` would serve QC, comparator, synthesis, and any future API consumer. The QC version is small enough to be a copy that should converge with whatever shared module emerges.

### Cross-check query benchmark (NEW, F10)

Before refactoring cross-checks, run a small benchmark: do cross-checks find better evidence using `policy_issues`, the original `finding_narrative`, the judge's `gap_description`, or some combination? Cheap experiment, real impact.

### Spreadsheet / CSV output redesign (NEW 2026-05-06, mirrors comparator)

QC has two CSV outputs that grew accretively as features were added, not designed end-to-end:
- **`summary.csv`** (UI/phased path): 12 columns + optional cross-check columns, generated by `generate_summary_csv()`
- **`{stem}_analyzed{suffix}.csv`** (CLI path): original input row + 6 appended columns

This is the same "tacked columns onto the end" shape comparator has. **Stop and think about what a deliberately designed QC spreadsheet output looks like** — what columns, what schema, who reads it (the QC team? a finding's stakeholder?), do they need to merge with the source CSV or stand alone, do they need to round-trip into a system of record? Bigger than the audit; tracked in `../cross_app_findings.md` as **CA-7** alongside comparator's equivalent. **May warrant its own work item** rather than being absorbed into cleanup.

## UI findings (2026-05-05)

Files: `ui/templates/qc.html`, `ui/templates/partials/qc_*.html`, `ui/app.py:L58-71, L750-1124`.

The UI tab is the canonical entry point. Page has six action buttons mapped to one route each: Upload → `/qc/upload`, Extract → `/qc/extract`, Investigate → `/qc/investigate`, CMR → `/qc/cmr_check`, FNS → `/qc/fns_check`, CFR → `/qc/cfr_check`. Each POST route uses `asyncio.to_thread` to call the matching backend function and returns an HTMX partial (`qc_upload_preview`, `qc_triage_table`, or `qc_results_table`).

### F16 [MAJOR] Three near-identical cross-check routes (mirrors F2)

`/qc/cmr_check` (L998-1029), `/qc/fns_check` (L1032-1063), `/qc/cfr_check` (L1066-1096) are structurally identical:
- Same form params (name + rerun)
- Same view-before-run guard
- Same `await asyncio.to_thread(run_X_check, analysis_dir, None, config)`
- Same `qc_results_table.html` partial
- Difference: source name + which `phases` flag is checked

Should be one route: `/qc/source_check/{source}`.

### F17 Three separate buttons for what's usually a single user intent

The qc.html buttons present CMR, FNS, and CFR as three distinct actions. In practice, when a user wants "what do the authorities say about this gap," they want **all three** to compare. Forcing three button clicks (and three round trips) is UX churn. A "Run all cross-checks" action (or a single button that fans out) would serve the actual user need.

### F18 Two duplicated view paths

`GET /qc/view/{name}/{phase}` (L798-844) loads existing phase results. **But every POST route also has a view-before-run branch** (e.g., L920-928 in `/qc/extract`) that returns existing results when `rerun != "1"`. Two paths to "show me existing results." Either centralize on the GET (POST always runs) or drop the GET (POST does view-or-run). Currently doing both.

### F19 [RETRACTED] ~~Vestigial `/qc/load/{name}` endpoint~~

Initially logged as possibly vestigial. **Retracted 2026-05-06**: confirmed in use by `loadQcAnalysis(name)` in `ui/static/app.js:L692-727`, called when a user clicks an existing analysis from the sidebar. See F25 for the *real* finding about this endpoint.

### F20 Three overlapping ways to get analysis state

- `/qc/analyses` — HTML list of all analyses with phase status (used on page load)
- `/qc/load/{name}` — JSON detail for one analysis (apparently unused, see F19)
- `/qc/{phase}` POST in view-before-run mode — HTML for one phase

Three endpoints accreted over UI iterations without consolidation.

### F21 [under-design] No streaming progress for long phases

Investigate is the slow phase: ~minutes per row × N rows × Sonnet agentic. The user clicks the button, sees the spinner with placeholder text "Warming up..." (qc.html L60), and waits with no feedback until the whole phase finishes. SSE or WebSocket streaming per-row progress would be a real UX improvement. **Feature work, not cleanup** — log but don't conflate.

### F22 [under-design] No abort for running phases

Once started, a phase runs to completion. No cancel button. **Feature work.**

### F23 [under-design] Cost meter exists but isn't surfaced

`meta["cost"]` is tracked per phase (extractor + judge) and persisted in `meta.json`. None of the templates I read display it. **Feature work.**

### F24 [under-design] Generic spinner text

"Warming up..." regardless of which phase the user clicked. Showing "Extracting policy issues..." vs "Investigating row 3 of 12..." would be cheap and meaningful. **Feature work, partially blocked by F21.** Partially supplanted by F27 — the JS does cycle through phase-specific text, but it's scripted theater, not real state.

## Config and JS findings (2026-05-06)

### F25 Two-call pattern for loading an analysis

`loadQcAnalysis(name)` in `app.js:L692-727` makes two sequential requests:
1. `GET /qc/load/{name}` → JSON with `latest_phase` (e.g., `"cfr_checked"`)
2. JS maps phase-name to URL-name via hardcoded table → `GET /qc/view/{name}/{phase}` → HTML

Two round trips and a JS translation table for one user action. One HTML endpoint that returns the right partial directly would replace both calls.

### F26 Phase-name convention drift

Backend stores `phases` as `cfr_checked / fns_checked / cmr_checked / investigated / extracted / uploaded`. URLs and UI use `cfr_check / fns_check / cmr_check / investigate / extract / upload`. JS translates between them (`app.js:L702-716`). Same six states, two naming conventions, translation table to bridge.

Pick one convention. Recommend the URL form (verbs/short) since it matches the routes; rename the metadata phase keys.

### F27 Progress text is scripted theater

`qcShowProgress(steps)` (`app.js:L530-561`) rotates through a hardcoded list every 4 seconds. **None of it is connected to actual backend state.** Examples from `INVESTIGATE_STEPS`:
- "Initializing OLG search client..."
- "Running seed searches..."
- "Judge is reading OLG results..."
- "Still searching. Policy is complicated."
- "One more row to go (maybe)..."

For real Investigate runs (10+ minutes for 30 rows of Sonnet agentic search), the timer cycles through the list and then stays on the last message indefinitely. The user thinks they're seeing progress; they're seeing a script. This:
- Papers over F21 (no real streaming) so the absence isn't visible to users
- Is actively misleading once it stalls on the last message
- "Policy is complicated" / "(maybe)" are charming but read as broken when timing reality diverges

When F21 is addressed, this scripted text gets replaced with real per-row state. Until then, at least the messages should be honest about not knowing where in the run it is.

### F28 `qcRun` and `qcRerun` are near-duplicate

`app.js:L580-620` and `L622-690` are structurally identical (~30 lines each). The only differences in `qcRerun`:
- A `confirm()` dialog
- `formData.append('rerun', '1')`

Should be one function with a `rerun: bool` parameter that conditionally adds the confirm and the form field.

### F29 `sendToAuthor` race condition

`sendToAuthor()` (`app.js:L749-763`) navigates to `/author` then uses `setTimeout(500)` to populate the assignment-name and assignment-text fields. This is a race — the populate runs blind 500ms after navigation regardless of whether the page is ready. Will fail intermittently if the Author page is slow to render (cold ChromaDB init, etc.).

URL parameters (`/author?name=...&assignment=...`) or sessionStorage would be deterministic. Minor, but it's the kind of brittle thing that fails once a year and confuses everyone.

### F30 [CONFIG BUG → B2] `cfr_check_model` missing from `config.ini`

`config.ini`'s `[qc_analyzer]` section has `cmr_check_model` and `fns_check_model` but **not** `cfr_check_model`. The code reads it with a `fallback="claude-haiku-4-5-20251001"` (qc_analyzer.py:L1325-1326), so the omission is silent.

Pattern matches CFR being added later — config update got missed, fallback hid it. Either add the key for symmetry, or (better, see F31) collapse the three keys into one.

### F31 Three per-source model configs that always equal Haiku

`cmr_check_model = claude-haiku-4-5-20251001`, `fns_check_model = claude-haiku-4-5-20251001`, and (in code fallback) the same for CFR. Three separate keys all pointing to the same model. Premature flexibility — a single `cross_check_model` key, or even reusing `extractor_model` since cross-checks are the same shape (cheap Haiku classification), would have served. Symptom of building three cross-checks one at a time without stopping to factor.

## Open questions

- **`/qc/load/{name}` usage**: confirm via `ui/static/app.js` whether this is called anywhere or vestigial (F19).
- **End-user output**: who reads `summary.csv` vs the per-finding JSONs? `/qc/download/{name}` (L1110) calls `generate_summary_csv` — that's the user-facing download. The per-finding JSON download (`/qc/finding/{name}/{row_index}`, L1099) is a power-user / debug path. Probably fine as-is.
- **Cadence**: how often is QC analyzer run? Per-finding latency tolerance? Batch sizes? (Informs whether streaming progress F21 is worth prioritizing.)
- **Trace consumption**: is anyone reading the JSONL traces, or are they dev-time only? (Informs whether to delete `TraceLogger` or wire it into the phased path.)

## Decisions log

- **2026-05-05**: Phased pipeline is canonical, CLI is legacy. UI is the canonical entry point. (Rationale in "Pipeline unification" opportunity above.)
- **2026-05-05**: Streaming progress, abort, cost meter, dynamic spinner text are *feature work* and tracked here but explicitly out of scope for the cleanup arc. They get their own work item later.
- **2026-05-06**: Engine routing — QC's API-only architecture is treated as a **gap, not intentional design**. F4 ("Engine routing does not apply here") is downgraded: it's accurate that QC has no Claude Code path today, but the lack is accidental rather than deliberate. **Claude Code integration to be added as feature work**, partly to develop a reusable engine-routing pattern that other apps can mirror (synthesis especially — see `../synthesis_review/README.md`). Out of scope for the cleanup arc; tracked here as the follow-up.

## Bug log

- **B1**: `extract_json` `fallback_classification` parameter is dead for cross-check callers (F5). Behavior is correct due to `.get(default)` catching it, but the parameter is misleading. No user-visible impact today.
- **B2** (2026-05-06): `cfr_check_model` missing from `config.ini` `[qc_analyzer]` section (F30). Code falls back to a hardcoded Haiku string, so the omission is silent. No user-visible impact, but means the config doesn't accurately reflect what models are in use.
