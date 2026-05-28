# Comparator UI Integration — Brainstorm

**Status:** Brainstorm. Not yet planned, not yet built.
**Date captured:** 2026-05-08
**Likely design session:** weekend of 2026-05-09 / 2026-05-10

## Why now

The comparator has lived as a CLI-only tool with hardcoded scope (FNS chapters 7-11 against OLG). Two things make a UI integration worth doing now rather than later:

1. **The user has more comparison ideas.** A UI tab makes new corpus pairings and focus prompts a config decision rather than a code change.
2. **A silent OLG filter bug surfaced 2026-05-08.** L2's OLG search was hardcoded `program="SNAP"`, which excludes Business Process (the SNAP procedural backbone) and Cross-Program (also SNAP content). A stopgap fix shipped same day swapping it to `exclude_programs=["TAFDC", "EAEDC"]`. Putting filter selection in the UI is the durable fix — it makes filtering visible by construction, which is the cross-cutting principle ("filtering allowed but never silent").

## User's notes (raw, captured 2026-05-08)

> We need to design a UI integration for comparator, following the other apps, its own tab. You should be able to select which corpus to compare with and against, and there should be a box for a prompt to clarify what the comparator is looking for. In our case, that's OLG against FNS and we're looking for coverage of policy AND procedure. Could do plenty of other things if we wanted.

## Confirmed from discussion

- **Default direction is OLG-as-target, FNS-as-source.** FNS Handbook 310 is the federal QC standard (the "should be"); OLG is what staff actually follow (the "what we have"). The comparator iterates FNS sections and looks for OLG coverage of each.
- **Default focus statement** is "coverage of policy AND procedure" — meaning absence of either the rule itself or the operational how-to is worth flagging.
- **OLG searches must not silently filter to SNAP-label-only.** Default must include BP, Cross-Program, etc. The hardcoded fix landed 2026-05-08 is a stopgap; the UI is the real fix.

## Existing patterns to follow

| App | Tab pattern | What's reusable |
|---|---|---|
| **Search (Ask)** | Single input → synthesized output → history list | Source registry, history persistence pattern |
| **Author** | Multi-phase pipeline (Research → Draft → Format) with run versioning, visible Claude Code spawn for Draft | Per-run versioning dirs (`runs/001_timestamp/`), windowed Claude Code spawn for visibility |
| **QC** | Upload → multi-phase per-row pipeline → per-row results table | Per-run timestamped output folder; **collapsible read-only filter panel showing per-source program include/exclude lists**; per-row JSON storage |
| **Comparator** (proposed) | Closest to QC: scoped run with per-section investigation, table-of-results display | Adopt QC's filter panel verbatim; adopt per-run timestamped folder |

## Design surface (preliminary)

### Inputs

- **Source corpus** (the standard being measured against): dropdown — FNS, CFR, CMR, OLG
- **Target corpus** (what's being checked for coverage): dropdown — OLG, CMR, FNS, CFR
- **Scope** within source: chapter range, section list, or "all" — shape depends on the source corpus
- **Focus prompt**: free-text box. "What is the comparator looking for?" Examples:
  - "Coverage of policy AND procedure" (current OLG-vs-FNS default)
  - "Statutory authority for state options"
  - "Verification standard alignment"
  - "Procedural completeness vs. policy completeness"
- **Program filters** (per source and per target): include/exclude lists, mirroring QC tab's collapsible read-only panel. Active filter visible at all times so silent filtering can't recur.

### Pipeline shape

Current 4-layer model and how it generalizes:

| Layer | Current behavior | UI generalization risk |
|---|---|---|
| **L0** pre-classify | FNS-specific prompt classifies sections as compare/skip/reference | Won't generalize as-is — either drop L0 for non-FNS source or refactor to be source-agnostic |
| **L1** triage | Multi-query retrieval against target + Haiku classification | Generalizes cleanly — works for any source/target pair |
| **L2** deep investigation | Agentic search of target (OLG) with focus on the source section | Focus prompt should plug into L2's system instructions |
| **L3** cross-check | Hardcoded to CMR + CFR | Needs rethinking — generalize to "compare against authority list" with the list selectable |

### Outputs

- Per-section result JSONs (existing cache pattern at `output/comparator/results/`)
- CSV per run
- HTML report (existing `report.py`)
- Within UI: per-row table view, classification + priority chips, expandable note, click L2 session ID to copy `claude --resume <UUID>`

## Open questions for design session

- **CLI vs UI coexistence.** Does the UI replace CLI runs or sit alongside? (Lean: alongside — CLI is good for batch and reproducibility.)
- **Run identification.** Per-run timestamped folders like QC's new pattern? (Lean: yes.)
- **Re-run semantics.** Re-run on same scope replaces, forks, or prompts (like QC re-extract)?
- **L2 visibility.** Spawn windowed Claude Code (like author drafts) or run headless with progress polling? Parallel runs make windowed chaotic.
- **Default corpus pair.** UI defaults to OLG-vs-FNS, or no default and user selects every time?
- **L0 fate.** Drop, generalize, or keep FNS-only?
- **What about the existing 270 contaminated results?** (See "Pre-existing data" below.)

## TODO when UI ships

- [ ] **Remove the hardcoded `exclude_programs=["TAFDC", "EAEDC"]`** at `apps/comparator/comparator.py:464` (L1) and `:662` (L2). Replace with UI-driven filter lists, mirroring QC's `_load_filters(config)` pattern with config-as-fallback.
- [ ] Decide L3 filter: currently `program="SNAP"` hardcoded at `comparator.py:488` for CMR and CFR. May be fine, may want to surface in UI as part of the cross-check authority selection.
- [ ] Update `docs/comparator.md` and CLAUDE.md to reflect the new UI tab.
- [ ] Add new tab to `ui/app.py` + corresponding Jinja template + HTMX partials.
- [ ] Decide migration of existing `output/comparator/results/` cache into the new run-folder structure (or start fresh).

## Pre-existing data — 2026-05-08 status

- **270 sections of comparator output exist** across `output/comparator/comparison_claude-code_20260321_FNS-*.csv` (March 2026 full run) and the May 2026 chapter-10 re-runs (51 cached results).
- **All of it was generated under the broken L2 OLG = SNAP-label-only filter.** This means some "Gap" / "policy_present_procedures_missing" findings are likely false positives — the OLG actually covers the topic, just under BP or Cross-Program.
- **What survives the bug:** L0 classifications (no OLG retrieval involved), L3 CMR/CFR cross-checks (independent reasoning), and the "different_standard" findings where the L2 actually found OLG content (it found SNAP-labeled content even with the narrow filter).
- **What's suspect:** "confirmed_gap" classifications where L2 said "OLG is silent" — silent in the SNAP label may not mean silent overall.
- **Triage candidates from existing run** (7 HIGH-priority items, may include false positives):

  | Section | Classification | Topic |
  |---|---|---|
  | Ch10 1013.4 | different_standard | Weekly/biweekly income conversion |
  | Ch10 1044 | different_standard | Educational grants verification (verified real) |
  | Ch10 1070.1 | different_standard | Income from ineligible household members |
  | Ch7 720.4 | confirmed_gap | Substantial lottery winnings reporting |
  | Ch7 741.3 | confirmed_gap | PA changes synchronization |
  | Ch9 932 | policy_present_procedures_missing | Non-citizen sponsor exempt resources |
  | Ch9 972 | confirmed_gap | Real property when no property acknowledged |

## Future use cases (capture as they come up)

User has additional comparator ideas to add here. To be filled in during the design session.

## Status timeline

- **2026-03-21 → 2026-05-07:** comparator runs (chapters 7-11, 270 sections; chapter 10 re-run during apps-cleanup migration). All under the broken L2 OLG filter.
- **2026-05-08 morning:** filter bug surfaced during user's chapter-10 re-run review. Stopgap fix shipped (L2 OLG `program="SNAP"` → `exclude_programs=["TAFDC", "EAEDC"]`).
- **2026-05-08 afternoon:** this brainstorm captured.
- **Weekend 2026-05-09 / 2026-05-10:** detailed UI design session.
- **TBD:** UI implementation.
- **TBD:** post-UI cleanup of hardcoded filter and full re-run.
