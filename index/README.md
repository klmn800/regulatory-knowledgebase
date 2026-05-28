# `index/` — parsed data + vector store

This directory holds the **parsed, chunked, and embedded** policy data plus the
ChromaDB vector store. Its contents are **not committed** — they are large and
fully regeneratable from the source documents in `raw/`. This README is the
only tracked file here; everything else is gitignored.

## What lives here (once populated)

```
index/
├── chroma_db/                 # ChromaDB persistent store (8 collections)
├── olg/   fns/   cmr/   cfr/  # per-source parsed sections + chunk JSON
```

## How to regenerate

For each source (`olg`, `fns`, `cmr`, `cfr`):

1. **Parse** the raw documents into structured JSON
   (e.g. `python rag/cmr/parser.py`; OLG uses `rag/olg/scraper.py`).
2. **Chunk** into the two-tier broad/section JSON
   (e.g. `python rag/cmr/chunker.py`).
3. **Embed** into ChromaDB
   (`python rag/embedder.py --source cmr`).

See the per-source pipeline docs in `docs/` (`olg_pipeline.md`,
`fns_pipeline.md`, `cmr_pipeline.md`, `cfr_pipeline.md`) for details.
