# Data Quality Issues

Tracker for source-data and parsing issues surfaced during benchmarking, audits, or normal use. Issues are logged here as they're found and worked off when the user prioritizes them. The point is that **nothing slips through the cracks** — even if a fix is deferred, it stays visible.

## How to use this file

When a benchmark run, an audit, or a user query surfaces a data quality issue:

1. Add a row in the "Open" table below
2. Include enough detail to reproduce: source, section/chunk, what's wrong, where it was surfaced
3. Don't fix immediately unless trivial — let the user decide priority
4. When fixed, move the row to "Fixed" with the commit hash

This is for **data/content** issues (parser artifacts, wrong content in chunks, missing sections, etc.), not architecture or feature work. Architecture/feature work goes in the relevant plan doc.

---

## Open

| ID | Source | Location | Issue | Surfaced by | Date | Priority |
|---|---|---|---|---|---|---|
| DQ-001 | CMR | 704.135 (E) | Doubled-character artifact at end of chunk: `RREENNTT OORR MMOORRTTGGAAGGEE`. CLAUDE.md notes char-level dedup was applied to chapter 704 (the doubled-font PDF), but coverage is incomplete for 704.135. | CMR judge-baseline 2026-05-04 (cmr_022 spot-check) | 2026-05-04 | Low — chunk still readable, judge correctly downgraded to PARTIAL. Investigate CMR 704 dedup pass for missed sections. |

---

## Fixed

| ID | Source | Location | Issue | Fixed in | Date |
|---|---|---|---|---|---|

---

## Notes on prioritization

- **High priority**: corrupt content that makes a chunk unreadable, missing sections, wrong cross-references, mid-word splits (these should have been caught by Tier 1 cleanup but flag any escapes).
- **Medium priority**: stray UI artifacts, formatting issues that affect readability, missing metadata.
- **Low priority**: cosmetic issues, isolated artifacts that don't affect retrieval or comprehension.

The benchmark itself can absorb low-priority issues without skewing measurements — the judge is robust to noise. So unless an issue is widespread, it can wait.
