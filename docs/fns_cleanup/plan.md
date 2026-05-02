# FNS Cleanup Plan

**Status**: DRAFT — under discussion
**Created**: 2026-05-01
**Last updated**: 2026-05-01 (revised after Ben input on program model + effort tiering)
**Parallels**: `docs/cmr_cleanup/plan.md`, `docs/olg_cleanup/plan.md`
**Cost**: Re-embedding ~$0.10. Zero LLM cost (deterministic code).

## Effort tiering

Per Ben's call: full effort goes into SNAP chapters (7, 8, 9, 10, 11, 13). QC Process chapters (1, 2, 3, 4, 5, 6, 12, 14) get only the universal mechanical fixes; we do not put manual work into auditing their charts, side-by-side boxes, or complex tables.

| Tier | Scope | What it covers |
|---|---|---|
| **Tier 1 — universal** | All 482 sections | Splitter rewrite, cross-heading merge protection, position metadata, program tag, continued-table headers, broader bullet recognition, page-header leak fix |
| **Tier 2 — SNAP only** | 307 SNAP sections | Side-by-side example box fix, Chart→prose conversion, definition-section handler, manual table audits |
| **Tier 3 — skipped** | QC sections | Side-by-side fix for QC, manual table audits for QC, definition handler for Ch 1 |

## Goal

Bring FNS Handbook 310 chunking up to the quality bar already in place for OLG, CMR, and CFR. Eliminate the same three problem patterns we removed elsewhere:

1. Mid-word / mid-list-item chunk splits when sections exceed `MAX_CHUNK_SIZE`
2. `(continued)` suffixes instead of structured position metadata
3. Missing per-chunk position metadata (`hierarchy_path`, `chunk_n`, `chunk_total`)

Plus FNS-specific work the other three cleanups did not need:

4. **Two-program tagging** — FNS is fundamentally a QC handbook with federal SNAP policy embedded inside. Tag every section with a `program` (`SNAP` or `QC_Process`) so the UI checkbox panel can let users explicitly include each one. Default pre-checked: `SNAP`.
5. **Bullet-dominant hierarchy profile** — FNS uses bullets (`•`, `➢`) and dashes (`-`) far more than CMR's nested paren markers `(A)→(1)→(a)`. Pattern profile is structurally different.
6. **Side-by-side example boxes** — 60 sections flagged `side_by_side_page` by the parser. Spot check on §844 shows the right-column "Example" box content is being **dropped entirely** (not just disordered). Real bug, not a verification step.
7. **Charts** — at least 2 SNAP sections contain "Chart 1", "Chart 2", "Chart 3" labels referring to flowcharts in the source PDF. Flowcharts almost certainly extracted as garbled text. Need to be replaced with prose decision trees, similar to how CFR's 16 garbled multi-column tables got manually rewritten.
8. **Definitions sections** — handle similarly to CFR's dedicated definition chunker for 271.2 / 292.2.
9. **Page-header leak** — §844 dump contains `FNS Handbook 310` mid-body (a page header that survived the parser's stripping). Suggests the side-by-side parsing path skips the header strip.

## Out of scope

- **Re-parsing the PDF**: the parser is in good shape. This cleanup is chunker + metadata + consumer updates. If parser issues surface during validation, scope them then.
- **Re-embedding** (Phase 6): held until Ben gives explicit go after chunking is verified.
- **Cross-source comparator changes**: comparator already consumes FNS. New `content_type` is additive metadata; comparator can opt in later.

## Current-state diagnostic (2026-05-01)

| Symptom | FNS today |
|---|---|
| Total section chunks | 722 |
| Chunks labeled `(continued)` | 295 (~41%) |
| Chunks still > 1,500 chars after splitting | 137 |
| Chunks with `hierarchy_path` | 0 |
| Chunks with `chunk_n` / `chunk_total` | 0 |
| Splitter | `paragraph → sentence → hard-slice` (no hierarchy awareness) |
| Cross-heading merge protection | none |
| Continued-table header repetition | none |
| Sections flagged `side_by_side_page` | 60 |
| Sections with tables | 22 (33 tables total) |

### Hierarchy pattern occurrences (482 sections)

| Pattern | Lines matched | Sections affected |
|---|---|---|
| `^[•·]\s+` (bullet) | 1,315 | 233 |
| `^[-—–]\s+` (dash) | 228 | 47 |
| `^\d+\.\s+` (numbered) | 95 | 27 |
| `^[A-Z]\.\s+` (upper letter) | 10 | 3 |
| `^[a-z]\.\s+` (lower letter) | 6 | 2 |
| `^\(\d+\)\s+` (paren num) | 1 | 1 |

**Plus**: arrow-style sub-bullets `➢` (right-pointing pointer, U+27A2) confirmed in §510 from the source PDF. Not in the initial regex profile — must be added. Likely also `▪`, `○`, or other glyphs depending on chapter.

**Key insight**: FNS is mostly **prose with bulleted lists**, not nested legal markers. The splitter strategy must mirror OLG's break-priority approach (list-item → paragraph → sentence), not CMR/CFR's top-level-marker approach. The section number itself (`1045.2`) is the structural address; the within-section structure is light.

### Problem-count breakdown by program

| Symptom | SNAP chapters (7,8,9,10,11,13) | QC chapters (1-6, 12, 14) |
|---|---|---|
| Sections | 307 | 175 |
| Section chunks | 445 | 277 |
| Chunks > 1500 chars | 81 | 56 |
| Chunks `(continued)` | 178 | 117 |
| Side-by-side flagged sections | 30 | 30 |
| Chart-bearing sections | 2 | 0 |
| Sections with tables | 14 | 8 |

Tier-1 mechanical fixes hit all 722 chunks. Tier-2 manual work (~46 sections of charts/tables/side-by-side audits in SNAP chapters) is the bounded scope for hand effort.

### Section count by chapter

| Ch | Title | Sections | Brainstorm policy relevance |
|---|---|---|---|
| 1 | Introduction | 27 | Low — definitions, admin |
| 2 | Basic Review Process | 29 | Low — QC procedures |
| 3 | Case Record Review | 23 | Low — QC procedures |
| 4 | Field Investigation | 32 | Low — QC procedures |
| 5 | Verification & Documentation | 20 | Medium — verification standards |
| 6 | Error Determination | 14 | Low — QC-specific |
| 7 | Review Procedures / Cert Systems | 68 | High — reporting rules |
| 8 | Non-Financial Eligibility | 50 | Very high — eligibility |
| 9 | Resources | 28 | Very high — asset limits |
| 10 | Income | 83 | Very high — income rules |
| 11 | Deductions | 62 | Very high — deduction rules |
| 12 | Making the Review Decision | 15 | Low — QC procedures |
| 13 | Negative Action Record Reviews | 16 | Medium — denial procedures |
| 14 | Informal Resolution & Arbitration | 15 | Low — QC-specific |

**Implication for content tagging**: chapters split fairly cleanly into "policy" vs "QC procedure" but with mixed chapters (5, 7, 13). Chapter-level tagging is too coarse; we need section-level overrides for those.

## Phase 1: Parser-layer fixes

**File**: `rag/fns/parser.py`

Less of a touch-up than originally scoped. Diagnostic dump of §844 surfaced two real bugs.

### 1.1 Side-by-side example box content recovery (TIER 2 — SNAP only)

**Bug confirmed (2026-05-01)**: §844 (`ch08_844.json`, flagged `side_by_side_page`) does not contain the right-column "Example of adding new members to a retrospectively budgeted household..." prose at all. The screenshot shows the example as a substantial bordered box adjacent to a bulleted list; the parsed JSON has only the bullets.

Need to:
1. Inspect the parser's `side_by_side_page` code path — find where the right-column text gets dropped
2. Restore the example box content. Recommend appending it after the main flow with an `Example:` prefix line so the chunk text reads as: main prose → bullets → `Example: ...`
3. Apply only to SNAP chapters (30 sections). QC sections with `side_by_side_page` get the bug fix mechanically since it's one code path; we just don't audit the QC results before re-embedding.

Spot-check after fix: §844, plus 4 other SNAP-chapter side-by-side sections.

### 1.2 Page-header leak in side-by-side path

§844 dump contains `FNS Handbook 310` mid-text. The header-stripping logic that works for normal pages misses on side-by-side pages. Fix while we're in that code path.

### 1.3 Bullet-marker recognition

Add `➢`, `▪`, `○`, and any other bullet glyphs that scanning Ch 5/8/10 surfaces. One-line regex update; benefits both Tier 1 (splitter break-priority detection) and parser bullet handling.

### 1.4 Charts → prose (TIER 2 — SNAP only)

2 sections in SNAP chapters reference `Chart N` flowcharts. These are decision-tree diagrams that almost certainly extracted as scrambled text. Mirror the CFR table-recovery approach: locate the affected section JSONs, hand-rewrite the chart as a numbered prose decision tree directly in the parsed JSON, document the change in `docs/fns_cleanup/findings.md`.

Section identification: `grep -l "Chart [1-9]" index/fns/parsed_sections/*.json`. Confirmed at least one in Ch 7 from screenshot (Chart 3 in retrospective income reporting). Inspect each, rewrite as prose, lock in.

### 1.5 Definition section handling (TIER 2 — SNAP only by default; check Ch 1 sample if cheap)

Mirror CFR's dedicated definition chunker for 271.2 / 292.2: when a section is a list of defined terms (each term is its own short entry), each definition becomes its own chunk regardless of MIN_CHUNK_SIZE — never merged with neighbors, never truncated.

Detection: a section is a "definition list" if the majority of its content is structured as `Term. Definition...` or bullet items where each starts with a capitalized phrase followed by a colon or period.

In SNAP chapters, scan for definition sections and apply the handler. Ch 1's `154_*` series is the obvious QC-side example, but per Ben we don't put effort into QC chapters; the chunker's cross-heading merge protection (Phase 2) prevents `154_1` from merging into `154_2` regardless, which is the main correctness concern.

## Phase 2: Hierarchy-aware chunker

**File**: `rag/fns/chunker.py` — replace `split_large_section()` and rework `merge_small_sections()`.

### 2.1 Split-priority order

When a section exceeds `MAX_CHUNK_SIZE` (1,500 chars), choose break points in this priority — borrowed from OLG, since FNS structure is closer to OLG than to CMR:

1. **Table row boundaries**: any line that's part of a rendered table block. Inside a table block, prefer breaks between rows. Never break inside a row.
2. **Bulleted list items**: lines starting with `^\s*[•·➢▪○]\s+` or `^\s*[-—–]\s+`. Prefer breaks at top-level item boundaries; do not break between a bullet and its sub-bullet (e.g., a `•` followed by indented `➢` lines stays grouped).
3. **Numbered list items**: `^\s*\d+\.\s+`. Same treatment.
4. **Paragraph boundaries**: `\n\n`.
5. **Sentence boundaries**: regex `(?<=[.?!])\s+(?=[A-Z])`.
6. **Hard character split** at `TARGET_CHUNK_SIZE` — last resort, log a warning so we can see if it still fires.

Define the priority list as a per-source `FNS_BREAK_PROFILE` so the splitting algorithm itself is generic. This mirrors how CMR/CFR define their hierarchy profile.

### 2.2 No top-level "marker break" — it's a list-item splitter

Unlike CMR/CFR, FNS has no consistent top-level paragraph marker (`(A)`, `(a)`, etc.) inside a section. The splitter is purely break-priority-driven. There is no "prefer_break when we see Level 1 marker" logic — every break decision is "current size near MAX, find the highest-priority boundary nearby".

### 2.3 Continued-table headers

When a table is split across chunks, the second chunk should begin with the table's header row repeated. Same fix OLG got. Affects only 22 sections that have tables; small but high-value where it applies.

### 2.4 Cross-heading merge protection

`merge_small_sections()` currently merges any sub-MIN section forward into its neighbor regardless of hierarchy. With FNS's `level` field already populated by the parser (sections have `level` 1, 2, or 3 based on section_number depth), apply the same OLG rule:

> A section may merge with a neighbor only when one side is heading-less (intro / level 0) or when both sides share the same parent_section. A merge that would combine two distinct level-2 sections, or a level-2 with its level-3 child, is rejected; the smaller section stays small.

Concrete example: `154_1 Definition A` (short) should NOT merge into `154_2 Definition B`. They're sibling level-3 definitions with the same parent (`154`); the merge would let one definition's text bleed into the other's chunk.

A section may stay below MIN_CHUNK_SIZE — that's fine. The chunk metadata still identifies what it is.

### 2.5 Replace `(continued)` with hierarchy_path

When a section splits, drop the `(continued)` suffix on `section_title`. Instead, populate `hierarchy_path` metadata with a position label. For FNS the natural label is the section number plus a position descriptor:

- Chunk 1 of 3: `hierarchy_path = "1045.2 Dividends and Interest"`
- Chunk 2 of 3: `hierarchy_path = "1045.2 Dividends and Interest (part 2 of 3)"`
- Chunk 3 of 3: `hierarchy_path = "1045.2 Dividends and Interest (part 3 of 3)"`

Open question: is "part N of M" enough, or should we attempt to surface a within-section topic label (e.g., a bullet-list intro phrase)? FNS doesn't give us reliable structural anchors for this. Recommend keeping it simple — `chunk_n` / `chunk_total` carry the position info; consumers display it however they want. This is **discussion item #1**.

### 2.6 Per-chunk position metadata

Three new metadata fields on every section chunk (matching CMR/OLG/CFR):

| Field | Type | Value |
|---|---|---|
| `hierarchy_path` | string | section number + title (+ `(part N of M)` if split) |
| `chunk_n` | int | 1-indexed position within section's split sequence |
| `chunk_total` | int | total chunks produced from this section |

A section that fits in one chunk has `chunk_n=1, chunk_total=1`.

### 2.7 Per-section chunk IDs

Already in good shape — IDs look like `fns_sec_1021_1__000`. Confirm they reset per section (they do today). No change needed.

## Phase 3: Two-program tagging (NEW — FNS-specific)

**Goal**: tag every section with a `program` value so the UI checkbox panel and CLI can explicitly include each one. Mirrors how OLG (`SNAP` / `TAFDC` / `EAEDC` / `Cross-Program` / `BP`) and CMR (same set + `Hearings` / `Program Integrity`) work.

### 3.1 Two values: `SNAP` and `QC_Process`

```python
FNS_CHAPTER_PROGRAM = {
    1:  "QC_Process",      # Introduction, definitions
    2:  "QC_Process",      # Basic Review Process
    3:  "QC_Process",      # Case Record Review
    4:  "QC_Process",      # Field Investigation
    5:  "QC_Process",      # Verification & Documentation (QC-side)
    6:  "QC_Process",      # Error Determination
    7:  "SNAP",            # Review Procedures / Cert Systems
    8:  "SNAP",            # Non-Financial Eligibility
    9:  "SNAP",            # Resources
    10: "SNAP",            # Income
    11: "SNAP",            # Deductions
    12: "QC_Process",      # Making the Review Decision
    13: "SNAP",            # Negative Action Record Reviews
    14: "QC_Process",      # Informal Resolution & Arbitration
}
```

Notes on the split (per Ben, 2026-05-01):
- The original brainstorm tagged Ch 5 (Verification) as Medium and Ch 13 (Negative Action Reviews) as Medium. Ben's reclassification puts Ch 5 in QC and Ch 13 in SNAP based on actual case-processing relevance — Ch 13 covers denial procedures that affect cases; Ch 5 verification is QC-side documentation rules.
- This matches the comparator's existing `fns_chapters_to_compare = 7,8,9,10,11` decision in `config.ini`, with Ch 13 added to SNAP.

### 3.2 Implementation

- Chapter is already on every chunk as integer `chapter` metadata. New field: `program` (string), populated by lookup at chunk-build time.
- No section-level overrides. Chapter is the unit. If a specific SNAP-chapter section turns out to be pure QC content, we deal with it as a one-off later — not worth maintaining an override list.
- `program` value lives on both `fns_sections` and `fns_chapter` collections.

### 3.3 Consumer behavior — explicit-include only

Per Ben's philosophy: every program tag must be explicitly included via UI checkbox or CLI flag. No silent default filtering anywhere.

- `query.py`: add `--program SNAP,QC_Process` flag (multi-value, comma-separated). When omitted: include all programs (current behavior, no regression).
- UI checkbox panel (future, when per-source filter UI lands): two checkboxes for FNS, **`SNAP` pre-checked, `QC_Process` unchecked** by default. User clicks `QC_Process` to widen the search.
- `synthesis.py` / Ask tab: respects whatever the UI panel sends; no internal default.
- Comparator: continues to use `fns_chapters_to_compare = 7,8,9,10,11` from config (Ch 13 may be added to that list separately if Ben wants — independent decision).

### 3.4 Per-section tagging only

`program` is set at the section level and inherited by all chunks from that section. We do not produce mixed-program chunks. If a future need surfaces for finer tagging, that's a separate decision — not part of this cleanup.

## Phase 4: Consumer display updates

**Files**: `rag/query.py`, `tools/synthesis.py`, `ui/templates/partials/answer.html`

Mirror the consumer work CMR Phase 8 / OLG Phase 5 already shipped.

- `rag/query.py` CLI — show `Path:` and `Part: N of M` lines for FNS results; show `Program:` line
- `rag/query.py` CLI — `--program SNAP,QC_Process` filter flag (multi-value)
- `tools/synthesis.py` — include `Section:` and `(part N of M)` in citation headers fed to Claude
- `ui/templates/partials/answer.html` — render position info and `program` badge in the result header
- UI checkbox panel: defer to the per-source filter UI work (already on TODO list); when it ships, FNS gets two checkboxes — `SNAP` pre-checked, `QC_Process` unchecked.

## Phase 5: Pre-embedding verification

Everything that must be checked before re-embedding.

### 5a. Chunker output verification

- Zero chunks under MIN_CHUNK_SIZE except where merge protection legitimately blocked the merge (those should be specifically the same-parent siblings, document the count)
- Zero chunks with `(continued)` in `section_title`
- Every multi-chunk section has `hierarchy_path` + `chunk_n` + `chunk_total`
- `chunk_total` consistency: sum of `chunk_n=1` rows equals total section count
- Every chunk has `content_type` set
- Total chunk count is reasonable (baseline: 722; expect modest delta either direction)
- Chunks-over-MAX count drops from 137 → 0 (or close to 0; document any remaining)
- Spot-check 10 sections: small intro, large income section that splits, side-by-side page, definition (`154_1`), table-bearing section (`1160`?), QC-only section (Ch 4), each `content_type` represented at least once

### 5b. Program tag verification

- Every chunk has `program` ∈ `{SNAP, QC_Process}`
- Distribution: ~445 SNAP chunks, ~277 QC_Process chunks (matches today's chapter buckets within a small delta from chunker changes)
- Spot-check 5 chunks per chapter to confirm the chapter→program mapping landed correctly

### 5c. Regression check

- Sections that don't split still produce identical single-chunk text content
- Chapter-level documents (`fns_chapters` collection) are unaffected — those don't change
- Metadata fields are ChromaDB-compatible (no None values, all strings/ints)

## Phase 6: Reprocess + re-embed

1. Re-run chunker: `python rag/fns/chunker.py`
2. Dry-run embedder: `python rag/embedder.py --source fns --dry-run` (confirm cost ~$0.10)
3. Re-embed: `python rag/embedder.py --source fns --force` — gated on Ben's go
4. Run a small benchmark — see Phase 7

## Phase 7: Validate

No FNS retrieval benchmark exists today (CMR has one; FNS doesn't). Two options for validation, both viable:

**Option A — port CMR's 20-question benchmark approach.** Hand-author a 15-20 question FNS retrieval benchmark sourced from real comparator findings (where the comparator actually needed to find a specific FNS section). Rerun before/after to compare. Effort: ~1 hour to draft, ~30 min per run.

**Option B — comparator regression.** Re-run a sampled subset of comparator results and compare classifications. If the new chunking changes any "MISSING" → "PRESENT" calls, those are wins.

Recommend **Option A** because it's purpose-built for retrieval quality and gives a clean number to compare. **Discussion item #4**.

## Phase 8: Documentation

Update `docs/fns_pipeline.md` with the new metadata fields, content_type taxonomy, and split-priority approach. Add section number ranges where each `content_type` predominantly applies. (Mechanical doc work, do at the end.)

## Implementation order

1. **Phase 1.1-1.2**: side-by-side parser fix + page-header strip — fixes a real data-loss bug
2. **Phase 1.3**: bullet-marker recognition (one-line update)
3. **Phase 2.1-2.4**: splitter rewrite + merge protection + continued-table headers
4. **Phase 2.5-2.7**: position metadata (integrated with 2.1-2.4)
5. **Phase 3**: program tagging — independent of splitter; lands in same PR
6. **Phase 1.4-1.5**: chart rewrites + definition handler (TIER 2, can defer if scope tight)
7. **Phase 5**: pre-embedding verification — gate on this
8. **Phase 4**: consumer updates — landed before re-embedding so we can verify display
9. **Phase 6**: re-embed (single pass)
10. **Phase 7**: benchmark
11. **Phase 8**: docs

One re-embedding pass covers everything.

## Discussion items (resolved 2026-05-01)

1. **`hierarchy_path` granularity for split chunks**: simple — `"X.Y Title (part N of M)"`. No within-section topic label extraction. RESOLVED.
2. **Default filter behavior**: explicit-include only via UI checkboxes / CLI flags. UI pre-checks `SNAP` only. No silent filtering. RESOLVED per Ben's philosophy.
3. **Per-chunk `program` override**: no — section-level only. RESOLVED.
4. **Validation approach**: TBD. Lean toward small (10-12 question) hand-authored benchmark sourced from comparator findings.
5. **Override list construction**: N/A — no overrides; chapter→program is the rule. RESOLVED.

## Files to modify

(Updated for revised scope.)

| File | Changes | Tier |
|---|---|---|
| `rag/fns/parser.py` | Side-by-side example box content recovery + page-header strip on side-by-side path; broader bullet recognition (`➢` etc.); chart-section identification helper | 1 + 2 |
| `rag/fns/chunker.py` | New splitter w/ break-priority profile, cross-heading merge protection, `hierarchy_path` / `chunk_n` / `chunk_total` / `program` metadata, continued-table header repetition, definition-section handler | 1 + 2 |
| `index/fns/parsed_sections/*.json` | Hand-rewrite of 2 SNAP-chapter Chart sections as prose decision trees | 2 |
| `rag/query.py` | `--program` filter flag; FNS result formatting (Path / Part / Program) | 1 |
| `tools/synthesis.py` | FNS citation format using `hierarchy_path` and `chunk_n/chunk_total` | 1 |
| `ui/templates/partials/answer.html` | Display `hierarchy_path`, `chunk_n/chunk_total`, `program` badge | 1 |
| `docs/fns_pipeline.md` | Document new metadata + program tagging | 1 |
| `docs/fns_cleanup/findings.md` | (Optional) Numerical findings + chart rewrite log | concurrent |
| `docs/fns_cleanup/retrieval_benchmark.md` | If Option A chosen — 10-12 question benchmark + baseline scores | concurrent |

## Approval gates

- Plan review (this document) — pending
- Phase 5 verification output review — pending
- Phase 6 re-embed — explicit Ben go required
