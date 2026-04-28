"""
Chunker for 106 CMR RAG pipeline.

Reads the parsed section JSON files and produces two sets of chunks
for embedding:

  1. Chapter-level documents (one per CMR chapter) — for broad topic matching
  2. Section-level chunks (granular) — for specific regulatory answers

The section chunker applies smart merge/split logic:
  - Tiny sections (< MIN_CHUNK_SIZE) are merged with their neighbors
  - Large sections (> MAX_CHUNK_SIZE) are split at paragraph boundaries
  - Tables are rendered as pipe-delimited text and appended
  - Each chunk gets a context prefix (106 CMR > Chapter > Section)
    prepended so the embedding model understands the hierarchy

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
INDEX_DIR = PROJECT_ROOT / "index" / "cmr"
PARSED_DIR = INDEX_DIR / "parsed_sections"
CHAPTER_CHUNKS_FILE = INDEX_DIR / "chapter_chunks.json"
SECTION_CHUNKS_FILE = INDEX_DIR / "section_chunks.json"

MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 1500
TARGET_CHUNK_SIZE = 1000

# Sections excluded from section-level indexing (kept in chapter-level only).
# 364.990 is a pure numerical proration table — 39 chunks of benefit amounts
# with no regulatory content. It floods search results for generic SNAP queries.
# Sections excluded from section-level indexing (kept in chapter-level only).
# 364.990: Pure numerical proration table, floods search results
# 704.410/420/440: Website pointer stubs with zero regulatory content
SECTION_EXCLUDES = {"364.990", "704.410", "704.420", "704.440"}


# ============================================================
# HIERARCHY PROFILES
# ============================================================

# CMR legal text hierarchy markers — validated against all 592 sections.
# Level 1 expanded to {1,2} letters for (AA)-(MM) in 701.600/704.250.
# Level 2 restricted to {1,2} digits to exclude phone area codes like (866).
CMR_HIERARCHY = [
    (1, re.compile(r"^\([A-Z]{1,2}\)\s+(.+)")),   # (A) Topic or (AA) Definition
    (2, re.compile(r"^\(\d{1,2}\)\s+(.+)")),       # (1) Sub-topic
    (3, re.compile(r"^\([a-z]\)\s+(.+)")),          # (a) detail
    (4, re.compile(r"^\d+\.\s+(.+)")),              # 1. item
]


def classify_line(line: str, hierarchy_profile: list) -> tuple:
    """Return (level, label_text) or (None, None) for a line."""
    for level, pattern in hierarchy_profile:
        if pattern.match(line):
            return level, line
    return None, None


def _normalize_line_breaks(text: str, hierarchy_profile: list = None) -> str:
    """
    Clean up PDF line-wrap artifacts in chunk text.

    - Joins mid-sentence line wraps into spaces
    - Preserves line breaks before hierarchy markers for readability
    - Strips continuation page artifacts like "327.220 : continued"
    """
    if hierarchy_profile is None:
        hierarchy_profile = CMR_HIERARCHY

    # Strip continuation artifacts (e.g., "327.220 : continued")
    text = re.sub(r"\n\d{3}\.\d{3}\s*:\s*continued\b", "", text, flags=re.IGNORECASE)

    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    parts = [lines[0]]
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Keep line break before hierarchy markers
        is_marker = any(p.match(stripped) for _, p in hierarchy_profile)
        if is_marker:
            parts.append("\n" + stripped)
        else:
            parts.append(" " + stripped)

    return "".join(parts)


def _truncate_hierarchy_label(label: str, max_len: int = 80) -> str:
    """
    Extract a concise topic label from a hierarchy marker line.

    "(D) Vehicles." → "(D) Vehicles."
    "(E) Income Producing Property. Income producing property is..."
        → "(E) Income Producing Property."
    "(H) The Department's agent shall make a very long determination..."
        → "(H) The Department's agent shall make a very long dete..."
    """
    if len(label) <= max_len:
        return label
    # Try to truncate at the first sentence boundary after the marker
    period_pos = label.find(".", 4)  # Skip past (X) marker
    if 0 < period_pos < max_len:
        return label[:period_pos + 1]
    return label[:max_len - 3] + "..."


# ============================================================
# TABLE RENDERING
# ============================================================

def render_table(table: dict) -> str:
    """Convert a structured table dict into pipe-delimited text."""
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
    """Render tables and append them to the section text."""
    if not tables:
        return text

    parts = [text.strip()]
    for table in tables:
        rendered = render_table(table)
        if rendered:
            parts.append(rendered)

    return "\n\n".join(parts)


# ============================================================
# CONTEXT PREFIX
# ============================================================

def build_context_prefix(chapter: int, chapter_title: str,
                         section_number: str | None = None,
                         section_title: str | None = None,
                         hierarchy_path: str | None = None) -> str:
    """
    Build a hierarchical context string prepended to chunk text.

    Examples:
      "106 CMR 362 > SNAP Nonfinancial Eligibility > 362.330 Good Cause Criteria"
      "106 CMR 703 > NONFINANCIAL > 703.192 EAEDC Medical Standards > (D) Cardiovascular System"
    """
    title_short = chapter_title
    if ":" in title_short:
        title_short = title_short.split(":", 1)[1].strip()
    if len(title_short) > 60:
        title_short = title_short[:57] + "..."

    parts = [f"106 CMR {chapter}", title_short]

    if section_number and section_title:
        parts.append(f"{section_number} {section_title}")
    elif section_number:
        parts.append(section_number)

    if hierarchy_path:
        parts.append(hierarchy_path)

    return " > ".join(parts)


# ============================================================
# CHUNK ID GENERATION
# ============================================================

def make_chapter_id(chapter_num: int) -> str:
    """Example: "cmr_ch362" """
    return f"cmr_ch{chapter_num}"


def make_section_id(section_number: str, chunk_index: int) -> str:
    """Example: "cmr_sec_362_330__000" """
    safe = section_number.replace(".", "_")
    return f"cmr_sec_{safe}__{chunk_index:03d}"


# ============================================================
# SMART MERGE LOGIC
# ============================================================

def merge_small_sections(sections: list[dict]) -> list[dict]:
    """
    Merge tiny sections (< MIN_CHUNK_SIZE) with their neighbors.
    Single-pass forward merge within a chapter.
    """
    if len(sections) <= 1:
        return sections

    result = []
    i = 0

    while i < len(sections):
        section = sections[i]
        text = section["text"]

        if len(text) >= MIN_CHUNK_SIZE:
            result.append(section)
            i += 1
            continue

        if i + 1 < len(sections):
            next_section = sections[i + 1]
            merged_text = _combine_text(
                section.get("section_title"), text,
                next_section.get("section_title"), next_section["text"]
            )
            merged = {
                **next_section,
                "section_title": section["section_title"] or next_section["section_title"],
                "section_number": section["section_number"],
                "text": merged_text,
            }
            sections[i + 1] = merged
            i += 1
            continue

        if result:
            prev = result[-1]
            merged_text = _combine_text(
                prev.get("section_title"), prev["text"],
                section.get("section_title"), text
            )
            result[-1] = {**prev, "text": merged_text}
            i += 1
            continue

        result.append(section)
        i += 1

    return result


def _combine_text(title_a: str | None, text_a: str,
                  title_b: str | None, text_b: str) -> str:
    """Combine two section texts, preserving the second's title as context."""
    parts = []
    if text_a.strip():
        parts.append(text_a.strip())
    if title_b:
        parts.append(f"{title_b}")
    if text_b.strip():
        parts.append(text_b.strip())
    return "\n\n".join(parts)


# ============================================================
# SMART SPLIT LOGIC
# ============================================================

def split_with_hierarchy(section: dict,
                         hierarchy_profile: list = None) -> list[dict]:
    """
    Split a section using hierarchy-aware boundaries.

    Prefers to break at top-level hierarchy markers (e.g., (A), (B))
    when the accumulator has reached MIN_CHUNK_SIZE. Falls back to
    size-only splitting for sections with no hierarchy markers.

    Each output chunk carries:
      hierarchy_label  — top-level marker text (e.g., "(D) Vehicles") or None
      chunk_n          — 1-indexed position within the section
      chunk_total      — total chunks for this section
    """
    if hierarchy_profile is None:
        hierarchy_profile = CMR_HIERARCHY

    text = section["text"]

    if len(text) <= MAX_CHUNK_SIZE:
        return [{
            **section,
            "hierarchy_label": None,
            "chunk_n": 1,
            "chunk_total": 1,
        }]

    lines = [l for l in text.split("\n") if l.strip()]

    # Classify each line
    classified = []
    for line in lines:
        level, label = classify_line(line, hierarchy_profile)
        classified.append((line, level, label))

    # Pre-scan: find the top (lowest number) hierarchy level present
    levels_present = [level for _, level, _ in classified if level is not None]
    if not levels_present:
        return _split_by_size_only(section, lines)

    top_level = min(levels_present)

    # Accumulate with hierarchy-aware breaks
    current_lines = []
    current_size = 0
    current_label = None
    hierarchy_state = {}
    raw_chunks = []

    for line, level, label in classified:
        line_size = len(line) + 1  # +1 for \n join

        # Update hierarchy tracking
        if level is not None:
            hierarchy_state[level] = label
            for l in range(level + 1, 6):
                hierarchy_state.pop(l, None)

        # Decide whether to start a new chunk
        must_break = (current_size + line_size > MAX_CHUNK_SIZE) and current_lines
        # Prefer break at top-level markers always, and at one level deeper
        # when the chunk is already large (avoids mid-sentence must_break)
        prefer_break = False
        if level is not None and current_lines and current_size >= MIN_CHUNK_SIZE:
            if level <= top_level:
                prefer_break = True
            elif level <= top_level + 1 and current_size >= TARGET_CHUNK_SIZE:
                prefer_break = True

        if must_break or prefer_break:
            raw_chunks.append((list(current_lines), current_label))
            current_lines = []
            current_size = 0
            current_label = hierarchy_state.get(top_level)

        # First top-level marker in this chunk becomes its label
        if current_label is None and level is not None and level <= top_level:
            current_label = label

        current_lines.append(line)
        current_size += line_size

    if current_lines:
        raw_chunks.append((list(current_lines), current_label))

    # Build output dicts
    total = len(raw_chunks)
    result = []
    for n, (chunk_lines, label) in enumerate(raw_chunks, 1):
        result.append({
            **section,
            "text": "\n".join(chunk_lines),
            "section_title": section["section_title"],  # Always original
            "hierarchy_label": label,
            "chunk_n": n,
            "chunk_total": total,
        })

    return result


def _split_by_size_only(section: dict, lines: list[str]) -> list[dict]:
    """Fallback split for sections with no hierarchy markers."""
    raw_chunks = _group_segments(lines, separator="\n")
    total = len(raw_chunks)
    result = []
    for n, chunk_text in enumerate(raw_chunks, 1):
        result.append({
            **section,
            "text": chunk_text,
            "section_title": section["section_title"],
            "hierarchy_label": None,
            "chunk_n": n,
            "chunk_total": total,
        })
    return result


def _group_segments(segments: list[str], separator: str = "\n\n") -> list[str]:
    """Greedily group text segments into chunks up to MAX_CHUNK_SIZE."""
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


def merge_small_chunks(chunks: list[dict]) -> list[dict]:
    """
    Fold sub-MIN_CHUNK_SIZE fragments into their neighbors after splitting.
    Merged chunk keeps the hierarchy_label of its first constituent.
    Recalculates chunk_n and chunk_total after merge.
    """
    if len(chunks) <= 1:
        return chunks

    result = []
    for chunk in chunks:
        if len(chunk["text"]) >= MIN_CHUNK_SIZE or not result:
            result.append(dict(chunk))
        else:
            prev = result[-1]
            prev["text"] = prev["text"] + "\n" + chunk["text"]

    total = len(result)
    for n, chunk in enumerate(result, 1):
        chunk["chunk_n"] = n
        chunk["chunk_total"] = total

    return result


# ============================================================
# CHAPTER-LEVEL DOCUMENT CREATION
# ============================================================

def create_chapter_document(chapter_num: int, chapter_title: str,
                            program: str, sections: list[dict]) -> dict:
    """Create a chapter-level document by concatenating all section text."""
    context_prefix = build_context_prefix(chapter_num, chapter_title)

    parts = [context_prefix, ""]

    for section in sections:
        sec_num = section["section_number"]
        sec_title = section.get("section_title", "")
        text = section["text"].strip()
        text = append_tables(text, section.get("tables", []))

        if sec_title:
            parts.append(f"## {sec_num} {sec_title}")
        if text:
            parts.append(text)
        parts.append("")

    full_text = "\n".join(parts).strip()

    return {
        "chunk_id": make_chapter_id(chapter_num),
        "doc_type": "chapter",
        "text": full_text,
        "metadata": {
            "source": "106 CMR",
            "chapter": chapter_num,
            "chapter_title": chapter_title,
            "program": program,
            "section_count": len(sections),
            "has_tables": str(any(s.get("tables") for s in sections)),
        },
    }


# ============================================================
# SECTION-LEVEL CHUNK CREATION
# ============================================================

def create_section_chunks(chapter_num: int, chapter_title: str,
                          program: str, sections: list[dict]) -> list[dict]:
    """
    Create section-level chunks applying merge/split/hierarchy logic.

    Flow: sections → merge_small_sections → split_with_hierarchy →
          merge_small_chunks → annotate with context prefix → output
    """
    chapter_id = make_chapter_id(chapter_num)

    # Filter out excluded sections (kept in chapter-level docs only)
    sections = [s for s in sections if s["section_number"] not in SECTION_EXCLUDES]

    # Append table text to section bodies
    sections_with_tables = []
    for section in sections:
        text = append_tables(section["text"], section.get("tables", []))
        sections_with_tables.append({**section, "text": text})

    # Merge tiny sections
    merged = merge_small_sections(sections_with_tables)

    # Split with hierarchy awareness, then fold tiny fragments
    chunks = []
    for section in merged:
        split_chunks = split_with_hierarchy(section)
        split_chunks = merge_small_chunks(split_chunks)

        sec_num = section["section_number"]
        sec_title = section.get("section_title")

        for chunk_idx, chunk in enumerate(split_chunks):
            text = _normalize_line_breaks(chunk["text"].strip())
            if not text:
                continue

            raw_label = chunk.get("hierarchy_label")
            hierarchy_label = (
                _truncate_hierarchy_label(raw_label) if raw_label else None
            )
            chunk_n = chunk["chunk_n"]
            chunk_total = chunk["chunk_total"]

            # Build context prefix — include hierarchy label for chunks 2+
            prefix = build_context_prefix(
                chapter_num, chapter_title, sec_num, sec_title,
                hierarchy_path=hierarchy_label if chunk_n > 1 else None,
            )
            chunk_text = f"{prefix}\n\n{text}"

            chunks.append({
                "chunk_id": make_section_id(sec_num, chunk_idx),
                "doc_type": "section",
                "text": chunk_text,
                "metadata": {
                    "source": "106 CMR",
                    "chapter": chapter_num,
                    "chapter_title": chapter_title,
                    "program": program,
                    "section_number": sec_num,
                    "section_title": sec_title or "",
                    "hierarchy_path": hierarchy_label or "",
                    "chunk_n": chunk_n,
                    "chunk_total": chunk_total,
                    "has_tables": str(bool(section.get("tables"))),
                    "cross_references": ",".join(
                        section.get("cross_references", [])
                    ),
                    "parent_chapter_id": chapter_id,
                    "pdf_file": section.get("pdf_file", ""),
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
        if chapter not in by_chapter:
            by_chapter[chapter] = []
        by_chapter[chapter].append(section)

    for chapter in by_chapter:
        by_chapter[chapter].sort(key=lambda s: s["section_number"])

    return by_chapter


def process_all_sections() -> tuple[list[dict], list[dict]]:
    """Process all parsed sections and return (chapter_chunks, section_chunks)."""
    by_chapter = load_all_sections()

    if not by_chapter:
        return [], []

    chapter_chunks = []
    section_chunks = []

    for chapter_num in sorted(by_chapter.keys()):
        sections = by_chapter[chapter_num]
        chapter_title = sections[0]["chapter_title"]
        program = sections[0].get("program", "Unknown")

        chapter_doc = create_chapter_document(
            chapter_num, chapter_title, program, sections
        )
        chapter_chunks.append(chapter_doc)

        sec_chunks = create_section_chunks(
            chapter_num, chapter_title, program, sections
        )
        section_chunks.extend(sec_chunks)

    return chapter_chunks, section_chunks


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(chapter_chunks: list[dict],
                     section_chunks: list[dict]) -> None:
    """Print a summary of the chunking results."""
    print("=" * 60)
    print("106 CMR Chunking Statistics")
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
        bar = "#" * (count // 3)
        print(f"  {buckets[i]:>5}-{buckets[i+1]:>5}: {count:>4} ({pct:4.1f}%) {bar}")
    print()

    chapters = {}
    for c in section_chunks:
        ch = c["metadata"]["chapter"]
        ch_title = c["metadata"]["chapter_title"]
        prog = c["metadata"]["program"]
        key = f"CMR {ch}: {ch_title[:40]}"
        chapters[key] = chapters.get(key, 0) + 1
    print("Chunks by chapter:")
    for ch, count in sorted(chapters.items()):
        print(f"  {ch:55s} {count}")
    print()

    still_small = sum(1 for s in sec_sizes if s < MIN_CHUNK_SIZE)
    still_large = sum(1 for s in sec_sizes if s > MAX_CHUNK_SIZE)
    print(f"Chunks still < {MIN_CHUNK_SIZE} chars after merge: "
          f"{still_small} ({still_small/len(sec_sizes)*100:.1f}%)")
    print(f"Chunks still > {MAX_CHUNK_SIZE} chars after split: "
          f"{still_large} ({still_large/len(sec_sizes)*100:.1f}%)")
    print()

    # Hierarchy-aware metrics
    with_hierarchy = sum(
        1 for c in section_chunks if c["metadata"].get("hierarchy_path")
    )
    with_continued = sum(
        1 for c in section_chunks if "(continued)" in c["metadata"].get("section_title", "")
    )
    multi_chunk_sections = sum(
        1 for c in section_chunks if c["metadata"].get("chunk_total", 1) > 1
    )
    single_chunk = sum(
        1 for c in section_chunks if c["metadata"].get("chunk_total", 1) == 1
    )
    print(f"Chunks with hierarchy_path:  {with_hierarchy} "
          f"({with_hierarchy/len(section_chunks)*100:.1f}%)")
    print(f"Chunks with '(continued)':   {with_continued}")
    print(f"Single-chunk sections:       {single_chunk}")
    print(f"Multi-chunk section parts:   {multi_chunk_sections}")


def preview_chunks(chapter_chunks: list[dict], section_chunks: list[dict],
                   count: int = 2) -> None:
    """Preview chunks for the first N chapters."""
    for chapter_doc in chapter_chunks[:count]:
        ch_meta = chapter_doc["metadata"]
        print("=" * 60)
        print(f"CHAPTER: CMR {ch_meta['chapter']} - {ch_meta['chapter_title'][:50]}")
        print(f"  Program: {ch_meta['program']}")
        print(f"  Chapter text length: {len(chapter_doc['text'])} chars")
        print(f"  Sections in chapter: {ch_meta['section_count']}")
        print()

        chapter_id = chapter_doc["chunk_id"]
        related = [c for c in section_chunks
                   if c["metadata"]["parent_chapter_id"] == chapter_id]
        print(f"  Section chunks: {len(related)}")
        for chunk in related[:15]:
            meta = chunk["metadata"]
            sec_num = meta["section_number"]
            sec_title = meta["section_title"] or "(no title)"
            text_preview = chunk["text"][:120].replace("\n", " ")
            print(f"    {sec_num} {sec_title}")
            print(f"        {len(chunk['text'])} chars: {text_preview}...")
        if len(related) > 15:
            print(f"    ... and {len(related) - 15} more")
        print()


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the chunker."""
    parser = argparse.ArgumentParser(
        description="Chunk parsed 106 CMR sections for RAG embedding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chunker.py                  # Process all sections, write output
  python chunker.py --stats          # Show statistics only
  python chunker.py --preview 2      # Preview chunks for 2 chapters
        """,
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show statistics only, don't write output files",
    )
    parser.add_argument(
        "--preview", type=int, default=0,
        help="Preview chunks for the first N chapters",
    )
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
        print(f"\nWrote {len(chapter_chunks)} chapter documents to {CHAPTER_CHUNKS_FILE}")

        with open(SECTION_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(section_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(section_chunks)} section chunks to {SECTION_CHUNKS_FILE}")


if __name__ == "__main__":
    main()
