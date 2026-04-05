# Policy Navigator

Multi-source RAG system for Massachusetts DTA (Department of Transitional Assistance) policy. Indexes three authoritative sources, searches across them, identifies gaps and conflicts, and authors new OLG content.

## Sources (priority order)

1. **OLG** (Online Guide) -- DTA's internal staff guide. ~1,200 HTML pages. What workers follow day-to-day.
2. **CMR** (Code of Massachusetts Regulations, 106 CMR) -- State regulations the OLG implements. 18 PDFs, ~360 pages.
3. **FNS Handbook 310** -- Federal SNAP Quality Control standard. Single PDF, 306 pages, 483 sections.

All three sources are fully parsed, chunked, embedded, and searchable via a shared ChromaDB instance.

## What It Does

| Capability | What | How to use it |
|-----------|------|---------------|
| **Search** | Ask policy questions, get synthesized answers with citations | Web UI or `core/query.py` CLI |
| **Compare** | Find gaps between federal rules and OLG coverage | `agents/comparator.py` CLI |
| **Author** | Research, draft, and format new OLG pages | Web UI or `agents/author.py` CLI |
| **Report** | Browse comparator findings in a filterable HTML report | `agents/report.py --open` |

---

## Quick Start

```bash
pip install -r requirements.txt
# Copy config.ini.example to config.ini and add your API keys
```

### Web UI (recommended)

```bash
python ui/app.py
# Opens at http://127.0.0.1:8001
```

Three tabs:
- **Ask** -- Type a policy question, get a synthesized answer with evidence from OLG/CMR/FNS
- **Author** -- Enter an assignment, run the research/draft/format pipeline with buttons
- **History** -- Browse past searches

### CLI

```bash
# Search
python core/query.py "income verification" --source olg
python core/query.py "income deduction" --source fns --top 10 --full
python core/query.py "work requirements" --source cmr --program SNAP
python core/query.py "income limits" --exclude-programs "TAFDC,EAEDC"

# Author an OLG page
python agents/author.py "Consolidate all VC-1 scripts" --name vc1_scripts
python agents/author.py --name vc1_scripts --research-only
python agents/author.py --name vc1_scripts --draft-only
python agents/author.py --name vc1_scripts --resume

# Run comparator
python agents/comparator.py --chapter 10 --engine claude-code --parallel 5

# Generate HTML report from comparator results
python agents/report.py --open
```

---

## Architecture

### Data Pipeline

Each source follows **Parse > Chunk > Embed > Query**:

| Source | Parser | Documents | Chunks |
|--------|--------|-----------|--------|
| OLG | `sources/olg/scraper.py` + `parser.py` | 1,202 pages | 6,785 sections |
| FNS | `sources/fns/parser.py` | 14 chapters | 722 sections |
| CMR | `sources/cmr/parser.py` | 18 chapters | 1,275 sections |

Two-tier chunking: broad documents for topic discovery, granular chunks for specific answers. Context prefixes baked into embeddings capture hierarchical position (e.g., `SNAP > Application Processing > Expedited Benefits`).

### Search Engine (`ui/` + `agents/synthesis.py`)

FastAPI backend with HTMX frontend. No heavy JS framework -- server-rendered HTML partials.

- **Standard mode**: Pre-fetches from selected sources, single Claude API call to synthesize
- **Deep mode**: Agentic loop with iterative RAG searches (up to 8 rounds)
- Search history persisted to SQLite with full evidence snapshots

### Comparator (`agents/comparator.py`)

Four-layer pipeline comparing FNS requirements against OLG coverage:

| Layer | Purpose | Engine |
|-------|---------|--------|
| L0 | Pre-classify FNS sections (compare vs skip) | Haiku API |
| L1 | Triage: RAG search + quick classification | Haiku API |
| L2 | Deep investigation: agentic search, 3-7 queries | Claude Code CLI |
| L3 | CMR cross-check for confirmed gaps | Haiku API |

All 5 FNS policy chapters complete (270 sections analyzed). Results in `data/comparator/results/` with per-chapter CSVs. See [docs/comparator.md](docs/comparator.md).

### OLG Authoring Pipeline (`agents/author.py`)

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
- `agents/references/2026 OLG Template.docx` -- Word template with OLG styles
- `agents/references/OLG Writer's Manual.docx` -- Writing rules
- `agents/references/sample_pages/` -- Example OLG pages for style analysis

**Style guide** (committed):
- `agents/references/olg_style_guide.md` -- Evidence-based guide extracted from the manual + 9 sample pages. Covers voice, structure, formatting, terminology, and page types.

Output goes to `data/author/{name}/` with all deliverables.

### HTML Report (`agents/report.py`)

Single-page HTML report generated from comparator CSVs. Features: dark mode, favorites, expandable detail rows, filter by chapter/classification/findings. Session ID click copies the full `claude --resume <UUID>` command.

```bash
python agents/report.py --open
```

### Shared Core (`core/`)

| Module | Role |
|--------|------|
| `core/query.py` | Unified search. CLI + Python API. `--source olg\|fns\|cmr`, program filtering, similarity scoring. |
| `core/embedder.py` | Batch embedding via Voyage AI. Token-aware batching, resume, cost estimation. |
| `core/claude_code_runner.py` | Subprocess wrapper for Claude Code CLI. Piped or windowed mode. Session ID capture for resume. |
| `core/docx_writer.py` | Markdown to styled .docx using OLG template. Handles headings, lists (XML numPr), tables, callouts. |

---

## Project Structure

```
policy_navigator/
├── config.ini               # API keys, model settings (gitignored)
├── requirements.txt
│
├── sources/                  # Parse/chunk pipelines
│   ├── olg/                  #   scraper, parser, extractor, chunker
│   ├── fns/                  #   parser, chunker
│   └── cmr/                  #   parser, chunker
│
├── core/                     # Shared infrastructure
│   ├── query.py              #   unified search (--source olg|fns|cmr)
│   ├── embedder.py           #   batch embedding pipeline
│   ├── claude_code_runner.py #   Claude Code CLI wrapper
│   └── docx_writer.py        #   markdown -> styled .docx
│
├── agents/                   # Higher-level tools
│   ├── author.py             #   OLG authoring pipeline
│   ├── synthesis.py          #   RAG synthesis (standard + deep)
│   ├── comparator.py         #   FNS vs OLG comparison engine
│   ├── qc_analyzer.py        #   QC error gap analysis
│   ├── report.py             #   HTML report generator
│   ├── prompts/              #   LLM prompt templates
│   │   ├── domain_preamble.md
│   │   ├── synthesis.md
│   │   ├── author_research.md
│   │   └── author_draft.md
│   └── references/           #   Style guide + templates (docx gitignored)
│       └── olg_style_guide.md
│
├── ui/                       # Web interface
│   ├── app.py                #   FastAPI application
│   ├── search.py             #   Search service layer
│   ├── history.py            #   SQLite search history
│   ├── static/               #   CSS + JS
│   └── templates/            #   Jinja2 + HTMX
│
├── data/                     # Generated data (mostly gitignored)
│   ├── olg/                  #   scraped pages, chunks
│   ├── fns/                  #   parsed sections, chunks
│   ├── cmr/                  #   parsed sections, chunks
│   ├── chroma_db/            #   shared vector store (6 collections)
│   ├── comparator/           #   comparison results, CSVs
│   └── author/               #   authoring pipeline outputs
│
├── docs/                     # Architecture docs
└── source_files/             # PDFs, HAR files (gitignored)
```

## Configuration

Single `config.ini` at project root (gitignored). Key sections:

| Section | What it configures |
|---------|--------------------|
| `[api]` | Voyage AI and Anthropic API keys |
| `[embedding]` | Model (`voyage-3`), batch size, rate limits |
| `[chromadb]` | Persist directory, collection names (6 total) |
| `[synthesis]` | Search engine model, token limits, search budget |
| `[author]` | Research model, template path, style guide path |
| `[comparator]` | Layer models, thresholds, chapter list |

**Embedding note**: Documents were embedded WITHOUT `input_type="document"`, so queries must NOT use `input_type="query"` -- asymmetry would degrade results.

## Tech Stack

- **Embeddings**: Voyage AI `voyage-3` (1,024 dimensions)
- **Vector store**: ChromaDB (embedded mode, no server)
- **LLM**: Claude via Anthropic API (synthesis, comparator L0/L1/L3) and Claude Code CLI (comparator L2, authoring)
- **Web**: FastAPI + HTMX + Jinja2
- **Document generation**: python-docx
- **Platform**: Windows 10, Python 3.13+

## Detailed Documentation

- [OLG Pipeline](docs/olg_pipeline.md)
- [FNS Pipeline](docs/fns_pipeline.md)
- [CMR Pipeline](docs/cmr_pipeline.md)
- [Comparator](docs/comparator.md)
- [Search Engine Architecture](docs/search_engine_architecture.md)
