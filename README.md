# Policy Navigator

Multi-source RAG system for Massachusetts DTA (Department of Transitional Assistance) policy. Indexes four authoritative sources, searches across them, identifies gaps and conflicts, and authors new OLG content.

## Sources (priority order)

1. **OLG** (Online Guide) -- DTA's internal staff guide. ~1,200 HTML pages. What workers follow day-to-day.
2. **CMR** (Code of Massachusetts Regulations, 106 CMR) -- State regulations the OLG implements. 18 PDFs, ~360 pages.
3. **FNS Handbook 310** -- Federal SNAP Quality Control standard. Single PDF, 306 pages, 483 sections.
4. **7 CFR** (federal SNAP regulations) -- Parts 271-275, 280, 292. The federal codification that 106 CMR implements. 7 PDFs, 517 pages, 118 sections, 1,623 chunks. Section-level program labels (SNAP / Issuance / Administration / QC / Disaster / Summer-EBT) for audience filtering.

All four sources are fully parsed, chunked, embedded, and searchable via a shared ChromaDB instance.

## What It Does

| Capability | What | How to use it |
|-----------|------|---------------|
| **Search** | Ask policy questions, get synthesized answers with citations | Web UI or `rag/query.py` CLI |
| **Compare** | Find gaps between federal rules and OLG coverage | `apps/comparator/comparator.py` CLI |
| **Author** | Research, draft, and format new OLG pages | Web UI or `apps/author/author.py` CLI |
| **Report** | Browse comparator findings in a filterable HTML report | `apps/comparator/report.py --open` |

---

## Quick Start

```bash
pip install -r requirements.txt
# Copy config.ini.example to config.ini and add your Voyage + Anthropic API keys
cp config.ini.example config.ini
```

> **This repository ships code only — no policy data.** The source documents
> and the built index are not distributed. To run the tools end to end you must
> supply your own sources (see [`raw/README.md`](raw/README.md)) and build the
> index (see [`index/README.md`](index/README.md)). Without an index, the search
> and comparison tools have nothing to query.

### Web UI (recommended)

```bash
python ui/app.py
# Opens at http://127.0.0.1:8001
```

Three tabs:
- **Ask** -- Type a policy question, get a synthesized answer with evidence from OLG/CMR/FNS/CFR
- **Author** -- Enter an assignment, run the research/draft/format pipeline with buttons. Each run is versioned with navigable history.
- **History** -- Browse past searches

### CLI

```bash
# Search
python rag/query.py "income verification" --source olg
python rag/query.py "income deduction" --source fns --top 10 --full
python rag/query.py "work requirements" --source cmr --program SNAP
python rag/query.py "summer EBT eligibility" --source cfr
python rag/query.py "income limits" --exclude-programs "TAFDC,EAEDC"

# Author an OLG page
python apps/author/author.py "Consolidate all VC-1 scripts" --name vc1_scripts
python apps/author/author.py --name vc1_scripts --research-only
python apps/author/author.py --name vc1_scripts --draft-only
python apps/author/author.py --name vc1_scripts --resume

# Run comparator
python apps/comparator/comparator.py --chapter 10 --engine claude-code --parallel 5

# Generate HTML report from comparator results
python apps/comparator/report.py --open
```

---

## Architecture

### Data Pipeline

Each source follows **Parse > Chunk > Embed > Query**:

| Source | Parser | Documents | Chunks |
|--------|--------|-----------|--------|
| OLG | `rag/olg/scraper.py` + `parser.py` | 1,164 pages | 6,511 sections |
| FNS | `rag/fns/parser.py` | 14 chapters | 860 sections |
| CMR | `rag/cmr/parser.py` | 18 chapters | 1,415 sections |
| CFR | `rag/cfr/parser.py` | 7 parts | 1,623 sections |

Two-tier chunking: broad documents for topic discovery, granular chunks for specific answers. Context prefixes baked into embeddings capture hierarchical position (e.g., `SNAP > Application Processing > Expedited Benefits`).

### Search Engine (`ui/` + `tools/synthesis.py`)

FastAPI backend with HTMX frontend. No heavy JS framework -- server-rendered HTML partials.

- **Standard mode**: Pre-fetches from selected sources, single Claude API call to synthesize
- **Deep mode**: Agentic loop with iterative RAG searches (up to 8 rounds)
- Search history persisted to SQLite with full evidence snapshots

### Comparator (`apps/comparator/comparator.py`)

Four-layer pipeline comparing FNS requirements against OLG coverage:

| Layer | Purpose | Engine |
|-------|---------|--------|
| L0 | Pre-classify FNS sections (compare vs skip) | Haiku API |
| L1 | Triage: RAG search + quick classification | Haiku API |
| L2 | Deep investigation: agentic search, 3-7 queries | Claude Code CLI |
| L3 | CMR cross-check for confirmed gaps | Haiku API |

All 5 FNS policy chapters complete (270 sections analyzed). Results in `output/comparator/results/` with per-chapter CSVs. See [docs/comparator.md](docs/comparator.md).

### OLG Authoring Pipeline (`apps/author/author.py`)

Three-phase pipeline that takes a policy assignment and produces a formatted OLG page:

```
Assignment (text)
       |
       v
  Phase 1: RESEARCH          Anthropic API (synthesis)
  Multi-query RAG             ~$0.05-0.40, 30-120 seconds
  -> research_report.md
  -> research_evidence.json
       |
       v
  Phase 2: AUTHOR             Claude Code CLI (subscription, $0)
  Style guide + research      2-5 minutes, session resumable
  -> draft.md
  -> session_id.txt
       |
       v
  Phase 3: FORMAT             python-docx (no LLM)
  Markdown -> styled .docx    < 1 second
  -> output.docx
```

**Engine split rationale**: API for structured/cheap research. Claude Code for free/resumable drafting. python-docx for deterministic formatting.

The web UI launches the Claude Code drafting phase in a visible terminal window so you can watch it work and debug if needed.

**Reference materials** (gitignored, must be provided):
- `apps/author/references/2026 OLG Template.docx` -- Word template with OLG styles
- `apps/author/references/OLG Writer's Manual.docx` -- Writing rules
- `apps/author/references/sample_pages/` -- Example OLG pages for style analysis

**Style guide** (committed):
- `apps/author/references/olg_style_guide.md` -- Evidence-based guide extracted from the manual + 9 sample pages. Covers voice, structure, formatting, terminology, and page types.

Output goes to `output/author/{name}/` with all deliverables. UI-triggered runs create versioned subdirectories (`research/001_...`, `drafts/001_...`, `formats/001_...`) preserving full history with assignment text and metadata. Top-level files always hold the latest version.

### HTML Report (`apps/comparator/report.py`)

Single-page HTML report generated from comparator CSVs. Features: dark mode, favorites, expandable detail rows, filter by chapter/classification/findings. Session ID click copies the full `claude --resume <UUID>` command.

```bash
python apps/comparator/report.py --open
```

### RAG Core (`rag/`)

| Module | Role |
|--------|------|
| `rag/query.py` | Unified search. CLI + Python API. `--source olg\|fns\|cmr\|cfr`, program filtering, similarity scoring. |
| `rag/embedder.py` | Batch embedding via Voyage AI. Token-aware batching, resume, cost estimation. |

### Shared Tools (`tools/`)

| Module | Role |
|--------|------|
| `tools/synthesis.py` | RAG synthesis (standard + deep mode). Used by search engine and author research. |
| `tools/claude_code_runner.py` | Subprocess wrapper for Claude Code CLI. Piped or windowed mode. Session ID capture for resume. |
| `tools/docx_writer.py` | Markdown to styled .docx using OLG template. Handles headings, lists (XML numPr), tables, callouts. |

---

## Project Structure

```
policy_navigator/
├── config.ini               # API keys, model settings (gitignored; copy from config.ini.example)
├── config.ini.example       # template config with placeholder keys
├── requirements.txt
│
├── rag/                      # RAG pipeline (parse/chunk/embed/query)
│   ├── query.py              #   unified search (--source olg|fns|cmr|cfr)
│   ├── embedder.py           #   batch embedding pipeline
│   ├── olg/                  #   scraper, parser, extractor, chunker
│   ├── fns/                  #   parser, chunker
│   └── cmr/                  #   parser, chunker
│
├── tools/                    # Shared tools used by apps
│   ├── synthesis.py          #   RAG synthesis (standard + deep)
│   ├── claude_code_runner.py #   Claude Code CLI wrapper
│   └── docx_writer.py        #   markdown -> styled .docx
│
├── apps/                     # Purpose-built apps
│   ├── author/               #   OLG authoring pipeline
│   │   ├── author.py
│   │   ├── prompts/          #     author-specific prompt templates
│   │   └── references/       #     style guide + templates (docx gitignored)
│   │       └── olg_style_guide.md
│   ├── comparator/           #   FNS vs OLG comparison engine
│   │   ├── comparator.py
│   │   └── report.py         #     HTML report generator
│   └── qc/                   #   QC error gap analysis
│       └── qc_analyzer.py
│
├── prompts/                  # Shared LLM prompt templates
│   ├── domain_preamble.md
│   └── synthesis.md
│
├── ui/                       # Web interface
│   ├── app.py                #   FastAPI application
│   ├── search.py             #   Search service layer
│   ├── history.py            #   SQLite search history
│   ├── static/               #   CSS + JS
│   └── templates/            #   Jinja2 + HTMX
│
├── index/                    # Parsed/chunked/vector data (gitignored; see index/README.md)
│   ├── olg/                  #   scraped pages, chunks
│   ├── fns/                  #   parsed sections, chunks
│   ├── cmr/                  #   parsed sections, chunks
│   ├── cfr/                  #   parsed sections, chunks
│   └── chroma_db/            #   shared vector store (8 collections)
│
├── output/                   # Tool deliverables (gitignored; see output/README.md)
│   ├── comparator/           #   FNS-vs-OLG gap analysis
│   ├── author/               #   authoring pipeline outputs
│   └── qc_analysis/          #   QC error gap analyses (contains case data)
│
├── raw/                      # Source PDFs, HAR files (gitignored; see raw/README.md)
└── docs/                     # Architecture docs
```

## Configuration

Single `config.ini` at project root (gitignored). Key sections:

| Section | What it configures |
|---------|--------------------|
| `[api]` | Voyage AI and Anthropic API keys |
| `[embedding]` | Query model (`voyage-context-3`), batch size, rate limits |
| `[chromadb]` | Persist directory, collection names (8 total) |
| `[synthesis]` | Search engine model, token limits, search budget |
| `[author]` | Research model, template path, style guide path |
| `[comparator]` | Layer models, thresholds, chapter list |

**Embedding note**: Documents were embedded WITHOUT `input_type="document"`, so queries must NOT use `input_type="query"` -- asymmetry would degrade results.

## Tech Stack

- **Embeddings**: Voyage AI -- `voyage-4-large` (broad tier) + `voyage-context-3` (section tier)
- **Vector store**: ChromaDB (embedded mode, no server)
- **LLM**: Claude via Anthropic API (synthesis, comparator L0/L1/L3) and Claude Code CLI (comparator L2, authoring)
- **Web**: FastAPI + HTMX + Jinja2
- **Document generation**: python-docx
- **Platform**: Windows 10, Python 3.13+

## Detailed Documentation

- [OLG Pipeline](docs/olg_pipeline.md)
- [FNS Pipeline](docs/fns_pipeline.md)
- [CMR Pipeline](docs/cmr_pipeline.md)
- [CFR Pipeline](docs/cfr_pipeline.md)
- [Comparator](docs/comparator.md)
- [Search Engine Architecture](docs/search_engine_architecture.md)

## License

No license -- all rights reserved. This is a personal portfolio project, published
for viewing and reference only. You may not reuse, modify, or redistribute the code
without permission.

The policy sources it indexes (7 CFR, FNS Handbook 310, 106 CMR, and the DTA Online
Guide) belong to their respective publishers and are not included in this repository.
