"""
Policy Navigator — Web search interface.

FastAPI application serving HTMX-powered search UI for policy analysts.
Synthesis-first: questions get natural language answers with citations.
Run with: python ui/app.py
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import markdown

UI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = UI_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ui.search import SOURCES, DEFAULT_SOURCE, init_clients, do_search
from agents.synthesis import run_synthesis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize search clients on startup."""
    print("Initializing search clients...")
    init_clients()
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


@app.post("/ask", response_class=HTMLResponse)
async def ask(
    request: Request,
    question: str = Form(...),
    sources: Optional[list[str]] = Form(None),
    program: Optional[str] = Form(None),
    deep: bool = Form(False),
):
    """Synthesize an answer to a policy question."""
    question = question.strip()
    if not question:
        return HTMLResponse("")

    if not sources:
        sources = [DEFAULT_SOURCE]

    # Filter out empty program selection
    if program == "" or program == "all":
        program = None

    # Run synthesis in a thread to avoid blocking the event loop
    result = await asyncio.to_thread(
        run_synthesis,
        question=question,
        sources=sources,
        program=program,
        deep=deep,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.app:app", host="127.0.0.1", port=8001, reload=True)
