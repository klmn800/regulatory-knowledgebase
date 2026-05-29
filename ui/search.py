"""
Search service layer for the Policy Navigator web UI.

Wraps core/query.py with pre-initialized clients and a source registry.
Templates and routes should reference SOURCES, never hardcode source names.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rag.query import create_client, search_with_client


# Source registry — the single place to define available sources.
# Templates iterate over this. Adding a source = adding one dict entry.
SOURCES = {
    "olg": {
        "label": "the Online Guide",
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
    "cfr": {
        "label": "7 CFR (Federal SNAP Regulations)",
        "short_label": "CFR",
        "has_program_filter": True,
    },
}

DEFAULT_SOURCE = "olg"


# Per-source program registry: every label that exists in the live corpus
# plus which ones are checked by default at page load. Keep this in sync
# with the live `program` metadata distribution. Audit script:
#   chromadb get(include=["metadatas"]) → Counter(m["program"] for m in ...)
#
# Defaults locked 2026-05-01 with Ben — see todo_per_source_program_filter.md
PROGRAM_REGISTRY = {
    "olg": {
        "all": [
            "SNAP", "TAFDC", "EAEDC", "BP", "Cross-Program", "Self-Service",
            "Pathways", "COVID", "Harper", "Domestic Violence",
            "Policies & Procedures", "SUN Bucks", "Notices/Forms",
            "Scheduled Mailings", "General", "Forms", "microcontent",
        ],
        "default_checked": [
            "SNAP", "TAFDC", "EAEDC", "BP", "Cross-Program", "Self-Service",
        ],
    },
    "cmr": {
        "all": ["SNAP", "EA", "SSP", "Hearings", "Program Integrity"],
        "default_checked": ["SNAP", "EA", "SSP"],
    },
    "cfr": {
        "all": [
            "SNAP", "Issuance", "Administration", "QC",
            "Disaster", "Summer-EBT",
        ],
        "default_checked": ["SNAP"],
    },
    # FNS: no program metadata; UI omits checkboxes for it.
    "fns": {"all": [], "default_checked": []},
}


def get_default_programs(source: str) -> list[str]:
    """Return the default-checked program list for a source."""
    return list(PROGRAM_REGISTRY.get(source, {}).get("default_checked", []))


# Pre-initialized clients (populated by init_clients())
_clients = {}


def init_clients():
    """Initialize search clients for all registered sources."""
    for source_key in SOURCES:
        _clients[source_key] = create_client(source=source_key)


def do_search(
    query: str,
    source: str = DEFAULT_SOURCE,
    programs: list[str] | None = None,
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
        programs=programs,
        program=program,
        exclude_programs=exclude_programs,
        top_n=top_n,
        threshold=threshold,
    )
