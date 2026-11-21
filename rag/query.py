"""
Search interface for the Regulatory Knowledgebase RAG pipeline.

Provides three ways to search the embedded policy knowledge base:

  1. CLI for humans   — python query.py "income deduction"
  2. Python API       — from query import search; search("income deduction")
  3. JSON output      — python query.py "income deduction" --json

Supports multiple sources via the --source flag:
  - olg  — the Online Guide (pages + sections)
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

    # Chunk ID lookup (retrieve specific chunk + neighbors)
    python query.py --source olg --chunk-id sec__SNAP__Eligibility__Stu_Students__035
    python query.py --source olg --chunk-id sec__SNAP__Eligibility__Stu_Students__035 --neighbors 1

    # Full OLG page by URL
    python query.py --source olg --url "https://example.gov/.../page.htm"

Configuration:
    See config.ini for API key, model, and ChromaDB settings.
"""

import argparse
import configparser
import json
import os
import sys
import textwrap
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError as ChromaNotFoundError
import voyageai
from voyageai.error import VoyageError


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.ini"

# Run as a script (`python rag/query.py`), only rag/ is on sys.path.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from rag.build_record import format_index_info_text, read_index_info  # noqa: E402
from rag.cli_errors import CONTRACT_VERSION, CliError, emit_error  # noqa: E402

# Display defaults
DEFAULT_TOP_N = 5
DEFAULT_COLLECTION = "sections"
DEFAULT_MAX_TEXT_LENGTH = 300  # chars, for CLI display truncation
DEFAULT_SIMILARITY_THRESHOLD = 0.0  # 0 = no filtering (show all)

# Hybrid retrieval defaults
RRF_K = 60                       # RRF constant; standard value
HYBRID_DENSE_CANDIDATES = 30     # top-N from dense before fusion
HYBRID_SPARSE_CANDIDATES = 30    # top-N from sparse before fusion
HYBRID_DENSE_WEIGHT = 1.0        # RRF weight for dense retriever
HYBRID_SPARSE_WEIGHT = 0.4       # RRF weight for sparse — dense is already
                                 # strong (vctx3 mode A), so equal weighting
                                 # regresses on natural-language queries.
                                 # Sparse needs to be a "rescue" channel for
                                 # adversarial cases, not equal voice.
VALID_RETRIEVAL_MODES = ("dense", "sparse", "hybrid")
DEFAULT_MODE = "dense"


class UnknownProgramError(ValueError):
    """A program name that matches no program in the collection."""


class SparseIndexMissingError(FileNotFoundError):
    """Sparse or hybrid search was asked for, but the source has no BM25 index."""

# Orchestrator-set OLG program whitelist (NOT user config). When this
# script is run as a subprocess from inside an agent loop (QC Claude Code
# judge, Author Claude Code research), the spawning orchestrator sets
# OLG_PROGRAMS so the agent's shell-out `python rag/query.py --source olg`
# can't broaden past the configured filter. Read once at import; the
# subprocess is short-lived, so env-var-at-import is the natural scope.
# Intersection semantics: agent --program / --exclude-programs / --programs
# can narrow within this whitelist, but anything outside is dropped.
_OLG_PROGRAMS_ENV = os.environ.get("OLG_PROGRAMS", "").strip()
OLG_PROGRAMS_WHITELIST: list[str] | None = (
    [p.strip() for p in _OLG_PROGRAMS_ENV.split(",") if p.strip()]
    if _OLG_PROGRAMS_ENV else None
)


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
            "source_label": "the Online Guide",
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
    elif source == "cmr":
        return {
            "broad_collection_key": "cmr_chapter_collection",
            "granular_collection_key": "cmr_section_collection",
            "broad_name": "chapters",
            "granular_name": "sections",
            "has_program_filter": True,
            "parent_id_field": "parent_chapter_id",
            "source_label": "106 CMR",
        }
    elif source == "cfr":
        return {
            "broad_collection_key": "cfr_part_collection",
            "granular_collection_key": "cfr_section_collection",
            "broad_name": "parts",
            "granular_name": "sections",
            "has_program_filter": True,
            "parent_id_field": "parent_part_id",
            "source_label": "7 CFR",
        }
    else:
        print(f"Error: Unknown source '{source}'. Use 'olg', 'fns', 'cmr', or 'cfr'.")
        sys.exit(1)


# ============================================================
# QUERY EMBEDDING
# ============================================================

def embed_query(query_text: str, client: voyageai.Client,
                model: str) -> list[float]:
    """
    Embed a query string using Voyage AI.

    For voyage-3 / voyage-4 family models: we do NOT set
    input_type='query' because the document embeddings were created
    without input_type='document'. Mixing input_types would degrade
    retrieval quality.

    For voyage-context-* models: we use contextualized_embed() with
    input_type='query' because those collections were embedded with
    input_type='document'. Symmetry is what matters.
    """
    is_context_model = model.startswith("voyage-context")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if is_context_model:
                result = client.contextualized_embed(
                    inputs=[[query_text]],
                    model=model,
                    input_type="query",
                    output_dimension=1024,
                )
                return result.results[0].embeddings[0]
            else:
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
                # stderr: stdout carries only the response (CLI contract).
                print(f"Rate limited — waiting {wait}s before retry...",
                      file=sys.stderr, flush=True)
                time.sleep(wait)
                continue
            raise


# ============================================================
# SPARSE / HYBRID RETRIEVAL
# ============================================================

def _load_sparse_index(clients: dict):
    """Load (and cache on the clients dict) the BM25 sparse index for the
    current source. Returns None if no index file exists.
    """
    cached = clients.get("_sparse_index")
    if cached is not None:
        return cached
    # Lazy import so dense-only paths don't pay rank_bm25 import cost.
    from rag.sparse_index import index_path_for, load_index
    path = index_path_for(PROJECT_ROOT, clients["source"])
    if not path.exists():
        clients["_sparse_index"] = False  # negative-cache
        return None
    idx = load_index(path)
    clients["_sparse_index"] = idx
    return idx


def _sparse_search(query: str, clients: dict, top_n: int) -> list[tuple[str, float]]:
    """Return up to top_n (chunk_id, bm25_score) pairs from the sparse index."""
    idx = _load_sparse_index(clients)
    if idx is None or idx is False:
        return []
    return idx.search(query, top_n=top_n)


def _rrf_fuse(
    dense_ranked: list[str],
    sparse_ranked: list[str],
    k: int = RRF_K,
    dense_weight: float = HYBRID_DENSE_WEIGHT,
    sparse_weight: float = HYBRID_SPARSE_WEIGHT,
) -> list[tuple[str, float]]:
    """Weighted Reciprocal Rank Fusion.

    rrf_score = w_d * 1/(k + dense_rank) + w_s * 1/(k + sparse_rank)

    Dense gets full weight (1.0); sparse is downweighted (default 0.4)
    because vctx3 dense is already strong on natural-language queries.
    Sparse contributes meaningfully on adversarial queries (acronyms,
    section numbers) where dense ranks the right chunk poorly — there,
    sparse's top hit becomes a "rescue" candidate that out-scores
    semantically-near-but-wrong dense chunks.
    """
    scores: dict[str, float] = {}
    for rank, cid in enumerate(dense_ranked):
        scores[cid] = scores.get(cid, 0.0) + dense_weight / (k + rank + 1)
    for rank, cid in enumerate(sparse_ranked):
        scores[cid] = scores.get(cid, 0.0) + sparse_weight / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _fetch_chunks_by_ids(
    chunk_ids: list[str],
    coll,
    where: dict | None = None,
) -> list[dict]:
    """Fetch chunk metadata + text for a list of chunk_ids, preserving input
    order. If `where` is provided, drop chunks that don't satisfy the filter.

    Returns dicts with the same shape as `query_collection` output:
      {"id", "rank", "score", "text", "metadata"}.
    `score` is None because there's no similarity to report — the caller can
    overwrite with bm25_score or rrf_score as appropriate.
    """
    if not chunk_ids:
        return []

    # ChromaDB get() returns by ID with no order guarantee; build a map.
    raw = coll.get(ids=chunk_ids, where=where)
    by_id: dict[str, dict] = {}
    for cid, doc, meta in zip(raw["ids"], raw["documents"], raw["metadatas"]):
        by_id[cid] = {"document": doc, "metadata": meta}

    out: list[dict] = []
    for cid in chunk_ids:
        if cid not in by_id:
            continue
        rec = by_id[cid]
        out.append({
            "rank": len(out) + 1,
            "score": None,
            "text": rec["document"],
            "metadata": rec["metadata"],
            "id": cid,
        })
    return out


# ============================================================
# CHROMADB SEARCH
# ============================================================

def _build_where_filter(
    programs: list[str] | None = None,
    program: str | None = None,
    exclude_programs: list[str] | None = None,
) -> dict | None:
    """
    Build a ChromaDB where filter from query parameters.

    Args:
        programs: Include only these programs (preferred — list-based,
            no hidden carve-outs).
        program: Single-program shorthand (legacy, CLI compat).
        exclude_programs: Exclude these programs (legacy, CLI compat).

    `programs` takes precedence over `program`/`exclude_programs` when
    both are set. Returns None if no filters are specified.
    """
    conditions = []

    if programs:
        if len(programs) == 1:
            conditions.append({"program": programs[0]})
        else:
            conditions.append({"program": {"$in": list(programs)}})
    elif program:
        conditions.append({"program": program})
    elif exclude_programs:
        conditions.append({"program": {"$nin": exclude_programs}})

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

def fetch_chunks_by_id(
    chunk_id: str,
    clients: dict,
    neighbors: int = 0,
) -> list[dict]:
    """
    Retrieve specific chunk(s) by ID from ChromaDB.

    Parses the numeric suffix from the chunk ID and optionally
    fetches neighboring chunks by incrementing/decrementing the index.

    Args:
        chunk_id: The exact chunk ID (e.g., 'sec__SNAP__Eligibility__Stu_Students__035').
        clients: Dict from create_client().
        neighbors: Number of chunks before and after to include (default 0).

    Returns:
        List of dicts with 'id', 'text', 'metadata' keys, ordered by chunk index.
        Missing IDs (e.g., before first or after last chunk) are silently skipped.
    """
    coll = clients["granular_collection"]

    # Parse the chunk ID: split off the numeric suffix after the last '__'
    sep = "__"
    parts = chunk_id.rsplit(sep, 1)
    if len(parts) != 2 or not parts[1].isdigit():
        # Can't parse — just try the exact ID
        ids_to_fetch = [chunk_id]
    else:
        base = parts[0]
        index = int(parts[1])
        width = len(parts[1])  # preserve zero-padding width
        ids_to_fetch = [
            f"{base}{sep}{str(i).zfill(width)}"
            for i in range(max(0, index - neighbors), index + neighbors + 1)
        ]

    result = coll.get(
        ids=ids_to_fetch,
        include=["documents", "metadatas"],
    )

    # Build result list, preserving order of ids_to_fetch
    found = {}
    for i, rid in enumerate(result["ids"]):
        found[rid] = {
            "id": rid,
            "text": result["documents"][i],
            "metadata": result["metadatas"][i],
        }

    # Return in index order, skipping any IDs not found
    return [found[rid] for rid in ids_to_fetch if rid in found]


def fetch_chunk_neighbors(
    chunk_id: str,
    clients: dict,
    n: int = 1,
    direction: str = "both",
) -> list[dict]:
    """Fetch chunks adjacent to chunk_id by parsing its numeric suffix.

    Chunk IDs follow a `{base}__{NNN}` convention where NNN counts the
    chunk's position within its parent document (OLG: within page; FNS /
    CMR / CFR: within section). Neighbors are fetched by incrementing /
    decrementing the suffix — chunks with the same `base` automatically
    stay in the same parent document, so this can't cross boundaries.

    Note: the `chunk_n` metadata field is NOT a substitute — it counts
    position within a *section* on OLG, not within a page, so filtering
    by it can return cross-section chunks. Suffix parsing is the
    authoritative ordering.

    Args:
        chunk_id: The exact chunk ID of the anchor chunk.
        clients: Dict from create_client().
        n: How many neighbors to fetch on each side (or per direction).
        direction: "prev" | "next" | "both". 'both' returns up to 2n
            chunks (anchor itself is excluded).

    Returns:
        List of dicts with 'id', 'text', 'metadata' sorted by suffix
        index. Does NOT include the anchor chunk. Missing IDs (e.g.
        beyond the first/last chunk) are silently skipped.
    """
    if direction not in ("prev", "next", "both"):
        raise ValueError(f"direction must be 'prev', 'next', or 'both', got {direction!r}")

    coll = clients["granular_collection"]
    sep = "__"
    parts = chunk_id.rsplit(sep, 1)
    if len(parts) != 2 or not parts[1].isdigit():
        return []
    base = parts[0]
    anchor_idx = int(parts[1])
    width = len(parts[1])

    if direction == "prev":
        wanted = list(range(max(0, anchor_idx - n), anchor_idx))
    elif direction == "next":
        wanted = list(range(anchor_idx + 1, anchor_idx + n + 1))
    else:
        wanted = list(range(max(0, anchor_idx - n), anchor_idx + n + 1))
        wanted = [i for i in wanted if i != anchor_idx]
    if not wanted:
        return []

    ids_to_fetch = [f"{base}{sep}{str(i).zfill(width)}" for i in wanted]
    result = coll.get(ids=ids_to_fetch, include=["documents", "metadatas"])
    rows = []
    for cid, doc, m in zip(result["ids"], result["documents"], result["metadatas"]):
        rows.append({"id": cid, "text": doc, "metadata": m})

    def _suffix_idx(row: dict) -> int:
        suffix = row["id"].rsplit(sep, 1)[1]
        return int(suffix) if suffix.isdigit() else 0

    rows.sort(key=_suffix_idx)
    return rows


def fetch_page_chunks(url: str, clients: dict) -> list[dict]:
    """Fetch all chunks belonging to a single OLG page (by URL).

    Returns chunks sorted by chunk_n for natural reading order. Each chunk
    is the same shape returned by fetch_chunk_neighbors.

    OLG-only — relies on the `url` metadata field. Other sources have no
    URL equivalent (they're PDFs); for those, fetch via parent_id_field.
    """
    if clients.get("source") != "olg":
        raise ValueError(
            f"fetch_page_chunks is OLG-only; got source={clients.get('source')!r}"
        )
    coll = clients["granular_collection"]
    result = coll.get(where={"url": url}, include=["documents", "metadatas"])
    rows = []
    for cid, doc, m in zip(result["ids"], result["documents"], result["metadatas"]):
        rows.append({"id": cid, "text": doc, "metadata": m})
    rows.sort(key=lambda r: r["metadata"].get("chunk_n", 0))
    return rows


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

def create_client(
    source: str = "olg",
    model_override: str | None = None,
    collection_suffix: str | None = None,
) -> dict:
    """
    Initialize Voyage AI and ChromaDB clients for repeated queries.

    Returns a dict with all the initialized objects needed by
    search_with_client(). Use this when making multiple queries
    to avoid re-initializing clients on every call.

    Args:
        source: Which source to search.
        model_override: If set, use this Voyage model instead of the
            one in config.ini. Must match the model the target
            collections were embedded with.
        collection_suffix: If set, append "_<suffix>" to the resolved
            collection names so this client targets side-by-side
            variant collections (e.g., "voyage4large") instead of
            production.

    Example::

        clients = create_client(source="fns")
        r1 = search_with_client("income deduction", clients)
        r2 = search_with_client("expedited benefits", clients)
    """
    config = load_config()
    source_config = _resolve_source_config(source)

    api_key = config.get("api", "voyage_api_key")
    model = model_override or config.get(
        "embedding", "model", fallback="voyage-4-large"
    )
    persist_dir = config.get("chromadb", "persist_dir", fallback="index/chroma_db")
    broad_coll_name = config.get(
        "chromadb", source_config["broad_collection_key"],
        fallback=source_config["broad_name"])
    granular_coll_name = config.get(
        "chromadb", source_config["granular_collection_key"],
        fallback=source_config["granular_name"])

    if collection_suffix:
        broad_coll_name = f"{broad_coll_name}_{collection_suffix}"
        granular_coll_name = f"{granular_coll_name}_{collection_suffix}"

    persist_path = (PROJECT_ROOT / persist_dir).resolve()

    if not persist_path.exists():
        print(f"Error: ChromaDB directory not found at {persist_path}")
        print("Run embedder.py first to create the vector store.")
        sys.exit(1)

    vo = voyageai.Client(api_key=api_key)
    chroma = chromadb.PersistentClient(
        path=str(persist_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # Granular is required (the workhorse collection); broad is
    # tolerated as missing for evaluation runs that only build the
    # granular tier.
    granular_collection = chroma.get_collection(granular_coll_name)
    try:
        broad_collection = chroma.get_collection(broad_coll_name)
    except Exception:
        broad_collection = None

    return {
        "voyage_client": vo,
        "chroma_client": chroma,
        "model": model,
        "source": source,
        "source_config": source_config,
        "broad_collection": broad_collection,
        "granular_collection": granular_collection,
    }


def search_with_client(
    query: str,
    clients: dict,
    collection: str = DEFAULT_COLLECTION,
    programs: list[str] | None = None,
    program: str | None = None,
    exclude_programs: list[str] | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
    mode: str = "dense",
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
        programs: Include only these programs (preferred). Empty list
                  or None means no filter.
        program: Single-program shorthand (legacy, CLI compat).
        exclude_programs: Exclude these programs (legacy, CLI compat).
                          Ignored if `programs` or `program` is set.
        top_n: Maximum number of results to return.
        threshold: Minimum similarity score (0-1). 0 = no threshold.
        include_context: If True and searching sections, include the
            full parent document text for each result.
        mode: Retrieval mode — "dense" (default), "sparse" (BM25 only) or
            "hybrid" (dense + BM25 fused via weighted RRF). Dense is the
            default because hybrid tested worse on the retrieval benchmark:
            top-1 relevance fell for OLG (62% → 46%) and CMR (65% → 57%)
            with no gain in useful-in-top-5. Use sparse or hybrid for
            literal tokens (form numbers, section numbers, acronyms).
            The sparse index covers the section tier only: a broad-tier
            search (pages / chapters / parts) silently runs dense, and the
            response's ``mode`` reports ``"dense"``. (The CLI rejects that
            combination instead.)

    Returns:
        Dict with query, source, collection, filters, mode (the mode that
        actually ran), result_count, results.

    Raises:
        SparseIndexMissingError: mode is sparse or hybrid on the section
            tier and ``index/sparse/{source}.pkl`` doesn't exist.
        UnknownProgramError: a program name matches no stored program.
    """
    source = clients["source"]
    source_config = clients["source_config"]

    if mode not in VALID_RETRIEVAL_MODES:
        raise ValueError(f"mode must be one of {VALID_RETRIEVAL_MODES}, got {mode!r}")

    # Resolve collection name to ChromaDB collection object
    broad_name = source_config["broad_name"]
    granular_name = source_config["granular_name"]

    if collection == broad_name:
        coll = clients["broad_collection"]
        is_granular = False
    elif collection == granular_name or collection == "sections":
        coll = clients["granular_collection"]
        is_granular = True
    else:
        print(f"Warning: Collection '{collection}' not valid for source "
              f"'{source}'. Using '{granular_name}'.")
        coll = clients["granular_collection"]
        collection = granular_name
        is_granular = True

    # Sparse index is granular-tier only. Downgrade quietly if needed.
    if not is_granular and mode != "dense":
        mode = "dense"

    # Fail loudly rather than return empty (sparse) or dense-only (hybrid)
    # results that look like a real answer.
    if mode != "dense" and not _load_sparse_index(clients):
        from rag.sparse_index import index_path_for
        raise SparseIndexMissingError(
            f"No sparse index for source {source!r} at "
            f"{index_path_for(PROJECT_ROOT, source)}; "
            f"{mode} search needs it."
        )

    # Handle program filter — sources without program metadata skip it entirely
    resolved_programs = None
    resolved_program = None
    resolved_excludes = None
    if source_config["has_program_filter"]:
        if programs:
            resolved_programs = [
                _resolve_program_name(p, clients["granular_collection"])
                for p in programs
            ]
        elif program:
            resolved_program = _resolve_program_name(
                program, clients["granular_collection"]
            )
        elif exclude_programs:
            resolved_excludes = [
                _resolve_program_name(p, clients["granular_collection"])
                for p in exclude_programs
            ]

    where = _build_where_filter(
        programs=resolved_programs,
        program=resolved_program,
        exclude_programs=resolved_excludes,
    )

    # Dispatch on mode
    if mode == "dense":
        query_embedding = embed_query(
            query, clients["voyage_client"], clients["model"]
        )
        results = query_collection(
            query_embedding, coll,
            n_results=top_n, where=where,
            similarity_threshold=threshold,
        )
    elif mode == "sparse":
        sparse_hits = _sparse_search(query, clients, top_n=HYBRID_SPARSE_CANDIDATES)
        if not sparse_hits:
            results = []
        else:
            ids_only = [cid for cid, _ in sparse_hits]
            fetched = _fetch_chunks_by_ids(ids_only, coll, where=where)
            score_map = dict(sparse_hits)
            for r in fetched:
                r["bm25_score"] = score_map.get(r["id"])
            results = fetched[:top_n]
    else:  # hybrid
        query_embedding = embed_query(
            query, clients["voyage_client"], clients["model"]
        )
        dense_results = query_collection(
            query_embedding, coll,
            n_results=HYBRID_DENSE_CANDIDATES, where=where,
            similarity_threshold=0.0,
        )
        dense_by_id = {r["id"]: r for r in dense_results}
        dense_ids = [r["id"] for r in dense_results]

        sparse_hits = _sparse_search(query, clients, top_n=HYBRID_SPARSE_CANDIDATES)
        sparse_score_map = dict(sparse_hits)
        sparse_ids = [cid for cid, _ in sparse_hits]

        fused = _rrf_fuse(dense_ids, sparse_ids)

        # Fetch metadata for sparse-only IDs (those not already in dense_results).
        # Over-fetch in case `where` filtering drops some.
        sparse_only_to_fetch = [
            cid for cid, _ in fused if cid not in dense_by_id
        ][: top_n * 3]
        sparse_only_fetched = _fetch_chunks_by_ids(
            sparse_only_to_fetch, coll, where=where
        )
        sparse_only_by_id = {r["id"]: r for r in sparse_only_fetched}

        results = []
        for cid, rrf_score in fused:
            if cid in dense_by_id:
                rec = dict(dense_by_id[cid])
                rec["rrf_score"] = rrf_score
                rec["bm25_score"] = sparse_score_map.get(cid)
                results.append(rec)
            elif cid in sparse_only_by_id:
                rec = dict(sparse_only_by_id[cid])
                rec["rrf_score"] = rrf_score
                rec["bm25_score"] = sparse_score_map.get(cid)
                results.append(rec)
            if len(results) >= top_n:
                break

        # Re-rank: rewrite ranks 1..N in the final hybrid order
        for i, r in enumerate(results, start=1):
            r["rank"] = i

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
    if resolved_programs:
        filters["programs"] = resolved_programs
    if resolved_program:
        filters["program"] = resolved_program
    if resolved_excludes:
        filters["exclude_programs"] = resolved_excludes

    return {
        "query": query,
        "source": source,
        "collection": collection,
        "filters": filters,
        "mode": mode,
        "result_count": len(results),
        "results": results,
    }


def search(
    query: str,
    source: str = "olg",
    collection: str = DEFAULT_COLLECTION,
    programs: list[str] | None = None,
    program: str | None = None,
    exclude_programs: list[str] | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
    mode: str = "dense",
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
        programs=programs,
        program=program,
        exclude_programs=exclude_programs,
        top_n=top_n,
        threshold=threshold,
        include_context=include_context,
        mode=mode,
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

    # No exact match — caller decides how to handle. Raise so the bug
    # surfaces instead of silently dropping the filter. (UnknownProgramError
    # is a ValueError, so existing `except ValueError` callers still work.)
    raise UnknownProgramError(
        f"Program {user_input!r} not found. "
        f"Available programs: {', '.join(programs)}"
    )


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
        elif source == "cmr":
            _format_cmr_result(lines, result, meta, score, collection)
        elif source == "cfr":
            _format_cfr_result(lines, result, meta, score, collection)
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
            if source == "olg":
                parent_label = "Parent Page"
            elif source == "cfr":
                parent_label = "Parent Part"
            else:
                parent_label = "Parent Chapter"
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
        parent_heading = meta.get("parent_heading", "")
        section_heading = meta.get("section_heading", "")
        if page_title:
            lines.append(f"     Page:    {page_title}")
        if parent_heading:
            lines.append(f"     Parent:  {parent_heading}")
        if section_heading:
            lines.append(f"     Section: {section_heading}")
        chunk_n = meta.get("chunk_n")
        chunk_total = meta.get("chunk_total")
        if chunk_total is not None and chunk_total > 1:
            lines.append(f"     Part:    {chunk_n} of {chunk_total}")
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

    lines.append(f"     Chunk:   {result['id']}")


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

    lines.append(f"     Chunk:   {result['id']}")


def _format_cmr_result(lines: list[str], result: dict, meta: dict,
                       score: float, collection: str) -> None:
    """Format a single CMR result's header lines."""
    chapter = meta.get("chapter", "")
    chapter_title = meta.get("chapter_title", "")
    program = meta.get("program", "")
    context = f"106 CMR {chapter} ({program})"
    lines.append(f"[{result['rank']}]  Score: {score:.2f}  |  {context}")

    if collection == "sections":
        sec_num = meta.get("section_number", "")
        sec_title = meta.get("section_title", "")
        if sec_num:
            lines.append(f"     Section: {sec_num} {sec_title}")
        if chapter_title:
            lines.append(f"     Chapter: {chapter_title[:60]}")
        hierarchy_path = meta.get("hierarchy_path", "")
        if hierarchy_path:
            lines.append(f"     Path:    {hierarchy_path}")
        chunk_n = meta.get("chunk_n")
        chunk_total = meta.get("chunk_total")
        if chunk_total is not None and chunk_total > 1:
            lines.append(f"     Part:    {chunk_n} of {chunk_total}")
    else:
        section_count = meta.get("section_count", "")
        if section_count:
            lines.append(f"     Sections: {section_count}")
        if chapter_title:
            lines.append(f"     Title:    {chapter_title[:60]}")

    lines.append(f"     Chunk:   {result['id']}")


def _format_cfr_result(lines: list[str], result: dict, meta: dict,
                       score: float, collection: str) -> None:
    """Format a single CFR result's header lines."""
    part = meta.get("part", "")
    part_title = meta.get("part_title", "")
    program = meta.get("program", "")
    context = f"7 CFR {part} ({program})"
    lines.append(f"[{result['rank']}]  Score: {score:.2f}  |  {context}")

    if collection == "sections":
        sec_num = meta.get("section_number", "")
        sec_title = meta.get("section_title", "")
        if sec_num:
            lines.append(f"     Section: § {sec_num} {sec_title}")
        if part_title:
            lines.append(f"     Part:    {part_title[:60]}")
        subpart_title = meta.get("subpart_title", "")
        if subpart_title:
            lines.append(f"     Subpart: {subpart_title[:60]}")
        hierarchy_path = meta.get("hierarchy_full_path") or meta.get("hierarchy_path", "")
        if hierarchy_path:
            lines.append(f"     Path:    {hierarchy_path}")
        chunk_n = meta.get("chunk_n")
        chunk_total = meta.get("chunk_total")
        if chunk_total is not None and chunk_total > 1:
            lines.append(f"     Chunk:   {chunk_n} of {chunk_total}")
    else:
        section_count = meta.get("section_count", "")
        if section_count:
            lines.append(f"     Sections: {section_count}")
        if part_title:
            lines.append(f"     Title:    {part_title[:60]}")

    lines.append(f"     Chunk:   {result['id']}")


def format_chunk_lookup_text(
    chunks: list[dict],
    target_id: str,
    source: str,
    show_full: bool = True,
    max_text_length: int = DEFAULT_MAX_TEXT_LENGTH,
) -> str:
    """Format chunk lookup results for the terminal."""
    lines = []
    lines.append(f"Chunk lookup: {target_id} (+{len(chunks) - 1} neighbors)"
                 if len(chunks) > 1
                 else f"Chunk lookup: {target_id}")
    lines.append(f"Found {len(chunks)} chunk(s)")
    lines.append("")

    if not chunks:
        lines.append("No chunks found with that ID.")
        return "\n".join(lines)

    for chunk in chunks:
        meta = chunk["metadata"]
        text = chunk["text"]
        is_target = chunk["id"] == target_id

        lines.append("=" * 60)

        marker = " <<< target" if is_target and len(chunks) > 1 else ""
        lines.append(f"Chunk: {chunk['id']}{marker}")

        page_title = meta.get("page_title", meta.get("chapter_title", ""))
        section = meta.get("section_heading", meta.get("section_title", ""))
        if page_title:
            lines.append(f"     Page:    {page_title}")
        if section:
            lines.append(f"     Section: {section}")

        url = meta.get("url", "")
        if url:
            lines.append(f"     URL:     {url}")

        lines.append("")

        if show_full:
            display_text = text
        else:
            if len(text) > max_text_length:
                display_text = text[:max_text_length].rstrip() + "..."
            else:
                display_text = text

        wrapped = textwrap.fill(display_text, width=70,
                                initial_indent="     ",
                                subsequent_indent="     ")
        lines.append(wrapped)
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def chunk_lookup_response(chunks: list[dict], target_id: str,
                          source: str) -> dict:
    """The chunk / URL lookup response as a dict (before the JSON envelope)."""
    return {
        "target_chunk_id": target_id,
        "source": source,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def format_chunk_lookup_json(chunks: list[dict], target_id: str,
                             source: str) -> str:
    """Format chunk lookup results as JSON."""
    return json.dumps(chunk_lookup_response(chunks, target_id, source),
                      indent=2, ensure_ascii=False)


def format_result_json(response: dict) -> str:
    """Format the full search response as indented JSON."""
    return json.dumps(response, indent=2, ensure_ascii=False)


def index_info(source: str) -> dict:
    """The ``index`` block (build record summary) for `source`. Never raises."""
    return read_index_info(source, index_root=PROJECT_ROOT / "index")


def with_envelope(response: dict, command: str, source: str) -> dict:
    """Add the contract 1.0 fields to a response.

    ``contract_version`` and ``command`` go first and ``index`` last; every
    existing field keeps its name and value.
    """
    out = {"contract_version": CONTRACT_VERSION, "command": command}
    out.update(response)
    out["index"] = index_info(source)
    return out


# ============================================================
# SOURCE INFO (--list-programs)
# ============================================================

INDEX_DATES_NOTE = (
    "  (Build dates say when this index was fetched and built. An OLG page's "
    "\"Updated\" date says when the agency last changed that page.)"
)


def collect_source_info(source: str, metadatas: list[dict]) -> dict:
    """Summarize a source's section-tier metadata for ``--list-programs``.

    Returns:
        ``programs``: ``[{program, chunk_count}]``, most chunks first;
        ``structure``: ``[{key, title, chunk_count}]`` for FNS / CMR chapters
        or CFR parts (CMR entries also carry ``program``), or ``None`` for
        OLG; ``total_chunks``.
    """
    programs: dict = {}
    for meta in metadatas:
        prog = meta.get("program", "")
        programs[prog] = programs.get(prog, 0) + 1
    program_rows = [
        {"program": prog, "chunk_count": count}
        for prog, count in sorted(programs.items(), key=lambda x: -x[1])
    ]

    structure = None
    if source in ("fns", "cmr", "cfr"):
        key_field, title_field = (
            ("part", "part_title") if source == "cfr" else ("chapter", "chapter_title")
        )
        groups: dict = {}
        for meta in metadatas:
            group = (meta.get(key_field, ""), meta.get(title_field, ""))
            if source == "cmr":
                group += (meta.get("program", ""),)
            groups[group] = groups.get(group, 0) + 1
        structure = []
        for group, count in sorted(groups.items()):
            row = {"key": group[0], "title": group[1], "chunk_count": count}
            if source == "cmr":
                row["program"] = group[2]
            structure.append(row)

    return {
        "source": source,
        "programs": program_rows,
        "structure": structure,
        "total_chunks": len(metadatas),
    }


def format_source_info_text(info: dict) -> str:
    """The ``--list-programs`` text, laid out as it always has been."""
    source = info["source"]
    label = _resolve_source_config(source)["source_label"]
    total = info["total_chunks"]
    lines: list[str] = []

    if source == "olg":
        lines += ["Available programs:", ""]
        for row in info["programs"]:
            lines.append(f"  {row['program']:25s} ({row['chunk_count']:,} chunks)")
        lines += ["", f"Total: {total:,} chunks across "
                      f"{len(info['programs'])} programs"]

    elif source == "fns":
        lines += [f"{label} chapters:", ""]
        for row in info["structure"]:
            lines.append(f"  Chapter {row['key']:>2}: {row['title']:50s} "
                         f"({row['chunk_count']} chunks)")
        lines += ["", f"Total: {total:,} chunks across "
                      f"{len(info['structure'])} chapters"]

    elif source == "cmr":
        lines += [f"{label} chapters:", ""]
        for row in info["structure"]:
            lines.append(f"  CMR {row['key']:>3}: {row['title'][:45]:45s} "
                         f"{row['program']:>12s}  ({row['chunk_count']} chunks)")
        lines += ["", f"Total: {total:,} chunks across "
                      f"{len(info['structure'])} chapters"]

    elif source == "cfr":
        lines += [f"{label} parts:", ""]
        for row in info["structure"]:
            lines.append(f"  Part {row['key']}: {row['title'][:50]:50s} "
                         f"({row['chunk_count']} chunks)")
        lines += ["", "Programs (section-level labels):", ""]
        for row in info["programs"]:
            lines.append(f"  {row['program']:20s} ({row['chunk_count']:,} chunks)")
        lines += ["", f"Total: {total:,} chunks across "
                      f"{len(info['structure'])} parts"]

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def run_query(
    query: str,
    source: str = "olg",
    collection: str = DEFAULT_COLLECTION,
    programs: list[str] | None = None,
    program: str | None = None,
    exclude_programs: list[str] | None = None,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    include_context: bool = False,
    output_json: bool = False,
    show_full: bool = False,
    mode: str = DEFAULT_MODE,
) -> None:
    """
    Execute a query and print results to stdout (JSON carries the envelope).
    """
    # Initialize clients once
    clients = create_client(source=source)

    # Run the search
    response = search_with_client(
        query, clients,
        collection=collection,
        programs=programs,
        program=program,
        exclude_programs=exclude_programs,
        top_n=top_n,
        threshold=threshold,
        include_context=include_context,
        mode=mode,
    )

    # Format and print
    if output_json:
        print(format_result_json(with_envelope(response, "search", source)))
    else:
        print(format_result_text(response, show_full=show_full))


# ============================================================
# CLI
# ============================================================

SOURCES = ("olg", "fns", "cmr", "cfr")
BROAD_COLLECTIONS = ("pages", "chapters", "parts")


class _CliArgumentParser(argparse.ArgumentParser):
    """ArgumentParser whose errors become `CliError("usage")` (exit 2)
    instead of argparse's own usage dump and exit code."""

    def error(self, message):  # noqa: D401 - argparse hook
        raise CliError("usage", message)


def _build_parser() -> argparse.ArgumentParser:
    """The query.py argument parser. Flags whose explicit use matters
    (--mode, --top, --threshold, --collection) default to None."""
    parser = _CliArgumentParser(
        prog="query.py",
        description="Search the Regulatory Knowledgebase knowledge base.",
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
  python query.py "SNAP-2 form" --mode hybrid           # Dense + BM25
  python query.py --list-programs                       # Show programs

  # FNS
  python query.py "income deduction" --source fns       # Search FNS
  python query.py "income" --source fns --collection chapters
  python query.py "income" --source fns --context       # Parent chapter
  python query.py --source fns --list-programs          # Show chapters

  # Chunk ID lookup
  python query.py --chunk-id sec__SNAP__Eligibility__Stu_Students__035
  python query.py --chunk-id sec__SNAP__Eligibility__Stu_Students__035 --neighbors 1

Exit codes: 0 ok (zero results is still 0), 2 usage, 3 index or config
unavailable, 4 Voyage API failure, 5 internal error. See docs/cli_contract.md.
        """,
    )
    parser.add_argument(
        "query", nargs="?", default=None,
        help="Search query (natural language)",
    )
    parser.add_argument(
        "--source", "-s", choices=list(SOURCES), default="olg",
        help="Which source to search (default: olg)",
    )
    parser.add_argument(
        "--collection", "-c", choices=["sections", *BROAD_COLLECTIONS],
        default=None,
        help=f"Which collection to search (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--mode", choices=list(VALID_RETRIEVAL_MODES), default=None,
        help=f"Retrieval mode (default: {DEFAULT_MODE}). dense = meaning; "
             "sparse = BM25 keywords; hybrid = both, fused. Dense ranks best on "
             "natural-language questions; sparse/hybrid help with literal tokens "
             "(form or section numbers). Sections only.",
    )
    parser.add_argument(
        "--programs",
        help="Include only these programs (comma-separated, e.g., SNAP,Hearings). "
             "Preferred over --program/--exclude-programs. Sources without program "
             "metadata (FNS) ignore this flag.",
    )
    parser.add_argument(
        "--program", "-p",
        help="Single-program shorthand (kept for compat — prefer --programs)",
    )
    parser.add_argument(
        "--exclude-programs",
        help="Exclude programs from results (comma-separated, e.g., TAFDC,EAEDC). "
             "Kept for compat — prefer --programs",
    )
    parser.add_argument(
        "--top", "-n", type=int, default=None,
        help=f"Number of results to return (default: {DEFAULT_TOP_N})",
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=None,
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
    parser.add_argument(
        "--chunk-id",
        help="Retrieve a specific chunk by ID (no search). "
             "E.g., sec__SNAP__Eligibility__Stu_Students__035",
    )
    parser.add_argument(
        "--neighbors", type=int, default=0,
        help="With --chunk-id, also return N chunks before and after (default: 0)",
    )
    parser.add_argument(
        "--url",
        help="Retrieve all chunks of an OLG page by URL (full-page fetch).",
    )
    return parser


# Lookup commands, in the order used to guess the command from raw argv.
_COMMAND_FLAGS = (
    ("--chunk-id", "chunk"),
    ("--url", "url"),
    ("--list-programs", "list"),
)


def _guess_context(argv: list[str]) -> tuple[str, str | None, bool]:
    """Best guess at (command, source, --json) from raw argv, for reporting
    an error that happens before (or while) the arguments parse."""
    as_json = "--json" in argv
    command = "search"
    for flag, name in _COMMAND_FLAGS:
        if any(a == flag or a.startswith(flag + "=") for a in argv):
            command = name
            break

    source: str | None = "olg"
    for i, arg in enumerate(argv):
        value = None
        if arg in ("--source", "-s"):
            value = argv[i + 1] if i + 1 < len(argv) else ""
        elif arg.startswith("--source="):
            value = arg.split("=", 1)[1]
        if value is not None:
            source = value if value in SOURCES else None
    return command, source, as_json


def _resolve_command(args: argparse.Namespace) -> str:
    """Pick the one command the arguments ask for, or raise a usage error.

    Also applies the checks that need no files: collection vs source,
    sparse/hybrid on a broad collection, and --url outside OLG.
    """
    given = []
    if args.query is not None:
        given.append(("search", "a search query"))
    if args.chunk_id:
        given.append(("chunk", "--chunk-id"))
    if args.url:
        given.append(("url", "--url"))
    if args.list_programs:
        given.append(("list", "--list-programs"))

    if not given:
        raise CliError("usage", "a search query is required "
                                "(or use --list-programs, --chunk-id or --url)")
    if len(given) > 1:
        raise CliError("usage", "use only one of a search query, --chunk-id, "
                                "--url or --list-programs (got "
                                + " and ".join(label for _, label in given) + ")")
    command = given[0][0]

    if command == "url" and args.source != "olg":
        raise CliError("usage", "--url is OLG-only (got --source "
                                f"{args.source})")

    if command == "search":
        if not args.query.strip():
            raise CliError("usage", "the search query is empty")
        source_config = _resolve_source_config(args.source)
        collection = args.collection or DEFAULT_COLLECTION
        valid = {source_config["broad_name"], source_config["granular_name"]}
        if collection not in valid:
            raise CliError("usage", f"--collection {collection} is not valid for "
                                    f"--source {args.source} (valid: "
                                    f"{', '.join(sorted(valid))})")
        mode = args.mode or DEFAULT_MODE
        if mode != "dense" and collection == source_config["broad_name"]:
            raise CliError("usage", f"--mode {mode} needs the section collection; "
                                    f"the sparse index doesn't cover "
                                    f"'{collection}'. Use --mode dense or drop "
                                    f"--collection.")
    return command


def _cli_config(require_api_key: bool) -> configparser.ConfigParser:
    """Read config.ini for the CLI, raising `unavailable` instead of exiting."""
    if not CONFIG_FILE.exists():
        raise CliError("unavailable", f"config file not found: {CONFIG_FILE}")
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    if require_api_key and not config.get("api", "voyage_api_key",
                                          fallback="").strip():
        raise CliError("unavailable",
                       f"no voyage_api_key in the [api] section of {CONFIG_FILE}")
    return config


def _open_chroma(config: configparser.ConfigParser):
    """Open the ChromaDB store, raising `unavailable` if its directory is missing."""
    persist_dir = config.get("chromadb", "persist_dir", fallback="index/chroma_db")
    persist_path = (PROJECT_ROOT / persist_dir).resolve()
    if not persist_path.exists():
        raise CliError("unavailable",
                       f"ChromaDB directory not found at {persist_path} "
                       "(run embedder.py first)")
    return chromadb.PersistentClient(
        path=str(persist_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_cli_collection(chroma, config: configparser.ConfigParser,
                        source: str, tier: str):
    """Fetch the source's broad or granular collection, or raise `unavailable`."""
    source_config = _resolve_source_config(source)
    key, fallback = (
        (source_config["broad_collection_key"], source_config["broad_name"])
        if tier == "broad" else
        (source_config["granular_collection_key"], source_config["granular_name"])
    )
    name = config.get("chromadb", key, fallback=fallback)
    try:
        return chroma.get_collection(name)
    except Exception as exc:
        raise CliError("unavailable",
                       f"ChromaDB collection '{name}' for source {source} is "
                       f"not available ({type(exc).__name__}: {exc})") from exc


def _preflight(args: argparse.Namespace, command: str,
               config: configparser.ConfigParser):
    """Check the index pieces the command needs before any client is created.

    Returns the open ChromaDB client.
    """
    chroma = _open_chroma(config)
    _get_cli_collection(chroma, config, args.source, "granular")

    if command == "search":
        source_config = _resolve_source_config(args.source)
        collection = args.collection or DEFAULT_COLLECTION
        if collection == source_config["broad_name"]:
            _get_cli_collection(chroma, config, args.source, "broad")
        mode = args.mode or DEFAULT_MODE
        if mode != "dense":
            from rag.sparse_index import index_path_for
            path = index_path_for(PROJECT_ROOT, args.source)
            if not path.exists():
                raise CliError("unavailable",
                               f"no sparse index for source {args.source} at "
                               f"{path}; --mode {mode} needs it")
    return chroma


def _classify_exception(exc: BaseException) -> CliError:
    """Map an exception raised during a run onto a contract error kind."""
    if isinstance(exc, CliError):
        return exc
    if isinstance(exc, UnknownProgramError):
        return CliError("usage", str(exc))
    if isinstance(exc, SparseIndexMissingError):
        return CliError("unavailable", str(exc))
    if (isinstance(exc, VoyageError)
            or type(exc).__module__.split(".")[0] == "voyageai"):
        return CliError("api", f"Voyage API call failed "
                               f"({type(exc).__name__}): {exc}")
    if isinstance(exc, ChromaNotFoundError):
        return CliError("unavailable", f"ChromaDB: {exc}")
    return CliError("internal", f"{type(exc).__name__}: {exc}")


def _print_json(payload: dict) -> None:
    """Write one JSON response to stdout."""
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _run_command(args: argparse.Namespace, command: str) -> None:
    """Run a parsed, validated command and print its response."""
    config = _cli_config(require_api_key=command != "list")
    chroma = _preflight(args, command, config)

    # --- URL → full page mode (OLG-only) ---
    if command == "url":
        clients = create_client(source="olg")
        chunks = fetch_page_chunks(args.url, clients)
        if args.output_json:
            _print_json(with_envelope(
                chunk_lookup_response(chunks, args.url, args.source),
                "url", args.source))
        else:
            print(format_chunk_lookup_text(
                chunks, args.url, args.source, show_full=True
            ))
        return

    # --- Chunk ID lookup mode ---
    if command == "chunk":
        clients = create_client(source=args.source)
        chunks = fetch_chunks_by_id(
            args.chunk_id, clients, neighbors=args.neighbors
        )
        if args.output_json:
            _print_json(with_envelope(
                chunk_lookup_response(chunks, args.chunk_id, args.source),
                "chunk", args.source))
        else:
            # Chunk lookups show full text by default (--full is implicit)
            print(format_chunk_lookup_text(
                chunks, args.chunk_id, args.source, show_full=True
            ))
        return

    # --- Info mode ---
    if command == "list":
        coll = _get_cli_collection(chroma, config, args.source, "granular")
        info = collect_source_info(
            args.source, coll.get(include=["metadatas"])["metadatas"])
        if args.output_json:
            _print_json(with_envelope(info, "list", args.source))
        else:
            print(format_source_info_text(info))
            print()
            print(format_index_info_text(index_info(args.source)))
            print(INDEX_DATES_NOTE)
        return

    # --- Search mode ---
    collection = args.collection or DEFAULT_COLLECTION
    mode = args.mode or DEFAULT_MODE
    top_n = args.top if args.top is not None else DEFAULT_TOP_N
    threshold = (args.threshold if args.threshold is not None
                 else DEFAULT_SIMILARITY_THRESHOLD)

    programs = None
    if args.programs:
        programs = [p.strip() for p in args.programs.split(",") if p.strip()]
    exclude = None
    if args.exclude_programs:
        exclude = [p.strip() for p in args.exclude_programs.split(",")]
    program = args.program

    # OLG_PROGRAMS guardrail (see module-level constant): intersect the
    # agent-passed filter with the orchestrator's whitelist so the
    # agent can narrow but never broaden.
    if OLG_PROGRAMS_WHITELIST is not None and args.source == "olg":
        whitelist = set(OLG_PROGRAMS_WHITELIST)
        if programs:
            programs = [p for p in programs if p in whitelist]
        elif program:
            programs = [program] if program in whitelist else []
            program = None
        else:
            base = whitelist - set(exclude or [])
            programs = sorted(base)
            exclude = None
        # Empty intersection ≠ "no filter at all". The agent asked for
        # something outside the whitelist — short-circuit to a zero-
        # results response (don't fall through to an unfiltered search).
        if not programs:
            empty = {
                "query": args.query,
                "source": "olg",
                "collection": collection,
                "filters": {"olg_programs_guardrail": "no_match"},
                "mode": mode,
                "result_count": 0,
                "results": [],
            }
            if args.output_json:
                _print_json(with_envelope(empty, "search", "olg"))
            else:
                print(
                    "No matching results — agent filter is outside the "
                    "OLG_PROGRAMS whitelist."
                )
            return

    run_query(
        query=args.query,
        source=args.source,
        collection=collection,
        programs=programs,
        program=program,
        exclude_programs=exclude,
        top_n=top_n,
        threshold=threshold,
        include_context=args.context,
        output_json=args.output_json,
        show_full=args.full,
        mode=mode,
    )


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the command, and return the process exit code.

    Every failure is reported through `emit_error` (one stderr line, plus the
    JSON error object with ``--json``) with the contract exit code.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    command, source, as_json = _guess_context(argv)
    try:
        args = _build_parser().parse_args(argv)
        source, as_json = args.source, args.output_json
        command = _resolve_command(args)
        _run_command(args, command)
        return 0
    except Exception as exc:
        err = _classify_exception(exc)
        return emit_error(err, command, source, as_json,
                          index_reader=index_info, exc=exc)


if __name__ == "__main__":
    sys.exit(main())
