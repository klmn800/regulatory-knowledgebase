"""
Chunker for FNS Handbook 310 RAG pipeline.

Reads the parsed section JSON files and produces two sets of chunks
for embedding:

  1. Chapter-level documents (one per chapter) — for broad topic matching
  2. Section-level chunks (granular) — for specific policy answers

Section chunking uses a break-priority splitter that respects FNS's
prose-with-bullets structure (no consistent paren-marker hierarchy
like CMR/CFR have). Splits prefer:
    table-row > bullet/numbered list item > paragraph > sentence > hard slice
Sub-bullets (➢ ▪ ○ -) are kept attached to their parent bullet.

Cross-section merging is disabled. Each FNS section becomes its own
chunk (or set of split chunks); small sections stay small.

Output:
  chapter_chunks.json  — list of chapter-level documents with metadata
  section_chunks.json  — list of section-level chunks with metadata

Usage:
    python chunker.py                     # Process all parsed sections
    python chunker.py --stats             # Show statistics only
    python chunker.py --preview 2         # Preview chunks for first 2 chapters
"""

import argparse
import json
import re
import statistics
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = PROJECT_ROOT / "index" / "fns"
PARSED_DIR = INDEX_DIR / "parsed_sections"
CHAPTER_CHUNKS_FILE = INDEX_DIR / "chapter_chunks.json"
SECTION_CHUNKS_FILE = INDEX_DIR / "section_chunks.json"

MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 1500
TARGET_CHUNK_SIZE = 1000

# Below MIN_CHUNK_SIZE but above HARD_MIN, the splitter may still place a
# break if the alternative (in-range) candidate is a low-priority break
# like mid-list. This favors structural integrity over hitting MIN.
HARD_MIN_CHUNK_SIZE = 100

# A break score is "high priority" if it represents a clean structural
# boundary worth preserving even when the resulting chunk dips below MIN.
HIGH_PRIORITY_BREAK_SCORE = 60

# Reserved character budget for the context prefix line that gets prepended
# to every chunk (e.g., "FNS 310 > Chapter 10: Income > 1045.2 ...").
# Subtracted from MAX when deciding split points so the final chunk_text
# (prefix + body) stays within MAX_CHUNK_SIZE.
PREFIX_BUDGET = 200

# Chapter → program mapping. SNAP chapters are case-processing relevant;
# QC_Process chapters cover how reviewers do their job. UI checkbox panel
# pre-checks SNAP only.
FNS_CHAPTER_PROGRAM = {
    1:  "QC_Process",
    2:  "QC_Process",
    3:  "QC_Process",
    4:  "QC_Process",
    5:  "QC_Process",
    6:  "QC_Process",
    7:  "SNAP",
    8:  "SNAP",
    9:  "SNAP",
    10: "SNAP",
    11: "SNAP",
    12: "QC_Process",
    13: "SNAP",
    14: "QC_Process",
}


# ============================================================
# LINE CLASSIFICATION
# ============================================================

# Top-level bullet markers — lines starting here are good break candidates.
TOP_BULLET_RE = re.compile(r"^[•·]\s+")

# Sub-bullet / continuation markers — lines starting here should NOT be
# separated from their parent bullet above. Includes arrow (➢ U+27A2),
# small square (▪), open circle (○), and dash variants.
SUB_BULLET_RE = re.compile(r"^[➢▪○\-—–]\s+")

# Numbered list items: "1. ", "2. ", etc.
NUMBERED_RE = re.compile(r"^\d+\.\s+")

# Procedural step markers: "Step 1.", "Step 2.", etc. Used in §726.x and similar
# step-by-step instruction sections. Treated as numbered list items so that
# list-integrity rules keep step bodies together and break-before-step gets
# a high score.
STEP_RE = re.compile(r"^Step\s+\d+\.\s+")

# Lettered list items: "A. ", "a. ", etc. (rare in FNS)
LETTERED_RE = re.compile(r"^[A-Za-z]\.\s+")

# Paren-numbered items: "(1) ", "(a) " — extremely rare in FNS but harmless.
PAREN_NUM_RE = re.compile(r"^\(\d{1,2}\)\s+")
PAREN_LETTER_RE = re.compile(r"^\([A-Za-z]{1,2}\)\s+")

# Table line: starts and ends with pipe.
TABLE_LINE_RE = re.compile(r"^\|.*\|$")

# Table separator row (the | --- | --- | line just under headers).
TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|$")


def classify_line(line: str) -> str:
    """
    Classify a line for break-priority decisions.

    Returns one of:
      'BLANK'       — empty/whitespace
      'TABLE_HDR'   — table header row (first | ... | line in a block)
      'TABLE_SEP'   — | --- | --- | separator
      'TABLE_ROW'   — table data row
      'BULLET_TOP'  — • or · bulleted item
      'BULLET_SUB'  — ➢ ▪ ○ - sub-bullet (or continuation)
      'NUMBERED'    — "1. " numbered item
      'LETTERED'    — "A. " or "a. " lettered item
      'PAREN'       — "(1) " or "(a) " paren-marked item
      'PROSE'       — anything else
    """
    stripped = line.strip()
    if not stripped:
        return "BLANK"
    if TABLE_SEP_RE.match(stripped):
        return "TABLE_SEP"
    if TABLE_LINE_RE.match(stripped):
        # Distinguish header from row by context — caller does that.
        return "TABLE_ROW"
    if TOP_BULLET_RE.match(stripped):
        return "BULLET_TOP"
    if SUB_BULLET_RE.match(stripped):
        return "BULLET_SUB"
    if STEP_RE.match(stripped):
        return "NUMBERED"
    if NUMBERED_RE.match(stripped):
        return "NUMBERED"
    if LETTERED_RE.match(stripped):
        return "LETTERED"
    if PAREN_NUM_RE.match(stripped) or PAREN_LETTER_RE.match(stripped):
        return "PAREN"
    return "PROSE"


def annotate_table_headers(line_classes: list[str]) -> list[str]:
    """
    Walk classifications and promote the first TABLE_ROW of a contiguous
    table block to TABLE_HDR. The table header is the row before the
    TABLE_SEP separator (if present), otherwise the first row of the block.
    """
    out = list(line_classes)
    in_table = False
    block_start = -1
    for i, cls in enumerate(out):
        is_table = cls in ("TABLE_ROW", "TABLE_HDR", "TABLE_SEP")
        if is_table and not in_table:
            in_table = True
            block_start = i
        elif not is_table and in_table:
            in_table = False
        # Find separator-marked headers
        if cls == "TABLE_SEP" and block_start >= 0 and i - 1 >= block_start:
            if out[i - 1] == "TABLE_ROW":
                out[i - 1] = "TABLE_HDR"
    return out


# ============================================================
# BREAK SCORING
# ============================================================

# Higher score = better place to break.
# 0 = forbidden / very bad
# 100 = ideal
BREAK_SCORES = {
    # Break BEFORE these line types:
    "BULLET_TOP_after_NONBULLET": 80,   # entering a bullet list from prose
    "TABLE_HDR_after_NONTABLE":   85,   # entering a table from prose
    "NUMBERED_after_NONNUMBERED": 80,
    "PROSE_after_BLANK":          60,   # paragraph break
    "BULLET_TOP_after_BULLET_TOP": 50,  # between sibling top-level bullets
    "TABLE_ROW_after_TABLE_ROW":  40,   # between table rows (mid-table)
    "PROSE_after_TABLE":          70,   # exiting a table
    "PROSE_after_BULLET_TOP":     30,   # bullet → prose transition (weak)
}

# Forbidden breaks (score 0): never break BEFORE these.
FORBIDDEN_BEFORE = {"BULLET_SUB", "TABLE_SEP"}


# Detects a line that ends with a sentence terminator (and is not just a
# bare token like "Mr."). Used to identify "soft" paragraph boundaries
# inside continuous prose where the parser didn't insert a blank line.
SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]?\s*$")

# A line starting with a capitalized word — candidate for being a new
# paragraph if the previous line ended with a sentence terminator.
CAPITAL_START_RE = re.compile(r"^[A-Z]")

# A "definition entry" line: starts with a capitalized term followed by
# en-dash or em-dash and a space, indicating "Term – Definition...".
# Common in glossary sections like §130, §154.x.
DEFINITION_LINE_RE = re.compile(r"^[A-Z][A-Za-z0-9 ,'()/-]{1,80}\s+[–—-]\s+\S")


# Detects a line that begins an example/callout block. Two forms:
#   "Example: ...rest..."
#   "Example of {subject}: ...rest..."
# The {subject} portion is bounded to avoid pathological matches.
EXAMPLE_START_RE = re.compile(r"^\s*Example(\s+of\s+[^:]{0,80})?:")


def _is_example_start(line: str) -> bool:
    """True when the line begins an example/callout block."""
    return bool(EXAMPLE_START_RE.match(line))


def annotate_example_ranges(lines: list[str]) -> list[bool]:
    """
    Return per-line booleans flagging lines INSIDE an example block.

    Example blocks span from an example-start line (exclusive) to the next
    example-start line OR end of section. The example-start line itself is
    False — it's the desired break-before target, not a forbidden one.
    Lines BEFORE the first example-start are also False.

    The splitter uses this to forbid breaks inside an example paragraph,
    so an example as a unit owns its chunk (or chunks if it overflows MAX).
    """
    in_example = [False] * len(lines)
    inside = False
    for i, line in enumerate(lines):
        if _is_example_start(line):
            inside = True
            in_example[i] = False
        else:
            in_example[i] = inside
    return in_example


def _is_subheading(line: str) -> bool:
    """
    Detect a prose line that functions as a sub-heading inside a section —
    e.g. 'Four-part test to establish fleeing felon status.', 'Verification.',
    'Application processing.', or 'Alternative test to establish fleeing
    felon status (also known as the Martinez test).'

    These are topic-introducer lines: end with a sentence terminator, not
    bulleted/numbered, start with a capital letter. The 100-char threshold
    catches longer headings like the Martinez test example while excluding
    typical regulatory body sentences which run 120+ chars.

    Breaking BEFORE a sub-heading groups it with its content; breaking
    AFTER one orphans the heading at chunk end.
    """
    s = line.strip()
    if not s or len(s) > 100:
        return False
    if not re.search(r"[.!?]$", s):
        return False
    if re.match(r"^[•·➢▪○\-—–]\s+", s):
        return False
    if re.match(r"^\d+\.\s+", s) or re.match(r"^[A-Za-z]\.\s+", s):
        return False
    if not s[0].isupper():
        return False
    return True


def _prev_meaningful_ends_colon(idx: int, lines: list[str],
                                 classes: list[str]) -> bool:
    """
    Walk backward through BLANK lines from idx-1 to the most recent non-blank
    line and check whether it ends with `:`. The list-intro orphan signal
    (colon directly preceding a list/table) is otherwise lost when the parser
    inserts a blank line between the intro and the list.
    """
    j = idx - 1
    while j >= 0 and classes[j] == "BLANK":
        j -= 1
    if j < 0:
        return False
    return lines[j].rstrip().endswith(":")


def score_break_before(idx: int, classes: list[str], lines: list[str],
                       in_example: list[bool] | None = None) -> int:
    """
    Return a score for breaking BEFORE line[idx]. Higher = better.
    0 means do not break here.

    `lines` is passed so we can look at content (sentence terminators,
    capitalized starts, definition patterns) when class-only scoring is
    insufficient. `in_example` (when provided) marks lines inside an example
    block so the splitter avoids mid-example breaks.
    """
    if idx == 0 or idx >= len(classes):
        return 0
    cur = classes[idx]
    prev = classes[idx - 1]
    cur_line = lines[idx]
    prev_line = lines[idx - 1]

    if cur in FORBIDDEN_BEFORE:
        return 0

    # Inside an example block — break here only as a last resort. The example
    # owns its chunk; mid-example breaks orphan the example body from its
    # heading. Score 1 (not 0) so the forced-break fallback can still place
    # a break here when no other option exists in the size window.
    if in_example is not None and in_example[idx]:
        return 1

    # Example-start line — high break-before score (sub-heading-equivalent).
    # Captures both "Example: ..." and "Example of X: ..." forms. This applies
    # regardless of prev's class, including the policy-text → first-example
    # seam (where prev is typically a BLANK line).
    if _is_example_start(cur_line):
        return 70

    # Don't break right after a table header / separator (would orphan the table)
    if prev in ("TABLE_HDR", "TABLE_SEP"):
        return 0

    # Sub-heading detection — give a high break score when cur is a topic-
    # introducer line (short, capitalized, ends with sentence terminator),
    # regardless of prev's class. This works whether prev is a list item,
    # a paragraph end, or a blank line. Breaking BEFORE a sub-heading
    # groups it with its content instead of orphaning the heading.
    if cur == "PROSE" and _is_subheading(cur_line):
        prev_complete = (
            prev == "BLANK"
            or prev in ("BULLET_TOP", "BULLET_SUB", "NUMBERED", "LETTERED", "PAREN")
            or (prev == "PROSE" and bool(SENTENCE_END_RE.search(prev_line)))
        )
        if prev_complete:
            return 65

    # If the previous (non-blank) line ends with a colon, it's an intro/lead-in
    # to a following list or table. Breaking between the intro and what it
    # introduces orphans the context. Penalize structural-entry scores in
    # that case. Looking through blanks is required because the parser often
    # inserts a blank between the intro and the list.
    prev_ends_colon = _prev_meaningful_ends_colon(idx, lines, classes)

    # Entering structures from prose / blank
    if cur == "TABLE_HDR" and prev not in ("TABLE_ROW", "TABLE_HDR", "TABLE_SEP"):
        return 5 if prev_ends_colon else 85
    if cur == "BULLET_TOP" and prev not in ("BULLET_TOP", "BULLET_SUB"):
        return 5 if prev_ends_colon else 80
    if cur == "NUMBERED" and prev != "NUMBERED":
        return 5 if prev_ends_colon else 80

    # Exiting a table
    if prev in ("TABLE_ROW", "TABLE_HDR") and cur not in ("TABLE_ROW", "TABLE_SEP"):
        return 70

    # Paragraph break (blank line then prose). The blank line is a real
    # paragraph boundary only if the line BEFORE the blank ends with a
    # sentence terminator AND the line AFTER starts with a capital letter.
    # Otherwise the blank is a PDF-extraction artifact mid-sentence (common
    # in side-by-side / column-wrapped sections).
    if prev == "BLANK" and cur == "PROSE":
        # Find the most recent non-BLANK line above
        before_blank = idx - 2
        while before_blank >= 0 and classes[before_blank] == "BLANK":
            before_blank -= 1
        prev_non_blank = lines[before_blank] if before_blank >= 0 else ""
        cur_starts_capital = bool(CAPITAL_START_RE.match(cur_line.strip()))
        prev_ends_sentence = bool(SENTENCE_END_RE.search(prev_non_blank))
        if prev_ends_sentence and cur_starts_capital:
            return 60          # real paragraph break
        elif cur_starts_capital:
            return 35          # weak signal — capital start without sentence end
        else:
            return 10          # spurious blank inside a continuing sentence

    # Sibling top-level bullets — fallback only. Lower than paragraph
    # breaks (45-60) so the algorithm prefers to break at paragraph
    # boundaries rather than mid-list when both are available. Mid-list
    # breaks happen only when the list itself is too large to fit.
    if prev == "BULLET_TOP" and cur == "BULLET_TOP":
        return 25

    # Mid-table row break (acceptable but worse than entering/exiting)
    if prev == "TABLE_ROW" and cur == "TABLE_ROW":
        return 40

    # Bullet → prose
    if prev == "BULLET_TOP" and cur == "PROSE":
        return 30

    # Content-aware paragraph detection (no blank line in source PDF):
    # If prev line ends with sentence terminator AND current line starts
    # with a capital, treat as soft paragraph boundary.
    if (prev == "PROSE" and cur == "PROSE"
            and SENTENCE_END_RE.search(prev_line)
            and CAPITAL_START_RE.match(cur_line.strip())):
        # Sub-heading: cur is a short heading line that introduces a new
        # topic. Breaking BEFORE it groups the heading with its content.
        if _is_subheading(cur_line):
            return 65
        # If prev_line is itself a sub-heading, breaking AFTER it would
        # orphan the heading at chunk end. Penalize.
        if _is_subheading(prev_line):
            return 15
        # Definition pattern ("Term – Definition")
        if DEFINITION_LINE_RE.match(cur_line.strip()):
            return 65
        return 45

    # Within continuous prose with no boundary signal — last-resort break
    return 5


# ============================================================
# TABLE HEADER TRACKING (for continued-table header repetition)
# ============================================================

def find_table_blocks(classes: list[str]) -> list[tuple[int, int, int | None]]:
    """
    Identify contiguous table blocks. Returns a list of (start, end, header_idx)
    triples where:
      start, end — inclusive line indices spanning the table
      header_idx — line index of the TABLE_HDR row, or None if no header
    """
    blocks = []
    in_block = False
    start = -1
    for i, cls in enumerate(classes):
        is_table = cls in ("TABLE_ROW", "TABLE_HDR", "TABLE_SEP")
        if is_table and not in_block:
            in_block = True
            start = i
        elif not is_table and in_block:
            header_idx = next(
                (j for j in range(start, i) if classes[j] == "TABLE_HDR"),
                None,
            )
            blocks.append((start, i - 1, header_idx))
            in_block = False
    if in_block:
        header_idx = next(
            (j for j in range(start, len(classes)) if classes[j] == "TABLE_HDR"),
            None,
        )
        blocks.append((start, len(classes) - 1, header_idx))
    return blocks


# ============================================================
# SPLIT ALGORITHM
# ============================================================

# Split a single prose line at internal sentence boundaries. Used as a
# preprocessing step so the line-boundary chunker sees more break candidates
# in continuous prose paragraphs (where the parser's PDF extraction did
# not insert blank lines between sentences).
#
# Lookahead allows: lowercase ([a-z]), whitespace (single-letter starts
# like "A State agency..."), or end-of-string. Excludes digits to avoid
# false-positive splits at "Section 622.\n1234" patterns.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z](?:[a-z]|\s|$))")


def _expand_long_prose_lines(lines: list[str], threshold: int = 0) -> list[str]:
    """
    Pre-split prose lines at internal sentence boundaries so the line-
    boundary chunker has more break candidates in continuous prose
    paragraphs (where the parser's PDF extraction did not insert blank
    lines between sentences).

    Lines shorter than `threshold` chars OR not classified as PROSE are
    returned as-is. SENTENCE_SPLIT_RE only matches `. [A-Z][a-z]` (period
    + space + capital letter + lowercase letter), so it doesn't split
    on abbreviations or numeric references like "8.1.0".
    """
    out = []
    for line in lines:
        if len(line) < threshold:
            out.append(line)
            continue
        cls = classify_line(line)
        if cls != "PROSE":
            out.append(line)
            continue
        pieces = SENTENCE_SPLIT_RE.split(line)
        if len(pieces) == 1:
            out.append(line)
        else:
            out.extend(pieces)
    return out


def split_text_by_breaks(text: str, max_size: int = MAX_CHUNK_SIZE,
                          min_size: int = MIN_CHUNK_SIZE) -> list[str]:
    """
    Split text into chunks using break-priority logic. Each output chunk
    targets TARGET_CHUNK_SIZE, never exceeds max_size if it can be
    avoided, and respects bullet/table/list integrity.

    max_size and min_size are parameters so callers can reserve budget
    for context prefix that will be prepended later.

    If a section's text fits in max_size, returns [text] unchanged.
    """
    if len(text) <= max_size:
        return [text]

    lines = text.split("\n")
    # Pre-split long prose lines at internal sentence boundaries so the
    # break-priority algorithm has more candidates in continuous prose.
    lines = _expand_long_prose_lines(lines)
    classes = annotate_table_headers([classify_line(l) for l in lines])
    in_example = annotate_example_ranges(lines)
    table_blocks = find_table_blocks(classes)

    # Map line index → header line index for table rows in mid-table blocks.
    # Used for continued-table header repetition.
    line_to_header = {}
    for start, end, hdr in table_blocks:
        if hdr is None:
            continue
        for i in range(start, end + 1):
            if i != hdr:
                line_to_header[i] = hdr

    # Greedy walk: accumulate lines, check for forced break when size exceeds
    # MAX. When forced, look back for the best break point.
    line_lens = [len(l) + 1 for l in lines]  # +1 for the join char

    chunks_line_ranges: list[tuple[int, int]] = []
    start = 0
    cum_size = 0

    for i in range(len(lines)):
        cum_size += line_lens[i]
        # When we cross max_size, decide where to break
        if cum_size > max_size and (cum_size - line_lens[i]) >= HARD_MIN_CHUNK_SIZE:
            # We need to break somewhere in [start+1 .. i].
            # Track the best in-range candidate ([MIN..MAX] window) and
            # the best below-MIN candidate ([HARD_MIN..MIN] window) separately.
            # If the in-range best is a low-priority break (mid-list, etc.)
            # and the below-MIN has a high-priority break (entering a list,
            # sub-heading, etc.), prefer the below-MIN. This favors list
            # integrity over hitting the MIN_CHUNK_SIZE target.
            best_in_range = (-1, -1)   # (score, j)
            best_below_min = (-1, -1)
            for j in range(i, start, -1):
                window_size = sum(line_lens[k] for k in range(start, j))
                if window_size < HARD_MIN_CHUNK_SIZE:
                    break
                if window_size > max_size:
                    continue
                sc = score_break_before(j, classes, lines, in_example)
                if window_size >= min_size:
                    if sc > best_in_range[0]:
                        best_in_range = (sc, j)
                else:
                    if sc > best_below_min[0]:
                        best_below_min = (sc, j)

            in_score, in_idx = best_in_range
            sub_score, sub_idx = best_below_min

            if in_idx == -1 and sub_idx == -1:
                # No usable break — accept break right before current line
                best_idx = i
                best_score = 1
            elif in_idx == -1:
                best_idx = sub_idx
                best_score = sub_score
            elif (in_score < HIGH_PRIORITY_BREAK_SCORE
                  and sub_idx != -1
                  and sub_score >= HIGH_PRIORITY_BREAK_SCORE):
                # In-range option is mid-list / weak; below-MIN has a clean
                # structural break. Prefer the structural break.
                best_idx = sub_idx
                best_score = sub_score
            else:
                best_idx = in_idx
                best_score = in_score

            if best_score == 0:
                best_idx = i
                best_score = 1

            chunks_line_ranges.append((start, best_idx))
            start = best_idx
            # Recompute cum_size for the new chunk starting at best_idx,
            # including the current line i (since we haven't added it yet
            # to the new chunk).
            cum_size = sum(line_lens[k] for k in range(start, i + 1))

    if start < len(lines):
        chunks_line_ranges.append((start, len(lines)))

    # Build output strings, with continued-table header repetition.
    chunks = []
    for chunk_idx, (s, e) in enumerate(chunks_line_ranges):
        chunk_lines = lines[s:e]
        # Continued-table fix: if this chunk's first line is a table row that's
        # not its block's header, prepend the header (and separator if any).
        if chunk_idx > 0 and s in line_to_header:
            hdr_idx = line_to_header[s]
            prepend = [lines[hdr_idx]]
            # Include separator row if present immediately after header
            if hdr_idx + 1 < len(lines) and classes[hdr_idx + 1] == "TABLE_SEP":
                prepend.append(lines[hdr_idx + 1])
            chunk_lines = prepend + chunk_lines
        text_out = "\n".join(chunk_lines).strip()
        if text_out:
            chunks.append(text_out)

    # Second pass: any chunk still too large gets sentence-split as a last resort
    final = []
    for c in chunks:
        if len(c) <= max_size:
            final.append(c)
        else:
            final.extend(_sentence_split(c, max_size))
    return final


def _sentence_split(text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """Last-resort sentence-boundary split for chunks that exceeded max
    despite break-priority logic (typically a single huge prose paragraph)."""
    sentences = re.split(r"(?<=[.?!])\s+(?=[A-Z])", text)
    if len(sentences) <= 1:
        # Truly unsplittable — hard slice
        return [text[i:i + TARGET_CHUNK_SIZE]
                for i in range(0, len(text), TARGET_CHUNK_SIZE)]

    chunks = []
    cur = []
    cur_size = 0
    for s in sentences:
        sz = len(s)
        if cur_size + sz > max_size and cur:
            chunks.append(" ".join(cur))
            cur = []
            cur_size = 0
        cur.append(s)
        cur_size += sz + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


# ============================================================
# TABLE RENDERING
# ============================================================

def render_table(table: dict) -> str:
    """Convert a structured table dict into pipe-delimited markdown text."""
    lines = []
    headers = table.get("headers")
    rows = table.get("rows", [])

    if not rows and not headers:
        return ""

    all_rows = ([headers] if headers else []) + rows
    if not all_rows:
        return ""

    col_count = max(len(row) for row in all_rows)

    if headers:
        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        lines.append(header_line)
        lines.append(separator)

    for row in rows:
        padded = list(row) + [""] * (col_count - len(row))
        row_line = "| " + " | ".join(str(cell) for cell in padded) + " |"
        lines.append(row_line)

    return "\n".join(lines)


def append_tables(text: str, tables: list[dict]) -> str:
    """Render tables and append them to section text after a blank line."""
    if not tables:
        return text
    parts = [text.strip()]
    for table in tables:
        rendered = render_table(table)
        if rendered:
            parts.append(rendered)
    return "\n\n".join(parts)


def append_example_text(text: str, example_text: str | None) -> str:
    """
    Append the right-column example_text (from side-by-side pages) to the
    main text with a clear "Example:" prefix so it survives chunking.
    """
    if not example_text:
        return text
    cleaned = example_text.strip()
    if not cleaned:
        return text
    # If the example_text already starts with "Example", don't double-label.
    prefix = "" if cleaned.lower().startswith("example") else "Example: "
    return f"{text.strip()}\n\n{prefix}{cleaned}"


# ============================================================
# CONTEXT PREFIX
# ============================================================

# Section titles longer than this carry enough topical signal on their own;
# adding parent_section title becomes redundant and bloats the prefix at the
# cost of body chunk budget. Below the threshold (e.g., §812.2 "Standard
# Verification" = 21 chars), the parent ("School Enrollment") is the
# topical anchor the embedding needs.
PARENT_TITLE_SECTION_TITLE_THRESHOLD = 60


def build_context_prefix(chapter: int, chapter_title: str,
                         section_number: str | None = None,
                         section_title: str | None = None,
                         parent_section: str | None = None,
                         parent_title: str | None = None) -> str:
    """
    Build the hierarchical context line prepended to chunk text before
    embedding. Position-within-section info (chunk_n / chunk_total) lives
    in metadata only — consistent with OLG, CMR, and CFR.

    When a section has a meaningful `parent_section` (e.g., §812.2's parent
    is §812 "School Enrollment"), the parent's number + title is inserted
    between the chapter line and the section line so the embedding captures
    the topical anchor. Skipped when parent_title is missing, duplicates the
    chapter title, or when section_title is already long enough to convey
    its topic on its own (avoids prefix bloat that would crowd body budget).

    Example:
        FNS 310 > Chapter 8: Non-Financial Eligibility Criteria > 812 School Enrollment > 812.2 Standard Verification
    """
    parts = ["FNS 310", f"Chapter {chapter}: {chapter_title}"]

    sec_title_clean = (section_title or "").strip()
    parent_title_clean = (parent_title or "").strip()
    chapter_title_clean = chapter_title.strip()
    if (parent_section
            and parent_title_clean
            and parent_title_clean.lower() != chapter_title_clean.lower()
            and len(sec_title_clean) <= PARENT_TITLE_SECTION_TITLE_THRESHOLD):
        parts.append(f"{parent_section} {parent_title_clean}")

    if section_number and sec_title_clean:
        parts.append(f"{section_number} {sec_title_clean}")
    elif section_number:
        parts.append(section_number)

    return " > ".join(parts)


# ============================================================
# CHUNK ID GENERATION
# ============================================================

def make_chapter_id(chapter_num: int) -> str:
    return f"fns_ch{chapter_num:02d}"


def make_section_id(section_number: str, chunk_index: int) -> str:
    safe = section_number.replace(".", "_")
    return f"fns_sec_{safe}__{chunk_index:03d}"


# ============================================================
# DEFINITIONS HANDLER (modeled on CFR's chunk_definitions)
# ============================================================

# Detects a definition entry start: a capitalized term followed by either
# a dash separator (en-dash, em-dash, or hyphen with surrounding spaces)
# or a verb ("means", "is", "Is", "refers to"). Term character class is
# restrictive — letters, digits, spaces, parens, ampersand, apostrophe,
# slash, dash. Excludes comma/period/colon so the lazy match can't span
# across mid-sentence verb words like "is" in "...the income is..."
_FNS_DEFINITION_ENTRY = re.compile(
    r"^([A-Z][A-Za-z0-9()&/' \-]{2,80}?)"
    r"(?:\s+[–—]\s+|\s+-\s+|\s+(?:means|refers to|[Ii]s)\s+)"
    r"\S"
)


def _is_fns_definition_start(line: str) -> str | None:
    """Return the term name if `line` starts a new definition entry, else None."""
    stripped = line.strip()
    if not stripped:
        return None
    m = _FNS_DEFINITION_ENTRY.match(stripped)
    if not m:
        return None
    return m.group(1).strip().rstrip(".")


def chunk_fns_definitions(section: dict, body_max: int | None = None) -> list[str]:
    """
    Chunk a definitions section with one chunk per defined term. Mirrors
    CFR's chunk_definitions(): each definition becomes its own chunk,
    no matter how short. Continuation lines (sub-bullets, additional
    sentences before the next term) belong to the preceding definition.

    Returns a list of chunk body strings (no prefix yet — caller adds it).
    Oversized single definitions are split at sentence boundaries.
    `body_max` overrides the default cap; defaults to MAX_CHUNK_SIZE - PREFIX_BUDGET.
    """
    if body_max is None:
        body_max = MAX_CHUNK_SIZE - PREFIX_BUDGET
    text = section["text"]
    lines = [l for l in text.split("\n") if l.strip()]

    # Skip the section heading line if present (typically ALL CAPS, ends with `.`)
    # Heading examples: "DEFINITIONS.", "NEGATIVE DEFINITIONS."
    start_idx = 0
    if lines and re.match(r"^[A-Z][A-Z\s]*[A-Z]\.?\s*$", lines[0].strip()):
        # This is the section heading; skip
        start_idx = 1
    elif lines and lines[0].strip().endswith(".") and lines[0].strip().isupper():
        start_idx = 1

    # Group lines into definition entries
    entries = []  # list of (term_name, [lines])
    current_term = None
    current_lines = []

    for line in lines[start_idx:]:
        term = _is_fns_definition_start(line)
        if term is not None:
            if current_lines:
                entries.append((current_term, current_lines))
            current_term = term
            current_lines = [line]
        else:
            if current_lines:
                current_lines.append(line)
            else:
                # Pre-entry preamble (rare); attach to first entry once it appears
                current_lines = [line]

    if current_lines:
        entries.append((current_term, current_lines))

    # Build chunk body strings, splitting oversized definitions
    raw_chunks = []
    for term, entry_lines in entries:
        entry_text = "\n".join(entry_lines)
        if len(entry_text) <= body_max:
            raw_chunks.append(entry_text)
        else:
            parts = split_text_by_breaks(
                entry_text,
                max_size=body_max,
                min_size=MIN_CHUNK_SIZE,
            )
            raw_chunks.extend(parts)

    return raw_chunks


def _is_definitions_section(section: dict) -> bool:
    """Detect whether a section is a definitions list that should be
    handled by chunk_fns_definitions instead of split_text_by_breaks."""
    title = (section.get("section_title") or "").upper()
    return "DEFINITION" in title


# ============================================================
# CHAPTER-LEVEL DOCUMENT CREATION
# ============================================================

def create_chapter_document(chapter_num: int, chapter_title: str,
                            sections: list[dict]) -> dict:
    """Create the chapter-level document (broad-context topic discovery)."""
    context_prefix = build_context_prefix(chapter_num, chapter_title)

    parts = [context_prefix, ""]

    for section in sections:
        sec_num = section["section_number"]
        sec_title = section.get("section_title", "")
        text = section["text"].strip()
        text = append_example_text(text, section.get("example_text"))
        text = append_tables(text, section.get("tables", []))

        if sec_title:
            parts.append(f"## {sec_num} {sec_title}")
        if text:
            parts.append(text)
        parts.append("")

    full_text = "\n".join(parts).strip()

    all_pdf_pages = []
    all_handbook_pages = []
    has_tables = False
    for s in sections:
        all_pdf_pages.extend(s.get("pdf_pages", []))
        all_handbook_pages.extend(s.get("handbook_pages", []))
        if s.get("tables"):
            has_tables = True

    return {
        "chunk_id": make_chapter_id(chapter_num),
        "doc_type": "chapter",
        "text": full_text,
        "metadata": {
            "source": "FNS Handbook 310",
            "chapter": chapter_num,
            "chapter_title": chapter_title,
            "program": FNS_CHAPTER_PROGRAM.get(chapter_num, "QC_Process"),
            "section_count": len(sections),
            "has_tables": str(has_tables),
            "pdf_pages": ",".join(str(p) for p in sorted(set(all_pdf_pages))),
            "handbook_pages": ",".join(sorted(set(all_handbook_pages))),
        },
    }


# ============================================================
# SECTION-LEVEL CHUNK CREATION
# ============================================================

def create_section_chunks(chapter_num: int, chapter_title: str,
                          sections: list[dict],
                          section_title_lookup: dict[str, str] | None = None,
                          ) -> list[dict]:
    """
    Create section-level chunks. No cross-section merging — each FNS
    section becomes its own chunk (or set of split chunks if oversized).

    `section_title_lookup` maps section_number → section_title across all
    chapters; used to resolve `parent_section` titles for the chunk prefix.
    """
    chapter_id = make_chapter_id(chapter_num)
    program = FNS_CHAPTER_PROGRAM.get(chapter_num, "QC_Process")
    if section_title_lookup is None:
        section_title_lookup = {}

    chunks = []
    for section in sections:
        sec_num = section["section_number"]
        sec_title = section.get("section_title")
        parent_section_num = (section.get("parent_section") or "").strip()
        parent_title = section_title_lookup.get(parent_section_num, "")

        # Compute the actual prefix once and use its length as the body
        # budget reserve. This adapts to long section titles (legitimate)
        # and to parent_section titles that aren't a fixed 200 chars.
        prefix = build_context_prefix(
            chapter_num, chapter_title, sec_num, sec_title,
            parent_section=parent_section_num or None,
            parent_title=parent_title or None,
        )
        # +2 for the "\n\n" separator between prefix and body in chunk_text.
        body_max = max(MIN_CHUNK_SIZE * 2, MAX_CHUNK_SIZE - len(prefix) - 2)

        # Build the full body: original text + example_text + tables
        body = section["text"].strip()
        body = append_example_text(body, section.get("example_text"))
        body = append_tables(body, section.get("tables", []))
        if not body:
            continue

        # Use the definitions handler for sections whose title indicates
        # a definitions list (e.g., "DEFINITIONS", "NEGATIVE DEFINITIONS").
        # Each defined term becomes its own chunk, no matter how short.
        if _is_definitions_section(section):
            split_pieces = chunk_fns_definitions(section, body_max=body_max)
            if not split_pieces:
                # Defensive fallback: no definitions detected, treat as prose
                split_pieces = split_text_by_breaks(
                    body,
                    max_size=body_max,
                    min_size=MIN_CHUNK_SIZE,
                )
        else:
            # Split using break-priority logic. Reserve actual prefix length
            # so the final chunk_text (prefix + body) stays within MAX_CHUNK_SIZE.
            split_pieces = split_text_by_breaks(
                body,
                max_size=body_max,
                min_size=MIN_CHUNK_SIZE,
            )
        total = len(split_pieces)

        for i, piece in enumerate(split_pieces):

            # Hierarchy path: section number + title (no part-of-N suffix
            # — position info lives in chunk_n / chunk_total metadata,
            # consistent with OLG / CMR / CFR).
            if sec_title:
                hierarchy_path = f"{sec_num} {sec_title}"
            else:
                hierarchy_path = sec_num

            chunk_text = f"{prefix}\n\n{piece}"

            chunks.append({
                "chunk_id": make_section_id(sec_num, i),
                "doc_type": "section",
                "text": chunk_text,
                "metadata": {
                    "source": "FNS Handbook 310",
                    "chapter": chapter_num,
                    "chapter_title": chapter_title,
                    "program": program,
                    "section_number": sec_num,
                    "section_title": sec_title or "",
                    "hierarchy_path": hierarchy_path,
                    "chunk_n": i + 1,
                    "chunk_total": total,
                    "level": section["level"],
                    "parent_section": section.get("parent_section", "") or "",
                    "pdf_pages": ",".join(str(p) for p in section.get("pdf_pages", [])),
                    "handbook_pages": ",".join(section.get("handbook_pages", [])),
                    "flags": ",".join(section.get("flags", [])),
                    "has_tables": str(bool(section.get("tables"))),
                    "cross_references": ",".join(section.get("cross_references", [])),
                    "chunk_index": i,
                    "parent_chapter_id": chapter_id,
                },
            })

    return chunks


# ============================================================
# MAIN PROCESSING
# ============================================================

def load_all_sections() -> dict[int, list[dict]]:
    """Load all parsed section JSON files and group by chapter."""
    section_files = sorted(PARSED_DIR.glob("*.json"))
    if not section_files:
        print(f"No JSON files found in {PARSED_DIR}")
        return {}

    by_chapter: dict[int, list[dict]] = {}
    for filepath in section_files:
        with open(filepath, "r", encoding="utf-8") as f:
            section = json.load(f)
        chapter = section["chapter"]
        by_chapter.setdefault(chapter, []).append(section)

    for chapter in by_chapter:
        by_chapter[chapter].sort(key=lambda s: _sec_sort_key(s["section_number"]))
    return by_chapter


def _sec_sort_key(sec_num: str) -> tuple:
    """Sort sections by their numeric components, e.g. '154.10' > '154.2'."""
    return tuple(int(p) if p.isdigit() else p for p in sec_num.split("."))


def process_all_sections() -> tuple[list[dict], list[dict]]:
    by_chapter = load_all_sections()
    if not by_chapter:
        return [], []

    section_title_lookup: dict[str, str] = {}
    for sections in by_chapter.values():
        for s in sections:
            section_title_lookup[s["section_number"]] = s.get("section_title", "") or ""

    chapter_chunks = []
    section_chunks = []

    for chapter_num in sorted(by_chapter.keys()):
        sections = by_chapter[chapter_num]
        chapter_title = sections[0]["chapter_title"]

        chapter_doc = create_chapter_document(chapter_num, chapter_title, sections)
        chapter_chunks.append(chapter_doc)

        sec_chunks = create_section_chunks(
            chapter_num, chapter_title, sections, section_title_lookup,
        )
        section_chunks.extend(sec_chunks)

    return chapter_chunks, section_chunks


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(chapter_chunks: list[dict],
                     section_chunks: list[dict]) -> None:
    print("=" * 60)
    print("FNS Handbook 310 — Chunking Statistics")
    print("=" * 60)
    print()

    ch_sizes = [len(c["text"]) for c in chapter_chunks]
    print(f"Chapter-level documents: {len(chapter_chunks)}")
    print(f"  Median size: {statistics.median(ch_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(ch_sizes):.0f} chars")
    print(f"  Min:         {min(ch_sizes)} chars")
    print(f"  Max:         {max(ch_sizes)} chars")
    print()

    sec_sizes = [len(c["text"]) for c in section_chunks]
    print(f"Section-level chunks: {len(section_chunks)}")
    print(f"  Median size: {statistics.median(sec_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(sec_sizes):.0f} chars")
    print(f"  Min:         {min(sec_sizes)} chars")
    print(f"  Max:         {max(sec_sizes)} chars")
    print()

    buckets = [0, 100, 200, 500, 1000, 1500, 2000, 3000, 5000, 999999]
    print("Section chunk size distribution:")
    for i in range(len(buckets) - 1):
        count = sum(1 for s in sec_sizes if buckets[i] <= s < buckets[i + 1])
        pct = count / len(sec_sizes) * 100
        bar = "#" * (count // 5)
        print(f"  {buckets[i]:>5}-{buckets[i+1]:>5}: {count:>4} ({pct:4.1f}%) {bar}")
    print()

    chapters = {}
    for c in section_chunks:
        ch = c["metadata"]["chapter"]
        ch_title = c["metadata"]["chapter_title"]
        prog = c["metadata"]["program"]
        key = f"Ch {ch} [{prog}]: {ch_title}"
        chapters[key] = chapters.get(key, 0) + 1
    print("Chunks by chapter:")
    for ch, count in sorted(chapters.items()):
        print(f"  {ch:60s} {count}")
    print()

    still_small = sum(1 for s in sec_sizes if s < MIN_CHUNK_SIZE)
    still_large = sum(1 for s in sec_sizes if s > MAX_CHUNK_SIZE)
    print(f"Chunks < {MIN_CHUNK_SIZE} chars: {still_small} "
          f"({still_small/len(sec_sizes)*100:.1f}%)")
    print(f"Chunks > {MAX_CHUNK_SIZE} chars: {still_large} "
          f"({still_large/len(sec_sizes)*100:.1f}%)")
    continued = sum(1 for c in section_chunks
                    if "continued" in (c["metadata"].get("section_title") or "").lower())
    print(f"Chunks with '(continued)' in title: {continued}")
    with_hp = sum(1 for c in section_chunks if c["metadata"].get("hierarchy_path"))
    print(f"Chunks with hierarchy_path: {with_hp} / {len(section_chunks)}")
    by_program = {}
    for c in section_chunks:
        p = c["metadata"]["program"]
        by_program[p] = by_program.get(p, 0) + 1
    print(f"Chunks by program: {by_program}")


def preview_chunks(chapter_chunks: list[dict], section_chunks: list[dict],
                   count: int = 2) -> None:
    for chapter_doc in chapter_chunks[:count]:
        ch_meta = chapter_doc["metadata"]
        print("=" * 60)
        print(f"CHAPTER: {ch_meta['chapter_title']} (Chapter {ch_meta['chapter']})")
        print(f"  Length: {len(chapter_doc['text'])} chars")
        print(f"  Sections: {ch_meta['section_count']}, program={ch_meta['program']}")
        print()
        chapter_id = chapter_doc["chunk_id"]
        related = [c for c in section_chunks
                   if c["metadata"]["parent_chapter_id"] == chapter_id]
        print(f"  Section chunks: {len(related)}")
        for chunk in related:
            meta = chunk["metadata"]
            sec_num = meta["section_number"]
            sec_title = meta["section_title"] or "(no title)"
            preview = chunk["text"][:120].replace("\n", " ")
            print(f"    [{meta['level']}] {sec_num} {sec_title} "
                  f"({meta['chunk_n']}/{meta['chunk_total']})")
            print(f"        {len(chunk['text'])} chars: {preview}...")
        print()


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Chunk parsed FNS Handbook 310 sections for RAG embedding.",
    )
    parser.add_argument("--stats", action="store_true",
                        help="Show statistics only, don't write output files")
    parser.add_argument("--preview", type=int, default=0,
                        help="Preview chunks for the first N chapters")
    args = parser.parse_args()

    print(f"Reading parsed sections from {PARSED_DIR}...")
    chapter_chunks, section_chunks = process_all_sections()

    if not chapter_chunks:
        return

    print_statistics(chapter_chunks, section_chunks)

    if args.preview > 0:
        preview_chunks(chapter_chunks, section_chunks, args.preview)

    if not args.stats and not args.preview:
        with open(CHAPTER_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(chapter_chunks, f, indent=2, ensure_ascii=False)
        print(f"\nWrote {len(chapter_chunks)} chapter docs to {CHAPTER_CHUNKS_FILE}")
        with open(SECTION_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(section_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(section_chunks)} section chunks to {SECTION_CHUNKS_FILE}")


if __name__ == "__main__":
    main()
