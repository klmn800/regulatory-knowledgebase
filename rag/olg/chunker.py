"""
Chunker for DTA Online Guide RAG pipeline.

Reads the scraped page JSON files and produces two sets of chunks
for embedding:

  1. Page-level documents (one per page) — for broad topic matching
  2. Section-level chunks (granular) — for specific policy answers

The section chunker applies smart merge/split logic:
  - Tiny sections (< MIN_CHUNK_SIZE) are merged with their neighbors
  - Large sections (> MAX_CHUNK_SIZE) are split at paragraph boundaries
  - [Table] placeholders are replaced with rendered table text
  - Each chunk gets a context prefix (breadcrumb > page title > heading)
    prepended so the embedding model understands the hierarchy

Output:
  page_chunks.json    — list of page-level documents with metadata
  section_chunks.json — list of section-level chunks with metadata

Usage:
    python chunker.py                     # Process all scraped pages
    python chunker.py --stats             # Show statistics only, no output
    python chunker.py --preview 5         # Preview chunks for first 5 pages
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rag.olg.page_excludes import PAGE_EXCLUDES, CHUNK_EXCLUDES


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = PROJECT_ROOT / "index" / "olg"
SCRAPED_DIR = INDEX_DIR / "scraped_pages"
PAGE_CHUNKS_FILE = INDEX_DIR / "page_chunks.json"
SECTION_CHUNKS_FILE = INDEX_DIR / "section_chunks.json"

# Chunk size thresholds (in characters).
# Sections smaller than MIN get merged with neighbors.
# Sections larger than MAX get split at paragraph boundaries.
# TARGET is the ideal size we aim for when splitting.
MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 1500
TARGET_CHUNK_SIZE = 1000


# ============================================================
# TABLE RENDERING
# ============================================================

def render_table(table: dict) -> str:
    """
    Convert a structured table dict into readable plain text.

    Tables are rendered in a pipe-delimited format:
        | Header1 | Header2 | Header3 |
        |---------|---------|---------|
        | cell1   | cell2   | cell3   |

    If the table has no headers, the pipe format is used without
    a header row. This format is embedding-friendly — the model
    can understand the structure from the delimiters.
    """
    lines = []
    headers = table.get("headers")
    rows = table.get("rows", [])

    if not rows and not headers:
        return ""

    # Determine column widths for alignment (capped for readability)
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
        # Pad row if it has fewer columns than expected
        padded = list(row) + [""] * (col_count - len(row))
        row_line = "| " + " | ".join(str(cell) for cell in padded) + " |"
        lines.append(row_line)

    return "\n".join(lines)


def inline_tables(sections: list[dict], tables: list[dict]) -> list[dict]:
    """
    Replace [Table] placeholders in section text with rendered table data.

    Matches tables to sections using the context_heading field. When a
    section has multiple [Table] placeholders and multiple tables share
    the same context_heading, they are inserted in order.

    Returns a new list of sections with tables inlined (does not modify
    the originals).
    """
    if not tables:
        return sections

    # Group tables by their context heading
    tables_by_heading: dict[str | None, list[dict]] = {}
    for table in tables:
        key = table.get("context_heading")
        if key not in tables_by_heading:
            tables_by_heading[key] = []
        tables_by_heading[key].append(table)

    result = []
    for section in sections:
        text = section["text"]

        if "[Table]" not in text:
            result.append(section)
            continue

        # Find tables that belong to this section
        heading = section.get("heading")
        matching_tables = tables_by_heading.get(heading, [])

        # Also check None heading for intro sections
        if heading is None and None in tables_by_heading:
            matching_tables = tables_by_heading[None]

        # Replace [Table] placeholders one at a time with rendered tables
        new_text = text
        for table in matching_tables:
            rendered = render_table(table)
            if rendered:
                new_text = new_text.replace("[Table]", "\n" + rendered + "\n", 1)

        # If there are leftover [Table] markers (no matching table found),
        # remove them rather than leaving raw placeholders
        new_text = new_text.replace("[Table]", "")
        new_text = re.sub(r"\n{3,}", "\n\n", new_text).strip()

        result.append({**section, "text": new_text})

    return result


# ============================================================
# CONTEXT PREFIX
# ============================================================

def build_context_prefix(breadcrumb: list[str], page_title: str,
                         section_heading: str | None = None,
                         parent_heading: str | None = None) -> str:
    """
    Build a hierarchical context string that gets prepended to chunk
    text before embedding.

    Example output:
        "SNAP > Application Processing > Expedited Benefits > Step One"
        "COVID-19 > [Page Title] > Pandemic UC Types > PUA"  (parent + section)

    This helps the embedding model understand where this content sits
    in the policy hierarchy, improving retrieval accuracy.
    """
    parts = list(breadcrumb)

    # Add page title if it's not already the last breadcrumb element
    if page_title and (not parts or parts[-1] != page_title):
        parts.append(page_title)

    # Insert parent heading (H2) above the section heading (H3) when present
    if parent_heading and parent_heading != section_heading:
        parts.append(parent_heading)

    # Add section heading if present
    if section_heading:
        parts.append(section_heading)

    return " > ".join(parts)


# ============================================================
# CHUNK ID GENERATION
# ============================================================

def make_page_id(url: str) -> str:
    """
    Generate a stable, readable ID for a page-level document.

    Example: "page__SNAP__AppProcessing__AppSNAP_ExpeditedBenefits"
    """
    after_webhelp = url.split("WebHelp/")[-1]
    after_webhelp = re.sub(r"\.htm[l]?$", "", after_webhelp, flags=re.IGNORECASE)
    safe = after_webhelp.replace("/", "__")
    safe = re.sub(r"[^\w\-.]", "_", safe)
    return f"page__{safe}"


def make_section_id(url: str, chunk_index: int) -> str:
    """
    Generate a stable, readable ID for a section-level chunk.

    Example: "sec__SNAP__AppProcessing__AppSNAP_ExpeditedBenefits__003"
    """
    after_webhelp = url.split("WebHelp/")[-1]
    after_webhelp = re.sub(r"\.htm[l]?$", "", after_webhelp, flags=re.IGNORECASE)
    safe = after_webhelp.replace("/", "__")
    safe = re.sub(r"[^\w\-.]", "_", safe)
    return f"sec__{safe}__{chunk_index:03d}"


# ============================================================
# PARENT HEADING TRACKING
# ============================================================

def add_parent_headings(sections: list[dict]) -> list[dict]:
    """
    Walk the section list and stamp each H3 with its parent H2's heading.

    The parser emits sections in document order with `level` in {0, 2, 3}.
    Adjacency in the list = adjacency in the source HTML, so the most
    recent level-2 we've seen is the parent of any subsequent level-3.

    H4/H5/H6 are absent in OLG (verified 2026-04-29), so this two-level
    tracking is sufficient. Level-0 (intro before first heading) and
    level-2 sections get parent_heading=None.
    """
    current_h2 = None
    result = []
    for section in sections:
        level = section.get("level", 0)
        if level == 2:
            current_h2 = section.get("heading")
            parent = None
        elif level == 3:
            parent = current_h2
        else:
            parent = None
        result.append({**section, "parent_heading": parent})
    return result


# ============================================================
# SMART MERGE LOGIC
# ============================================================

def merge_small_sections(sections: list[dict]) -> list[dict]:
    """
    Merge tiny sections (< MIN_CHUNK_SIZE) with their neighbors, with
    cross-level merge protection.

    Rule (post-cleanup 2026-04-29): merging is only allowed when one
    side is heading-less — i.e. the level-0 intro section before the
    first H2/H3. This prevents the "subsection-merge contamination"
    bug where a tiny H2 intro absorbed its first H3 child, putting the
    H3 heading into the body as a bare line and inheriting the wrong
    heading.

    Concrete bug avoided (`COVID_ProcPandUCInc`): H2 "Pandemic UC Types"
    had only ~150 chars of intro, so it used to merge forward into H3
    "PUA" — the merged chunk carried the H2 heading but the body was
    PUA's content, with the H3 heading as a bare paragraph.

    Per Ben's L92/95 instruction: small chunks are fine. There's no onus
    to fill chunks. A tiny H3 stays a tiny H3.

    Section `links` and `parent_heading` travel through merges intact.
    "Related Topics" sections no longer reach this function — they're
    lifted to a top-level field by the parser.
    """
    if len(sections) <= 1:
        return sections

    result = []
    i = 0

    while i < len(sections):
        section = sections[i]
        text = section["text"]

        # If this section is large enough, keep it
        if len(text) >= MIN_CHUNK_SIZE:
            result.append(section)
            i += 1
            continue

        heading = section.get("heading")

        # This section is too small — try to merge forward, but only when
        # one side has no heading (i.e. it's the level-0 intro). Two
        # heading-bearing sections never merge.
        if i + 1 < len(sections):
            next_section = sections[i + 1]
            next_heading = next_section.get("heading")

            if not heading or not next_heading:
                merged_text = _combine_text(
                    heading, text,
                    next_heading, next_section["text"]
                )
                merged = {
                    "heading": heading or next_heading,
                    "level": min(section["level"], next_section["level"]) if section["level"] > 0 else next_section["level"],
                    "text": merged_text,
                    "links": _merge_links(section.get("links", []), next_section.get("links", [])),
                    "parent_heading": next_section.get("parent_heading") if next_heading else section.get("parent_heading"),
                }
                sections[i + 1] = merged
                i += 1
                continue

        # Last section and too small — merge backward into previous,
        # again only if one side is heading-less.
        if result:
            prev = result[-1]
            prev_heading = prev.get("heading")
            if not prev_heading or not heading:
                merged_text = _combine_text(
                    prev_heading, prev["text"],
                    heading, text
                )
                result[-1] = {
                    **prev,
                    "heading": prev_heading or heading,
                    "text": merged_text,
                    "links": _merge_links(prev.get("links", []), section.get("links", [])),
                }
                i += 1
                continue

        # Can't merge across heading boundaries — small section stays small.
        result.append(section)
        i += 1

    return result


def _merge_links(a: list[dict], b: list[dict]) -> list[dict]:
    """Concatenate two link lists, deduping by href."""
    seen = set()
    merged = []
    for link in list(a) + list(b):
        href = link.get("href")
        if href and href not in seen:
            seen.add(href)
            merged.append(link)
    return merged


def _combine_text(heading_a: str | None, text_a: str,
                  heading_b: str | None, text_b: str) -> str:
    """
    Combine two section texts when one side is heading-less (level-0 intro).

    With the cross-level merge protection in `merge_small_sections()`, exactly
    one of `heading_a` / `heading_b` is set; the merged section's heading
    field captures it, and the context prefix renders it. We do NOT insert
    the heading inline as a body separator — that produced the §1A pattern
    where the heading appeared as a bare text line in the chunk body.
    """
    parts = []
    if text_a.strip():
        parts.append(text_a.strip())
    if text_b.strip():
        parts.append(text_b.strip())
    return "\n\n".join(parts)


# ============================================================
# SMART SPLIT LOGIC
# ============================================================

# Line classifier patterns — applied in order. Each line is exactly one kind.
_LINE_PATTERNS = [
    ("table_sep", re.compile(r"^\|\s*-+.*\|\s*$")),       # | --- | --- |
    ("table_row", re.compile(r"^\|.*\|\s*$")),             # | cell | cell |
    ("numbered",  re.compile(r"^\d+\.\s+\S")),             # 1. text
    ("paren_num", re.compile(r"^\(\d+\)\s+\S")),           # (1) text
    ("alpha",     re.compile(r"^[A-Z]\.\s+\S")),           # A. text
    ("bullet",    re.compile(r"^[-*]\s+\S")),              # - text   * text
]

_LIST_KINDS = {"numbered", "paren_num", "alpha", "bullet"}
_TABLE_KINDS = {"table_row", "table_sep"}

# Logged as a side effect so we can audit which sections still hit the
# oversized-line passthrough after the splitter rewrite.
_oversized_line_warnings: list[str] = []


def classify_line(line: str) -> tuple[str, int]:
    """
    Return (kind, indent) where indent is the count of leading spaces.

    kind is one of: blank, table_sep, table_row, numbered, paren_num,
    alpha, bullet, prose. Indent matters for list items: a "  a. sub"
    line (indent=2) is a child of a "1. parent" line (indent=0) and
    should not be split away from it. The splitter uses indent to
    decide whether a list-item line is a top-of-block flush boundary
    or a sub-item that must stay with its parent.
    """
    indent = len(line) - len(line.lstrip(" "))
    stripped = line.strip()
    if not stripped:
        return ("blank", 0)
    for kind, pat in _LINE_PATTERNS:
        if pat.match(stripped):
            return (kind, indent)
    return ("prose", indent)


def _is_header_only(lines: list[str]) -> bool:
    """
    True if `lines` contains only table header content (one table_row +
    optionally a table_sep), with no data rows or other content.
    """
    non_blank = [l for l in lines if l.strip()]
    if not non_blank or len(non_blank) > 2:
        return False
    kinds = [classify_line(l)[0] for l in non_blank]
    if kinds == ["table_row"]:
        return True
    if kinds == ["table_row", "table_sep"]:
        return True
    return False


def split_large_section(section: dict) -> list[dict]:
    """
    Split a section that exceeds MAX_CHUNK_SIZE using a line-classifier
    walker. Break-point preference (highest to lowest):

      1. Start of a new table block (flush prose/list content before the
         table starts so the table's header opens a fresh chunk)
      2. Table row boundary (between rows; never inside a row)
      3. List item boundary (numbered, paren_num, alpha, or bullet line)
      4. Paragraph boundary (blank line)
      5. Sentence boundary inside a single prose paragraph
      6. Oversized single line (e.g. a giant table row) — emitted as one
         chunk that exceeds MAX_CHUNK_SIZE, with a warning logged. Voyage-3
         has ample token room; preserving the row's logical integrity beats
         slicing it.

    Header continuity for tables:
      - When a table is split across chunks, the table's header row +
        separator are auto-prepended to every continuation chunk so the
        chunk stands alone.
      - A chunk that would consist only of a table header (no data rows)
        is never emitted; the header is held and carried forward.

    Each split chunk gets:
      - heading: always the original section heading (no "(continued)" —
        position is conveyed by chunk_n / chunk_total)
      - level, parent_heading, links: inherited from the parent
      - chunk_n / chunk_total: 1-indexed position within this section's
        split sequence
    """
    text = section["text"]

    if len(text) <= MAX_CHUNK_SIZE:
        return [{
            **section,
            "chunk_n": 1,
            "chunk_total": 1,
        }]

    lines = text.split("\n")
    classified = [(line,) + classify_line(line) for line in lines]

    chunks: list[list[str]] = []
    current: list[str] = []
    current_size = 0
    in_table_run = False
    active_header: list[str] = []  # most recent [header_row, sep] for the table

    # Smallest indent of any list-item line currently in `current`. None when
    # the buffer holds no list items. Used to decide whether a new list-item
    # line is a flushable top-of-block boundary or a deeper sub-child that
    # must stay with the parent already accumulated.
    buffer_min_list_indent: int | None = None

    def _recompute_min_list_indent(buf: list[str]) -> int | None:
        result: int | None = None
        for ln in buf:
            k, ind = classify_line(ln)
            if k in _LIST_KINDS:
                if result is None or ind < result:
                    result = ind
        return result

    def flush():
        """
        Emit `current` as a chunk and reset. If `current` is just a table
        header (no data), hold it instead — the header carries forward
        into the next chunk.
        """
        nonlocal current, current_size, buffer_min_list_indent
        if not current:
            return
        # Trim trailing blanks
        while current and not current[-1].strip():
            current.pop()
        if not current:
            current_size = 0
            buffer_min_list_indent = None
            return
        # Don't emit header-only chunks — hold and let the next data row join
        if _is_header_only(current):
            return
        chunks.append(list(current))
        current = []
        current_size = 0
        buffer_min_list_indent = None
        # If we just flushed mid-table, prepend the active header so the
        # continuation chunk includes it.
        if in_table_run and active_header:
            for h in active_header:
                current.append(h)
                current_size += len(h) + 1

    def split_flush_at_top_level() -> bool:
        """
        Split current at the last top-of-block list-item boundary so the
        emitted "head" is everything before that boundary, and `current`
        becomes the trailing "tail" (parent step + any accumulated
        children). Used when must_flush triggers on a deep sub-item — we
        keep the parent step with its kids in the next chunk instead of
        ejecting all of current as one big chunk that orphans the kids.

        Returns True if the split happened, False if no usable split
        point exists (caller falls back to plain flush).
        """
        nonlocal current, current_size, buffer_min_list_indent
        if buffer_min_list_indent is None:
            return False
        split_idx: int | None = None
        # Walk backward; idx 0 is not a usable split (would emit empty head).
        for idx in range(len(current) - 1, 0, -1):
            k, ind = classify_line(current[idx])
            if k in _LIST_KINDS and ind == buffer_min_list_indent:
                split_idx = idx
                break
        if split_idx is None:
            return False
        head = current[:split_idx]
        tail = current[split_idx:]
        while head and not head[-1].strip():
            head.pop()
        if head and not _is_header_only(head):
            chunks.append(list(head))
        current = list(tail)
        current_size = sum(len(l) + 1 for l in current)
        buffer_min_list_indent = _recompute_min_list_indent(current)
        return True

    def _peek_next_non_blank(start_idx: int) -> tuple[str, int] | None:
        """Return (kind, indent) of the next non-blank line at or after
        start_idx, or None if there isn't one."""
        for j in range(start_idx, len(classified)):
            _, k, ind = classified[j]
            if k != "blank":
                return (k, ind)
        return None

    for i, (line, kind, indent) in enumerate(classified):
        line_size = len(line) + 1

        # Detect "start of new table" BEFORE updating in_table_run state.
        # This is the case where the current line is a table_row but the
        # previous accumulated line was non-table — the table is starting
        # fresh and we want to flush the prose preamble before its header.
        starting_new_table = (
            kind == "table_row"
            and not in_table_run
            and bool(current)
        )

        # Update table-run state and capture active header
        if kind == "table_row":
            in_table_run = True
        elif kind == "table_sep":
            in_table_run = True
            # The line above us in `current` is the table's header row
            if current and classify_line(current[-1])[0] == "table_row":
                active_header = [current[-1], line]
        elif kind == "blank":
            in_table_run = False
            active_header = []
        # prose/list lines don't change in_table_run state until next blank

        # Skip leading blanks at the start of an empty chunk
        if not current and kind == "blank":
            continue

        new_size = current_size + line_size
        must_flush = new_size > MAX_CHUNK_SIZE and bool(current)
        prefer_flush = False

        if starting_new_table and current_size >= MIN_CHUNK_SIZE:
            # Flush prose/list content before the table's header so the
            # header opens a new chunk rather than dangling at the end.
            prefer_flush = True

        if current and current_size >= TARGET_CHUNK_SIZE:
            if kind == "blank":
                # Paragraph boundary — usually a good flush point, but
                # peek ahead: if the next non-blank line is a list-item
                # deeper than the parent we've already accumulated, the
                # blank separates a parent from its sub-children. Don't
                # split them across chunks.
                next_lookup = _peek_next_non_blank(i + 1)
                holds_for_subitem = (
                    next_lookup is not None
                    and next_lookup[0] in _LIST_KINDS
                    and buffer_min_list_indent is not None
                    and next_lookup[1] > buffer_min_list_indent
                )
                if not holds_for_subitem:
                    prefer_flush = True
            elif kind in _LIST_KINDS and not in_table_run:
                # Only flush at a list-item boundary if this item is at
                # the top-of-block level (or shallower) for what's already
                # in the buffer. A deeper-indented item is a sub-child
                # of the parent we just accumulated — don't strand it.
                if (buffer_min_list_indent is None
                        or indent <= buffer_min_list_indent):
                    prefer_flush = True

        if must_flush:
            # If we'd be orphaning a deep sub-item from its parent, try
            # to split before the last top-of-block boundary so parent +
            # accumulated children stay together.
            if (kind in _LIST_KINDS
                    and buffer_min_list_indent is not None
                    and indent > buffer_min_list_indent):
                if not split_flush_at_top_level():
                    flush()
            else:
                flush()
        elif prefer_flush:
            flush()

        current.append(line)
        current_size += line_size
        if kind in _LIST_KINDS:
            if buffer_min_list_indent is None or indent < buffer_min_list_indent:
                buffer_min_list_indent = indent

    flush()

    # Convert each line list into a chunk text string
    chunk_texts: list[str] = []
    for chunk_lines in chunks:
        chunk_text = "\n".join(chunk_lines).strip()
        if chunk_text and not _is_header_only(chunk_lines):
            chunk_texts.append(chunk_text)

    # Second pass: oversize prose chunks get sentence-split. Oversize table
    # chunks are passed through with a warning.
    final_chunks: list[str] = []
    for chunk_text in chunk_texts:
        if len(chunk_text) <= MAX_CHUNK_SIZE:
            final_chunks.append(chunk_text)
            continue

        chunk_lines = chunk_text.split("\n")
        kinds = {classify_line(l)[0] for l in chunk_lines if l.strip()}
        if kinds & _TABLE_KINDS:
            _oversized_line_warnings.append(
                f"oversize table chunk ({len(chunk_text)} chars) in section "
                f"heading={section.get('heading')!r}"
            )
            final_chunks.append(chunk_text)
            continue

        sentences = re.split(r"(?<=[.?!])\s+(?=[A-Z])", chunk_text)
        if len(sentences) > 1:
            final_chunks.extend(_group_segments(sentences, separator=" "))
        else:
            _oversized_line_warnings.append(
                f"oversize prose chunk ({len(chunk_text)} chars), no "
                f"sentence boundaries, in heading={section.get('heading')!r}"
            )
            final_chunks.append(chunk_text)

    # Build per-chunk dicts. Heading stays original on all chunks; position
    # is conveyed by chunk_n / chunk_total in metadata.
    heading = section.get("heading")
    level = section["level"]
    parent_links = section.get("links", [])
    parent_heading = section.get("parent_heading")
    total = len(final_chunks)
    result = []
    for i, chunk_text in enumerate(final_chunks):
        result.append({
            "heading": heading,
            "level": level,
            "text": chunk_text,
            "links": parent_links,
            "parent_heading": parent_heading,
            "chunk_n": i + 1,
            "chunk_total": total,
        })

    return result


def _group_segments(segments: list[str], separator: str = "\n\n") -> list[str]:
    """
    Greedily group text segments into chunks around TARGET_CHUNK_SIZE,
    not exceeding MAX_CHUNK_SIZE when possible.
    """
    chunks = []
    current_parts = []
    current_size = 0

    for segment in segments:
        seg_size = len(segment)

        if current_size + seg_size > MAX_CHUNK_SIZE and current_parts:
            chunks.append(separator.join(current_parts))
            current_parts = []
            current_size = 0

        current_parts.append(segment)
        current_size += seg_size

    if current_parts:
        chunks.append(separator.join(current_parts))

    return chunks


# ============================================================
# PAGE-LEVEL DOCUMENT CREATION
# ============================================================

def create_page_document(page_data: dict, sections_with_tables: list[dict]) -> dict:
    """
    Create a page-level document by concatenating all section text
    with headings. This is the broad-context document used for topic
    discovery.
    """
    url = page_data["url"]
    breadcrumb = page_data.get("breadcrumb", [])
    title = page_data.get("title", "")
    program = page_data.get("program", "")

    # Build the full page text with heading markers
    parts = []
    context_prefix = build_context_prefix(breadcrumb, title)
    parts.append(context_prefix)
    parts.append("")  # blank line after prefix

    for section in sections_with_tables:
        heading = section.get("heading")
        if heading:
            parts.append(f"## {heading}")
        if section["text"].strip():
            parts.append(section["text"].strip())
        parts.append("")  # blank line between sections

    full_text = "\n".join(parts).strip()

    return {
        "chunk_id": make_page_id(url),
        "doc_type": "page",
        "text": full_text,
        "metadata": {
            "url": url,
            "program": program,
            "breadcrumb": " > ".join(breadcrumb),
            "title": title,
            "last_updated": page_data.get("last_updated"),
            "section_count": len(sections_with_tables),
            "has_tables": bool(page_data.get("tables")),
            "related_pages": page_data.get("related_pages", []),
        },
    }


# ============================================================
# SECTION-LEVEL CHUNK CREATION
# ============================================================

def create_section_chunks(page_data: dict, sections_with_tables: list[dict]) -> list[dict]:
    """
    Create section-level chunks from a page's sections, applying
    merge/split logic and adding context prefixes.

    This is the main chunking pipeline:
    1. Merge tiny sections with neighbors
    2. Split oversized sections at paragraph boundaries
    3. Add context prefix (breadcrumb > title > heading)
    4. Attach metadata
    """
    url = page_data["url"]
    breadcrumb = page_data.get("breadcrumb", [])
    title = page_data.get("title", "")
    program = page_data.get("program", "")
    page_id = make_page_id(url)

    # Step 0: Stamp each H3 with its parent H2 heading (no parser change needed)
    sections_with_parents = add_parent_headings(sections_with_tables)

    # Step 1: Merge small sections (cross-level merge protection applies)
    merged = merge_small_sections(sections_with_parents)

    # Step 2: Split large sections with hierarchy-aware walker
    split_sections = []
    for section in merged:
        split_sections.extend(split_large_section(section))

    # Step 3: Build chunks with context prefixes and metadata
    chunks = []
    for i, section in enumerate(split_sections):
        heading = section.get("heading")
        parent_heading = section.get("parent_heading")
        text = section["text"].strip()

        if not text:
            continue

        # Build context prefix and prepend to text
        prefix = build_context_prefix(breadcrumb, title, heading, parent_heading)
        chunk_text = f"{prefix}\n\n{text}"

        # Filter the section's links down to those whose anchor text actually
        # appears in this chunk's text.
        section_links = section.get("links", [])
        outbound_links = [
            link for link in section_links
            if link.get("text") and link["text"] in chunk_text
        ]

        chunk = {
            "chunk_id": make_section_id(url, i),
            "doc_type": "section",
            "text": chunk_text,
            "metadata": {
                "url": url,
                "program": program,
                "breadcrumb": " > ".join(breadcrumb),
                "page_title": title,
                "section_heading": heading,
                "parent_heading": parent_heading,
                "section_level": section["level"],
                "last_updated": page_data.get("last_updated"),
                "chunk_index": i,
                "chunk_n": section.get("chunk_n", 1),
                "chunk_total": section.get("chunk_total", 1),
                "parent_page_id": page_id,
                "outbound_links": outbound_links,
            },
        }
        chunks.append(chunk)

    return chunks


# ============================================================
# MAIN PROCESSING
# ============================================================

def process_all_pages() -> tuple[list[dict], list[dict]]:
    """
    Process all scraped page files and return (page_chunks, section_chunks).
    """
    page_files = sorted(SCRAPED_DIR.glob("*.json"))

    if not page_files:
        print(f"No JSON files found in {SCRAPED_DIR}")
        return [], []

    page_chunks = []
    section_chunks = []
    excluded_count = 0

    for page_file in page_files:
        if page_file.name in PAGE_EXCLUDES:
            excluded_count += 1
            continue

        with open(page_file, "r", encoding="utf-8") as f:
            page_data = json.load(f)

        sections = page_data.get("sections", [])
        tables = page_data.get("tables", [])

        # Step 0: Inline tables into section text
        sections_with_tables = inline_tables(sections, tables)

        # Create page-level document
        page_doc = create_page_document(page_data, sections_with_tables)
        page_chunks.append(page_doc)

        # Create section-level chunks
        sec_chunks = create_section_chunks(page_data, sections_with_tables)
        section_chunks.extend(sec_chunks)

    if CHUNK_EXCLUDES:
        before = len(section_chunks)
        section_chunks = [c for c in section_chunks if c["chunk_id"] not in CHUNK_EXCLUDES]
        chunk_drop = before - len(section_chunks)
    else:
        chunk_drop = 0

    if excluded_count or chunk_drop:
        print(f"Excluded {excluded_count} pages and {chunk_drop} chunks via page_excludes.py")

    return page_chunks, section_chunks


def print_statistics(page_chunks: list[dict], section_chunks: list[dict]) -> None:
    """Print a summary of the chunking results."""
    print("=" * 60)
    print("Chunking Statistics")
    print("=" * 60)
    print()

    # Page-level stats
    page_sizes = [len(c["text"]) for c in page_chunks]
    print(f"Page-level documents: {len(page_chunks)}")
    print(f"  Median size: {statistics.median(page_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(page_sizes):.0f} chars")
    print(f"  Min:         {min(page_sizes)} chars")
    print(f"  Max:         {max(page_sizes)} chars")
    print()

    # Section-level stats
    sec_sizes = [len(c["text"]) for c in section_chunks]
    print(f"Section-level chunks: {len(section_chunks)}")
    print(f"  Median size: {statistics.median(sec_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(sec_sizes):.0f} chars")
    print(f"  Min:         {min(sec_sizes)} chars")
    print(f"  Max:         {max(sec_sizes)} chars")
    print()

    # Size distribution
    buckets = [0, 100, 200, 500, 1000, 1500, 2000, 3000, 5000, 999999]
    print("Section chunk size distribution:")
    for i in range(len(buckets) - 1):
        count = sum(1 for s in sec_sizes if buckets[i] <= s < buckets[i + 1])
        pct = count / len(sec_sizes) * 100
        bar = "#" * (count // 15)
        print(f"  {buckets[i]:>5}-{buckets[i+1]:>5}: {count:>4} ({pct:4.1f}%) {bar}")
    print()

    # Program distribution
    programs = {}
    for c in section_chunks:
        prog = c["metadata"]["program"]
        programs[prog] = programs.get(prog, 0) + 1
    print("Chunks by program:")
    for prog, count in sorted(programs.items(), key=lambda x: -x[1]):
        print(f"  {prog:25s} {count}")
    print()

    # Chunks that are still small (after merging)
    still_small = sum(1 for s in sec_sizes if s < MIN_CHUNK_SIZE)
    still_large = sum(1 for s in sec_sizes if s > MAX_CHUNK_SIZE)
    print(f"Chunks still < {MIN_CHUNK_SIZE} chars after merge: {still_small} ({still_small/len(sec_sizes)*100:.1f}%)")
    print(f"Chunks still > {MAX_CHUNK_SIZE} chars after split: {still_large} ({still_large/len(sec_sizes)*100:.1f}%)")


def preview_chunks(page_chunks: list[dict], section_chunks: list[dict],
                   count: int = 5) -> None:
    """Preview chunks for the first N pages."""
    # Get unique page IDs from first N page chunks
    page_ids = [c["chunk_id"] for c in page_chunks[:count]]

    for page_id in page_ids:
        page_doc = next(c for c in page_chunks if c["chunk_id"] == page_id)
        print("=" * 60)
        print(f"PAGE: {page_doc['metadata']['title']}")
        print(f"  Program: {page_doc['metadata']['program']}")
        print(f"  Breadcrumb: {page_doc['metadata']['breadcrumb']}")
        print(f"  Page text length: {len(page_doc['text'])} chars")
        print()

        # Find section chunks for this page
        related = [c for c in section_chunks
                   if c["metadata"]["parent_page_id"] == page_id]
        print(f"  Section chunks: {len(related)}")
        for chunk in related:
            heading = chunk["metadata"]["section_heading"] or "(intro)"
            text_preview = chunk["text"][:120].replace("\n", " ")
            print(f"    [{chunk['metadata']['section_level']}] {heading}")
            print(f"        {len(chunk['text'])} chars: {text_preview}...")
        print()


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the chunker."""
    parser = argparse.ArgumentParser(
        description="Chunk scraped DTA policy pages for RAG embedding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chunker.py                  # Process all pages, write output
  python chunker.py --stats          # Show statistics only
  python chunker.py --preview 5      # Preview chunks for 5 pages
        """,
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show statistics only, don't write output files",
    )
    parser.add_argument(
        "--preview", type=int, default=0,
        help="Preview chunks for the first N pages",
    )
    args = parser.parse_args()

    print(f"Reading scraped pages from {SCRAPED_DIR}...")
    page_chunks, section_chunks = process_all_pages()

    if not page_chunks:
        return

    print_statistics(page_chunks, section_chunks)

    if args.preview > 0:
        preview_chunks(page_chunks, section_chunks, args.preview)

    if not args.stats and not args.preview:
        # Write output files
        with open(PAGE_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(page_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(page_chunks)} page documents to {PAGE_CHUNKS_FILE}")

        with open(SECTION_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(section_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(section_chunks)} section chunks to {SECTION_CHUNKS_FILE}")


if __name__ == "__main__":
    main()
