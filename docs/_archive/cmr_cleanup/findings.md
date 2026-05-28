# CMR Pipeline Cleanup — Audit Findings

**Date**: 2026-04-22
**Scope**: 106 CMR parser (`rag/cmr/parser.py`) + chunker (`rag/cmr/chunker.py`)
**Data**: 592 parsed sections, 1,275 chunks across 18 chapters

---

## Executive Summary

The CMR pipeline correctly extracts all sections from all 18 PDFs and retains 96-97% of source text. The fundamentals are solid. However, **chunk quality issues degrade retrieval accuracy to ~50% top-1 correctness** on realistic worker questions. Three root causes account for most problems: the merge-before-split ordering, single-line title capture, and mid-thought paragraph splits.

**Current retrieval accuracy** (20-question benchmark):
- Top-1 correct: **10/20 (50%)**
- Top-3 correct: **16/20 (80%)**
- Top-5 correct: **16/20 (80%)**
- Complete miss: **4/20 (20%)**

**Target**: 85%+ top-1 accuracy.

---

## Issue 1: Merge-Before-Split Creates Orphan Fragments

### The Problem

The chunker pipeline runs: `merge_small_sections()` → `split_large_section()` → output. Because merge runs BEFORE split, any tiny fragments created by splitting never get a second merge pass.

### Evidence

**28 chunks under 150 chars** (2.2% of all chunks). These are sentence fragments that are useless for retrieval:

| chunk_id | chars | trailing text |
|----------|-------|---------------|
| `cmr_sec_703_430__160` | 82 | `"Known to"` |
| `cmr_sec_703_340__148` | 90 | `"Except as specified in 106 CMR"` |
| `cmr_sec_367_275__011` | 92 | `"by the Department."` |
| `cmr_sec_343_030__002` | 100 | `"The interpreter is sworn to make"` |
| `cmr_sec_363_210__036` | 100 | `"Additional situations when the"` |
| `cmr_sec_703_192__094` | 143 | `"While psychotropic"` |
| `cmr_sec_703_220__138` | 130 | `"(k) Other governmental records."` |
| `cmr_sec_366_910__064` | 122 | `"household being updated on DTA's computer system."` |
| `cmr_sec_704_430__095` | 123 | `"(A) Defifinition."` |
| `cmr_sec_343_320__031` | 125 | `"of the dismissal notice."` |

...and 18 more. Full list spans 14 different chapters.

### Root Cause

`split_large_section()` splits at `\n\n` paragraph boundaries. In legal text, many "paragraphs" are single numbered sub-items like `(A)`, `(1)`, etc. When a paragraph group is split, the last fragment may be tiny. Since `merge_small_sections()` already ran, nothing catches these orphans.

### Fix

Add a **post-split merge pass**: after `split_large_section()`, run a second merge on the resulting chunks to fold any sub-`MIN_CHUNK_SIZE` fragments into their neighbors.

---

## Issue 2: Section Title Regex Captures Only One Line

### The Problem

The parser's heading detection regex:
```python
re.compile(rf"^({chapter_prefix}\.\d{{3}}):?\s+(.+?)$", re.MULTILINE)
```

Captures only the first line after the section number. If a heading wraps across multiple lines in the PDF extract, the title becomes a fragment.

### Evidence

**4 sections with broken/fragment titles**, affecting **60+ chunks**:

| Section | Current (broken) title | Likely real title | Chunks affected |
|---------|----------------------|-------------------|-----------------|
| `703.192` | `"or the SSI Listing of Impairments. The determination shall be based on the"` | EAEDC Disability Determination (continued from 703.191) | **53 chunks** |
| `703.720` | `"or has good cause as specified in 106 CMR 701.380: Good Cause Criteria."` | Work Program Sanctions / Good Cause | unknown |
| `366.115` | `"and recalculate the household's SNAP benefit amount during the certification period."` | Interim Reporting Changes | unknown |
| `367.825` | `"are applicable to ADHs. The hearing official shall advise the household member or his"` | Administrative Disqualification Hearing Procedures | unknown |

Additionally, **12 sections have titles >80 chars** that likely captured body text. These are less broken but still long:

| Section | Title (truncated) |
|---------|-------------------|
| `360.250` | `"Department Obligations under Title II of the Americans With Disabilities Act (ADA) (42 U.S.C."` |
| `362.200` | `"Citizens, Noncitizens, Canadian-born or Mexican-born Native Americans and Members of"` |
| `703.183` | `"TAFDC Teen Parent Structured Residential Setting [Note: 106 CMR 703.183 was formerly found"` |
| `703.522` | `"TAFDC Cooperation in Obtaining Third-party Liability Coverage for Medical Services"` |

### Root Cause

pdfplumber extracts multi-line headings as separate lines. The regex `(.+?)$` stops at the first newline. For long titles that wrap in the PDF, only the first line (or a continuation fragment) gets captured.

### Fix

After matching a heading, look ahead to see if the next line(s) are part of the title (not starting with `(A)`, `(1)`, not a sub-item, not blank, not another section number). Concatenate continuation lines into the title.

### Verification Needed

Go to the raw PDFs for sections 703.192, 703.720, 366.115, 367.825 and extract the actual heading text to confirm what the correct titles should be. The 703.192 case is especially important since it affects 53 chunks.

---

## Issue 3: 56.6% of Chunks Have Degraded "(continued)" Titles

### The Problem

When `split_large_section()` splits a section into multiple chunks, it sets `section_title` to `"Original Title (continued)"` for all chunks after the first. This means:

- **722 out of 1,275 chunks (56.6%)** have `(continued)` as their effective title
- The metadata `section_title` field is degraded for the majority of chunks
- The context prefix still contains the original title, but the searchable metadata doesn't

### Evidence

Sections split into the most chunks:

| Section | Chunks | Title |
|---------|--------|-------|
| `703.192` | 53 | EAEDC Disability (broken title) |
| `364.990` | 39 | SNAP Allotment Proration Table |
| `363.140` | 17 | Noncountable Assets |
| `363.230` | 16 | Excluded Income |
| `703.193` | 14 | EAEDC Vocational Factors |
| `362.220` | 13 | Noncitizens |
| `364.400` | 13 | Determining Deductions |
| `703.430` | 12 | TAFDC Noncitizen Status |
| `704.240` | 12 | Lump Sum Income |

199 of 553 unique sections (36%) are split into multiple chunks.

### Potential Improvement

Instead of generic "(continued)", include the sub-item context. Legal text has a clear hierarchy `(A) → (1) → (a)` — the chunk could carry the last major sub-heading it falls under. For example, instead of `"Determining Deductions (continued)"`, it could be `"Determining Deductions > (C) Medical Deduction"`.

This is a significant enhancement though — it requires parsing the `(A)/(1)/(a)` structure during splitting.

---

## Issue 4: Retrieval Quality Problems

### The Benchmark

20 questions a real DTA worker would ask, with expected CMR sections identified manually.

### Results Detail

**Complete misses (4/20) — correct section not in top 5:**

| Question | Got #1 | Expected | Why it missed |
|----------|--------|----------|---------------|
| `"What vehicles are exempt from SNAP asset test"` | 363.230 Excluded Income | 363.140 Noncountable Assets | The word "exempt" pulled income exclusions instead of asset exemptions. The actual section title "Noncountable Assets" doesn't use the word "exempt" or "vehicle" prominently. |
| `"TAFDC work program requirements"` | 706.410 Direct Deposit | 703.150 TAFDC Work Program | 706.410 (Direct Deposit!) beat the actual work program section. The work program section appeared at #3 and #5. Possibly the 706.410 chunk text happens to mention "TAFDC" and "program" frequently. |
| `"SNAP fair hearing process"` | 364.840 Notice of SNAP Termination | 343.xxx Fair Hearing Rules | **Program filter issue**: Query used `program='SNAP'`, but chapter 343 (Fair Hearing Rules) is tagged as `Cross-Program`. The filter excluded the correct results entirely. |
| `"SNAP household composition rules"` | 361.200 Household Concept/Definition | 362.1xx | Actually 361.200 IS the right section — my expected answer was wrong. This is a **TOP1 hit**, making the real score 11/20 (55%). |

**Near-misses (correct answer at #2 or #3) — 5/20:**

| Question | #1 (wrong) | Correct at # | Score gap |
|----------|-----------|-------------|-----------|
| `"bank account limits"` | 366.110 Reporting (0.470) | #2: 363.110 Assets (0.468) | 0.002 |
| `"application processing time"` | 366.920 SSI/SNAP (0.445) | #2: 361.700 Timeliness (0.427) | 0.018 |
| `"excluded income"` | 363.210 Verification (0.492) | #2: 363.230 Excluded Income (0.467) | 0.025 |
| `"self employment income"` | 365.970 Benefits (0.566) | #3: 363.220 Countable Income (0.459) | 0.107 |
| `"gross income limit"` | 366.620 Certification (0.458) | #3: 363.110 Assets (0.430) | 0.028 |

### Patterns

1. **366.110 "Household Reporting Responsibilities"** appears as a false positive in many queries. Its text is broad enough to match many topics. This section may need to be chunked differently or its embedding context improved.

2. **Program filter excludes cross-program chapters** (343 Fair Hearing, 327 SSP). Queries about fair hearings with `program='SNAP'` will never find chapter 343. This is a query.py design issue, not a chunk quality issue.

3. **Near-miss scores are very close** — the top-1 misses often lose by <0.03 similarity. Better chunk text (clearer titles in the context prefix, less noise) could flip these.

4. **Proration table chunks (364.990)** with 39 chunks of pure numbers occasionally surface in unrelated queries but are not the worst offenders.

---

## Issue 5: Chunk ID Numbering

### The Problem

`chunk_index` is global per-chapter, not per-section. Example: `cmr_sec_362_310__039` means "position 39 in chapter 362", not "chunk 39 of section 362.310".

### Impact

- `--neighbors` in query.py works on collection order, so it still finds adjacent chunks functionally
- But the ID doesn't tell you whether you're looking at chunk 1/11 or 7/11 of a section
- Makes debugging harder but doesn't affect retrieval

### Fix Priority

Low. Cosmetic improvement that could be addressed when re-chunking.

---

## Summary: Fix Priority

| Issue | Impact | Effort | Priority |
|-------|--------|--------|----------|
| **Post-split merge pass** | Eliminates 28 noise chunks | Small (add ~10 lines to chunker) | **High** |
| **Multi-line title detection** | Fixes 4 broken titles, 60+ chunks | Medium (parser regex enhancement) | **High** |
| **Program filter for cross-program** | Fixes fair hearing retrieval miss | Small (query.py change) | **High** |
| **Better "(continued)" context** | Improves 722 chunk titles | Large (sub-heading parser) | **Medium** |
| **Re-embed after fixes** | Required to realize improvements | Small (~$0.10, automated) | **Required** |
| **Chunk ID scheme** | Cosmetic | Small | **Low** |

---

## Retrieval Accuracy Test Suite

The 20-question benchmark should be saved and re-run after any changes to measure improvement. Current baseline:

- **Adjusted top-1: 11/20 (55%)** (correcting the household composition false negative)
- **Top-3: 16/20 (80%)**
- **Top-5: 16/20 (80%)**
- **True misses: 3/20 (15%)** — vehicles/assets, TAFDC work program, fair hearing (filter issue)

Target after cleanup: **17+/20 top-1 (85%+)**.
