"""
Chunker for FNS Handbook 310 RAG pipeline.

Reads the parsed section JSON files and produces two sets of chunks
for embedding:

  1. Chapter-level documents (one per chapter) — for broad topic matching
  2. Section-level chunks (granular) — for specific policy answers

The section chunker applies smart merge/split logic:
  - Tiny sections (< MIN_CHUNK_SIZE) are merged with their neighbors
  - Large sections (> MAX_CHUNK_SIZE) are split at paragraph boundaries
  - Tables are rendered as pipe-delimited text and appended to section text
  - Each chunk gets a context prefix (FNS 310 > Chapter > Section)
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
INDEX_DIR = PROJECT_ROOT / "index" / "fns"
PARSED_DIR = INDEX_DIR / "parsed_sections"
CHAPTER_CHUNKS_FILE = INDEX_DIR / "chapter_chunks.json"
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
    """
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
    """
    Render tables and append them to the section text.

    Unlike OLG (which has [Table] placeholders), FNS tables are stored
    separately and need to be appended at the end of the text.
    """
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
                         section_title: str | None = None) -> str:
    """
    Build a hierarchical context string prepended to chunk text
    before embedding.

    Example output:
        "FNS 310 > Chapter 10: Income > 1021.1 Positive Allegation"
    """
    parts = [f"FNS 310", f"Chapter {chapter}: {chapter_title}"]

    if section_number and section_title:
        parts.append(f"{section_number} {section_title}")
    elif section_number:
        parts.append(section_number)

    return " > ".join(parts)


# ============================================================
# CHUNK ID GENERATION
# ============================================================

def make_chapter_id(chapter_num: int) -> str:
    """
    Generate a stable ID for a chapter-level document.

    Example: "fns_ch10"
    """
    return f"fns_ch{chapter_num:02d}"


def make_section_id(section_number: str, chunk_index: int) -> str:
    """
    Generate a stable, readable ID for a section-level chunk.

    Example: "fns_sec_1021_1__000"
    """
    safe = section_number.replace(".", "_")
    return f"fns_sec_{safe}__{chunk_index:03d}"


# ============================================================
# SMART MERGE LOGIC
# ============================================================

def merge_small_sections(sections: list[dict]) -> list[dict]:
    """
    Merge tiny sections (< MIN_CHUNK_SIZE) with their neighbors.

    Rules:
    - A tiny section gets merged INTO the next section.
    - If the tiny section is the last one, merge it into the
      previous section.
    - The merged section inherits the title of whichever part
      had a title. If both have titles, keep the first one
      and note the second in the text.

    Single-pass forward merge within a chapter.
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

        # This section is too small — try to merge forward
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
                "level": min(section["level"], next_section["level"]) if section["level"] > 0 else next_section["level"],
                "text": merged_text,
            }
            sections[i + 1] = merged
            i += 1
            continue

        # Last section and too small — merge backward into previous
        if result:
            prev = result[-1]
            merged_text = _combine_text(
                prev.get("section_title"), prev["text"],
                section.get("section_title"), text
            )
            result[-1] = {**prev, "text": merged_text}
            i += 1
            continue

        # Only section and it's tiny — keep it anyway
        result.append(section)
        i += 1

    return result


def _combine_text(title_a: str | None, text_a: str,
                  title_b: str | None, text_b: str) -> str:
    """
    Combine two section texts. If the second section had a title,
    insert it as a marker so the context isn't lost.
    """
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

def split_large_section(section: dict) -> list[dict]:
    """
    Split a section that exceeds MAX_CHUNK_SIZE into smaller chunks.

    Splitting strategy (in order of preference):
    1. Split at paragraph boundaries (double newline)
    2. If paragraphs are still too large, split at sentence boundaries
    3. Each sub-chunk inherits the title with "(continued)" suffix
    """
    text = section["text"]

    if len(text) <= MAX_CHUNK_SIZE:
        return [section]

    title = section.get("section_title")

    # First try: split into paragraphs (double newline)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # If that didn't produce enough splits, try single newlines
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # Group paragraphs into chunks around TARGET_CHUNK_SIZE
    chunks = _group_segments(paragraphs, separator="\n\n")

    # Second pass: any chunk still too large gets sentence-split
    final_chunks = []
    for chunk_text in chunks:
        if len(chunk_text) <= MAX_CHUNK_SIZE:
            final_chunks.append(chunk_text)
        else:
            sentences = re.split(r"(?<=[.?!])\s+(?=[A-Z])", chunk_text)
            if len(sentences) > 1:
                final_chunks.extend(_group_segments(sentences, separator=" "))
            else:
                # Truly unsplittable — hard split at TARGET_CHUNK_SIZE
                for start in range(0, len(chunk_text), TARGET_CHUNK_SIZE):
                    final_chunks.append(chunk_text[start:start + TARGET_CHUNK_SIZE])

    # Build section dicts for each chunk
    result = []
    for i, chunk_text in enumerate(final_chunks):
        if i == 0:
            chunk_title = title
        else:
            chunk_title = f"{title} (continued)" if title else None

        result.append({
            **section,
            "section_title": chunk_title,
            "text": chunk_text,
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
# CHAPTER-LEVEL DOCUMENT CREATION
# ============================================================

def create_chapter_document(chapter_num: int, chapter_title: str,
                            sections: list[dict]) -> dict:
    """
    Create a chapter-level document by concatenating all section text.
    This is the broad-context document used for topic discovery.
    """
    context_prefix = build_context_prefix(chapter_num, chapter_title)

    parts = [context_prefix, ""]  # blank line after prefix

    for section in sections:
        sec_num = section["section_number"]
        sec_title = section.get("section_title", "")
        text = section["text"].strip()

        # Append tables to section text
        text = append_tables(text, section.get("tables", []))

        if sec_title:
            parts.append(f"## {sec_num} {sec_title}")
        if text:
            parts.append(text)
        parts.append("")  # blank line between sections

    full_text = "\n".join(parts).strip()

    # Collect metadata across all sections
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
                          sections: list[dict]) -> list[dict]:
    """
    Create section-level chunks from a chapter's sections, applying
    merge/split logic and adding context prefixes.

    Pipeline:
    1. Append tables to section text
    2. Merge tiny sections with neighbors
    3. Split oversized sections at paragraph boundaries
    4. Add context prefix and metadata
    """
    chapter_id = make_chapter_id(chapter_num)

    # Step 1: Append tables to section text
    sections_with_tables = []
    for section in sections:
        text = append_tables(section["text"], section.get("tables", []))
        sections_with_tables.append({**section, "text": text})

    # Step 2: Merge small sections
    merged = merge_small_sections(sections_with_tables)

    # Step 3: Split large sections
    split_sections = []
    for section in merged:
        split_sections.extend(split_large_section(section))

    # Step 4: Build chunks with context prefixes and metadata
    chunks = []
    for i, section in enumerate(split_sections):
        sec_num = section["section_number"]
        sec_title = section.get("section_title")
        text = section["text"].strip()

        if not text:
            continue

        # Build context prefix and prepend to text
        prefix = build_context_prefix(chapter_num, chapter_title,
                                      sec_num, sec_title)
        chunk_text = f"{prefix}\n\n{text}"

        chunk = {
            "chunk_id": make_section_id(sec_num, i),
            "doc_type": "section",
            "text": chunk_text,
            "metadata": {
                "source": "FNS Handbook 310",
                "chapter": chapter_num,
                "chapter_title": chapter_title,
                "section_number": sec_num,
                "section_title": sec_title or "",
                "level": section["level"],
                "parent_section": section.get("parent_section", ""),
                "pdf_pages": ",".join(str(p) for p in section.get("pdf_pages", [])),
                "handbook_pages": ",".join(section.get("handbook_pages", [])),
                "flags": ",".join(section.get("flags", [])),
                "has_tables": str(bool(section.get("tables"))),
                "cross_references": ",".join(section.get("cross_references", [])),
                "chunk_index": i,
                "parent_chapter_id": chapter_id,
            },
        }
        chunks.append(chunk)

    return chunks


# ============================================================
# MAIN PROCESSING
# ============================================================

def load_all_sections() -> dict[int, list[dict]]:
    """
    Load all parsed section JSON files and group by chapter.

    Returns a dict mapping chapter number → sorted list of section dicts.
    """
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

    # Sort sections within each chapter by section_number
    for chapter in by_chapter:
        by_chapter[chapter].sort(key=lambda s: s["section_number"])

    return by_chapter


def process_all_sections() -> tuple[list[dict], list[dict]]:
    """
    Process all parsed sections and return (chapter_chunks, section_chunks).
    """
    by_chapter = load_all_sections()

    if not by_chapter:
        return [], []

    chapter_chunks = []
    section_chunks = []

    for chapter_num in sorted(by_chapter.keys()):
        sections = by_chapter[chapter_num]
        chapter_title = sections[0]["chapter_title"]

        # Create chapter-level document
        chapter_doc = create_chapter_document(chapter_num, chapter_title, sections)
        chapter_chunks.append(chapter_doc)

        # Create section-level chunks
        sec_chunks = create_section_chunks(chapter_num, chapter_title, sections)
        section_chunks.extend(sec_chunks)

    return chapter_chunks, section_chunks


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(chapter_chunks: list[dict],
                     section_chunks: list[dict]) -> None:
    """Print a summary of the chunking results."""
    print("=" * 60)
    print("FNS Handbook 310 — Chunking Statistics")
    print("=" * 60)
    print()

    # Chapter-level stats
    ch_sizes = [len(c["text"]) for c in chapter_chunks]
    print(f"Chapter-level documents: {len(chapter_chunks)}")
    print(f"  Median size: {statistics.median(ch_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(ch_sizes):.0f} chars")
    print(f"  Min:         {min(ch_sizes)} chars")
    print(f"  Max:         {max(ch_sizes)} chars")
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
        bar = "#" * (count // 5)
        print(f"  {buckets[i]:>5}-{buckets[i+1]:>5}: {count:>4} ({pct:4.1f}%) {bar}")
    print()

    # Chapter distribution
    chapters = {}
    for c in section_chunks:
        ch = c["metadata"]["chapter"]
        ch_title = c["metadata"]["chapter_title"]
        key = f"Ch {ch}: {ch_title}"
        chapters[key] = chapters.get(key, 0) + 1
    print("Chunks by chapter:")
    for ch, count in sorted(chapters.items()):
        print(f"  {ch:45s} {count}")
    print()

    # Chunks that are still small (after merging) or large (after splitting)
    still_small = sum(1 for s in sec_sizes if s < MIN_CHUNK_SIZE)
    still_large = sum(1 for s in sec_sizes if s > MAX_CHUNK_SIZE)
    print(f"Chunks still < {MIN_CHUNK_SIZE} chars after merge: "
          f"{still_small} ({still_small/len(sec_sizes)*100:.1f}%)")
    print(f"Chunks still > {MAX_CHUNK_SIZE} chars after split: "
          f"{still_large} ({still_large/len(sec_sizes)*100:.1f}%)")


def preview_chunks(chapter_chunks: list[dict], section_chunks: list[dict],
                   count: int = 2) -> None:
    """Preview chunks for the first N chapters."""
    for chapter_doc in chapter_chunks[:count]:
        ch_meta = chapter_doc["metadata"]
        print("=" * 60)
        print(f"CHAPTER: {ch_meta['chapter_title']} (Chapter {ch_meta['chapter']})")
        print(f"  Chapter text length: {len(chapter_doc['text'])} chars")
        print(f"  Sections in chapter: {ch_meta['section_count']}")
        print()

        # Find section chunks for this chapter
        chapter_id = chapter_doc["chunk_id"]
        related = [c for c in section_chunks
                   if c["metadata"]["parent_chapter_id"] == chapter_id]
        print(f"  Section chunks: {len(related)}")
        for chunk in related:
            meta = chunk["metadata"]
            sec_num = meta["section_number"]
            sec_title = meta["section_title"] or "(no title)"
            text_preview = chunk["text"][:120].replace("\n", " ")
            print(f"    [{meta['level']}] {sec_num} {sec_title}")
            print(f"        {len(chunk['text'])} chars: {text_preview}...")
        print()


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the chunker."""
    parser = argparse.ArgumentParser(
        description="Chunk parsed FNS Handbook 310 sections for RAG embedding.",
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
        # Write output files
        with open(CHAPTER_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(chapter_chunks, f, indent=2, ensure_ascii=False)
        print(f"\nWrote {len(chapter_chunks)} chapter documents to {CHAPTER_CHUNKS_FILE}")

        with open(SECTION_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(section_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(section_chunks)} section chunks to {SECTION_CHUNKS_FILE}")


if __name__ == "__main__":
    main()
