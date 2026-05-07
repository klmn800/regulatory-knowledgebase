# Search (Ask tab) — Cleanup Notes

Working document. Updated across sessions. See `../README.md` for the cleanup charter and audit methodology.

**Audit status**: Steps 1 (module read-through), 2 (layer mapping), 3 (UI surface), 4 (JS surface), and 5 (config audit) complete. **Deep architectural findings F1-F24 + B1 added 2026-05-06.** Cross-app comparison pass still pending — see "To do for next session" at the bottom.

## Purpose

The "Search" / "Ask" app is the canonical interactive policy-question entry point. A user opens the FastAPI UI at `http://127.0.0.1:8001/`, types a question, picks sources + per-source program filters + standard/deep mode, and gets a synthesized markdown answer with citations. Past searches are persisted to SQLite and viewable in a History tab; results can be exported to .docx.

This is the **thinnest of the four apps** — most of the work is delegated to `tools/synthesis.py`. Search's responsibilities are:

1. **UI surface**: form rendering, partial fragments, source/program checkboxes, deep-mode toggle
2. **Source registry** (`ui/search.py`): single source-of-truth dict for which sources exist + per-source program metadata
3. **Pre-initialized RAG clients** (`init_clients()` at app startup) — UI startup eats the cost so per-request is fast
4. **History persistence** (`ui/history.py`): SQLite with schema migration; saves question + answer + evidence + cost on every `/ask`
5. **Export**: `/search/export/{id}` builds markdown from a history entry and renders it via `tools/docx_writer.generate_docx`
6. **Raw search** (`/search` POST): a separate endpoint that returns result cards without synthesis — labeled "kept for power users" in app.py L310

## File shape

The "search" app is spread across several files (it has no dedicated subfolder; it lives in `ui/`):

| File | Lines | Role |
|---|---|---|
| `ui/search.py` | 121 | Source registry (`SOURCES`, `PROGRAM_REGISTRY`), pre-initialized client cache (`_clients`), `do_search()` wrapper |
| `ui/history.py` | 152 | SQLite persistence (`searches` table), schema migration on startup, `save_search` / `get_recent` / `get_by_id` |
| `ui/app.py` (search routes only) | ~200 lines (L1-330 of larger ~2000-line file) | `/`, `/ask`, `/search`, `/history`, `/history/recent`, `/history/{id}`, `/search/export/{id}` |
| `ui/templates/index.html` | TBD | Search form page |
| `ui/templates/history.html` | TBD | History list page |
| `ui/templates/history_detail.html` | TBD | View one past search |
| `ui/templates/partials/answer.html` | TBD | HTMX response after `/ask` |
| `ui/templates/partials/result_card.html` | TBD | Per-result card for raw `/search` endpoint |
| `ui/templates/partials/history_list.html` | TBD | Sidebar recent-searches partial |
| `ui/templates/partials/tab_content.html` | TBD | Used by `/search` route — purpose to confirm during step 3 |
| `ui/static/app.js` (search section) | TBD | Form submission, deep-mode toggle, source/program checkboxes |

`ui/app.py` line counts for non-search-app routes (Author, QC, Convert) are not search's concern but they share the same module — worth confirming during step 3 that there are no shared helpers or accidental coupling between them.

## Layer mapping

| Function/route | RAG direct | Synthesis | Claude Code | Anthropic SDK direct |
|---|:---:|:---:|:---:|:---:|
| `GET /` (index) | — | — | — | — |
| **`POST /ask`** | — | ✓ **`run_synthesis`** (the canonical path) | — | — |
| `POST /search` (raw) | ✓ `do_search` → `search_with_client` | — | — | — |
| `GET /history*` | — | — | — | — |
| `GET /search/export/{id}` | — | — | — | — (uses `docx_writer.generate_docx`, no model call) |
| `do_search` (search.py) | ✓ thin wrapper around `search_with_client` | — | — | — |
| `save_search` / `get_*` (history.py) | — | — | — | — (SQLite only) |

**No hand-rolled Anthropic calls.** Search is the only app that uses `tools/synthesis.py` as its primary surface. Every other app (comparator, QC) has hand-rolled SDK calls.

This makes search **the canonical synthesis caller** — it's the use case synthesis was shaped around. The audit will mostly verify that:
- The UI exposes the synthesis surface area we want (deep, sources, programs, max_searches?)
- Nothing is hidden that should be exposed
- Nothing is exposed that's actually downstream-defaulted

## Initial observations from the dip (preliminary, to verify in deep-findings session)

These were noticed during steps 1-2 but not yet examined carefully. Logged so we don't lose them — verify and properly categorize during the deep-findings pass.

- **OBS-A** [outdated] `ui/search.py:L4` docstring says "Wraps core/query.py" but the import (L14) is from `rag.query`. Pre-restructure path drift, same shape as comparator F2 (`agents/report.py`) and the synthesis CLI docstring (synthesis.py:L7-11). Cross-app sweep candidate.
- **OBS-B** [interesting] `SOURCES` registry (search.py L19-40) has `has_program_filter` boolean per source. FNS = False (no program metadata in chunks). Templates and routes are supposed to iterate this, never hardcode. Verify during step 3 that no templates have hardcoded source lists. Connects to the deferred TODO `todo_per_source_program_filter.md` — the per-source program filter design is the active design.
- **OBS-C** [duplication, cross-app] `do_search()` exists in both `ui/search.py:L94-120` AND `tools/synthesis.py:L236-251` with the same name and similar shape. Different init strategies (search.py uses startup pre-init `_clients`; synthesis.py uses lazy `_search_clients` cache). Same function name, two homes. Cross-app candidate.
- **OBS-D** [interesting] `init_clients()` (search.py L88-91) eagerly initializes ChromaDB clients for all four sources at app startup. Synthesis lazy-loads on first call. Tradeoff visible (slow startup, fast first request vs fast startup, slow first request). Document the choice.
- **OBS-E** [under-design / suspect] `/ask` POST handler (app.py L127-168) calls `run_synthesis` with **fixed defaults only**: no `max_searches`, no `config_overrides`, no `prompt_name`. Synthesis's defaults take effect (max_searches=8, max_tokens=1500, prompt="synthesis"). **No UI surface to tune these.** Either intentional (UI is for non-power-users) or a missing feature. Worth confirming.
- **OBS-F** [under-design] `/search` raw endpoint comment (L310) says "kept for power users". Two questions: (1) Is it actually reachable from the UI, or hidden? (2) Is it still used? If hidden + unused, it's vestigial.
- **OBS-G** [interesting] `init_db()` (history.py L25-54) does inline schema migration: creates table if missing, then ALTERs to add `programs_by_source` if column missing. **Schema state isn't versioned.** Adding more columns later continues this pattern; eventually the db has columns from multiple eras. Pattern worth flagging.
- **OBS-H** [vestigial?] Two columns in the SQLite schema represent program-filter intent: legacy `program_filter` (preset string like "snap_only", L33) and new `programs_by_source` (JSON dict, L51). New rows write NULL to legacy (L84); reader (`_row_to_dict` L138-140) only reads new column. Legacy column is **dead for new reads** but historic data still uses it. Cleanup question: drop legacy column or leave it.
- **OBS-I** [duplication, cross-app] `SOURCE_LABELS` dict (app.py L208-213) used by `_build_export_markdown`. Synthesis.py also has `SOURCE_LABELS` (L116-121). Different shapes — synthesis's is shorter strings (`"OLG"`, `"CMR"`), app.py's is longer (`"Online Guide (OLG)"`). Three+ apps will have this dict eventually. Cross-app cleanup candidate.
- **OBS-J** [duplication] `_build_export_markdown` (app.py L216-278) has source-specific citation rendering for OLG/FNS/CMR/CFR — same dispatch pattern as `format_results_for_prompt` (synthesis L124-210) and comparator's four formatters, but for markdown export instead of prompt context. Yet another per-source dispatcher.
- **OBS-K** [under-design] History save (`/ask` L150-157) is **forced** — every successful synthesis is saved with no opt-out. Probably fine for the single-user-as-owner model; if multi-user emerges (e.g., shared deployment), this becomes a privacy concern.
- **OBS-L** [interesting] `app.py` imports search-app, qc-app, author-app, convert-app, and shared `tools/` modules at the top (L30-72). All four apps share one FastAPI process. No app-level isolation. Worth flagging as an architecture decision (intentional? worth keeping?). Also means circular-import or load-order problems would surface here.

## Architectural findings

OBS-A through OBS-L (preliminary observations from the dip) are preserved above for trail. The verified findings below carry numbered IDs and supersede the OBS markers; resolution column shows which OBS each finding came from.

### F1 [outdated] `ui/search.py` docstring references pre-restructure path

`ui/search.py:L4` says `"Wraps core/query.py with pre-initialized clients..."` but the actual import is `from rag.query import create_client, search_with_client` (L14). Same shape as comparator F2, comparator F1's docstring, synthesis L7-11, qc_analyzer F4. Cross-app sweep candidate (CA-5). [Resolves OBS-A.]

### F2 [vestigial, MAJOR] `/search` raw POST endpoint and `partials/tab_content.html` are unreachable

`app.py:L308-328` defines `POST /search` with comment "kept for power users" (L310). **Verified: zero references** in any template, any JS handler, or any other route. Searched for `hx-post=` / `fetch('/search'` / link to `/search` in `ui/templates/` and `ui/static/app.js` — only matches are `/search/export/{id}` (a different route) and the route definition itself.

`partials/tab_content.html` is only rendered by this dead endpoint, so it's dead too.

The "kept for power users" comment is aspirational. The endpoint and partial are vestigial. Cleanup options: (a) delete both and the `do_search` helper that backs them, (b) wire a UI affordance and use it, (c) document as an undocumented power-user URL and accept the discoverability gap. [Resolves OBS-F.]

### F3 [vestigial] `/history/recent` route and `partials/history_list.html` are unreachable

`app.py:L184-190` defines `GET /history/recent` returning `partials/history_list.html`. **Verified: zero references** — no `htmx.ajax('GET', '/history/recent', ...)`, no template includes `partials/history_list.html`. Compare to QC's `/qc/analyses` which IS wired via `hx-get="/qc/analyses"` in `qc.html:L47` and via `htmx.ajax('GET', '/qc/analyses', '#qc-analyses-list')` in `app.js:L611` etc. Search has no analogous sidebar live-update; the partial was scaffolded but never connected.

Cleanup options: (a) delete the route + partial, (b) wire a recent-searches sidebar in `index.html` (feature work).

### F4 [under-design] `/ask` exposes only a fraction of synthesis's surface area

`app.py:L141-147` calls `run_synthesis(question, sources, programs_by_source, deep)` with **no other arguments**. Synthesis defaults take effect for `max_searches`, `max_tokens`, `prompt_name`, `config_overrides`, `program`, `exclude_programs`, `results_per_search`. `index.html` form has only: question text, source checkboxes, per-source program checkboxes, deep-mode toggle.

**Cleanup question**: is the limited surface deliberate ("UI is for non-power-users, simple is better") or oversight? If deliberate, document. If oversight, decide which params to expose. [Resolves OBS-E.]

Note: the form's `Deep analysis` checkbox lives in `index.html:L34-37` as the **only** synthesis-tuning control; the rest of synthesis's behavior is invisible to the user.

### F5 [bug, B1] `history_detail.html` evidence rendering omits CFR

`history_detail.html:L46-52` renders evidence by source key with `if/elif` for `olg`, `fns`, `cmr` — **CFR is missing**. A history entry that included CFR results would render the CFR section's results with a result-context line that's blank (no source label, no section number).

The CFR pipeline integrated 2026-04-30 (per memory). The history detail template was apparently not updated when CFR was added. Compare to `answer.html:L34-42` which DOES handle CFR; same shape, written at the same time but only one was kept up to date.

**This is a real bug** — the user-facing failure mode is silent (no error, just missing data on screen). Logged as **B1**. Categorize as bug, not rollout-followup, because it produces wrong output for any user who runs a search that included CFR and then opens it from history.

### F6 [drift, MAJOR] Per-source rendering dispatcher exists in five places with diverged shapes

Same conceptual operation (render a result by source key with source-specific metadata) implemented five times:

| Location | Source keys handled | Metadata fields shown |
|---|---|---|
| `partials/result_card.html` (raw `/search`) | olg/fns/cmr/cfr | breadcrumb (olg), last_updated, handbook_pages, pdf_pages, chapter_title, subpart_title |
| `partials/answer.html` (synthesis evidence) | olg/fns/cmr/cfr | breadcrumb, parent_heading, chunk_n/total, page_title, section_heading |
| `templates/history_detail.html` (history evidence) | olg/fns/cmr **(no CFR — see F5)** | breadcrumb only (no parent_heading, no chunk_n/total) |
| `app.py:_build_export_markdown` (docx export, L216-278) | olg/fns/cmr/cfr | citation strings (`"FNS {sec}: {title}"`, `"7 CFR § {sec} {title}"`, etc.) |
| `tools/synthesis.py:format_results_for_prompt` (LLM context, L124-210) | olg/fns/cmr/cfr | full prose for LLM prompts |

Five dispatchers, four sets of metadata-field choices, three template files repeating the same `if source_key == "olg"` ladder. Adding a fifth source = touching five places, three of which are templates. CA-3 candidate; this is the search-side evidence that `format_results_for_prompt` should consolidate not just across apps but across templates too. [Resolves OBS-J, partly OBS-I.]

### F7 [drift, cross-app] Four near-identical "rotate progress text every N seconds" implementations

| Location | Lines | Interval | Purpose |
|---|---|---|---|
| `index.html:L75-122` (inline `<script>`) | 47 lines | 3000ms | Ask spinner |
| `app.js:authorShowProgress` | L50-72 (23 lines) | 4000ms | Author spinner |
| `app.js:qcShowProgress` | L530-561 (32 lines) | 4000ms | QC spinner |
| `app.js:convertShowProgress` | L772-789 (18 lines) | 3000ms | Convert spinner |

Same pattern (text array, interval, opacity transition, hide-on-done). Inconsistent timings (3s vs 4s). All four are **scripted theater** — they cycle through messages independent of backend state. Same shape as QC F27 (the QC pass already flagged this). Cross-app: should be one `showProgress(spinnerEl, steps, intervalMs)` utility.

The Ask spinner is uniquely embedded inline in `index.html` rather than in `app.js` — every other apps' progress code lives centrally. Inconsistent placement in addition to inconsistent implementation.

### F8 [under-design, MAJOR] No error handling on `/ask` route

`app.py:L141-168` (the `/ask` POST handler):

- L141-147: `await asyncio.to_thread(run_synthesis, ...)` — no try/except
- L150-157: `await asyncio.to_thread(save_search, ...)` — no try/except
- L159-168: `templates.TemplateResponse(...)` — no error path

If `run_synthesis` raises (RateLimitError, network error, ChromaDB error, anthropic API down), FastAPI returns a 500. HTMX swap target is `#answer-area` — depending on htmx config, swap-on-error may not fire and the user sees... nothing visible change beyond the spinner stopping. There's no graceful "synthesis failed; here's why" path.

Same gap for save_search: if SQLite raises (db locked, disk full, malformed JSON), the user's answer was computed but they see a 500 instead of the answer.

**Cross-app**: synthesis itself has retry on `RateLimitError` (synthesis.py:L412-448), so the most-common transient failure is already handled inside synthesis. Less-common failures (ChromaDB down, Anthropic outage on second retry, save_search disk-full) are unhandled. Reliability gap is smaller than QC's or comparator's, but still present. Feeds **CA-8** in cross-app findings.

### F9 [under-design] No try/except in `init_clients()` — startup failure wedges all four apps

`ui/search.py:L88-91`:

```python
def init_clients():
    for source_key in SOURCES:
        _clients[source_key] = create_client(source=source_key)
```

If any single source's ChromaDB collection is missing/corrupt, `create_client` raises and the FastAPI lifespan handler (`app.py:L78-82`) propagates the exception, killing app startup. **Because all four apps (search, author, qc, convert) share this one process, search's startup failure takes down the others too.**

Fail-fast is defensible; the asymmetry is what's worth flagging — a runtime error in QC or Author or Convert can't take search down (they have their own try/except patterns), but a search startup error takes everyone down. Tradeoff worth documenting. [Connects to OBS-L.]

### F10 [drift] Result-card metadata diverges between raw and synthesis paths

`result_card.html` (raw `/search`) shows: last_updated, handbook_pages, pdf_pages, chapter_title, subpart_title. `answer.html` (synthesis evidence) shows: breadcrumb, parent_heading, chunk_n/total, page_title, section_heading.

Same chunks backing both — different fields surfaced. Each is purpose-fit (raw search wants the "where is this in the source corpus" answer; synthesis wants the "show me Claude's reasoning context" answer), but the divergence is undocumented. Adding a metadata field requires deciding which view(s) get it.

### F11 [drift] Three different history-list shapes; only two visible

| View | File | Question shown | Cost shown | Time shown | Source list shown |
|---|---|---|---|---|---|
| Full history page table | `history.html:L11-35` | first 80 chars | yes | yes (duration) | yes (joined) |
| Sidebar partial (NOT WIRED, see F3) | `partials/history_list.html` | first 60 chars | no | yes (duration) | yes (joined) |
| Detail page header | `history_detail.html:L11-21` | full | yes | yes (duration + tokens + model) | yes (joined) |

Three views of the same SQLite rows with three different field-selection choices. Cleanup question after F3 is resolved: pick a single shape (with verbosity flag) or accept the per-context purpose-fit divergence.

### F12 [duplication, cross-app] `do_search` exists in both `ui/search.py` and `tools/synthesis.py`

- `ui/search.py:L94-120` — eager-init via module-level `_clients` populated at startup
- `tools/synthesis.py:L236-251` — lazy-init via module-level `_search_clients` cache, populated on first call

**Same name, same conceptual operation, two homes, different init strategies.** Logged as **CA-N candidate** (likely new CA-11). The eager pattern fits UI's interactive use case (cold-start cost paid once at app launch); the lazy pattern fits synthesis's CLI/batch use case (cold-start cost paid on first call). Both defensible, but having two functions with identical names is a footgun for any developer who imports the wrong one. [Resolves OBS-C.]

### F13 [duplication, cross-app] Three `SOURCE_LABELS` registries with different values

- `ui/search.py:SOURCES` (L19-40) — has `label` and `short_label` per source. Canonical home (the `SOURCES` registry itself).
- `app.py:SOURCE_LABELS` (L208-213) — flat dict, long-form labels (e.g., `"Online Guide (OLG)"`)
- `tools/synthesis.py:SOURCE_LABELS` (L116-121) — flat dict, short-form (e.g., `"OLG"`)

Three labels-per-source registries with three different value strings. Templates that use `SOURCES[key].label` get one form; export markdown uses a second form; synthesis prompts use a third. Cross-app candidate; existing **CA-3** absorbs this. [Resolves OBS-I.]

### F14 [duplication] Evidence-rendering Jinja partials are near-duplicate

`partials/answer.html:L31-83` (synthesis evidence section) and `history_detail.html:L40-56` (history evidence section) render the **same data structure** with mostly-overlapping markup. Both iterate `entry.evidence.items()` → per-source `<details>` block → result cards with score + context + text. Differences:

- answer.html shows full per-source metadata (parent_heading, chunk_n/total, urls); history_detail.html shows breadcrumb-only
- answer.html handles cfr; history_detail.html doesn't (F5)
- answer.html has external link footer for OLG; history_detail.html doesn't

Looks like copy-paste-then-edit. Could be one shared partial `partials/evidence_section.html` parameterized by `verbose: bool` (or by `is_history: bool` if the divergence is intentional). The CFR-omission bug (F5) wouldn't have happened if both rendered through one partial.

### F15 [legacy column] SQLite schema retains dead `program_filter` column

`history.py:L33` declares legacy `program_filter TEXT`. New rows write `NULL` (L84: `..., NULL, ...`). New rows write to `programs_by_source` (added via inline ALTER, L51). Reader at L138-140 only reads `programs_by_source`. **Legacy column is read-dead and write-dead for new rows; only historical rows have non-NULL values.**

Cleanup options: (a) drop the legacy column (loses access to historical filter intent), (b) keep for archival display (then reader should expose it for old rows), (c) status quo (column is silently useless).

The unanswered question is whether anyone actually reads pre-2026-05-01 history rows; if the answer is "no," the column can drop. [Resolves OBS-H.]

### F16 [pattern] Inline schema migration without versioning

`history.py:init_db()` (L25-54) does `CREATE TABLE IF NOT EXISTS` followed by `PRAGMA table_info(searches)` to detect missing columns and `ALTER TABLE` to add them. Pattern works for one-time additions but doesn't scale: adding more columns means more `if "X" not in existing_cols` blocks accumulating in `init_db`. Schema state is implicit (derived from "what columns happen to exist") rather than explicit (a migration log).

If more SQLite-backed features land (audit log, bookmarks, sessions), the pattern should be formalized into a migration sequence with version tracking. Cross-app: this is the precedent — if QC or comparator ever go DB-backed, they'll follow this pattern unless replaced. [Resolves OBS-G.]

### F17 [hardcoded] History row limits hardcoded in routes

`app.py:L178` — `await asyncio.to_thread(get_recent, 50)` for full history page.
`app.py:L187` — `await asyncio.to_thread(get_recent, 10)` for sidebar partial (currently dead, F3).

Two magic numbers that govern the user's view of history. Should be config-driven or named module constants. No pagination — once history exceeds 50 entries, older entries are hidden with no way to access them.

### F18 [hardcoded] Text truncation lengths scattered across templates

| Template | Line | Limit | Field |
|---|---|---|---|
| `result_card.html` | L62 | 500 | result text |
| `answer.html` | L84 | 400 | result text |
| `history_detail.html` | L54 | 400 | result text |
| `history.html` | L25 | 80 | question preview |
| `partials/history_list.html` | L5 | 60 | question preview |
| `app.py:_build_export_markdown` | (none) | full | exported result text |

Five truncation lengths across five files. Could be three named constants (RESULT_PREVIEW_CHARS, RESULT_PREVIEW_HISTORY_CHARS, QUESTION_PREVIEW_CHARS) or one `truncate(text, max)` Jinja filter. The export uses no truncation, which is correct for downloadable artifacts but inconsistent with the on-screen views' choices.

### F19 [intentional, document] History save is forced — no opt-out

`app.py:L150-157` calls `save_search(...)` unconditionally after every successful synthesis. **No incognito mode, no checkbox to skip, no setting to disable.**

Acceptable for the single-user-as-owner deployment model. Becomes a privacy concern if the deployment ever serves multiple users (search history per-user vs shared). Document as intentional deviation tied to single-user assumption. [Resolves OBS-K.]

### F20 [intentional, document] Eager client init at startup

`ui/search.py:init_clients()` (L88-91) called from FastAPI lifespan handler (`app.py:L77-82`). All four ChromaDB clients constructed before the server accepts requests. Tradeoff: slow startup (~2-5 seconds for all four), fast first response.

Synthesis's lazy pattern (`tools/synthesis.py:_search_clients` populated on first call) is the opposite tradeoff: fast startup, slow first response. Both defensible — UI's interactive use case favors fast first response; CLI/batch favors fast startup so a `--help` invocation doesn't wait for ChromaDB. Document as intentional deviation. [Resolves OBS-D.]

### F21 [intentional, document] Four apps share one FastAPI process

`app.py:L43-72` imports search-app, author-app, qc-app, convert-app, plus shared tools. Single uvicorn process, single threadpool, shared ChromaDB connection pool, shared SQLite connection. **No app isolation.**

Consequences:
- Startup failure in any app's deps wedges all four (F9 specifically).
- Memory consumption is the union of all apps' working sets; a memory leak in any app affects all.
- A long-running synthesis blocks the event loop unless it's correctly threadpool-isolated (it is — `asyncio.to_thread` in all the routes I saw).
- Deployment is one-process-per-host; horizontal scaling means scaling all four together.

Acceptable for current single-user single-machine deployment. Worth flagging as an architecture decision. [Resolves OBS-L.]

### F22 [navigation pattern] History list uses `window.location` not HTMX

`history.html:L23` — `<tr onclick="window.location='/history/{{ s.id }}'" class="history-row">`. Full-page navigation. Inconsistent with the rest of the app's HTMX-partial swap pattern, but defensible — the history detail IS a full page (not a sidebar partial), so a partial swap would be the wrong pattern. Documenting as intentional rather than drift.

### F23 [drift] CFR rollout follow-up — same shape as comparator F10/F11

CFR pipeline integrated 2026-04-30. The search audit found one CFR rollout follow-up:
- F5 / B1 — `history_detail.html` evidence rendering omits CFR

Other CFR-touched surfaces (answer.html, result_card.html, _build_export_markdown) DO handle CFR correctly. The history-detail miss is an isolated rollout gap, not a systemic drift. Not categorized as architectural drift; trivial template update.

### F24 [drift] Sources nav lists the apps, not the policy sources

`base.html:L18-24` nav: `Ask | Author | Convert | QC Analysis | History`. The word "Sources" doesn't appear anywhere as a top-level navigation concept. Source selection is per-app (each app's form has its own source checkboxes via `SOURCES.items()` iteration), and source registry is enforced through `SOURCES` (good), but there's no "browse the corpus" tab — sources only matter when you've already typed a question. Worth flagging as a deliberate navigational choice (synthesis-first model) rather than a finding; documenting prevents the question from being re-asked later.

## Synthesis-interaction findings

Search is the **canonical synthesis caller** — `/ask` calls `run_synthesis()` and renders the result. This section catalogs how the contract holds up: what synthesis offers, what search uses, what falls through the cracks.

### Synthesis's surface area

`run_synthesis()` (synthesis.py:L542-588) takes 9 parameters:

| Param | Default | Used by `/ask`? |
|---|---|:---:|
| `question` | required | ✓ |
| `sources` | `["olg"]` | ✓ |
| `programs_by_source` | `None` | ✓ |
| `program` (legacy) | `None` | — |
| `exclude_programs` (legacy) | `None` | — |
| `deep` | `False` | ✓ |
| `max_searches` | `None` (uses config) | — |
| `prompt_name` | `"synthesis"` | — |
| `config_overrides` | `None` | — |

**4 of 9 exposed.** Two of the unused (legacy `program`/`exclude_programs`) are correctly omitted because `programs_by_source` supersedes them. The other three (`max_searches`, `prompt_name`, `config_overrides`) are real omissions — see F4.

`SynthesisResult` (synthesis.py:L66-75) returns 8 fields:

| Field | Used by `/ask` answer.html? | Persisted by save_search? | Used by history_detail.html? |
|---|:---:|:---:|:---:|
| `answer` | ✓ markdown | ✓ | ✓ |
| `evidence` (dict source → list) | ✓ rendered | ✓ JSON-serialized | ✓ (CFR missing — F5) |
| `search_queries` | count only | **✗ NOT PERSISTED** | **✗ NOT VISIBLE** |
| `input_tokens` | ✓ combined | ✓ | ✓ separately |
| `output_tokens` | ✓ combined | ✓ | ✓ separately |
| `cost` | ✓ | ✓ | ✓ |
| `duration_seconds` | ✓ | ✓ | ✓ |
| `model` | tooltip only | ✓ | ✓ visible |

### NS1 [under-design, MAJOR] `search_queries` is a provenance leak — synthesis provides it, search throws it away

`SynthesisResult.search_queries` (synthesis.py:L70) is a list of `"{source}: {query}"` strings — every search Claude ran to answer the question. In **deep mode**, Claude can run up to `max_searches=8` additional iterative searches with different angles ("SNAP eligibility", "expedited benefits process", "income deduction calculation"...). The agentic loop builds this list as it goes (synthesis.py:L290, L368, L477).

What `/ask` does with it:
- `answer.html:L10` — shows the **count** only: `{{ result.search_queries|length }} searches`
- `save_search` (history.py:L80-98) — **does not persist `search_queries` at all**

So a user who sees "5 searches" in the answer card has zero way to inspect what Claude actually searched. After the page reloads, even the count is the only artifact — clicking the history entry shows nothing about the queries because they were never saved.

**This is information synthesis already returns.** No new computation needed. Adding a `search_queries TEXT` column to the `searches` table and a small `<details>` block in answer.html / history_detail.html would expose Claude's reasoning provenance.

**Severity rationale**: for deep mode specifically, this is the difference between an opaque answer and an explainable one. Especially valuable when an answer disagrees with what the user expects — they can see whether Claude failed to search the relevant angle.

### NS2 [drift, MAJOR] `do_search` signatures in `ui/search.py` and `tools/synthesis.py` are subtly mismatched

Same name, different argument order:

```python
# ui/search.py:L94-101
def do_search(query: str, source: str = DEFAULT_SOURCE, programs=..., program=..., exclude_programs=..., top_n: int = 5, threshold: float = 0.0)

# tools/synthesis.py:L236-251
def do_search(source: str, query: str, top_n: int = 5, programs=..., program=..., exclude_programs=...)
```

- `query` and `source` positional order is **reversed**
- search.py exposes `threshold`; synthesis.py hardcodes `threshold=0.0` internally
- Default `top_n=5` matches; default `source="olg"` exists in search but not synthesis (synthesis requires source explicitly)

Anyone consolidating these into one shared `do_search` has to pick a signature and break the other caller's positional callsites. Compounds F12 — it's not just two homes, it's two **subtly incompatible** signatures sharing a name. Latent footgun.

### NS3 [drift, MAJOR] Eager `init_clients()` in `ui/search.py` is dead for the canonical `/ask` path

`/ask` traces:
1. `app.py:L142` → `run_synthesis(...)` (synthesis.py)
2. `run_synthesis` → `run_standard` or `run_deep`
3. Both call `do_search(source, question, ...)` — **synthesis.py's do_search**, not ui/search.py's
4. synthesis.do_search → `get_search_clients(source)` (synthesis.py:L229)
5. `get_search_clients` consults **synthesis.py's `_search_clients` cache** (synthesis.py:L226), populating lazily

**The eager init in `ui/search.py` populates `ui/search.py:_clients` (search.py:L85), which is only consulted by `ui/search.py:do_search`, which is only called by the dead `/search` raw endpoint (F2).**

Consequence: the "fast first response" benefit of eager init (F20) is **illusory for the canonical /ask path**. The first /ask call after server startup pays full ChromaDB connection cost — once per source as Claude searches it, lazily — because synthesis's cache is empty. Eager startup work doesn't help.

This is a significant misalignment. Two independent caches (one eager in UI, one lazy in synthesis), and the UI's is wired to the dead path. Resolutions:
1. **Fix the dead path.** Make UI's `do_search` actually used (i.e., wire synthesis to consume `ui/search.py:_clients` via dependency injection).
2. **Drop the dead init.** If F2 is killed, `init_clients()` and `_clients` go with it; synthesis's lazy pattern is the only one.
3. **Share the cache.** A single module-level cache in `rag/query.py` (or `tools/`) consumed by both. Cleanest, but requires both apps to plug into the same import.

(2) is the simplest if F2 is also killed. (1) makes the eager pattern actually deliver. (3) is the long-term right answer.

### NS4 [under-design] Custom prompt selection (`prompt_name`) is unused by search

`run_synthesis(prompt_name="synthesis")` defaults to `prompts/synthesis.md`. Author uses `prompt_name="author_research"` for its research phase — a different prompt with the same `SynthesisResult` shape.

Search's `/ask` accepts the default. There's no UI surface to pick an alternate prompt. **This is the only currently-shipped prompt variant**, but the affordance exists in synthesis and search doesn't use it. If "summary mode" / "compare-sources mode" / etc. were ever shipped as prompt variants, search would need to expose them.

Categorize as feature opportunity, not drift. But worth noting that synthesis's prompt-template flexibility is currently used by author and not by search, even though the architecture suggests search would be the primary consumer.

### NS5 [suspect] Deep-mode evidence accumulation has no dedup or ranking-merge

In `run_deep` (synthesis.py:L489-491):

```python
if source not in all_evidence:
    all_evidence[source] = []
all_evidence[source].extend(search_response["results"])
```

Each iterative search appends to the source's evidence list. If Claude does 3 OLG searches and `results_per_search=5`, `all_evidence["olg"]` has up to **15 results**, possibly with duplicates (the same chunk surfaced by overlapping queries scores differently each time but is the same content).

`answer.html` renders all of them — `{% for result in results_list %}` (L27). For a deep search that triggered Claude's full 8-search budget, the user sees up to **40+ result cards** in the evidence section. Possibly intentional (more provenance is better), possibly accidental (the dedup step doesn't exist).

Worth confirming: is the long evidence list deliberate, or should it be deduplicated by chunk_id and ranked-merged? Synthesis already returns `id` per result; dedup is straightforward.

### NS6 [drift, cross-app] Standard mode has no retry; deep mode does

`run_deep` (L401-448) catches `RateLimitError` (sleeps 60s, retries once) and `APIError` (returns error result). `run_standard` (L305-310) has **no try/except** at all. A rate-limit hit in standard mode propagates up to `/ask`, which has no try/except either (F8) → user sees 500.

Deep mode reliability is **strictly better** than standard mode, despite standard mode being the default and the more common path. Asymmetric retry policy within synthesis itself.

Feeds **CA-8** (cross-app retry/error policy divergence): synthesis's deep mode is the gold standard the doc cites, but synthesis's standard mode is bare-handed and matches comparator's zero-retry pattern.

### NS7 [drift, cross-app] Deep mode error path returns a "fake answer"

When `run_deep` catches `APIError` (synthesis.py:L437-448, L425-436), it returns:

```python
return SynthesisResult(
    answer=f"Synthesis failed due to API error: {e}",
    evidence=all_evidence,
    ...
)
```

**The error becomes the `answer` field as plain text.** Search's `answer.html` renders `result.answer | markdown | safe` (L4) without inspecting whether it's success or failure. So the user sees an answer card with error text inside it, styled identically to a real answer.

`save_search` then **persists this error result to history** (app.py:L150-157, no error check). The user can re-open it in history later and see the same fake answer.

Same shape as comparator F25 (degenerate L2 outcomes cached as findings). Synthesis-side analog: error states should be distinguishable in `SynthesisResult` (e.g., a `success: bool` field, or an `error: str | None` field), so callers can branch on success vs failure rather than rendering errors as answers.

### NS8 [drift, cross-app] Hardcoded `max_turns = 15` in synthesis matches comparator's hardcoded 15

`synthesis.py:L350` — `max_turns = 15`. Hardcoded.
`comparator.py:L729` — `max_turns = 15`. Hardcoded.
QC at `qc_analyzer.py:L648` — `max_turns = max_searches + 5`. Formula-based.

Three apps' agentic loops, three different turn-budget choices, two of which happen to land on the same magic number. Same finding as **CA-10** (different agentic-loop budget designs); the addition here is that **synthesis itself uses the same magic number as comparator**, suggesting one was modeled on the other or both converged on "15 feels right."

### NS9 [drift] `_search_clients` cache is module-level mutable state

`tools/synthesis.py:L226` — `_search_clients = {}`. Populated lazily by `get_search_clients()`. **Threadsafe?** ChromaDB clients held there. The FastAPI threadpool (`asyncio.to_thread` on `/ask`) means concurrent /ask requests share this dict. Dict mutation under contention is a race risk; ChromaDB clients themselves are typically read-thread-safe but the cache-fill `if source not in _search_clients` then `_search_clients[source] = create_client(...)` is a check-then-act race.

Low-impact in practice (single user, requests serial in practice), but worth flagging during the eventual full synthesis audit. Same shape as ui/search.py's `_clients` (F20).

### What this analysis tells us about A1/A2/B

This was the second task in the user's request: does this audit help understand whether synthesis is applicable to other apps?

**Answer: synthesis is the cleanest design among the three agentic-loop apps, and the drift is mostly in the *other apps* (comparator/QC duplicating what synthesis has cleaner versions of).**

Specifically:
- **`format_results_for_prompt`** — synthesis's unified dispatcher (L124-210) is richer than comparator's (F30 says comparator's is leaner; QC's is OLG-specific). **Synthesis is the canonical implementation.**
- **`MODEL_PRICING`** — synthesis has the correct rates (L36-40); comparator's rates are wrong (B1). **Synthesis is the canonical implementation.**
- **Retry on `RateLimitError`** — synthesis's deep-mode retry (L412-448) is the cleanest of the three; comparator has zero, QC is mixed. **Synthesis is the gold standard, except its own standard mode (NS6) is bare-handed.**
- **Agentic loop** — synthesis's deep mode is well-shaped: separate search budget + turn budget (better than comparator's CA-10), single-tool (simpler than comparator's two-tool L2), markdown output (simpler than QC's strict JSON).

**Implication for A1/A2/B:**
- **A1 bloats synthesis** — adding tools list + extractor + engine routing + seed-results-injection turns a 9-param function into a 13-param function with most params unused for the current /ask use case.
- **A2 (extract `agentic_search_loop`)** — synthesis's deep mode becomes one caller. The primitive must absorb all four flexibilities (multi-tool, extractor, engine, seed-message-history). Substantial primitive.
- **B (factor only duplicates)** — most realistic. The duplicates `format_results_for_prompt`, `MODEL_PRICING`, `SOURCE_LABELS`, `extract_json` extract cleanly to `tools/` modules. The agentic loops stay separate but each app converges on synthesis's design choices (search/turn budget split, retry policy, model pricing). **B "fully funded" gives ~80% of A2's value with a fraction of the change surface.**

The data point search adds: **synthesis was built right. The cross-app problem is QC and comparator drifting from synthesis, not synthesis being the wrong shape.** Cleanup direction: pull QC and comparator toward synthesis's idioms; promote synthesis's helpers to `tools/`; do NOT bend synthesis to absorb the other apps' specific shapes.

## Config findings

`config.ini` has **no `[search]` section** — verified by reading the file. Search-relevant sections: `[chromadb]` (collection names, persist_dir), `[synthesis]` (model, max_tokens, max_searches, results_per_search), `[embedding]` (query embedding model). All search-side `config.get*` calls happen indirectly through `tools/synthesis.py` and `rag/query.py`. Search itself reads no config keys directly.

### CF1 [hardcoded] `do_search` defaults in `ui/search.py:L100-101`

`top_n: int = 5, threshold: float = 0.0` are function-level defaults, not config-driven. `top_n=5` happens to coincide with `[synthesis] results_per_search = 5`, but they're set in two places. `threshold=0.0` differs from search-engine norms (synthesis uses configured threshold elsewhere). Should align: either both code-default OR both config-driven; pick one.

### CF2 [hardcoded] History row limits in routes

See F17 above. `get_recent(50)` and `get_recent(10)` are not config-tunable.

### CF3 [hardcoded] Text truncation lengths in templates

See F18 above. Five different truncation values scattered across templates.

### CF4 [hardcoded] Default-checked source = "olg"

`ui/search.py:L42` — `DEFAULT_SOURCE = "olg"`. Module constant, not config. Acceptable since it matches the policy hierarchy (OLG → CMR → FNS / CFR per project intent), but worth flagging — if the system ever needs to default to CMR for a different deployment, it's a code change.

### CF5 [no-finding] `[chromadb]` and `[synthesis]` reads via shared modules are correct

Spot-checked `config.get*` calls in routes: search code never reads `[chromadb]` or `[synthesis]` directly. All reads happen inside `rag/query.py:create_client` and `tools/synthesis.py`. Search delegates correctly through those modules. Good — no drift.

## Opportunities

### Vestigial endpoints (F2, F3)

Two endpoints + two partials with zero references in templates or JS:
- `POST /search` raw + `partials/tab_content.html` (F2)
- `GET /history/recent` + `partials/history_list.html` (F3)

Options: (a) delete all four as confirmed dead code, (b) wire them up to discoverable UI affordances (sidebar history, power-user search panel), (c) document as undocumented power-user URLs and accept the discoverability gap.

**Lean toward (a)** since these have been dead long enough that no one missed them; (b) is feature work that should earn its weight on its own merits, not be retrofitted to dead infrastructure.

### Per-source dispatcher consolidation (F6, F7, F13, F14)

Five places dispatch on source key with diverged shapes (F6). Three label registries with different values (F13). Four scripted-progress implementations (F7). Two near-duplicate evidence-rendering Jinja partials (F14).

Cross-app candidates — feed **CA-3** (formatters) and add a new **CA-N** for progress-text utility. Search alone can't pick these without alignment with synthesis and the cleanup of the comparator/QC formatters; this is one of the things the cross-app comparison pass needs to land on.

### Source registry leverage (verified)

`SOURCES` and `PROGRAM_REGISTRY` (search.py:L19-76) are the canonical home. `index.html:L22-31` iterates `SOURCES.items()` for source checkboxes; L43-58 iterates `SOURCES.items() if src.has_program_filter` for program groups. **Templates honor the registry pattern for form rendering.**

But: result-rendering templates (`result_card.html`, `answer.html`, `history_detail.html`) hardcode `if source_key == "olg"` ladders instead of iterating registry-driven dispatch tables. Inconsistent. Adding a fifth source today touches `SOURCES` once for forms but five places for rendering. [Resolves OBS-B.]

### Error-handling hardening (F8, F9)

- `/ask` route: add try/except around `run_synthesis` and `save_search`; return a partial that shows an error message in `#answer-area` instead of a 500.
- `init_clients()`: decide whether startup should fail fast (current) or degrade gracefully (e.g., disable individual sources, log, continue). The fail-fast wedges all four apps (F21); the degrade-gracefully model needs UI surfacing for "this source is unavailable."

Feeds **CA-8** (retry/error policy divergence in cross_app_findings.md).

### History schema policy (F15, F16)

Two open decisions:
1. Drop legacy `program_filter` column or keep for archival? (Hinges on whether anyone reads pre-2026-05-01 entries.)
2. Formalize migrations (alembic-style) or stick with inline ALTER pattern?

Trivial alone; matters more if more SQLite-backed features land.

### Synthesis param exposure on Ask (F4)

Decide which synthesis params the Ask tab should expose: max_searches, prompt_name, config_overrides, results_per_search. Default position should be "simple is better" — the form is intentionally minimal. But a "Show advanced settings" `<details>` block could expose tuning without cluttering the main flow. Feature work, not cleanup.

### Hardcoded values consolidation (F17, F18, CF1-CF4)

Two named constants would clean up most of this:
- `RESULT_PREVIEW_CHARS` (default 400) for result card text on screen
- `QUESTION_PREVIEW_CHARS` (default 80) for history table

Plus moving `top_n=5` from `do_search` defaults into `[chromadb]` or removing the explicit default and forcing all callers to specify it.

## Open questions

- **Multi-user concerns**: is the user-as-only-user model permanent (F19)? Affects history privacy, forced-save policy, and db schema.
- **Synthesis param exposure**: should max_searches / prompt_name / config_overrides / results_per_search be UI-tunable for the Ask tab (F4)? Or is "simple is better" the right call?
- **App isolation in `ui/app.py`**: is the four-app-shared-process model permanent (F21)? If so, search's startup-fail-takes-everyone-down (F9) is the price.
- **Schema versioning**: formalize SQLite migrations (alembic-style) or stick with inline ALTERs (F16)?
- **Pre-2026-05-01 history rows**: does anyone read them? If no, F15's legacy column drops; if yes, the reader needs to expose it for archival display.
- **Vestigial endpoints**: confirm F2 / F3 are safe to delete (no external bookmarks, no scripts that hit them, no docs that mention them).

## Decisions log

*(empty — populate as decisions are made)*

## Bug log

- **B1** (2026-05-06): `history_detail.html:L46-52` evidence rendering is missing CFR (F5). The `if source_key ==` ladder handles olg/fns/cmr but not cfr. A history entry that included CFR results renders the CFR section's results with a blank context line. Silent — no error, just incomplete display. Trivial fix (add `elif source_key == "cfr"`); cross-app implication is that F14 (duplicated evidence partials) made this miss possible — if `answer.html` and `history_detail.html` were the same partial, the CFR-handling addition to one would have fixed both.

## To do for next session

1. ~~**Step 3 — UI surface**~~ — **COMPLETE 2026-05-06**. Templates mapped, registry iteration verified for forms, hardcoded source ladders found in result-rendering templates, F2/F3 confirmed vestigial.
2. ~~**Step 4 — JS surface**~~ — **COMPLETE 2026-05-06**. `app.js` read end-to-end. Inline `<script>` in `index.html` mapped. F7 (four scripted-progress implementations) is the main surface-level finding.
3. ~~**Step 5 — Config audit**~~ — **COMPLETE 2026-05-06**. No `[search]` section needed (correctly so); CF1-CF5 catalog hardcoded values that could move to config.
4. ~~**Deep architectural findings**~~ — **COMPLETE 2026-05-06**. F1-F24 + B1 added. OBS-A through OBS-L all resolved/superseded.
5. **Cross-app comparison pass** (in `../cross_app_findings.md`): now the natural next move. With QC, comparator, and search audited, the CA-N findings need to be promoted from seeds to recommendations. Search-specific cross-app inputs:
   - **F12** (`do_search` exists in two homes) → new CA-11 candidate
   - **F7** (four scripted-progress implementations) → new CA-12 candidate (or merge with QC F27 awareness into a CA item about UX feedback patterns)
   - **F13** (`SOURCE_LABELS` × 3) → folds into existing **CA-3** (formatters / source dispatch)
   - **F6** (per-source rendering dispatcher × 5) → folds into **CA-3**
   - **F8/F9** (no error handling at /ask, no try in init_clients) → feeds existing **CA-8** (retry/error policy)
   - **F14** (evidence-rendering Jinja partial duplication) → folds into **CA-3** at the template layer
6. ~~**Synthesis observations from search**~~ — **COMPLETE 2026-05-06**. NS1-NS9 added to this doc above; `synthesis_review/README.md` now has a full "Search (audit complete)" section with the A1/A2/B refinement.
7. **Author audit** is the last app remaining. Should happen after the cross-app pass so any author-specific findings can be cross-referenced with CA-N items already formalized.

## Special notes for the search audit

Search is **structurally different** from QC and comparator: it's a thin UI wrapper around `tools/synthesis.py`. The cleanup question for search isn't "what drift is here?" but **"is the UI surfacing the right things from synthesis, and is anything happening here that shouldn't be?"**

**Audit answer (2026-05-06)**:
- The UI is **under-surfacing** synthesis (F4 — 4 of 9 params exposed). Whether this is intentional or oversight is the open question.
- Things happening here that shouldn't: dead `/search` raw endpoint (F2), dead `/history/recent` (F3), CFR rendering missing in history detail (F5/B1), four progress-text rotators that should be one (F7), three source-label registries that should be one (F13), error handling that's missing entirely (F8/F9).
- Things happening here that should: source registry pattern is honored for forms (good), history schema migration runs at startup (works, but unversioned — F16), eager client init is a deliberate UX choice (F20).

The audit lens worked: most findings are about **what's hidden from the user** (under-design) or **what's drifted between near-duplicate paths** (drift), exactly as predicted by the dip.

If search reveals nuances that update the synthesis_review observations, drop them into `../synthesis_review/README.md` under a new "Search (audit complete)" section — see to-do item 6.
