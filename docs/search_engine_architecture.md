# Policy Search Engine — Architecture & Design

*Living document. Updated as decisions are made across sessions.*

## Purpose

A policy search tool for DTA policy analysts. Accepts natural-language queries, retrieves relevant passages from indexed policy sources, and optionally synthesizes answers using Claude. This is the system's primary daily-use interface — distinct from the comparator, which is a purpose-built research tool for cross-source analysis.

## Users

**Primary audience: Policy analysts.** People who already know the OLG, CMR, and FNS source material well. They're looking for specific references, verifying policy, and cross-checking across sources. The UI should respect their expertise — precise results, not oversimplified summaries.

## Core Search Flow

```
┌─────────────────────────────────────────────────────┐
│  Analyst enters query                               │
│  - Selects sources: [x] OLG  [ ] CMR  [ ] FNS      │
│  - Filters by program: SNAP / TAFDC / EAEDC / All   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI Backend                                    │
│  - Routes query to selected ChromaDB collections    │
│  - Uses existing rag/query.py infrastructure         │
│  - Returns ranked passages organized by source      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Results View (default)                             │
│  - Raw passages, ranked by relevance                │
│  - Grouped/labeled by source (OLG, CMR, FNS)       │
│  - Chunk metadata visible (section path, program)   │
│                                                     │
│  [ Synthesize ]  ← on-demand button                 │
└──────────────────┬──────────────────────────────────┘
                   │ (only if analyst clicks)
                   ▼
┌─────────────────────────────────────────────────────┐
│  Claude Agent (Agent SDK)                           │
│  - Receives query + retrieved passages              │
│  - Produces natural-language answer with citations   │
│  - Flags cross-source disagreements when present    │
│  - Uses shared prompts from prompts/                │
└─────────────────────────────────────────────────────┘
```

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Default source | OLG only | OLG is what staff follow day-to-day; most searches start there |
| Source selection | Analyst chooses via checkboxes | Analysts know which sources matter for their question |
| Result format | Raw passages (default) | Analysts want to see the actual text, not a rewrite |
| Synthesis | On-demand via button | Keeps search fast; synthesis is expensive and not always needed |
| Disagreements | Surfaced in synthesis only | Raw search shouldn't editorialize; synthesis can note conflicts |
| Program filtering | Essential, core UI element | Analysts typically work within one program at a time |
| Backend framework | FastAPI | Async (good for API calls), auto-docs, Pydantic models, Python-native |
| Frontend | HTMX + server-rendered HTML | One Python codebase, no Node toolchain. Form→results pattern is ideal for HTMX. |
| Result layout | Tabbed by source | Clean separation per source. OLG tab pre-selected. Other tabs load on click (lazy). |
| LLM integration | Claude Agent SDK | Structured agent with tools, same pattern as comparator |
| Agent prompts | Shared `prompts/` folder | Search agent needs the same DTA policy context as comparator |
| Search history | Server-side persistence | Analysts can revisit prior searches. Stored in backend database. |
| Results per tab | 5 (with "show more") | Concise default, matches CLI. Analyst can load more on demand. |
| Agent retrieval | Iterative, on analyst toggle | Agent works with fixed passages by default. "Dig deeper" toggle lets it search for more. |
| Authentication | None | Internal tool on trusted network. No login required. |
| Export | Results exportable (clipboard, CSV) | More useful than bookmarks for analyst workflow. |
| No-results handling | Suggest other sources | "No OLG results — try CMR or FNS?" with one-click buttons to broaden search. |

## Tech Stack

- **Backend**: FastAPI (Python)
- **Vector store**: ChromaDB (existing, 6 collections)
- **Embeddings**: Voyage AI `voyage-3` (existing)
- **LLM**: Claude via Agent SDK (for synthesis)
- **Frontend**: HTMX + server-rendered HTML (FastAPI templates)
- **Retrieval layer**: Wraps existing `rag/query.py` Python API

## Architecture Notes

### Retrieval Layer

The search engine's retrieval backend wraps `rag/query.py`, which already provides:
- Multi-source support (`--source olg|fns|cmr`)
- Program filtering (`--program SNAP`)
- Two-tier collections (page/chapter level + section level)
- Python API: `create_client(source)` + `search_with_client()` for reusable clients
- JSON output mode

The FastAPI layer adds:
- HTTP API endpoints
- Concurrent multi-source queries (when analyst selects multiple sources)
- Response formatting for the frontend

### Synthesis Agent

- Uses Claude Agent SDK
- Shares prompt templates with comparator (`prompts/`)
- **Default mode**: Receives original query + retrieved passages (with metadata). Produces natural-language answer with inline citations. Flags cross-source disagreements when present.
- **Deep mode** (analyst toggle): Agent gains access to search tools and can pull additional chunks if the initial results are insufficient. Only activated when analyst explicitly requests it.
- Only invoked on analyst request (not on every search)

### Extensibility — New Sources

New policy sources may be added in the future. The search engine must scale without architectural changes:

- **Backend**: `rag/query.py` already uses `_resolve_source_paths()` / `_resolve_source_config()` — adding a source is one dict entry per resolver. The FastAPI layer should discover available sources from these resolvers, not hardcode OLG/CMR/FNS.
- **UI**: Source checkboxes and tabs should be dynamically generated from the list of available sources, not hardcoded.
- **Synthesis agent**: Prompt templates should be source-agnostic where possible. Source-specific context (like "CMR uses formal legal language") can be injected via metadata.
- **Search history**: Source list stored per search record so historical searches remain valid even if sources are added/removed.

### Relationship to Comparator

The comparator and search engine are **separate tools** with **shared infrastructure**:
- Both use ChromaDB collections via `rag/query.py`
- Both use Claude agents with shared prompts in `prompts/`
- Comparator: systematic pairwise analysis (research tool)
- Search engine: ad-hoc query answering (daily-use tool)

## Open Questions

All initial design questions resolved (2026-03-23). New questions as they arise:

- [ ] Search history storage — SQLite? Or reuse ChromaDB? Need to decide on persistence layer.
- [ ] Export formats — CSV is clear. What does "copy to clipboard" look like for multi-result output?
- [ ] HTMX template structure — how to organize Jinja2 templates (base layout, partials for tabs, result cards)
- [ ] Deployment — how will analysts access this? Local machine? Shared server?

## File Structure (Planned)

```
policy_navigator/
├── ui/                           ← FastAPI backend + HTMX templates + static assets
│   ├── app.py                    ← App entry point, routes
│   ├── search.py                 ← Search service layer + source registry
│   ├── history.py                ← SQLite search history
│   ├── templates/                ← Jinja2 templates
│   └── static/                   ← CSS, minimal JS
│
├── apps/
│   └── comparator/
│       └── comparator.py         ← Existing comparator
│
├── tools/
│   └── synthesis.py              ← RAG synthesis (standard + deep)
│
├── prompts/                      ← Shared prompt templates
│
├── rag/
│   ├── embedder.py               ← Existing
│   └── query.py                  ← Existing (search engine wraps this)
```

## Changelog

- **2026-03-18**: Initial design decisions captured. Core flow, tech stack, and user model established.
- **2026-03-23**: All open design questions resolved. Added: HTMX frontend, tabbed layout, search history, export, synthesis agent deep mode, no-results handling.
