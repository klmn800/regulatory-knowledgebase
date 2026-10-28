# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Regulatory Knowledgebase** is a multi-source RAG (Retrieval-Augmented Generation) system for U.S. public-assistance (SNAP) policy. It indexes four authoritative policy sources in priority order:

1. **OLG** (Online Guide) — the agency's internal staff guide; ~1,200 HTML pages covering SNAP, TAFDC, EAEDC, and cross-program policy. This is what workers follow day-to-day.
2. **CMR** (Code of Massachusetts Regulations, Title 106) — The state regulations the OLG implements. 18 PDFs, ~360 pages of formal legal language.
3. **FNS Handbook 310** — The federal SNAP Quality Control standard the CMR is supposed to implement. Single PDF, 306 pages, 483 numbered sections.
4. **7 CFR** (federal SNAP regulations) — Parts 271-275, 280, 292. The federal codification that 106 CMR implements. 7 PDFs, 517 pages, 118 sections.

**Use cases**: Staff/agents ask policy questions and get answers using sources in OLG → CMR → FNS / CFR order. The system also compares sources to find gaps, and authors new OLG content from research.

**When sources disagree, the disagreement IS the finding.**

## Current State

| Source | Parse | Chunk | Embed | Query | Comparator |
|--------|-------|-------|-------|-------|------------|
| OLG | COMPLETE (1,164 pages) | COMPLETE (1,164 + 6,511) | COMPLETE | COMPLETE | N/A |
| FNS | COMPLETE (482 sections) | COMPLETE (14 + 860) | COMPLETE | COMPLETE | ALL 5 CHAPTERS COMPLETE (270 sections) |
| CMR | COMPLETE (592 sections) | COMPLETE (18 + 1,415) | COMPLETE | COMPLETE | Used in L3 cross-check |
| CFR | COMPLETE (118 sections) | COMPLETE (7 + 1,623) | COMPLETE | COMPLETE | Used in L3 cross-check (alongside CMR) |

| Component | Status |
|-----------|--------|
| Search engine (web UI) | COMPLETE — Ask + History tabs, standard + deep synthesis |
| Comparator | COMPLETE — All 5 FNS chapters (7-11), 270 sections analyzed; CFR L3 cross-check added |
| OLG authoring pipeline | COMPLETE — Research + Draft + Format, CLI + web UI |
| QC analyzer | COMPLETE — extractor + judge + CMR/FNS/CFR cross-checks |
| HTML report | COMPLETE — Filterable comparator findings viewer (CMR + CFR detail blocks) |

**All four sources are fully indexed and searchable.** All major tools are built and operational.

## Architecture

Each source follows the same pipeline pattern: **Parse → Chunk → Embed → Query**

### Shared Infrastructure
- **Embedding models**: Voyage AI. Production runs `voyage-4-large` (broad tier: pages/chapters/parts) + `voyage-context-3` mode A (section tier, with chunker context prefix retained). All collections re-embedded 2026-05-04 — no `voyage-3` vectors remain. `config.ini [embedding] model = voyage-context-3` governs query embedding. See `docs/retrieval_quality_plan.md` for the journey.
- **Vector store**: ChromaDB (persistent, embedded mode — no server). All sources share a single instance at `index/chroma_db/`.
- **LLM**: Claude via Anthropic API (synthesis, comparator L0/L1/L3) and Claude Code CLI (comparator L2, authoring drafts).
- **Multi-source CLI**: Both `rag/embedder.py` and `rag/query.py` accept `--source olg|fns|cmr|cfr` to target any source.

### OLG Pipeline (`rag/olg/`)

Fully complete. Source is a MadCap Flare WebHelp site scraped via HTTP.

| Module | Role |
|--------|------|
| `rag/olg/extractor.py` | HAR file → `policy_urls.txt` + `policy_manifest.json` + `policy_toc.json` |
| `rag/olg/parser.py` | Pure HTML parser (no I/O). Called by scraper. Extracts sections at H2/H3 boundaries, tables, internal links, last-updated dates. |
| `rag/olg/scraper.py` | Orchestrates fetching, calls parser, saves one JSON per page to `index/olg/scraped_pages/`. Resumable with progress tracking. |
| `rag/olg/chunker.py` | Two-tier output: page-level docs (1,164) + section-level chunks (6,511). Smart merge (<200 chars) and split (>1,500 chars). Tables inlined at `[Table]` placeholders. Context prefix prepended. |

**ChromaDB collections**: `pages` (1,164 docs, voyage-4-large), `sections` (6,511 chunks, voyage-context-3)

**Key data flow**: The chunker prepends a context prefix like `"SNAP > Application Processing > Expedited Benefits > Step One"` to every chunk before embedding, so the embedding captures hierarchical context.

### FNS Pipeline (`rag/fns/`)

Fully complete (parse, chunk, embed, query).

| Module | Role |
|--------|------|
| `rag/fns/parser.py` | PDF → structured JSON sections via pdfplumber. Handles side-by-side example boxes (47 pages) with column-aware extraction, cross-reference extraction, section hierarchy. |
| `rag/fns/chunker.py` | Two-tier output: chapter-level docs (14) + section-level chunks (860). Same merge/split logic. Context prefix: `"FNS 310 > Chapter 10: Income > 1021.1 Positive Allegation"`. |

**ChromaDB collections**: `fns_chapters` (14 docs, voyage-4-large), `fns_sections` (860 chunks, voyage-context-3)

**Parsed output**: 482 JSON files in `index/fns/parsed_sections/`, one per handbook section.

### CMR Pipeline (`rag/cmr/`)

Fully complete (parse, chunk, embed, query).

| Module | Role |
|--------|------|
| `rag/cmr/parser.py` | 18 CMR PDFs → structured JSON sections via pdfplumber. Chapter-filtered section detection, TOC boundary detection, continuation page merging, character-level dedup for one doubled-font PDF (704), cross-reference and table extraction. |
| `rag/cmr/chunker.py` | Two-tier output: chapter-level docs (18) + section-level chunks (1,415). Same merge/split logic. Context prefix: `"106 CMR 362 > SNAP Nonfinancial Eligibility > 362.330 Good Cause Criteria"`. |

**ChromaDB collections**: `cmr_chapters` (18 docs, voyage-4-large), `cmr_sections` (1,415 chunks, voyage-context-3)

**Parsed output**: 592 JSON files in `index/cmr/parsed_sections/`, one per regulation section.

### CFR Pipeline (`rag/cfr/`)

Fully complete (parse, chunk, embed, query). Used in comparator L3 cross-check and QC analyzer cross-check.

| Module | Role |
|--------|------|
| `rag/cfr/parser.py` | 7 CFR PDFs → structured JSON sections via pdfplumber. 3-line header + 1-line footer stripping per page, TOC boundary via duplicate detection, subpart extraction from raw TOC, amendment-note stripping (`[Amdt. ...]`, `[NN FR ...]`), `[Reserved]` filtering. |
| `rag/cfr/chunker.py` | Two-tier output: part-level docs (7) + section-level chunks (1,623). Hierarchy profile `(a)(1)(i)(A)`. Three section JSON variants (top-marker / fullpath / context-with-ancestor-intros). Top-level marker break is unconditional. Hierarchy-boundary splitting reduced mid-sentence breaks from 332 to 4. Dedicated definition chunker for 271.2 / 292.2. Section-level program labels (SNAP / Issuance / Administration / QC / Disaster / Summer-EBT). |

**ChromaDB collections**: `cfr_parts` (7 docs, voyage-4-large), `cfr_sections` (1,623 chunks, voyage-context-3)

**Parsed output**: 118 JSON files in `index/cfr/parsed_sections/`, one per regulation section. **Embedded variant**: `index/cfr/section_chunks_context.json` (chosen for parent-context preamble).

**Manual cleanup**: 16 garbled multi-column tables in 273.18, 275.3, and 275.11 were rewritten as flowing prose directly in the parsed JSONs. See [`docs/cfr_pipeline.md`](docs/cfr_pipeline.md) for the recovery procedure if those JSONs are ever regenerated.

### Shared RAG Modules (`rag/`)

| Module | Role |
|--------|------|
| `rag/embedder.py` | Batch embedding via Voyage AI → ChromaDB. `--source olg\|fns\|cmr\|cfr` flag routes to correct chunk files and collections. Token-aware batching, resume support, cost estimation, `--dry-run`, `--force`, `--only`. |
| `rag/query.py` | Three interfaces: CLI, Python API (`search()` / `create_client(source)` + `search_with_client()`), JSON output. `--source olg\|fns\|cmr\|cfr` flag. Program filtering (OLG/CMR), `--exclude-programs` filter, similarity scoring, parent context fetching, source-specific display formatting. |

### Tools (`tools/`)

| Module | Role |
|--------|------|
| `tools/synthesis.py` | RAG synthesis (standard + deep). `prompt_name` and `config_overrides` support. Used by search engine and authoring research phase. |
| `tools/claude_code_runner.py` | Generic subprocess wrapper for Claude Code CLI. Piped mode (headless, captures session IDs) or windowed mode (visible terminal). Used by comparator L2 and authoring pipeline. Supports `parse_json=False` for non-JSON outputs. |
| `tools/docx_writer.py` | Markdown → styled .docx using OLG template. Handles headings 1-4, numbered/bullet lists (via XML numPr), tables, Note/Important callouts, inline bold/italic. Strips Author's Notes before generating. |

### Search Engine (`ui/` + `tools/synthesis.py`)

FastAPI + HTMX web interface at `http://127.0.0.1:8001`. Run with `python ui/app.py`.

| Tab | What it does |
|-----|-------------|
| **Ask** | Type a question, get a synthesized answer with citations from OLG/CMR/FNS. Standard or deep (agentic) mode. |
| **Author** | Enter an assignment, click buttons to run Research/Draft/Format phases. Draft spawns a visible Claude Code terminal. Each run is versioned with navigable history. |
| **History** | Browse past searches with full evidence snapshots. |

Key files: `ui/app.py` (FastAPI routes), `ui/search.py` (source registry), `ui/history.py` (SQLite persistence), `ui/versioning.py` (author output versioning), `tools/synthesis.py` (RAG synthesis with `prompt_name` and `config_overrides` support).

### Comparator (`apps/comparator/comparator.py`)

Purpose-built research agent comparing FNS requirements against OLG coverage. Four-layer pipeline:

| Layer | Purpose | Engine |
|-------|---------|--------|
| L0 | Pre-classify FNS sections (compare vs skip) | Haiku API |
| L1 | Triage: RAG search + quick classification | Haiku API |
| L2 | Deep investigation: agentic search, 3-7 queries | Claude Code CLI (subscription) |
| L3 | CMR cross-check for confirmed gaps | Haiku API |

All 5 FNS policy chapters complete: Ch7 (68), Ch8 (50), Ch9 (28), Ch10 (62), Ch11 (62) = 270 sections. Results in `output/comparator/results/` with per-chapter CSVs. `--parallel 5` cuts runtime ~3x. See [docs/comparator.md](docs/comparator.md).

### OLG Authoring Pipeline (`apps/author/author.py`)

Three-phase pipeline: **Research → Author → Format**

| Phase | Engine | Cost | Output |
|-------|--------|------|--------|
| Research | Anthropic API (`run_synthesis()` with `author_research` prompt, deep mode) | ~$0.05-0.40 | `research_report.md`, `research_evidence.json` |
| Author | Claude Code CLI (visible terminal, session resumable) | $0 (subscription) | `draft.md`, `session_id.txt` |
| Format | python-docx (deterministic, no LLM) | $0 | `output.docx` |

CLI: `python apps/author/author.py "assignment" --name name`. Flags: `--research-only`, `--draft-only`, `--resume`, `--no-docx`, `--assignment-file`.

Web UI: Author tab with buttons for each phase. Draft spawns a Claude Code terminal window for live observation. Clicking a phase button shows existing output with version navigation (left/right arrows) and a "Run Again" button; draft views include a Resume button wired to the version-specific session ID.

Output versioning (`ui/versioning.py`): Each UI-triggered run creates a numbered version directory (e.g., `research/001_20260406-1430/`) with the output files, assignment text used (`input.txt`), and metadata. Top-level files always hold the latest version for phase-to-phase handoff. CLI runs are not versioned.

Output directory: `output/author/{name}/`

Key supporting files:
- `prompts/author_research.md` — Structured research output prompt
- `apps/author/prompts/author_draft.md` — OLG-voice drafting instructions
- `apps/author/references/olg_style_guide.md` — Evidence-based style guide (committed)
- `apps/author/references/2026 OLG Template.docx` — Word template with OLG styles (gitignored)

Both prompts include a self-improvement directive: agents suggest changes to style guide, tools, and references in Author's Notes.

### QC Analyzer (`apps/qc/qc_analyzer.py`)

Reads a QC reviewer's CSV of error findings, extracts the abstract policy issues, evaluates whether the OLG covers each one, and cross-checks CMR / FNS / 7 CFR for gaps. Phased pipeline driven by the QC tab in the web UI.

| Phase | Engine | Role |
|-------|--------|------|
| Extract | Haiku API | Per CSV row, extract a list of distinct policy issues + 2-3 OLG search queries each. Multi-finding by default — a single QC narrative often spans unrelated topics (e.g., income coding + household composition + shelter deduction) and each becomes its own finding. |
| Investigate | Sonnet API (agentic loop with `search_olg` tool) | Per finding: seed search + iterative judge that classifies OLG coverage as Adequate / Partial / Gap. `judge_trace` (per-turn reasoning + tool calls) is folded into the finding JSON. |
| Cross-check (CMR / FNS / CFR) | Haiku API, single-turn | For Partial/Gap findings only: search the chosen source and classify whether it covers the same topic, is silent, or differs. |

**Storage**: per-row JSONs at `output/qc_analysis/{name}_{YYYY-MM-DD_HHMM}/results/row_NNN.json`. Each row has case identity at the top level (review #, APID, narrative) and a nested `findings: [...]` array — judge results, cross-check results, and `judge_trace` nest inside each finding. `flatten_findings()` produces one entry per (row, finding) for UI display ("5.1", "5.2", "5.3" rendering). Legacy single-finding rows auto-migrate on read via `_migrate_legacy_row()`.

**Per-source program filters**: `[qc_analyzer]` config has `{olg|cmr|fns|cfr}_include` / `_exclude` lists. The include list is the active whitelist; the exclude list is informational so a reader sees all known programs without grepping ChromaDB metadata. Filter scope is surfaced in the QC tab via a collapsible read-only panel (decision: filtering is allowed, silent filtering is not).

**Re-extract safety**: re-running extract on an analysis with downstream phases populated (judge / cross-checks) returns an in-page modal listing what would be wiped, with three options: Fork to new analysis (copies `upload.csv` to a new timestamped dir, preserves the original), Re-extract here (destructive, wipes downstream phase flags), or Cancel.

### HTML Report (`apps/comparator/report.py`)

Single-page HTML from comparator CSVs. Dark mode, favorites, expandable details, filter by chapter/classification/findings. Session ID click copies `claude --resume <UUID>`. Run: `python apps/comparator/report.py --open`.

## Commands

All commands run from the project root (`policy_navigator/`).

### Web UI
```bash
python ui/app.py              # Starts at http://127.0.0.1:8001
```

### Querying (all sources)
```bash
# OLG (default)
python rag/query.py "income deduction"
python rag/query.py "expedited SNAP" --program SNAP
python rag/query.py "benefit calculation" --top 10 --full
python rag/query.py "eligibility rules" --collection pages
python rag/query.py "income limits" --context
python rag/query.py "work requirements" --json
python rag/query.py "income limits" --exclude-programs "TAFDC,EAEDC"
python rag/query.py --list-programs

# FNS
python rag/query.py "income deduction" --source fns
python rag/query.py "income" --source fns --collection chapters

# CMR
python rag/query.py "income deduction" --source cmr
python rag/query.py "work requirements" --source cmr --program SNAP

# CFR
python rag/query.py "income deduction" --source cfr
python rag/query.py "summer EBT eligibility" --source cfr --collection parts
python rag/query.py "income" --source cfr --exclude-programs "Administration,QC"
```

### Authoring
```bash
python apps/author/author.py "Consolidate all VC-1 scripts" --name vc1_scripts
python apps/author/author.py "Find VC-1 scripts" --name vc1_scripts --research-only
python apps/author/author.py --name vc1_scripts --draft-only
python apps/author/author.py --name vc1_scripts --resume
python apps/author/author.py --name vc1_scripts --no-docx
python apps/author/author.py --assignment-file assignment.txt --name my_assignment
```

### Comparator
```bash
python apps/comparator/comparator.py --chapter 10 --engine claude-code --parallel 5
python apps/comparator/comparator.py --compile --chapter 10
python apps/comparator/report.py --open
```

### Embedding
```bash
python rag/embedder.py --source olg --dry-run       # Cost estimate
python rag/embedder.py --source fns                  # Embed FNS
python rag/embedder.py --source cmr --force          # Re-embed from scratch
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

Single unified `config.ini` at project root (gitignored). Key sections:

| Section | What it configures |
|---------|--------------------|
| `[api]` | Voyage AI and Anthropic API keys |
| `[embedding]` | Model (currently `voyage-3` for production parity; will flip to `voyage-4-large` on swap), batch size, rate limits |
| `[chromadb]` | Persist directory, 6 collection names |
| `[synthesis]` | Search engine model, token limits, search budget |
| `[author]` | Research model, template .docx path, style guide path, Claude Code timeout |
| `[comparator]` | Layer models, thresholds, FNS chapters to compare |
| `[qc_analyzer]` | Extractor/judge models, search budgets |

**Embedding note**: Document embeddings were created WITHOUT `input_type="document"`, so queries must NOT use `input_type="query"` — asymmetry would degrade results.

## Project Structure

```
policy_navigator/
├── CLAUDE.md
├── README.md
├── .gitignore
├── requirements.txt
├── config.ini                       ← unified config (gitignored)
│
├── rag/                             ← embedder, query + per-source pipelines
│   ├── embedder.py
│   ├── query.py
│   ├── olg/                         ← extractor, parser, scraper, chunker
│   ├── fns/                         ← parser, chunker
│   └── cmr/                         ← parser, chunker
│
├── index/                           ← vector store + parsed/chunked data
│   ├── chroma_db/
│   ├── olg/
│   ├── fns/
│   └── cmr/
│
├── raw/                             ← source PDFs, HAR files (gitignored)
│
├── tools/                           ← shared capabilities used by apps
│   ├── synthesis.py
│   ├── claude_code_runner.py
│   └── docx_writer.py
│
├── prompts/                         ← shared prompts (domain_preamble, synthesis, author_research)
│
├── apps/
│   ├── comparator/                  ← comparator.py, report.py, prompts/
│   ├── author/                      ← author.py, prompts/, references/
│   ├── qc/                          ← qc_analyzer.py, prompts/, inputs/
│   └── search/                      ← prompts/ (thin — logic lives in ui/ + tools/)
│
├── output/                          ← all deliverables
│   ├── comparator/
│   ├── author/
│   ├── qc_analysis/
│   └── search_history.db
│
├── ui/                              ← FastAPI app (unchanged location)
│   ├── app.py                       ← FastAPI application
│   ├── search.py                    ← search service layer + source registry
│   ├── history.py                   ← SQLite search history
│   ├── versioning.py                ← author output versioning
│   ├── static/                      ← CSS + JS
│   └── templates/                   ← Jinja2 + HTMX partials
│
└── docs/                            ← architecture docs, pipeline docs
```

## Conventions

- **One JSON file per parsed unit**: OLG produces one JSON per page, FNS one per section, CMR one per section. Easy to inspect, debug, and reprocess individually.
- **Flat section lists with level numbers** instead of nested trees — simpler for chunkers to iterate while preserving hierarchy.
- **Context prefixes** prepended to chunk text before embedding so embeddings capture hierarchical position.
- **Stable, readable chunk IDs**: e.g., `sec__SNAP__AppProcessing__...` (OLG), `fns_sec_1021_1__000` (FNS), `cmr_sec_362_330__000` (CMR).
- **Two-tier chunking**: Broad documents (page/chapter level) for topic discovery + granular chunks (section level) for specific answers.
- **Python API pattern**: `search()` for one-off convenience, `create_client(source)` + `search_with_client()` for agent loops that need to avoid re-initialization.
- **Source-agnostic RAG modules**: `embedder.py` and `query.py` use `_resolve_source_paths()` / `_resolve_source_config()` — adding a new source requires one dict per resolver function.
- All modules use `configparser` for settings, `argparse` for CLI, and `pathlib` for paths.
- **Path resolution**: Scripts in `rag/*/` use `PROJECT_ROOT = Path(__file__).resolve().parents[2]`. Scripts in `rag/`, `tools/`, and `ui/` use `PROJECT_ROOT = Path(__file__).resolve().parents[1]`. Scripts in `apps/*/` use `PROJECT_ROOT = Path(__file__).resolve().parents[2]`.
- **Engine split for LLM work**: API for structured/cheap tasks (synthesis, triage). Claude Code CLI for expensive/resumable work (comparator L2, authoring drafts). python-docx for deterministic formatting.

## Key Design Decisions

1. **ChromaDB over alternatives**: Metadata filtering is essential (filter by program, date, section type). Three consumer types need different query patterns. Embedded mode means no server to manage.
2. **Voyage AI for embeddings**: Anthropic's recommended embedding provider for use with Claude. Strong retrieval quality for domain-specific text.
3. **JSON per-page/section output**: Chosen over SQLite for inspectability and debuggability during development. May migrate later.
4. **FNS section detection via regex**: The PDF has no bookmarks or tagged structure. Numbered section patterns (`100 GENERAL.`) at line start are validated against known chapter ranges to distinguish from inline references.
5. **CMR section detection filtered by chapter prefix**: Each PDF is one chapter. Only `XXX.XXX:` patterns matching the chapter prefix are treated as section headings — avoids false positives from cross-references that happen to start at the beginning of a line.
6. **CMR chunk strategy**: Chunk at CMR section level (e.g., `362.330`), NOT at sub-items. Deep nested `(A)(1)(a)(b)(c)` structure preserved within each chunk. Continuation pages merged before chunking.
7. **Comparator is source-pair-agnostic**: Designed to compare any two sources (OLG vs CMR, CMR vs FNS, OLG vs FNS), not hardcoded to one pair.
8. **Authoring engine split**: Research via API (structured SynthesisResult, cheap, integrated with existing RAG). Drafting via Claude Code CLI (free on subscription, session resumable via UUID, can do additional searches). Formatting via python-docx (deterministic, uses real OLG template styles).
9. **Web UI uses HTMX**: Server-rendered HTML partials, no heavy JS framework. FastAPI backend runs synthesis in thread pool to avoid blocking. Author draft phase spawns a visible Claude Code terminal instead of running headless.
10. **Directory structure follows dependency flow**: `apps/ → tools/ → rag/ → index/`. Apps are top-level workflows, tools are shared capabilities, rag is the retrieval layer, index is stored data. Prompts shared across apps live in `prompts/`; app-specific prompts live in `apps/*/prompts/`. (The term **app** refers to the four user-facing applications — comparator, author, qc, search. The word "program" is reserved for chunk metadata — SNAP, EAEDC, Hearings, etc.)

## Important File Locations

- **OLG scraped data**: `index/olg/scraped_pages/*.json` (~1,202 files)
- **FNS parsed data**: `index/fns/parsed_sections/*.json` (~482 files)
- **CMR parsed data**: `index/cmr/parsed_sections/*.json` (~592 files)
- **CFR parsed data**: `index/cfr/parsed_sections/*.json` (118 files)
- **CFR chunk variant chosen for embedding**: `index/cfr/section_chunks_context.json`
- **Shared vector store**: `index/chroma_db/` (8 collections)
- **Comparator results**: `output/comparator/results/` (per-section JSONs), `output/comparator/FNS-{ch}.csv`
- **Author outputs**: `output/author/{name}/` (top-level latest + `research/`, `drafts/`, `formats/` version dirs)
- **QC analysis outputs**: `output/qc_analysis/`
- **Search history**: `output/search_history.db`
- **FNS source PDF**: `raw/FNS Handbook 310 1.13.26.pdf`
- **CMR source PDFs**: `raw/cmr/*.pdf` (18 files)
- **CFR source PDFs**: `raw/cfr/*.pdf` (7 files)
- **Shared prompts**: `prompts/domain_preamble.md`, `prompts/synthesis.md`, `prompts/author_research.md`
- **Comparator prompts**: `apps/comparator/prompts/`
- **Author prompts**: `apps/author/prompts/author_draft.md`
- **QC prompts**: `apps/qc/prompts/`
- **Author references**: `apps/author/references/` (style guide, templates, sample pages)
- **Pipeline documentation**: `docs/olg_pipeline.md`, `docs/fns_pipeline.md`, `docs/cmr_pipeline.md`, `docs/cfr_pipeline.md`, `docs/comparator.md`

### User Preferences
- **Incremental Development**: One component at a time
- **Quality Over Speed**: Robust, well-tested components
- **Anti-Feature Creep**: Focused requests without assumptions
- **Windows Environment**: All code must work on Windows PC
- **Enhancement Protocol**: Always offer suggestions to take requests to the next level, but NEVER implement enhancements without explicit approval. Stick to the exact scope requested until user approves additional changes. However, you may push back on instructions if they would be harmful, cumbersome, follow worst practices, or be overly complicated.
- **NO COP-OUT ANSWERS**: NEVER give up on solving technical problems or provide "that's good enough" responses when something clearly isn't working. Always debug thoroughly and find the actual root cause. If an UPDATE statement isn't working, investigate why instead of suggesting workarounds.
- **NO QUICK FIXES**: When a bug reveals a design flaw, fix the design — don't patch over it with workarounds. If a mechanism is fundamentally fragile (e.g., relying on a race condition), redesign it so the failure mode doesn't exist, rather than adding fallbacks to catch failures after the fact.
- **FOLLOW INSTRUCTIONS EXACTLY**: When user gives specific values or instructions (e.g., "set all to 300"), implement EXACTLY what was requested. Do not improvise variations (300/350/400) or interpret creatively. If the instruction is unclear, ask for clarification. Do not second-guess explicit directives.
- **Git Workflow**: Offer to commit after completing each meaningful unit of work (pipeline stage, bug fix, refactor, etc.). Offer to push to GitHub periodically so the remote backup stays current. User controls timing — always ask, never auto-commit or auto-push. Repo: `klmn800/policy-navigator` (private).
