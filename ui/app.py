"""
Policy Navigator — Web search interface.

FastAPI application serving HTMX-powered search UI for policy analysts.
Synthesis-first: questions get natural language answers with citations.
Run with: python ui/app.py
"""

import asyncio
import subprocess
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

import shutil

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ui.search import SOURCES, DEFAULT_SOURCE, init_clients, do_search
from ui.history import init_db, save_search, get_recent, get_by_id
from ui.versioning import (
    save_research_version,
    save_draft_version,
    save_format_version,
    load_version_view,
    version_count,
)
from tools.synthesis import run_synthesis
from programs.author.author import (
    load_config as load_author_config,
    get_output_dir,
    run_research,
    compose_authoring_prompt,
    run_format,
    DATA_DIR,
)
from programs.qc.qc_analyzer import (
    load_config as load_qc_config,
    get_analysis_dir,
    load_csv as load_qc_csv,
    run_extract,
    run_investigate,
    run_cmr_check,
    run_fns_check,
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
templates.env.filters["markdown"] = lambda text: markdown.markdown(
    text, extensions=["tables", "fenced_code"]
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the search form page."""
    return templates.TemplateResponse(request, "index.html")


PROGRAM_FILTERS = {
    "all": {"program": None, "exclude_programs": None},
    "snap": {"program": None, "exclude_programs": ["TAFDC", "EAEDC"]},
    "tafdc": {"program": None, "exclude_programs": ["SNAP", "EAEDC"]},
    "eaedc": {"program": None, "exclude_programs": ["SNAP", "TAFDC"]},
    "snap_only": {"program": "SNAP", "exclude_programs": None},
    "tafdc_only": {"program": "TAFDC", "exclude_programs": None},
    "eaedc_only": {"program": "EAEDC", "exclude_programs": None},
}


@app.post("/ask", response_class=HTMLResponse)
async def ask(
    request: Request,
    question: str = Form(...),
    sources: Optional[list[str]] = Form(None),
    program_filter: str = Form("all"),
    deep: bool = Form(False),
):
    """Synthesize an answer to a policy question."""
    question = question.strip()
    if not question:
        return HTMLResponse("")

    if not sources:
        sources = [DEFAULT_SOURCE]

    pf = PROGRAM_FILTERS.get(program_filter, PROGRAM_FILTERS["all"])

    # Run synthesis in a thread to avoid blocking the event loop
    result = await asyncio.to_thread(
        run_synthesis,
        question=question,
        sources=sources,
        program=pf["program"],
        exclude_programs=pf["exclude_programs"],
        deep=deep,
    )

    # Save to history
    await asyncio.to_thread(
        save_search,
        question=question,
        sources=sources,
        program_filter=program_filter,
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
# RAW SEARCH (power users)
# ============================================================

@app.post("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    query: str = Form(...),
    source: str = Form(DEFAULT_SOURCE),
):
    """Raw search — returns result cards (kept for power users)."""
    query = query.strip()
    if not query:
        return HTMLResponse("")

    results = do_search(query=query, source=source)

    return templates.TemplateResponse(
        request,
        "partials/tab_content.html",
        {"results": results, "query": query, "source": source},
    )


# ============================================================
# AUTHOR
# ============================================================

@app.get("/author", response_class=HTMLResponse)
async def author_page(request: Request):
    """Render the authoring page."""
    return templates.TemplateResponse(request, "author.html")


@app.get("/author/assignments", response_class=HTMLResponse)
async def author_assignments(request: Request):
    """List existing assignments with their phase status."""
    assignments = []
    if DATA_DIR.exists():
        for d in sorted(DATA_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                assignments.append({
                    "name": d.name,
                    "has_research": (d / "research_report.md").exists(),
                    "has_draft": (d / "draft.md").exists(),
                    "has_docx": (d / "output.docx").exists(),
                    "has_session": (d / "session_id.txt").exists(),
                })
    return templates.TemplateResponse(
        request, "partials/assignments_list.html",
        {"assignments": assignments},
    )


@app.get("/author/load/{name}", response_class=HTMLResponse)
async def author_load(request: Request, name: str):
    """Load an existing assignment's details as JSON for the form."""
    output_dir = get_output_dir(name)
    assignment_file = output_dir / "assignment.txt"
    assignment = ""
    if assignment_file.exists():
        assignment = assignment_file.read_text(encoding="utf-8")
    return JSONResponse({
        "name": name,
        "assignment": assignment,
        "has_research": (output_dir / "research_report.md").exists(),
        "has_draft": (output_dir / "draft.md").exists(),
        "has_docx": (output_dir / "output.docx").exists(),
        "has_session": (output_dir / "session_id.txt").exists(),
        "research_versions": version_count(output_dir, "research"),
        "draft_versions": version_count(output_dir, "draft"),
        "format_versions": version_count(output_dir, "format"),
    })


@app.get("/author/view/{name}/{phase}", response_class=HTMLResponse)
async def author_view(
    request: Request, name: str, phase: str, v: Optional[int] = None,
):
    """Return a view of a specific (or latest) version for a phase."""
    if phase not in ("research", "draft", "format"):
        return HTMLResponse("<p>Invalid phase.</p>", status_code=400)

    output_dir = get_output_dir(name)
    view = load_version_view(output_dir, phase, version_num=v)

    if not view:
        return HTMLResponse("")

    template_map = {
        "research": "partials/author_view_research.html",
        "draft": "partials/author_view_draft.html",
        "format": "partials/author_view_format.html",
    }
    return templates.TemplateResponse(
        request, template_map[phase], {"view": view, "name": name}
    )


@app.post("/author/research", response_class=HTMLResponse)
async def author_research(
    request: Request,
    name: str = Form(...),
    assignment: str = Form(""),
    rerun: str = Form(""),
):
    """Run the research phase, or show existing output if not a rerun."""
    name = name.strip()
    assignment = assignment.strip()
    if not name:
        return HTMLResponse("<p>Assignment name is required.</p>")

    output_dir = get_output_dir(name)

    # View-before-run: if output exists and this isn't a rerun, show it
    if rerun != "1":
        view = load_version_view(output_dir, "research")
        if view:
            return templates.TemplateResponse(
                request, "partials/author_view_research.html",
                {"view": view, "name": name},
            )

    # Actually running — assignment required
    if not assignment:
        return HTMLResponse("<p>Enter an assignment description for research.</p>")

    config = load_author_config()

    result = await asyncio.to_thread(
        run_research, assignment, name, config,
    )

    # Save versioned copy
    save_research_version(output_dir, assignment, result)

    # Show the newly created version
    view = load_version_view(output_dir, "research")
    return templates.TemplateResponse(
        request, "partials/author_view_research.html",
        {"view": view, "name": name},
    )


@app.post("/author/draft", response_class=HTMLResponse)
async def author_draft(
    request: Request,
    name: str = Form(...),
    assignment: str = Form(""),
    rerun: str = Form(""),
):
    """Spawn a Claude Code terminal, or show existing draft if not a rerun."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Assignment name is required.</p>")

    output_dir = get_output_dir(name)

    # View-before-run: if draft exists and this isn't a rerun, show it
    if rerun != "1":
        view = load_version_view(output_dir, "draft")
        if view:
            return templates.TemplateResponse(
                request, "partials/author_view_draft.html",
                {"view": view, "name": name},
            )

    config = load_author_config()

    # Load assignment from form or saved file
    assignment = assignment.strip()
    if not assignment:
        saved = output_dir / "assignment.txt"
        if saved.exists():
            assignment = saved.read_text(encoding="utf-8").strip()
    if not assignment:
        return HTMLResponse("<p>No assignment text found. Enter one or run Research first.</p>")

    # Generate and save session ID upfront so Resume works later
    session_id = str(uuid.uuid4())
    session_file = output_dir / "session_id.txt"
    session_file.write_text(session_id, encoding="utf-8")

    # Create version directory — Claude writes directly here (authoritative copy)
    version_dir = save_draft_version(output_dir, assignment, session_id)
    versioned_draft = version_dir / "draft.md"
    toplevel_draft = output_dir / "draft.md"

    # Compose prompt pointing Claude at the versioned path
    prompt = compose_authoring_prompt(assignment, name, config,
                                      draft_file=versioned_draft)
    prompt_file = DATA_DIR / ".draft_prompt.md"
    prompt_file.write_text(prompt, encoding="utf-8")

    # Also save a copy in the assignment dir for reference
    (output_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    prompt_path = str(prompt_file.resolve())

    # Launch Claude Code in interactive mode with a pre-assigned session ID
    initial_msg = (
        f"Your full assignment is in {prompt_path} — it has the research findings, "
        f"style guide, and output instructions. Please read it and take it from there."
    )

    # .bat runs Claude, then copies versioned draft → top-level for phase handoff.
    # If the terminal closes before the copy, the versioned file is already safe.
    bat_file = DATA_DIR / ".run_draft.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {PROJECT_ROOT}\n'
        f'title Claude Code - {name}\n'
        f'echo.\n'
        f'echo  Authoring: {name}\n'
        f'echo  Draft output: {versioned_draft}\n'
        f'echo  Session ID: {session_id}\n'
        f'echo.\n'
        f'claude --session-id {session_id} "{initial_msg}"\n'
        f'echo.\n'
        f'if exist "{versioned_draft}" (\n'
        f'    copy "{versioned_draft}" "{toplevel_draft}"\n'
        f'    echo  Draft copied to top-level for phase handoff.\n'
        f')\n'
        f'echo.\n'
        f'echo  === Draft session complete ===\n'
        f'echo.\n'
        f'pause\n',
        encoding="utf-8",
    )

    # Spawn the terminal
    subprocess.Popen(
        ["cmd", "/c", str(bat_file)],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    msg = (
        f"## Claude Code Terminal Launched\n\n"
        f"A new terminal window has opened running the drafting session for **{name}**.\n\n"
        f"You'll see Claude Code's interactive UI — watch it think, search, and write.\n\n"
        f"When it finishes, the draft will be at:\n"
        f"`{versioned_draft}`\n\n"
        f"Then click **Format** to generate the .docx.\n\n"
        f"Session ID `{session_id}` saved — **Resume** will work for this session."
    )

    return templates.TemplateResponse(
        request, "partials/author_action_result.html",
        {"message": msg},
    )


@app.post("/author/format", response_class=HTMLResponse)
async def author_format(
    request: Request,
    name: str = Form(...),
    rerun: str = Form(""),
):
    """Run the format phase, or show existing .docx if not a rerun."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Assignment name is required.</p>")

    output_dir = get_output_dir(name)

    # View-before-run: only show cached .docx if no draft is newer than it.
    # Format is cheap and deterministic — always reformat if the draft changed.
    # Check both top-level draft and latest versioned draft (the authoritative
    # copy, which may be newer if the bat file's top-level copy didn't run).
    if rerun != "1":
        docx_file = output_dir / "output.docx"
        if docx_file.exists():
            docx_mtime = docx_file.stat().st_mtime
            draft_newer = False

            # Check top-level draft
            toplevel_draft = output_dir / "draft.md"
            if toplevel_draft.exists() and toplevel_draft.stat().st_mtime > docx_mtime:
                draft_newer = True

            # Check latest versioned draft (source of truth)
            if not draft_newer:
                from ui.versioning import latest_version
                latest = latest_version(output_dir, "draft")
                if latest:
                    vdraft = latest / "draft.md"
                    if vdraft.exists() and vdraft.stat().st_mtime > docx_mtime:
                        draft_newer = True

            if not draft_newer:
                view = load_version_view(output_dir, "format")
                if view:
                    return templates.TemplateResponse(
                        request, "partials/author_view_format.html",
                        {"view": view, "name": name},
                    )

    config = load_author_config()
    docx_path = await asyncio.to_thread(run_format, name, config)

    if docx_path and docx_path.exists():
        save_format_version(output_dir)
        view = load_version_view(output_dir, "format")
        return templates.TemplateResponse(
            request, "partials/author_view_format.html",
            {"view": view, "name": name},
        )
    else:
        msg = "## Format Failed\n\nCould not generate .docx. Check the server console for details."
        return templates.TemplateResponse(
            request, "partials/author_action_result.html",
            {"message": msg},
        )


@app.post("/author/resume", response_class=HTMLResponse)
async def author_resume(
    request: Request,
    name: str = Form(...),
    session_id: str = Form(""),
):
    """Resume a previous Claude Code session in a new terminal."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Assignment name is required.</p>")

    output_dir = get_output_dir(name)

    # Use provided session_id (from version view) or fall back to top-level file
    session_id = session_id.strip()
    if not session_id:
        session_file = output_dir / "session_id.txt"

        if not session_file.exists():
            return HTMLResponse(
                f"<p>No session ID found for <strong>{name}</strong>. "
                f"Run the Draft phase first.</p>"
            )

        session_id = session_file.read_text(encoding="utf-8").strip()

    # Spawn a resume terminal
    bat_file = output_dir / "run_resume.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {PROJECT_ROOT}\n'
        f'title Claude Code Resume - {name}\n'
        f'echo.\n'
        f'echo  Resuming session: {session_id}\n'
        f'echo.\n'
        f'claude --resume {session_id}\n'
        f'echo.\n'
        f'pause\n',
        encoding="utf-8",
    )

    subprocess.Popen(
        ["cmd", "/c", str(bat_file)],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    msg = (
        f"## Session Resumed\n\n"
        f"A terminal window has opened resuming session `{session_id}` for **{name}**.\n\n"
        f"You can interact with Claude Code directly in that window."
    )

    return templates.TemplateResponse(
        request, "partials/author_action_result.html",
        {"message": msg},
    )


@app.get("/author/download/{name}")
async def author_download(name: str):
    """Download the generated .docx file."""
    output_dir = get_output_dir(name)
    docx_file = output_dir / "output.docx"
    if not docx_file.exists():
        return HTMLResponse("<p>File not found.</p>", status_code=404)
    return FileResponse(
        docx_file,
        filename=f"{name}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


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
    for phase in ("fns_checked", "cmr_checked", "investigated", "extracted", "uploaded"):
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

    elif phase in ("investigate", "cmr_check", "fns_check"):
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


@app.post("/qc/cmr_check", response_class=HTMLResponse)
async def qc_cmr_check(
    request: Request,
    name: str = Form(...),
    rerun: str = Form(""),
):
    """Run CMR cross-check on Partial/Gap findings, or show existing results."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)

    # View-before-run: if CMR checks exist and not a rerun, show them
    if rerun != "1":
        meta = load_meta(analysis_dir) or {}
        if meta.get("phases", {}).get("cmr_checked"):
            all_findings = load_all_findings(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                {"findings": all_findings, "name": name, "meta": meta},
            )

    config = load_qc_config()
    await asyncio.to_thread(run_cmr_check, analysis_dir, None, config)

    all_findings = load_all_findings(analysis_dir)
    meta = load_meta(analysis_dir)
    return templates.TemplateResponse(
        request, "partials/qc_results_table.html",
        {"findings": all_findings, "name": name, "meta": meta},
    )


@app.post("/qc/fns_check", response_class=HTMLResponse)
async def qc_fns_check(
    request: Request,
    name: str = Form(...),
    rerun: str = Form(""),
):
    """Run FNS cross-check on Partial/Gap findings, or show existing results."""
    name = name.strip()
    if not name:
        return HTMLResponse("<p>Analysis name is required.</p>")

    analysis_dir = get_analysis_dir(name)

    # View-before-run: if FNS checks exist and not a rerun, show them
    if rerun != "1":
        meta = load_meta(analysis_dir) or {}
        if meta.get("phases", {}).get("fns_checked"):
            all_findings = load_all_findings(analysis_dir)
            return templates.TemplateResponse(
                request, "partials/qc_results_table.html",
                {"findings": all_findings, "name": name, "meta": meta},
            )

    config = load_qc_config()
    await asyncio.to_thread(run_fns_check, analysis_dir, None, config)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.app:app", host="127.0.0.1", port=8001, reload=True)
