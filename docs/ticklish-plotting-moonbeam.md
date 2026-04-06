# Policy Navigator — Directory Reorganization Plan

## Context

The project started as `new_olg_rag`, grew to include `fns_handbook_rag`, and now needs CMR support too. The two sub-projects were dropped into a new `policy_navigator/` directory but are still organized as independent sibling projects with duplicated configs, scattered docs, and cross-directory path hacks (`../new_olg_rag/chroma_db`). This reorganization creates a unified structure that scales to any number of policy sources and separates concerns cleanly: source-specific ingestion code, shared infrastructure, data, and documentation.

## Target Structure

> **Note**: This was the original migration plan from `new_olg_rag/` + `fns_handbook_rag/` into
> `policy_navigator/`. The project has since been restructured further into the current layout
> (`rag/`, `tools/`, `programs/`, `index/`, `output/`, `raw/`). This document is preserved for
> historical reference.

```
policy_navigator/
├── CLAUDE.md
├── .gitignore
├── requirements.txt
├── config.ini
│
├── rag/
│   ├── olg/                 ← extractor, parser, scraper, chunker
│   ├── fns/                 ← parser, chunker
│   ├── cmr/                 ← parser, chunker
│   ├── embedder.py          ← shared embedding pipeline
│   └── query.py             ← shared query interface
│
├── tools/                   ← shared utilities
├── programs/                ← comparator, author, qc
├── ui/                      ← web interface
│
├── index/
│   ├── olg/                 ← scraped_pages/, chunks, manifests
│   ├── fns/                 ← parsed_sections/, chunks
│   ├── cmr/                 ← parsed_sections/, chunks
│   └── chroma_db/           ← shared vector store
│
├── output/                  ← comparator results, author outputs
│
├── docs/
│   ├── olg_pipeline.md
│   ├── fns_pipeline.md
│   ├── cmr_brainstorm.md
│   └── fns_brainstorm.md
│
└── raw/                     ← PDFs, HAR files (gitignored)
```

## Migration Steps

### Step 1: Create directory skeleton

Create all new directories (empty). Nothing moves yet, nothing breaks.

```
rag/olg/
rag/fns/
rag/cmr/
tools/
programs/
ui/
index/olg/
index/fns/
index/cmr/
output/
docs/
raw/
```

### Step 2: Create unified root files

**`.gitignore`** — Merge both existing .gitignore files into one at project root:
```
# Secrets
config.ini

# Data (large, regeneratable)
index/olg/scraped_pages/
index/olg/page_chunks.json
index/olg/section_chunks.json
index/olg/scrape_progress.json
index/fns/parsed_sections/
index/fns/chapter_chunks.json
index/fns/section_chunks.json
index/cmr/parsed_sections/
index/chroma_db/

# Source files (large, not ours to redistribute)
raw/

# Python
__pycache__/
*.pyc

# Windows
desktop.ini

# IDE
.vscode/
.idea/
```

**`requirements.txt`** — Union of both:
```
beautifulsoup4>=4.12.0
chromadb>=0.4.0
voyageai>=0.3.0
pdfplumber>=0.11.0
anthropic>=0.50.0
openpyxl>=3.1.0
```

**`config.ini`** — Merge into unified config with source-specific sections:
```ini
[api]
voyage_api_key = <copied from existing>
anthropic_api_key = YOUR_KEY_HERE

[embedding]
model = voyage-3
batch_size = 64
max_tokens_per_batch = 8000
rate_limit_delay = 21

[chromadb]
persist_dir = index/chroma_db
olg_page_collection = pages
olg_section_collection = sections
fns_chapter_collection = fns_chapters
fns_section_collection = fns_sections

[fns]
pdf_path = raw/FNS Handbook 310 1.13.26.pdf
content_start_page = 18
content_end_page = 298
side_by_side_pages = 43,48,49,50,51,55,56,57,59,60,61,79,95,101,102,124,126,128,129,160,161,162,164,212,213,214,217,221,223,224,225,229,230,232,233,235,252,253,254,263,268,269,285,287,288,289,296

[comparator]
model = claude-haiku-4-5-20251001
olg_results_per_section = 3
chapters_to_compare = 7,8,9,10,11
```

### Step 3: Move documentation

| From | To |
|------|-----|
| `new_olg_rag/PROJECT.md` | `docs/olg_pipeline.md` |
| `fns_handbook_rag/PROJECT.md` | `docs/fns_pipeline.md` |
| `new_olg_rag/CMR_BRAINSTORM.md` | `docs/cmr_brainstorm.md` |
| `new_olg_rag/FNS_HANDBOOK_BRAINSTORM.md` | `docs/fns_brainstorm.md` |

### Step 4: Move source files (originals)

| From | To |
|------|-----|
| `new_olg_rag/FNS Handbook 310 1.13.26.pdf` | `raw/FNS Handbook 310 1.13.26.pdf` |
| `fns_handbook_rag/adobe_summary.txt` | `raw/adobe_summary.txt` |

Note: No HAR file currently exists (was in the old parent project). If it reappears, it goes in `raw/`.

### Step 5: Move data files

| From | To |
|------|-----|
| `new_olg_rag/scraped_pages/` | `index/olg/scraped_pages/` |
| `new_olg_rag/page_chunks.json` | `index/olg/page_chunks.json` |
| `new_olg_rag/section_chunks.json` | `index/olg/section_chunks.json` |
| `new_olg_rag/policy_urls.txt` | `index/olg/policy_urls.txt` |
| `new_olg_rag/policy_manifest.json` | `index/olg/policy_manifest.json` |
| `new_olg_rag/policy_toc.json` | `index/olg/policy_toc.json` |
| `new_olg_rag/scrape_progress.json` | `index/olg/scrape_progress.json` |
| `new_olg_rag/scrape_report.txt` | `index/olg/scrape_report.txt` |
| `new_olg_rag/chroma_db/` | `index/chroma_db/` |
| `fns_handbook_rag/parsed_sections/` | `index/fns/parsed_sections/` |

### Step 6: Move and update code files

This is the critical step. Each file moves and gets its path constants updated.

#### Path resolution strategy

Every script currently uses `BASE_DIR = Path(__file__).parent` to find adjacent files. After the move, code lives in `rag/olg/` or `rag/` while data lives in `index/`. The fix: change each script's path constants to resolve the project root and then navigate to the right data directory.

- Scripts in `rag/olg/` and `rag/fns/`: `PROJECT_ROOT = Path(__file__).resolve().parents[2]`
- Scripts in `rag/` (top-level): `PROJECT_ROOT = Path(__file__).resolve().parents[1]`

#### 6a: OLG source code → `rag/olg/`

**Move files:**
| From | To |
|------|-----|
| `new_olg_rag/extractor.py` | `rag/olg/extractor.py` |
| `new_olg_rag/parser.py` | `rag/olg/parser.py` |
| `new_olg_rag/scraper.py` | `rag/olg/scraper.py` |
| `new_olg_rag/chunker.py` | `rag/olg/chunker.py` |

**Update `rag/olg/extractor.py`:**
- Currently uses `cwd`-relative filenames like `HAR_FILENAME = "eohhs.ehs.state.ma.us.har"`
- Change to resolve paths from PROJECT_ROOT:
  - `HAR_FILENAME` → `PROJECT_ROOT / "raw" / "eohhs.ehs.state.ma.us.har"`
  - `FLAT_OUTPUT` → `PROJECT_ROOT / "index" / "olg" / "policy_urls.txt"`
  - `TOC_OUTPUT` → `PROJECT_ROOT / "index" / "olg" / "policy_toc.json"`
  - Manifest output (line ~227) → `PROJECT_ROOT / "index" / "olg" / "policy_manifest.json"`

**Update `rag/olg/parser.py`:**
- Pure parser, no file paths, no I/O. **No changes needed.**

**Update `rag/olg/scraper.py`:**
- `from parser import parse_page` — **still works** (parser.py is in the same directory)
- Update path constants:
  - `BASE_DIR` → `PROJECT_ROOT = Path(__file__).resolve().parents[2]` + `DATA_DIR = PROJECT_ROOT / "index" / "olg"`
  - `MANIFEST_FILE` → `DATA_DIR / "policy_manifest.json"`
  - `OUTPUT_DIR` → `DATA_DIR / "scraped_pages"`
  - `PROGRESS_FILE` → `DATA_DIR / "scrape_progress.json"`
  - `REPORT_FILE` → `DATA_DIR / "scrape_report.txt"`

**Update `rag/olg/chunker.py`:**
- Update path constants:
  - `BASE_DIR` → `PROJECT_ROOT` + `DATA_DIR`
  - `SCRAPED_DIR` → `DATA_DIR / "scraped_pages"`
  - `PAGE_CHUNKS_FILE` → `DATA_DIR / "page_chunks.json"`
  - `SECTION_CHUNKS_FILE` → `DATA_DIR / "section_chunks.json"`

#### 6b: FNS source code → `rag/fns/`

**Move files:**
| From | To |
|------|-----|
| `fns_handbook_rag/fns_parser.py` | `rag/fns/parser.py` (renamed) |

**Update `rag/fns/parser.py`:**
- `PROJECT_ROOT = Path(__file__).resolve().parents[2]`
- `CONFIG_FILE = PROJECT_ROOT / "config.ini"`
- Config section changes: read from `[fns]` section for PDF path, parser settings
- `pdf_path` resolves relative to PROJECT_ROOT (not script dir)
- Default output dir → `PROJECT_ROOT / "index" / "fns" / "parsed_sections"`

#### 6c: Shared RAG code → `rag/`

**Move files:**
| From | To |
|------|-----|
| `new_olg_rag/embedder.py` | `rag/embedder.py` |
| `new_olg_rag/query.py` | `rag/query.py` |

**Update `rag/embedder.py`:**
- `PROJECT_ROOT = Path(__file__).resolve().parents[1]`
- `CONFIG_FILE = PROJECT_ROOT / "config.ini"`
- Chunk file paths: `PROJECT_ROOT / "index" / "olg" / "page_chunks.json"` (etc.)
- ChromaDB persist_dir: read from config, resolve relative to PROJECT_ROOT
- Config key names: `[chromadb]` section with `olg_page_collection`, `olg_section_collection`

**Update `rag/query.py`:**
- `PROJECT_ROOT = Path(__file__).resolve().parents[1]`
- `CONFIG_FILE = PROJECT_ROOT / "config.ini"`
- ChromaDB persist_dir: read from config, resolve relative to PROJECT_ROOT
- Config key names: `[chromadb]` section with `olg_page_collection`, `olg_section_collection`

### Step 7: Update CLAUDE.md

Update all path references, commands section (no more `cd new_olg_rag`), and file locations to reflect the new structure.

### Step 8: Clean up old directories

After verifying everything works:
- Delete `new_olg_rag/` (should be empty except `__pycache__/`)
- Delete `fns_handbook_rag/` (should be empty except `reports/`)
- Delete old sub-project `.gitignore`, `config.ini`, `requirements.txt` files
- Delete `desktop.ini`, `claude.exe` (not project files)
- Delete `__pycache__/` directories

### Step 9: Initialize git

- `git init`
- Stage and commit the organized project

## Files Modified (Summary)

| File | Change Type |
|------|------------|
| `rag/olg/extractor.py` | Path constants updated |
| `rag/olg/scraper.py` | Path constants updated |
| `rag/olg/chunker.py` | Path constants updated |
| `rag/olg/parser.py` | No changes (pure parser) |
| `rag/fns/parser.py` | Path constants + config section names updated |
| `rag/embedder.py` | Path constants + config key names updated |
| `rag/query.py` | Path constants + config key names updated |
| `config.ini` | New unified file (merged from two) |
| `.gitignore` | New unified file (merged from two) |
| `requirements.txt` | New unified file (merged from two) |
| `CLAUDE.md` | Updated paths, commands, file locations |

## What This Plan Does NOT Do

These are future enhancements, not part of the migration:
- Refactor embedder/query to be source-agnostic (currently OLG-specific by paths)
- Extract shared chunking utilities into `rag/chunking_utils.py`
- Build FNS Phase 2/3 (chunker, embedder, query, comparator)
- Build CMR pipeline
- Build agents (orchestrator, synthesizer)
- Build UI
- Make the project a Python package with `__init__.py`

## Verification

After migration, test each pipeline still works:

1. **OLG query** (fastest to verify — just needs ChromaDB):
   ```
   python rag/query.py "income deduction"
   python rag/query.py --list-programs
   ```

2. **OLG chunker** (verify it can read scraped_pages):
   ```
   python rag/olg/chunker.py --stats
   ```

3. **OLG embedder** (dry-run only — don't re-embed):
   ```
   python rag/embedder.py --dry-run
   ```

4. **FNS parser** (dry-run only):
   ```
   python rag/fns/parser.py --dry-run --chapter 10
   ```

All four should produce the same output they did before the migration.
