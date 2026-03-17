"""
Search interface for the Policy Navigator RAG pipeline.

Provides three ways to search the embedded policy knowledge base:

  1. CLI for humans   — python query.py "income deduction"
  2. Python API       — from query import search; search("income deduction")
  3. JSON output      — python query.py "income deduction" --json

Supports multiple sources via the --source flag:
  - olg  — DTA Online Guide (pages + sections)
  - fns  — FNS Handbook 310 (chapters + sections)

Features:
  - Program filtering (SNAP, TAFDC, EAEDC, etc.) — OLG only
  - Similarity scores converted to intuitive 0-1 scale
  - Parent context fetching (parent page for OLG, parent chapter for FNS)
  - Reusable client objects for agent integration (avoid re-init)
  - Source attribution with breadcrumb paths and URLs

Usage:
    # OLG (default)
    python query.py "income deduction"
    python query.py "expedited SNAP" --program SNAP
    python query.py "benefit calculation" --top 10 --full
    python query.py "eligibility rules" --collection pages
    python query.py "income limits" --context
    python query.py "work requirements" --json
    python query.py --list-programs

    # FNS
    python query.py "income deduction" --source fns
    python query.py "income" --source fns --collection chapters
    python query.py "income" --source fns --context
    python query.py --source fns --list-programs

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


def _resolve_source_config(source: str) -> dict:
    """
    Return collection config keys, labels, and feature flags
    for a given source.
    """
    if source == "olg":
        return {
            "broad_collection_key": "olg_page_collection",
            "granular_collection_key": "olg_section_collection",
            "broad_name": "pages",
            "granular_name": "sections",
            "has_program_filter": True,
            "parent_id_field": "parent_page_id",
            "source_label": "DTA Online Guide",
        }
    elif source == "fns":
        return {
            "broad_collection_key": "fns_chapter_collection",
            "granular_collection_key": "fns_section_collection",
            "broad_name": "chapters",
            "granular_name": "sections",
            "has_program_filter": False,
            "parent_id_field": "parent_chapter_id",
            "source_label": "FNS Handbook 310",
        }
    else:
        print(f"Error: Unknown source '{source}'. Use 'olg' or 'fns'.")
        sys.exit(1)


# ============================================================
# QUERY EMBEDDING
# ============================================================

def embed_query(query_text: str, client: voyageai.Client,
                model: str) -> list[float]:
    """
    Embed a query string using Voyage AI.

    Note: We do NOT set input_type='query' because the document
    embeddings were created without input_type='document'. Mixing
    input_types would degrade retrieval quality.
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

    Returns None if no filters are specified.
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

    Returns list of result dicts with rank, score, text, metadata, id.
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

def fetch_parent_context(
    parent_id: str,
    broad_collection: chromadb.Collection,
) -> dict | None:
    """
    Fetch the full parent document (page or chapter) for a section chunk.

    Uses the parent_page_id or parent_chapter_id metadata field from
    a section result to look up the full document in the broad collection.
    """
    try:
        result = broad_collection.get(
            ids=[parent_id],
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

def create_client(source: str = "olg") -> dict:
    """
    Initialize Voyage AI and ChromaDB clients for repeated queries.

    Returns a dict with all the initialized objects needed by
    search_with_client(). Use this when making multiple queries
    to avoid re-initializing clients on every call.

    Example::

        clients = create_client(source="fns")
        r1 = search_with_client("income deduction", clients)
        r2 = search_with_client("expedited benefits", clients)
    """
    config = load_config()
    source_config = _resolve_source_config(source)

    api_key = config.get("api", "voyage_api_key")
    model = config.get("embedding", "model", fallback="voyage-3")
    persist_dir = config.get("chromadb", "persist_dir", fallback="data/chroma_db")
    broad_coll_name = config.get(
        "chromadb", source_config["broad_collection_key"],
        fallback=source_config["broad_name"])
    granular_coll_name = config.get(
        "chromadb", source_config["granular_collection_key"],
        fallback=source_config["granular_name"])

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
        "source": source,
        "source_config": source_config,
        "broad_collection": chroma.get_collection(broad_coll_name),
        "granular_collection": chroma.get_collection(granular_coll_name),
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
        collection: Which collection to search ('sections', 'pages',
                    or 'chapters').
        program: Filter by program (e.g., 'SNAP'). OLG only.
        top_n: Maximum number of results to return.
        threshold: Minimum similarity score (0-1). 0 = no threshold.
        include_context: If True and searching sections, include the
            full parent document text for each result.

    Returns:
        Dict with query, source, collection, filters, result_count, results.
    """
    source = clients["source"]
    source_config = clients["source_config"]

    # Resolve collection name to ChromaDB collection object
    broad_name = source_config["broad_name"]
    granular_name = source_config["granular_name"]

    if collection == broad_name:
        coll = clients["broad_collection"]
    elif collection == granular_name or collection == "sections":
        coll = clients["granular_collection"]
    else:
        print(f"Warning: Collection '{collection}' not valid for source "
              f"'{source}'. Using '{granular_name}'.")
        coll = clients["granular_collection"]
        collection = granular_name

    # Handle program filter
    resolved_program = None
    if program:
        if not source_config["has_program_filter"]:
            print(f"Note: Program filtering is not available for {source_config['source_label']} "
                  f"(all content is SNAP QC). Ignoring --program.")
        else:
            resolved_program = _resolve_program_name(
                program, clients["granular_collection"]
            )

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

    # Optionally fetch parent context for section results
    if include_context and collection in ("sections", granular_name):
        parent_id_field = source_config["parent_id_field"]
        for result in results:
            parent_id = result["metadata"].get(parent_id_field)
            if parent_id:
                result["parent_context"] = fetch_parent_context(
                    parent_id, clients["broad_collection"]
                )
            else:
                result["parent_context"] = None
    else:
        for result in results:
            result["parent_context"] = None

    # Build filters dict for the response
    filters = {}
    if resolved_program:
        filters["program"] = resolved_program

    return {
        "query": query,
        "source": source,
        "collection": collection,
        "filters": filters,
        "result_count": len(results),
        "results": results,
    }


def search(
    query: str,
    source: str = "olg",
    collection: str = DEFAULT_COLLECTION,
    program: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
) -> dict:
    """
    Search the policy knowledge base (convenience wrapper).

    Initializes clients internally — simple for one-off queries.
    For repeated queries, use create_client() + search_with_client()
    to avoid re-initialization overhead.
    """
    clients = create_client(source=source)
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
    sections collection.
    """
    # Get all unique programs from the collection
    all_meta = sections_collection.get(include=["metadatas"])
    programs = sorted(set(
        m["program"] for m in all_meta["metadatas"] if "program" in m
    ))

    # Build a lookup map: uppercase -> canonical
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
    Adapts display format based on the source (OLG vs FNS).
    """
    lines = []
    query = response["query"]
    source = response["source"]
    collection = response["collection"]
    count = response["result_count"]
    filters = response["filters"]

    # Header
    source_config = _resolve_source_config(source)
    filter_str = ""
    if filters:
        parts = [f"{k}={v}" for k, v in filters.items()]
        filter_str = f"  (filtered: {', '.join(parts)})"

    lines.append(f'Found {count} results for "{query}" in '
                 f'{source_config["source_label"]} {collection}{filter_str}')
    lines.append("")

    if count == 0:
        lines.append("No matching results. Try broader search terms or")
        lines.append("remove filters.")
        return "\n".join(lines)

    for result in response["results"]:
        meta = result["metadata"]
        score = result["score"]
        text = result["text"]

        lines.append("=" * 60)

        if source == "olg":
            _format_olg_result(lines, result, meta, score, collection)
        else:
            _format_fns_result(lines, result, meta, score, collection)

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

        # Parent context (if available)
        parent = result.get("parent_context")
        if parent and parent.get("text"):
            lines.append("")
            parent_label = "Parent Page" if source == "olg" else "Parent Chapter"
            lines.append(f"     --- {parent_label} Context ---")
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


def _format_olg_result(lines: list[str], result: dict, meta: dict,
                       score: float, collection: str) -> None:
    """Format a single OLG result's header lines."""
    breadcrumb = meta.get("breadcrumb", "")
    lines.append(f"[{result['rank']}]  Score: {score:.2f}  |  {breadcrumb}")

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

    url = meta.get("url", "")
    if url:
        lines.append(f"     URL:     {url}")

    last_updated = meta.get("last_updated", "")
    if last_updated:
        lines.append(f"     Updated: {last_updated}")


def _format_fns_result(lines: list[str], result: dict, meta: dict,
                       score: float, collection: str) -> None:
    """Format a single FNS result's header lines."""
    chapter = meta.get("chapter", "")
    chapter_title = meta.get("chapter_title", "")
    context = f"FNS 310 > Chapter {chapter}: {chapter_title}"
    lines.append(f"[{result['rank']}]  Score: {score:.2f}  |  {context}")

    if collection == "sections":
        sec_num = meta.get("section_number", "")
        sec_title = meta.get("section_title", "")
        if sec_num:
            lines.append(f"     Section: {sec_num} {sec_title}")

        handbook_pages = meta.get("handbook_pages", "")
        pdf_pages = meta.get("pdf_pages", "")
        if handbook_pages:
            page_str = f"     Pages:   {handbook_pages}"
            if pdf_pages:
                page_str += f" (PDF p.{pdf_pages})"
            lines.append(page_str)
    else:
        section_count = meta.get("section_count", "")
        if section_count:
            lines.append(f"     Sections: {section_count}")


def format_result_json(response: dict) -> str:
    """Format the full search response as indented JSON."""
    return json.dumps(response, indent=2, ensure_ascii=False)


# ============================================================
# MAIN
# ============================================================

def _print_info(source: str) -> None:
    """List source-specific info (programs for OLG, chapters for FNS)."""
    config = load_config()
    source_config = _resolve_source_config(source)
    persist_dir = config.get("chromadb", "persist_dir", fallback="data/chroma_db")
    persist_path = (PROJECT_ROOT / persist_dir).resolve()

    if not persist_path.exists():
        print(f"Error: ChromaDB directory not found at {persist_path}")
        print("Run embedder.py first to create the vector store.")
        sys.exit(1)

    chroma = chromadb.PersistentClient(path=str(persist_path))
    granular_coll_name = config.get(
        "chromadb", source_config["granular_collection_key"],
        fallback=source_config["granular_name"])
    collection = chroma.get_collection(granular_coll_name)
    all_meta = collection.get(include=["metadatas"])

    if source == "olg":
        # Show programs
        programs = {}
        for meta in all_meta["metadatas"]:
            prog = meta.get("program", "")
            programs[prog] = programs.get(prog, 0) + 1

        print("Available programs:")
        print()
        for prog, count in sorted(programs.items(), key=lambda x: -x[1]):
            print(f"  {prog:25s} ({count:,} chunks)")
        print()
        print(f"Total: {sum(programs.values()):,} chunks across "
              f"{len(programs)} programs")

    elif source == "fns":
        # Show chapters
        chapters = {}
        for meta in all_meta["metadatas"]:
            ch = meta.get("chapter", "")
            ch_title = meta.get("chapter_title", "")
            key = (ch, ch_title)
            chapters[key] = chapters.get(key, 0) + 1

        print(f"{source_config['source_label']} chapters:")
        print()
        for (ch, ch_title), count in sorted(chapters.items()):
            print(f"  Chapter {ch:>2}: {ch_title:50s} ({count} chunks)")
        print()
        print(f"Total: {sum(chapters.values()):,} chunks across "
              f"{len(chapters)} chapters")


def run_query(
    query: str,
    source: str = "olg",
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
    """
    # Initialize clients once
    clients = create_client(source=source)

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
        description="Search the Policy Navigator knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # OLG (default)
  python query.py "income deduction"                    # Basic search
  python query.py "expedited SNAP" --program SNAP       # Filter by program
  python query.py "benefit calculation" --top 10        # More results
  python query.py "eligibility rules" --collection pages  # Search pages
  python query.py "income limits" --context             # Include parent page
  python query.py "work requirements" --json            # JSON output
  python query.py --list-programs                       # Show programs

  # FNS
  python query.py "income deduction" --source fns       # Search FNS
  python query.py "income" --source fns --collection chapters
  python query.py "income" --source fns --context       # Parent chapter
  python query.py --source fns --list-programs          # Show chapters
        """,
    )
    parser.add_argument(
        "query", nargs="?", default=None,
        help="Search query (natural language)",
    )
    parser.add_argument(
        "--source", "-s", choices=["olg", "fns"], default="olg",
        help="Which source to search (default: olg)",
    )
    parser.add_argument(
        "--collection", "-c", choices=["sections", "pages", "chapters"],
        default=DEFAULT_COLLECTION,
        help=f"Which collection to search (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--program", "-p",
        help="Filter results by program (e.g., SNAP, TAFDC) — OLG only",
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
        help="Include full parent document text for section results",
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
        help="List available programs (OLG) or chapters (FNS) and exit",
    )
    args = parser.parse_args()

    # Validate --collection against --source
    source_config = _resolve_source_config(args.source)
    valid_collections = {source_config["broad_name"], source_config["granular_name"]}
    if args.collection not in valid_collections:
        print(f"Error: --collection {args.collection} is not valid for "
              f"--source {args.source}.")
        print(f"  Valid choices for {args.source}: "
              f"{', '.join(sorted(valid_collections))}")
        sys.exit(1)

    if args.list_programs:
        _print_info(args.source)
        return

    if not args.query:
        parser.error("Search query is required (or use --list-programs)")

    run_query(
        query=args.query,
        source=args.source,
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
