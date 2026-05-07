# OLG Author — Cleanup Notes

Working document. Updated across sessions. See `../README.md` for the cleanup charter and audit methodology.

**Audit status**: Steps 1 (module read-through), 2 (layer mapping), 3 (UI surface), 4 (JS surface), 5 (config audit) complete. **Deep architectural findings F1-F26 + B1 added 2026-05-06.** Cross-app updates and synthesis_review section also added — see end of doc.

## Purpose

The Author app produces full OLG pages from a high-level assignment. Three independent phases:

1. **Research** — multi-source RAG synthesis. Calls `run_synthesis()` with `prompt_name="author_research"` and `deep=True`. Outputs `report.md` + `evidence.json` + `meta.json` + `prompt.md` to a versioned directory.
2. **Draft** — composes a prompt from the research package + style guide + assignment, then **spawns a visible Claude Code terminal** via a generated `.bat` file. The session UUID is pre-generated and saved so the user can resume the same session later. Output: `draft.md` written by Claude.
3. **Format** — deterministic markdown → `.docx` conversion using `tools/docx_writer.py` and the OLG template. No LLM.

Versioning is **per-phase, independent**. A draft v001 records which research version(s) it was based on (`meta.json:based_on`). A format v001 records which draft version it formatted. Users pick research versions to include when launching a draft.

This is **the clearest engine-routing example in the codebase**: API for structured research, Claude Code for agentic-with-revisions drafting, pure Python for deterministic formatting. Each phase uses the engine that fits.

## File shape

| File | Lines | Role |
|---|---|---|
| `programs/author/author.py` | 569 | All three phase functions + CLI |
| `programs/author/prompts/author_draft.md` | 42 | Draft-phase Claude Code instructions |
| `prompts/author_research.md` (shared) | 106 | Research-phase synthesis prompt |
| `programs/author/references/olg_style_guide.md` | TBD | Style guide injected into draft prompt |
| `programs/author/references/olg_toc.md` | TBD | OLG table of contents (referenced by draft prompt) |
| `programs/author/references/2026 OLG Template.docx` | binary | Word template for format phase |
| `programs/author/references/sample_pages/*.docx` | binary | 8 sample pages (reference only) |
| `programs/author/references/OLG Writer's Manual.docx` | binary | Reference doc |
| `ui/versioning.py` | 256 | Per-phase versioning helpers (used by Author + Search history) |
| `ui/app.py` (author routes) | ~370 lines (L332-L722) | All author HTTP routes |
| `ui/templates/author.html` | 88 | Author tab page |
| `ui/templates/partials/author_*.html` | TBD (8 partials) | Per-phase fragments |
| `ui/static/app.js` (author section) | ~480 lines (L29-L480) | All author JS |
| `tools/docx_writer.py` | TBD | Markdown → docx (called by format phase) |

`programs/author/author.py` banner-separated sections:

| Lines | Section |
|---|---|
| 36-61 | CONFIGURATION (load_config, load_text, get_default_research_prompt, get_default_draft_prompt) |
| 63-71 | OUTPUT DIRECTORY (get_output_dir) |
| 74-202 | PHASE 1: RESEARCH (run_research) |
| 205-353 | PHASE 2: DRAFT (compose_draft_prompt, launch_draft, launch_resume) |
| 384-428 | PHASE 3: FORMAT (run_format) |
| 431-565 | CLI (main) |

## Layer mapping

This is the data point that completes the four-app picture for the A1/A2/B decision.

| Function | RAG direct | Synthesis | Claude Code | Anthropic SDK direct | Pure Python |
|---|:---:|:---:|:---:|:---:|:---:|
| `run_research` (Phase 1) | — | ✓ **`run_synthesis` deep mode** | — | — | — |
| `compose_draft_prompt` (Phase 2 prep) | — | — | — | — | ✓ |
| `launch_draft` (Phase 2) | — | — | ✓ **(.bat + subprocess.Popen)** | — | — |
| `launch_resume` (Phase 2) | — | — | ✓ **(.bat + subprocess.Popen)** | — | — |
| `run_format` (Phase 3) | — | — | — | — | ✓ **(`docx_writer.generate_docx`)** |

**No hand-rolled Anthropic SDK calls.** Author uses synthesis (canonical), Claude Code (subprocess), and pure Python — never the SDK directly. **This is the canonical synthesis caller besides search.**

### Comparison to other apps

| App | Synthesis | Claude Code | Anthropic SDK |
|---|:---:|:---:|:---:|
| Search (Ask tab) | ✓ canonical /ask | — | — |
| Author | ✓ research phase | ✓ draft phase | — |
| QC | — | — (gap; F4) | ✓ all 6 stages |
| Comparator | — | ✓ L2 dominant | ✓ L0/L1/L2/L3 fallback |

**Author is the only app that uses both API (synthesis) and Claude Code as deliberate choices for different work.** This is the canonical engine-routing pattern.

### What this means for A1/A2/B

The cross-app pass already recommended **B (factor only duplicates)**. Author's layering reinforces it:

- Author's `run_research` is **the cleanest example of synthesis-as-canonical** — uses 4 of 9 synthesis params (`prompt_name`, `config_overrides`, `max_searches`, `deep`, plus the inputs `question`/`sources`). Search uses a different 4. Together search + author exercise 5 of 9 params; the remaining 4 (`program`, `exclude_programs`, `programs_by_source`, lone parameter usage) are either legacy (program/exclude_programs) or unused by author specifically (programs_by_source — author searches without filter).
- Author's draft phase **does not use `tools/claude_code_runner.py`** — it hand-rolls a `.bat` file and `subprocess.Popen`. Comparator L2 also uses Claude Code; the two implementations are independent. **Cross-app drift candidate.**
- Author's research output is **the canonical example of how to persist a `SynthesisResult`** — saves report.md + evidence.json (with search_queries!) + meta.json. Search's history.py drops `search_queries` (search NS1). **Author already does what search NS1 says search should do.**

## Initial observations from the dip (preliminary, to verify in deep-findings session)

These were noticed during steps 1-2 but not yet examined carefully. Logged so we don't lose them — verify and properly categorize during the deep-findings pass.

- **OBS-A** [duplication, cross-app] `load_config` (author.py:L40-43) is the same shape as comparator's, QC's, and synthesis's. Five+ apps now have their own `load_config` reading from the same `config.ini`. Cross-app candidate (variant of CA-3).
- **OBS-B** [interesting] Author has TWO prompt locations: `prompts/author_research.md` (project-shared) and `programs/author/prompts/author_draft.md` (app-local). Search uses project-shared `prompts/synthesis.md`; QC uses app-local `programs/qc/prompts/`; comparator uses app-local. **Author straddles both conventions.** Might be intentional (research is canonical synthesis, draft is app-specific) or accidental. Worth confirming.
- **OBS-C** [duplication, cross-app] `launch_draft` (author.py:L300-353) and `launch_resume` (author.py:L356-381) hand-roll `.bat` files and `subprocess.Popen` for Claude Code. **Comparator uses `tools/claude_code_runner.py` for the same operation** (per memory + comparator F8). Two independent Claude Code subprocess implementations. Cross-app candidate.
- **OBS-D** [interesting / under-design] Author's research uses **NO program filter**. `run_research` (L126-137) calls `run_synthesis` without `programs_by_source`, `program`, or `exclude_programs`. Searches across all programs. For SNAP-specific OLG content, this likely surfaces TAFDC/EAEDC noise. Possibly intentional (research wants breadth), possibly oversight. **No surface in the web UI to add filters either.** Cross-references the deferred TODO `todo_per_source_program_filter.md`.
- **OBS-E** [intentional, document] Author exposes synthesis params **more fully than search does**: `prompt_name="author_research"`, `config_overrides={model, max_tokens, results_per_search}`, `max_searches=12` (vs synthesis default 8). This is the closest thing to a power-user UI for synthesis — but it's hardcoded in `run_research`, not user-tunable. Document as intentional rather than search F4-style under-design.
- **OBS-F** [under-design] Author's research saves `search_queries` to `evidence.json` (L160). **This is exactly what search NS1 says should happen but doesn't.** Author got it right; search dropped the field on the floor. Cross-references search NS1; suggests the cleanup direction is "search adopts author's persistence pattern."
- **OBS-G** [bug-shaped, B candidate] `compose_draft_prompt` writes to `DATA_DIR / ".draft_prompt.md"` (L322) — a **shared scratch file** across all assignments. If two drafts launch concurrently (impossible in single-user CLI but possible in web UI threadpool), the second's write overwrites the first's prompt before Claude reads it. Single-user assumption baked in.
- **OBS-H** [duplication, intra-module] `launch_draft` and `launch_resume` (author.py:L300-381) both hand-roll a similar `.bat` file. Two near-identical implementations of "launch Claude Code in a new console." Could be one helper, parameterized by the command (`claude --session-id ...` vs `claude --resume ...`).
- **OBS-I** [drift] **CLI is missing capabilities the web UI has**:
  - CLI's `--research-only` runs research with **empty task_instructions** (L514: `run_research(assignment, "", research_dir, config)`) — no way to provide focus text from the CLI
  - CLI has no `--sources` flag — always uses all four sources
  - CLI's `--draft-only` always uses ALL research versions (L530) — no way to pick subset
  - CLI cannot run Phase 3 (Format) at all — `run_format` is only invoked from web UI
  - `--no-docx` flag (L457) is documented but **does nothing** since CLI never runs format anyway
  - L562 prints a "Run format after the draft is complete: python programs/author/author.py --name X --format-draft Y" instruction, but `--format-draft` is **not a registered argparse option**. Lying error message.
  
  Same shape as QC F1 (CLI-vs-UI capability divergence). Web UI is canonical; CLI is degraded.
- **OBS-J** [duplication] Phase 2 prompt has Author's Notes instructions in TWO places:
  - `compose_draft_prompt` (L266-275) appends 9 lines of inline Author's Notes instructions
  - `programs/author/prompts/author_draft.md` already says "if you notice that...the system is missing information...flag anything that would help"
  - Both end up in the prompt Claude sees. Redundant; possibly conflicting if one is updated and the other isn't.
- **OBS-K** [pattern] Per-phase versioning model — `research/001_*`, `drafts/001_*`, `formats/001_*` — is **author-specific** (`ui/versioning.py`). No other app uses it. Could be reusable (QC could version its phases the same way) but currently isn't. Worth flagging during cross-app review.
- **OBS-L** [windows-coupling] `launch_draft` uses `subprocess.CREATE_NEW_CONSOLE` (L352) and writes a `.bat` file (L331). **Windows-only.** Same constraint as comparator's Claude Code path. Per architecture principle, the API path must remain viable; Windows-only is the user's deployment, but cross-platform deployment would need this rewritten.
- **OBS-M** [intentional, document] Phase 2 (Draft) is **the only place in the codebase where a Claude Code session is launched as a visible terminal window for the user to interact with**. Comparator's L2 Claude Code is headless (subprocess captures output). Author's Draft is interactive (user can resume, ask Claude to revise, etc.). This earns the .bat-file approach — it's not just "run a subprocess," it's "open a visible window the user owns." Document as intentional deviation.
- **OBS-N** [duplication, cross-app] Author's `evidence.json` shape (L156-179) duplicates the evidence-rendering Python dispatch we already see in 5 places (CA-3). Author's persistence layer chose its own field selection (rank, score, text, metadata, id). Compare to search history's evidence_summary (history.py:L66-76) — same idea, slightly different field selection (no rank). Two independent evidence-persistence implementations. Cross-app: yet another per-source data shape.

## Architectural findings

OBS-A through OBS-N (preliminary observations from the dip) are preserved above for trail. The verified findings below carry numbered IDs and supersede the OBS markers; resolution column shows which OBS each finding came from.

### F1 [drift, MAJOR] Author hand-rolls Claude Code subprocess launch instead of using `tools/claude_code_runner.py`

`programs/author/author.py:L300-353` (`launch_draft`) and `L356-381` (`launch_resume`) write `.bat` files and call `subprocess.Popen` with `subprocess.CREATE_NEW_CONSOLE` directly.

`tools/claude_code_runner.py` already exists as the project's canonical Claude Code subprocess wrapper. It supports a `windowed=True` flag (claude_code_runner.py:L66-68) that opens "a visible console window (Windows). Session output streams to the window instead of being captured. **Useful for watching sessions in real time.**" — the exact use case author needs.

Comparator imports it (`programs/comparator/comparator.py:L44`: `from tools.claude_code_runner import run_claude_task`) for L2 investigations. Author does not import it at all (verified via grep).

**Two independent Claude Code subprocess implementations exist in the codebase**, with author bypassing the canonical wrapper. The drift is *one of the cleanest cross-app duplications* in the cleanup arc — the right module already exists and is in use elsewhere.

Differences worth noting:
- `claude_code_runner.run_claude_task` uses a **result file** mechanism (the prompt instructs the session to write its output to a path, the wrapper reads that file). Author needs `draft_file` written by Claude — this fits the pattern.
- `run_claude_task` accepts `windowed=True` for visible terminal — exactly what author launches today.
- `run_claude_task` does not currently support `--session-id` for resume, but adding it is mechanical (it already captures `session_id` in piped mode).

[Resolves OBS-C, OBS-H, OBS-L. Cross-app candidate — see CA-13 in `../cross_app_findings.md`.]

### F2 [under-design / MAJOR] Author's research uses NO program filter at any layer

Confirmed at five layers, all of which default to "all four sources, all programs":

| Layer | File:line | Hardcode |
|---|---|---|
| Author module default | `programs/author/author.py:L99` | `sources = ["olg", "cmr", "fns", "cfr"]` |
| Route default | `ui/app.py:L437` | `sources: str = Form("olg,cmr,fns,cfr")` |
| Route fallback | `ui/app.py:L455` | `source_list = ["olg", "cmr", "fns", "cfr"]` |
| Detail-view fallback | `partials/author_research_detail.html:L21` | `view.meta.get('sources', ['olg','cmr','fns','cfr'])` |
| Editor UI | `partials/author_prompt_editor.html:L7-10` | four `<input type="checkbox" checked>` |

**No program-filter UI exists for author.** `run_research` (author.py:L126-137) calls `run_synthesis` without `programs_by_source`, `program`, or `exclude_programs`. The Ask tab exposes per-source program checkboxes (search F-finding context); author does not.

For SNAP-specific assignments (the most common case), this surfaces TAFDC/EAEDC/EA results as noise. The author-draft prompt (`programs/author/prompts/author_draft.md:L21-22`) actually instructs Claude *during* drafting to use `--exclude-programs "TAFDC,EAEDC"` — but the **research phase** has no such filter.

`templates.env.globals["SOURCES"]` is registered at `app.py:L90`, so author templates *could* iterate the registry. They don't. Adding a fifth source today touches four files (author.py, app.py, two partials).

[Resolves OBS-D. Cross-references the deferred TODO `todo_per_source_program_filter.md`.]

### F3 [drift, MAJOR] CLI lags web UI badly

The CLI (`author.py:L435-565`) cannot do what the web UI does:

| Capability | Web UI | CLI |
|---|---|---|
| Choose source subset | ✓ form checkboxes | ✗ always all four |
| Provide task instructions / focus text | ✓ research prompt textarea | ✗ `--research-only` runs with `task_instructions=""` (L514) |
| Pick subset of research versions for draft | ✓ checkboxes in prompt editor | ✗ always uses ALL versions (L530) |
| Run Phase 3 (Format) | ✓ button | ✗ unsupported entirely |
| Resume specific draft session | ✓ per-version Resume button | ✗ resumes the most recent session w/ a session_id (L476-480) |

Specific bugs in the CLI surface:

- **`--no-docx` flag is documented but does nothing** (L457). The CLI never calls `run_format` regardless of this flag, so the flag is a no-op.
- **`--format-draft` is referenced in a print message at L562 but is not registered as an argparse option** (L439-467). A user following the printed instruction `python programs/author/author.py --name {x} --format-draft {y}` gets argparse error. **Lying error message.**
- **Mixed-up control flow at L511-514**: `if not args.draft_only:` runs research with `task_instructions=""` — but `--research-only` doesn't go through a separate path. So `--research-only` produces a research version with empty focus text and no way to populate it from the CLI.

Same shape as **QC F1** (CLI-vs-UI capability divergence) and **comparator F-findings** about CLI gaps. Web UI is canonical; CLI is degraded. Cleanup question is whether the CLI is a maintained interface or a debug helper. [Resolves OBS-I.]

### F4 [under-design, MAJOR] No error handling on any author route

Verified for every author route in `app.py:L332-L722`:

| Route | Backend call | try/except? |
|---|---|---|
| `POST /author/{name}/research/run` (L431-477) | `await asyncio.to_thread(author_run_research, ...)` (L465-468) | ✗ |
| `POST /author/{name}/drafts/run` (L518-599) | `compose_draft_prompt(...)` (L564-570), `launch_draft(...)` (L573-581) | ✗ |
| `POST /author/{name}/drafts/{num}/resume` (L602-620) | `launch_resume(...)` (L610) | ✗ |
| `POST /author/{name}/formats/run` (L651-700) | `await asyncio.to_thread(author_run_format, ...)` (L674-676) | partial — checks `docx_path and docx_path.exists()` after the call but doesn't catch exceptions |

Author module itself has **one** try/except in 569 lines:

- `run_format` (author.py:L411-413) catches `ImportError` if `docx_writer` is missing.

Everything else (synthesis call in `run_research`, file writes in `compose_draft_prompt`, subprocess launches in `launch_draft`/`launch_resume`, template/draft path validation) is bare-handed.

Failure modes that produce a 500 with no graceful path:
- `RateLimitError` from synthesis on `/author/{name}/research/run` — same shape as search F8/NS6
- `subprocess.Popen` raising `FileNotFoundError` if `cmd` is unavailable (non-Windows) on `/drafts/run` — would be a Linux deployment hard-stop
- `Document(template_path)` raising on a corrupt/missing template (verified template-exists check at L421-423 returns None, but that's not the same as catching `Document()` raise)
- File writes in version directories raising `OSError` (disk full, permission)
- `time.strftime()` failures (basically impossible but illustrates the nakedness)

Feeds **CA-8** (retry/error policy divergence). Author adds **four bare-handed routes** to the catalog. Same shape as search F8 (`/ask`), QC's bare cross-checks, comparator F24's zero retries.

### F5 [drift] Three different list partials with the same shape

Same shape, three partials: `author_research_list.html` (29 lines), `author_drafts_list.html` (24 lines), `author_formats_list.html` (34 lines).

Common structure (verified in all three):
- `<div class="version-list-header">` with phase title + "New X" button
- `{% if versions %}` ladder
- `<div class="version-entries">` iterating `versions | reverse`
- Per-entry: `version-num`, `version-ts`, optional badge, optional preview, optional meta

Per-phase variation:
- research: prompt_preview + meta (sources/duration/searches/cost)
- drafts: draft/pending badge + based_on
- formats: docx badge + based_on (string, not list)

Adding a fourth phase = a fourth near-duplicate partial. Could be one shared `partials/version_entries.html` parameterized by phase + entry-renderer macro. F5/F6 in search audit demonstrated the cost of partial duplication (CFR rendering miss in history_detail.html). Same shape.

### F6 [drift] Three different detail partials with the same shape

`author_research_detail.html` (51 lines), `author_draft_detail.html` (56 lines), `author_format_detail.html` (35 lines).

Common structure:
- `<div class="author-result-container">` wrapper
- `<div class="author-version-bar">` with version-nav (prev/next/index)
- Optional `<div class="version-actions">` with phase-specific buttons
- `<div class="answer-card">` with phase-specific body

Per-phase variation:
- research: "Run Again" button with `data-sources` attribute, prompt details, report markdown, meta line
- drafts: "Resume" button (conditional), based_on, prompt preview, draft markdown, session_id
- formats: based_on, docx download link

Same partial-duplication smell as F5. Same fix shape: shared `partials/version_detail.html` with phase-specific block extension.

### F7 [duplication, intra-module] `launch_draft` and `launch_resume` write near-identical .bat files

`programs/author/author.py:L331-347` (launch_draft) and `L364-375` (launch_resume) both:

1. Write a `.bat` file with header `@echo off`, `cd /d {PROJECT_ROOT}`, `title ...`
2. Echo a status line
3. Call `claude` with phase-specific args:
   - `claude --session-id {session_id} "{initial_msg}"` (launch_draft)
   - `claude --resume {session_id}` (launch_resume)
4. Echo a footer
5. `pause`
6. `subprocess.Popen(["cmd", "/c", str(bat_file)], cwd=..., creationflags=CREATE_NEW_CONSOLE)`

Two near-identical implementations, differing only in the claude command line. Could be one helper `_launch_claude_in_terminal(name, claude_command, banner_lines)`. **Inside CA-13 / OBS-C** (extract to `tools/claude_code_runner.py`) — but separately fixable inside the module if the cross-app extraction is deferred. [Resolves OBS-H.]

### F8 [bug-shaped, B1] Shared scratch files in `DATA_DIR` are race-prone

`programs/author/author.py` writes three shared scratch files at module-level paths:

| File | Line | Written by |
|---|---|---|
| `DATA_DIR / ".draft_prompt.md"` | L322-323 | `launch_draft` (every draft launch) |
| `DATA_DIR / ".run_draft.bat"` | L331-347 | `launch_draft` |
| `DATA_DIR / ".run_resume.bat"` | L363-374 | `launch_resume` |

If two drafts launch concurrently from the web UI (FastAPI threadpool), the second's write overwrites the first's `.draft_prompt.md` before Claude has read it. Single-user assumption baked in.

`launch_draft` writes prompt to `.draft_prompt.md` then immediately spawns subprocess; subprocess `cmd /c .run_draft.bat` runs `claude --session-id ... "{initial_msg}"` where `initial_msg` references `.draft_prompt.md` by absolute path. If the second user's draft run interleaves between the first's prompt write and the first Claude session starting, both Claude sessions will see the second's prompt.

Single-user single-machine deployment makes this practically impossible (the user clicks one button and waits for the terminal to open). But it's a fragile mechanism. **Logged as B1** because the user-facing failure mode is silent (the wrong prompt would be sent without any warning).

Compare to `claude_code_runner.run_claude_task` (claude_code_runner.py:L42-51) which takes a `result_file` path argument from the caller — explicit per-call paths, no shared scratch. The canonical pattern is what F1 says author should use. [Resolves OBS-G.]

### F9 [bug-shaped, B2] `next_version_dir` race risk under concurrent requests

`ui/versioning.py:L85-99`:

```python
def next_version_dir(output_dir: Path, phase: str) -> Path:
    root = _phase_root(output_dir, phase)
    root.mkdir(parents=True, exist_ok=True)
    existing = list_versions(output_dir, phase)
    if existing:
        next_num = _parse_version_num(existing[-1].name) + 1
    else:
        next_num = 1
    timestamp = time.strftime("%Y%m%d-%H%M")
    version_dir = root / f"{next_num:03d}_{timestamp}"
    version_dir.mkdir(parents=True, exist_ok=True)
    return version_dir
```

Two concurrent calls can read the same `existing` list, compute the same `next_num`, and the second `mkdir` succeeds because timestamps differ down to the minute (so `001_20260506-1430` and `001_20260506-1430` collide if same minute, but `001_20260506-1430` and `001_20260506-1431` are both created with `next_num=1` if they happen at the boundary). The directory name uniqueness depends on timestamp differing between concurrent calls.

Also: the `existing[-1]` selection assumes `list_versions` is sorted. It is (versioning.py:L71-74), so OK.

Single-user assumption again. **Logged as B2** alongside B1. Same fix as F8 — if author moves to `tools/claude_code_runner.py`-style explicit paths, version-dir creation is naturally serial under threadpool because each request creates exactly one. But the race window exists. Compare to QC's stage-keyed JSON writes — different shape but same single-user assumption.

### F10 [drift] Phase-dispatcher logic in `versioning.py` is two `if phase ==` ladders

`ui/versioning.py` has two functions with `if phase == "research" / "drafts" / "formats"` ladders:

- `load_version_list` (L158-198) — 3-arm ladder (lines 180-194)
- `_load_version_data` (L201-255) — 3-arm ladder (lines 220-253)

Adding a fourth phase touches both functions. Could be class-per-phase (`ResearchPhase`, `DraftsPhase`, `FormatsPhase`) with `summary()` and `detail()` methods, or registry-driven dispatch (`PHASE_LOADERS = {"research": _load_research, ...}`). Either pattern would localize per-phase variation.

Not a high-priority cleanup — three phases exist and a fourth is unlikely. But same shape as the **per-source dispatcher problem** (CA-3). Mention only; no action recommended.

### F11 [drift, cross-app] HTML-parsing pattern in JS appears in three places

`ui/static/app.js` parses author server-rendered HTML to extract data three times:

| Function | Lines | What it parses |
|---|---|---|
| `authorPopulateDraftSelect` | L172-203 | drafts list HTML → `<option>` for `<select>` |
| `authorRunResearchAgain` | L275-305 | research detail HTML → focus text + sources |
| `authorShowDraftPrompt` | L325-371 | research list HTML → research-version checkboxes |

All three:
1. Fetch the server-rendered partial HTML
2. Insert it into a `document.createElement('div')`
3. `querySelectorAll('.version-entry')` (or similar)
4. Read `.textContent` of inner elements (`.version-num`, `.version-ts`, `[data-sources]`, `.author-input-text`)
5. `parseInt(numText.replace('v', ''), 10)` to extract numeric version

**Brittle.** Changing class names in `partials/author_research_list.html` breaks `authorPopulateDraftSelect`. Changing the `data-sources` attribute name in `author_research_detail.html` breaks `authorRunResearchAgain`. The implicit contract is: "HTML rendered by template X must continue to expose className Y in element Z."

Cleaner: separate `/data` endpoints that return JSON. E.g., `GET /author/{name}/drafts.json` returns `[{num, ts, has_draft}, ...]` and JS consumes it directly.

Search audit didn't find this pattern — search's `init_clients` and source registry are server-side. Author's UI is unique in re-parsing rendered HTML to drive interaction. Logged as cross-app candidate **CA-N** because if QC's filter UI (or a future feature) does the same, the pattern compounds.

### F12 [duplication, cross-app] Scripted-progress invocations × 4 within author alone

`ui/static/app.js` (the author section, L29-L480) has FOUR scripted-progress invocations:

| Function | Lines | Steps array |
|---|---|---|
| `authorRunResearch` | L254 | `RESEARCH_STEPS` (module-level, L33-45, 11 strings) |
| `authorRunDraft` | L388-392 | inline 3 strings |
| `authorResumeDraft` | L417-420 | inline 2 strings |
| `authorRunFormat` | L460-463 | inline 2 strings |

Plus `authorShowProgress` (L50-72) and `authorHideProgress` (L74-81) helpers. 4000ms interval hardcoded at L71.

Same as **search F7 / CA-12** (four scripted-progress implementations across apps). Author alone has four invocations within itself, which means the helper extraction (`showProgress(spinnerEl, steps, intervalMs)` from CA-12) would replace not just one but five callsites in this app. [Folds into CA-12.]

### F13 [drift] Author's Notes guidance duplicated in two places

`programs/author/prompts/author_draft.md:L31-41` instructs Claude to flag system improvement suggestions in Author's Notes:

> If, during your work, you notice that the style guide, reference materials, prompts, tools, or any other part of this system is missing information or conventions that would help you do a better job, say so in the Author's Notes...

`compose_draft_prompt` (author.py:L266-275) also appends instructions inline:

```python
parts.append(
    "Use the Write tool to create the file. ...\n"
    "At the end of the draft, include a `---` separator followed by "
    "a brief **Author's Notes** section with:\n"
    "- Any areas where you had to make judgment calls about structure or content\n"
    "- Any gaps you couldn't fill from available sources\n"
    "- Suggestions for the reviewer (content that should be verified, links to add, etc.)\n"
    "- Any system improvement suggestions (see the prompt above)\n"
)
```

Both end up in the prompt Claude sees. The list of bullets and the shared-prompt narrative aren't quite the same shape; if one is updated and the other isn't, Claude gets inconsistent guidance.

[Resolves OBS-J.] Cleanup: pick one home (the prompt, since it's editable; the inline append is harder to find) and remove the other.

### F14 [drift] `tools/docx_writer.py` markdown parser is its own implementation

`tools/docx_writer.py:L38-183` has a custom `_parse_markdown` function with regex-based block detection (heading, table, bullet, numbered, blockquote, note callout, paragraph). The route handler at `app.py:L93-95` registers `markdown.markdown(text, extensions=["tables", "fenced_code"])` as a Jinja filter — **uses a different markdown library** for the screen rendering of `report.md` and `draft.md`.

Result: the same draft markdown could parse differently to the docx vs the screen view. Specifically, `docx_writer._parse_markdown` does NOT support:
- Fenced code blocks (` ``` `) — the screen view does (via `fenced_code` extension)
- Footnotes
- Definition lists
- Horizontal rules other than `---`/`***`/`___`
- Inline HTML

The screen markdown library renders fenced code as `<pre><code>`; the docx writer would render the literal backticks as paragraph text. **Surprises possible** if Claude writes a fenced code block in a draft.

Listed as drift, not a bug, because the docx writer's parser is purpose-fit (no library dependency, full control over block-to-style mapping). But the divergence isn't documented. Cleanup options: (a) document the supported subset in `tools/docx_writer.py` docstring, (b) replace the custom parser with a library + Pandoc-style style mapping (substantial work, feature-shaped).

### F15 [outdated/dead] `claude_code_timeout` config key is dead

`config.ini:L59` declares `claude_code_timeout = 600` in `[author]`. Verified via grep across the entire codebase:

```
docs/author.md:112:| `claude_code_timeout` | Timeout for CLI draft sessions | `600` |
docs/apps_cleanup/author_cleanup/README.md:126,164: (this audit)
```

**Zero source-code references.** Author module never reads it. `launch_draft`/`launch_resume` use `subprocess.CREATE_NEW_CONSOLE` and `cmd /c` with a `pause` at the end of the `.bat` file (L345, L373); the parent process detaches from the subprocess, so a timeout in the parent has no effect on the terminal session.

Documented in `docs/author.md` as "Timeout for CLI draft sessions" — but not enforceable in the current architecture. Same shape as **comparator F18** (dead config). Cleanup: remove from config.ini and from docs/author.md, OR (if `tools/claude_code_runner.py` migration happens per F1) wire it through to `run_claude_task(timeout=...)`. The runner already has a `timeout` parameter (claude_code_runner.py:L45). [Resolves config-audit pending question.]

### F16 [drift] `load_config` shape duplicated across apps

`programs/author/author.py:L40-43` defines `load_config()` reading `CONFIG_FILE = PROJECT_ROOT / "config.ini"` with `configparser`. Same shape exists in:

- `programs/comparator/comparator.py` — own `load_config`
- `programs/qc/qc_analyzer.py` — own `load_config`
- `tools/synthesis.py` — own `load_config`
- `ui/app.py:L44-45` imports author's via `from programs.author.author import load_config as load_author_config` and uses it for author routes (L467, L561, L673, L1189)
- Also imports QC's via `from programs.qc.qc_analyzer import load_config as load_qc_config` (L58-59)

**Five+ apps each have their own one-line `load_config` reading from the same `config.ini`.** A single shared `tools/config.py:load_config()` would centralize. The function is one line, so the extraction is low-value individually — but the pattern signals each app has its own initialization concerns instead of converging.

Cleanup question: extract or document as accepted duplication. Lean toward documenting (one-line functions don't justify a shared module). [Resolves OBS-A. Folds into CA-15 in cross-app findings.]

### F17 [drift, cross-app] Prompt-loading conventions diverge

Author uses TWO prompt locations:

- `prompts/author_research.md` (project-shared) — loaded by synthesis via `prompt_name="author_research"` (author.py:L131)
- `programs/author/prompts/author_draft.md` (app-local) — loaded by author's `get_default_draft_prompt` (author.py:L58-60)

Other apps:
- Search: project-shared `prompts/synthesis.md` (synthesis default)
- QC: app-local `programs/qc/prompts/`
- Comparator: app-local `programs/comparator/prompts/`

**Author straddles both conventions.** Defensible as intentional: research is canonical synthesis (project-shared), draft is app-specific (app-local). Other apps that use synthesis (search) only have the project-shared prompt. [Resolves OBS-B.]

Cleanup: document the convention. Lean toward keeping the split — it accurately reflects which prompts are app-specific (draft prompts are author-specific) vs which are reusable across callers. If a future app adds a synthesis call with a custom prompt, it should follow author's pattern (project-shared prompt loaded via `prompt_name`). Cross-app candidate **CA-N** for documenting the convention; not for changing it.

### F18 [under-design] Author exposes synthesis params more deeply than search but still hardcodes them

`run_research` (author.py:L101-106) reads four config keys:
- `research_model` (default `claude-sonnet-4-5-20250929`) — passed via `config_overrides["model"]`
- `research_max_searches` (default `12`) — passed via `max_searches`
- `research_results_per_search` (default `8`) — passed via `config_overrides["results_per_search"]`
- `research_max_tokens` (default `4096`, but config.ini sets `8192` at L58) — passed via `config_overrides["max_tokens"]`

Plus `prompt_name="author_research"` and `deep=True` hardcoded.

Together: author exercises 5 of synthesis's 9 params (`prompt_name`, `config_overrides`, `max_searches`, `deep`, `sources`). The remaining 4 — `program`, `exclude_programs`, `programs_by_source`, lone `question` — are either legacy (program/exclude_programs) or unused by author specifically (programs_by_source per F2).

**This is the deepest synthesis caller in the codebase.** Search uses 4 of 9 (`question`, `sources`, `programs_by_source`, `deep`) and intentionally hides the rest behind synthesis defaults (search F4). Together search + author exercise 5 of 9 params — the full param surface synthesis offers minus the legacy program filter ones.

**Where this matters for the synthesis audit**: synthesis's `prompt_name`, `config_overrides`, and `max_searches` are *only used by author* (verified). If author goes away or shifts patterns, those synthesis params have zero callers. Synthesis's flexibility is being used; author is what justifies it.

Author's hardcoding choices (deep=True, prompt_name="author_research", config_overrides for model/max_tokens/results_per_search) are not user-tunable from the UI. This is not under-design relative to search — it's *intentionally not user-tunable* because the research phase's prompt and budgets are part of the system design, not the user's choice. **Document as intentional.** [Resolves OBS-E.]

### F19 [drift, cross-app] Author's `evidence.json` is the canonical SynthesisResult persistence pattern

`run_research` (author.py:L155-183) persists the full SynthesisResult via `evidence.json`:

```python
evidence_data = {
    "assignment": ...,
    "timestamp": ...,
    "model": result.model,
    "search_queries": result.search_queries,    # ← search NS1 dropped this
    "tokens": {"input": ..., "output": ...},
    "cost": ...,
    "duration_seconds": ...,
    "evidence": {source: [{rank, score, text, metadata, id} for r in results]}
}
```

**Compare to search's `save_search`** (`ui/history.py:L80-98`) which persists a subset and **drops `search_queries` entirely** (search NS1).

Author got it right; search dropped `search_queries` on the floor.

Author's evidence-entry shape (`rank`, `score`, `text`, `metadata`, `id`) is also richer than search history's `evidence_summary` (which omits `rank` per search F-finding analysis).

**Cross-app cleanup direction**: search adopts author's persistence pattern. Specifically, `save_search` should add a `search_queries` column and persist the full SynthesisResult.search_queries, matching what author already does in evidence.json. [Resolves OBS-F. Cross-app candidate **CA-14** in `../cross_app_findings.md`.]

### F20 [intentional, document] Three engines deliberately routed

This was the dip's headline observation. Verified.

| Phase | Engine | Why |
|---|---|---|
| Research | API (`tools/synthesis.py:run_synthesis`) | Structured output via SynthesisResult, integrates with existing RAG, cheap per call, no interactive component |
| Draft | Claude Code CLI (visible terminal subprocess) | Session resumability, agentic exploration during drafting, user can interject, $0 on subscription |
| Format | Pure Python (`tools/docx_writer.py`) | Deterministic markdown→docx conversion, no LLM needed, no cost, no failure modes from API |

**This is the canonical example of the engine-routing pattern.** Each phase uses the engine that fits. Document as intentional deviation from "everything goes through synthesis" or "everything goes through Claude Code." [Resolves OBS-M.]

The cleanup question this raises is actually about **other apps**: should comparator's L0/L1/L3 (Haiku-on-API for fast structured triage) also be considered "engine routing earning its keep"? Yes — same principle. Author + comparator both route per task fit; QC and synthesis are single-engine apps. [Cross-app data point for the architecture-principles work.]

### F21 [windows-coupling, document] Author is Windows-only at the OS level

`programs/author/author.py:L350` uses `subprocess.CREATE_NEW_CONSOLE` (Windows-only flag).
`L331-347, L364-374` write `.bat` files (Windows shell scripts).
`L350, L378` invoke `subprocess.Popen(["cmd", "/c", str(bat_file)], ...)` — `cmd` is Windows.

If a Linux deployment ever needs author, all three sites need rewrites: shell script (`.sh`), `subprocess.Popen([...]) ` without `CREATE_NEW_CONSOLE`, and `xterm`/`gnome-terminal`/`tmux new-window` for visible terminals.

`tools/claude_code_runner.py:L66-67` (the canonical wrapper author should use per F1) acknowledges Windows-only for `windowed=True` ("If True, open in a visible console window (Windows)") — so even the canonical pattern is Windows-only for the visible-terminal case.

**Per architecture principles**: API path must remain viable. Phase 1 (research) is API-only and works cross-platform. Phase 2 (draft) is Windows-coupled by design. Phase 3 (format) is pure Python, cross-platform. So 2/3 of author works on Linux today; only the visible-terminal Phase 2 is blocked. [Resolves OBS-L.]

### F22 [drift] Source-list rendering does not iterate `SOURCES` registry

`templates.env.globals["SOURCES"] = SOURCES` is registered at `ui/app.py:L90`. Search templates (per search audit) iterate `SOURCES.items()` for source checkboxes (good). Author templates **do not**:

- `partials/author_prompt_editor.html:L7-10` hardcodes four `<input>` elements with values `"olg"`, `"cmr"`, `"fns"`, `"cfr"`.
- `partials/author_research_detail.html:L21` hardcodes the fallback `['olg','cmr','fns','cfr']` for `data-sources`.

Adding a fifth source today requires touching both partials (and the four hardcoded backend lists per F2). The registry pattern is established, available, and not used here. Same shape as search F-finding context about template-side hardcoded source ladders.

[Folds into CA-3 / per-source dispatcher consolidation.]

### F23 [drift] Two label conventions for sources in author templates

Author templates display sources two ways:
- Checkbox label text: `OLG`, `CMR`, `FNS`, `CFR` (uppercase short, partials/author_prompt_editor.html:L7-10)
- Meta line in research_list: `view.meta.sources | join(', ') | upper` — produces `OLG, CMR, FNS, CFR` (partials/author_research_list.html:L18)
- Meta line in research_detail: same `| upper` filter (partials/author_research_detail.html:L43)

All three pick "uppercase short label." None reads from `SOURCES.items()` `label` or `short_label` per the registry. Adding a label change to `SOURCES` doesn't propagate to author. [Folds into search's F13 / CA-3 — three label-form registries with different values, plus the templates that hardcode their own.]

### F24 [drift] `partials/author_prompt_editor.html` does double-duty for two phases via `{% if %}` ladder

`partials/author_prompt_editor.html:L3-34` renders one of two completely different forms based on `phase`:

- `phase == "research"` (L3-19): source checkboxes + research focus textarea + Run/Cancel buttons
- `phase == "drafts"` (L21-34): draft instructions textarea + research version checkboxes + Launch/Cancel buttons

Two distinct UIs in one template via top-level `{% if %}`. Format phase has *no* prompt editor — its launching UI lives in `partials/author_formats_list.html:L6-14` (the `format-controls` block at top of the list partial).

Three phases, three different launching-UI placements:
- research → `author_prompt_editor.html` (research branch)
- drafts → `author_prompt_editor.html` (drafts branch)
- formats → `author_formats_list.html` (top of list partial)

Asymmetric. Format's launcher is in the list partial because it doesn't need a textarea (just a select). But the inconsistency means a developer adding a new phase has to choose which pattern to follow. Document, don't fix.

### F25 [intentional, document] Phase 2 is the only place a visible Claude Code terminal launches for user interaction

Per F20, three engines route across three phases. Phase 2 specifically uses **windowed Claude Code** so the user can:
- Watch the agent draft
- Resume the same session later (`launch_resume`)
- Interject to ask for revisions
- Use Claude's tool-use loop to do additional searches during drafting

Comparator's L2 Claude Code path uses `claude_code_runner.run_claude_task` in **headless** mode (subprocess captures output via result file). Author's draft is the *only* place in the codebase where a Claude Code session is launched as a visible terminal **the user owns**.

This earns the windowed-terminal pattern. `tools/claude_code_runner.py:L66-67` already supports `windowed=True` for this exact use case (per F1, author should adopt it). Document as intentional. [Resolves OBS-M.]

### F26 [under-design] No test coverage for any author phase

Verified via glob: no `test_author*.py`, no `tests/author/`, no test for `tools/docx_writer.py` either. Same gap as the rest of the codebase — but author's three-engine structure makes it harder to test (Phase 1 needs API mocking, Phase 2 needs subprocess mocking, Phase 3 needs docx round-trip checking).

Phase 3 (format) is the most testable — pure function `generate_docx(markdown, output, template)` returns a Path. A round-trip test (markdown → docx → re-extract → compare) is straightforward.

Logged for completeness. **Out of scope for cleanup** (testing is feature work). Document as known gap.

## UI / templates findings

Step 3 (UI surface) findings are F5, F6, F22, F23, F24 above. Summary:

- **F5/F6**: three list partials + three detail partials with same shape
- **F22/F23**: source-list rendering doesn't iterate `SOURCES` registry; label conventions diverge
- **F24**: prompt editor double-duties for research+drafts; format's launcher lives in the list partial

Total templates: 1 page (`author.html`) + 9 partials + ~370 lines of routes in `app.py:L332-L722`. The partial duplication is the headline UI finding.

The phase-tab pattern at `author.html:L31-36` is correct: tabs are static (no fetch on switch), phase panels reveal pre-loaded HTMX content. Switching phases doesn't reload — the version-list area was loaded by `authorLoadVersionLists` when the assignment was selected. [Resolves a half-formed worry about HTMX vs full-page nav.]

`templates.env.globals["SOURCES"]` is registered at app.py:L90 — author *could* iterate it, but doesn't (F22).

## JS findings

Step 4 (JS surface) findings are F11, F12 above. Summary:

- **F11**: HTML-parsing pattern × 3 — JS parses server-rendered partial HTML to extract version data
- **F12**: scripted-progress invocations × 4 within author alone (folds into search F7 / CA-12)

The JS section is `ui/static/app.js:L29-L480` (~480 lines). The `_currentAuthorName` module-level mutable state (L48) is touched in `authorSaveAssignment` (L113) and `loadAssignment` (L129). Every other author function falls back to `document.getElementById('author-name').value.trim()` if `_currentAuthorName` is empty. Defensible.

Tab switching (`authorSwitchTab` L84-92) is local-only — no fetch, no state save. Auto-switching on `loadAssignment` (L133-136) picks the most-advanced phase (formats > drafts > research). Reasonable UX; documented behavior.

**The HTML-parsing pattern (F11) is the single biggest JS-side concern** because three separate functions implement it slightly differently (different selectors, different extracted fields). A failure of one wouldn't necessarily trigger the others. Cleanup direction: introduce JSON data endpoints (`/author/{name}/drafts.json`) for JS-driven UIs.

## Config findings

Step 5 (config audit) findings are F15, F18 above. Summary:

- **F15**: `claude_code_timeout` is dead config (zero source references)
- **F18**: author's synthesis param exposure documented as intentional (5 of 9 params used)

`[author]` section keys vs author.py usage:

| Key | Default in code | config.ini value | Usage |
|---|---|---|---|
| `research_model` | `claude-sonnet-4-5-20250929` | `claude-sonnet-4-5-20250929` | author.py:L101 |
| `research_max_searches` | `12` | `12` | author.py:L103 |
| `research_results_per_search` | `8` | `8` | author.py:L104 |
| `research_max_tokens` | `4096` | `8192` | author.py:L106 — **config differs from code default** |
| `claude_code_timeout` | (none) | `600` | **DEAD** (F15) |
| `template_docx` | `programs/author/references/2026 OLG Template.docx` | same | author.py:L417 |
| `style_guide` | `programs/author/references/olg_style_guide.md` | same | author.py:L229 |

**Note on `research_max_tokens` divergence**: code default is 4096, config.ini sets 8192. The config wins (it's what production uses). Code default is what runs if config.ini is missing. Worth aligning code default to config value, or — better — making the config-ini key required with no fallback.

No drift found in template/style-guide path resolution: both keys resolve under `PROJECT_ROOT` correctly, and both code defaults match the config values.

### CF1 [hardcoded] `[author]` config has no error-handling section

No `claude_code_timeout` enforcement (F15), no retry-policy keys, no rate-limit-handling keys. Compare to QC's `max_judge_searches` and synthesis's `max_searches` — both have config-driven budgets with sensible defaults. Author's `research_max_searches` follows that pattern but no others. If author grows error-handling per CA-8, config keys would land here.

### CF2 [hardcoded] `MAX_TURNS`, `INTERVAL_MS` etc. for JS spinner are inline

JS-side hardcodes:
- `RESEARCH_STEPS` array (app.js:L33-45) — 11 strings
- `INTERVAL_MS = 4000` (app.js:L71) — implicit, hardcoded in `setInterval`
- Inline progress arrays at app.js:L388-392, L417-420, L460-463

Same shape as search F7. If CA-12 (scripted-progress helper) lands, these become inputs to `showProgress(spinner, steps, intervalMs)`.

## Bug log

- **B1** (2026-05-06): `author.py:L322-323` writes `.draft_prompt.md` to a shared scratch path. Concurrent draft launches under FastAPI threadpool would race, with the second's prompt overwriting the first's before Claude reads it. **Single-user assumption baked in.** Per F8. Trivial fix once F1 lands (`tools/claude_code_runner.py` takes explicit per-call paths). Cross-app implication: same shape as `next_version_dir` race (B2).

- **B2** (2026-05-06): `ui/versioning.py:L85-99` `next_version_dir` reads `existing[-1].name` then `+1` — race between concurrent calls. Two simultaneous requests can compute the same `next_num` and create directories at minute-boundary timestamps. Single-user assumption again. Per F9. Fix: file-lock the parent dir, or use `os.makedirs(..., exist_ok=False)` retry-on-collision.

## Opportunities

### Adopt `tools/claude_code_runner.py` (F1)

The right module already exists and is in use by comparator. Author hand-rolls .bat files and subprocess.Popen instead. Migrating `launch_draft` and `launch_resume` to call `run_claude_task(..., windowed=True, session_id=...)` would:

- Eliminate F7 (intra-module .bat duplication)
- Eliminate B1 (shared scratch file race) by using explicit per-call `result_file`
- Activate F15's dead `claude_code_timeout` config key by passing `timeout=` to the runner
- Centralize the "open visible Claude Code terminal" pattern across author + (future callers)

**Caveat**: `run_claude_task` does not currently support `--session-id` for resume. Adding it is mechanical. Logged as **CA-13** opportunity, not blocked on it.

### Wire program filter into research (F2)

Five layers hardcode `["olg","cmr","fns","cfr"]`. Adding program filter to author's research:
1. Add `programs_by_source` Form param to `/author/{name}/research/run`
2. Add per-source program checkboxes to `partials/author_prompt_editor.html` (research branch) using `PROGRAM_REGISTRY` template global
3. Pass `programs_by_source` through to `run_synthesis`

Same shape as the work that wired program filter into the Ask tab (per memory). Connects to deferred TODO `todo_per_source_program_filter.md`. [Folds into per-source program filter UI work.]

### CLI/UI parity decision (F3)

Decide if the CLI is a maintained interface or a debug helper:
- **Maintained**: fix `--no-docx`, `--format-draft`, add `--sources`, `--task-instructions`, `--research-version`
- **Debug helper**: document as such; remove the lying `--format-draft` print message; deprecate `--no-docx`

Current state is in-between (mostly works for happy path, lies in two places).

### Partial consolidation (F5/F6)

Three list partials + three detail partials with same shape. Could be:
- One `partials/version_entries.html` parameterized by phase + entry-renderer macro
- One `partials/version_detail.html` with phase-specific block extension

Adding a fourth phase would otherwise mean six new partials.

### Author's Notes deduplication (F13)

Pick one home for "flag system improvements in Author's Notes" instructions: the prompt (`programs/author/prompts/author_draft.md`) is editable by the user; the inline append in `compose_draft_prompt` is harder to find. Lean toward keeping it in the prompt only.

### JSON data endpoints for JS (F11)

Three places parse server-rendered HTML to extract version data. Cleaner: `/author/{name}/drafts.json` returns `[{num, ts, has_draft, ...}, ...]` directly. JS consumes JSON, not parsed HTML. Replaces the brittle CSS-selector contract with an explicit JSON contract.

### Drop `claude_code_timeout` config or wire it through (F15)

Dead config. Either delete the key from `config.ini` and `docs/author.md`, or — if F1 lands — pass it through to `run_claude_task(timeout=...)`.

### Adopt author's evidence persistence pattern in search history (F19)

Author's `evidence.json` is the canonical SynthesisResult persistence shape; search drops `search_queries`. Cross-app cleanup direction: search NS1 fix follows author's pattern. **CA-14** in cross-app findings.

## Open questions

- **CLI vs web UI**: maintained or debug helper? (F3)
- **Program filter on author research**: default to SNAP, expose UI, or accept the breadth as deliberate? (F2)
- **Visible terminal architecture**: keep Windows-only as deliberate, or design for cross-platform (F21)?
- **`tools/claude_code_runner.py` migration scope**: F1 is straightforward but adds a `--session-id` arg requirement. In-scope for this cleanup arc, or deferred?
- **Per-phase versioning model**: stays author-specific (F10's pattern), or absorb into `tools/` if QC adopts it?
- **Author's two prompt locations**: keep the project-shared/app-local split, or move both to one home? (F17)

## Decisions log

*(empty — populate as decisions are made)*


## To do for next session

1. ~~**Step 3 — UI surface**~~ — **COMPLETE 2026-05-06**. 9 partials + author routes mapped. F5/F6/F22/F23/F24 added.
2. ~~**Step 4 — JS surface**~~ — **COMPLETE 2026-05-06**. `app.js:L29-L480` read. F11 (HTML-parsing × 3) and F12 (scripted-progress × 4) added.
3. ~~**Step 5 — Config audit**~~ — **COMPLETE 2026-05-06**. `[author]` section + `tools/docx_writer.py` audited. F15 confirms `claude_code_timeout` is dead config; F18 documents author as deepest synthesis caller.
4. ~~**Deep architectural findings**~~ — **COMPLETE 2026-05-06**. F1-F26 + B1 + B2 added. OBS-A through OBS-N all resolved/superseded.
5. ~~**Cross-app additions**~~ — **COMPLETE 2026-05-06**. CA-13 (Claude Code subprocess duplication), CA-14 (SynthesisResult persistence shapes), CA-15 (load_config × 5 + prompt-loading conventions) added; existing CAs updated with author data points.
6. ~~**Synthesis observations from author**~~ — **COMPLETE 2026-05-06**. "Author (audit complete)" section added to `../synthesis_review/README.md`.

**This is the last app audit.** Cross-app comparison pass is now complete with author inputs. Cleanup execution sequencing is ready (see `../cross_app_findings.md`).

## Special notes for the author audit

Author is **structurally different from the other three apps** in two ways:

1. **It's the only app with three engines deliberately routed**: API (synthesis for research), Claude Code (subprocess for drafting), pure Python (docx_writer for formatting). Each phase uses the engine that fits. **This is the canonical example of the engine-routing pattern.** The audit's job is to confirm each routing is intentional and well-shaped, not accidental.

2. **It's the deepest synthesis caller**: search uses synthesis as a black box; author exercises more of synthesis's surface area (`prompt_name`, `config_overrides`, custom `max_searches`, deep mode hardcoded). The audit should verify each customization is earning its weight.

The audit lens: **"is each engine routing earning its keep, and is the rich synthesis interface being used as intended?"** Most findings will be:
- Drift: hand-rolled .bat files instead of `tools/claude_code_runner.py` (OBS-C)
- Drift: own `evidence.json` shape (OBS-N)
- Under-design: no program filter on research (OBS-D), no error handling (research/draft/format all lack try/except), CLI lags web UI (OBS-I)
- Cross-app: same patterns as the other audits (load_config, retry, formatters, scripted progress)

**This is the last app audit.** When complete, the cross-app comparison pass picks up its final inputs and the cleanup execution phase begins.
