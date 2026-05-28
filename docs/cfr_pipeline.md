# 7 CFR — RAG Pipeline

## Source Material

- **What**: 7 CFR Parts 271-275, 280, 292 (federal SNAP regulations under the Food and Nutrition Act)
- **Format**: 7 PDFs, 517 pages, 118 regulation sections after parsing
- **Programs covered**: SNAP (the federal codification), Summer EBT (Part 292), and federal QC procedure (Part 275)
- **Citation format**: `7 CFR § 273.9(d)(6)(ii)`
- **Location**: `raw/cfr/*.pdf`

7 CFR is the federal statutory codification — the law that 106 CMR (state regulation) implements and the OLG (worker guide) explains. FNS Handbook 310 is a separate federal source for QC procedure; it overlaps Part 275 but is more operationally detailed.

```
7 CFR (federal regulation)     ← THE LAW
    ↓ implements
106 CMR (state regulation)     ← Massachusetts implementation
    ↓ explains
OLG (staff guide)              ← What workers follow

FNS 310 (QC handbook)         ← Federal QC procedure (separate chain)
```

## Pipeline Overview

| Stage | Module | Input | Output |
|-------|--------|-------|--------|
| Parse | `rag/cfr/parser.py` | 7 PDFs | 118 JSON files in `index/cfr/parsed_sections/` |
| Chunk | `rag/cfr/chunker.py` | 118 JSON files | `part_chunks.json` (7) + 3 section variants |
| Embed | `rag/embedder.py --source cfr` | `section_chunks_context.json` | ChromaDB collections `cfr_parts`, `cfr_sections` |
| Query | `rag/query.py --source cfr` | User query | Ranked results with metadata |

---

## Phase 1: Parsing (COMPLETE — committed `7235be8`)

### What the parser does

1. Opens each of 7 CFR PDFs with pdfplumber
2. Strips a 3-line page header and 1-line footer per page (vs CMR's 1-line header)
3. Detects the TOC boundary using `§ {part}.{section}` regex with first-duplicate detection
4. Pulls the part title from line 2 of the raw first page (eCFR convention)
5. Extracts subpart structure from the first 3 raw TOC pages (Parts 273, 275, 292 have subparts)
6. Strips amendment notes — both `[Amdt. ...]` and `[NN FR ...]` patterns
7. Filters out `[Reserved]` sections
8. Outputs one JSON file per section

### Per-section JSON structure

```json
{
  "source": "7 CFR",
  "part": 273,
  "part_title": "Certification of Eligible Households",
  "section_number": "273.9",
  "section_title": "Income and deductions",
  "subpart_letter": "D",
  "subpart_title": "Eligibility and Benefit Levels",
  "program": "SNAP",
  "text": "...",
  "tables": [],
  "cross_references": ["§ 273.9", "§ 273.10"],
  "pdf_file": "7-cfr-part-273.pdf"
}
```

### Parse results

| Metric | Value |
|--------|-------|
| PDFs processed | 7 |
| Total sections | 118 |
| Sections excluded | 1 (`271.8` — OMB control number table, no policy content) |

### Key design decisions

1. **3-line header strip vs CMR's 1-line.** Every CFR page has the publication header (`7 CFR Part 273 (up to date as of …)`) plus a breadcrumb line (`7 CFR 273.9(d)(4)(i)`) plus a section-position line. Stripping all three avoids polluting embeddings with breadcrumb noise.

2. **TOC boundary via duplicate detection.** Same approach as CMR: § markers appear in both the TOC and the body; the first repeated section number marks where the body starts. Reliable across all 7 PDFs.

3. **Amendment note stripping at parse time, not chunk time.** Patterns like `[Amdt. 132,43 FR 47882, Oct. 17, 1982, as amended by Amdt. 216,47 FR 23461, May 28, 1982]` are noise for retrieval but useful for tracing regulatory history. Decision: strip from text. Future option to preserve in metadata if regulatory history matters.

4. **Subpart extraction from raw TOC.** Subpart structure (`Subpart A`, `Subpart B`, …) is announced in the TOC, not on body pages. Parser reads the first 3 pages raw to capture subpart titles before chunking.

5. **`[Reserved]` filtering.** CFR has reserved-but-empty section slots. These have a heading like `§ 271.5 [Reserved]` and no body. Filter at parse time so they don't pollute the chunk count.

---

## Phase 2: Chunking (COMPLETE — committed `7235be8`)

CFR sections are dramatically larger than CMR sections (§ 273.9 alone runs 20+ pages of nested subitems vs CMR's median 884 chars). The chunker is hierarchy-aware, with several CFR-specific design decisions captured below.

### Constants

- `MIN_CHUNK_SIZE = 200`, `MAX_CHUNK_SIZE = 1500`, `TARGET_CHUNK_SIZE = 1000`
- Hierarchy profile: `(a)(1)(i)(A)` — inverted from CMR's `(A)(1)(a)1.`

### Three output JSON variants

The chunker produces three section-level JSON files. Choose one for embedding.

| File | Top-level marker | Hierarchy display | Parent context |
|------|------------------|-------------------|----------------|
| `section_chunks.json` | `(a)`, `(b)` | top-level only | none |
| `section_chunks_fullpath.json` | `(a)(1)(iv)` | full nesting path | none |
| `section_chunks_context.json` | full path | full nesting path | **ancestor intros prepended** |

**`section_chunks_context.json` is the chosen embedding variant** — it gives the best retrieval semantics. A chunk starting at `(iv)` under `(b)(1)` is prepended with the ancestor intros so the embedding captures setup like:

```
(b) Definition of income.
(1) Earned income shall include:
(iv) [chunk body…]
```

Without this, deeply nested chunks lose the semantic context that defined the list they live in.

### Key chunker design decisions

1. **Marker-only hierarchy labels.** `classify_line()` returns just the marker (`(a)`, `(1)`, …) not the full line text. CFR markers introduce regulatory prose, not concise topic headers like CMR.

2. **Dedicated definition chunker.** `chunk_definitions()` is a fully separate code path from `split_with_hierarchy()`. Definitions have a fundamentally different structure — `term → description`, not nested hierarchy. Detection layers:
   - **Primary**: `_DEF_VERBS` patterns — `{Term} means`, `{Term} refers to`, `{Term}, as used in this part…`
   - **Manual list**: `NON_VERB_DEFINITIONS` for ~8 entries that lack verb patterns (e.g., "Assessment", "Firm.", "2 CFR part 200")
   - **Override list**: `TERM_NAME_OVERRIDES` for entries where the regex captures more than the actual term name (e.g., "Adequate notice in a periodic reporting system…" → "Adequate notice")

3. **Top-level marker break — UNCONDITIONAL.** When a level-1 marker `(a)`, `(b)`, `(c)` arrives and the accumulator has any content, the chunker ALWAYS breaks. No size gate. This eliminates `(a)(4)` bleeding into `(b)` cross-contamination at the cost of ~85 extra chunks. The user's hard rule was "logical chunks that begin and end cleanly" — the size cost was worth the cleanliness.

4. **Hierarchy boundary splitting on must-break.** When a chunk exceeds MAX_CHUNK_SIZE, `_split_at_hierarchy_boundary()` scans backward for the last hierarchy marker and splits before it (the marker becomes the start of the next chunk). Falls back to `_split_at_line_boundary()` (sentence-boundary scan) only when there's no marker — single long paragraphs. This reduced mid-sentence splits from 332 to 4 unavoidable cases (semicolon-list runs in 272.2 and 273.10).

5. **Parent context injection — bug fix.** `hierarchy_intros` is tracked in `split_with_hierarchy()` and snapshotted at chunk **start** (not emit time, which was the bug). `_extract_intro()` takes the first sentence/clause (up to `. ; :`) or truncates at 150 chars. `build_parent_context_version()` post-processes: finds first body marker, prepends ancestor-level intros for each path level above.

6. **Excludes**:
   - `SECTION_EXCLUDES = {"271.8"}` — OMB control number table, no policy content
   - `SUBSECTION_EXCLUDES = {"272.1": [regex for (g) amendment history]}` — strips 142k chars of procedural noise

### Chunk statistics

| Metric | Value |
|--------|-------|
| Part documents | 7 |
| Section chunks | 1,623 |
| Mid-sentence splits | 4 (down from 332) |

---

## Phase 3: Manual Table Cleanup (COMPLETE — committed `7235be8`)

CFR PDFs contain 16 multi-column tables that pdfplumber's table extraction renders as garbled prose. Rather than build a custom table parser, the tables were rewritten as flowing prose directly in the parsed JSONs (`index/cfr/parsed_sections/cfr*.json`).

| Section | Tables | What was rewritten |
|---------|-------:|---------------------|
| 273.18 (Claims) | 9 | Types of claims, calculating, referral, pre-establishment, write-offs, payment forms, allotment reduction, EBT collection, retention rates |
| 275.3 (Validation Reviews) | 3 | Federal subsample formulas (active and negative cases) |
| 275.11 (QC Sampling) | 4 | Active and negative case sample size formulas |

### Patterns used for prose rewrites

- "if X / then Y / unless Z" decision tables → "As a State agency, if X, then Y, unless Z." sentences
- "method / However" 2-column tables → "Method; however, caveat." sentences
- Formula tier tables → "for an N of [range], the n = [value]; for N of [range], n = [formula]" semicolon-separated single sentences

### Recovery procedure

If parsed JSONs are ever regenerated, the table fixes will be lost. Re-apply via patch scripts (those scripts were deleted after commit but can be rebuilt from the user-validated rewrites — search the conversation history of session `f525b70b-d02c-45e7-9d6b-8fe5c041335b` for "I'll paste the content as it is intended to be read" exchanges).

### Character normalization

Two intentional substitutions were made during patching:
- U+2032 PRIME (`n′`) → apostrophe (`n'`) — for searchability (users type apostrophe, not prime)
- U+2212 MINUS SIGN → hyphen-minus — for consistency with how users write formulas

---

## Phase 4: Program Labels (COMPLETE — committed `7235be8`)

CFR is divided into operational domains. Section-level labels in `metadata.program` enable audience-based filtering.

| Label | Chunks | Sections | Composition |
|-------|-------:|---------:|-------------|
| SNAP | 951 | 41 | 271.2 + 272.8-14/272.16+ + 273 (all) |
| Summer-EBT | 252 | 28 | 292 (all) |
| QC | 159 | 24 | 275 (all) |
| Administration | 137 | 15 | 271.1/.3-.9 + 272.1-.7/.15 |
| Issuance | 123 | 8 | 274 (all) |
| Disaster | 1 | 1 | 280 (all) |

### Implementation

- `SECTION_PROGRAMS` dict with explicit overrides for the 271/272 splits (sections that don't follow the part-default rule)
- `DEFAULT_PROGRAM_BY_PART` dict for the rest
- `get_program(section_number, part_num)` helper applies the override-then-default rule
- Part-level docs use `get_part_program()` which returns the dominant section's label

### Why section-level (not part-level)?

Part 271 mixes definitions (relevant to all SNAP work) with administrative provisions (governance, OMB controls). Part 272 mixes state-plan administrative requirements with operational SNAP rules. A part-level label would force users into a coarser granularity than the source actually supports.

### Filter rationale by audience

- **SNAP workers** querying eligibility: include `SNAP` only (or `SNAP + Issuance` for finance work)
- **Policy team**: include `SNAP`, optionally `Administration` for governance work
- **FNS QC**: include `QC`
- **Author pipeline**: include `SNAP` only (don't pollute OLG voice with administrative content)
- **Comparator**: no filter (needs everything for cross-references)

---

## Phase 5: Embedding (COMPLETE — committed `4163f57`)

- Model: Voyage AI `voyage-3`
- Variant embedded: `section_chunks_context.json` (parent-context-prepended)
- Tokens: 548,944
- Cost: $0.033
- Collections: `cfr_parts` (7 docs), `cfr_sections` (1,623 chunks)

### One generic embedder change required

CFR section metadata includes a `hierarchy_intros: {}` dict field (used during chunking, retained for inspection). ChromaDB only accepts scalar metadata values. The embedder gained a generic dict/list → JSON-string serializer in the metadata flattening step alongside its existing None and bool handlers. Other sources benefit too: any future complex metadata is now safely passable through the embedder.

---

## Phase 6: Multi-source Integration (COMPLETE — committed `e034b0b`, `7f569e2`, `acf5ec2`)

### Query layer

- `rag/query.py --source cfr` works alongside `--source olg|fns|cmr`
- `has_program_filter: True`, `parent_id_field: "parent_part_id"`
- New formatter `_format_cfr_result()` displays § notation, Part / Subpart / Program / hierarchy_full_path
- `_print_info` (`--list-programs`) shows part breakdown plus the program-label distribution

### Synthesis layer (`tools/synthesis.py`)

- `SEARCH_POLICY_TOOL` enum extended to `["olg", "cmr", "fns", "cfr"]`
- New CFR branch in `format_results_for_prompt()` matching the CMR pattern with § notation and hierarchy
- CLI `--sources` choices include cfr

### UI

- `ui/search.py` `SOURCES` registry adds the cfr entry; the Ask form's source-checkbox row picks it up automatically
- Result-card and answer-evidence templates have CFR display branches
- Search export (`/search/export/{search_id}`) renders CFR citations as `7 CFR § 273.9 Income and deductions`
- Author research checkbox panel includes CFR; default sources are `[olg, cmr, fns, cfr]`

### Comparator L3 cross-check (`apps/comparator/comparator.py`)

CFR is added as an additional L3 cross-check **alongside** the existing CMR L3 — not replacing it. Each confirmed gap finding now carries verdicts from both:

- New prompt: `apps/comparator/prompts/layer3_cfr_validation.md`
- Classifications: `cfr_requires` / `cfr_allows` / `cfr_differs` / `cfr_silent` / `handbook_only`
- New functions: `query_cfr()`, `format_cfr_results_for_prompt()`, `run_layer3_cfr()`
- Pipeline: in the L3 phase, after CMR L3, run CFR L3 if `cfr_clients` is initialized
- Persistence: `_layer3_cfr` key in result JSON; new CSV columns `cfr_classification`, `cfr_section`, `cfr_note`
- HTML report: CFR Cross-Check detail block alongside CMR; "7 CFR Section" row in metadata sidebar
- Config: `cfr_max_results` in `[comparator]` (default 5)

The "comparator with CFR as the subject" alternative (replacing FNS as the input axis to find gaps in OLG against ALL federal SNAP regs) was deferred — bigger scope, defer until concrete need.

### QC analyzer cross-check (`apps/qc/qc_analyzer.py`)

Strict mirror of `run_cmr_check` / `run_fns_check`:

- New prompt: `apps/qc/prompts/qc_cfr_check.md`
- Classifications: `cfr_covers_topic` / `cfr_silent` / `cfr_differs`
- `run_cfr_check()` iterates Partial/Gap findings, queries CFR with `program=SNAP`, stores result as `_cfr_check`
- Sets `meta.phases.cfr_checked`
- UI: new POST `/qc/cfr_check` route, "CFR" button in qc.html action row, "Re-run CFR" button, CFR badge column (Covers/Silent/Differs), CFR Cross-Check detail block, "7" phase badge in analyses list, JS `CFR_CHECK_STEPS`
- Config: `cfr_check_model` in `[qc_analyzer]` (defaults to Haiku)

---

## Filter Design Decision (2026-04-30)

**No hidden defaults anywhere.** The principle:

- CLI: explicit `--program` / `--exclude-programs` flags
- UI: visible state via checkboxes/dropdowns; pre-fills are fine, but the user must always be able to see what's included or excluded
- Source modules (`query.py`, `synthesis.py`): no per-source automatic filtering

The driving concern is the "I'll forget" problem: if `--source cfr` silently excluded `Administration` and `QC` chunks, a user investigating an EBT card procedure overhaul would see "nothing in the CFR" when in fact Issuance content had been hidden. Better to require an explicit gesture every time.

The current `index.html` program dropdown (SNAP / TAFDC / EAEDC) is functional for CFR (SNAP filter matches SNAP chunks; TAFDC/EAEDC filters return zero, semantically correct) but limited — a future redesign should replace it with a per-source program checkbox panel. That work is not scoped yet.

---

## Commands

```bash
# Parsing
python rag/cfr/parser.py                    # Parse all 7 PDFs
python rag/cfr/parser.py --part 273         # Parse one part
python rag/cfr/parser.py --dry-run          # Show sections, don't write

# Chunking (produces all three JSON variants)
python rag/cfr/chunker.py
python rag/cfr/chunker.py --stats
python rag/cfr/chunker.py --preview 273

# Embedding (uses section_chunks_context.json)
python rag/embedder.py --source cfr --dry-run
python rag/embedder.py --source cfr
python rag/embedder.py --source cfr --force

# Querying
python rag/query.py "income deduction" --source cfr
python rag/query.py "summer ebt" --source cfr --collection parts
python rag/query.py "work requirements" --source cfr --program SNAP
python rag/query.py "income" --source cfr --exclude-programs "Administration,QC"
python rag/query.py --source cfr --list-programs
```

---

## File Inventory

| Part | PDF | Title | Pages | Sections | Chunks | Default Program |
|-----:|-----|-------|------:|---------:|-------:|-----------------|
| 271 | `7-cfr-part-271.pdf` | General Information & Definitions | 26 | 9 | 151 | Administration (most), SNAP (271.2 definitions) |
| 272 | `7-cfr-part-272.pdf` | State Agency Requirements | 88 | 18 | 146 | Administration / SNAP (mixed by section) |
| 273 | `7-cfr-part-273.pdf` | **Certification of Eligible Households** | **252** | **32** | **791** | SNAP |
| 274 | `7-cfr-part-274.pdf` | Issuance & Use of Benefits | 39 | 8 | 123 | Issuance |
| 275 | `7-cfr-part-275.pdf` | Performance Reporting | 50 | 24 | 159 | QC |
| 280 | `7-cfr-part-280.pdf` | Emergency Disaster Assistance | 1 | 1 | 1 | Disaster |
| 292 | `7-cfr-part-292.pdf` | Summer EBT Program | 61 | 31 | 252 | Summer-EBT |
| | | **TOTAL** | **517** | **123** | **1,623** | |

Note: 123 raw sections - 5 reserved/excluded = 118 chunked sections. The 1,623 chunks come from 118 sections distributed unevenly (Part 273 alone holds 791 chunks because of § 273.9 / § 273.7 / § 273.10 / § 273.18 size).

---

## Open Questions / Future Work

1. **Tree-aware splitting** — Deferred. Pin only if retrieval quality degrades on deeply nested § 273.9-style sections.
2. **CFR ↔ CMR mapping table** — Cross-source comparator support. § 273.9 (Income) ↔ 106 CMR 363/364; § 273.7 (Work) ↔ 106 CMR 362.300s; etc. Useful for gap-analysis triangulation but not yet built.
3. **Comparator with CFR as subject** — A separate run that walks CFR sections (instead of FNS Handbook 310 sections) to find OLG gaps against the full federal SNAP regs. 1,623 chunks vs FNS's 270 already-analyzed sections; whole new scope. Defer until concrete need.
4. **Program filter UI redesign** — Replace `index.html`'s single dropdown with per-source program checkbox panel. Honors the "no hidden defaults" principle while letting users compose include/exclude sets per source.
5. **Amendment notes as metadata** — Currently stripped at parse time. Could be preserved in a `metadata.amendment_history` field for users tracing regulatory provenance.

---

## Related Documentation

- Pre-implementation planning notes: [`docs/cfr_processing/notes.md`](cfr_processing/notes.md) (historical artifact, dated 2026-04-22; superseded by this doc)
- Other source pipelines: [`docs/olg_pipeline.md`](olg_pipeline.md), [`docs/fns_pipeline.md`](fns_pipeline.md), [`docs/cmr_pipeline.md`](cmr_pipeline.md)
- Comparator: [`docs/comparator.md`](comparator.md)
