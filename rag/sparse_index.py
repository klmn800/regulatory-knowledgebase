"""BM25 sparse index — build and search.

Stored at `index/sparse/{source}.pkl` as a pickle of a `SparseIndex` instance
(BM25Okapi + ordered chunk_ids list + minimal metadata).

The index is a per-source companion to the dense ChromaDB collections.
Hybrid retrieval fuses dense + sparse via RRF (see `rag.query.search`).
"""
from __future__ import annotations

import json
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rank_bm25 import BM25Okapi

from rag.sparse_tokenizer import tokenize, tokenize_query

INDEX_VERSION = 1


@dataclass
class SparseIndex:
    """A BM25 index over one source's section-tier chunks."""
    bm25: BM25Okapi
    chunk_ids: list[str]
    source: str
    version: int = INDEX_VERSION
    built_at: float = 0.0

    def search(self, query: str, top_n: int = 30) -> list[tuple[str, float]]:
        """Return top-N (chunk_id, score) sorted by descending score."""
        tokens = tokenize_query(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        idx_score_pairs = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_n]
        return [(self.chunk_ids[i], float(s)) for i, s in idx_score_pairs if s > 0]


def _chunk_text(chunk: dict) -> str:
    """Combine the searchable text fields from a chunk."""
    parts: list[str] = []
    for key in ("text", "content", "body", "context_prefix"):
        v = chunk.get(key)
        if isinstance(v, str):
            parts.append(v)
    return "\n".join(parts) if parts else json.dumps(chunk)


def _chunk_id(chunk: dict) -> str:
    """Resolve the canonical chunk identifier."""
    for key in ("chunk_id", "id"):
        v = chunk.get(key)
        if isinstance(v, str) and v:
            return v
    raise KeyError(f"chunk missing 'chunk_id' or 'id': {chunk!r}")


def build_sparse_index(source: str, chunks: Iterable[dict]) -> SparseIndex:
    """Tokenize every chunk and construct a BM25 index."""
    chunk_ids: list[str] = []
    tokenized_corpus: list[list[str]] = []
    for ch in chunks:
        chunk_ids.append(_chunk_id(ch))
        tokenized_corpus.append(tokenize(_chunk_text(ch)))

    if not tokenized_corpus:
        raise ValueError(f"No chunks provided for source={source}")

    bm25 = BM25Okapi(tokenized_corpus)
    return SparseIndex(
        bm25=bm25,
        chunk_ids=chunk_ids,
        source=source,
        built_at=time.time(),
    )


def save_index(index: SparseIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(index, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_index(path: Path) -> SparseIndex:
    with path.open("rb") as f:
        return pickle.load(f)


def index_path_for(project_root: Path, source: str) -> Path:
    return project_root / "index" / "sparse" / f"{source}.pkl"
