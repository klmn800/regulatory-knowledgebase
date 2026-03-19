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
│  - Uses existing core/query.py infrastructure       │
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
│  - Uses shared prompts from agents/prompts/         │
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
| LLM integration | Claude Agent SDK | Structured agent with tools, same pattern as comparator |
| Agent prompts | Shared `agents/prompts/` folder | Search agent needs the same DTA policy context as comparator |

## Tech Stack

- **Backend**: FastAPI (Python)
- **Vector store**: ChromaDB (existing, 6 collections)
- **Embeddings**: Voyage AI `voyage-3` (existing)
- **LLM**: Claude via Agent SDK (for synthesis)
- **Frontend**: TBD
- **Retrieval layer**: Wraps existing `core/query.py` Python API

## Architecture Notes

### Retrieval Layer

The search engine's retrieval backend wraps `core/query.py`, which already provides:
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
- Shares prompt templates with comparator (`agents/prompts/`)
- Receives: original query + retrieved passages (with metadata)
- Returns: natural-language answer with inline citations + optional disagreement flags
- Only invoked on analyst request (not on every search)

### Relationship to Comparator

The comparator and search engine are **separate tools** with **shared infrastructure**:
- Both use ChromaDB collections via `core/query.py`
- Both use Claude agents with shared prompts in `agents/prompts/`
- Comparator: systematic pairwise analysis (research tool)
- Search engine: ad-hoc query answering (daily-use tool)

## Open Questions

- [ ] Frontend framework/approach (React? Plain HTML/JS? Something else?)
- [ ] How should multi-source results be organized? (Tabbed by source? Interleaved by relevance? Side-by-side?)
- [ ] Should search history be persisted? (Useful for analysts revisiting prior research)
- [ ] How many results to show by default? (Current CLI default is 5)
- [ ] Should the synthesis agent have access to search tools (iterative retrieval), or just receive a fixed set of passages?
- [ ] Authentication/access control needed? Or internal-only tool?
- [ ] Should there be a "saved searches" or "bookmarks" feature?
- [ ] How to handle queries that match nothing? (Suggest reformulations? Broaden to other sources?)

## File Structure (Planned)

```
policy_navigator/
├── api/                          ← FastAPI backend (new)
│   ├── main.py                   ← App entry point, CORS, lifespan
│   ├── routes/
│   │   ├── search.py             ← Search endpoints
│   │   └── synthesize.py         ← Synthesis endpoint (calls agent)
│   └── models/
│       ├── requests.py           ← Pydantic request models
│       └── responses.py          ← Pydantic response models
│
├── agents/
│   ├── comparator.py             ← Existing
│   ├── search_agent.py           ← New: synthesis agent for search
│   └── prompts/                  ← Shared prompt templates
│
├── ui/                           ← Frontend (TBD)
│
├── core/
│   ├── embedder.py               ← Existing
│   └── query.py                  ← Existing (search engine wraps this)
```

## Changelog

- **2026-03-18**: Initial design decisions captured. Core flow, tech stack, and user model established.
