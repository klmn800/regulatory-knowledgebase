"""
Search interface for the DTA Online Guide RAG pipeline.

Provides three ways to search the embedded policy knowledge base:

  1. CLI for humans   — python query.py "income deduction"
  2. Python API       — from query import search; search("income deduction")
  3. JSON output      — python query.py "income deduction" --json

Searches two ChromaDB collections:
  - sections  (~6,785 chunks) — default, for specific policy answers
  - pages     (~1,202 docs)   — for broad topic discovery

Features:
  - Program filtering (SNAP, TAFDC, EAEDC, etc.)
  - Similarity scores converted to intuitive 0-1 scale
  - Parent page context fetching for section results
  - Reusable client objects for agent integration (avoid re-init)
  - Source attribution with breadcrumb paths and URLs

Usage:
    # Basic search
    python query.py "income deduction"

    # Filter by program
    python query.py "expedited SNAP" --program SNAP

    # More results, full text
    python query.py "benefit calculation" --top 10 --full

    # Search page-level documents
    python query.py "eligibility rules" --collection pages

    # Include parent page context
    python query.py "income limits" --context

    # Machine-readable JSON output
    python query.py "work requirements" --json

    # List available programs
    python query.py --list-programs

Configuration:
    See config.ini for API key, model, and ChromaDB settings.
"""

import argparse
import configparser
import json
import sys
import textwrap
import time
from pathlib import Path

import chromadb
import voyageai


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.ini"

# TODO: This module currently only queries OLG collections (pages, sections).
# When FNS Phase 2 lands, it needs to become source-aware — e.g., a --source
# CLI flag to select which collections to search, or an orchestration layer
# that queries multiple sources and merges results.

# Display defaults
DEFAULT_TOP_N = 5
DEFAULT_COLLECTION = "sections"
DEFAULT_MAX_TEXT_LENGTH = 300  # chars, for CLI display truncation
DEFAULT_SIMILARITY_THRESHOLD = 0.0  # 0 = no filtering (show all)


def load_config() -> configparser.ConfigParser:
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")

    if not config.has_option("api", "voyage_api_key"):
        print(f"Error: No voyage_api_key found in {CONFIG_FILE}")
        print("Create config.ini with:")
        print("  [api]")
        print("  voyage_api_key = your_key_here")
        sys.exit(1)

    return config


# ============================================================
# QUERY EMBEDDING
# ============================================================

def embed_query(query_text: str, client: voyageai.Client,
                model: str) -> list[float]:
    """
    Embed a query string using Voyage AI.

    Retries on rate limit errors with exponential backoff (up to 3
    attempts). This is important for accounts without a payment method
    on the Voyage AI dashboard, which are limited to 3 RPM / 10K TPM.

    Note: We do NOT set input_type='query' because the document
    embeddings were created without input_type='document'. Mixing
    input_types would degrade retrieval quality. If the embedder
    is re-run with input_type in the future, update this to match.

    Args:
        query_text: The search query string.
        client: Initialized Voyage AI client.
        model: Embedding model name (e.g., 'voyage-3').

    Returns:
        Embedding vector as list of floats.

    Raises:
        voyageai.error.VoyageError: If the API call fails after retries.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = client.embed([query_text], model=model)
            return result.embeddings[0]
        except Exception as e:
            err_str = str(e)
            is_rate_limit = (
                "rate" in err_str.lower()
                or "429" in err_str
                or "limit" in err_str.lower()
            )
            if is_rate_limit and attempt < max_retries - 1:
                wait = 25 * (attempt + 1)
                print(f"Rate limited — waiting {wait}s before retry...",
                      flush=True)
                time.sleep(wait)
                continue
            raise


# ============================================================
# CHROMADB SEARCH
# ============================================================

def _build_where_filter(program: str | None = None) -> dict | None:
    """
    Build a ChromaDB where filter from query parameters.

    ChromaDB where syntax:
        {"program": "SNAP"}
        {"$and": [{"program": "SNAP"}, {"section_level": 2}]}

    Returns None if no filters are specified (ChromaDB treats
    None as "no filter").
    """
    conditions = []

    if program:
        conditions.append({"program": program})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def _l2_to_similarity(l2_distance: float) -> float:
    """
    Convert L2 (squared Euclidean) distance to a 0-1 similarity score.

    For unit-normalized vectors (Voyage AI embeddings are normalized):
        L2_distance = 2 * (1 - cosine_similarity)
        similarity = 1 - (L2_distance / 2)

    Returns a float between 0.0 (completely dissimilar) and
    1.0 (identical).
    """
    return max(0.0, 1.0 - (l2_distance / 2.0))


def query_collection(
    query_embedding: list[float],
    collection: chromadb.Collection,
    n_results: int = DEFAULT_TOP_N,
    where: dict | None = None,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[dict]:
    """
    Query a ChromaDB collection and return ranked results.

    Args:
        query_embedding: The query vector from Voyage AI.
        collection: ChromaDB collection to search.
        n_results: Maximum number of results to return.
        where: ChromaDB metadata filter dict (or None for no filter).
        similarity_threshold: Minimum similarity score (0-1). Results
            below this threshold are excluded. 0 means no filtering.

    Returns:
        List of result dicts, each containing:
            rank (int):     1-indexed position
            score (float):  Similarity score 0-1 (higher = better)
            text (str):     Full document text
            metadata (dict): All ChromaDB metadata fields
            id (str):       ChromaDB document ID
    """
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where is not None:
        kwargs["where"] = where

    raw = collection.query(**kwargs)

    # ChromaDB returns parallel lists indexed by [0] (first query)
    ids = raw["ids"][0]
    documents = raw["documents"][0]
    metadatas = raw["metadatas"][0]
    distances = raw["distances"][0]

    results = []
    for i, (doc_id, text, meta, dist) in enumerate(
        zip(ids, documents, metadatas, distances)
    ):
        score = _l2_to_similarity(dist)

        if similarity_threshold > 0 and score < similarity_threshold:
            continue

        results.append({
            "rank": len(results) + 1,
            "score": round(score, 4),
            "text": text,
            "metadata": meta,
            "id": doc_id,
        })

    return results


# ============================================================
# CONTEXT FETCHING
# ============================================================

def fetch_parent_page(
    parent_page_id: str,
    pages_collection: chromadb.Collection,
) -> dict | None:
    """
    Fetch the full parent page document for a section chunk.

    Uses the parent_page_id metadata field from a section result
    to look up the full page in the pages collection.

    Args:
        parent_page_id: The chunk_id of the parent page document.
        pages_collection: The ChromaDB pages collection.

    Returns:
        Dict with 'text' and 'metadata' keys, or None if the page
        is not found in the collection.
    """
    try:
        result = pages_collection.get(
            ids=[parent_page_id],
            include=["documents", "metadatas"],
        )
        if result["ids"]:
            return {
                "text": result["documents"][0],
                "metadata": result["metadatas"][0],
            }
    except Exception:
        pass

    return None


# ============================================================
# PYTHON API
# ============================================================

def create_client() -> dict:
    """
    Initialize Voyage AI and ChromaDB clients for repeated queries.

    Returns a dict with all the initialized objects needed by
    search_with_client(). Use this when making multiple queries
    to avoid re-initializing clients on every call.

    Example::

        clients = create_client()
        r1 = search_with_client("income deduction", clients)
        r2 = search_with_client("expedited benefits", clients)
    """
    config = load_config()

    api_key = config.get("api", "voyage_api_key")
    model = config.get("embedding", "model", fallback="voyage-3")
    persist_dir = config.get("chromadb", "persist_dir", fallback="data/chroma_db")
    page_coll_name = config.get("chromadb", "olg_page_collection", fallback="pages")
    section_coll_name = config.get("chromadb", "olg_section_collection",
                                   fallback="sections")

    persist_path = (PROJECT_ROOT / persist_dir).resolve()

    if not persist_path.exists():
        print(f"Error: ChromaDB directory not found at {persist_path}")
        print("Run embedder.py first to create the vector store.")
        sys.exit(1)

    vo = voyageai.Client(api_key=api_key)
    chroma = chromadb.PersistentClient(path=str(persist_path))

    return {
        "voyage_client": vo,
        "chroma_client": chroma,
        "model": model,
        "pages_collection": chroma.get_collection(page_coll_name),
        "sections_collection": chroma.get_collection(section_coll_name),
    }


def search_with_client(
    query: str,
    clients: dict,
    collection: str = DEFAULT_COLLECTION,
    program: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
) -> dict:
    """
    Search the knowledge base using pre-initialized clients.

    This is the core search function. Use create_client() to get
    the clients dict, then call this for each query.

    Args:
        query: Natural language search query.
        clients: Dict from create_client() with initialized clients.
        collection: Which collection to search ('sections' or 'pages').
        program: Filter by program (e.g., 'SNAP'). None = all programs.
        top_n: Maximum number of results to return.
        threshold: Minimum similarity score (0-1). 0 = no threshold.
        include_context: If True and searching sections, include the
            full parent page text for each result.

    Returns:
        Dict with keys:
            query (str):         The original query text
            collection (str):    Which collection was searched
            filters (dict):      Applied metadata filters
            result_count (int):  Number of results returned
            results (list):      List of result dicts, each containing:
                rank (int), score (float), text (str),
                metadata (dict), id (str), parent_page (dict|None)
    """
    # Resolve program filter (case-insensitive)
    resolved_program = None
    if program:
        resolved_program = _resolve_program_name(
            program, clients["sections_collection"]
        )

    # Choose collection
    if collection == "pages":
        coll = clients["pages_collection"]
    else:
        coll = clients["sections_collection"]

    # Embed the query
    query_embedding = embed_query(
        query, clients["voyage_client"], clients["model"]
    )

    # Build filter and search
    where = _build_where_filter(program=resolved_program)
    results = query_collection(
        query_embedding, coll,
        n_results=top_n, where=where,
        similarity_threshold=threshold,
    )

    # Optionally fetch parent page context for section results
    if include_context and collection == "sections":
        for result in results:
            parent_id = result["metadata"].get("parent_page_id")
            if parent_id:
                result["parent_page"] = fetch_parent_page(
                    parent_id, clients["pages_collection"]
                )
            else:
                result["parent_page"] = None
    else:
        for result in results:
            result["parent_page"] = None

    # Build filters dict for the response
    filters = {}
    if resolved_program:
        filters["program"] = resolved_program

    return {
        "query": query,
        "collection": collection,
        "filters": filters,
        "result_count": len(results),
        "results": results,
    }


def search(
    query: str,
    collection: str = DEFAULT_COLLECTION,
    program: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
) -> dict:
    """
    Search the DTA Online Guide knowledge base (convenience wrapper).

    Initializes clients internally — simple for one-off queries.
    For repeated queries, use create_client() + search_with_client()
    to avoid re-initialization overhead.

    Args:
        query: Natural language search query.
        collection: 'sections' (default) or 'pages'.
        program: Filter by program (e.g., 'SNAP'). None = all.
        top_n: Maximum number of results.
        threshold: Minimum similarity score (0-1).
        include_context: Include full parent page text for sections.

    Returns:
        Same dict structure as search_with_client().
    """
    clients = create_client()
    return search_with_client(
        query, clients,
        collection=collection,
        program=program,
        top_n=top_n,
        threshold=threshold,
        include_context=include_context,
    )


def _resolve_program_name(
    user_input: str,
    sections_collection: chromadb.Collection,
) -> str | None:
    """
    Resolve a user-provided program name to the canonical stored value.

    Does a case-insensitive match against all program values in the
    sections collection. Returns the correctly-cased program name,
    or prints a warning and returns None if no match is found.
    """
    # Get all unique programs from the collection
    all_meta = sections_collection.get(include=["metadatas"])
    programs = sorted(set(m["program"] for m in all_meta["metadatas"]))

    # Build a lookup map: uppercase → canonical
    lookup = {p.upper(): p for p in programs}

    canonical = lookup.get(user_input.upper())
    if canonical:
        return canonical

    # No exact match — suggest alternatives
    print(f"Warning: Program '{user_input}' not found.")
    print(f"Available programs: {', '.join(programs)}")
    print(f"Use --list-programs to see all options.")
    print()
    return None


# ============================================================
# CLI OUTPUT
# ============================================================

def format_result_text(
    response: dict,
    max_text_length: int = DEFAULT_MAX_TEXT_LENGTH,
    show_full: bool = False,
) -> str:
    """
    Format search results as human-readable text for the terminal.

    Args:
        response: The search response dict from search().
        max_text_length: Truncate text to this many characters
            (ignored if show_full is True).
        show_full: If True, show complete text without truncation.

    Returns:
        Formatted string ready to print.
    """
    lines = []
    query = response["query"]
    collection = response["collection"]
    count = response["result_count"]
    filters = response["filters"]

    # Header
    filter_str = ""
    if filters:
        parts = [f"{k}={v}" for k, v in filters.items()]
        filter_str = f"  (filtered: {', '.join(parts)})"

    lines.append(f'Found {count} results for "{query}" in {collection}{filter_str}')
    lines.append("")

    if count == 0:
        lines.append("No matching results. Try broader search terms or")
        lines.append("remove filters.")
        return "\n".join(lines)

    for result in response["results"]:
        meta = result["metadata"]
        score = result["score"]
        text = result["text"]

        # Build the breadcrumb display line
        breadcrumb = meta.get("breadcrumb", "")

        lines.append("=" * 60)

        # Header line: rank, score, breadcrumb
        lines.append(f"[{result['rank']}]  Score: {score:.2f}  |  {breadcrumb}")

        # Page title and section heading
        if collection == "sections":
            page_title = meta.get("page_title", "")
            section_heading = meta.get("section_heading", "")
            if page_title:
                lines.append(f"     Page:    {page_title}")
            if section_heading:
                lines.append(f"     Section: {section_heading}")
        else:
            title = meta.get("title", "")
            if title:
                lines.append(f"     Title:   {title}")

        # URL
        url = meta.get("url", "")
        if url:
            lines.append(f"     URL:     {url}")

        # Last updated
        last_updated = meta.get("last_updated", "")
        if last_updated:
            lines.append(f"     Updated: {last_updated}")

        lines.append("")

        # Text body (truncated or full)
        if show_full:
            display_text = text
        else:
            if len(text) > max_text_length:
                display_text = text[:max_text_length].rstrip() + "..."
            else:
                display_text = text

        # Indent the text for readability
        wrapped = textwrap.fill(display_text, width=70,
                                initial_indent="     ",
                                subsequent_indent="     ")
        lines.append(wrapped)

        # Parent page context (if available)
        parent = result.get("parent_page")
        if parent and parent.get("text"):
            lines.append("")
            lines.append("     --- Parent Page Context ---")
            parent_text = parent["text"]
            if not show_full and len(parent_text) > max_text_length:
                parent_text = parent_text[:max_text_length].rstrip() + "..."
            wrapped_parent = textwrap.fill(
                parent_text, width=70,
                initial_indent="     ",
                subsequent_indent="     ",
            )
            lines.append(wrapped_parent)

        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_result_json(response: dict) -> str:
    """
    Format the full search response as indented JSON.

    Suitable for piping to other tools or for programmatic
    consumption.
    """
    return json.dumps(response, indent=2, ensure_ascii=False)


# ============================================================
# MAIN
# ============================================================

def _print_programs() -> None:
    """List all unique program values in the sections collection."""
    config = load_config()
    persist_dir = config.get("chromadb", "persist_dir", fallback="data/chroma_db")
    persist_path = (PROJECT_ROOT / persist_dir).resolve()
    section_name = config.get("chromadb", "olg_section_collection",
                              fallback="sections")

    if not persist_path.exists():
        print(f"Error: ChromaDB directory not found at {persist_path}")
        print("Run embedder.py first to create the vector store.")
        sys.exit(1)

    chroma = chromadb.PersistentClient(path=str(persist_path))
    collection = chroma.get_collection(section_name)

    all_meta = collection.get(include=["metadatas"])
    programs = {}
    for meta in all_meta["metadatas"]:
        prog = meta["program"]
        programs[prog] = programs.get(prog, 0) + 1

    print("Available programs:")
    print()
    for prog, count in sorted(programs.items(), key=lambda x: -x[1]):
        print(f"  {prog:25s} ({count:,} chunks)")
    print()
    print(f"Total: {sum(programs.values()):,} chunks across "
          f"{len(programs)} programs")


def run_query(
    query: str,
    collection: str = DEFAULT_COLLECTION,
    program: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
    output_json: bool = False,
    show_full: bool = False,
) -> None:
    """
    Execute a query and print results to stdout.

    This is the orchestration function called by main(). It handles
    client initialization, search execution, and output formatting.
    """
    # Initialize clients once
    clients = create_client()

    # Run the search
    response = search_with_client(
        query, clients,
        collection=collection,
        program=program,
        top_n=top_n,
        threshold=threshold,
        include_context=include_context,
    )

    # Format and print
    if output_json:
        print(format_result_json(response))
    else:
        print(format_result_text(response, show_full=show_full))


# ============================================================
# CLI
# ============================================================

def main():
    """Parse command-line arguments and run the query."""
    parser = argparse.ArgumentParser(
        description="Search the DTA Online Policy Guide knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query.py "income deduction"                    # Basic search
  python query.py "expedited SNAP" --program SNAP       # Filter by program
  python query.py "benefit calculation" --top 10        # More results
  python query.py "eligibility rules" --collection pages  # Search pages
  python query.py "income limits" --context             # Include parent page
  python query.py "work requirements" --json            # JSON output
  python query.py "transfer cases" --full               # Full text
  python query.py --list-programs                       # Show programs
        """,
    )
    parser.add_argument(
        "query", nargs="?", default=None,
        help="Search query (natural language)",
    )
    parser.add_argument(
        "--collection", "-c", choices=["sections", "pages"],
        default=DEFAULT_COLLECTION,
        help=f"Which collection to search (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--program", "-p",
        help="Filter results by program (e.g., SNAP, TAFDC, EAEDC)",
    )
    parser.add_argument(
        "--top", "-n", type=int, default=DEFAULT_TOP_N,
        help=f"Number of results to return (default: {DEFAULT_TOP_N})",
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
        help="Minimum similarity score 0-1 (default: 0 = no threshold)",
    )
    parser.add_argument(
        "--context", action="store_true",
        help="Include full parent page text for section results",
    )
    parser.add_argument(
        "--json", dest="output_json", action="store_true",
        help="Output results as JSON (for programmatic consumption)",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Show full text without truncation",
    )
    parser.add_argument(
        "--list-programs", action="store_true",
        help="List all available programs and exit",
    )
    args = parser.parse_args()

    if args.list_programs:
        _print_programs()
        return

    if not args.query:
        parser.error("Search query is required (or use --list-programs)")

    run_query(
        query=args.query,
        collection=args.collection,
        program=args.program,
        top_n=args.top,
        threshold=args.threshold,
        include_context=args.context,
        output_json=args.output_json,
        show_full=args.full,
    )


if __name__ == "__main__":
    main()
