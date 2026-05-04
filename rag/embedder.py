"""
Embedder for Policy Navigator RAG pipeline.

Reads chunked JSON files produced by source-specific chunkers, generates
embeddings via the Voyage AI API, and stores everything in ChromaDB
for retrieval.

Supports multiple sources via the --source flag:
  - olg  — DTA Online Guide (pages + sections)
  - fns  — FNS Handbook 310 (chapters + sections)

Features:
  - Batch embedding (sends up to 64 texts per API call)
  - Progress tracking — can resume if interrupted
  - Cost estimation before and after embedding
  - Metadata stored alongside embeddings for filtered retrieval

Usage:
    # OLG (default)
    python embedder.py --dry-run
    python embedder.py
    python embedder.py --only pages

    # FNS
    python embedder.py --source fns --dry-run
    python embedder.py --source fns
    python embedder.py --source fns --only chapters

    # Force re-embed from scratch
    python embedder.py --source fns --force

Configuration:
    See config.ini for API key, model name, and ChromaDB settings.
"""

import argparse
import configparser
import json
import sys
import time
from pathlib import Path

import chromadb
import voyageai


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.ini"

# Voyage AI pricing (per 1M tokens) as of May 2026
# See https://docs.voyageai.com/docs/pricing
VOYAGE_PRICING = {
    "voyage-4-large": 0.12,
    "voyage-4": 0.06,
    "voyage-4-lite": 0.02,
    "voyage-context-3": 0.18,
    "voyage-3-large": 0.18,
    "voyage-3.5": 0.06,
    "voyage-3.5-lite": 0.02,
    "voyage-3": 0.06,
    "voyage-3-lite": 0.02,
    "voyage-code-3": 0.18,
}


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


def _resolve_source_paths(source: str) -> dict:
    """
    Return chunk file paths, collection config keys, labels, and
    descriptions for a given source.
    """
    if source == "olg":
        return {
            "broad_chunks_file": PROJECT_ROOT / "index" / "olg" / "page_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "index" / "olg" / "section_chunks.json",
            "broad_collection_key": "olg_page_collection",
            "granular_collection_key": "olg_section_collection",
            "broad_label": "pages",
            "granular_label": "sections",
            "broad_description": "DTA Policy Online Guide - page-level documents",
            "granular_description": "DTA Policy Online Guide - section-level chunks",
        }
    elif source == "fns":
        return {
            "broad_chunks_file": PROJECT_ROOT / "index" / "fns" / "chapter_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "index" / "fns" / "section_chunks.json",
            "broad_collection_key": "fns_chapter_collection",
            "granular_collection_key": "fns_section_collection",
            "broad_label": "chapters",
            "granular_label": "sections",
            "broad_description": "FNS Handbook 310 - chapter-level documents",
            "granular_description": "FNS Handbook 310 - section-level chunks",
        }
    elif source == "cmr":
        return {
            "broad_chunks_file": PROJECT_ROOT / "index" / "cmr" / "chapter_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "index" / "cmr" / "section_chunks.json",
            "broad_collection_key": "cmr_chapter_collection",
            "granular_collection_key": "cmr_section_collection",
            "broad_label": "chapters",
            "granular_label": "sections",
            "broad_description": "106 CMR - chapter-level documents",
            "granular_description": "106 CMR - section-level chunks",
        }
    elif source == "cfr":
        return {
            "broad_chunks_file": PROJECT_ROOT / "index" / "cfr" / "part_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "index" / "cfr" / "section_chunks_context.json",
            "broad_collection_key": "cfr_part_collection",
            "granular_collection_key": "cfr_section_collection",
            "broad_label": "parts",
            "granular_label": "sections",
            "broad_description": "7 CFR SNAP regulations - part-level documents",
            "granular_description": "7 CFR SNAP regulations - section-level chunks",
        }
    else:
        print(f"Error: Unknown source '{source}'. Use 'olg', 'fns', 'cmr', or 'cfr'.")
        sys.exit(1)


# ============================================================
# CHUNK LOADING
# ============================================================

def load_chunks(filepath: Path) -> list[dict]:
    """Load chunks from a JSON file."""
    if not filepath.exists():
        print(f"Error: {filepath} not found. Run the chunker first.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {filepath.name}")
    return chunks


# ============================================================
# COST ESTIMATION
# ============================================================

def estimate_tokens(texts: list[str]) -> int:
    """
    Rough token estimate: ~4 characters per token for English text.
    This is a conservative estimate — actual usage may be lower.
    """
    total_chars = sum(len(t) for t in texts)
    return total_chars // 4


def estimate_cost(texts: list[str], model: str) -> tuple[int, float]:
    """
    Estimate the embedding cost for a set of texts.

    Returns (estimated_tokens, estimated_cost_usd).
    """
    tokens = estimate_tokens(texts)
    price_per_million = VOYAGE_PRICING.get(model, 0.06)
    cost = (tokens / 1_000_000) * price_per_million
    return tokens, cost


# ============================================================
# EMBEDDING
# ============================================================

def _build_token_aware_batches(chunks: list[dict], max_tokens_per_batch: int,
                                max_items_per_batch: int) -> list[list[dict]]:
    """
    Group chunks into batches that stay under the token limit.

    Uses the ~4 chars per token heuristic to estimate tokens per chunk,
    then greedily fills batches up to the limit.
    """
    batches = []
    current_batch = []
    current_tokens = 0

    for chunk in chunks:
        chunk_tokens = len(chunk["text"]) // 4
        # If this single chunk exceeds the limit, it gets its own batch
        if chunk_tokens >= max_tokens_per_batch:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            batches.append([chunk])
            continue

        if (current_tokens + chunk_tokens > max_tokens_per_batch or
                len(current_batch) >= max_items_per_batch):
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(chunk)
        current_tokens += chunk_tokens

    if current_batch:
        batches.append(current_batch)

    return batches


# Parent metadata field names by source — used to group chunks per
# parent document for voyage-context-3's contextualized embedding API.
_PARENT_FIELDS = ("parent_chapter_id", "parent_page_id", "parent_part_id")


def _group_chunks_by_parent(chunks: list[dict]) -> list[list[dict]]:
    """
    Group chunks by parent document, preserving file order.

    For granular-tier chunks (sections), groups by parent_chapter_id /
    parent_page_id / parent_part_id. For broad-tier chunks (chapters,
    pages, parts) which have no parent, each chunk becomes its own
    single-element doc.

    Returns a list of doc lists, where each doc list contains the
    chunks of one parent in their original order.
    """
    docs: dict[str, list[dict]] = {}
    standalone: list[list[dict]] = []

    for chunk in chunks:
        meta = chunk.get("metadata", {})
        parent_id = None
        for field in _PARENT_FIELDS:
            val = meta.get(field)
            if val:
                parent_id = val
                break

        if parent_id is None:
            # Broad-tier chunk with no parent — treat as its own doc
            standalone.append([chunk])
        else:
            docs.setdefault(parent_id, []).append(chunk)

    # Preserve insertion order: docs first (in encounter order), then
    # any standalone chunks
    return list(docs.values()) + standalone


def _split_oversize_doc(
    doc: list[dict], max_doc_tokens: int
) -> list[list[dict]]:
    """
    Split a doc whose chunks together exceed max_doc_tokens into
    smaller sub-docs of <=max_doc_tokens each.

    voyage-context-3 has a 32K-token context window per inner list.
    When a chapter's sections exceed that, we chunk the doc list.
    Cross-boundary context is lost between the splits, but within
    each sub-doc the chunks still get neighbor awareness.
    """
    sub_docs: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0

    for c in doc:
        c_tokens = len(c["text"]) // 4
        # A single chunk over the cap can't be embedded at all by
        # voyage-context-3. Skip it with a warning — the caller will
        # see the count drop.
        if c_tokens > max_doc_tokens:
            print(f"\n  WARN: chunk {c['chunk_id']} alone exceeds "
                  f"{max_doc_tokens} tokens — skipping (voyage-context-3 "
                  f"can't handle it)")
            continue

        if current_tokens + c_tokens > max_doc_tokens and current:
            sub_docs.append(current)
            current = []
            current_tokens = 0

        current.append(c)
        current_tokens += c_tokens

    if current:
        sub_docs.append(current)

    return sub_docs


def _build_contextualized_batches(
    chunks: list[dict],
    max_tokens_per_request: int = 100_000,
    max_chunks_per_request: int = 15_000,
    max_inputs_per_request: int = 1_000,
    max_tokens_per_doc: int = 28_000,
) -> list[list[list[dict]]]:
    """
    Build batches for the voyage-context-3 contextualized_embed API.

    Each batch is a list of docs; each doc is a list of chunks.
    Respects per-request and per-doc limits documented at:
    https://docs.voyageai.com/reference/contextualized-embeddings-api
        - 1,000 inputs (docs) per request
        - 16K chunks per request
        - 120K tokens per request
        - 32K tokens per doc (model context window)

    Docs exceeding max_tokens_per_doc are split into sub-docs.
    Defaults leave headroom under the documented caps.
    """
    raw_docs = _group_chunks_by_parent(chunks)

    # Pre-split any docs that exceed the per-doc context window
    docs: list[list[dict]] = []
    for doc in raw_docs:
        doc_tokens = sum(len(c["text"]) // 4 for c in doc)
        if doc_tokens > max_tokens_per_doc:
            split = _split_oversize_doc(doc, max_tokens_per_doc)
            print(f"  Split oversize doc ({doc_tokens:,} tokens) into "
                  f"{len(split)} sub-docs")
            docs.extend(split)
        else:
            docs.append(doc)

    batches: list[list[list[dict]]] = []
    current: list[list[dict]] = []
    current_tokens = 0
    current_chunks = 0

    for doc in docs:
        doc_tokens = sum(len(c["text"]) // 4 for c in doc)
        doc_chunks = len(doc)

        # Roll over to a new batch if adding this doc would exceed any
        # cap.
        if (current_tokens + doc_tokens > max_tokens_per_request
                or current_chunks + doc_chunks > max_chunks_per_request
                or len(current) >= max_inputs_per_request):
            if current:
                batches.append(current)
                current = []
                current_tokens = 0
                current_chunks = 0

        current.append(doc)
        current_tokens += doc_tokens
        current_chunks += doc_chunks

    if current:
        batches.append(current)

    return batches


def _is_contextualized_model(model: str) -> bool:
    """Models in the voyage-context family use contextualized_embed()."""
    return model.startswith("voyage-context")


def _flatten_chunk_for_chroma(c: dict) -> tuple[str, str, dict]:
    """Return (id, text, metadata-flattened-for-Chroma) for one chunk."""
    meta = dict(c["metadata"])
    for key, val in list(meta.items()):
        if val is None:
            meta[key] = ""
        elif isinstance(val, bool):
            meta[key] = str(val)
        elif isinstance(val, (dict, list)):
            meta[key] = json.dumps(val, ensure_ascii=False)
    meta["doc_type"] = c["doc_type"]
    return c["chunk_id"], c["text"], meta


def _embed_chunks_contextualized(
    to_embed: list[dict],
    collection: chromadb.Collection,
    client: voyageai.Client,
    model: str,
    rate_limit_delay: float,
    max_tokens_per_batch: int,
) -> tuple[int, int]:
    """
    Embed chunks using voyage-context-3's contextualized_embed API.

    Groups chunks by parent document and sends doc-grouped requests so
    the model produces neighbor-aware vectors. Returns (total_tokens,
    total_embedded).
    """
    # voyage-context-3 enforces 120K tokens / 16K chunks / 1000 inputs
    # per request. Token estimates are approximate (~4 chars/token), so
    # leave headroom.
    token_cap = max_tokens_per_batch if max_tokens_per_batch > 0 else 100_000
    batches = _build_contextualized_batches(
        to_embed, max_tokens_per_request=token_cap
    )

    total_tokens = 0
    total_embedded = 0
    start_time = time.time()

    for batch_idx, batch in enumerate(batches):
        # batch: list of docs, each doc: list of chunks
        inputs = [[c["text"] for c in doc] for doc in batch]
        flat_chunks = [c for doc in batch for c in doc]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = client.contextualized_embed(
                    inputs=inputs,
                    model=model,
                    input_type="document",
                    output_dimension=1024,
                )
                # Flatten embeddings in the same order as flat_chunks
                embeddings = []
                for r in result.results:
                    embeddings.extend(r.embeddings)
                total_tokens += getattr(result, "total_tokens", 0) or 0
                break
            except Exception as e:
                err_str = str(e)
                if "rate" in err_str.lower() or "429" in err_str or "limit" in err_str.lower():
                    wait = 30 * (attempt + 1)
                    print(f"\n  Rate limited, waiting {wait}s... ",
                          end="", flush=True)
                    time.sleep(wait)
                    continue
                print(f"\n  Error on batch {batch_idx + 1}: {e}")
                print(f"  Stopping — {total_embedded} chunks embedded so far.")
                print(f"  Run again to resume from where it stopped.")
                return total_tokens, total_embedded
        else:
            print(f"\n  Failed after {max_retries} retries on batch "
                  f"{batch_idx + 1}")
            return total_tokens, total_embedded

        # Add to ChromaDB
        ids, docs_text, metadatas = [], [], []
        for c in flat_chunks:
            cid, text, meta = _flatten_chunk_for_chroma(c)
            ids.append(cid)
            docs_text.append(text)
            metadatas.append(meta)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=docs_text,
            metadatas=metadatas,
        )

        total_embedded += len(flat_chunks)

        elapsed = time.time() - start_time
        rate = total_embedded / elapsed if elapsed > 0 else 0
        remaining = len(to_embed) - total_embedded
        eta_seconds = remaining / rate if rate > 0 else 0
        eta_min = eta_seconds / 60
        pct = total_embedded / len(to_embed) * 100
        print(f"  [{total_embedded}/{len(to_embed)}] ({pct:.0f}%) "
              f"tokens: {total_tokens:,}  "
              f"ETA: {eta_min:.0f}min     ", end="\r", flush=True)

        if batch_idx < len(batches) - 1:
            time.sleep(rate_limit_delay)

    print()
    return total_tokens, total_embedded


def embed_chunks(
    chunks: list[dict],
    collection: chromadb.Collection,
    client: voyageai.Client,
    model: str,
    batch_size: int,
    collection_name: str,
    rate_limit_delay: float = 0.2,
    max_tokens_per_batch: int = 0,
) -> dict:
    """
    Embed a list of chunks and add them to a ChromaDB collection.

    Processes in token-aware batches to stay within Voyage AI's API
    limits. Skips chunks that already exist in the collection (for
    resume). Retries on rate limit errors with exponential backoff.

    Branches to a contextualized code path for voyage-context-* models
    so chunks are sent grouped by parent document.

    Returns a stats dict with token count, cost, etc.
    """
    # Check which chunks already exist in the collection
    existing_ids = set()
    try:
        existing = collection.get()
        existing_ids = set(existing["ids"])
    except Exception:
        pass

    # Filter to chunks that need embedding
    to_embed = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not to_embed:
        print(f"  All {len(chunks)} chunks already in '{collection_name}' — skipping")
        return {"tokens": 0, "cost": 0.0, "embedded": 0, "skipped": len(chunks)}

    skipped = len(chunks) - len(to_embed)
    if skipped > 0:
        print(f"  Skipping {skipped} already-embedded chunks, "
              f"{len(to_embed)} remaining")

    # Contextualized models follow a different request shape and code
    # path — branch off here.
    if _is_contextualized_model(model):
        total_tokens, total_embedded = _embed_chunks_contextualized(
            to_embed, collection, client, model,
            rate_limit_delay, max_tokens_per_batch,
        )
        return _make_stats(total_tokens, total_embedded, skipped, model)

    # Build batches respecting token limits
    if max_tokens_per_batch > 0:
        batches = _build_token_aware_batches(to_embed, max_tokens_per_batch, batch_size)
    else:
        # Simple fixed-size batches
        batches = []
        for i in range(0, len(to_embed), batch_size):
            batches.append(to_embed[i:i + batch_size])

    total_tokens = 0
    total_embedded = 0
    start_time = time.time()

    for batch_idx, batch in enumerate(batches):
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]

        # Flatten metadata — ChromaDB requires simple types
        metadatas = []
        for c in batch:
            meta = dict(c["metadata"])
            # ChromaDB doesn't accept None values
            for key, val in list(meta.items()):
                if val is None:
                    meta[key] = ""
                elif isinstance(val, bool):
                    meta[key] = str(val)
                elif isinstance(val, (dict, list)):
                    meta[key] = json.dumps(val, ensure_ascii=False)
            meta["doc_type"] = c["doc_type"]
            metadatas.append(meta)

        # Call Voyage AI with retry on rate limit errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = client.embed(texts, model=model)
                embeddings = result.embeddings
                total_tokens += result.total_tokens
                break
            except Exception as e:
                err_str = str(e)
                if "rate" in err_str.lower() or "429" in err_str or "limit" in err_str.lower():
                    wait = 30 * (attempt + 1)
                    print(f"\n  Rate limited, waiting {wait}s... ", end="", flush=True)
                    time.sleep(wait)
                    continue
                print(f"\n  Error on batch {batch_idx + 1}: {e}")
                print(f"  Stopping — {total_embedded} chunks embedded so far.")
                print(f"  Run again to resume from where it stopped.")
                return _make_stats(total_tokens, total_embedded, skipped, model)
        else:
            print(f"\n  Failed after {max_retries} retries on batch {batch_idx + 1}")
            print(f"  Run again to resume.")
            return _make_stats(total_tokens, total_embedded, skipped, model)

        # Add to ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        total_embedded += len(batch)

        # Progress with ETA
        elapsed = time.time() - start_time
        rate = total_embedded / elapsed if elapsed > 0 else 0
        remaining = len(to_embed) - total_embedded
        eta_seconds = remaining / rate if rate > 0 else 0
        eta_min = eta_seconds / 60

        pct = total_embedded / len(to_embed) * 100
        print(f"  [{total_embedded}/{len(to_embed)}] ({pct:.0f}%) "
              f"tokens: {total_tokens:,}  "
              f"ETA: {eta_min:.0f}min     ", end="\r", flush=True)

        # Rate limit delay
        if batch_idx < len(batches) - 1:
            time.sleep(rate_limit_delay)

    print()  # newline after progress

    return _make_stats(total_tokens, total_embedded, skipped, model)


def _make_stats(total_tokens: int, embedded: int, skipped: int,
                model: str) -> dict:
    """Build a stats dict from embedding results."""
    price_per_million = VOYAGE_PRICING.get(model, 0.06)
    cost = (total_tokens / 1_000_000) * price_per_million
    return {
        "tokens": total_tokens,
        "cost": cost,
        "embedded": embedded,
        "skipped": skipped,
    }


# ============================================================
# MAIN
# ============================================================

def run_embedder(
    source: str = "olg",
    dry_run: bool = False,
    force: bool = False,
    only: str | None = None,
    model_override: str | None = None,
    collection_suffix: str | None = None,
    max_tokens_per_batch_override: int | None = None,
    granular_chunks_file_override: str | None = None,
) -> None:
    """
    Main embedding pipeline.

    Args:
        source: Which source to embed ('olg' or 'fns').
        dry_run: If True, estimate cost without actually embedding.
        force: If True, delete existing collections before embedding.
        only: If set, embed only the broad tier ('pages'/'chapters')
              or 'sections'.
        model_override: If set, use this Voyage model instead of the
              one in config.ini. Used for evaluation runs.
        collection_suffix: If set, append "_<suffix>" to the resolved
              collection names so the run writes to side-by-side
              variant collections (e.g., "voyage4large") instead of
              clobbering production. Used for evaluation runs.
    """
    config = load_config()
    paths = _resolve_source_paths(source)

    # Validate --only against source
    if only:
        valid_only = {paths["broad_label"], paths["granular_label"]}
        if only not in valid_only:
            print(f"Error: --only {only} is not valid for --source {source}.")
            print(f"  Valid choices for {source}: {', '.join(sorted(valid_only))}")
            sys.exit(1)

    api_key = config.get("api", "voyage_api_key")
    model = model_override or config.get(
        "embedding", "model", fallback="voyage-4-large"
    )
    batch_size = config.getint("embedding", "batch_size", fallback=64)
    if max_tokens_per_batch_override is not None:
        max_tpb = max_tokens_per_batch_override
    else:
        max_tpb = config.getint("embedding", "max_tokens_per_batch", fallback=0)
    rate_delay = config.getfloat("embedding", "rate_limit_delay", fallback=0.2)
    persist_dir = config.get("chromadb", "persist_dir", fallback="index/chroma_db")
    broad_collection_name = config.get(
        "chromadb", paths["broad_collection_key"],
        fallback=paths["broad_label"])
    granular_collection_name = config.get(
        "chromadb", paths["granular_collection_key"],
        fallback=paths["granular_label"])

    if collection_suffix:
        broad_collection_name = f"{broad_collection_name}_{collection_suffix}"
        granular_collection_name = f"{granular_collection_name}_{collection_suffix}"

    # Resolve persist dir relative to the project root
    persist_path = (PROJECT_ROOT / persist_dir).resolve()

    print(f"Source: {source}")
    print(f"Model: {model}")
    print(f"Batch size: {batch_size} items, {max_tpb} tokens/batch")
    print(f"Rate limit delay: {rate_delay}s between requests")
    print(f"ChromaDB path: {persist_path}")
    print()

    # Load chunks
    do_broad = only is None or only == paths["broad_label"]
    do_granular = only is None or only == paths["granular_label"]

    granular_path = paths["granular_chunks_file"]
    if granular_chunks_file_override:
        granular_path = (PROJECT_ROOT / granular_chunks_file_override).resolve()

    broad_chunks = load_chunks(paths["broad_chunks_file"]) if do_broad else []
    granular_chunks = load_chunks(granular_path) if do_granular else []

    # Cost estimation
    all_texts = (
        ([c["text"] for c in broad_chunks] if do_broad else []) +
        ([c["text"] for c in granular_chunks] if do_granular else [])
    )

    est_tokens, est_cost = estimate_cost(all_texts, model)
    print(f"\nEstimated tokens: {est_tokens:,}")
    print(f"Estimated cost:   ${est_cost:.4f}")
    print(f"  ({len(broad_chunks)} {paths['broad_label']} + "
          f"{len(granular_chunks)} {paths['granular_label']})")
    print()

    if dry_run:
        print("Dry run — no embeddings generated.")
        return

    # Initialize clients
    vo = voyageai.Client(api_key=api_key)
    chroma_client = chromadb.PersistentClient(path=str(persist_path))

    total_stats = {"tokens": 0, "cost": 0.0, "embedded": 0}

    # Embed broad tier (pages or chapters)
    if do_broad and broad_chunks:
        print(f"{'='*50}")
        print(f"Embedding {paths['broad_label']} into '{broad_collection_name}'")
        print(f"{'='*50}")

        if force:
            try:
                chroma_client.delete_collection(broad_collection_name)
                print(f"  Deleted existing '{broad_collection_name}' collection")
            except Exception:
                pass

        broad_collection = chroma_client.get_or_create_collection(
            name=broad_collection_name,
            metadata={"description": paths["broad_description"]},
        )

        stats = embed_chunks(
            broad_chunks, broad_collection, vo, model, batch_size,
            broad_collection_name,
            rate_limit_delay=rate_delay,
            max_tokens_per_batch=max_tpb,
        )
        total_stats["tokens"] += stats["tokens"]
        total_stats["cost"] += stats["cost"]
        total_stats["embedded"] += stats["embedded"]

        print(f"  {paths['broad_label'].title()}: {stats['embedded']} embedded, "
              f"{stats['skipped']} skipped, "
              f"{stats['tokens']:,} tokens, ${stats['cost']:.4f}")
        print()

    # Embed granular tier (sections)
    if do_granular and granular_chunks:
        print(f"{'='*50}")
        print(f"Embedding {paths['granular_label']} into '{granular_collection_name}'")
        print(f"{'='*50}")

        if force:
            try:
                chroma_client.delete_collection(granular_collection_name)
                print(f"  Deleted existing '{granular_collection_name}' collection")
            except Exception:
                pass

        granular_collection = chroma_client.get_or_create_collection(
            name=granular_collection_name,
            metadata={"description": paths["granular_description"]},
        )

        stats = embed_chunks(
            granular_chunks, granular_collection, vo, model, batch_size,
            granular_collection_name,
            rate_limit_delay=rate_delay,
            max_tokens_per_batch=max_tpb,
        )
        total_stats["tokens"] += stats["tokens"]
        total_stats["cost"] += stats["cost"]
        total_stats["embedded"] += stats["embedded"]

        print(f"  {paths['granular_label'].title()}: {stats['embedded']} embedded, "
              f"{stats['skipped']} skipped, "
              f"{stats['tokens']:,} tokens, ${stats['cost']:.4f}")
        print()

    # Summary
    print(f"{'='*50}")
    print(f"Embedding complete!")
    print(f"{'='*50}")
    print(f"  Total embedded: {total_stats['embedded']:,} chunks")
    print(f"  Total tokens:   {total_stats['tokens']:,}")
    print(f"  Total cost:     ${total_stats['cost']:.4f}")
    print(f"  ChromaDB:       {persist_path}")


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the embedder."""
    parser = argparse.ArgumentParser(
        description="Embed policy chunks using Voyage AI and store in ChromaDB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # OLG (default)
  python embedder.py --dry-run             # Estimate cost first
  python embedder.py                       # Embed everything
  python embedder.py --only pages          # Embed pages only

  # FNS
  python embedder.py --source fns --dry-run
  python embedder.py --source fns
  python embedder.py --source fns --only chapters

  # Force re-embed
  python embedder.py --source fns --force
        """,
    )
    parser.add_argument(
        "--source", choices=["olg", "fns", "cmr", "cfr"], default="olg",
        help="Which source to embed (default: olg)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Estimate cost without actually embedding",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Delete existing collections and re-embed from scratch",
    )
    parser.add_argument(
        "--only", choices=["pages", "sections", "chapters", "parts"],
        help="Embed only one tier (pages/chapters/parts=broad, sections=granular)",
    )
    parser.add_argument(
        "--model",
        help="Override the embedding model from config.ini "
             "(e.g., voyage-4-large, voyage-context-3). For evaluation runs.",
    )
    parser.add_argument(
        "--collection-suffix",
        help="Append '_<suffix>' to the collection names so this run writes "
             "to side-by-side variant collections instead of production "
             "(e.g., voyage4large). For evaluation runs.",
    )
    parser.add_argument(
        "--max-tokens-per-batch", type=int,
        help="Override [embedding] max_tokens_per_batch from config. Use when "
             "a model enforces a stricter per-batch limit (e.g., voyage-4-large "
             "= 120000).",
    )
    parser.add_argument(
        "--chunks-file",
        help="Override the granular chunks JSON path (relative to project root). "
             "Used to embed alternative chunk variants for evaluation runs.",
    )
    args = parser.parse_args()

    run_embedder(
        source=args.source,
        dry_run=args.dry_run,
        force=args.force,
        only=args.only,
        model_override=args.model,
        collection_suffix=args.collection_suffix,
        max_tokens_per_batch_override=args.max_tokens_per_batch,
        granular_chunks_file_override=args.chunks_file,
    )


if __name__ == "__main__":
    main()
