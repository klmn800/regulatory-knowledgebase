"""
Search service layer for the Policy Navigator web UI.

Wraps core/query.py with pre-initialized clients and a source registry.
Templates and routes should reference SOURCES, never hardcode source names.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.query import create_client, search_with_client


# Source registry — the single place to define available sources.
# Templates iterate over this. Adding a source = adding one dict entry.
SOURCES = {
    "olg": {
        "label": "DTA Online Guide",
        "short_label": "OLG",
        "has_program_filter": True,
    },
    "cmr": {
        "label": "106 CMR",
        "short_label": "CMR",
        "has_program_filter": True,
    },
    "fns": {
        "label": "FNS Handbook 310",
        "short_label": "FNS",
        "has_program_filter": False,
    },
}

DEFAULT_SOURCE = "olg"

# Pre-initialized clients (populated by init_clients())
_clients = {}


def init_clients():
    """Initialize search clients for all registered sources."""
    for source_key in SOURCES:
        _clients[source_key] = create_client(source=source_key)


def do_search(
    query: str,
    source: str = DEFAULT_SOURCE,
    program: str | None = None,
    exclude_programs: list[str] | None = None,
    top_n: int = 5,
    threshold: float = 0.0,
) -> dict:
    """
    Search a source and return structured results.

    Returns the same dict as core/query.py's search_with_client().
    """
    if source not in _clients:
        raise ValueError(f"Unknown source: {source}")

    return search_with_client(
        query=query,
        clients=_clients[source],
        collection="sections",
        program=program,
        exclude_programs=exclude_programs,
        top_n=top_n,
        threshold=threshold,
    )
