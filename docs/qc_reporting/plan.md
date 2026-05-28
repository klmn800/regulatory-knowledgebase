# QC Reporting & Presentation Plan

**Status**: PPT Steps 1–3 implemented (in review); HTML report design resolved 2026-05-08, execution pending
**Created**: 2026-05-08
**Last updated**: 2026-05-08
**Owner workflow**: Ben (policy team)

## Workflow context

QC analyzer is one stage in a larger job. The full pipeline Ben runs is:

1. **Receive** a QC reviewer's report (CSV of error findings)
2. **Analyze** the findings for policy coverage gaps — *what QC analyzer does today*
3. **Present** the gaps to his boss — currently a manual write-up; this plan adds it
4. **Author** OLG pages to fill the gaps — handled by the existing author tool

This plan covers step 3: turning a completed QC analysis into shareable artifacts. Two outputs:

- **HTML report** — comprehensive, filterable, working-document for Ben and peers
- **PPT presentation** — curated, narrative-driven, deck for the boss conversation

Both are **optional** post-analysis steps that live below the existing investigation results display on the same page (single-page scroll workflow — analysis at top, optional outputs below).

## Outputs in scope

### HTML report (DEFERRED — design resolved 2026-05-08, execution still pending)

**Audience**: Ben (triage), peers (review, sharing).

**Pattern**: Copy `apps/comparator/report.py` look-and-feel — single dark-mode page, expandable details, filter pills, clean cross-source detail blocks. Differences from comparator:
- **Engine: pure Python templating, no LLM.** The data is structured (findings + judge trace + cross-checks + recurring gaps); rendering is deterministic. Zero per-run cost, fast, no versioning needed.
- **Delivery: live route + downloadable file.** Served at a FastAPI route (`/qc/report` or similar) for the user's local browsing, plus a "Download" button that produces a self-contained .html (CSS + JS inlined) for emailing peers. The app isn't hosted, so the URL is local-only — download is the sharing mechanism.
- **Cross-analysis is in scope.** The HTML view scopes to All analyses or any subset via comparator-style pill buttons (e.g., `[All] [Oct-2025] [Sept-2025] [Q3-2025]`). Triage benefits from seeing across batches; this is where cross-batch recurring gaps surface as the headline signal.

**Decisions made**:
- **Cross-analysis: in scope.** Default scope = All; user can scope down with pill buttons. Reverses the earlier per-analysis-only decision.
- **Engine**: pure Jinja-style templating, no LLM. Faster, cheaper, deterministic.
- **Versioning**: none. The HTML is a function of analysis state — regenerate on each request.
- **Comprehensive**: every finding included. Filterable and expandable.
- **Cross-source rendering**: reuse comparator's detail-block look. QC has up to three cross-checks (CMR + FNS + CFR) vs comparator's two — adapt the layout once the basics are in place.
- **Judge trace**: surfaced as expandable detail (per-turn reasoning + tool calls already nested in finding JSON).
- **Recurring-gap callout**: top-of-report panel, before the filterable table. Cross-analysis-aware — pages flagged across multiple batches are the headline signal.
- **Filter dimensions** (all surfaced as pill buttons / chips):
  - Analysis scope (`[All] [Oct-2025] [Sept-2025] ...`)
  - Coverage classification (Adequate / Partial / Gap / Error)
  - OLG program (SNAP / TAFDC / EAEDC / Hearings)
  - Cross-check alignment per source (CMR aligns / silent / differs; same for FNS, CFR)
  - Recurring (yes/no)
  - Confidence (HIGH / MEDIUM / LOW)
  - Free-text search across `policy_issues`, `gap_description`, `reasoning`
- **Flag (renamed from "favorite")**: localStorage-only marking, generic ("attention," "ignore," whatever Ben wants) — becomes another filter dimension. Round-tripping flags into the analysis JSON is deferred.
- **UI entry point**: narrow row above the PPT section on the QC analysis page ("Open HTML report" button). The report itself spans analyses; opening it from a specific analysis pre-selects that one as the filter.
- **Storage**: live-rendered, no on-disk artifact. The data lives in `output/qc_analysis/*/results/*.json`; templating on each request is cheap. "Download" generates the self-contained file on click.

**Top-of-report layout** (target):
1. Stats row — total findings, breakdown by classification, analyses included
2. Recurring-gap callout panel — pages flagged across analyses
3. Filter pills — analysis scope first, then coverage / program / cross-check / flag / confidence
4. Search box — free-text across abstract policy fields
5. Findings table — expandable rows with judge trace + cross-checks

**Open questions** (resolve during execution):
- Performance at scale: rendering all findings across N analyses with judge traces inline could get heavy. Lazy-load expandable details? Paginate? Probably fine up to ~hundreds of findings.
- Cross-analysis recurring-gap detection: the existing `find_recurring_gaps()` operates on one analysis. Needs a wrapper that flattens findings across multiple analyses before running.
- Download bundle: inline all CSS/JS into one .html, or accept a small set of asset files? Single self-contained file matches comparator and is much friendlier to email.

### PPT presentation (NEXT — execution starts after this doc)

**Audience**: Ben's boss (decision-maker) and possibly leadership briefings.

**Architecture** (mirrors the author pipeline almost exactly):

| Phase | Engine | Cost | Output |
|-------|--------|------|--------|
| Configure | UI form (checkbox finding selector + free-text instructions) | $0 | `inputs.json` (selected findings + instructions + filter selections) |
| Generate | Claude Code CLI (windowed, resumable via `session_id.txt`) | $0 (subscription) | `outline.json` (validated against `pptx_writer` schema) |
| Format | `pptx_writer.generate_pptx()` (deterministic) | $0 | `output.pptx` |

**Why this engine split**:
- Free format step (`pptx_writer` already encodes the DTA standard).
- Free generation step (Claude Code on subscription).
- Observable + resumable Claude Code window matches the author tab pattern Ben already uses and trusts.
- The intermediate `outline.json` is editable — Ben can tweak before formatting if needed.

**Decisions made**:
- **Finding selector**: checkbox UI. Default = all Gaps selected. Other classifications (Partial, Adequate) selectable but not on by default.
- **Instructions**: free-text textbox baked into the Claude Code prompt (e.g., "frame as urgency for next quarter", "emphasize income-coding patterns").
- **Versioning**: per-run versioned dirs like author tab — `output/qc_analysis/{name}_{ts}/ppt/runs/001_<timestamp>/`. Top-level files always hold latest. "Run Again" button creates a new version. Resume button uses version-specific session ID.
- **Slide structure** (target): one section divider → exec summary → one slide per gap (typically `two_column` for OLG-coverage vs cross-source) → speaker notes per slide. Final structure decided by the LLM under instruction guidance, within the schema constraints below.

**Format constraints (from `tools/pptx_writer.py`)**:

The LLM must emit `{"slides": [...]}` where each slide is one of:

| Type | Required fields | Notes |
|------|-----------------|-------|
| `title` | `title`, optional `subtitle` | DTA section-breaker layout, gold line |
| `section` | `title`, optional `subtitle` | Section divider |
| `content` | `title`, `bullets` (list of str or `{text, sub}`) | Bullets warned >120 chars |
| `table` | `title`, `headers`, `rows` | Manual table on blank layout |
| `two_column` | `title`, `left_title`, `right_title`, `left`, `right` (bullet lists) | Comparison layout |

All slides accept optional `notes` (speaker notes). Validation via `pptx_writer.validate_outline()` runs before render — rejects malformed input.

**Open questions** (resolve during execution):
- Does the LLM see the full analysis JSON or only the selected-findings subset? (Lean: subset, plus recurring-gap data, plus instructions.)
- Cap on slide count? (Lean: no hard cap; let the prompt guide.)
- Should `inputs.json` capture the user's filter UI state (which checkboxes were on) so re-runs are reproducible?

## PPT execution plan (next session)

### Step 1: Prompt + schema for Claude Code generation

Write `apps/qc/prompts/ppt_outline.md` covering:
- Slide schema (5 types + fields + 120-char bullet warning)
- Required final write to `outline.json`
- Validation hint (must pass `pptx_writer.validate_outline()`)
- Default narrative arc when user gives no instructions (title → exec summary → one slide per gap → closing)
- Instructions to incorporate Ben's free-text directives
- Speaker notes guidance (what to put in notes vs on the slide)

### Step 2: UI — configuration panel

Below the investigation results display in the QC analysis page:
- "Generate Presentation" section heading
- Checkbox group: include findings classified as [✓ Gap] [ ] Partial [ ] Adequate
- Free-text instruction textarea
- "Generate PPT" button → POSTs to backend → spawns Claude Code window
- Run history navigation (prev/next arrows + Run Again + Resume buttons), matching author tab

### Step 3: Backend — orchestration

- New module: likely `apps/qc/ppt_generator.py` (parallel to existing analyzer modules).
- Writes `inputs.json` (selected findings + instructions + filter snapshot).
- Spawns Claude Code via `tools/claude_code_runner.py` in windowed mode, prompt = the new `ppt_outline.md`.
- Captures session ID for resume.
- On Claude Code exit, validates `outline.json` and runs `generate_pptx()` to produce `output.pptx`.

### Step 4: Versioning + storage layout

```
output/qc_analysis/{name}_{ts}/
  results/                  # existing per-row JSONs
  ppt/
    inputs.json             # latest top-level
    outline.json            # latest top-level
    output.pptx             # latest top-level
    session_id.txt          # latest top-level
    runs/
      001_<timestamp>/
        inputs.json
        outline.json
        output.pptx
        session_id.txt
        metadata.json
```

Pattern matches `output/author/{name}/runs/...`.

### Step 5: UI wiring

- Endpoint to trigger generation
- Endpoint to download .pptx
- Endpoint to view current outline.json (debug / pre-format inspection)
- Resume endpoint (uses version-specific `session_id.txt`)

## Out of scope (explicit)

- **Cross-analysis PPT** — PPT is per-analysis only (the HTML report is the cross-analysis surface). Reconsidered 2026-05-08 and dropped because cross-analysis narrative gets unwieldy in slide form.
- **Auto-generation on analysis completion** — both outputs are user-triggered.
- **Editing PPT content in the UI after generation** — outline.json is editable on disk; round-trip UI editing is a future enhancement.
- **HTML-to-PPT or PPT-to-HTML conversion** — independent generators.
- **Round-tripping HTML report flags into analysis JSON** — flags are localStorage-only for now; integration with PPT pre-selection is a future enhancement.

## Decisions log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-08 | Two outputs (HTML + PPT), both optional, below investigation display, single page | Matches Ben's scroll-down workflow; separates from required investigate flow |
| 2026-05-08 | HTML = comprehensive; PPT = curated | Different audiences (Ben/peers vs boss) demand different artifacts |
| 2026-05-08 | PPT engine: Claude Code windowed | Free, observable, resumable; matches author tab pattern; intermediate JSON is editable |
| 2026-05-08 | PPT default selection: all Gaps; Partial/Adequate selectable via checkbox | Gaps are the action items worth a slide; rest is optional context |
| 2026-05-08 | PPT versioning: per-run dirs like author tab | Reuse author's UX exactly so the patterns are familiar |
| 2026-05-08 | HTML pattern: copy comparator first, iterate | Comparator report works well; no reason to redesign from scratch |
| 2026-05-08 | PPT before HTML | Higher value for the boss-presentation workflow; HTML can be modeled on a known-good (comparator) when we get to it |
| 2026-05-08 | HTML engine: pure templating, no LLM | Data is structured; rendering is deterministic. Zero per-run cost, no versioning needed. PPT needed an LLM because narrative; HTML is a triage dump |
| 2026-05-08 | HTML cross-analysis: in scope (reverses earlier "per-analysis only") | Triage benefits from seeing everything; cross-batch recurring gaps are the highest-value signal and only surface when scope spans analyses. Doesn't suffer from PPT's narrative-coherence problem |
| 2026-05-08 | HTML delivery: live FastAPI route + download button | App isn't hosted, so URL is local-only. Live route is always-current for Ben; download produces a self-contained .html for emailing peers |
| 2026-05-08 | HTML default scope: All analyses | Cross-analysis view is the value-add; default to it. User can scope down with pill buttons |
| 2026-05-08 | HTML "favorite" → "flag" + localStorage-only | Generic naming (could be attention or ignore); cross-machine persistence not needed yet |
| 2026-05-08 | Cross-analysis PPT: dropped (was briefly considered) | Cross-analysis narrative gets unwieldy in slide form; HTML report is the right surface for cross-analysis viewing |
