# 7 CFR Processing Notes (HISTORICAL — pre-implementation)

> **Status**: This is the original planning document from 2026-04-22, captured before the CFR pipeline was built. Many of the open questions below have been answered and the design has evolved during implementation. **For the canonical record of what was actually built and why, see [`docs/cfr_pipeline.md`](../cfr_pipeline.md).** This file is preserved as a historical reference for tracing the original design intent.

**Date**: 2026-04-22
**Source**: 7 CFR Parts 271, 272, 273, 274, 275, 280, 292 (SNAP federal regulations)
**Location**: `raw/cfr/`

---

## Source Inventory

| Part | Title | Pages | Sections | Description |
|------|-------|------:|----------|-------------|
| 271 | General Information & Definitions | 26 | 9 | Purpose, master definitions, OMB control numbers |
| 272 | State Agency Requirements | 88 | 18 | State plans, training, outreach, automation, QC contractors |
| 273 | **Certification of Eligible Households** | **252** | **32** | THE core regulation — household concept, application processing, residency, citizenship, students, work/E&T, resources, income/deductions, benefit levels, reporting, recert, fair hearings, IPV, claims, ABAWD, transitional benefits |
| 274 | Issuance & Use of Benefits | 39 | 8 | EBT systems, benefit delivery, retailer management, card replacement |
| 275 | Performance Reporting | 50 | 24 | QC reviews, management evaluations, sampling, corrective action, error rates |
| 280 | Emergency Disaster Assistance | 1 | 1 | Temporary eligibility during disasters (single paragraph) |
| 292 | Summer EBT Program | 61 | 31 | Summer nutrition benefits for school kids (new 2024 program) |
| | **TOTAL** | **517** | **123** | |

## How This Fits the Source Hierarchy

```
7 CFR (federal regulation)     ← THE LAW (new source)
    ↓ implements
106 CMR (state regulation)     ← Massachusetts implementation (have)
    ↓ explains
OLG (staff guide)              ← What workers follow (have)

FNS 310 (QC handbook)         ← How to REVIEW cases (have, separate chain)
```

The 7 CFR is the **authoritative federal source** that 106 CMR implements. Part 273 alone (252 pages) is larger than the entire 106 CMR (342 pages).

## Structure Differences vs CMR

| Feature | 106 CMR | 7 CFR |
|---------|---------|-------|
| Section marker | `XXX.XXX:` (e.g., `362.330:`) | `§ XXX.XX` (e.g., `§ 273.9`) |
| Section numbering | 3-digit chapter + 3-digit section | 3-digit part + 1-2 digit section |
| Section count per part/chapter | ~20-60 sections per chapter | ~1-32 sections per part |
| Section length | Short to medium (median 884 chars) | **Very long** — a single section like § 273.9 can be 20+ pages |
| Sub-item hierarchy | `(A)(1)(a)` | `(a)(1)(i)(A)` — lowercase first, then numbers, then roman, then uppercase |
| Internal references | `106 CMR 362.330` | `§ 273.9`, `paragraph (d)(6)(ii)` |
| TOC | Inline at start of each PDF | First 1-2 pages per PDF |
| Page headers | `"106 CMR: DEPARTMENT OF TRANSITIONAL ASSISTANCE"` | `"7 CFR Part 273 (up to date as of 4/20/2026)"` + `"7 CFR 273.9(d)(4)(i)"` (breadcrumb) |
| Page footers | None standard | `"7 CFR 273.1(b)(1)(ii) (enhanced display) page 2 of 252"` |
| Amendment notes | None in text | Inline: `[Amdt. 132,43 FR 47882, Oct. 17, 1982, as amended by...]` |
| Subparts | No | Yes — Part 273 has Subparts A through H |
| Continuation pages | `"XXX.XXX: continued"` heading | No continuation markers — sections flow across pages |

## Key Design Decisions for CFR Parser

### 1. Section Detection

**Pattern**: `§ {part}.{section}` at start of headings. Unlike CMR which uses `\d{3}\.\d{3}:`, CFR uses `§\s*\d{3}\.\d{1,2}\b`.

**Complication**: The `§` symbol appears in both the TOC and the body, and also in cross-references mid-text. Need to distinguish:
- TOC entry: `§ 273.9 Income and deductions.`
- Body heading: `§ 273.9 Income and deductions.` (identical format!)
- Cross-reference: `...as specified in § 273.4...` (inline, not at line start)

**Approach**: Same TOC boundary detection as CMR — find the first duplicate section number. But also need to handle that body section headings may not be at line start (pdfplumber can wrap them).

### 2. Sub-item Hierarchy

CFR uses a different nesting convention than CMR:
```
(a) Top level          ← lowercase letter
  (1) Second level     ← number
    (i) Third level    ← lowercase roman
      (A) Fourth level ← uppercase letter
```

This is inverted from CMR's `(A)(1)(a)` pattern. The chunker should be aware of this for potential sub-heading extraction in continued chunks.

### 3. Section Length Problem

CMR sections are median 884 chars. CFR sections will be **much longer** — § 273.7 (Work provisions) and § 273.9 (Income and deductions) each span 20+ pages. This means:
- More aggressive splitting will be needed
- Sub-item context in chunks becomes even more important
- A single CFR section might produce 30-50 chunks

### 4. Amendment Notes

CFR text is peppered with amendment citations:
```
[Amdt. 132,43 FR 47882, Oct. 17, 1982, as amended by Amdt. 216,47 FR 23461, May 28, 1982;...]
```

These should be **stripped or preserved as metadata** — they add noise to embeddings without adding policy content.

### 5. Page Headers/Footers

Every page has two lines to strip:
- Header: `7 CFR Part 273 (up to date as of 4/20/2026)` + breadcrumb like `7 CFR 273.9(d)(4)(i)`
- Footer: `7 CFR 273.1(b)(1)(ii) (enhanced display) page X of Y`

The breadcrumb is useful metadata (tells you exactly where you are in the hierarchy) but should be stripped from the text to avoid embedding noise.

### 6. Subpart Structure

Part 273 has Subparts A through H. This adds a hierarchy level above sections:
```
Part 273 > Subpart D (Eligibility and Benefit Levels) > § 273.9 (Income and deductions)
```

The context prefix should include the subpart. This maps well to the existing `build_context_prefix()` pattern.

### 7. Cross-References

CFR uses both `§ 273.9` references and paragraph-level references like `paragraph (d)(6)(ii) of this section`. These should be extracted as cross-references similar to how CMR extracts `106 CMR XXX.XXX` references.

### 8. Tables

From initial inspection, the CFR PDFs have fewer tables than CMR. The pdfplumber table extraction should work the same way.

## Lessons from CMR Cleanup (Apply to CFR)

1. **Post-split merge pass** — Build this into the CFR chunker from day one
2. **Multi-line title detection** — CFR section headings may also wrap across lines
3. **Sentence-boundary splits** — Split at sentence boundaries, not just `\n\n`
4. **Sub-item context in continued chunks** — Include `(a)(1)(i)` breadcrumb in chunk titles
5. **Cross-program filter issue** — CFR is SNAP-only, so no program filter needed (simpler)
6. **Amendment note stripping** — Remove `[Amdt. ...]` blocks before chunking
7. **Retrieval benchmark** — Create a CFR-specific benchmark from day one

## Processing Strategy

**Start small**: Parse and chunk Part 280 (1 page, 1 section) as a smoke test. Then Part 271 (26 pages, 9 sections) as a real test. Then tackle Part 273 (252 pages, 32 sections) — the main event.

**Reuse infrastructure**: `rag/embedder.py` and `rag/query.py` already support `--source` flags. Adding `cfr` requires one dict entry per resolver function. ChromaDB collections: `cfr_parts` (7 docs) and `cfr_sections` (123+ chunks).

**New files needed**:
- `rag/cfr/parser.py` — PDF → structured JSON sections
- `rag/cfr/chunker.py` — JSON sections → chunk files
- `index/cfr/parsed_sections/` — output directory
- Config entries in `config.ini`

## Open Questions

1. Should we chunk at the `§ 273.9` level (very long) or at the sub-item `(a)` level (more granular)?
   - CMR chunks at section level (e.g., 362.330) which is fine because CMR sections are short
   - CFR sections are 10-50x longer — may need to chunk at sub-item level instead
   - But sub-items don't have titles, just `(a)`, `(1)` markers

2. Should amendment notes be stripped entirely or kept as metadata?
   - They're noise for retrieval but useful for tracing regulatory history
   - Recommendation: Strip from chunk text, preserve in metadata field

3. Do we need all 7 parts or just the core ones (271, 273, 274)?
   - Part 275 (QC) overlaps heavily with FNS 310 which we already have
   - Part 292 (Summer EBT) is a separate program
   - Part 280 is 1 page
   - **Start with 271 + 273**, add others incrementally

4. How does CFR map to CMR sections? (for future cross-source comparator)
   - § 273.9 (Income) → 106 CMR 363 (Financial) + 106 CMR 364 (Determining)
   - § 273.7 (Work) → 106 CMR 362.300s
   - § 273.8 (Resources) → 106 CMR 363.100s
   - A mapping table would be valuable for gap analysis
