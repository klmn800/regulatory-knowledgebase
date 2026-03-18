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

# Voyage AI pricing (per 1M tokens) as of 2026
# See https://docs.voyageai.com/docs/pricing
VOYAGE_PRICING = {
    "voyage-3": 0.06,
    "voyage-3-lite": 0.02,
    "voyage-3-large": 0.18,
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
            "broad_chunks_file": PROJECT_ROOT / "data" / "olg" / "page_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "data" / "olg" / "section_chunks.json",
            "broad_collection_key": "olg_page_collection",
            "granular_collection_key": "olg_section_collection",
            "broad_label": "pages",
            "granular_label": "sections",
            "broad_description": "DTA Policy Online Guide - page-level documents",
            "granular_description": "DTA Policy Online Guide - section-level chunks",
        }
    elif source == "fns":
        return {
            "broad_chunks_file": PROJECT_ROOT / "data" / "fns" / "chapter_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "data" / "fns" / "section_chunks.json",
            "broad_collection_key": "fns_chapter_collection",
            "granular_collection_key": "fns_section_collection",
            "broad_label": "chapters",
            "granular_label": "sections",
            "broad_description": "FNS Handbook 310 - chapter-level documents",
            "granular_description": "FNS Handbook 310 - section-level chunks",
        }
    elif source == "cmr":
        return {
            "broad_chunks_file": PROJECT_ROOT / "data" / "cmr" / "chapter_chunks.json",
            "granular_chunks_file": PROJECT_ROOT / "data" / "cmr" / "section_chunks.json",
            "broad_collection_key": "cmr_chapter_collection",
            "granular_collection_key": "cmr_section_collection",
            "broad_label": "chapters",
            "granular_label": "sections",
            "broad_description": "106 CMR - chapter-level documents",
            "granular_description": "106 CMR - section-level chunks",
        }
    else:
        print(f"Error: Unknown source '{source}'. Use 'olg', 'fns', or 'cmr'.")
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
) -> None:
    """
    Main embedding pipeline.

    Args:
        source: Which source to embed ('olg' or 'fns').
        dry_run: If True, estimate cost without actually embedding.
        force: If True, delete existing collections before embedding.
        only: If set, embed only the broad tier ('pages'/'chapters')
              or 'sections'.
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
    model = config.get("embedding", "model", fallback="voyage-3")
    batch_size = config.getint("embedding", "batch_size", fallback=64)
    max_tpb = config.getint("embedding", "max_tokens_per_batch", fallback=0)
    rate_delay = config.getfloat("embedding", "rate_limit_delay", fallback=0.2)
    persist_dir = config.get("chromadb", "persist_dir", fallback="data/chroma_db")
    broad_collection_name = config.get(
        "chromadb", paths["broad_collection_key"],
        fallback=paths["broad_label"])
    granular_collection_name = config.get(
        "chromadb", paths["granular_collection_key"],
        fallback=paths["granular_label"])

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

    broad_chunks = load_chunks(paths["broad_chunks_file"]) if do_broad else []
    granular_chunks = load_chunks(paths["granular_chunks_file"]) if do_granular else []

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
        "--source", choices=["olg", "fns", "cmr"], default="olg",
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
        "--only", choices=["pages", "sections", "chapters"],
        help="Embed only one tier (pages/chapters=broad, sections=granular)",
    )
    args = parser.parse_args()

    run_embedder(
        source=args.source,
        dry_run=args.dry_run,
        force=args.force,
        only=args.only,
    )


if __name__ == "__main__":
    main()
