"""
Policy Navigator — Web search interface.

FastAPI application serving HTMX-powered search UI for policy analysts.
Synthesis-first: questions get natural language answers with citations.
Run with: python ui/app.py
"""

import asyncio
import json
import sys
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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
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
    get_analysis_dir,
    load_csv as load_qc_csv,
    run_extract,
    run_investigate,
    run_source_check,
    SOURCE_CHECK_CONFIG,
    load_all_findings,
    load_meta,
    save_meta,
    generate_summary_csv,
    ANALYSIS_DIR as QC_DIR,
)


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
    return templates.TemplateResponse(request, "qc.html")


@app.get("/qc/analyses", response_class=HTMLResponse)
async def qc_analyses(request: Request):
    """List existing analyses with their phase status."""
    analyses = []
    if QC_DIR.exists():
        for d in sorted(QC_DIR.iterdir()):
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
        findings = load_all_findings(analysis_dir)
        extracted = [f for f in findings if f.get("phase") in ("extracted", "investigated")]
        if not extracted:
            return HTMLResponse("<p>No extraction results found. Click Extract first.</p>")
        return templates.TemplateResponse(
            request, "partials/qc_triage_table.html",
            {"findings": extracted, "name": name, "meta": meta},
        )

    elif phase in ("investigate", "cmr_check", "fns_check", "cfr_check"):
        # All three post-investigation views use the same results table,
        # which conditionally shows CMR/FNS columns when data is present
        findings = load_all_findings(analysis_dir)
        if not findings:
            return HTMLResponse("<p>No results found.</p>")
        return templates.TemplateResponse(
            request, "partials/qc_results_table.html",
            {"findings": findings, "name": name, "meta": meta},
        )

    return HTMLResponse(f"<p>Unknown phase: {phase}</p>", status_code=400)


@app.post("/qc/upload", response_class=HTMLResponse)
async def qc_upload(
    request: Request,
    name: str = Form(""),
    file: UploadFile = File(...),
):
    """Upload a QC CSV and show a preview."""
    # Auto-populate name from filename if empty
    name = name.strip()
    if not name:
        name = Path(file.filename).stem

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
):
    """Run the Extractor phase, or show existing results."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)

    # View-before-run: if extraction results exist and not a rerun, show them
    if rerun != "1":
        findings = load_all_findings(analysis_dir)
        extracted = [f for f in findings if f.get("phase") in ("extracted", "investigated")]
        if extracted:
            meta = load_meta(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_triage_table.html",
                {"findings": extracted, "name": name, "meta": meta},
            )

    # Load CSV
    csv_path = analysis_dir / "upload.csv"
    if not csv_path.exists():
        return HTMLResponse("<p>No CSV uploaded. Upload a file first.</p>")

    _, rows = load_qc_csv(csv_path)

    config = load_qc_config()
    findings = await asyncio.to_thread(run_extract, analysis_dir, rows, config)

    meta = load_meta(analysis_dir)
    return templates.TemplateResponse(
        request, "partials/qc_triage_table.html",
        {"findings": findings, "name": name, "meta": meta},
    )


@app.post("/qc/investigate", response_class=HTMLResponse)
async def qc_investigate(
    request: Request,
    name: str = Form(...),
    row_indices: str = Form(""),
    rerun: str = Form(""),
):
    """Run the Judge on selected rows, or show existing results."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)

    # View-before-run: if investigated findings exist and not a rerun, show them
    if rerun != "1":
        findings = load_all_findings(analysis_dir)
        investigated = [f for f in findings if f.get("phase") == "investigated"]
        if investigated:
            meta = load_meta(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                {"findings": findings, "name": name, "meta": meta},
            )

    # Parse row indices from comma-separated string
    indices = None
    if row_indices.strip():
        indices = [int(x.strip()) for x in row_indices.split(",") if x.strip()]

    if not indices:
        # Default to all findings (extracted or already investigated)
        findings = load_all_findings(analysis_dir)
        indices = [f["row_index"] for f in findings
                   if f.get("phase") in ("extracted", "investigated")]

    if not indices:
        return HTMLResponse("<p>No rows selected for investigation.</p>")

    config = load_qc_config()
    results = await asyncio.to_thread(run_investigate, analysis_dir, indices, config)

    # Reload all findings for the results table
    all_findings = load_all_findings(analysis_dir)
    meta = load_meta(analysis_dir)
    return templates.TemplateResponse(
        request, "partials/qc_results_table.html",
        {"findings": all_findings, "name": name, "meta": meta},
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
            all_findings = load_all_findings(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                {"findings": all_findings, "name": name, "meta": meta},
            )

    config = load_qc_config()
    await asyncio.to_thread(run_source_check, source, analysis_dir, None, config)

    all_findings = load_all_findings(analysis_dir)
    meta = load_meta(analysis_dir)
    return templates.TemplateResponse(
        request, "partials/qc_results_table.html",
        {"findings": all_findings, "name": name, "meta": meta},
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.app:app", host="127.0.0.1", port=8001, reload=True)
