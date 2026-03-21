# Policy Navigator

Multi-source RAG system for Massachusetts DTA (Department of Transitional Assistance) policy. Indexes three authoritative sources and finds agreement, gaps, and conflicts between them.

## Sources (priority order)

1. **OLG** (Online Guide) -- DTA's internal staff guide. ~1,200 HTML pages. What workers follow day-to-day.
2. **CMR** (Code of Massachusetts Regulations, 106 CMR) -- State regulations the OLG implements. 18 PDFs, ~360 pages.
3. **FNS Handbook 310** -- Federal SNAP Quality Control standard. Single PDF, 306 pages, 483 sections.

All three sources are fully parsed, chunked, embedded, and searchable via a shared ChromaDB instance.

## Components

### Pipelines (`sources/`)

Each source follows **Parse > Chunk > Embed > Query**:

| Source | Parser | Output |
|--------|--------|--------|
| OLG | `sources/olg/scraper.py` + `parser.py` | 1,202 pages |
| FNS | `sources/fns/parser.py` | 482 sections |
| CMR | `sources/cmr/parser.py` | 592 sections |

Chunkers produce two tiers: broad documents (page/chapter level) for topic discovery, granular chunks (section level) for specific answers. Context prefixes baked into embeddings capture hierarchical position.

### Shared Core (`core/`)

- **`core/query.py`** -- Unified search interface. CLI + Python API. `--source olg|fns|cmr`, program filtering, similarity scoring, JSON output.
- **`core/embedder.py`** -- Batch embedding via Voyage AI. Token-aware batching, resume support, cost estimation.
- **`core/claude_code_runner.py`** -- Subprocess wrapper for Claude Code CLI sessions. Routes LLM work through subscription instead of per-token API. Captures session IDs for conversation resume.

### Comparator (`agents/comparator.py`)

Purpose-built research agent that compares FNS requirements against OLG coverage. Four-layer pipeline:

| Layer | Purpose | Engine |
|-------|---------|--------|
| L0 | Pre-classify FNS sections (compare vs skip) | Haiku API |
| L1 | Triage: RAG search + quick classification | Haiku API |
| L2 | Deep investigation: agentic search, 3-7 queries | Claude Code CLI (subscription) or API |
| L3 | CMR cross-check for confirmed gaps | Haiku API |

See [docs/comparator.md](docs/comparator.md) for the full workflow diagram and details.

### QC Gap Analyzer (`agents/qc_analyzer.py`)

Analyzes QC error reports to identify OLG guidance gaps that may have contributed to caseworker errors.

## Quick Start

```bash
pip install -r requirements.txt
# Configure config.ini (see config.ini.example or CLAUDE.md)

# Search any source
python core/query.py "income verification" --source olg
python core/query.py "income deduction" --source fns
python core/query.py "work requirements" --source cmr --program SNAP
python core/query.py "income verification" --source olg --exclude-programs "TAFDC,EAEDC"

# Run comparator (Claude Code engine, recommended)
python agents/comparator.py --chapter 10 --engine claude-code

# Run comparator with parallel L2 (5 concurrent workers)
python agents/comparator.py --chapter 10 --engine claude-code --parallel 5

# Run comparator (API engine)
python agents/comparator.py --chapter 10 --engine api

# Compile results from a previous run
python agents/comparator.py --compile --chapter 10
```

## Project Structure

```
policy_navigator/
├── sources/
│   ├── olg/          # scraper, parser, extractor, chunker
│   ├── fns/          # parser, chunker
│   └── cmr/          # parser, chunker
├── core/
│   ├── query.py      # unified search (--source olg|fns|cmr)
│   ├── embedder.py   # batch embedding pipeline
│   └── claude_code_runner.py  # Claude Code CLI wrapper
├── agents/
│   ├── comparator.py          # FNS vs OLG comparison engine
│   ├── qc_analyzer.py         # QC error gap analysis
│   └── prompts/               # LLM prompt templates
├── data/
│   ├── olg/           # scraped pages, chunks
│   ├── fns/           # parsed sections, chunks
│   ├── cmr/           # parsed sections, chunks
│   ├── chroma_db/     # shared vector store (6 collections)
│   └── comparator/    # comparison results, CSVs
├── docs/              # pipeline docs, architecture notes
└── source_files/      # PDFs, HAR files (gitignored)
```

## Tech Stack

- **Embeddings**: Voyage AI `voyage-3` (1,024 dimensions)
- **Vector store**: ChromaDB (embedded mode, no server)
- **LLM**: Claude (Anthropic API for L0/L1/L3, Claude Code CLI for L2)
- **Platform**: Windows 10, Python 3.11+
