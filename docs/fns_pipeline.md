# FNS Handbook 310 — RAG Pipeline & Policy Comparator

## Project Goal

Build a RAG system for the USDA FNS Handbook 310 (the federal SNAP Quality Control
standard), and a comparator agent that identifies meaningful policy differences between
the federal handbook and the Massachusetts DTA Online Guide (OLG).

The FNS RAG is an independent system that mirrors the OLG RAG architecture. The
comparator bridges both systems but neither depends on the other for core functionality.

## Source Document

- **Document**: FNS Handbook 310, "SNAP Quality Control Review Handbook"
- **Edition**: October 2025, through QC PM 26-04, Change 2 (January 13, 2026)
- **File**: `FNS Handbook 310 1.13.26.pdf` (4.8 MB, 306 PDF pages)
- **Content**: 289 content pages, ~96,500 words, 14 chapters, 483 numbered sections
- **Location**: `../new_olg_rag/FNS Handbook 310 1.13.26.pdf`

## Related Resources

- **PRD**: `../tasks/0002-prd-fns-handbook-rag.md`
- **Brainstorm**: `../tasks/0002-brainstorm-fns-handbook.md`
- **OLG RAG project**: `../new_olg_rag/PROJECT.md`

## Architecture

- **Sibling project** to `new_olg_rag/` — independent directory, shared ChromaDB
- **Shared ChromaDB**: FNS collections (`fns_chapters`, `fns_sections`) live alongside OLG
  collections (`pages`, `sections`) in `new_olg_rag/chroma_db/`
- **Comparator** lives here, imports OLG query API when needed
- **No dependency from OLG → FNS**: The OLG RAG works standalone. Only the comparator
  (in this project) crosses the boundary.

---

## Phase 1: PDF Parsing (COMPLETE)

### What was built

`fns_parser.py` — Extracts structured sections from the handbook PDF using pdfplumber.

**Process**:
1. Open PDF with pdfplumber
2. Extract text from content pages (18–298), skip cover/TOC/appendices/index/back cover
3. Strip page headers ("FNS HANDBOOK 310") and footers (page numbers like "10-4")
4. Clean special characters (`\uf0d8` Wingdings bullet → `- `)
5. Detect section boundaries via numbered section regex (`^\d{3,4}(\.\d+)*\s+[A-Z]`)
6. Absorb multi-line section headings (continuation lines before body text starts)
7. Handle 47 side-by-side example box pages with column-aware extraction
8. Extract tables via `pdfplumber.extract_tables()`
9. Extract cross-references ("See Section 622", "Chapter 7") as normalized metadata
10. Build section hierarchy from numbering scheme (chapter, level, parent)
11. Output one JSON file per section to `parsed_sections/`

### Parse results (2026-03-07)

| Metric | Value |
|---|---|
| Sections parsed | 482 (of 483 in PDF — 1 empty heading skipped) |
| Clean sections | 422 (88%) — readable, no garbling |
| Flagged (side-by-side) | 60 sections across 47 pages |
| Column separation succeeded | 51 of 60 — example text extracted to separate field |
| Column separation failed | ~9 — still interleaved, flagged for manual review |
| Sections with tables | 22 |
| Sections with cross-references | 154 |
| Short sections (<100 chars) | 27 (mostly umbrella headings with subsections) |

### Per-section JSON structure

```json
{
  "source": "FNS Handbook 310",
  "source_edition": "October 2025, Change 2 (January 13, 2026)",
  "chapter": 10,
  "chapter_title": "Income",
  "section_number": "1021.1",
  "section_title": "Positive Allegation",
  "level": 3,
  "parent_section": "1021",
  "text": "Positive Allegation. When the household states...",
  "tables": [],
  "cross_references": ["Chapter 10", "Section 622"],
  "pdf_pages": [195],
  "handbook_pages": ["10-4"],
  "flags": [],
  "example_text": null
}
```

**Fields**:
- `level`: 0 = chapter heading (x00), 1 = major section (x10/x20), 2 = section (x11),
  3 = subsection (x.1)
- `parent_section`: e.g., "1021" for "1021.1", "1020" for "1021", "1000" for "1020"
- `flags`: `["side_by_side_page"]` if the section spans a page with example boxes;
  `["manual_review_needed"]` if column separation failed (currently 0 — all failures
  are caught by the `side_by_side_page` flag)
- `example_text`: Separated right-column text from side-by-side pages (when column
  separation succeeded), or absent

### Key design decisions (Phase 1)

1. **Section detection via regex, not PDF structure**: The PDF has no bookmarks or tagged
   structure. Section boundaries are detected by the numbered pattern (`100 GENERAL.`)
   appearing at the start of a line. Validated against known chapter ranges to avoid
   matching inline references like "See Section 622".

2. **Multi-line heading absorption**: Section headings in the PDF can span 2-3 lines.
   The parser reads continuation lines until it hits a period-followed-by-body-text
   pattern, a blank line, a bullet point, or the next section heading.

3. **Column-aware extraction for side-by-side pages**: Uses pdfplumber word-level
   x-coordinates to separate left (policy) and right (example) columns. The boundary
   is the median gap position. When separation works, example text goes to a separate
   `example_text` field. When it doesn't, the section is flagged.

4. **47 side-by-side pages, not 11**: Initial analysis found 11 pages with obvious
   two-column layout. Deeper detection (gap analysis with threshold >= 3 gap lines
   per page) found 45, plus 2 more added manually. The config lists all 47.

5. **Cross-references normalized**: Raw matches like "See Section 622", "see\nSection 622",
   "Section 622" are all normalized to just "Section 622". Chapter references normalized
   to "Chapter N".

6. **One JSON file per section**: Filename format `ch{NN}_{section_number}.json` (e.g.,
   `ch10_1021_1.json`). Easy to inspect, debug, and re-process individual sections.

### Known limitations

- **~9 sections with garbled text**: Side-by-side column separation failed on these.
  They are flagged but the text is interleaved. Most are in Chapters 6 and 11.
  For RAG, the garbled text still contains correct keywords; for human reading,
  these would need manual cleanup.
- **1 section not parsed**: One section heading in the PDF had no body text and was
  skipped by the empty-section filter. This is the correct behavior.
- **Example boxes are illustrative, not policy**: The `example_text` field contains
  examples that help explain the policy but aren't the policy rules themselves.
  The comparator should focus on the `text` field.

---

## Phase 2: Chunking & Embedding (NOT STARTED)

### Plan

Mirror the OLG chunker/embedder architecture:

1. **Two-tier chunks**: Chapter-level documents (~14) for broad topic matching +
   section-level chunks (~482, after merge/split) for specific answers
2. **Merge/split rules**: Same as OLG — merge sections <200 chars with next sibling,
   split sections >1,500 chars at paragraph boundaries
3. **Context prefix**: `"FNS 310 > Chapter 10: Income > 1021.1 Positive Allegation"`
4. **Tables rendered inline** as pipe-delimited text
5. **Embed with Voyage AI** (voyage-3) into shared ChromaDB
6. **Collections**: `fns_chapters` and `fns_sections` (alongside OLG's `pages` and `sections`)

### Modules to build

| File | Purpose |
|---|---|
| `chunker.py` | Read `parsed_sections/`, produce chunks with merge/split |
| `embedder.py` | Call Voyage AI API, store in ChromaDB |
| `query.py` | Search interface — CLI, Python API, JSON output |

---

## Phase 3: Comparator Agent (NOT STARTED)

### Plan

Build `comparator.py` that:
1. Iterates through FNS sections (configurable by chapter)
2. Uses each section's text as a query against the OLG RAG
3. Sends FNS text + OLG results to Claude for comparison
4. Records: match / minor_difference / major_difference / no_state_equivalent
5. Outputs structured report (JSON + Excel)

### Key decisions still needed

- Comparison prompt design (what types of differences to look for)
- Whether to filter OLG to SNAP-only or include cross-program
- Model choice (Haiku for bulk, Sonnet for flagged items?)
- Report format and organization

---

## Chapter breakdown (for reference)

| Ch | Title | Sections | Comparison relevance |
|---|---|---|---|
| 1 | Introduction | 27 | Low — definitions, admin |
| 2 | Basic Review Process | 29 | Low — QC procedures |
| 3 | Case Record Review | 23 | Low — QC procedures |
| 4 | Field Investigation | 32 | Low — QC procedures |
| 5 | Verification & Documentation | 20 | Medium |
| 6 | Error Determination | 14 | Low — QC-specific |
| 7 | Review Procedures / Cert Systems | 68 | **High** |
| 8 | Non-Financial Eligibility | 50 | **Very high** |
| 9 | Resources | 28 | **Very high** |
| 10 | Income | 83 | **Very high** |
| 11 | Deductions | 62 | **Very high** |
| 12 | Making the Review Decision | 15 | Low |
| 13 | Negative Action Record Reviews | 16 | Medium |
| 14 | Informal Resolution & Arbitration | 15 | Low |

---

## Running the tools

```bash
# Phase 1 (complete)
python fns_parser.py                    # Parse full handbook
python fns_parser.py --chapter 10       # Parse one chapter
python fns_parser.py --pages 195-200    # Parse specific PDF pages
python fns_parser.py --dry-run          # Show sections found, don't write files

# Phase 2 (not yet built)
python chunker.py                       # Generate chunks from parsed sections
python embedder.py                      # Embed chunks and store in ChromaDB
python query.py "income deduction"      # Search FNS handbook

# Phase 3 (not yet built)
python comparator.py                    # Run comparison against OLG
python comparator.py --chapter 10       # Compare one chapter
```

---

## Project files reference

```
fns_handbook_rag/
├── PROJECT.md              ← this file
├── requirements.txt
├── config.ini              ← API keys, paths, settings (gitignored)
├── .gitignore
│
├── fns_parser.py           ← PDF → structured JSON sections (Phase 1, COMPLETE)
├── chunker.py              ← Sections → chunks with merge/split (Phase 2)
├── embedder.py             ← Chunks → Voyage AI → ChromaDB (Phase 2)
├── query.py                ← Search interface (Phase 2)
├── comparator.py           ← FNS vs OLG comparison agent (Phase 3)
│
├── parsed_sections/        ← 482 JSON files (one per handbook section)
│   └── ch{NN}_{section}.json
├── chapter_chunks.json     ← Chapter-level documents (Phase 2)
├── section_chunks.json     ← Section-level chunks (Phase 2)
└── reports/                ← Comparison output (Phase 3)
```

Dependencies: `pdfplumber`, `chromadb`, `voyageai`, `anthropic`, `openpyxl`
