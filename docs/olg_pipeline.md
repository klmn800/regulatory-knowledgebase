# DTA Online Guide — RAG Pipeline

## Project Goal

Build a RAG (Retrieval-Augmented Generation) system so AI agents can check policy writing against the Massachusetts DTA Online Policy Guide. The guide is a public-facing MadCap Flare WebHelp site with ~1,200 pages covering SNAP, TAFDC, EAEDC, and cross-program policy.

End users: AI agents, human policy writers, and programmatic search/retrieval.

## Source Site

- **Base URL**: `https://eohhs.ehs.state.ma.us/DTA/PolicyOnline/BEACON5/!SSL!/WebHelp/`
- **Content**: Clean, well-structured HTML with H1/H2/H3 headings, paragraphs, tables, lists
- **Page structure**: All content inside `<div id="rh-topic">`, "Last Update" date in H3 at bottom
- **Programs covered**: SNAP (205 pages), TAFDC (244), EAEDC (164), Cross-Program (275), BP (80), Pathways (57), COVID (39), Harper (34), plus smaller categories

---

## Phase 1: Scraping (COMPLETE)

### What was built

| File | Purpose |
|---|---|
| `extractor.py` | Reads HAR file, reconstructs TOC hierarchy, produces `policy_urls.txt` and `policy_manifest.json` |
| `parser.py` | Pure HTML parser — extracts title, sections (split at H2/H3), tables, internal links, last updated date |
| `scraper.py` | Orchestration — fetches pages, calls parser, saves JSON, tracks progress |
| `policy_urls.txt` | 1,204 fully qualified URLs (one per line) |
| `policy_manifest.json` | 1,289 entries with URL, title, and breadcrumb path from TOC hierarchy (85 are duplicates across TOC locations) |
| `policy_toc.json` | Full hierarchical TOC tree |
| `scraped_pages/*.json` | 1,202 structured JSON files (one per page) |

### Scrape results (2026-03-02)

- **1,202 / 1,202 pages scraped (100% success)**
- 0 failures, 0 404s
- 7.5 MB total on disk
- 4,917 sections extracted (avg 4.1 per page)
- 358 tables across 183 pages
- 4,273 internal cross-reference links
- Scrape time: ~34 minutes (1.5s delay between requests)

### Parser features

- Sections split at H2/H3 boundaries with level numbers (0=intro, 2=H2, 3=H3)
- Tables: colspan/rowspan support, layout table filtering (skips decorative image tables), semicolon-separated multi-item cells
- Lists: ordered/unordered with nested indentation preserved
- Internal links resolved to absolute URLs
- CDATA/script tag filtering
- Non-ASCII URL encoding (en-dash in filenames)

### Per-page JSON structure

```json
{
  "url": "https://...",
  "title": "Page Title from H1",
  "program": "SNAP",
  "breadcrumb": ["SNAP", "Application Processing"],
  "last_updated": "April 7, 2023",
  "sections": [
    {"heading": null, "level": 0, "text": "Intro text..."},
    {"heading": "Section Name", "level": 2, "text": "..."},
    {"heading": "Subsection", "level": 3, "text": "..."}
  ],
  "tables": [
    {"context_heading": "nearest heading", "headers": [...], "rows": [[...], ...]}
  ],
  "internal_links": [
    {"text": "Link Text", "href": "https://resolved/url"}
  ],
  "scraped_at": "2026-03-02T..."
}
```

### Key design decisions (Phase 1)

1. **JSON files per page** instead of SQLite — easy to inspect, debug, and re-process individual pages
2. **Flat section list with level numbers** instead of nested tree — simpler for the chunker to iterate; level number preserves hierarchy
3. **Manifest breadcrumbs** from the TOC give richer context than URL path parsing alone
4. **Tables extracted separately AND referenced in section text** as `[Table]` — in Phase 2, the chunker replaces `[Table]` with rendered table text so embeddings capture table data in context

---

## Phase 2: Chunking & Embedding (COMPLETE)

### Technology choices (decided)

| Component | Choice | Rationale |
|---|---|---|
| **Embedding model** | Voyage AI | Anthropic's recommended embedding provider for use with Claude. Strong retrieval quality for domain-specific text. Cost ~$0.50-1.00 for full dataset (one-time). |
| **Vector store** | ChromaDB | Built-in metadata filtering essential for this use case (filter by program, date, section type). Three consumer types (humans, AI agents, programs) need different query patterns. Embedded mode, no server needed. |
| **Chunking strategy** | Hierarchical (Option D) with smart merge/split (Option B) | Two-tier: page-level documents for broad topic matching + section-level chunks for specific answers. Merge tiny sections, split oversized ones. |

### Architecture

**Two ChromaDB collections:**

1. **`pages`** (~1,202 documents) — one per page, full concatenated text
   - For broad topic discovery: "Which policy covers expedited SNAP benefits?"
   - Metadata: url, program, breadcrumb, title, last_updated, section_count, has_tables

2. **`sections`** (~4,500-5,500 chunks after merge/split) — granular policy content
   - For specific answers: "What are the income limits for expedited service?"
   - Metadata: url, program, breadcrumb, page_title, section_heading, section_level, last_updated, chunk_index, parent_page_id
   - Text includes breadcrumb + heading prefix so embedding captures context

**Retrieval flow:**
1. Search `sections` for specific answers
2. Use `parent_page_id` to pull full page context if needed
3. Breadcrumb + heading metadata provides source attribution

**Smart merge/split rules:**
- Sections < ~200 chars → merge with next sibling section
- Sections > ~1,500 chars → split at paragraph boundaries, sub-chunks inherit heading
- `[Table]` placeholders replaced with rendered table text inline
- Every chunk gets breadcrumb + heading prepended as context prefix

### Chunking results (2026-03-02)

| Metric | Value |
|---|---|
| Page-level documents | 1,202 |
| Section-level chunks | 6,785 |
| Median chunk size | 960 chars |
| Max chunk size | 3,938 chars (was 33K before sentence splitting) |
| Sweet spot (500-1500 chars) | 65.2% |
| Small residuals (< 200 chars) | 4.8% (mostly "Related Topics" lists) |
| Output files | `page_chunks.json` (6.3 MB), `section_chunks.json` (10.5 MB) |

**Chunker features:**
- Three-tier split strategy: paragraph boundaries → single newlines → sentence boundaries
- Forward-merge for tiny sections (< 200 chars), keeps "Related Topics" as-is
- Table text rendered inline (pipe-delimited format) at `[Table]` placeholder positions
- Context prefix prepended: `"SNAP > Application Processing > Expedited Benefits > Step One"`
- Continued chunks get `"(heading) (continued)"` suffix
- Stable chunk IDs: `sec__SNAP__AppProcessing__AppSNAP_ExpeditedBenefits__003`

### Modules status

| File | Purpose | Status |
|---|---|---|
| `chunker.py` | Reads `scraped_pages/`, produces chunks with merge/split + hierarchical structure | Complete |
| `embedder.py` | Calls Voyage AI API, stores in ChromaDB | Complete |
| `query.py` | Search interface for humans, agents, and programs | Complete |
| `config.ini` | API keys, model names, collection settings | Complete |

### Embedding results (2026-03-02)

| Metric | Value |
|---|---|
| Total chunks embedded | 7,051 (1,202 pages + 5,849 sections) |
| Total tokens | 1,688,645 |
| Total cost | $0.10 |
| Model | voyage-3 (1,024 dimensions) |
| Vector store | ChromaDB persistent at `index/chroma_db/` |
| Collections | `pages` (1,202 docs), `sections` (6,785 chunks) |

**Config notes:**
- Rate limits: 3 RPM / 10K TPM (no payment method on Voyage dashboard yet)
- `config.ini` has `rate_limit_delay = 21` and `max_tokens_per_batch = 8000` for reduced limits
- After adding payment method to Voyage: change to `rate_limit_delay = 0.2` and `max_tokens_per_batch = 0`

### Dependencies

```
beautifulsoup4
voyageai
chromadb
```

---

## Phase 3: Query Interface (COMPLETE)

### What was built

`rag/query.py` — a search interface serving three audiences:

1. **Humans (CLI)** — `python rag/query.py "income deduction"` with formatted output
2. **AI agents (Python API)** — `from query import search` or `create_client()` + `search_with_client()` for repeated queries
3. **Programs (JSON)** — `python rag/query.py "income deduction" --json`

### CLI flags

| Flag | Purpose |
|---|---|
| `query` (positional) | Natural language search text |
| `--collection` / `-c` | `sections` (default) or `pages` |
| `--program` / `-p` | Filter by program (case-insensitive) |
| `--top` / `-n` | Number of results (default: 5) |
| `--threshold` / `-t` | Minimum similarity score 0-1 |
| `--context` | Include full parent page text for section results |
| `--json` | Machine-readable JSON output |
| `--full` | Show full text (default truncates to 300 chars) |
| `--list-programs` | Show all programs with chunk counts |

### Python API

```python
# One-shot query (initializes clients internally)
from query import search
results = search("income deduction", program="SNAP", top_n=5)

# Reusable clients for agent loops (avoids re-initialization)
from query import create_client, search_with_client
clients = create_client()
r1 = search_with_client("income deduction", clients, program="SNAP")
r2 = search_with_client("expedited benefits", clients)
```

### Features

- **Similarity scores** converted from L2 distance to intuitive 0-1 scale
- **Program filtering** with case-insensitive matching and "did you mean?" suggestions
- **Parent page context** fetching via `parent_page_id` metadata
- **Rate limit retry** with exponential backoff (25s × attempt) for reduced-rate Voyage accounts
- **Source attribution**: breadcrumb paths, URLs, page titles, last updated dates

### Design decisions (Phase 3)

1. **Default to `sections` collection** — most useful for specific policy answers. Use `--collection pages` for topic discovery.
2. **Plain dicts for API return type** — JSON-serializable, no extra imports, matches ChromaDB patterns.
3. **No `input_type` on query embedding** — document embeddings were created without `input_type="document"`, so query must not use `input_type="query"` (asymmetry would degrade results). Future improvement: re-embed with input_type set.
4. **Two-tier Python API** — `search()` for convenience, `create_client()` + `search_with_client()` for performance in agent loops.

---

## Project files reference

```
policy_navigator/
├── rag/
│   ├── olg/
│   │   ├── extractor.py        ← HAR → URL list + TOC hierarchy
│   │   ├── parser.py           ← HTML → structured JSON (pure parser)
│   │   ├── scraper.py          ← Fetch + parse + save (orchestration)
│   │   └── chunker.py          ← JSON → chunks with merge/split
│   ├── embedder.py             ← Chunks → Voyage AI → ChromaDB (shared)
│   └── query.py                ← Search interface — CLI, Python API, JSON (shared)
│
├── index/
│   ├── olg/
│   │   ├── scraped_pages/      ← 1,202 JSON files
│   │   ├── page_chunks.json    ← 1,202 page-level documents
│   │   ├── section_chunks.json ← 6,785 section-level chunks
│   │   ├── policy_urls.txt     ← 1,204 URLs (flat list)
│   │   ├── policy_manifest.json← URLs + titles + breadcrumbs
│   │   ├── policy_toc.json     ← Full hierarchical TOC
│   │   ├── scrape_progress.json← Scraper resume state
│   │   └── scrape_report.txt   ← Scrape summary
│   └── chroma_db/              ← ChromaDB persistent storage (shared)
│
└── raw/                        ← Source files (gitignored)
```

---

## Running the tools

```bash
# Phase 1 (already complete)
python rag/olg/extractor.py                    # HAR → URLs + TOC
python rag/olg/scraper.py                      # Fetch all pages
python rag/olg/scraper.py --batch 10           # Test with 10 pages
python rag/olg/scraper.py --program SNAP       # Scrape one program
python rag/olg/scraper.py --retry-failed       # Re-attempt failures

# Phase 2 (complete)
python rag/olg/chunker.py                      # Generate chunks from scraped pages
python rag/embedder.py --source olg            # Embed chunks and store in ChromaDB

# Phase 3 — Query (complete)
python rag/query.py "income deduction"                    # Basic search
python rag/query.py "expedited SNAP" --program SNAP       # Filter by program
python rag/query.py "benefit calculation" --top 10        # More results
python rag/query.py "eligibility rules" --collection pages  # Search pages
python rag/query.py "income limits" --context             # Include parent page
python rag/query.py "work requirements" --json            # JSON output
python rag/query.py --list-programs                       # Show programs
```
