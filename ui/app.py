"""
Policy Navigator — Web search interface.

FastAPI application serving HTMX-powered search UI for policy analysts.
Synthesis-first: questions get natural language answers with citations.
Run with: python ui/app.py
"""

import asyncio
import json
import shutil
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import markdown

UI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = UI_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ui.search import (
    SOURCES, DEFAULT_SOURCE, PROGRAM_REGISTRY, get_default_programs,
    init_clients, do_search,
)
from ui.history import init_db, save_search, get_recent, get_by_id
from ui.versioning import (
    list_versions,
    get_version_dir,
    next_version_dir,
    version_count,
    load_version,
    load_version_list,
)
from tools.synthesis import run_synthesis
from programs.author.author import (
    load_config as load_author_config,
    get_output_dir,
    get_default_research_prompt,
    get_default_draft_prompt,
    run_research as author_run_research,
    compose_draft_prompt,
    launch_draft,
    launch_resume,
    run_format as author_run_format,
    DATA_DIR,
)
from tools.docx_reader import has_tracked_changes, read_docx, to_markdown
from tools.docx_writer import generate_docx
from programs.qc.qc_analyzer import (
    load_config as load_qc_config,
    CONFIG_FILE as QC_CONFIG_FILE,
    get_analysis_dir,
    load_csv as load_qc_csv,
    run_extract,
    run_investigate,
    run_source_check,
    SOURCE_CHECK_CONFIG,
    load_all_findings,
    flatten_findings,
    find_recurring_gaps,
    load_meta,
    reconstruct_qc_costs,
    make_forked_name,
    downstream_summary,
    clear_downstream_meta,
    save_meta,
    generate_summary_csv,
    get_investigate_progress,
    clear_investigate_progress,
    _load_filters as load_qc_filters,
    ANALYSIS_DIR as QC_DIR,
)


def _qc_results_context(name: str, rows: list, meta: dict) -> dict:
    """Build the template context for qc_results_table.html, including the
    recurring-gaps, agent-notes, and reconstructed cost-breakdown data.
    Centralized so every route renders the table the same way."""
    flat = flatten_findings(rows)
    agent_notes = [
        f for f in flat
        if (f.get("agent_notes") or "").strip()
    ]
    try:
        costs = reconstruct_qc_costs(get_analysis_dir(name))
    except Exception:
        # Never let cost reconstruction errors block the results page —
        # the template handles a missing/empty costs object gracefully.
        costs = {"total_cost": 0.0}
    return {
        "findings": flat,
        "name": name,
        "meta": meta,
        "recurring_gaps": find_recurring_gaps(flat),
        "agent_notes": agent_notes,
        "costs": costs,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize search clients and database on startup."""
    print("Initializing search clients...")
    init_clients()
    init_db()
    print(f"Ready — {len(SOURCES)} sources loaded.")
    yield


app = FastAPI(title="Policy Navigator", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=UI_DIR / "static"), name="static")
templates = Jinja2Templates(directory=UI_DIR / "templates")

# Make source registry and markdown filter available to all templates
templates.env.globals["SOURCES"] = SOURCES
templates.env.globals["DEFAULT_SOURCE"] = DEFAULT_SOURCE
templates.env.globals["PROGRAM_REGISTRY"] = PROGRAM_REGISTRY
templates.env.filters["markdown"] = lambda text: markdown.markdown(
    text, extensions=["tables", "fenced_code"]
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the search form page."""
    return templates.TemplateResponse(request, "index.html")


def _programs_by_source_from_form(
    form: dict, active_sources: list[str]
) -> dict[str, list[str]]:
    """
    Extract per-source program selections from form data.

    Reads `programs_<source>` fields (multi-value) for each active source
    that has a program filter. Sources without checkboxes (e.g. FNS) get
    no entry. Sources whose user submitted zero checkboxes get an empty
    list — interpreted by the backend as "no programs match" (returns 0
    results). To indicate "no filter", omit the source key entirely.
    """
    result: dict[str, list[str]] = {}
    for src in active_sources:
        cfg = SOURCES.get(src, {})
        if not cfg.get("has_program_filter"):
            continue
        # FastAPI forms expose multi-value as repeated keys
        values = form.getlist(f"programs_{src}")
        result[src] = [v for v in values if v]
    return result


@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request):
    """Synthesize an answer to a policy question."""
    form = await request.form()
    question = (form.get("question") or "").strip()
    if not question:
        return HTMLResponse("")

    sources = form.getlist("sources") or [DEFAULT_SOURCE]
    deep = form.get("deep") == "true"

    programs_by_source = _programs_by_source_from_form(form, sources)

    # Run synthesis in a thread to avoid blocking the event loop
    result = await asyncio.to_thread(
        run_synthesis,
        question=question,
        sources=sources,
        programs_by_source=programs_by_source,
        deep=deep,
    )

    if result.error:
        # Errored runs are still persisted to history with the failure message
        # in `answer` (current behavior). Skip-on-error and an `error` column
        # are bundled with CA-14 in the search-cleanup phase.
        await asyncio.to_thread(
            save_search,
            question=question,
            sources=sources,
            programs_by_source=programs_by_source,
            deep=deep,
            result=result,
        )
        return templates.TemplateResponse(
            request,
            "partials/answer_error.html",
            {"error": result.error},
        )

    # Save to history
    search_id = await asyncio.to_thread(
        save_search,
        question=question,
        sources=sources,
        programs_by_source=programs_by_source,
        deep=deep,
        result=result,
    )

    return templates.TemplateResponse(
        request,
        "partials/answer.html",
        {
            "result": result,
            "question": question,
            "sources": sources,
            "search_id": search_id,
        },
    )


# ============================================================
# HISTORY
# ============================================================

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Full history page."""
    searches = await asyncio.to_thread(get_recent, 50)
    return templates.TemplateResponse(
        request, "history.html", {"searches": searches}
    )


@app.get("/history/recent", response_class=HTMLResponse)
async def history_recent(request: Request):
    """Recent searches partial for sidebar."""
    searches = await asyncio.to_thread(get_recent, 10)
    return templates.TemplateResponse(
        request, "partials/history_list.html", {"searches": searches}
    )


@app.get("/history/{search_id}", response_class=HTMLResponse)
async def history_detail(request: Request, search_id: int):
    """View a past search result."""
    entry = await asyncio.to_thread(get_by_id, search_id)
    if not entry:
        return HTMLResponse("<p>Search not found.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "history_detail.html", {"entry": entry}
    )


# ============================================================
# SEARCH EXPORT
# ============================================================

SOURCE_LABELS = {
    "olg": "Online Guide (OLG)",
    "fns": "FNS Handbook 310",
    "cmr": "Code of Massachusetts Regulations",
    "cfr": "7 CFR (Federal SNAP Regulations)",
}


def _build_export_markdown(entry: dict) -> str:
    """Build a markdown document from a search history entry."""
    mode = "Deep" if entry.get("deep") else "Standard"
    sources_str = ", ".join(s.upper() for s in entry["sources"])
    lines = [
        f"# {entry['question']}",
        "",
        f"**Date:** {entry['created_at']} | **Mode:** {mode} | **Sources:** {sources_str}",
        "",
        "---",
        "",
        entry["answer"],
    ]

    # Sources section
    evidence = entry.get("evidence", {})
    if evidence:
        lines += ["", "---", "", "## Sources", ""]
        for source_key, results_list in evidence.items():
            if not results_list:
                continue
            label = SOURCE_LABELS.get(source_key, source_key.upper())
            lines.append(f"### {label}")
            lines.append("")
            for r in results_list:
                meta = r.get("metadata", {})
                score_pct = round(r.get("score", 0) * 100)
                text = r.get("text", "")

                if source_key == "olg":
                    title = meta.get("page_title", "")
                    section = meta.get("section_heading", "")
                    cite = f"{title} > {section}" if section else title
                    url = meta.get("url", "")
                    if url:
                        line = f"- [{cite}]({url}) ({score_pct}%)"
                    else:
                        line = f"- **{cite}** ({score_pct}%)"
                elif source_key == "fns":
                    sec_num = meta.get("section_number", "")
                    sec_title = meta.get("section_title", "")
                    cite = f"FNS {sec_num}: {sec_title}" if sec_num else sec_title
                    line = f"- **{cite}** ({score_pct}%)"
                elif source_key == "cmr":
                    sec_num = meta.get("section_number", "")
                    sec_title = meta.get("section_title", "")
                    cite = f"CMR {sec_num}: {sec_title}" if sec_num else sec_title
                    line = f"- **{cite}** ({score_pct}%)"
                elif source_key == "cfr":
                    sec_num = meta.get("section_number", "")
                    sec_title = meta.get("section_title", "")
                    cite = f"7 CFR § {sec_num} {sec_title}" if sec_num else sec_title
                    line = f"- **{cite}** ({score_pct}%)"
                else:
                    line = f"- ({score_pct}%)"

                lines.append(line)
                if text:
                    lines.append(f"  {text}")
                    lines.append("")
            lines.append("")

    return "\n".join(lines)


@app.get("/search/export/{search_id}")
async def search_export(search_id: int):
    """Export a search result as a .docx file."""
    from tools.docx_writer import generate_docx

    entry = await asyncio.to_thread(get_by_id, search_id)
    if not entry:
        return HTMLResponse("<p>Search not found.</p>", status_code=404)

    export_dir = PROJECT_ROOT / "output" / "search_exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_dir / f"search_{search_id}.docx"

    md = _build_export_markdown(entry)
    await asyncio.to_thread(generate_docx, md, output_path, None)

    return FileResponse(
        output_path,
        filename=f"policy_search_{search_id}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ============================================================
# RAW SEARCH (power users)
# ============================================================

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request):
    """Raw search — returns result cards (kept for power users)."""
    form = await request.form()
    query = (form.get("query") or "").strip()
    if not query:
        return HTMLResponse("")

    source = form.get("source") or DEFAULT_SOURCE
    cfg = SOURCES.get(source, {})
    programs = None
    if cfg.get("has_program_filter"):
        programs = [v for v in form.getlist(f"programs_{source}") if v]

    results = do_search(query=query, source=source, programs=programs)

    return templates.TemplateResponse(
        request,
        "partials/tab_content.html",
        {"results": results, "query": query, "source": source},
    )


# ============================================================
# AUTHOR — Main page + assignment management
# ============================================================

@app.get("/author", response_class=HTMLResponse)
async def author_page(request: Request):
    """Render the authoring page."""
    return templates.TemplateResponse(request, "author.html")


@app.get("/author/assignments", response_class=HTMLResponse)
async def author_assignments(request: Request):
    """List existing assignments with their version counts per phase."""
    assignments = []
    if DATA_DIR.exists():
        for d in sorted(DATA_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                assignments.append({
                    "name": d.name,
                    "research_count": version_count(d, "research"),
                    "draft_count": version_count(d, "drafts"),
                    "format_count": version_count(d, "formats"),
                })
    return templates.TemplateResponse(
        request, "partials/author_assignments_list.html",
        {"assignments": assignments},
    )


@app.post("/author/create", response_class=HTMLResponse)
async def author_create(
    request: Request,
    name: str = Form(...),
    assignment: str = Form(""),
):
    """Create a new assignment."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Assignment name is required.</p>")

    output_dir = get_output_dir(name)
    assignment = assignment.strip()
    if assignment:
        (output_dir / "assignment.txt").write_text(assignment, encoding="utf-8")

    return JSONResponse({"name": name, "created": True})


@app.get("/author/load/{name}")
async def author_load(name: str):
    """Load an assignment's details as JSON."""
    output_dir = get_output_dir(name)
    assignment_file = output_dir / "assignment.txt"
    assignment = ""
    if assignment_file.exists():
        assignment = assignment_file.read_text(encoding="utf-8")
    return JSONResponse({
        "name": name,
        "assignment": assignment,
        "research_count": version_count(output_dir, "research"),
        "draft_count": version_count(output_dir, "drafts"),
        "format_count": version_count(output_dir, "formats"),
    })


@app.post("/author/save-assignment")
async def author_save_assignment(
    name: str = Form(...),
    assignment: str = Form(""),
):
    """Save/update assignment text."""
    output_dir = get_output_dir(name.strip())
    (output_dir / "assignment.txt").write_text(assignment.strip(), encoding="utf-8")
    return JSONResponse({"saved": True})


# ============================================================
# AUTHOR — Research
# ============================================================

@app.get("/author/{name}/research", response_class=HTMLResponse)
async def author_research_list(request: Request, name: str):
    """List all research versions."""
    output_dir = get_output_dir(name)
    versions = load_version_list(output_dir, "research")
    return templates.TemplateResponse(
        request, "partials/author_research_list.html",
        {"versions": versions, "name": name},
    )


@app.get("/author/{name}/research/prompt", response_class=HTMLResponse)
async def author_research_prompt(request: Request, name: str):
    """Get the research prompt editor (task instructions only — system prompt injected automatically)."""
    return templates.TemplateResponse(
        request, "partials/author_prompt_editor.html",
        {"prompt": "", "name": name, "phase": "research"},
    )


@app.post("/author/{name}/research/run", response_class=HTMLResponse)
async def author_research_run(
    request: Request,
    name: str,
    prompt: str = Form(""),
    assignment: str = Form(""),
    sources: str = Form("olg,cmr,fns,cfr"),
):
    """Execute research with provided task instructions and source selection."""
    name = name.strip()
    output_dir = get_output_dir(name)

    # Load assignment from form or saved file
    assignment = assignment.strip()
    if not assignment:
        saved = output_dir / "assignment.txt"
        if saved.exists():
            assignment = saved.read_text(encoding="utf-8").strip()
    if not assignment:
        return HTMLResponse("<p>No assignment text found. Enter one first.</p>")

    # Parse sources
    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    if not source_list:
        source_list = ["olg", "cmr", "fns", "cfr"]

    # Task instructions are the user-editable part (focus, keywords, constraints).
    # The system research prompt (author_research.md) is always injected by run_research.
    task_instructions = prompt.strip()

    # Create version directory
    version_dir = next_version_dir(output_dir, "research")

    # Run research — task_instructions get saved as prompt.md in the version dir
    result = await asyncio.to_thread(
        author_run_research, assignment, task_instructions, version_dir,
        load_author_config(), sources=source_list,
    )

    # Return the detail view of the new version
    from ui.versioning import _parse_version_num
    num = _parse_version_num(version_dir.name)
    view = load_version(output_dir, "research", num)
    return templates.TemplateResponse(
        request, "partials/author_research_detail.html",
        {"view": view, "name": name},
    )


@app.get("/author/{name}/research/{num}", response_class=HTMLResponse)
async def author_research_detail(request: Request, name: str, num: int):
    """View a specific research version."""
    output_dir = get_output_dir(name)
    view = load_version(output_dir, "research", num)
    if not view:
        return HTMLResponse("<p>Research version not found.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "partials/author_research_detail.html",
        {"view": view, "name": name},
    )


# ============================================================
# AUTHOR — Drafts
# ============================================================

@app.get("/author/{name}/drafts", response_class=HTMLResponse)
async def author_drafts_list(request: Request, name: str):
    """List all draft versions."""
    output_dir = get_output_dir(name)
    versions = load_version_list(output_dir, "drafts")
    return templates.TemplateResponse(
        request, "partials/author_drafts_list.html",
        {"versions": versions, "name": name},
    )


@app.get("/author/{name}/drafts/prompt", response_class=HTMLResponse)
async def author_draft_prompt(request: Request, name: str):
    """Get the default draft prompt for the textarea."""
    prompt = get_default_draft_prompt()
    return templates.TemplateResponse(
        request, "partials/author_prompt_editor.html",
        {"prompt": prompt, "name": name, "phase": "drafts"},
    )


@app.post("/author/{name}/drafts/run", response_class=HTMLResponse)
async def author_draft_run(
    request: Request,
    name: str,
    prompt: str = Form(""),
    assignment: str = Form(""),
    research_versions: str = Form(""),
):
    """Launch Claude Code with provided prompt + selected research versions."""
    name = name.strip()
    output_dir = get_output_dir(name)

    # Load assignment
    assignment = assignment.strip()
    if not assignment:
        saved = output_dir / "assignment.txt"
        if saved.exists():
            assignment = saved.read_text(encoding="utf-8").strip()
    if not assignment:
        return HTMLResponse("<p>No assignment text found.</p>")

    # Parse selected research versions
    research_nums = []
    if research_versions.strip():
        research_nums = [int(x.strip()) for x in research_versions.split(",") if x.strip()]

    # Resolve research version dirs
    research_paths = []
    based_on_labels = []
    for num in research_nums:
        vdir = get_version_dir(output_dir, "research", num)
        if vdir:
            research_paths.append(vdir)
            based_on_labels.append(f"research/{num:03d}")

    # Use provided prompt or default
    instructions = prompt.strip() or get_default_draft_prompt()

    # Create draft version directory
    draft_dir = next_version_dir(output_dir, "drafts")
    draft_file = draft_dir / "draft.md"
    session_id = str(uuid.uuid4())

    config = load_author_config()

    # Assemble full prompt
    full_prompt = compose_draft_prompt(
        instructions=instructions,
        research_paths=research_paths,
        assignment=assignment,
        config=config,
        draft_file=draft_file,
    )

    # Launch Claude Code terminal
    launch_draft(
        full_prompt=full_prompt,
        draft_dir=draft_dir,
        instructions=instructions,
        config=config,
        name=name,
        session_id=session_id,
        based_on=based_on_labels,
    )

    from ui.versioning import _parse_version_num
    num = _parse_version_num(draft_dir.name)

    msg = (
        f"## Claude Code Terminal Launched\n\n"
        f"A new terminal window has opened for the drafting session.\n\n"
        f"**Draft version:** {num:03d}\n\n"
        f"**Based on research:** {', '.join(based_on_labels) or 'none selected'}\n\n"
        f"When it finishes, the draft will be at:\n"
        f"`{draft_file}`\n\n"
        f"Session ID `{session_id[:8]}...` saved for resume."
    )

    return templates.TemplateResponse(
        request, "partials/author_action_result.html",
        {"message": msg},
    )


@app.post("/author/{name}/drafts/{num}/resume", response_class=HTMLResponse)
async def author_draft_resume(request: Request, name: str, num: int):
    """Resume a specific draft session."""
    output_dir = get_output_dir(name)
    view = load_version(output_dir, "drafts", num)
    if not view or not view.get("session_id"):
        return HTMLResponse("<p>No session ID found for this draft version.</p>")

    launch_resume(view["session_id"], name)

    msg = (
        f"## Session Resumed\n\n"
        f"A terminal window has opened resuming session for draft v{num:03d}.\n\n"
        f"Session: `{view['session_id'][:8]}...`"
    )
    return templates.TemplateResponse(
        request, "partials/author_action_result.html",
        {"message": msg},
    )


@app.get("/author/{name}/drafts/{num}", response_class=HTMLResponse)
async def author_draft_detail(request: Request, name: str, num: int):
    """View a specific draft version."""
    output_dir = get_output_dir(name)
    view = load_version(output_dir, "drafts", num)
    if not view:
        return HTMLResponse("<p>Draft version not found.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "partials/author_draft_detail.html",
        {"view": view, "name": name},
    )


# ============================================================
# AUTHOR — Formats
# ============================================================

@app.get("/author/{name}/formats", response_class=HTMLResponse)
async def author_formats_list(request: Request, name: str):
    """List all format versions."""
    output_dir = get_output_dir(name)
    versions = load_version_list(output_dir, "formats")
    return templates.TemplateResponse(
        request, "partials/author_formats_list.html",
        {"versions": versions, "name": name},
    )


@app.post("/author/{name}/formats/run", response_class=HTMLResponse)
async def author_format_run(
    request: Request,
    name: str,
    draft_version: int = Form(...),
):
    """Format a selected draft version."""
    output_dir = get_output_dir(name)

    # Find the draft version
    draft_dir = get_version_dir(output_dir, "drafts", draft_version)
    if not draft_dir:
        return HTMLResponse(f"<p>Draft version {draft_version} not found.</p>")

    draft_path = draft_dir / "draft.md"
    if not draft_path.exists():
        return HTMLResponse(f"<p>No draft.md found in draft version {draft_version}.</p>")

    # Create format version directory
    format_dir = next_version_dir(output_dir, "formats")
    output_path = format_dir / "output.docx"

    config = load_author_config()
    docx_path = await asyncio.to_thread(
        author_run_format, draft_path, output_path, config,
    )

    if docx_path and docx_path.exists():
        # Save metadata
        meta = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "based_on": f"drafts/{draft_version:03d}",
        }
        (format_dir / "meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        from ui.versioning import _parse_version_num
        num = _parse_version_num(format_dir.name)
        view = load_version(output_dir, "formats", num)
        return templates.TemplateResponse(
            request, "partials/author_format_detail.html",
            {"view": view, "name": name},
        )
    else:
        msg = "## Format Failed\n\nCould not generate .docx. Check the server console for details."
        return templates.TemplateResponse(
            request, "partials/author_action_result.html",
            {"message": msg},
        )


@app.get("/author/{name}/formats/{num}/download")
async def author_format_download(name: str, num: int):
    """Download a specific format version's .docx."""
    output_dir = get_output_dir(name)
    format_dir = get_version_dir(output_dir, "formats", num)
    if not format_dir:
        return HTMLResponse("<p>Format version not found.</p>", status_code=404)

    docx_file = format_dir / "output.docx"
    if not docx_file.exists():
        return HTMLResponse("<p>File not found.</p>", status_code=404)

    response = FileResponse(
        docx_file,
        filename=f"{name}_v{num:03d}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


# ============================================================
# QC ANALYSIS
# ============================================================

import re as _re

def _clean_determination(value: str) -> str:
    """Strip parenthetical noise like '(Complete A1 and A2)' from determination."""
    return _re.sub(r"\s*\(Complete [^)]+\)", "", value).strip()


def _build_preview_rows(rows: list[dict]) -> list[dict]:
    """Build preview rows for the upload table. All rows included."""
    preview_rows = []
    for i, row in enumerate(rows, start=1):
        preview_rows.append({
            "index": i,
            "review_number": row.get("Review Number", ""),
            "apid": row.get("APID", ""),
            "determination": _clean_determination(row.get("Food Stamp Determination", "")),
            "error_type": " / ".join(p.strip() for p in row.get("Type Of Errors", "").split(";") if p.strip()),
            "finding_preview": row.get("QC Findings", "")[:120],
        })
    return preview_rows


@app.get("/qc", response_class=HTMLResponse)
async def qc_page(request: Request):
    """Render the QC analysis page."""
    filters = load_qc_filters(load_qc_config())
    return templates.TemplateResponse(
        request, "qc.html", {"filters": filters},
    )


@app.get("/qc/analyses", response_class=HTMLResponse)
async def qc_analyses(request: Request):
    """List existing analyses with their phase status."""
    analyses = []
    if QC_DIR.exists():
        for d in sorted(QC_DIR.iterdir(), reverse=True):
            if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_"):
                meta = load_meta(d)
                if meta:
                    analyses.append({
                        "name": d.name,
                        "phases": meta.get("phases", {}),
                    })
    return templates.TemplateResponse(
        request, "partials/qc_analyses_list.html",
        {"analyses": analyses},
    )


@app.get("/qc/load/{name}")
async def qc_load(name: str):
    """Load an analysis's details as JSON."""
    analysis_dir = get_analysis_dir(name)
    meta = load_meta(analysis_dir)
    if not meta:
        return JSONResponse({"error": "Analysis not found"}, status_code=404)

    # Determine most advanced phase
    phases = meta.get("phases", {})
    latest_phase = None
    for phase in ("cfr_checked", "fns_checked", "cmr_checked", "investigated", "extracted", "uploaded"):
        if phases.get(phase):
            latest_phase = phase
            break

    return JSONResponse({
        "name": name,
        "meta": meta,
        "latest_phase": latest_phase,
    })


@app.get("/qc/view/{name}/{phase}", response_class=HTMLResponse)
async def qc_view(request: Request, name: str, phase: str):
    """Load a view of an analysis phase from disk."""
    analysis_dir = get_analysis_dir(name)
    meta = load_meta(analysis_dir)
    if not meta:
        return HTMLResponse("<p>Analysis not found.</p>", status_code=404)

    if phase == "upload":
        # Re-render upload preview
        csv_path = analysis_dir / "upload.csv"
        if not csv_path.exists():
            return HTMLResponse("<p>No upload found.</p>")
        fieldnames, rows = load_qc_csv(csv_path)
        return templates.TemplateResponse(
            request, "partials/qc_upload_preview.html",
            {
                "name": name,
                "filename": meta.get("source_file", ""),
                "total_rows": meta.get("total_rows", len(rows)),
                "columns": fieldnames,
                "preview_rows": _build_preview_rows(rows),
            },
        )

    elif phase == "extract":
        rows = load_all_findings(analysis_dir)
        extracted_rows = [r for r in rows if r.get("phase") in ("extracted", "investigated")]
        if not extracted_rows:
            return HTMLResponse("<p>No extraction results found. Click Extract first.</p>")
        return templates.TemplateResponse(
            request, "partials/qc_triage_table.html",
            {"findings": flatten_findings(extracted_rows), "name": name, "meta": meta},
        )

    elif phase in ("investigate", "cmr_check", "fns_check", "cfr_check"):
        # If an investigate run is in flight for this analysis, show the
        # running partial so a page reload re-attaches to the live job
        # instead of showing stale (or empty) results.
        if phase == "investigate":
            progress = get_investigate_progress(name)
            if progress and progress.get("state") == "running":
                return templates.TemplateResponse(
                    request, "partials/qc_investigate_running.html",
                    {
                        "name": name,
                        "progress": progress,
                        "eta": _eta_minutes(progress),
                    },
                )
        # All three post-investigation views use the same results table,
        # which conditionally shows CMR/FNS columns when data is present
        rows = load_all_findings(analysis_dir)
        if not rows:
            return HTMLResponse("<p>No results found.</p>")
        return templates.TemplateResponse(
            request, "partials/qc_results_table.html",
            _qc_results_context(name, rows, meta),
        )

    return HTMLResponse(f"<p>Unknown phase: {phase}</p>", status_code=400)


@app.post("/qc/upload", response_class=HTMLResponse)
async def qc_upload(
    request: Request,
    name: str = Form(""),
    file: UploadFile = File(...),
):
    """Upload a QC CSV and show a preview. New uploads land in a
    timestamped folder ({name}_{YYYY-MM-DD_HHMM}) so re-uploads of the
    same name don't silently overwrite earlier runs."""
    # Auto-populate name from filename if empty
    name = name.strip()
    if not name:
        name = Path(file.filename).stem

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    name = f"{name}_{timestamp}"
    analysis_dir = get_analysis_dir(name)

    # Save uploaded file
    upload_path = analysis_dir / "upload.csv"
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Load and validate
    try:
        fieldnames, rows = load_qc_csv(upload_path)
    except Exception as e:
        return HTMLResponse(f"<p>Error reading CSV: {e}</p>")

    if "QC Findings" not in fieldnames:
        return HTMLResponse(
            "<p>CSV must contain a 'QC Findings' column. "
            f"Found columns: {', '.join(fieldnames[:10])}</p>"
        )

    preview_rows = _build_preview_rows(rows)

    # Save meta
    meta = load_meta(analysis_dir) or {}
    meta["name"] = name
    meta["created"] = datetime.now().isoformat()
    meta["source_file"] = file.filename
    meta["total_rows"] = len(rows)
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"]["uploaded"] = True
    if "cost" not in meta:
        meta["cost"] = {}
    if "filter_snapshot" not in meta:
        meta["filter_snapshot"] = load_qc_filters(load_qc_config())
    save_meta(analysis_dir, meta)

    return templates.TemplateResponse(
        request, "partials/qc_upload_preview.html",
        {
            "name": name,
            "filename": file.filename,
            "total_rows": len(rows),
            "columns": fieldnames,
            "preview_rows": preview_rows,
        },
    )


@app.post("/qc/extract", response_class=HTMLResponse)
async def qc_extract(
    request: Request,
    name: str = Form(...),
    rerun: str = Form(""),
    confirm: str = Form(""),
):
    """Run the Extractor phase, or show existing results.

    On rerun, if downstream phases have data and `confirm` is unset, returns
    a modal asking the user to choose: fork to a new analysis (preserve the
    current run), re-extract in place (destructive), or cancel.
    """
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)

    # View-before-run: if extraction results exist and not a rerun, show them
    if rerun != "1":
        rows = load_all_findings(analysis_dir)
        extracted_rows = [r for r in rows if r.get("phase") in ("extracted", "investigated")]
        if extracted_rows:
            meta = load_meta(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_triage_table.html",
                {"findings": flatten_findings(extracted_rows), "name": name, "meta": meta},
            )

    # Re-run safety: if downstream phases populated and user hasn't picked
    # a confirm path, return the modal.
    if rerun == "1" and confirm == "":
        summary = downstream_summary(analysis_dir)
        if summary["populated"]:
            return templates.TemplateResponse(
                request, "partials/qc_extract_confirm.html",
                {"summary": summary, "name": name},
            )

    # Fork: create a fresh analysis dir, copy the source CSV, and proceed
    # against the new dir. Original analysis is left untouched.
    if rerun == "1" and confirm == "fork":
        old_csv = analysis_dir / "upload.csv"
        if not old_csv.exists():
            return HTMLResponse("<p>No source CSV in the original analysis.</p>")
        new_name = make_forked_name(name)
        new_dir = get_analysis_dir(new_name)
        shutil.copyfile(old_csv, new_dir / "upload.csv")
        old_meta = load_meta(analysis_dir) or {}
        new_meta = {
            "name": new_name,
            "created": datetime.now().isoformat(),
            "source_file": old_meta.get("source_file", ""),
            "forked_from": name,
            "total_rows": old_meta.get("total_rows", 0),
            "phases": {"uploaded": True},
            "filter_snapshot": load_qc_filters(load_qc_config()),
        }
        save_meta(new_dir, new_meta)
        # Switch context to the new analysis for the rest of this request
        name = new_name
        analysis_dir = new_dir

    # Overwrite path: clear downstream meta so the analysis returns to
    # extract-only state. The nested judge/cross-check data inside row
    # findings is wiped automatically when run_extract rewrites them.
    elif rerun == "1" and confirm == "overwrite":
        clear_downstream_meta(analysis_dir)

    # Load CSV
    csv_path = analysis_dir / "upload.csv"
    if not csv_path.exists():
        return HTMLResponse("<p>No CSV uploaded. Upload a file first.</p>")

    _, rows = load_qc_csv(csv_path)

    config = load_qc_config()
    extracted_rows = await asyncio.to_thread(run_extract, analysis_dir, rows, config)

    meta = load_meta(analysis_dir)
    return templates.TemplateResponse(
        request, "partials/qc_triage_table.html",
        {"findings": flatten_findings(extracted_rows), "name": name, "meta": meta},
    )


def _eta_minutes(progress: dict) -> int | None:
    """Estimate remaining minutes from started_at + completed/total.

    Returns None if there's not enough data to estimate (no completes yet).
    Rounds up so the indicator never undersells time remaining.
    """
    completed = progress.get("completed", 0)
    total = progress.get("total", 0)
    started = progress.get("started_at")
    if completed <= 0 or total <= 0 or not started:
        return None
    try:
        start_dt = datetime.fromisoformat(started)
    except (ValueError, TypeError):
        return None
    elapsed = (datetime.now() - start_dt).total_seconds()
    if elapsed <= 0:
        return None
    rate = completed / elapsed  # findings per second
    remaining = total - completed
    if remaining <= 0 or rate <= 0:
        return 0
    secs = remaining / rate
    return max(1, int((secs + 59) // 60))  # ceil to whole minute


@app.post("/qc/investigate", response_class=HTMLResponse)
async def qc_investigate(
    request: Request,
    name: str = Form(...),
    row_indices: str = Form(""),
    rerun: str = Form(""),
):
    """Kick off investigate as a background task and return the progress
    partial. The browser then polls /qc/investigate/status until done.
    """
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)

    # View-before-run: if investigated findings exist and not a rerun, show them
    if rerun != "1":
        rows = load_all_findings(analysis_dir)
        if any(r.get("phase") == "investigated" for r in rows):
            meta = load_meta(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                _qc_results_context(name, rows, meta),
            )

    # Parse row indices from comma-separated string
    indices = None
    if row_indices.strip():
        indices = [int(x.strip()) for x in row_indices.split(",") if x.strip()]

    if not indices:
        # Default to all rows (extracted or already investigated)
        rows = load_all_findings(analysis_dir)
        indices = [r["row_index"] for r in rows
                   if r.get("phase") in ("extracted", "investigated")]

    if not indices:
        return HTMLResponse("<p>No rows selected for investigation.</p>")

    # If a previous run for this name is still in flight, just return the
    # progress partial without spawning a second task — first-writer wins.
    existing = get_investigate_progress(name)
    if existing and existing.get("state") == "running":
        return templates.TemplateResponse(
            request, "partials/qc_investigate_running.html",
            {
                "name": name,
                "progress": existing,
                "eta": _eta_minutes(existing),
            },
        )

    # Clear any stale "done" entry from a prior run before starting fresh,
    # so the polling endpoint doesn't immediately report "done".
    clear_investigate_progress(name)

    config = load_qc_config()
    asyncio.create_task(
        asyncio.to_thread(run_investigate, analysis_dir, indices, config)
    )

    # Return the running partial; HTMX will start polling status.
    return templates.TemplateResponse(
        request, "partials/qc_investigate_running.html",
        {
            "name": name,
            "progress": {
                "state": "running",
                "total": len(indices),  # approximation; status endpoint will correct
                "completed": 0,
                "skipped": 0,
                "errors": 0,
                "in_flight": [],
            },
            "eta": None,
        },
    )


@app.get("/qc/investigate/status", response_class=HTMLResponse)
async def qc_investigate_status(request: Request, name: str):
    """Poll endpoint for the in-flight investigate task. Returns the
    running partial while in progress, or the results table when done.
    """
    name = name.strip()
    progress = get_investigate_progress(name)

    if not progress:
        # No record — either never ran, or already cleared. Try to show
        # results if they exist; otherwise an idle message.
        analysis_dir = get_analysis_dir(name)
        rows = load_all_findings(analysis_dir)
        if any(r.get("phase") == "investigated" for r in rows):
            meta = load_meta(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                _qc_results_context(name, rows, meta),
            )
        return HTMLResponse("<p>No investigation in progress.</p>")

    if progress.get("state") == "done":
        analysis_dir = get_analysis_dir(name)
        rows = load_all_findings(analysis_dir)
        meta = load_meta(analysis_dir)
        # Keep progress entry for one more poll so transient race conditions
        # don't blank the UI; clean up on the next idle poll instead.
        return templates.TemplateResponse(
            request, "partials/qc_results_table.html",
            _qc_results_context(name, rows, meta),
        )

    return templates.TemplateResponse(
        request, "partials/qc_investigate_running.html",
        {
            "name": name,
            "progress": progress,
            "eta": _eta_minutes(progress),
        },
    )


@app.post("/qc/source_check/{source}", response_class=HTMLResponse)
async def qc_source_check(
    request: Request,
    source: str,
    name: str = Form(...),
    rerun: str = Form(""),
):
    """Run a CMR / FNS / CFR cross-check on Partial/Gap findings, or show existing results."""
    if source not in SOURCE_CHECK_CONFIG:
        return HTMLResponse(
            f"<p>Unknown source: {source}</p>", status_code=400,
        )

    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)
    phase_name = SOURCE_CHECK_CONFIG[source]["phase_name"]

    # View-before-run: if checks exist and not a rerun, show them
    if rerun != "1":
        meta = load_meta(analysis_dir) or {}
        if meta.get("phases", {}).get(phase_name):
            all_rows = load_all_findings(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                _qc_results_context(name, all_rows, meta),
            )

    config = load_qc_config()
    await asyncio.to_thread(run_source_check, source, analysis_dir, None, config)

    all_rows = load_all_findings(analysis_dir)
    meta = load_meta(analysis_dir)
    return templates.TemplateResponse(
        request, "partials/qc_results_table.html",
        _qc_results_context(name, all_rows, meta),
    )


@app.get("/qc/finding/{name}/{row_index}")
async def qc_finding_json(name: str, row_index: int):
    """Download an individual finding JSON."""
    from programs.qc.qc_analyzer import load_finding as _load_finding
    analysis_dir = get_analysis_dir(name)
    finding = _load_finding(analysis_dir, row_index)
    if not finding:
        return HTMLResponse("<p>Finding not found.</p>", status_code=404)
    return JSONResponse(finding)


@app.post("/qc/judge_resume/{name}/{row_index}/{finding_index}",
          response_class=HTMLResponse)
async def qc_judge_resume(name: str, row_index: int, finding_index: int):
    """Open a terminal resuming the Claude Code judge session for a finding."""
    from programs.qc.qc_analyzer import load_finding as _load_finding
    from programs.qc.judge_claude_code import launch_judge_resume

    analysis_dir = get_analysis_dir(name)
    row = _load_finding(analysis_dir, row_index)
    if not row:
        return HTMLResponse("<p>Finding not found.</p>", status_code=404)

    findings = row.get("findings", [])
    target = next(
        (f for f in findings if f.get("finding_index") == finding_index),
        None,
    )
    if not target:
        return HTMLResponse(
            f"<p>Finding {finding_index} not found in row {row_index}.</p>",
            status_code=404,
        )

    session_id = target.get("_session_id")
    if not session_id:
        return HTMLResponse(
            "<p>This finding has no Claude Code session ID — it was either "
            "judged via the API engine, or pre-dates the dual-engine "
            "support. Re-run investigate via the Claude Code engine to "
            "produce a resumable session.</p>",
            status_code=400,
        )

    label = f"{name} {row_index}.{finding_index}"
    await asyncio.to_thread(launch_judge_resume, session_id, label)

    return HTMLResponse(
        f'<div class="qc-resume-status">Terminal opened. '
        f'Resuming session <code>{session_id[:8]}…</code> for '
        f'finding {row_index}.{finding_index}.</div>'
    )


@app.get("/qc/download/{name}")
async def qc_download(name: str):
    """Download the summary CSV."""
    analysis_dir = get_analysis_dir(name)
    csv_path = await asyncio.to_thread(generate_summary_csv, analysis_dir)
    if not csv_path or not csv_path.exists():
        return HTMLResponse("<p>No results to download.</p>", status_code=404)
    return FileResponse(
        csv_path,
        filename=f"{name}_summary.csv",
        media_type="text/csv",
    )


# ------------------------------------------------------------
# QC PPT panel + orchestration
# ------------------------------------------------------------

from programs.qc.ppt_generator import (
    ensure_pptx_built as _ppt_ensure_built,
    generate_ppt as _ppt_generate,
    resume_ppt as _ppt_resume,
    run_ppt_again as _ppt_run_again,
    read_metadata as _ppt_read_metadata,
)


def _list_ppt_versions(runs_dir: Path) -> list[dict]:
    """Enumerate PPT runs under output/qc_analysis/{name_ts}/ppt/runs/.
    Each entry: {num, ts, has_outline, has_pptx, has_session, classifications,
    selected_count, format_status, format_error}. Returns [] if dir missing.

    Side effect: calls ensure_pptx_built() on each run so newly-arrived
    outline.json files get formatted opportunistically. Idempotent — built
    runs short-circuit immediately."""
    if not runs_dir.exists():
        return []
    out = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        try:
            num = int(d.name.split("_", 1)[0])
        except (ValueError, IndexError):
            continue
        ts = d.name.split("_", 1)[1] if "_" in d.name else ""

        # Lazy format: turn outline.json → output.pptx the moment it appears.
        _ppt_ensure_built(d)

        entry = {
            "num": num,
            "ts": ts,
            "dir": str(d),
            "has_outline": (d / "outline.json").exists(),
            "has_pptx": (d / "output.pptx").exists(),
            "has_session": (d / "session_id.txt").exists(),
        }
        inputs_file = d / "inputs.json"
        if inputs_file.exists():
            try:
                inputs = json.loads(inputs_file.read_text(encoding="utf-8"))
                fs = inputs.get("filter_state", {}) or {}
                cls = []
                if fs.get("include_gap"):
                    cls.append("Gap")
                if fs.get("include_partial"):
                    cls.append("Partial")
                if fs.get("include_adequate"):
                    cls.append("Adequate")
                entry["classifications"] = cls
                entry["selected_count"] = len(inputs.get("selected_findings", []) or [])
            except (json.JSONDecodeError, OSError):
                pass

        meta = _ppt_read_metadata(d)
        if meta:
            entry["format_status"] = meta.get("format_status")
            entry["format_error"] = meta.get("format_error")
            entry["format_warnings"] = meta.get("format_warnings", [])

        out.append(entry)
    return out


def _load_ppt_version(runs_dir: Path, num: int | None) -> dict | None:
    """Load one PPT run's data with navigation metadata for the detail view."""
    versions = _list_ppt_versions(runs_dir)
    total = len(versions)
    if total == 0:
        return None

    if num is None:
        idx = total - 1
    else:
        idx = next((i for i, v in enumerate(versions) if v["num"] == num), total - 1)

    v = versions[idx]
    version_dir = Path(v["dir"])
    data = dict(v)
    data["version_num"] = v["num"]
    data["total"] = total
    data["index"] = idx + 1
    data["has_prev"] = idx > 0
    data["has_next"] = idx < total - 1
    if data["has_prev"]:
        data["prev_num"] = versions[idx - 1]["num"]
    if data["has_next"]:
        data["next_num"] = versions[idx + 1]["num"]

    inputs_file = version_dir / "inputs.json"
    if inputs_file.exists():
        try:
            inputs = json.loads(inputs_file.read_text(encoding="utf-8"))
            data["instructions"] = inputs.get("instructions", "")
        except (json.JSONDecodeError, OSError):
            pass

    sid_file = version_dir / "session_id.txt"
    if sid_file.exists():
        data["session_id"] = sid_file.read_text(encoding="utf-8").strip()

    return data


def _ppt_panel_context(name: str, version: int | None = None) -> dict:
    """Build the template context for qc_ppt_panel.html."""
    analysis_dir = get_analysis_dir(name)
    rows = load_all_findings(analysis_dir) if analysis_dir.exists() else []
    flat = flatten_findings(rows) if rows else []
    counts = {
        "gap": sum(1 for f in flat if f.get("coverage") == "Gap"),
        "partial": sum(1 for f in flat if f.get("coverage") == "Partial"),
        "adequate": sum(1 for f in flat if f.get("coverage") == "Adequate"),
    }
    has_findings = (counts["gap"] + counts["partial"] + counts["adequate"]) > 0

    runs_dir = analysis_dir / "ppt" / "runs"
    versions = _list_ppt_versions(runs_dir)
    view = _load_ppt_version(runs_dir, version) if versions else None

    return {
        "name": name,
        "counts": counts,
        "has_findings": has_findings,
        "versions": versions,
        "view": view,
    }


def _parse_classifications(raw: str) -> list[str]:
    """Comma-separated 'Gap,Partial,Adequate' → list, dedup + drop unknowns."""
    valid = {"Gap", "Partial", "Adequate"}
    seen = set()
    out = []
    for token in (raw or "").split(","):
        t = token.strip()
        if t in valid and t not in seen:
            out.append(t)
            seen.add(t)
    return out


@app.get("/qc/{name}/ppt", response_class=HTMLResponse)
async def qc_ppt_panel(request: Request, name: str):
    """Render the PPT generation panel for a QC analysis."""
    return templates.TemplateResponse(
        request, "partials/qc_ppt_panel.html",
        _ppt_panel_context(name),
    )


@app.get("/qc/{name}/ppt/view/{version_num}", response_class=HTMLResponse)
async def qc_ppt_view_version(request: Request, name: str, version_num: int):
    """Render just the run-detail block for a specific PPT version (for nav)."""
    ctx = _ppt_panel_context(name, version=version_num)
    if not ctx.get("view"):
        return HTMLResponse("<p>Version not found.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "partials/qc_ppt_run_detail.html",
        {"name": name, "view": ctx["view"]},
    )


@app.post("/qc/{name}/ppt/generate", response_class=HTMLResponse)
async def qc_ppt_generate(
    request: Request,
    name: str,
    classifications: str = Form(""),
    instructions: str = Form(""),
):
    """Spawn a windowed Claude Code session that writes outline.json into a
    new versioned run dir. Returns the panel partial reflecting the new run."""
    analysis_dir = get_analysis_dir(name)
    if not analysis_dir.exists():
        return HTMLResponse("<p>Analysis not found.</p>", status_code=404)

    cls = _parse_classifications(classifications)
    if not cls:
        return HTMLResponse(
            "<p>Select at least one classification (Gap, Partial, Adequate).</p>",
            status_code=400,
        )

    rows = load_all_findings(analysis_dir)
    flat = flatten_findings(rows) if rows else []
    if not any(f.get("coverage") in cls for f in flat):
        return HTMLResponse(
            f"<p>No findings match the selected classifications "
            f"({', '.join(cls)}). Run Investigate first or pick a different mix.</p>",
            status_code=400,
        )

    try:
        result = await asyncio.to_thread(
            _ppt_generate, analysis_dir, cls, instructions,
        )
    except Exception as e:
        return HTMLResponse(f"<p>Error launching PPT generation: {e}</p>",
                             status_code=500)

    return templates.TemplateResponse(
        request, "partials/qc_ppt_panel.html",
        _ppt_panel_context(name, version=result["version_num"]),
    )


@app.post("/qc/{name}/ppt/resume/{version_num}", response_class=HTMLResponse)
async def qc_ppt_resume(request: Request, name: str, version_num: int):
    """Re-launch the windowed Claude Code session for an existing run."""
    analysis_dir = get_analysis_dir(name)
    if not analysis_dir.exists():
        return HTMLResponse("<p>Analysis not found.</p>", status_code=404)

    try:
        await asyncio.to_thread(_ppt_resume, analysis_dir, version_num)
    except FileNotFoundError as e:
        return HTMLResponse(f"<p>{e}</p>", status_code=404)
    except Exception as e:
        return HTMLResponse(f"<p>Error resuming session: {e}</p>",
                             status_code=500)

    return templates.TemplateResponse(
        request, "partials/qc_ppt_panel.html",
        _ppt_panel_context(name, version=version_num),
    )


@app.post("/qc/{name}/ppt/run-again", response_class=HTMLResponse)
async def qc_ppt_run_again(
    request: Request,
    name: str,
    version_num: int = Form(...),
):
    """Clone a prior run's inputs into a new versioned run + spawn fresh CC."""
    analysis_dir = get_analysis_dir(name)
    if not analysis_dir.exists():
        return HTMLResponse("<p>Analysis not found.</p>", status_code=404)

    try:
        result = await asyncio.to_thread(
            _ppt_run_again, analysis_dir, version_num,
        )
    except FileNotFoundError as e:
        return HTMLResponse(f"<p>{e}</p>", status_code=404)
    except Exception as e:
        return HTMLResponse(f"<p>Error cloning run: {e}</p>", status_code=500)

    return templates.TemplateResponse(
        request, "partials/qc_ppt_panel.html",
        _ppt_panel_context(name, version=result["version_num"]),
    )


@app.get("/qc/{name}/ppt/{version_num}/download")
async def qc_ppt_download(name: str, version_num: int):
    """Serve output.pptx for a specific PPT run version."""
    analysis_dir = get_analysis_dir(name)
    runs_dir = analysis_dir / "ppt" / "runs"
    if not runs_dir.exists():
        return HTMLResponse("<p>No PPT runs.</p>", status_code=404)

    target = None
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        try:
            if int(d.name.split("_", 1)[0]) == version_num:
                target = d
                break
        except (ValueError, IndexError):
            continue
    if target is None:
        return HTMLResponse("<p>Version not found.</p>", status_code=404)

    pptx_file = target / "output.pptx"
    if not pptx_file.exists():
        # Try a lazy build before giving up — covers a race where the user
        # clicks Download right after Claude Code finished outline.json.
        await asyncio.to_thread(_ppt_ensure_built, target)

    if not pptx_file.exists():
        return HTMLResponse("<p>output.pptx not yet built.</p>", status_code=404)

    return FileResponse(
        pptx_file,
        filename=f"{name}_v{version_num:03d}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@app.get("/qc/{name}/ppt/{version_num}/outline")
async def qc_ppt_outline(name: str, version_num: int):
    """Serve outline.json inline so the browser displays it as JSON."""
    analysis_dir = get_analysis_dir(name)
    runs_dir = analysis_dir / "ppt" / "runs"
    if not runs_dir.exists():
        return HTMLResponse("<p>No PPT runs.</p>", status_code=404)

    target = None
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        try:
            if int(d.name.split("_", 1)[0]) == version_num:
                target = d
                break
        except (ValueError, IndexError):
            continue
    if target is None:
        return HTMLResponse("<p>Version not found.</p>", status_code=404)

    outline_file = target / "outline.json"
    if not outline_file.exists():
        return HTMLResponse("<p>outline.json not yet written.</p>",
                             status_code=404)

    try:
        outline = json.loads(outline_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return FileResponse(outline_file, media_type="application/json")
    return JSONResponse(outline)


# ============================================================
# CONVERT
# ============================================================

CONVERT_DIR = PROJECT_ROOT / "output" / "convert"


@app.get("/convert", response_class=HTMLResponse)
async def convert_page(request: Request):
    """Render the Convert tab."""
    return templates.TemplateResponse(request, "convert.html", {})


@app.post("/convert/upload", response_class=HTMLResponse)
async def convert_upload(
    request: Request,
    file: UploadFile = File(...),
    change_mode: str = Form("accept"),
):
    """Upload a .docx, convert to markdown, return editable preview."""
    if not file.filename or not file.filename.lower().endswith(".docx"):
        return HTMLResponse("<p>Please upload a .docx file.</p>")

    CONVERT_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(file.filename).stem

    # Save uploaded file
    upload_path = CONVERT_DIR / f"{stem}.docx"
    content = await file.read()
    upload_path.write_bytes(content)

    # Detect tracked changes (before resolution)
    tc_info = has_tracked_changes(upload_path)

    # Convert
    image_dir = CONVERT_DIR / f"{stem}_images"
    blocks = await asyncio.to_thread(
        read_docx, upload_path, change_mode, str(image_dir),
    )
    md = to_markdown(blocks)

    image_count = sum(1 for b in blocks if b["type"] == "image_placeholder")

    return templates.TemplateResponse(
        request, "partials/convert_markdown.html",
        {
            "filename": file.filename,
            "stem": stem,
            "tracked_changes": tc_info,
            "change_mode": change_mode,
            "markdown": md,
            "image_count": image_count,
        },
    )


@app.post("/convert/format", response_class=HTMLResponse)
async def convert_format(
    request: Request,
    markdown: str = Form(...),
    stem: str = Form(...),
):
    """Format markdown into a styled .docx using the OLG template."""
    CONVERT_DIR.mkdir(parents=True, exist_ok=True)

    config = load_author_config()
    template_path = config.get(
        "author", "template_docx",
        fallback="programs/author/references/2026 OLG Template.docx",
    )
    template_file = PROJECT_ROOT / template_path

    output_path = CONVERT_DIR / f"{stem}_formatted.docx"
    await asyncio.to_thread(generate_docx, markdown, output_path, template_file)

    return templates.TemplateResponse(
        request, "partials/convert_result.html",
        {"stem": stem},
    )


@app.get("/convert/download/{stem}")
async def convert_download(stem: str):
    """Download the formatted .docx file."""
    docx_path = CONVERT_DIR / f"{stem}_formatted.docx"
    if not docx_path.exists():
        return HTMLResponse("<p>File not found.</p>", status_code=404)

    response = FileResponse(
        docx_path,
        filename=f"{stem}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------------------------------------
# QC HTML report — live render + downloadable self-contained file
# ------------------------------------------------------------

from programs.qc.html_report import (
    generate_html as _qc_html_generate,
    list_analysis_names as _qc_html_list_names,
    load_analyses as _qc_html_load_analyses,
)


def _parse_names_param(names: Optional[str]) -> Optional[list[str]]:
    if not names:
        return None
    parsed = [n.strip() for n in names.split(",") if n.strip()]
    return parsed or None


def _render_qc_report(names: Optional[str], selected: Optional[str]) -> tuple[str, int]:
    """Build the HTML report on a thread-pool worker. Returns (html, status)."""
    name_list = _parse_names_param(names)
    selected_list = [selected] if selected else None
    analyses = _qc_html_load_analyses(name_list)
    if not analyses:
        return ("<h1>No QC analyses available.</h1>"
                "<p>Upload and run an analysis under the QC tab first.</p>", 404)
    html = _qc_html_generate(analyses, selected=selected_list)
    return (html, 200)


@app.get("/qc/report", response_class=HTMLResponse)
async def qc_report(names: Optional[str] = None, selected: Optional[str] = None):
    """Live-render the QC HTML report.

    Query params:
        names     comma-separated analysis names; defaults to all
        selected  single analysis name to pre-apply as the scope filter
                  (loads all analyses but lands on a filtered view)
    """
    html, status = await asyncio.to_thread(_render_qc_report, names, selected)
    return HTMLResponse(html, status_code=status)


@app.get("/qc/report/download")
async def qc_report_download(names: Optional[str] = None, selected: Optional[str] = None):
    """Download the QC HTML report as a self-contained .html file.

    Filename includes the active scope when present (e.g.
    `qc_report_Oct-2025-QC-Report_20260511_1322.html`) so saved
    snapshots over time are distinguishable.
    """
    html, status = await asyncio.to_thread(_render_qc_report, names, selected)
    if status != 200:
        return HTMLResponse(html, status_code=status)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    scope = selected or (names.split(",")[0] if names else None)
    if scope:
        safe_scope = "".join(c if c.isalnum() or c in "-_." else "_"
                             for c in scope.strip())[:60]
        filename = f"qc_report_{safe_scope}_{ts}.html"
    else:
        filename = f"qc_report_{ts}.html"
    return HTMLResponse(
        html,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


# ============================================================
# SETTINGS — config.ini editor (UI-first replacement for hand-editing)
# ============================================================
#
# Scope grows incrementally — start with [qc_analyzer], add other
# sections as the surface stabilizes. [api] is intentionally excluded
# (plaintext keys do not belong in a browser-rendered DOM).
#
# Comments in config.ini are NOT preserved on save (Python configparser
# is line-based and drops them on write). Per-field help text in
# settings.html is the canonical reference for what each value does.

_QC_ENUM_FIELDS = {"judge_engine": ("api", "claude-code")}

_QC_INT_FIELDS = (
    "max_judge_searches",
    "investigate_parallel",
    "olg_results_per_search",
    "seed_results_per_query",
)

_QC_STR_FIELDS = (
    "judge_model",
    "extractor_model",
    "cmr_check_model",
    "fns_check_model",
    "cfr_check_model",
)

# Free-text fields where empty is meaningful (and not a validation error).
# judge_cc_model = "" means "let Claude Code use its own default model".
_QC_OPTIONAL_STR_FIELDS = (
    "judge_cc_model",
)

# [debug] section — hidden behind the testing-mode gate. Lay users never
# see these; the qc_analyzer only honors the temperature overrides when
# debug_mode is also true.
_DEBUG_BOOL_FIELDS = ("debug_mode",)
_DEBUG_OPTIONAL_FLOAT_FIELDS = (
    "extractor_temperature",
    "judge_api_temperature",
    "cross_check_temperature",
)


def _read_qc_settings() -> dict:
    """Return current [qc_analyzer] + [debug] values for form pre-fill."""
    config = load_qc_config()
    values = {}
    for k in _QC_ENUM_FIELDS:
        values[k] = config.get("qc_analyzer", k, fallback="")
    for k in _QC_INT_FIELDS + _QC_STR_FIELDS + _QC_OPTIONAL_STR_FIELDS:
        values[k] = config.get("qc_analyzer", k, fallback="")
    for k in _DEBUG_BOOL_FIELDS:
        values[k] = config.get("debug", k, fallback="false")
    for k in _DEBUG_OPTIONAL_FLOAT_FIELDS:
        values[k] = config.get("debug", k, fallback="")
    return values


_anthropic_models_cache: list[dict] | None = None
_anthropic_models_lock = threading.Lock()


def _get_anthropic_models() -> list[dict]:
    """Fetch the Anthropic model catalog for the settings datalist.

    Cached for the process lifetime — restart the UI to pick up new
    models. On failure (network, auth, rate limit) we cache an empty
    list so the field falls back to a plain text input rather than
    re-hitting the API on every page load.
    """
    global _anthropic_models_cache
    if _anthropic_models_cache is not None:
        return _anthropic_models_cache
    with _anthropic_models_lock:
        if _anthropic_models_cache is not None:
            return _anthropic_models_cache
        try:
            import anthropic
            config = load_qc_config()
            api_key = config.get("api", "anthropic_api_key")
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.models.list(limit=20)
            _anthropic_models_cache = [
                {"id": m.id, "display_name": m.display_name}
                for m in resp.data
            ]
        except Exception:
            _anthropic_models_cache = []
        return _anthropic_models_cache


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, saved: int = 0):
    """Render the settings page with current config.ini values pre-filled."""
    values = _read_qc_settings()
    models = await asyncio.to_thread(_get_anthropic_models)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "values": values,
            "errors": {},
            "saved": saved,
            "anthropic_models": models,
        },
    )


@app.post("/settings/save")
async def settings_save(request: Request):
    """Validate, write back to config.ini, redirect on success."""
    form = await request.form()
    submitted = {k: (form.get(k) or "").strip()
                 for k in (*_QC_ENUM_FIELDS, *_QC_INT_FIELDS,
                           *_QC_STR_FIELDS, *_QC_OPTIONAL_STR_FIELDS,
                           *_DEBUG_OPTIONAL_FLOAT_FIELDS)}
    # Checkbox: present in form => "true", absent => "false".
    for k in _DEBUG_BOOL_FIELDS:
        submitted[k] = "true" if form.get(k) else "false"

    errors: dict[str, str] = {}
    parsed_ints: dict[str, int] = {}
    parsed_floats: dict[str, str] = {}  # store as normalized strings

    for k, allowed in _QC_ENUM_FIELDS.items():
        if submitted[k] not in allowed:
            errors[k] = f"Must be one of: {', '.join(allowed)}."

    for k in _QC_INT_FIELDS:
        raw = submitted[k]
        try:
            v = int(raw)
        except ValueError:
            errors[k] = "Must be an integer."
            continue
        if v < 1:
            errors[k] = "Must be 1 or greater."
            continue
        parsed_ints[k] = v

    for k in _QC_STR_FIELDS:
        if not submitted[k]:
            errors[k] = "Required."

    # Optional floats: empty string = "no override" (don't write a value).
    # Anthropic accepts temperature in [0, 1]; reject anything outside.
    for k in _DEBUG_OPTIONAL_FLOAT_FIELDS:
        raw = submitted[k]
        if not raw:
            parsed_floats[k] = ""
            continue
        try:
            v = float(raw)
        except ValueError:
            errors[k] = "Must be a number (e.g. 0, 0.5, 1) or blank."
            continue
        if v < 0 or v > 1:
            errors[k] = "Must be between 0 and 1 (Anthropic API range)."
            continue
        parsed_floats[k] = str(v)

    if errors:
        models = await asyncio.to_thread(_get_anthropic_models)
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "values": submitted,
                "errors": errors,
                "saved": 0,
                "anthropic_models": models,
            },
        )

    config = load_qc_config()
    if not config.has_section("qc_analyzer"):
        config.add_section("qc_analyzer")
    for k in _QC_ENUM_FIELDS:
        config.set("qc_analyzer", k, submitted[k])
    for k, v in parsed_ints.items():
        config.set("qc_analyzer", k, str(v))
    for k in _QC_STR_FIELDS:
        config.set("qc_analyzer", k, submitted[k])
    for k in _QC_OPTIONAL_STR_FIELDS:
        config.set("qc_analyzer", k, submitted[k])

    if not config.has_section("debug"):
        config.add_section("debug")
    for k in _DEBUG_BOOL_FIELDS:
        config.set("debug", k, submitted[k])
    for k, v in parsed_floats.items():
        config.set("debug", k, v)

    with open(QC_CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

    return RedirectResponse(url="/settings?saved=1", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.app:app", host="127.0.0.1", port=8001, reload=True)
