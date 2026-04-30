# OLG Cleanup Plan

**Status**: Draft, awaiting approval before implementation
**Created**: 2026-04-29
**Parallels**: `docs/cmr_cleanup/plan.md` (completed 2026-04-27)

## Goal

Bring OLG parsing and chunking up to the quality bar set by the CMR cleanup. Eliminate the same three problem patterns we removed from CMR:

1. Mid-cell / mid-word chunk splits inside tables
2. Boilerplate UI artifact text contaminating chunks
3. Missing per-chunk position metadata (`chunk_n`, `chunk_total`, `hierarchy_path`)

Plus three OLG-specific issues:

4. Catalog pages (Brochures, Flyers, form lists) polluting retrieval
5. Transmittal log pages cluttering policy answers
6. Related Topics sections embedded as fuzzy text instead of structured cross-references

## Out of scope

- **Slug redesign** (4.4 in discussion): chunk IDs derive from URL today; deferred until other changes settle and we can judge readability gaps.
- **Acronym glossary as a prompt-side resource**: tracked separately in
  `~/.claude/projects/E--policy-navigator/memory/todo_acronym_glossary.md`.
- **Transmittal subdatabase**: future feature; not this cleanup.
- **Re-embedding**: held until Ben gives explicit go after chunking is verified.

## Findings summary (from review 2026-04-29)

Detailed findings to be captured in `findings.md` alongside this plan. Key
numbers from the diagnostic scan:

| Symptom | Count |
|---|---|
| Section chunks total | 6,785 |
| Chunks containing `View/Hide View/Hide` boilerplate | 235 |
| Confirmed mid-word splits between consecutive chunks | 20+ |
| Chunks ending without sentence terminator | ~1,200 (many are table rows; some are real truncations) |
| Pages where page-widget vs manifest breadcrumb disagree | 44 / 1,202 |
| Transmittal log pages | 13 (`Transmittals__TU_*.json`) |
| Online Forms catalog pages | 8 (the Online Forms book minus `View and Print Online Forms`) |
| Cross Program Forms catalog/table-only pages | TBD — to be hand-curated |

## Phase 1: Parser-layer cleanup

**File**: `rag/olg/parser.py`

### 1.1 Strip JS toggle artifacts

The MadCap Flare scrape captured the literal text of expand/collapse button
labels. The mechanism defaults to "expanded" so any content under those toggles
was already extracted into the section text — only the labels themselves are
garbage.

Strings to strip (case-insensitive, possibly doubled):
- `View/Hide View/Hide`
- `view/hide view/hide`
- `View/Hide`
- `Show All` / `Hide All` / `Expand All` / `Collapse All`
- `Subscribe`
- `Print Topic` / `Print this page`
- `Loading...`

Approach: text-substitution on extracted section text (whitespace-aware) before
the section dict is returned. Keep the substitution table small and explicit.

**Not stripped**: "Click here" / "click here" — verified 2026-04-29 against all
15 occurrences. They are hyperlink anchor text inside real prose ("For more
info, click here.") not button labels. Stripping would mutilate sentences. The
URL the link points to is captured separately in §1.2.

### 1.2 Carry hyperlink targets through to chunk metadata

The parser already extracts page-level `internal_links`. Extension: pass link
data through to chunks as metadata so the URL travels with the chunk text,
even when the prose says "click here" with no inline URL.

Approach:
- During section extraction in the parser, record links as they appear inside
  each section, keyed to the section.
- During chunking, attach an `outbound_links` array to each chunk's metadata
  containing every link that appears in that chunk's text:

```json
"metadata": {
  ...,
  "outbound_links": [
    {"text": "click here", "href": "https://.../schedules"},
    {"text": "Verification Chart", "href": "https://.../VerifChart.htm"}
  ]
}
```

Rationale: an agent that retrieves the chunk "FNS has published the Monthly
Issuance Schedule. Click here to view the schedules." gets the URL via
metadata and can follow it. Inline URL injection (`[click here](url)`) was
considered and rejected — Ben's preference is metadata-only so the
embedding text stays prose-clean.

### 1.3 Lift "Related Topics" out of section content

Detect the section whose heading matches `^Related Topic` (case-insensitive)
during section extraction. Rather than emit it as a section dict, capture its
internal links into a new top-level field on the page record:

```json
{
  "title": "...",
  "sections": [...],          // no longer includes Related Topics
  "tables": [...],
  "internal_links": [...],    // existing — page-wide
  "related_pages": [          // NEW — links from the Related Topics block
    {"text": "Receiving Calls in the Phone Queue", "href": "https://..."}
  ]
}
```

Rationale: cross-references serve to connect pages; that's their job.
Embedding the link text inside fuzzy similarity search is the wrong tool.
Putting the relationships in metadata makes them queryable directly later.

The current `merge_small_sections()` rule that preserves "Related Topics" as
its own chunk gets removed.

### 1.4 Accept duplicate-page reality

44 / 1,202 pages have a page-widget breadcrumb that disagrees with the
manifest's TOC breadcrumb. Four sub-patterns surfaced (see `findings.md`):

- **Pattern A** (~8 pages): same file in two real books — e.g.
  `BPp_Proc_Unread_Doc` lives under both BP/Procedures and Forms/Cross
  Program Forms. Accept; we're not deduplicating source content.
- **Pattern B** (12 pages, `EAEDC__Views__*`): EAEDC pages tagged in the TOC
  under TAFDC. Known content-merge work in progress at the OLG source. Use
  the page widget — page is EAEDC, respect that.
- **Pattern C** (15 pages, `NoticeForms__NF_*`): same content reachable via
  both Forms/Cross Program Forms and Notices/Forms/Cross Program books.
  Treat as duplicates; the catalog/table-only exclusion logic in §2 must
  cover the Notices/Forms book too.
- **Pattern D** (~5 pages): TOC adds a depth level the page widget omits
  (e.g. `BPov_BP` is the top-of-section page for BP itself). Page widget is
  canonical; ignore the TOC depth.

For all four: use the page-widget breadcrumb as the canonical
`hierarchy_path`. We considered an `also_under` metadata field for storing
the alternate path; deferring that — the only pattern where it would have
real retrieval value is A (8 pages), and Phase C exclusions will eliminate
most of the duplicate-path cases at the source. If retrieval misses surface
later, revisit.

## Phase 2: Hierarchy-aware chunker

**File**: `rag/olg/chunker.py` — replace `split_large_section()` with a
hierarchy-aware splitter analogous to CMR's `split_with_hierarchy()`, AND
fix `merge_small_sections()` so it stops crossing heading boundaries.

(Phase 2 and 3 swapped 2026-04-29 — splitter rewrite addresses the most
visible problem (mid-word table splits) and is independent of exclusions.)

### 2.0 Cross-level merge protection

The current `merge_small_sections()` blindly forward-merges any sub-MIN_CHUNK
section into its neighbor regardless of heading level. Concrete bug
(`COVID_ProcPandUCInc`): H2 "Pandemic UC Types" had only intro text (<MIN),
so it merged forward into H3 "PUA" — the H3 heading became a bare line in
the merged chunk's body, and the chunk inherited the H2 heading. **434 of
6,785 chunks** show this pattern.

Original instruction (Ben, pre-compact): *"we don't want text from two
subsections in one chunk. We don't want two sections in one chunk. Small
chunks are fine, no onus to fill them."*

**Rule**: a section may merge with a neighbor only when one side is
heading-less (level 0 — intro before the first heading). Any merge that
would combine two distinct H2s, two distinct H3s, or an H2 with its child
H3 is rejected; the smaller section stays small.

This means: an H3 that's only 80 chars stays an 80-char chunk. The chunk
is small — fine. The chunk's heading and parent_heading still identify
exactly what subsection it belongs to.

**Metadata addition**: each chunk also carries `parent_heading`. For an H3
chunk, this is the H2 immediately above it in the parser's section list
(walking backward to find the most recent level-2 with the same parent
page). For an H2 chunk, `parent_heading` is null. The context prefix uses
this when present:

```
"SNAP > Eligibility > [Page Title] > Pandemic UC Types > PUA"
```

instead of just

```
"SNAP > Eligibility > [Page Title] > PUA"
```

**Implementation note**: the parser already emits sections with `level` in
`{0, 2, 3}` and adjacent-in-list-order means adjacent-in-document. So
walking the section list and tracking "most recent H2" is enough — no
parser changes required. H4/H5/H6 verified absent in OLG (0 occurrences
across sampled pages 2026-04-29).

### 2.1 Split-priority order

When a section exceeds `MAX_CHUNK_SIZE` (1,500 chars), choose break points
in this priority:

1. **Table row boundaries**: any line matching `^\|.*\|$` is a table row.
   Inside a table block, prefer breaks between rows. Never break inside a
   row.
2. **Numbered/lettered list items**: lines starting with `^\d+\.\s`, `^\(\d+\)`,
   `^[A-Z]\.\s`, `^- ` (bullet). Prefer breaks at item boundaries.
3. **Paragraph boundaries**: `\n\n`.
4. **Sentence boundaries**: regex `(?<=[.?!])\s+(?=[A-Z])`.
5. **Hard character split** at TARGET_CHUNK_SIZE — last resort, log a warning
   so we can see if it's still happening.

### 2.2 Continued-table headers

When a table is split across chunks, the second chunk should begin with the
table's header row repeated, so the chunk standalone makes sense. The
Verification Chart is the canonical example of this need.

The current "(continued)" suffix on the heading stays, but additionally the
table portion of the chunk gets its header row prepended.

### 2.3 Manual treatment for the Verification Chart

`Vers_Types_VerifChart.json` is the largest and most policy-critical table
in the OLG. Even with hierarchy-aware splitting, this one chart deserves a
manual review pass — confirm the splits land on logical row groupings (e.g.
all "Identity" rows in one chunk, not split), and that each chunk has the
header row + maybe a small prose preamble explaining what the chart is.

**Driver**: Claude does the first pass. Approach:

1. Read `index/olg/scraped_pages/CrossProg__Verifications__Vers_Types_VerifChart.json`
   to understand the full table — count rows, identify the topical groupings
   (Identity, Income, Citizenship, etc.).
2. Decide chunk groupings manually — aim for ~6-10 chunks of cohesive subject
   matter rather than letting the splitter slice arbitrarily.
3. Produce a draft set of chunks with: small prose preamble per chunk
   ("Verification Chart — Identity rows"), the table header row, then the
   body rows for that grouping.
4. Show Ben the draft for review before locking in. Ben edits if needed.
5. Implementation: store the manual chunking as a static override in
   `rag/olg/chunker.py` (or a sibling `chunker_overrides.py`) that bypasses
   `split_large_section()` for this one URL.

## Phase 3: Page-level exclusions

**File**: new `rag/olg/page_excludes.py` or constant in `chunker.py`

A hand-curated exclusion list applied during chunking. We chose manual
curation over programmatic detection because the volume is small (~30 pages)
and the cost of misclassifying a real policy page is much higher than the
cost of the human review.

### 3.1 Transmittal logs (13 pages)

Exclude every URL matching `WebHelp/Transmittals/TU_*.htm`. These are
chronological tables of policy changes — useful as a separate artifact, not
useful as RAG retrieval surface for policy questions.

### 3.2 Online Forms book (8 of 9 pages)

Exclude every page in the "Online Forms" TOC section *except*
`Forms/locate_view_and_print_online_forms.htm`. The eight excluded pages are
pure form catalogs (Brochures, Cross Programs forms list, EAEDC forms list,
Flyers, Non Program forms list, SNAP forms list, TAFDC forms list, Voter
Registration forms list).

### 3.3 Cross Program Forms book + Notices/Forms book — hand-curated

Two TOC books contain catalog/table-only pages mixed with real guidance:

- **Forms / Cross Program Forms** (16 pages — the `Forms__*` set listed in
  `policy_toc.json` under that section)
- **Notices/Forms / Cross Program** (15 pages — the `NoticeForms__NF_*` set,
  Pattern C duplicates of the same content)

Ben will spot-check each page and produce an exclusion list. The 16 Cross
Program Forms titles to review:

```
EBT Replacement Pilot Forms
Calculation Page - Overview
Address Change Cover Letter
Client Assistance Coordinator Letters
Cross Programs - Notices
EAEDC Calculation Page Example
Letter Request
Pregnancy Information Update
Processing Unreadable Documents
Returned Document Notice
Revised Calculation Page
Rights and Responsibilities
SNAP Calculation Page Example
SNAP - Notices
TAFDC Calculation Page Example
TAFDC, EAEDC and SNAP: Using Document Processing Center for Mailing Address Form
```

The 15 NoticeForms equivalents share the same titles (Calculation Page
examples, Notices, Letter Request, etc.) — when a Cross Program Forms page
is excluded as catalog/table-only, exclude its NoticeForms duplicate too.

Output: a list of URLs / file basenames to exclude, hand-edited into
`page_excludes.py`.

### 3.4 Pure-acronym chunks

Currently one confirmed: `sec__BP__Overview__BPov_NG_Overview__004` is a
list of 30+ acronyms with no body text. Scan for any others (sections that
are only short tokens with no prose). Likely to be 1-3 chunks total.

Approach: at chunk creation, drop section chunks where >80% of tokens are
short capitalized acronyms and there is no full sentence. Or — simpler — add
the chunk IDs to an explicit excluded-chunk list. Pick simpler if the count
is small.

## Phase 4: Per-chunk position metadata

**File**: `rag/olg/chunker.py` — extend `create_section_chunks()`

Add three new fields to chunk metadata:

```python
"hierarchy_path": "SNAP > Eligibility Requirements > Students > Documentary Evidence...",
"chunk_n": 3,            # 1-indexed position within this section's split sequence
"chunk_total": 7,        # total chunks produced from this section
```

`hierarchy_path` is just the breadcrumb chain (page widget version, since it
matches the page's self-identification) joined with ` > `. Same string that
goes into the context prefix today, but stored as structured metadata.

`chunk_n` / `chunk_total` describe position within the *section's* split
sequence — so a section that didn't need splitting is 1/1. Different from
the existing `chunk_index` field, which is page-wide.

### 4.1 No `also_under` field

Considered storing a secondary breadcrumb path for the 44 pages where the
manifest TOC disagrees with the page widget. Decision (2026-04-29): skip.

Reasoning per pattern (see §1.4):
- Pattern A (8 pages, real dual-book listing): would have value, but small
  population and Phase 3 exclusions remove most of the affected pages.
- Pattern B (12 pages): the alternate path is *wrong* (EAEDC pages tagged
  TAFDC) — adding it would mislead retrieval.
- Pattern C (15 pages): all duplicates excluded in §3.3.
- Pattern D (~5 pages): alternate path is just verbose; no retrieval gain.

Use the page-widget breadcrumb as the canonical `hierarchy_path`. Revisit
if specific retrieval misses surface against Pattern A pages later.

## Phase 5: Consumer display updates

**Files**: `rag/query.py`, `tools/synthesis.py`,
`ui/templates/partials/answer.html`

Mirror the CMR Phase 8 work:

- `rag/query.py` CLI — show `Path:` and `Part: N of M` lines for OLG results
- `tools/synthesis.py` — include `Subsection:` and `(part N of M)` in
  citation headers fed to Claude
- `ui/templates/partials/answer.html` — render position info in the result
  header

This is small mechanical work once Phase 4 metadata exists.

## Phase 6: Verification, then re-embed

### 6.1 Verification

Before re-embedding the whole corpus:

- Re-run the chunker, write fresh `section_chunks.json`
- Spot-check 20 chunks: verify no `View/Hide`, no mid-word splits, position
  metadata present
- Run a 20-question retrieval benchmark *against the existing embeddings* —
  wait, can't, because the chunk text changed. Instead, run a small
  cost-controlled re-embed against just one program (e.g. Cross Programs
  ~600 chunks) and benchmark, before committing to full re-embed.

### 6.2 Re-embed

Hold for Ben's explicit go. Estimated cost on `voyage-3` for ~6,500 chunks
is well under $1, but the time and the destructiveness of overwriting the
existing collection both mean we don't run it casually.

Command shape: `python rag/embedder.py --source olg --force`

## Estimated effort

| Phase | Effort | Risk |
|---|---|---|
| 1. Parser cleanup | Small | Low |
| 2. Hierarchy splitter | Medium | Medium — splits affect every chunk |
| 3. Page exclusions | Small (15-30 min hand curation + small code) | Low |
| 4. Position metadata | Small | Low |
| 5. Consumer display | Small | Low |
| 6. Verification + re-embed | Medium | Low — re-embed itself is mechanical, but verification gates it |

Total: a few sessions of focused work. Comparable to the CMR cleanup arc.

## Resolved questions (2026-04-29)

1. **"Click here" strip** — resolved: do NOT strip. All 15 occurrences are
   real prose. Capture URL as metadata instead (§1.2).
2. **`also_under` metadata** — resolved: skip (§4.1).
3. **Verification chart manual pass** — resolved: Claude drives the first
   pass, shows Ben for review (§2.3).

## Approval gates

Phases 1-5 can land in one branch. Phase 6 (re-embed) is gated on Ben's
explicit go after verification.
