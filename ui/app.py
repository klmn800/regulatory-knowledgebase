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
from pathlib import Path
from typing import Optional

import markdown

UI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = UI_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
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
    from fastapi.responses import JSONResponse
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
async def author_view(request: Request, name: str, phase: str):
    """Return a read-only view of the latest output for a phase."""
    if phase not in ("research", "draft", "format"):
        return HTMLResponse("<p>Invalid phase.</p>", status_code=400)

    output_dir = get_output_dir(name)
    view = load_version_view(output_dir, phase)

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

    # Compose the prompt and write to a space-free temp path
    prompt = compose_authoring_prompt(assignment, name, config)
    prompt_file = DATA_DIR / ".draft_prompt.md"
    prompt_file.write_text(prompt, encoding="utf-8")

    # Also save a copy in the assignment dir for reference
    (output_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    draft_file = output_dir / "draft.md"
    prompt_path = str(prompt_file.resolve())

    # Generate and save session ID upfront so Resume works later
    session_id = str(uuid.uuid4())
    session_file = output_dir / "session_id.txt"
    session_file.write_text(session_id, encoding="utf-8")

    # Create version directory for this draft run
    version_dir = save_draft_version(output_dir, assignment, session_id)

    # Launch Claude Code in interactive mode with a pre-assigned session ID
    initial_msg = (
        f"Your full assignment is in {prompt_path} — it has the research findings, "
        f"style guide, and output instructions. Please read it and take it from there."
    )

    # .bat copies draft.md into the version dir after Claude exits
    bat_file = DATA_DIR / ".run_draft.bat"
    bat_file.write_text(
        f'@echo off\n'
        f'cd /d {PROJECT_ROOT}\n'
        f'title Claude Code - {name}\n'
        f'echo.\n'
        f'echo  Authoring: {name}\n'
        f'echo  Draft output: {draft_file}\n'
        f'echo  Session ID: {session_id}\n'
        f'echo.\n'
        f'claude --session-id {session_id} "{initial_msg}"\n'
        f'echo.\n'
        f'if exist "{draft_file}" (\n'
        f'    copy "{draft_file}" "{version_dir}\\draft.md"\n'
        f'    echo  Draft copied to version directory.\n'
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
        f"`{draft_file}`\n\n"
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

    # View-before-run: if .docx exists and this isn't a rerun, show it
    if rerun != "1":
        view = load_version_view(output_dir, "format")
        if view:
            return templates.TemplateResponse(
                request, "partials/author_view_format.html",
                {"view": view, "name": name},
            )

    draft_file = output_dir / "draft.md"
    if not draft_file.exists():
        return HTMLResponse(
            f"<p>No draft found at <code>{draft_file}</code>. "
            f"Run the Draft phase first.</p>"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.app:app", host="127.0.0.1", port=8001, reload=True)
