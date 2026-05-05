"""Build BM25 sparse indexes for one or all sources.

Reads section-tier chunk JSONs (the same ones the embedder uses), tokenizes
them per `rag.sparse_tokenizer`, and pickles a `SparseIndex` to
`index/sparse/{source}.pkl`.

Designed to be re-runnable: each invocation rebuilds from scratch. Cheap —
all in-memory, ~10K total chunks across the four sources.

Usage:
    python tools/build_sparse_index.py                    # all sources
    python tools/build_sparse_index.py --source olg       # one source
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rag.embedder import _resolve_source_paths
from rag.sparse_index import build_sparse_index, save_index, index_path_for

SOURCES = ("olg", "cmr", "fns", "cfr")


def build_one(source: str) -> dict:
    paths = _resolve_source_paths(source)
    chunks_path: Path = paths["granular_chunks_file"]
    if not chunks_path.exists():
        return {"source": source, "ok": False, "reason": f"missing chunks file {chunks_path}"}

    with chunks_path.open(encoding="utf-8") as f:
        data = json.load(f)
    chunks = data if isinstance(data, list) else data.get("chunks", [])
    if not chunks:
        return {"source": source, "ok": False, "reason": "no chunks loaded"}

    t0 = time.time()
    index = build_sparse_index(source, chunks)
    out_path = index_path_for(PROJECT_ROOT, source)
    save_index(index, out_path)
    elapsed = time.time() - t0
    size_kb = out_path.stat().st_size / 1024

    return {
        "source": source,
        "ok": True,
        "chunks": len(chunks),
        "out": out_path,
        "size_kb": size_kb,
        "elapsed_s": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=SOURCES, default=None,
                        help="Build for one source. Default: all.")
    args = parser.parse_args()

    targets = (args.source,) if args.source else SOURCES
    results = []
    for src in targets:
        print(f"[build] {src}: ", end="", flush=True)
        result = build_one(src)
        results.append(result)
        if result["ok"]:
            print(f"OK — {result['chunks']:,} chunks, "
                  f"{result['size_kb']:,.0f} KB, "
                  f"{result['elapsed_s']:.1f}s -> {result['out']}")
        else:
            print(f"SKIP — {result['reason']}")

    print()
    print("=== Summary ===")
    for r in results:
        if r["ok"]:
            print(f"  {r['source']:6} {r['chunks']:>6,} chunks   {r['size_kb']:>8,.0f} KB")
        else:
            print(f"  {r['source']:6} (skipped: {r['reason']})")


if __name__ == "__main__":
    main()
