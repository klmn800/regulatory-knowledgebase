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

| Source | Scrape/Parse | Chunk | Embed | Query | Comparator |
|--------|-------------|-------|-------|-------|------------|
| OLG | COMPLETE | COMPLETE | COMPLETE | COMPLETE | N/A |
| FNS | COMPLETE (Phase 1) | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| CMR | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | N/A |

## Architecture

Each source follows the same pipeline pattern: **Parse → Chunk → Embed → Query**

### Shared Infrastructure
- **Embedding model**: Voyage AI `voyage-3` (1,024 dimensions). Single unified `config.ini` at project root.
- **Vector store**: ChromaDB (persistent, embedded mode — no server). All sources share a single instance at `data/chroma_db/`.
- **LLM**: Claude (Anthropic API) — used by the comparator agent (not yet built for FNS; planned).

### OLG Pipeline (`sources/olg/`)

Fully complete. Source is a MadCap Flare WebHelp site scraped via HTTP.

| Module | Role |
|--------|------|
| `sources/olg/extractor.py` | HAR file → `policy_urls.txt` + `policy_manifest.json` + `policy_toc.json` |
| `sources/olg/parser.py` | Pure HTML parser (no I/O). Called by scraper. Extracts sections at H2/H3 boundaries, tables, internal links, last-updated dates. |
| `sources/olg/scraper.py` | Orchestrates fetching, calls parser, saves one JSON per page to `data/olg/scraped_pages/`. Resumable with progress tracking. |
| `sources/olg/chunker.py` | Two-tier output: page-level docs (1,202) + section-level chunks (~6,785). Smart merge (<200 chars) and split (>1,500 chars). Tables inlined at `[Table]` placeholders. Context prefix prepended. |
| `core/embedder.py` | Batch embedding via Voyage AI → ChromaDB. Token-aware batching, resume support, cost estimation. |
| `core/query.py` | Three interfaces: CLI, Python API (`search()` / `create_client()` + `search_with_client()`), JSON output. Program filtering, similarity scoring, parent page context fetching. |

**ChromaDB collections**: `pages` (1,202 docs), `sections` (6,785 chunks)

**Key data flow**: The chunker prepends a context prefix like `"SNAP > Application Processing > Expedited Benefits > Step One"` to every chunk before embedding, so the embedding captures hierarchical context.

### FNS Pipeline (`sources/fns/`)

Phase 1 complete (parsing). Phases 2-3 not started.

| Module | Role | Status |
|--------|------|--------|
| `sources/fns/parser.py` | PDF → structured JSON sections via pdfplumber. Handles side-by-side example boxes (47 pages) with column-aware extraction, cross-reference extraction, section hierarchy. | COMPLETE |
| `sources/fns/chunker.py` | Mirror of OLG chunker pattern for FNS sections | NOT BUILT |
| `core/embedder.py` | Same pattern, targeting `fns_chapters` and `fns_sections` collections | NOT BUILT (FNS support) |
| `core/query.py` | Same pattern as OLG query | NOT BUILT (FNS support) |
| `agents/comparator.py` | FNS vs OLG comparison agent using Claude | NOT BUILT |

**Parsed output**: 482 JSON files in `data/fns/parsed_sections/`, one per handbook section. Filename format: `ch{NN}_{section_number}.json`.

**Planned ChromaDB collections**: `fns_chapters` (~14 docs), `fns_sections` (~482 chunks)

### CMR Pipeline (`sources/cmr/` — Not Started)

Will follow the same parse → chunk → embed → query pattern. Key difference: 18 separate PDFs, deeply nested legal structure `(A)(1)(a)(b)(c)` that must be preserved within chunks (chunk at the CMR section level, not sub-items).

**Planned collections**: `cmr_chapters`, `cmr_sections`

### Not Yet Built (Bigger Vision)
- **Orchestration layer**: Decides which sources to query and in what order based on the question
- **Synthesis agent**: Reasons across results from multiple collections, identifies agreement/gaps/conflicts
- **Web UI**: For policy staff (currently CLI-only)

## Commands

All commands run from the project root (`policy_navigator/`).

### OLG Pipeline
```bash
# Scraping (already complete — only re-run if source site updates)
python sources/olg/extractor.py                         # HAR → URLs + TOC
python sources/olg/scraper.py                           # Fetch all pages (resumable)
python sources/olg/scraper.py --batch 10                # Test with 10 pages
python sources/olg/scraper.py --program SNAP            # Scrape one program

# Chunking & Embedding
python sources/olg/chunker.py                           # Generate chunks from scraped pages
python sources/olg/chunker.py --stats                   # Show statistics only
python core/embedder.py --dry-run                       # Estimate cost without embedding
python core/embedder.py                                 # Embed into ChromaDB
python core/embedder.py --force                         # Re-embed from scratch

# Querying
python core/query.py "income deduction"                      # Basic search
python core/query.py "expedited SNAP" --program SNAP         # Filter by program
python core/query.py "benefit calculation" --top 10 --full   # More results, full text
python core/query.py "eligibility rules" --collection pages  # Search page-level docs
python core/query.py "income limits" --context               # Include parent page
python core/query.py "work requirements" --json              # Machine-readable output
python core/query.py --list-programs                         # Show available programs
```

### FNS Pipeline
```bash
# Parsing (already complete)
python sources/fns/parser.py                        # Parse full handbook
python sources/fns/parser.py --chapter 10           # Parse one chapter
python sources/fns/parser.py --pages 195-200        # Parse specific PDF pages
python sources/fns/parser.py --dry-run              # Show sections found, don't write
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

Single unified `config.ini` at project root (gitignored). Key settings:

- **Voyage AI rate limits**: Currently configured for reduced-rate accounts (`rate_limit_delay = 21`, `max_tokens_per_batch = 8000`). After adding a payment method on the Voyage dashboard, change to `rate_limit_delay = 0.2` and `max_tokens_per_batch = 0`.
- **ChromaDB**: All collections live in `data/chroma_db/`. Collection names are configured in the `[chromadb]` section.
- **Embedding note**: Document embeddings were created WITHOUT `input_type="document"`, so queries must NOT use `input_type="query"` — asymmetry would degrade results.

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
│   ├── fns/                      ← parser (chunker future)
│   └── cmr/                      ← empty placeholder
│
├── core/
│   ├── embedder.py               ← shared embedding pipeline
│   └── query.py                  ← shared query interface
│
├── agents/                       ← empty placeholder (comparator, orchestrator)
├── ui/                           ← empty placeholder (web UI)
│
├── data/
│   ├── olg/                      ← scraped_pages/, chunks, manifests
│   ├── fns/                      ← parsed_sections/, reports/
│   ├── cmr/                      ← empty placeholder
│   └── chroma_db/                ← shared vector store
│
├── docs/
│   ├── olg_pipeline.md
│   ├── fns_pipeline.md
│   ├── cmr_brainstorm.md
│   └── fns_brainstorm.md
│
└── source_files/                 ← PDFs, HAR files (gitignored)
```

## Conventions

- **One JSON file per parsed unit**: OLG produces one JSON per page (`data/olg/scraped_pages/`), FNS produces one JSON per section (`data/fns/parsed_sections/`). Easy to inspect, debug, and reprocess individually.
- **Flat section lists with level numbers** instead of nested trees — simpler for chunkers to iterate while preserving hierarchy.
- **Context prefixes** prepended to chunk text before embedding (e.g., `"SNAP > Application Processing > ..."`) so embeddings capture hierarchical position.
- **Stable, readable chunk IDs**: e.g., `sec__SNAP__AppProcessing__AppSNAP_ExpeditedBenefits__003` — derived from URL/section paths, not random UUIDs.
- **Two-tier chunking**: Broad documents (page/chapter level) for topic discovery + granular chunks (section level) for specific answers.
- **Python API pattern**: `search()` for one-off convenience, `create_client()` + `search_with_client()` for agent loops that need to avoid re-initialization.
- All modules use `configparser` for settings, `argparse` for CLI, and `pathlib` for paths.
- **Path resolution**: Scripts in `sources/*/` use `PROJECT_ROOT = Path(__file__).resolve().parents[2]`. Scripts in `core/` use `PROJECT_ROOT = Path(__file__).resolve().parents[1]`.

## Key Design Decisions

1. **ChromaDB over alternatives**: Metadata filtering is essential (filter by program, date, section type). Three consumer types need different query patterns. Embedded mode means no server to manage.
2. **Voyage AI for embeddings**: Anthropic's recommended embedding provider for use with Claude. Strong retrieval quality for domain-specific text.
3. **JSON per-page/section output**: Chosen over SQLite for inspectability and debuggability during development. May migrate later.
4. **FNS section detection via regex**: The PDF has no bookmarks or tagged structure. Numbered section patterns (`100 GENERAL.`) at line start are validated against known chapter ranges to distinguish from inline references.
5. **CMR chunk strategy differs**: Chunk at CMR section level (e.g., `362.330`), NOT at sub-items. Deep nested `(A)(1)(a)(b)(c)` structure must be preserved within each chunk.

## Important File Locations

- **OLG scraped data**: `data/olg/scraped_pages/*.json` (~1,202 files)
- **OLG vector store**: `data/chroma_db/` (shared with FNS)
- **FNS parsed data**: `data/fns/parsed_sections/*.json` (~482 files)
- **FNS source PDF**: `source_files/FNS Handbook 310 1.13.26.pdf`
- **Pipeline documentation**: `docs/olg_pipeline.md`, `docs/fns_pipeline.md`
- **Brainstorm docs**: `docs/cmr_brainstorm.md`, `docs/fns_brainstorm.md`

### User Preferences
- **Incremental Development**: One component at a time
- **Quality Over Speed**: Robust, well-tested components
- **Anti-Feature Creep**: Focused requests without assumptions
- **Windows Environment**: All code must work on Windows PC
- **Enhancement Protocol**: Always offer suggestions to take requests to the next level, but NEVER implement enhancements without explicit approval. Stick to the exact scope requested until user approves additional changes. However, you may push back on instructions if they would be harmful, cumbersome, follow worst practices, or be overly complicated.
- **NO COP-OUT ANSWERS**: NEVER give up on solving technical problems or provide "that's good enough" responses when something clearly isn't working. Always debug thoroughly and find the actual root cause. If an UPDATE statement isn't working, investigate why instead of suggesting workarounds.
- **FOLLOW INSTRUCTIONS EXACTLY**: When user gives specific values or instructions (e.g., "set all to 300"), implement EXACTLY what was requested. Do not improvise variations (300/350/400) or interpret creatively. If the instruction is unclear, ask for clarification. Do not second-guess explicit directives.
- **Git Workflow**: Offer to commit after completing each meaningful unit of work (pipeline stage, bug fix, refactor, etc.). Offer to push to GitHub periodically so the remote backup stays current. User controls timing — always ask, never auto-commit or auto-push. Repo: `klmn800/policy-navigator` (private).
