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
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "olg"
SCRAPED_DIR = DATA_DIR / "scraped_pages"
PAGE_CHUNKS_FILE = DATA_DIR / "page_chunks.json"
SECTION_CHUNKS_FILE = DATA_DIR / "section_chunks.json"

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
                         section_heading: str | None = None) -> str:
    """
    Build a hierarchical context string that gets prepended to chunk
    text before embedding.

    Example output:
        "SNAP > Application Processing > Expedited Benefits > Step One"

    This helps the embedding model understand where this content sits
    in the policy hierarchy, improving retrieval accuracy.
    """
    parts = list(breadcrumb)

    # Add page title if it's not already the last breadcrumb element
    if page_title and (not parts or parts[-1] != page_title):
        parts.append(page_title)

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
# SMART MERGE LOGIC
# ============================================================

def merge_small_sections(sections: list[dict]) -> list[dict]:
    """
    Merge tiny sections (< MIN_CHUNK_SIZE) with their neighbors.

    Rules:
    - An empty or tiny section gets merged INTO the next section
      at the same or lower level (same heading hierarchy).
    - If the tiny section is the last one, merge it into the
      previous section.
    - "Related Topics" sections are kept as-is (they're useful
      link reference lists even when short).
    - The merged section inherits the heading of whichever part
      had a heading. If both have headings, keep the first one
      and note the second in the text.

    This is a single-pass forward merge. After merging, some chunks
    that were just above the threshold might still be small, but
    that's fine — we're preventing truly degenerate 10-char chunks,
    not enforcing strict minimums.
    """
    if len(sections) <= 1:
        return sections

    result = []
    i = 0

    while i < len(sections):
        section = sections[i]
        text = section["text"]
        heading = section.get("heading") or ""

        # Keep "Related Topics" sections as-is — they're useful even when short
        if heading.lower().startswith("related topic"):
            result.append(section)
            i += 1
            continue

        # If this section is large enough, keep it
        if len(text) >= MIN_CHUNK_SIZE:
            result.append(section)
            i += 1
            continue

        # This section is too small — try to merge forward
        if i + 1 < len(sections):
            next_section = sections[i + 1]
            merged_text = _combine_text(
                heading, text,
                next_section.get("heading"), next_section["text"]
            )
            merged = {
                "heading": section["heading"] or next_section["heading"],
                "level": min(section["level"], next_section["level"]) if section["level"] > 0 else next_section["level"],
                "text": merged_text,
            }
            # Replace next section with the merged version
            sections[i + 1] = merged
            i += 1
            continue

        # Last section and too small — merge backward into previous
        if result:
            prev = result[-1]
            merged_text = _combine_text(
                prev.get("heading"), prev["text"],
                heading, text
            )
            result[-1] = {**prev, "text": merged_text}
            i += 1
            continue

        # Only section and it's tiny — keep it anyway
        result.append(section)
        i += 1

    return result


def _combine_text(heading_a: str | None, text_a: str,
                  heading_b: str | None, text_b: str) -> str:
    """
    Combine two section texts. If the second section had a heading,
    insert it as a bold-style marker so the context isn't lost.
    """
    parts = []

    if text_a.strip():
        parts.append(text_a.strip())

    if heading_b:
        parts.append(f"{heading_b}")

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
    3. Each sub-chunk inherits the heading with "(continued)" suffix

    This handles both well-structured content (many <p> tags) and
    pages where the HTML used inline elements, producing one giant
    block of text.
    """
    text = section["text"]

    if len(text) <= MAX_CHUNK_SIZE:
        return [section]

    heading = section.get("heading")
    level = section["level"]

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
            # Split on sentence boundaries (period/question/exclamation
            # followed by a space and a capital letter, or end of string)
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
            chunk_heading = heading
        else:
            chunk_heading = f"{heading} (continued)" if heading else None

        result.append({
            "heading": chunk_heading,
            "level": level,
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

        # If adding this segment would exceed MAX and we have content,
        # flush current chunk first
        if current_size + seg_size > MAX_CHUNK_SIZE and current_parts:
            chunks.append(separator.join(current_parts))
            current_parts = []
            current_size = 0

        current_parts.append(segment)
        current_size += seg_size

    # Flush remaining
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

    # Step 1: Merge small sections
    merged = merge_small_sections(sections_with_tables)

    # Step 2: Split large sections
    split_sections = []
    for section in merged:
        split_sections.extend(split_large_section(section))

    # Step 3: Build chunks with context prefixes and metadata
    chunks = []
    for i, section in enumerate(split_sections):
        heading = section.get("heading")
        text = section["text"].strip()

        if not text:
            continue

        # Build context prefix and prepend to text
        prefix = build_context_prefix(breadcrumb, title, heading)
        chunk_text = f"{prefix}\n\n{text}"

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
                "section_level": section["level"],
                "last_updated": page_data.get("last_updated"),
                "chunk_index": i,
                "parent_page_id": page_id,
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

    for page_file in page_files:
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
