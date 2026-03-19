# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Policy Navigator** is a multi-source RAG (Retrieval-Augmented Generation) system for Massachusetts DTA (Department of Transitional Assistance) policy. It indexes three authoritative policy sources in priority order:

1. **OLG** (Online Guide) — DTA's internal staff guide; ~1,200 HTML pages covering SNAP, TAFDC, EAEDC, and cross-program policy. This is what workers follow day-to-day.
2. **CMR** (Code of Massachusetts Regulations, Title 106) — The state regulations the OLG implements. 18 PDFs, ~360 pages of formal legal language.
3. **FNS Handbook 310** — The federal SNAP Quality Control standard the CMR is supposed to implement. Single PDF, 306 pages, 483 numbered sections.

**Use cases**: Staff/agents ask policy questions and get answers using sources in OLG → CMR → FNS order. Also used to find discrepancies or gaps in the OLG (which is always in development).

**When sources disagree, the disagreement IS the finding.**

## Current State

| Source | Parse | Chunk | Embed | Query | Comparator |
|--------|-------|-------|-------|-------|------------|
| OLG | COMPLETE (1,202 pages) | COMPLETE (1,202 + 6,785) | COMPLETE | COMPLETE | N/A |
| FNS | COMPLETE (482 sections) | COMPLETE (14 + 722) | COMPLETE | COMPLETE | NOT STARTED |
| CMR | COMPLETE (592 sections) | COMPLETE (18 + 1,275) | COMPLETE | COMPLETE | NOT STARTED |

**All three sources are fully indexed and searchable.** Next: comparator agent for cross-source analysis.

## Architecture

Each source follows the same pipeline pattern: **Parse → Chunk → Embed → Query**

### Shared Infrastructure
- **Embedding model**: Voyage AI `voyage-3` (1,024 dimensions). Single unified `config.ini` at project root.
- **Vector store**: ChromaDB (persistent, embedded mode — no server). All sources share a single instance at `data/chroma_db/`.
- **LLM**: Claude (Anthropic API) — planned for the comparator agent.
- **Multi-source CLI**: Both `core/embedder.py` and `core/query.py` accept `--source olg|fns|cmr` to target any source.

### OLG Pipeline (`sources/olg/`)

Fully complete. Source is a MadCap Flare WebHelp site scraped via HTTP.

| Module | Role |
|--------|------|
| `sources/olg/extractor.py` | HAR file → `policy_urls.txt` + `policy_manifest.json` + `policy_toc.json` |
| `sources/olg/parser.py` | Pure HTML parser (no I/O). Called by scraper. Extracts sections at H2/H3 boundaries, tables, internal links, last-updated dates. |
| `sources/olg/scraper.py` | Orchestrates fetching, calls parser, saves one JSON per page to `data/olg/scraped_pages/`. Resumable with progress tracking. |
| `sources/olg/chunker.py` | Two-tier output: page-level docs (1,202) + section-level chunks (~6,785). Smart merge (<200 chars) and split (>1,500 chars). Tables inlined at `[Table]` placeholders. Context prefix prepended. |

**ChromaDB collections**: `pages` (1,202 docs), `sections` (6,785 chunks)

**Key data flow**: The chunker prepends a context prefix like `"SNAP > Application Processing > Expedited Benefits > Step One"` to every chunk before embedding, so the embedding captures hierarchical context.

### FNS Pipeline (`sources/fns/`)

Fully complete (parse, chunk, embed, query).

| Module | Role |
|--------|------|
| `sources/fns/parser.py` | PDF → structured JSON sections via pdfplumber. Handles side-by-side example boxes (47 pages) with column-aware extraction, cross-reference extraction, section hierarchy. |
| `sources/fns/chunker.py` | Two-tier output: chapter-level docs (14) + section-level chunks (722). Same merge/split logic. Context prefix: `"FNS 310 > Chapter 10: Income > 1021.1 Positive Allegation"`. |

**ChromaDB collections**: `fns_chapters` (14 docs), `fns_sections` (722 chunks)

**Parsed output**: 482 JSON files in `data/fns/parsed_sections/`, one per handbook section.

### CMR Pipeline (`sources/cmr/`)

Fully complete (parse, chunk, embed, query).

| Module | Role |
|--------|------|
| `sources/cmr/parser.py` | 18 CMR PDFs → structured JSON sections via pdfplumber. Chapter-filtered section detection, TOC boundary detection, continuation page merging, character-level dedup for one doubled-font PDF (704), cross-reference and table extraction. |
| `sources/cmr/chunker.py` | Two-tier output: chapter-level docs (18) + section-level chunks (1,275). Same merge/split logic. Context prefix: `"106 CMR 362 > SNAP Nonfinancial Eligibility > 362.330 Good Cause Criteria"`. |

**ChromaDB collections**: `cmr_chapters` (18 docs), `cmr_sections` (1,275 chunks)

**Parsed output**: 592 JSON files in `data/cmr/parsed_sections/`, one per regulation section.

### Shared Core Modules (`core/`)

| Module | Role |
|--------|------|
| `core/embedder.py` | Batch embedding via Voyage AI → ChromaDB. `--source olg\|fns\|cmr` flag routes to correct chunk files and collections. Token-aware batching, resume support, cost estimation, `--dry-run`, `--force`, `--only`. |
| `core/query.py` | Three interfaces: CLI, Python API (`search()` / `create_client(source)` + `search_with_client()`), JSON output. `--source olg\|fns\|cmr` flag. Program filtering (OLG/CMR), similarity scoring, parent context fetching, source-specific display formatting. |

### Roadmap

1. **Comparator agent** (in development): Purpose-built research tool for cross-source analysis — compares any two sources to find agreement, gaps, and conflicts. Lives in `agents/`.
2. **Policy search engine**: The broad-use tool for policy analysts. Accepts a question, orchestrates queries across all sources in the right order, and returns well-organized results. This is the system's primary daily-use interface.
3. **Web UI**: Frontend for the policy search engine. Key priority — the target audience is non-technical policy staff who need a clean, accessible interface.

## Commands

All commands run from the project root (`policy_navigator/`).

### Querying (all sources)
```bash
# OLG (default)
python core/query.py "income deduction"
python core/query.py "expedited SNAP" --program SNAP
python core/query.py "benefit calculation" --top 10 --full
python core/query.py "eligibility rules" --collection pages
python core/query.py "income limits" --context
python core/query.py "work requirements" --json
python core/query.py --list-programs

# FNS
python core/query.py "income deduction" --source fns
python core/query.py "income" --source fns --collection chapters
python core/query.py --source fns --list-programs

# CMR
python core/query.py "income deduction" --source cmr
python core/query.py "income" --source cmr --collection chapters
python core/query.py "work requirements" --source cmr --program SNAP
python core/query.py --source cmr --list-programs
```

### Embedding
```bash
python core/embedder.py --source olg --dry-run       # Cost estimate
python core/embedder.py --source fns                  # Embed FNS
python core/embedder.py --source cmr                  # Embed CMR
python core/embedder.py --source cmr --force          # Re-embed from scratch
python core/embedder.py --source fns --only chapters  # Selective
```

### Parsing (already complete for all sources)
```bash
# OLG
python sources/olg/extractor.py                       # HAR → URLs + TOC
python sources/olg/scraper.py                         # Fetch all pages
python sources/olg/chunker.py                         # Generate chunks
python sources/olg/chunker.py --stats                 # Statistics only

# FNS
python sources/fns/parser.py                          # Parse full handbook
python sources/fns/parser.py --chapter 10             # Parse one chapter
python sources/fns/chunker.py                         # Generate chunks
python sources/fns/chunker.py --stats                 # Statistics only

# CMR
python sources/cmr/parser.py                          # Parse all 18 PDFs
python sources/cmr/parser.py --chapter 362            # Parse one chapter
python sources/cmr/chunker.py                         # Generate chunks
python sources/cmr/chunker.py --stats                 # Statistics only
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

Single unified `config.ini` at project root (gitignored). Key settings:

- **Voyage AI rate limits**: Configured for paid accounts (`rate_limit_delay = 0.2`, `max_tokens_per_batch = 0`).
- **ChromaDB**: All collections live in `data/chroma_db/`. Collection names configured in `[chromadb]` section: `pages`, `sections` (OLG), `fns_chapters`, `fns_sections`, `cmr_chapters`, `cmr_sections`.
- **Embedding note**: Document embeddings were created WITHOUT `input_type="document"`, so queries must NOT use `input_type="query"` — asymmetry would degrade results.
- **CMR doubled PDF**: `jud-lib-106cmr704.pdf` listed in `[cmr] doubled_pdfs` — parser applies character-level dedup.

## Project Structure

```
policy_navigator/
├── CLAUDE.md
├── .gitignore
├── requirements.txt
├── config.ini                    ← unified config (gitignored)
│
├── sources/
│   ├── olg/                      ← extractor, parser, scraper, chunker
│   ├── fns/                      ← parser, chunker
│   └── cmr/                      ← parser, chunker
│
├── core/
│   ├── embedder.py               ← shared embedding pipeline (--source olg|fns|cmr)
│   └── query.py                  ← shared query interface (--source olg|fns|cmr)
│
├── agents/                       ← placeholder (comparator, orchestrator)
├── ui/                           ← placeholder (web UI)
│
├── data/
│   ├── olg/                      ← scraped_pages/, page_chunks.json, section_chunks.json
│   ├── fns/                      ← parsed_sections/, chapter_chunks.json, section_chunks.json
│   ├── cmr/                      ← parsed_sections/, chapter_chunks.json, section_chunks.json
│   └── chroma_db/                ← shared vector store (all 6 collections)
│
├── docs/
│   ├── olg_pipeline.md
│   ├── fns_pipeline.md
│   ├── cmr_pipeline.md
│   ├── cmr_analysis.md
│   ├── cmr_brainstorm.md
│   └── fns_brainstorm.md
│
└── source_files/                 ← PDFs, HAR files (gitignored)
    ├── cmr/                      ← 18 CMR chapter PDFs
    └── FNS Handbook 310 1.13.26.pdf
```

## Conventions

- **One JSON file per parsed unit**: OLG produces one JSON per page, FNS one per section, CMR one per section. Easy to inspect, debug, and reprocess individually.
- **Flat section lists with level numbers** instead of nested trees — simpler for chunkers to iterate while preserving hierarchy.
- **Context prefixes** prepended to chunk text before embedding so embeddings capture hierarchical position.
- **Stable, readable chunk IDs**: e.g., `sec__SNAP__AppProcessing__...` (OLG), `fns_sec_1021_1__000` (FNS), `cmr_sec_362_330__000` (CMR).
- **Two-tier chunking**: Broad documents (page/chapter level) for topic discovery + granular chunks (section level) for specific answers.
- **Python API pattern**: `search()` for one-off convenience, `create_client(source)` + `search_with_client()` for agent loops that need to avoid re-initialization.
- **Source-agnostic core modules**: `embedder.py` and `query.py` use `_resolve_source_paths()` / `_resolve_source_config()` — adding a new source requires one dict per resolver function.
- All modules use `configparser` for settings, `argparse` for CLI, and `pathlib` for paths.
- **Path resolution**: Scripts in `sources/*/` use `PROJECT_ROOT = Path(__file__).resolve().parents[2]`. Scripts in `core/` use `PROJECT_ROOT = Path(__file__).resolve().parents[1]`.

## Key Design Decisions

1. **ChromaDB over alternatives**: Metadata filtering is essential (filter by program, date, section type). Three consumer types need different query patterns. Embedded mode means no server to manage.
2. **Voyage AI for embeddings**: Anthropic's recommended embedding provider for use with Claude. Strong retrieval quality for domain-specific text.
3. **JSON per-page/section output**: Chosen over SQLite for inspectability and debuggability during development. May migrate later.
4. **FNS section detection via regex**: The PDF has no bookmarks or tagged structure. Numbered section patterns (`100 GENERAL.`) at line start are validated against known chapter ranges to distinguish from inline references.
5. **CMR section detection filtered by chapter prefix**: Each PDF is one chapter. Only `XXX.XXX:` patterns matching the chapter prefix are treated as section headings — avoids false positives from cross-references that happen to start at the beginning of a line.
6. **CMR chunk strategy**: Chunk at CMR section level (e.g., `362.330`), NOT at sub-items. Deep nested `(A)(1)(a)(b)(c)` structure preserved within each chunk. Continuation pages merged before chunking.
7. **Comparator is source-pair-agnostic**: Designed to compare any two sources (OLG vs CMR, CMR vs FNS, OLG vs FNS), not hardcoded to one pair.

## Important File Locations

- **OLG scraped data**: `data/olg/scraped_pages/*.json` (~1,202 files)
- **FNS parsed data**: `data/fns/parsed_sections/*.json` (~482 files)
- **CMR parsed data**: `data/cmr/parsed_sections/*.json` (~592 files)
- **Shared vector store**: `data/chroma_db/` (6 collections)
- **FNS source PDF**: `source_files/FNS Handbook 310 1.13.26.pdf`
- **CMR source PDFs**: `source_files/cmr/*.pdf` (18 files)
- **Pipeline documentation**: `docs/olg_pipeline.md`, `docs/fns_pipeline.md`, `docs/cmr_pipeline.md`

### User Preferences
- **Incremental Development**: One component at a time
- **Quality Over Speed**: Robust, well-tested components
- **Anti-Feature Creep**: Focused requests without assumptions
- **Windows Environment**: All code must work on Windows PC
- **Enhancement Protocol**: Always offer suggestions to take requests to the next level, but NEVER implement enhancements without explicit approval. Stick to the exact scope requested until user approves additional changes. However, you may push back on instructions if they would be harmful, cumbersome, follow worst practices, or be overly complicated.
- **NO COP-OUT ANSWERS**: NEVER give up on solving technical problems or provide "that's good enough" responses when something clearly isn't working. Always debug thoroughly and find the actual root cause. If an UPDATE statement isn't working, investigate why instead of suggesting workarounds.
- **FOLLOW INSTRUCTIONS EXACTLY**: When user gives specific values or instructions (e.g., "set all to 300"), implement EXACTLY what was requested. Do not improvise variations (300/350/400) or interpret creatively. If the instruction is unclear, ask for clarification. Do not second-guess explicit directives.
- **Git Workflow**: Offer to commit after completing each meaningful unit of work (pipeline stage, bug fix, refactor, etc.). Offer to push to GitHub periodically so the remote backup stays current. User controls timing — always ask, never auto-commit or auto-push. Repo: `klmn800/policy-navigator` (private).
