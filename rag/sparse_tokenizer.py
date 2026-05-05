"""Tokenizer for the BM25 sparse index.

Two atomic-preservation rules survive the audit (see `docs/sparse_token_audit.md`):

  R1 dotted numerics:   \\d+(\\.\\d+)+    e.g. 363.140, 271.2, 1170.5, 5.00
  R3 hyphenated codes:  [A-Z]+-\\d+       e.g. VC-1, COVID-19, I-130, AP-1

These are the patterns the default tokenizer (whitespace + punctuation)
would split incorrectly. Everything else (acronyms like ABAWD, BEACON, codes
like BEACON5) survives default tokenization fine and benefits from
case-folding without atomic preservation.

R1 is kept wide; some dollar amounts ($5.00, $40.50) get preserved as atomic
tokens. This is cosmetically noisy but functionally neutral — extra
vocabulary entries don't hurt BM25 retrieval.
"""
from __future__ import annotations

import re

_R1_DOTTED = re.compile(r"\b\d+(?:\.\d+)+\b")
_R3_HYPHEN = re.compile(r"\b[A-Z]+-\d+\b")

# Combined pattern for atomic protection. Order matters: R3 before R1 so that
# something like "I-130" doesn't get partial-matched.
_ATOMIC = re.compile(r"\b[A-Z]+-\d+\b|\b\d+(?:\.\d+)+\b")

# Tokenizer for the non-atomic remainder: split on anything that isn't a
# letter, digit, or apostrophe (keeps contractions intact).
_WORD = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> list[str]:
    """Tokenize a chunk of text for BM25 indexing.

    Steps:
      1. Find atomic spans (R1, R3), record their positions, lowercase them.
      2. Tokenize the gaps between atomic spans normally (lowercase word-runs).
      3. Stitch tokens back together in document order.

    Returns a flat list of lowercased tokens.
    """
    if not text:
        return []

    tokens: list[str] = []
    pos = 0
    for match in _ATOMIC.finditer(text):
        start, end = match.span()
        if start > pos:
            tokens.extend(t.lower() for t in _WORD.findall(text[pos:start]))
        tokens.append(match.group(0).lower())
        pos = end
    if pos < len(text):
        tokens.extend(t.lower() for t in _WORD.findall(text[pos:]))

    return tokens


def tokenize_query(query: str) -> list[str]:
    """Tokenize a search query the same way as documents.

    Same function as `tokenize` for now — kept separate so we can diverge
    if we ever want to e.g. add query-side synonym expansion.
    """
    return tokenize(query)
