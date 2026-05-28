# `output/` — generated deliverables

This directory is where the tools write their results. Its contents are
**not committed** — the system is portable, the results are not. Outputs are
gitignored both because they can be bulky and because some (QC analyses)
contain confidential case data. This README is the only tracked file here.

## What the system generates here (once run)

```
output/
├── comparator/        # FNS-vs-OLG gap analysis (per-section JSON + CSVs)
├── author/            # researched/drafted/formatted OLG pages, versioned per run
├── qc_analysis/       # QC error-finding analyses (contains case data — never published)
└── search_history.db  # search engine history (SQLite)
```

Each tool recreates its own subdirectory on first run, so this directory can
start empty on a fresh clone.
