# FNS Handbook 310 — RAG Pipeline Brainstorm

## The Problem

DTA (Massachusetts) follows the **Online Guide (OLG)** for SNAP policy. The federal agency
(FNS/USDA) publishes the **FNS Handbook 310** as the federal standard. These two rulebooks
mostly overlap but sometimes diverge, leading to QC errors that are hard to catch manually
because:

- Both documents are enormous (OLG: ~1,200 pages; Handbook: 306 PDF pages, ~96K words)
- The policy language is dense and technical
- Differences can be subtle — a different income threshold, a different verification standard,
  a different definition of "household member"
- Staff can't reasonably be expected to cross-reference two massive documents

**Goal**: Build tooling to systematically identify meaningful differences between federal
(FNS 310) and state (OLG) SNAP policy, using RAG + AI comparison.

---

## What We Already Have

The OLG side is fully built:

| Component | Status | Details |
|---|---|---|
| OLG scraper + parser | Complete | 1,202 pages scraped, structured JSON |
| OLG chunker | Complete | 6,785 section chunks + 1,202 page docs |
| OLG embeddings | Complete | Voyage AI (voyage-3) in ChromaDB |
| OLG query interface | Complete | `rag/query.py` — CLI, Python API, JSON output |

**What's missing**: The FNS Handbook side — parsing, chunking, embedding — plus the
comparison agent that brings both sides together.

---

## The FNS Handbook 310 — Document Analysis

### Basic stats

| Metric | Value |
|---|---|
| File | `FNS Handbook 310 1.13.26.pdf` (4.8 MB) |
| Total PDF pages | 306 |
| TOC / front matter | Pages 1–17 |
| Content pages | Pages 18–298 (281 pages) |
| Appendices | Pages 299–302 (A, B, C, D — placeholders for forms) |
| Index | Pages 303–305 |
| Back cover | Page 306 |
| Total text | ~637,000 chars / ~96,500 words |
| Estimated tokens | ~130,000–160,000 (too large for single context window) |
| Chapters | 14 |
| Numbered sections | 483 |
| Edition | October 2025, through QC PM 26-04, Change 2 (January 13, 2026) |

### Chapter breakdown

| Ch | Title | Pages | Words | Sections | Comparison relevance |
|---|---|---|---|---|---|
| 1 | Introduction | 22 | 7,707 | 27 | Low — definitions, admin |
| 2 | Basic Review Process | 13 | 4,224 | 29 | Low — QC procedures |
| 3 | Case Record Review | 12 | 3,818 | 22 | Low — QC procedures |
| 4 | Field Investigation | 22 | 7,841 | 32 | Low — QC procedures |
| 5 | Verification & Documentation | 11 | 3,917 | 21 | Medium — verification standards |
| 6 | Error Determination | 5 | 1,880 | 14 | Low — QC-specific |
| 7 | Review Procedures / Cert Systems | 43 | 14,720 | 68 | **High** — reporting rules |
| 8 | Non-Financial Eligibility | 37 | 12,898 | 50 | **Very high** — eligibility rules |
| 9 | Resources | 9 | 2,666 | 28 | **Very high** — asset limits |
| 10 | Income | 37 | 11,422 | 83 | **Very high** — income rules |
| 11 | Deductions | 30 | 9,675 | 62 | **Very high** — deduction rules |
| 12 | Making the Review Decision | 13 | 3,305 | 16 | Low — QC procedures |
| 13 | Negative Action Record Reviews | 21 | 6,243 | 16 | Medium — denial procedures |
| 14 | Informal Resolution & Arbitration | 6 | 1,940 | 15 | Low — QC-specific |

**Key insight**: Chapters 7–11 contain the substantive policy rules (~51,000 words, 291
sections). These are where state vs. federal differences will appear. Chapters 1–6 and
12–14 are mostly about *how to conduct QC reviews* — important context but less likely
to have state-level divergences.

### Document structure

The handbook uses a consistent **numbered section system**:

```
Chapter 8:  800, 810, 811, 812, 812.1, 812.2, 820, 821, 821.1, ...
Chapter 10: 1000, 1010, 1011, 1012, 1013.1, 1013.2, ..., 1060, 1061, 1061.1, ...
```

- First 1–2 digits encode the chapter (8xx = Ch 8, 10xx = Ch 10)
- Three-digit base number = major topic
- Additional digits = sub-topics
- Dot notation = sub-sections (e.g., 154.3, 1021.1)

Every page has a header ("FNS HANDBOOK 310") and footer (handbook page number like "10-4").

### Parsing challenges identified

#### Challenge 1: Side-by-side example boxes (14 pages)

Some pages place policy text on the left and an illustrative example in a bordered box on the
right. When pdfplumber extracts text, the two columns interleave line-by-line:

```
Good (what the PDF looks like):
  LEFT COLUMN                    | RIGHT COLUMN (example box)
  The State agency did not       | Example of a penalty that was not
  know of the household's...     | applied and did not have to be...

Bad (what extract_text() produces):
  "The State agency did not Example of a penalty that was not"
  "know of the household's applied and did not have to be..."
```

**Pages affected**: 43, 55, 56, 57, 161, 223, 224, 225, 268, 287, 288, 303, 304, 305

Note: Pages 303–305 are the INDEX (side-by-side columns are intentional there and not
policy-relevant). So the real problem is **11 content pages**.

**Options considered**:

- **Option A (column separation)**: Use word x-coordinates from pdfplumber to detect and
  separate left vs right text blocks. Extract each column independently. Most accurate,
  moderate complexity.

- **Option B (layout mode + post-process)**: Use `extract_text(layout=True)` which preserves
  spatial layout as whitespace, then parse columns from the indentation. Simpler but the
  output is messy.

- **Option C (flag for manual review)**: Accept garbled text on these pages, flag them in the
  output for manual correction. Simplest, but leaves 11 pages with bad text.

**Decision**: **Option A** as primary approach. If column separation proves unreliable for
specific pages, fall back to **Option C** (flag for manual cleanup). The example boxes
contain illustrative content, not policy rules — so even if some are imperfect, the policy
text in the left column is what matters most for comparison.

#### Challenge 2: Special characters

| Character | Unicode | Appears on | Fix |
|---|---|---|---|
| `\uf0d8` | Wingdings bullet | ~20 pages | Replace with `*` or `-` |
| `'` (U+2019) | Right single quote | Throughout | Keep as-is (valid apostrophe) |
| `—` (U+2014) | Em dash | Throughout | Keep as-is |
| `–` (U+2013) | En dash | Throughout | Keep as-is |

#### Challenge 3: Page headers and footers

Every page starts with "FNS HANDBOOK 310" and ends with a page number like "10-4" or
"8-22". These need to be stripped so they don't pollute the chunk text. Some pages also have
"Change 1 (October 27, 2025)" footers.

#### Challenge 4: Cross-references are plain text

The OLG has hyperlinks between pages. The handbook has plain text references like "See
Section 622" or "as described in Chapter 7, Section 726.1". These are valuable for the
comparison agent (they tell you which sections are related) but need regex extraction rather
than link parsing.

#### Challenge 5: Tables

Only 18 content pages have multi-row tables. `pdfplumber.extract_tables()` handles them
well. The most complex is a 39-row × 8-column table on page 268. Tables will be extracted
separately and rendered as pipe-delimited text inline (same approach as OLG chunker).

---

## Should We Split the PDF Into Smaller Files?

**Short answer: No — but the parser should output per-section JSON files.**

Splitting the PDF itself doesn't buy much:

- pdfplumber handles the full 306-page file fine (loads in seconds)
- The section numbering system is strong enough to split content logically without
  file-level boundaries
- Splitting adds a manual or semi-manual step that could introduce errors
- If we need to re-parse, we'd want to re-parse the whole thing anyway

What DOES make sense is for the parser to **output structured JSON per section** (or per
chapter), similar to how the OLG parser outputs one JSON file per page. The monolithic PDF
is the input; structured, inspectable JSON files are the output.

---

## Pipeline Architecture

### Phase 1: Parse the FNS Handbook

**Input**: `raw/FNS Handbook 310 1.13.26.pdf`

**New module**: `rag/fns/parser.py`

**Process**:
1. Open PDF with pdfplumber
2. Skip front matter (pages 1–17), appendices (299–302), index (303–305), back cover (306)
3. Extract text page by page
4. Strip page headers ("FNS HANDBOOK 310") and footers (page numbers)
5. Clean special characters
6. Detect section boundaries using numbered section regex
7. Handle side-by-side pages with column-aware extraction
8. Extract tables and associate with nearest section
9. Extract cross-references ("See Section NNN")
10. Build hierarchical section metadata (chapter, level, parent section)

**Output**: `index/fns/parsed_sections/` directory with one JSON file per section, structured like:

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
  "text": "When the household states a member earns wages...",
  "tables": [],
  "cross_references": ["Chapter 10", "Section 622"],
  "pdf_pages": [195],
  "handbook_pages": ["10-4"],
  "flags": []
}
```

The `flags` field captures issues: `["side_by_side_page", "manual_review_needed"]`

### Phase 2: Chunk and Embed

**Reuse/adapt**: `rag/fns/chunker.py` and `rag/embedder.py` patterns

- Most sections are naturally chunk-sized (median ~960 chars in OLG; likely similar here)
- Apply same merge/split rules: merge tiny sections (<200 chars), split oversized ones
- Prepend context prefix: `"FNS 310 > Chapter 10: Income > 1021.1 Positive Allegation"`
- Embed with Voyage AI, store in new ChromaDB collection: `fns_sections`

### Phase 3: Comparison Agent

**New module**: `programs/comparator/comparator.py`

For each FNS section (or at least Chapters 7–11):
1. Pull the FNS section text
2. Use it to query the OLG RAG (`rag/query.py` API) for matching state policy
3. Send both texts to Claude with a comparison prompt
4. Record Claude's analysis: match / difference / no state equivalent
5. Output structured comparison report

**Output**: Comparison report (CSV/Excel or structured JSON) with:
- FNS section reference
- OLG reference(s) found
- Similarity score from RAG
- Claude's assessment (match / minor difference / major difference / no equivalent)
- Explanation of any difference
- Relevance/impact notes

---

## Open Questions

1. **Chunking granularity**: Should we chunk at the section level (483 chunks) or also
   create chapter-level documents (14 docs) for broad topic matching? The OLG uses both
   tiers — probably should do the same here.

2. **Which chapters to compare first**: Start with Chapters 8–11 (most policy-relevant)?
   Or process everything and let the comparison agent prioritize?

3. **Comparison prompt design**: What exactly should we ask Claude to look for? Threshold
   differences? Definition differences? Procedural differences? All of the above?

4. **Rate limits and cost**: Each comparison = 1 Claude API call + 1 Voyage embedding query.
   ~300 sections in Chapters 7–11 = ~300 API calls. At Haiku rates, that's cheap. At Opus
   rates, less so. Model choice matters.

5. **Validation**: How do we verify the comparison results? Sample-check a subset manually?

---

## Next Steps

1. [ ] Build `rag/fns/parser.py` — PDF to structured JSON
2. [ ] Verify parser output — spot-check sections, especially the 11 flagged pages
3. [ ] Adapt chunker for FNS sections
4. [ ] Embed FNS chunks into ChromaDB
5. [ ] Design comparison prompt
6. [ ] Build `programs/comparator/comparator.py`
7. [ ] Run comparison on Chapters 8–11 first
8. [ ] Review results, iterate on prompt if needed
9. [ ] Expand to remaining chapters
