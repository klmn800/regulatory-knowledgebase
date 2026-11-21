"""Exact phrase search (`query.py --exact`), contract 1.0.

Finds literal occurrences of a phrase in a source's broad-tier text (OLG
pages, FNS / CMR chapters, CFR parts) and reports each match against the
section chunk that contains it. No embeddings and no Voyage call.

How a match is found and attributed:

1. The phrase and every broad document are normalized the same way
   (`normalize`): case-folded, quote / dash / space variants unified,
   zero-width characters and soft hyphens dropped, Markdown heading markers
   at line start dropped, whitespace collapsed. Matching is a plain
   substring match on the normalized text, so ``snap`` also matches inside
   ``snapshot``.
2. For a broad document with matches, its section chunks are loaded and
   ordered by where each chunk's body appears in the document
   (`order_chunks`). Their bodies (chunk text minus the context prefix, i.e.
   everything before the first blank line) are normalized and joined with
   single spaces into one *stream*, with a span per chunk.
3. Each broad match is aligned to a stream occurrence of the phrase
   (`attribute`): in order, picking the nearby occurrence whose surrounding
   text agrees best. A match that doesn't align is tried again against the
   chunks with each one's own heading (the last ``>`` segment of its prefix
   line) put back in front of its body, so a phrase on or across a heading
   lands on the chunk under that heading. An aligned match is reported
   against the chunk where it starts, listing every chunk it spans. A match
   that still can't be aligned (text left out of the section tier, or a
   table laid out differently there) is reported against the parent
   document.

The module splits into pure functions over plain document dicts
(``{"id", "text", "metadata"}``) and a thin ChromaDB loader at the end.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable

# ------------------------------------------------------------------ normalization

_QUOTES_SINGLE = "‘’‚‛′ʼ＇"
_QUOTES_DOUBLE = "“”„‟″«»＂"
_DASHES = "‐‑‒–—―−﹘﹣－"
_SPACES = ("          "
           "     　")
_REMOVED = "​‌‍⁠﻿­"

_TABLE: dict[int, str | None] = {}
_TABLE.update({ord(c): "'" for c in _QUOTES_SINGLE})
_TABLE.update({ord(c): '"' for c in _QUOTES_DOUBLE})
_TABLE.update({ord(c): "-" for c in _DASHES})
_TABLE.update({ord(c): " " for c in _SPACES})
_TABLE.update({ord(c): None for c in _REMOVED})

_HEADING_RE = re.compile(r"(?m)^[ \t]*#{1,6}(?=\s|$)")
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize text for exact matching (PRD 0002 section 4.2.4)."""
    text = text.translate(_TABLE)
    text = _HEADING_RE.sub("", text)
    text = text.casefold()
    return _WS_RE.sub(" ", text).strip()


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalize `text` and map each normalized index to an original index.

    Produces exactly the same string as `normalize`. For a collapsed
    whitespace run, the map points at the run's first character; a
    case-fold that expands one character (``ß`` → ``ss``) maps every output
    character to that one original index.
    """
    out: list[str] = []
    omap: list[int] = []
    n = len(text)
    i = 0
    line_start = True
    space_at: int | None = None  # original index of a pending whitespace run

    def translated(idx: int) -> str:
        ch = text[idx]
        t = _TABLE.get(ord(ch), ch)
        return "" if t is None else t

    def skip_removed(idx: int) -> int:
        while idx < n and translated(idx) == "":
            idx += 1
        return idx

    while i < n:
        if line_start:
            line_start = False
            # Heading marker: optional spaces/tabs, 1-6 '#', then whitespace or
            # end. Removed characters are invisible here, as in `normalize`.
            j = skip_removed(i)
            while j < n and translated(j) in (" ", "\t"):
                j = skip_removed(j + 1)
            k = j
            hashes = 0
            while k < n and translated(k) == "#":
                hashes += 1
                k = skip_removed(k + 1)
            if 0 < hashes <= 6 and (k == n or translated(k).isspace()):
                if j > i and space_at is None:
                    space_at = i
                i = k
                continue
        ch = text[i]
        if ch == "\n":
            line_start = True
        for c in translated(i).casefold():
            if c.isspace():
                if space_at is None:
                    space_at = i
                continue
            if space_at is not None and out:
                out.append(" ")
                omap.append(space_at)
            space_at = None
            out.append(c)
            omap.append(i)
        i += 1
    return "".join(out), omap


# ------------------------------------------------------------------ matching

def find_matches(phrase_norm: str, text_norm: str) -> list[int]:
    """Start offsets of non-overlapping occurrences of `phrase_norm`."""
    if not phrase_norm:
        return []
    starts = []
    pos = text_norm.find(phrase_norm)
    while pos != -1:
        starts.append(pos)
        pos = text_norm.find(phrase_norm, pos + len(phrase_norm))
    return starts


def chunk_body(text: str) -> str:
    """A chunk's text without its context prefix (everything before the
    first blank line; CFR's ancestor preamble sits there too)."""
    head, sep, body = text.partition("\n\n")
    return body if sep else text


# Head length used to find a chunk body inside its parent document.
_ANCHOR_CHARS = 100


def order_chunks(parent_norm: str, chunks: list[dict]) -> list[dict]:
    """Order a parent's chunks by where each body starts in the parent text.

    A chunk whose body head isn't found keeps its place after the chunk
    before it in the given order (the loader's order), so ordering never
    depends on chunk-id conventions, which differ by source.
    """
    keyed = []
    last = -1
    for n, ch in enumerate(chunks):
        head = normalize(chunk_body(ch["text"]))[:_ANCHOR_CHARS]
        pos = parent_norm.find(head) if head else -1
        if pos != -1:
            last = pos
        keyed.append(((last, n), ch))
    keyed.sort(key=lambda kv: kv[0])
    return [ch for _, ch in keyed]


def chunk_heading(text: str) -> str:
    """A chunk's own heading: the last ``>`` segment of its prefix line.

    E.g. ``"106 CMR 362 > NONFINANCIAL > 362.330 Good Cause Criteria"`` gives
    ``"362.330 Good Cause Criteria"``. Empty when the chunk has no prefix.
    """
    head, sep, _ = text.partition("\n\n")
    if not sep:
        return ""
    first_line = head.split("\n", 1)[0]
    return first_line.rsplit(" > ", 1)[-1].strip()


def build_stream(chunks: list[dict],
                 with_headings: bool = False) -> tuple[str, list[tuple[int, int]]]:
    """Join the normalized chunk bodies with single spaces.

    With `with_headings`, each body is preceded by the chunk's own heading
    (`chunk_heading`), which the broad text carries inline but the chunk
    keeps only in its prefix line.

    Returns the stream and each chunk's ``(start, end)`` span in it.
    """
    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    pos = 0
    for ch in chunks:
        body = chunk_body(ch["text"])
        if with_headings:
            body = chunk_heading(ch["text"]) + "\n" + body
        body = normalize(body)
        if parts:
            pos += 1  # the joining space
        spans.append((pos, pos + len(body)))
        parts.append(body)
        pos += len(body)
    return " ".join(parts), spans


_CONTEXT = 40       # characters compared on each side of a match
_MIN_AGREE = 12     # agreeing context characters needed to accept an alignment
_BAND = 16          # stream occurrences considered either side of the expected one


def _common_suffix(a: str, b: str) -> int:
    n = 0
    while n < len(a) and n < len(b) and a[-1 - n] == b[-1 - n]:
        n += 1
    return n


def _common_prefix(a: str, b: str) -> int:
    n = 0
    while n < len(a) and n < len(b) and a[n] == b[n]:
        n += 1
    return n


def _agreement(a: str, ap: int, b: str, bp: int, length: int) -> tuple[int, int]:
    """(agreeing context characters, best possible) around two occurrences."""
    al, bl = a[max(0, ap - _CONTEXT):ap], b[max(0, bp - _CONTEXT):bp]
    ar, br = a[ap + length:ap + length + _CONTEXT], b[bp + length:bp + length + _CONTEXT]
    score = _common_suffix(al, bl) + _common_prefix(ar, br)
    return score, min(len(al), len(bl)) + min(len(ar), len(br))


def attribute(
    phrase_norm: str,
    parent_norm: str,
    parent_offsets: list[int],
    stream: str,
    spans: list[tuple[int, int]],
) -> list[list[int] | None]:
    """Align each parent match to a stream occurrence and name its chunks.

    The two texts usually list occurrences in the same order, but not
    always (FNS example boxes repeat and come out in a different order), so
    the alignment isn't forced to be monotonic. Every pair within a band
    around its expected position is scored by how much surrounding text
    agrees; pairs are then taken best-first (ties: closest to the expected
    position), each occurrence used once, and only if enough context agrees.

    Returns, per parent match (same order), the indexes of the chunks the
    match spans, start chunk first, or ``None`` if it can't be aligned.
    """
    length = len(phrase_norm)
    stream_offsets = find_matches(phrase_norm, stream)
    if not stream_offsets:
        return [None] * len(parent_offsets)

    ratio = len(stream_offsets) / max(1, len(parent_offsets))
    pairs = []
    for i, p in enumerate(parent_offsets):
        expected = round(i * ratio)
        lo, hi = max(0, expected - _BAND), min(len(stream_offsets), expected + _BAND + 1)
        for j in range(lo, hi):
            score, possible = _agreement(parent_norm, p, stream, stream_offsets[j], length)
            if score >= min(_MIN_AGREE, possible):
                pairs.append((-score, abs(j - expected), i, j))
    pairs.sort()

    chosen: dict[int, int] = {}
    used: set[int] = set()
    for _, _, i, j in pairs:
        if i not in chosen and j not in used:
            chosen[i] = j
            used.add(j)

    out: list[list[int] | None] = []
    for i in range(len(parent_offsets)):
        if i not in chosen:
            out.append(None)
            continue
        s = stream_offsets[chosen[i]]
        e = s + length
        out.append([k for k, (cs, ce) in enumerate(spans) if cs < e and s < ce])
    return out


# ------------------------------------------------------------------ search

class EmptyPhraseError(ValueError):
    """The phrase is empty once normalized."""


_SNIPPET_SIDE = 80
_MAX_SNIPPETS = 3


def _snippet(text_norm: str, start: int, length: int) -> str:
    a = max(0, start - _SNIPPET_SIDE)
    b = min(len(text_norm), start + length + _SNIPPET_SIDE)
    return (("..." if a > 0 else "") + text_norm[a:b]
            + ("..." if b < len(text_norm) else ""))


def _parent_metadata(meta: dict) -> dict:
    """Parent metadata for an unaligned result (OLG ``title`` → ``page_title``)."""
    out = dict(meta or {})
    if "title" in out and "page_title" not in out:
        out["page_title"] = out["title"]
    return out


def search_document(
    phrase_norm: str,
    doc: dict,
    chunks: list[dict],
    filter_fn: Callable[[dict], bool] | None = None,
    include_context: bool = False,
    parent_norm: str | None = None,
) -> list[dict]:
    """Exact-search one broad document; returns its results (unranked).

    Results follow chunk order, with the unaligned group (if any) last.
    `parent_norm` (the normalized document text) is computed if not given.
    """
    if parent_norm is None:
        parent_norm = normalize(doc["text"] or "")
    offsets = find_matches(phrase_norm, parent_norm)
    if not offsets:
        return []

    ordered = order_chunks(parent_norm, chunks)
    stream, spans = build_stream(ordered)
    attributions = attribute(phrase_norm, parent_norm, offsets, stream, spans)

    # Second pass for matches on or across a heading: align against the
    # chunks with their own headings restored. Run over every match so the
    # one-occurrence-per-match rule still holds, but only fill the gaps.
    if None in attributions:
        h_stream, h_spans = build_stream(ordered, with_headings=True)
        retry = attribute(phrase_norm, parent_norm, offsets, h_stream, h_spans)
        attributions = [a if a is not None else r
                        for a, r in zip(attributions, retry)]

    by_chunk: dict[int, dict] = {}
    unaligned: list[int] = []
    for p, chunk_idx in zip(offsets, attributions):
        if chunk_idx is None:
            unaligned.append(p)
            continue
        group = by_chunk.setdefault(chunk_idx[0], {"offsets": [], "chunks": set()})
        group["offsets"].append(p)
        group["chunks"].update(chunk_idx)

    parent_context = ({"text": doc["text"], "metadata": doc["metadata"]}
                      if include_context else None)
    length = len(phrase_norm)
    results = []
    for k in sorted(by_chunk):
        ch = ordered[k]
        if filter_fn is not None and not filter_fn(ch["metadata"] or {}):
            continue
        group = by_chunk[k]
        results.append({
            "id": ch["id"],
            "chunk_ids": [ordered[i]["id"] for i in sorted(group["chunks"])],
            "parent_id": doc["id"],
            "match_count": len(group["offsets"]),
            "snippets": [_snippet(parent_norm, p, length)
                         for p in group["offsets"][:_MAX_SNIPPETS]],
            "text": ch["text"],
            "metadata": ch["metadata"],
            "parent_context": parent_context,
        })
    if unaligned:
        meta = _parent_metadata(doc["metadata"])
        if filter_fn is None or filter_fn(meta):
            results.append({
                "id": None,
                "chunk_ids": [],
                "parent_id": doc["id"],
                "match_count": len(unaligned),
                "snippets": [_snippet(parent_norm, p, length)
                             for p in unaligned[:_MAX_SNIPPETS]],
                "text": doc["text"],
                "metadata": meta,
                "parent_context": parent_context,
            })
    return results


def exact_search(
    phrase: str,
    broad_docs: Iterable[dict],
    chunk_loader: Callable[[str], list[dict]],
    filter_fn: Callable[[dict], bool] | None = None,
    top: int | None = None,
    include_context: bool = False,
) -> dict:
    """Find `phrase` in every broad document and rank the results.

    Args:
        phrase: The literal phrase (normalized here).
        broad_docs: ``{"id", "text", "metadata"}`` per broad document.
        chunk_loader: Returns a parent's section chunks, given its id.
        filter_fn: Keeps a result when it returns True for the result's
            metadata (the chunk's, or the parent's for an unaligned result).
        top: Cap on returned results; None returns all.
        include_context: Put the parent document in ``parent_context``.

    Returns:
        ``normalized_phrase``, ``result_count``, ``total_results``,
        ``total_matches``, ``truncated`` and ``results``. Parents sort by
        their match count (descending), then parent id; within a parent,
        chunk order with the unaligned result last.

    Raises:
        EmptyPhraseError: the phrase normalizes to nothing.
    """
    phrase_norm = normalize(phrase or "")
    if not phrase_norm:
        raise EmptyPhraseError("the --exact phrase is empty")

    per_parent = []
    for doc in broad_docs:
        parent_norm = normalize(doc["text"] or "")
        if phrase_norm not in parent_norm:
            continue
        results = search_document(phrase_norm, doc, chunk_loader(doc["id"]),
                                  filter_fn=filter_fn, include_context=include_context,
                                  parent_norm=parent_norm)
        if results:
            per_parent.append((sum(r["match_count"] for r in results), doc["id"], results))

    per_parent.sort(key=lambda t: (-t[0], t[1]))
    ranked = [r for _, _, results in per_parent for r in results]
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i

    total = len(ranked)
    kept = ranked if top is None else ranked[:max(0, top)]
    # Rank first in each result, like a normal search hit.
    kept = [{"rank": r["rank"], **{k: v for k, v in r.items() if k != "rank"}}
            for r in kept]
    return {
        "normalized_phrase": phrase_norm,
        "result_count": len(kept),
        "total_results": total,
        "total_matches": sum(n for n, _, _ in per_parent),
        "truncated": len(kept) < total,
        "results": kept,
    }


# ------------------------------------------------------------------ ChromaDB loader

def load_broad_docs(broad_collection) -> list[dict]:
    """Every document in a broad collection, as plain dicts."""
    raw = broad_collection.get(include=["documents", "metadatas"])
    return [{"id": i, "text": d or "", "metadata": m or {}}
            for i, d, m in zip(raw["ids"], raw["documents"], raw["metadatas"])]


def make_chunk_loader(granular_collection, parent_id_field: str) -> Callable[[str], list[dict]]:
    """A loader for one parent's section chunks, queried on demand."""
    def load(parent_id: str) -> list[dict]:
        raw = granular_collection.get(where={parent_id_field: parent_id},
                                      include=["documents", "metadatas"])
        return [{"id": i, "text": d or "", "metadata": m or {}}
                for i, d, m in zip(raw["ids"], raw["documents"], raw["metadatas"])]
    return load
