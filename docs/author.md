# OLG Authoring Pipeline — Developer Guide

The authoring pipeline creates new OLG (Online Guide) content through three independent phases: **Research**, **Draft**, and **Format**. Each phase versions its outputs independently, and phases can be run in any order, any number of times.

## Architecture

```
User (Web UI or CLI)
  │
  ├── Research ──→ Anthropic API (synthesis engine)
  │                  ├── Searches OLG, CMR, FNS via ChromaDB
  │                  └── Returns structured report + evidence
  │
  ├── Draft ────→ Claude Code CLI (terminal window)
  │                  ├── Reads research reports + style guide + assignment
  │                  ├── Can do additional searches via rag/query.py
  │                  └── Writes draft.md to versioned directory
  │
  └── Format ───→ python-docx (deterministic)
                     ├── Reads draft.md from a specific draft version
                     └── Generates output.docx using OLG template
```

**Engine split rationale:**
- Research uses the **API** — structured output, cheap, integrated with the existing RAG synthesis engine.
- Draft uses **Claude Code CLI** — free on subscription, session resumable via UUID, can do additional searches, runs in a visible terminal so the user can watch and intervene.
- Format uses **python-docx** — deterministic, no LLM needed, uses real OLG template styles.

## Directory Structure

Each assignment lives at `output/author/{name}/`:

```
output/author/{name}/
├── assignment.txt                    ← the stable project description
├── research/
│   ├── 001_20260408-2130/
│   │   ├── prompt.md                 ← task instructions for this run (may be empty)
│   │   ├── report.md                 ← research output
│   │   ├── evidence.json             ← structured evidence with search results
│   │   └── meta.json                 ← timestamp, duration, cost, model, search count
│   └── 002_20260409-1015/
│       └── ...
├── drafts/
│   ├── 001_20260409-1100/
│   │   ├── prompt.md                 ← draft instructions (the editable part)
│   │   ├── draft.md                  ← the authored content (written by Claude Code)
│   │   ├── session_id.txt            ← Claude Code session UUID for resume
│   │   ├── full_prompt.md            ← complete assembled prompt (instructions + research + style guide)
│   │   └── meta.json                 ← timestamp, based_on: ["research/001", "research/002"]
│   └── ...
└── formats/
    ├── 001_20260409-1130/
    │   ├── output.docx
    │   └── meta.json                 ← timestamp, based_on: "drafts/001"
    └── ...
```

**Key design decisions:**
- Phases version independently. You might run research 3 times before drafting once.
- Explicit linkage: each draft records which research versions it used; each format records which draft.
- The version directory is the source of truth. No top-level convenience copies.
- Resume updates in place — resuming a Claude Code session writes back to the same draft version directory.

## File Inventory

### Core files

| File | Role |
|------|------|
| `ui/versioning.py` | Version directory primitives — create, list, load versions per phase |
| `apps/author/author.py` | Phase execution logic — `run_research()`, `compose_draft_prompt()`, `launch_draft()`, `run_format()` |
| `ui/app.py` (author section) | FastAPI endpoints — REST-style routes for all three phases |
| `ui/static/app.js` (author section) | Client-side JS — tab switching, version browsing, prompt editing, research selection |

### Templates

| Template | Used by |
|----------|---------|
| `author.html` | Main page — assignment form, phase tabs, version panels |
| `partials/author_assignments_list.html` | Sidebar — assignment list with R/D/F version counts |
| `partials/author_research_list.html` | Research tab — version entries with metadata |
| `partials/author_research_detail.html` | Research tab — full report view with navigation |
| `partials/author_prompt_editor.html` | Research + Draft — editable prompt textarea |
| `partials/author_drafts_list.html` | Draft tab — version entries with status badges |
| `partials/author_draft_detail.html` | Draft tab — full draft view with resume button |
| `partials/author_formats_list.html` | Format tab — version entries with draft selector |
| `partials/author_format_detail.html` | Format tab — download link |
| `partials/author_action_result.html` | Status messages (terminal launched, session resumed) |

### Prompts

| File | What it is | Editable in UI? |
|------|-----------|-----------------|
| `prompts/author_research.md` | System prompt for the research agent — how to search, output format, citation rules | No — always injected automatically |
| `apps/author/prompts/author_draft.md` | Default draft instructions — how to write OLG content, revision process, improvement suggestions | Yes — shown in the draft prompt textarea |
| `apps/author/references/olg_style_guide.md` | Evidence-based OLG writing style guide | No — injected into the full draft prompt |
| `apps/author/references/olg_toc.md` | OLG table of contents (for structure/placement reference) | No — referenced by draft agent |

### Config

The `[author]` section in `config.ini`:

| Key | Purpose | Default |
|-----|---------|---------|
| `research_model` | Model for research synthesis | `claude-sonnet-4-5-20250929` |
| `research_max_searches` | Search budget per research run | `12` |
| `research_results_per_search` | Results per search query | `8` |
| `research_max_tokens` | Max output tokens for research | `4096` |
| `style_guide` | Path to OLG style guide | `apps/author/references/olg_style_guide.md` |
| `template_docx` | Path to OLG Word template | `apps/author/references/2026 OLG Template.docx` |
| `claude_code_timeout` | Timeout for CLI draft sessions | `600` |

## How Prompts Are Assembled

### Research

The research agent sees:
1. **System prompt** (`prompts/author_research.md`) — injected via `prompt_name="author_research"` in the synthesis engine. Not editable per-run.
2. **Question** — the assignment text from `assignment.txt`, optionally followed by "Research focus for this run:" + the user's task instructions from the textarea.

The task instructions textarea is for per-run focus: keywords, areas to emphasize, things to avoid, output style preferences. It starts empty. Previous versions' instructions are pre-filled when clicking "Run Again".

### Draft

The draft prompt is assembled by `compose_draft_prompt()` from four parts:

```
[Draft instructions]          ← from textarea (default: author_draft.md)
---
## Assignment
[assignment.txt]
---
## Research Findings
[research report(s)]          ← from selected research version(s)
---
## OLG Style Guide
[olg_style_guide.md]
---
## Output Instructions
Write your draft to: `{path}`
```

The draft instructions are the only editable part in the UI. Research reports and style guide are injected automatically based on the user's selections.

## API Endpoints

All author endpoints are under `/author`. The `{name}` parameter is the assignment directory name.

### Assignment management
- `GET /author` — render the author page
- `GET /author/assignments` — sidebar list with version counts
- `POST /author/create` — create new assignment (form: `name`, `assignment`)
- `GET /author/load/{name}` — JSON with assignment text + version counts
- `POST /author/save-assignment` — update assignment text (form: `name`, `assignment`)

### Research
- `GET /author/{name}/research` — version list partial
- `GET /author/{name}/research/prompt` — prompt editor partial (empty textarea)
- `POST /author/{name}/research/run` — execute research (form: `prompt`, `assignment`)
- `GET /author/{name}/research/{num}` — version detail partial

### Drafts
- `GET /author/{name}/drafts` — version list partial
- `GET /author/{name}/drafts/prompt` — prompt editor partial (pre-filled with default draft instructions)
- `POST /author/{name}/drafts/run` — launch Claude Code terminal (form: `prompt`, `assignment`, `research_versions`)
- `GET /author/{name}/drafts/{num}` — version detail partial
- `POST /author/{name}/drafts/{num}/resume` — resume Claude Code session

### Formats
- `GET /author/{name}/formats` — version list partial with draft selector
- `POST /author/{name}/formats/run` — format a draft (form: `draft_version`)
- `GET /author/{name}/formats/{num}/download` — download .docx

## Versioning Internals (`ui/versioning.py`)

The versioning module provides pure filesystem operations with no external dependencies:

```python
next_version_dir(output_dir, phase)    # Creates research/003_20260409-1430/
list_versions(output_dir, phase)       # Returns sorted list of version dir Paths
get_version_dir(output_dir, phase, n)  # Returns specific version dir by number
version_count(output_dir, phase)       # Number of versions
latest_version_dir(output_dir, phase)  # Latest version dir or None
load_version(output_dir, phase, n)     # Full version data dict with navigation metadata
load_version_list(output_dir, phase)   # Summary list for sidebar display
```

Version directories are named `{num:03d}_{timestamp}` (e.g., `001_20260409-1430`). The number is the version identifier used in URLs and API calls.

Phase names for the directory structure: `research`, `drafts`, `formats`.

## Adding a New Phase

If you need to add a fourth phase (e.g., "Review"):

1. Add the phase to `PHASE_DIRS` in `versioning.py`
2. Add the execution function in `author.py`
3. Add endpoints in `app.py` (list, detail, prompt, run)
4. Add templates (list, detail)
5. Add a tab in `author.html` and JS handlers in `app.js`
6. Add a panel div in the `#author-panel` section

## CLI Usage

The CLI in `author.py` still works for headless/scripted runs:

```bash
# Full pipeline (research + draft terminal)
python apps/author/author.py "Consolidate VC-1 scripts" --name vc1_scripts

# Research only
python apps/author/author.py "Find VC-1 scripts" --name vc1_scripts --research-only

# Draft only (uses existing research)
python apps/author/author.py --name vc1_scripts --draft-only

# Resume a draft session
python apps/author/author.py --name vc1_scripts --resume

# Assignment from file
python apps/author/author.py --assignment-file assignment.txt --name my_task
```

CLI runs create versioned directories in the same structure as the UI, so outputs are visible from either interface.
