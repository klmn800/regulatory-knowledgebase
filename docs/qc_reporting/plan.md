# QC Reporting & Presentation Plan

**Status**: Planning — PPT execution next, HTML report deferred but captured here so we don't lose context
**Created**: 2026-05-08
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

### HTML report (DEFERRED — notes preserved here)

**Audience**: Ben (triage), peers (review, sharing).

**Pattern**: Copy `programs/comparator/report.py` model first, iterate from there. Comparator's report is a single dark-mode HTML page with favorites, expandable details, filter by chapter/classification/findings, and clean detail blocks per cross-source.

**Decisions made**:
- **Scope**: per-analysis only (not roll-up across analyses).
- **Comprehensive**: every finding included, not just Gaps. Filterable and expandable like the comparator page.
- **Cross-source rendering**: reuse comparator's CMR/CFR detail-block look as the starting point. QC has up to **three** cross-checks (CMR + FNS + CFR) vs comparator's two — adapt the layout once the basics are in place.
- **Judge trace**: surfaced as expandable detail (per-turn reasoning + tool calls already nested in finding JSON).
- **Recurring-gap awareness**: the cross-row recurring-gap panel from the QC audit follow-up should feed into the report (TBD whether as its own section or inline tags).

**Open questions** (revisit when we pick this up):
- Does the report bundle into the analysis run dir, or is it a standalone download like comparator's?
- Filter dimensions: which combination of program / classification / cross-check status / recurring matters most for Ben's triage flow?
- Favorites/marking: persist in the HTML (localStorage) or in the analysis JSON (so it round-trips)?

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

Write `programs/qc/prompts/ppt_outline.md` covering:
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

- New module: likely `programs/qc/ppt_generator.py` (parallel to existing analyzer modules).
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

- **Roll-up across analyses** — per-analysis only for both outputs (decision recorded above).
- **Auto-generation on analysis completion** — both outputs are user-triggered.
- **Editing PPT content in the UI after generation** — outline.json is editable on disk; round-trip UI editing is a future enhancement.
- **HTML-to-PPT or PPT-to-HTML conversion** — independent generators.

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
