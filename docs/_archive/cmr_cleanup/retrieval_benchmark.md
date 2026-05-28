# CMR Retrieval Benchmark

**Date established**: 2026-04-22
**Purpose**: Measure retrieval accuracy before/after pipeline changes. Re-run after any parser, chunker, or embedding changes.

## How to Run

```python
from rag.query import search

test_cases = [
    # (question, program_filter, expected_section_prefix, topic)
    ("How much can a SNAP household have in bank accounts", "SNAP", "363.1", "asset limits"),
    ("What is the shelter deduction for SNAP", "SNAP", "364.4", "deductions"),
    ("Can a noncitizen get TAFDC benefits", None, "703.4", "noncitizen"),
    ("How long does DTA have to process a SNAP application", "SNAP", "361", "timeliness"),
    ("What income is excluded from SNAP eligibility", "SNAP", "363.23", "excluded income"),
    ("When can SNAP benefits be restored after an error", "SNAP", "366.5", "restoration"),
    ("What are the ABAWD exemptions", "SNAP", "362.32", "ABAWD"),
    ("EAEDC disability determination process", None, "703.19", "disability"),
    ("What vehicles are exempt from SNAP asset test", "SNAP", "363.14", "noncountable assets"),
    ("How is self employment income calculated for SNAP", "SNAP", "363.22", "income calc"),
    ("What happens if a SNAP household fails to report changes", "SNAP", "366", "reporting"),
    ("SNAP categorical eligibility requirements", "SNAP", "365.18", "cat elig"),
    ("How are SNAP benefits calculated", "SNAP", "364", "benefit calc"),
    ("What is the SNAP gross income limit", "SNAP", "363", "income limits"),
    ("TAFDC work program requirements", None, "703.7", "TAFDC work"),
    ("How does DTA verify identity at SNAP application", "SNAP", "361", "verification"),
    ("SNAP fair hearing process", None, "343", "fair hearing"),  # No program filter! 343 is Cross-Program
    ("What are the SNAP recertification rules", "SNAP", "366", "recertification"),
    ("EAEDC grant calculation", None, "704.43", "EAEDC grant"),
    ("SNAP household composition rules", "SNAP", "361.2", "household"),  # 361.200 is correct
]
```

## Scoring

- **TOP1**: Expected section prefix matches the #1 result's `section_number`
- **TOP3**: Expected section prefix found in top 3 results
- **TOP5**: Expected section prefix found in top 5 results
- **MISS**: Expected section not in top 5

## Baseline (2026-04-22, pre-cleanup)

```
Top-1: 11/20 (55%)    — note: fair hearing query had wrong program filter
Top-3: 16/20 (80%)
Top-5: 16/20 (80%)
Miss:   3/20 (15%)    — vehicles/assets, TAFDC work, fair hearing
```

### Detailed Baseline Results

| # | Topic | Score | Got | Expected | Status |
|---|-------|-------|-----|----------|--------|
| 1 | asset limits | 0.470 | 366.110 | 363.1 | TOP3 (0.468 at #2) |
| 2 | deductions | 0.560 | 364.400 | 364.4 | **TOP1** |
| 3 | noncitizen | 0.597 | 703.430 | 703.4 | **TOP1** |
| 4 | timeliness | 0.445 | 366.920 | 361 | TOP3 (0.427 at #2) |
| 5 | excluded income | 0.492 | 363.210 | 363.23 | TOP3 (0.467 at #2) |
| 6 | restoration | 0.466 | 366.510 | 366.5 | **TOP1** |
| 7 | ABAWD | 0.475 | 362.320 | 362.32 | **TOP1** |
| 8 | disability | 0.398 | 703.191 | 703.19 | **TOP1** |
| 9 | noncountable assets | 0.356 | 363.230 | 363.14 | **MISS** |
| 10 | income calc | 0.566 | 365.970 | 363.22 | TOP3 (0.459 at #3) |
| 11 | reporting | 0.600 | 366.110 | 366 | **TOP1** |
| 12 | cat elig | 0.420 | 365.180 | 365.18 | **TOP1** |
| 13 | benefit calc | 0.490 | 364.990 | 364 | **TOP1** |
| 14 | income limits | 0.458 | 366.620 | 363 | TOP3 (0.430 at #3) |
| 15 | TAFDC work | 0.502 | 706.410 | 703.7 | **MISS** (703.150 at #3) |
| 16 | verification | 0.462 | 365.830 | 361 | TOP3 (0.457 at #3) |
| 17 | fair hearing | 0.346 | 364.840 | 343 | **MISS** (filter issue in baseline) |
| 18 | recertification | 0.576 | 366.300 | 366 | **TOP1** |
| 19 | EAEDC grant | 0.480 | 704.430 | 704.43 | **TOP1** |
| 20 | household | 0.421 | 361.200 | 361.2 | **TOP1** |

### Known Issues Affecting Scores

1. **Fair hearing (Q17)**: Original test used `program='SNAP'` which filtered out chapter 343 (Cross-Program). Corrected in test suite above to use `None`.
2. **Household (Q20)**: Original expected was `362.1` but `361.200` is actually the correct section. Corrected above.
3. **366.110 false positive**: "Household Reporting Responsibilities" appears as #1 for asset limits and other unrelated queries. Broad text acts as a catch-all.

## Post-Cleanup (2026-04-27)

```
Top-1: 14/20 (70%)    +3 from baseline
Top-3: 18/20 (90%)    +2 from baseline
Top-5: 19/20 (95%)    +3 from baseline
Miss:   1/20 (5%)     -2 from baseline — only TAFDC work (EA low priority)
```

### Detailed Post-Cleanup Results

| # | Topic | Score | Got | Expected | Status | Change |
|---|-------|-------|-----|----------|--------|--------|
| 1 | asset limits | 0.486 | 363.110 | 363.1 | **TOP1** | TOP3 → TOP1 |
| 2 | deductions | 0.561 | 364.400 | 364.4 | **TOP1** | — |
| 3 | noncitizen | 0.579 | 703.430 | 703.4 | **TOP1** | — |
| 4 | timeliness | 0.476 | 366.920 | 361 | TOP3 (at #2) | — |
| 5 | excluded income | 0.502 | 364.500 | 363.23 | TOP3 (at #3) | — |
| 6 | restoration | 0.490 | 366.510 | 366.5 | **TOP1** | — |
| 7 | ABAWD | 0.461 | 362.320 | 362.32 | **TOP1** | — |
| 8 | disability | 0.436 | 703.190 | 703.19 | **TOP1** | — |
| 9 | noncountable assets | 0.360 | 363.140 | 363.14 | **TOP1** | MISS → TOP1 |
| 10 | income calc | 0.559 | 365.970 | 363.22 | TOP3 (at #3) | — |
| 11 | reporting | 0.592 | 366.210 | 366 | **TOP1** | — |
| 12 | cat elig | 0.427 | 365.180 | 365.18 | **TOP1** | — |
| 13 | benefit calc | 0.464 | 364.600 | 364 | **TOP1** | — (was 364.990 junk, now real section) |
| 14 | income limits | 0.466 | 363.110 | 363 | **TOP1** | TOP3 → TOP1 |
| 15 | TAFDC work | 0.543 | 701.200 | 703.7 | **MISS** | still miss (EA low priority) |
| 16 | verification | 0.492 | 362.500 | 361 | TOP3 (at #3) | — |
| 17 | fair hearing | 0.357 | 343.010 | 343 | **TOP1** | MISS → TOP1 |
| 18 | recertification | 0.591 | 366.300 | 366 | **TOP1** | — |
| 19 | EAEDC grant | 0.479 | 704.285 | 704.43 | TOP5 (at #4) | TOP1 → TOP5 (regression) |
| 20 | household | 0.420 | 361.200 | 361.2 | **TOP1** | — |

### What Changed

1. **364.990 excluded** from section-level indexing — cleared false positives for asset/benefit queries
2. **Program labels fixed** — 327=SSP, 343=Hearings, 367=Program Integrity, 701-708=EA
3. **Hearings $or filter** — fair hearing queries now find chapter 343
4. **Hierarchy-aware chunking** — cleaner chunk boundaries, no mid-sentence splits
5. **Line-break normalization** — PDF wrap artifacts removed from embedded text
6. **Continuation artifacts stripped** — "XXX.XXX : continued" no longer in chunk text

### Remaining Issues

- **TAFDC work (Q15)**: Broad EA chapter intro (701.200) outranks specific work program section (703.7xx). EA is low priority; accepted.
- **EAEDC grant (Q19)**: Minor regression from TOP1 to TOP5. 704.285 (payment standards) now ranks above 704.430 (grant calc). Chunking changes may have shifted the vector slightly.

## Original Target

```
Top-1: 17+/20 (85%+)
Top-3: 19+/20 (95%+)
Miss:   0/20
```

Did not hit Top-1 target but significantly improved all metrics. The remaining gaps are in EA chapters (low priority) and inherently difficult cross-chapter queries.
