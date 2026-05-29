# `raw/` — source documents

This directory holds the **original source documents** the pipelines parse.
Its contents are **not committed** to the repository — the files are large
and are not ours to redistribute. This README is the only tracked file here;
everything else is gitignored.

The parsers (`rag/cmr/parser.py`, `rag/cfr/parser.py`, `rag/fns/parser.py`)
and the OLG scraper read from this directory. A fresh clone must populate it
before the parse stage of any pipeline will run.

## Expected layout

```
raw/
├── FNS Handbook 310 <date>.pdf      # FNS Handbook 310 (federal SNAP QC standard)
├── cmr/                             # 106 CMR Title 106 regulation PDFs (18 files)
│   └── *.pdf
└── cfr/                             # 7 CFR Parts 271–275, 280, 292 (7 files)
    └── *.pdf
```

OLG (the Online Guide) is not a static file — it is scraped from the source
WebHelp site via `rag/olg/scraper.py`, seeded from a HAR capture. See
`docs/olg_pipeline.md`.

## Where to obtain each source

- **7 CFR** and **FNS Handbook 310** — federal, publicly available.
- **106 CMR** — Commonwealth of Massachusetts regulations, publicly available.
- **OLG** — the agency's internal Online Guide; access per your own authorization.
