# 106 CMR — RAG Pipeline

## Source Material

- **What**: Code of Massachusetts Regulations, Title 106 (Department of Transitional Assistance)
- **Format**: 18 PDFs, 342 pages total, ~592 regulation sections
- **Programs**: SNAP (chapters 360-367), TAFDC/EAEDC (chapters 701-708), Cross-Program (327, 343)
- **Citation format**: `106 CMR 362.330(A)(1)(a)`
- **Location**: `raw/cmr/*.pdf`

## Pipeline Overview

| Stage | Module | Input | Output |
|-------|--------|-------|--------|
| Parse | `rag/cmr/parser.py` | 18 PDFs | 592 JSON files in `index/cmr/parsed_sections/` |
| Chunk | `rag/cmr/chunker.py` | 592 JSON files | `chapter_chunks.json` (18) + `section_chunks.json` (1,275) |
| Embed | `rag/embedder.py --source cmr` | Chunk JSON files | ChromaDB collections `cmr_chapters`, `cmr_sections` |
| Query | `rag/query.py --source cmr` | User query | Ranked results with metadata |

---

## Phase 1: Parsing (COMPLETE)

### What the parser does

1. Opens each of the 18 CMR PDFs with pdfplumber
2. Strips page headers (`106 CMR: DEPARTMENT OF TRANSITIONAL ASSISTANCE`)
3. Detects the TOC boundary — the first duplicate section number marks where body content begins
4. Extracts sections using chapter-filtered regex (`^{chapter_prefix}.\d{3}: Title`) to avoid cross-reference false positives
5. Merges continuation pages (`XXX.XXX: continued`) back into their parent sections
6. Handles one doubled-character PDF (`jud-lib-106cmr704.pdf`) via character-level dedup
7. Extracts cross-references (`106 CMR XXX.XXX`) and tables
8. Outputs one JSON file per section

### Per-section JSON structure

```json
{
  "source": "106 CMR",
  "chapter": 362,
  "chapter_title": "SUPPLEMENTAL NUTRITION ASSISTANCE PROGRAM: NONFINANCIAL...",
  "section_number": "362.330",
  "section_title": "Good Cause Criteria for the General SNAP Work Requirements",
  "program": "SNAP",
  "text": "Good cause for failure to meet...\n(A) Good Cause Reasons.\n(1) Suitable...",
  "tables": [],
  "cross_references": ["106 CMR 362.330(A)", "106 CMR 362.330(B)"],
  "pdf_file": "106cmr362.pdf"
}
```

### Parse results

| Metric | Value |
|--------|-------|
| PDFs processed | 18 |
| Total sections | 592 |
| SNAP sections (ch 360-367) | 283 |
| TAFDC/EAEDC sections (ch 701-708) | 240 |
| Cross-Program sections (ch 327, 343) | 69 |
| Sections with tables | 7 |
| Sections with cross-references | 357 |
| Doubled-char PDF sections | 37 (from 704) |

### Key design decisions

1. **Chapter-filtered section detection**: Each PDF is one CMR chapter. Section headings are matched only against the chapter's prefix (e.g., `^362\.\d{3}:` for `106cmr362.pdf`). This eliminates false positives from cross-references that happen to start at the beginning of a line after PDF text wrapping.

2. **TOC boundary via duplicate detection**: Page 1 lists section numbers in a table of contents, then body content repeats those same numbers with actual text. The first duplicate marks the boundary. Works reliably for all 18 PDFs (including multi-page TOCs).

3. **Continuation merging**: Sections spanning multiple pages have `XXX.XXX: continued` at the top of each subsequent page. The parser merges all continuations into the parent section, preserving the full nested `(A)(1)(a)(b)(c)` legal structure.

4. **Character-level dedup for 704**: One PDF (`jud-lib-106cmr704.pdf`) has font metrics that cause pdfplumber to double every character in `extract_text()` output. The actual PDF is fine — it's a pdfplumber extraction quirk. Fixed by skipping consecutive identical non-space characters.

5. **Program mapping from chapter number**: 360-367 = SNAP, 701-708 = TAFDC/EAEDC, 327/343 = Cross-Program. Hardcoded in parser since this is stable regulatory structure.

---

## Phase 2: Chunking & Embedding (COMPLETE)

### Chunker design

Self-contained chunker mirroring FNS/OLG patterns.

**Two-tier output**:
- 18 chapter-level documents (7K-205K chars) for broad topic matching
- 1,275 section-level chunks (median 980 chars) for specific regulatory answers

**Context prefix**: `"106 CMR 362 > SNAP Nonfinancial Eligibility > 362.330 Good Cause Criteria"`

**Chunk IDs**: `cmr_ch362` (chapters), `cmr_sec_362_330__000` (sections)

**Merge/split**: Same thresholds as OLG/FNS (MIN=200, MAX=1500, TARGET=1000). CMR sections are already larger after continuation merging (median 884 chars raw), so there's less merging and more splitting than FNS.

### Chunk statistics

| Metric | Value |
|--------|-------|
| Chapter documents | 18 |
| Section chunks | 1,275 |
| Median chunk size | 980 chars |
| Mean chunk size | 962 chars |
| Min | 82 chars |
| Max | 3,391 chars |

### Embedding

- Model: Voyage AI `voyage-3`
- Tokens: 576,413
- Cost: $0.035
- Collections: `cmr_chapters` (18 docs), `cmr_sections` (1,275 chunks)

---

## Commands

```bash
# Parsing
python rag/cmr/parser.py                    # Parse all 18 PDFs
python rag/cmr/parser.py --chapter 362       # Parse one chapter
python rag/cmr/parser.py --dry-run            # Show sections, don't write

# Chunking
python rag/cmr/chunker.py                    # Generate chunks
python rag/cmr/chunker.py --stats             # Statistics only
python rag/cmr/chunker.py --preview 2         # Preview first 2 chapters

# Embedding
python rag/embedder.py --source cmr --dry-run    # Cost estimate
python rag/embedder.py --source cmr              # Embed into ChromaDB
python rag/embedder.py --source cmr --force      # Re-embed from scratch

# Querying
python rag/query.py "income deduction" --source cmr
python rag/query.py "work requirements" --source cmr --program SNAP
python rag/query.py "income" --source cmr --collection chapters
python rag/query.py --source cmr --list-programs
```

---

## File Inventory

| Chapter | PDF | Program | Sections | Chunks |
|---------|-----|---------|----------|--------|
| 327 | `jud-lib-106cmr327.pdf` | Cross-Program | 24 | 23 |
| 343 | `106cmr343.pdf` | Cross-Program | 45 | 63 |
| 360 | `jud-lib-106cmr360.pdf` | SNAP | 19 | 30 |
| 361 | `106cmr361.pdf` | SNAP | 47 | 76 |
| 362 | `106cmr362.pdf` | SNAP | 20 | 81 |
| 363 | `jud-lib-106cmr363.pdf` | SNAP | 11 | 65 |
| 364 | `jud-lib-106cmr364.pdf` | SNAP | 44 | 114 |
| 365 | `106cmr365.pdf` | SNAP | 47 | 101 |
| 366 | `jud-lib-106cmr366.pdf` | SNAP | 32 | 72 |
| 367 | `106cmr367.pdf` | SNAP | 43 | 67 |
| 701 | `jud-lib-106cmr701.pdf` | TAFDC/EAEDC | 29 | 58 |
| 702 | `jud-lib-106cmr702.pdf` | TAFDC/EAEDC | 34 | 58 |
| 703 | `jud-lib-106cmr703.pdf` | TAFDC/EAEDC | 59 | 214 |
| 704 | `jud-lib-106cmr704.pdf` | TAFDC/EAEDC | 37 | 102 |
| 705 | `106cmr705.pdf` | TAFDC/EAEDC | 22 | 26 |
| 706 | `jud-lib-106cmr706.pdf` | TAFDC/EAEDC | 53 | 58 |
| 707 | `jud-lib-106cmr707.pdf` | TAFDC/EAEDC | 19 | 57 |
| 708 | `106cmr708.pdf` | TAFDC/EAEDC | 7 | 10 |
