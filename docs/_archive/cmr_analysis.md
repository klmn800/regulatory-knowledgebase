# CMR Source Analysis — Parser Design Notes

**Date**: 2026-03-17
**Purpose**: Detailed analysis of the 18 CMR PDFs to inform parser design.

## Source Overview

| Metric | Value |
|--------|-------|
| PDFs | 18 files |
| Total pages | 342 |
| Total size | 3.7 MB |
| Sections found | ~623 (17 clean PDFs) + ~45 estimated in doubled PDF |
| Sections with clean text | 17 of 18 PDFs |
| Doubled-character PDF | 1 (`jud-lib-106cmr704.pdf`, 28 pages) |
| Tables | 7 total (across 4 PDFs) |

## File Inventory

| File | Chapter | Program | Pages | Sections | Tables |
|------|---------|---------|-------|----------|--------|
| `106cmr343.pdf` | 343 | Cross-Program | 16 | 46 | 0 |
| `106cmr361.pdf` | 361 | SNAP | 19 | 57 | 0 |
| `106cmr362.pdf` | 362 | SNAP | 21 | 22 | 0 |
| `106cmr365.pdf` | 365 | SNAP | 24 | 56 | 0 |
| `106cmr367.pdf` | 367 | SNAP | 16 | 44 | 0 |
| `106cmr705.pdf` | 705 | TAFDC/EAEDC | 7 | 25 | 0 |
| `106cmr708.pdf` | 708 | TAFDC/EAEDC | 3 | 7 | 0 |
| `jud-lib-106cmr327.pdf` | 327 | Cross-Program | 6 | 25 | 0 |
| `jud-lib-106cmr360.pdf` | 360 | SNAP | 10 | 20 | 0 |
| `jud-lib-106cmr363.pdf` | 363 | SNAP | 16 | 14 | 1 |
| `jud-lib-106cmr364.pdf` | 364 | SNAP | 30 | 47 | 1 |
| `jud-lib-106cmr366.pdf` | 366 | SNAP | 19 | 37 | 0 |
| `jud-lib-106cmr701.pdf` | 701 | TAFDC/EAEDC | 15 | 38 | 2 |
| `jud-lib-106cmr702.pdf` | 702 | TAFDC/EAEDC | 16 | 38 | 1 |
| `jud-lib-106cmr703.pdf` | 703 | TAFDC/EAEDC | 65 | 65 | 1 |
| `jud-lib-106cmr704.pdf` | 704 | TAFDC/EAEDC | 28 | ~45* | 1 |
| `jud-lib-106cmr706.pdf` | 706 | TAFDC/EAEDC | 15 | 56 | 0 |
| `jud-lib-106cmr707.pdf` | 707 | TAFDC/EAEDC | 16 | 26 | 0 |

*704 has doubled characters requiring word-level dedup

## Chapter Titles and Programs

**SNAP chapters** (360-367):
- 327: Eligibility Requirements for SSP
- 343: Fair Hearing Rules (cross-program)
- 360: General Provisions
- 361: Application Process
- 362: Nonfinancial Eligibility Standards
- 363: Financial Eligibility Standards
- 364: Determining Household Eligibility and Benefit Level
- 365: Special Situations
- 366: Additional SNAP Provisions
- 367: Violations, Disqualifications, and Claim Collection

**TAFDC/EAEDC chapters** (701-708):
- 701: General Policies
- 702: Application Process
- 703: Nonfinancial Eligibility
- 704: Financial Eligibility
- 705: Related Provisions
- 706: Auxiliary Benefits
- 707: Employment Services
- 708: Full Employment Program

## PDF Structure Patterns

### Page Header
Every page starts with one of two variants:
- `106 CMR: DEPARTMENT OF TRANSITIONAL ASSISTANCE`
- `106 CMR DEPARTMENT OF TRANSITIONAL ASSISTANCE`

### Table of Contents (Page 1+)
- Page 1 starts with the chapter title: `106 CMR XXX.000: CHAPTER TITLE`
- Followed by `Section` header
- Then section number listings (TOC entries)
- Body content begins when a section number appears for the **second time** (duplicate = end of TOC)
- Most PDFs: TOC is top of page 1, body starts mid-page 1
- Largest PDF (703): TOC spans pages 1-2, body starts on page 3

### Section Headings
Format: `XXX.XXX: Section Title` at start of a line.
- All use 3-digit chapter prefix + 3-digit section number: `362.330`
- No 4+ digit section suffixes found

### Continuation Markers
When a section spans multiple pages: `XXX.XXX: continued` appears at the top of subsequent pages (after the page header). These need to be merged back into the parent section.

### Nested Structure
Nearly all PDFs have 3+ levels of nesting:
- `(A)` / `(B)` — uppercase letter level
- `(1)` / `(2)` — number level
- `(a)` / `(b)` — lowercase letter level
- `1.` / `2.` — numbered sub-items (occasional 4th level)

This is the legal logic structure and **must be preserved within each section chunk**.

### Cross-References
Abundant, using format: `106 CMR XXX.XXX` (sometimes with sub-references like `106 CMR 362.330(A)(1)`). Easy regex extraction.

## Section Size Analysis (17 clean PDFs)

| Metric | Value |
|--------|-------|
| Total sections | 623 |
| Min size | 6 chars |
| Max size | 7,183 chars |
| Mean | 562 chars |
| Median | 192 chars |

### Size Distribution
```
    0-  200:  607 (50.5%)  ← Many tiny umbrella headings
  200-  500:  184 (15.3%)
  500- 1000:  179 (14.9%)
 1000- 1500:  102 ( 8.5%)
 1500- 2000:   48 ( 4.0%)
 2000- 3000:   55 ( 4.6%)
 3000- 5000:   20 ( 1.7%)
 5000-10000:    7 ( 0.6%)  ← Proration tables in 364
```

**Key insight**: 50% of sections are under 200 chars. Merge logic is critical.

## Doubled-Character PDF (704)

`jud-lib-106cmr704.pdf` has every character rendered twice in the PDF font.
- Raw text: `DDEEPPAARRTTMMEENNTT OOFF TTRRAANNSSIITTIIOONNAALL AASSSSIISSTTAANNCCEE`
- **Fix**: Word-level dedup using pdfplumber's `extract_words()`, taking every other character from each word's text.
- Verified: dedup produces clean, readable text across all 28 pages.
- All other 17 PDFs extract cleanly.

## Tables

Only 7 tables across 4 PDFs. All are simple 2-4 column tables:
- 363: Asset disqualification period chart (6 rows)
- 364: Medical expense deduction amounts (5 rows)
- 701: Benefit delivery time requirements (2 tables, 6+8 rows)
- 702: One table
- 703: Age/education/work experience table (31 rows)

Tables can be rendered inline as pipe-delimited text, same as OLG/FNS.
