"""
PDF Parser for FNS Handbook 310 (SNAP Quality Control Review Handbook).

Takes the handbook PDF and extracts structured sections suitable for
downstream RAG chunking. This is the PDF equivalent of the OLG project's
parser.py, which handles HTML pages.

The parser targets content pages (skipping TOC, appendices, index) and:
  - Detects section boundaries via the handbook's numbered section system
    (e.g., 100, 154.3, 1021.1)
  - Builds section hierarchy from the numbering scheme
  - Strips page headers ("FNS HANDBOOK 310") and footers (page numbers)
  - Cleans special characters (Wingdings bullets, etc.)
  - Handles 11 pages with side-by-side example boxes using column-aware
    extraction
  - Extracts tables via pdfplumber
  - Extracts cross-references ("See Section 622") as metadata
  - Outputs one JSON file per section to parsed_sections/

Design notes:
  - This module does all the work: PDF reading, parsing, and file output.
  - The OLG parser is a pure parser (no I/O) because the scraper handles
    I/O. Here there's no scraper — the PDF is our only input.
  - Section detection uses regex on the numbered section pattern. The key
    challenge is distinguishing actual section headings from inline
    cross-references to section numbers.

Usage:
    python fns_parser.py                    # Parse full handbook
    python fns_parser.py --chapter 10       # Parse one chapter
    python fns_parser.py --pages 195-200    # Parse specific PDF pages
    python fns_parser.py --dry-run          # Show sections found, don't write files
"""

import argparse
import configparser
import json
import os
import re
import sys
from pathlib import Path

import pdfplumber


# ============================================================
# CONSTANTS
# ============================================================

# Chapter titles keyed by chapter number
CHAPTER_TITLES = {
    1: "Introduction",
    2: "Basic Review Process",
    3: "Case Record Review",
    4: "Field Investigation",
    5: "Verification and Documentation",
    6: "Error Determination Process",
    7: "Review Procedures Relative to Certification Systems and Changes",
    8: "Non-Financial Eligibility Criteria",
    9: "Resources",
    10: "Income",
    11: "Deductions",
    12: "Making the Review Decision",
    13: "Negative Action Record Reviews",
    14: "Informal Resolution and Arbitration",
}

# Chapter number → section number range (first digit(s) of section numbers)
# Chapters 1-9: section numbers are 100-999 (first digit = chapter)
# Chapters 10-14: section numbers are 1000-1499 (first two digits = chapter)
CHAPTER_RANGES = {
    1: (100, 199),
    2: (200, 299),
    3: (300, 399),
    4: (400, 499),
    5: (500, 599),
    6: (600, 699),
    7: (700, 799),
    8: (800, 899),
    9: (900, 999),
    10: (1000, 1099),
    11: (1100, 1199),
    12: (1200, 1299),
    13: (1300, 1399),
    14: (1400, 1499),
}

# Page header pattern to strip
# Case-insensitive: the handbook uses both "FNS HANDBOOK 310" and "FNS Handbook 310"
# (the latter appears in the right column of side-by-side example boxes).
PAGE_HEADER_PATTERN = re.compile(
    r"^(?:FNS\s+HANDBOOK\s+310|FFFNNNSSS\s+HHHAAANNNDDDBBBOOOOOOKKK\s+333111000)\s*$",
    re.IGNORECASE,
)

# Page footer patterns to strip
PAGE_FOOTER_PATTERNS = [
    # Handbook page numbers like "1-2", "10-4", "8-22", "A-1"
    re.compile(r"^\d{1,2}[–—-]\d{1,2}$"),
    re.compile(r"^[A-Z][–—-]\d{1,2}$"),
    # Roman numerals (TOC pages, shouldn't appear in content but just in case)
    re.compile(r"^(i{1,3}|iv|vi{0,3}|ix|xi{0,3}|xiv|xv)$"),
    # Change annotations
    re.compile(r"^Change\s+\d+\s+\(.*\)\s*$"),
]

# Chapter divider patterns. Each chapter starts on a new page with a
# divider showing "Chapter N" and the chapter title centered. Without
# stripping, that text leaks into the LAST section of the previous chapter.
CHAPTER_DIVIDER_PATTERNS = [
    re.compile(r"^Chapter\s+\d{1,2}\s*$", re.IGNORECASE),
    # Chapter N + ALL CAPS title on one line (after soft-wrap flattening)
    re.compile(r"^Chapter\s+\d{1,2}\s+[A-Z][A-Z\s]{3,}$"),
]

# Section heading pattern: a numbered section at the start of a line
# Examples: "100 GENERAL.", "1021.1 Positive Allegation.", "820 CITIZENSHIP AND..."
# Must start at line beginning, have 3-4 digit base, optional dot-subsections,
# followed by whitespace and then text starting with a capital letter or digit.
SECTION_HEADING_PATTERN = re.compile(
    r"^(\d{3,4}(?:\.\d+)*)\s+([A-Z].+)"
)

# Cross-reference patterns in running text
CROSS_REF_PATTERNS = [
    # "See Section 622" or "see Section 1021.1"
    re.compile(r"[Ss]ee\s+[Ss]ection\s+(\d{3,4}(?:\.\d+)*)"),
    # "Chapter 7, Section 726.1" or "Chapter 10"
    re.compile(r"[Cc]hapter\s+(\d{1,2})(?:,?\s+[Ss]ection\s+(\d{3,4}(?:\.\d+)*))?"),
    # "Section 622" standalone
    re.compile(r"[Ss]ection\s+(\d{3,4}(?:\.\d+)*)"),
]

# Wingdings bullet replacement
WINGDINGS_BULLET = "\uf0d8"


# ============================================================
# PUBLIC API
# ============================================================

def parse_handbook(
    pdf_path: str,
    content_start: int = 18,
    content_end: int = 298,
    side_by_side_pages: list[int] | None = None,
    chapter_filter: int | None = None,
    page_range: tuple[int, int] | None = None,
) -> list[dict]:
    """
    Parse the FNS Handbook 310 PDF into structured sections.

    Args:
        pdf_path: Path to the PDF file.
        content_start: First content page (1-indexed). Default 18.
        content_end: Last content page (1-indexed). Default 298.
        side_by_side_pages: List of 1-indexed page numbers with side-by-side
            example boxes that need column-aware extraction.
        chapter_filter: If set, only return sections from this chapter.
        page_range: If set, only process pages in this (start, end) range
            (1-indexed, inclusive).

    Returns:
        A list of section dicts, each with:
        {
            "source": "FNS Handbook 310",
            "source_edition": "October 2025, Change 2 (January 13, 2026)",
            "chapter": 10,
            "chapter_title": "Income",
            "section_number": "1021.1",
            "section_title": "Positive Allegation",
            "level": 3,
            "parent_section": "1021",
            "text": "When the household states...",
            "tables": [...],
            "cross_references": ["Section 622", "Chapter 7"],
            "pdf_pages": [195],
            "handbook_pages": ["10-4"],
            "flags": []
        }
    """
    if side_by_side_pages is None:
        side_by_side_pages = []

    side_by_side_set = set(side_by_side_pages)

    # Determine page range to process
    if page_range:
        start_pg, end_pg = page_range
    else:
        start_pg, end_pg = content_start, content_end

    print(f"Opening PDF: {pdf_path}")
    pdf = pdfplumber.open(pdf_path)
    print(f"  Total PDF pages: {len(pdf.pages)}")
    print(f"  Processing pages {start_pg}-{end_pg}")
    print()

    # Step 1: Extract raw text from each page
    print("Step 1: Extracting text from PDF pages...")
    raw_pages = []
    for page_num in range(start_pg, end_pg + 1):
        page_idx = page_num - 1
        if page_idx >= len(pdf.pages):
            break

        page = pdf.pages[page_idx]

        # Always try column detection. The auto-detector falls back to
        # single-column extract_text() when no two-column structure is
        # found, so this is safe on every page. The manual side_by_side
        # list still acts as a hint flag for traceability/review.
        main_text, example_text, extraction_ok = _extract_columns(page)

        flags = []
        if example_text:
            flags.append("side_by_side_page")
        if page_num in side_by_side_set and not example_text:
            # Manual hint says it's side-by-side but auto-detection didn't
            # find columns — flag for review
            flags.append("manual_review_needed")

        # Extract tables from this page
        tables = _extract_tables(page)

        # Get handbook page number from footer
        handbook_page = _extract_handbook_page_number(main_text)

        # Clean the text — apply to both columns so the right-column example
        # box gets the same header/footer stripping as the left column.
        main_text = _clean_page_text(main_text)
        if example_text:
            example_text = _clean_page_text(example_text)

        raw_pages.append({
            "pdf_page": page_num,
            "text": main_text,
            "example_text": example_text,
            "tables": tables,
            "handbook_page": handbook_page,
            "flags": flags,
        })

    print(f"  Extracted {len(raw_pages)} pages")
    flagged = sum(1 for p in raw_pages if p["flags"])
    if flagged:
        print(f"  Flagged pages: {flagged}")
    print()

    pdf.close()

    # Step 2: Concatenate all page text and split into sections
    print("Step 2: Detecting section boundaries...")
    sections = _split_into_sections(raw_pages)
    print(f"  Found {len(sections)} sections")
    print()

    # Step 3: Enrich sections with metadata
    print("Step 3: Enriching section metadata...")
    for section in sections:
        _enrich_section(section)

    # Step 4: Filter by chapter if requested
    if chapter_filter is not None:
        sections = [s for s in sections if s["chapter"] == chapter_filter]
        print(f"  Filtered to chapter {chapter_filter}: {len(sections)} sections")

    # Summary
    chapters_found = sorted(set(s["chapter"] for s in sections if s["chapter"]))
    print(f"\nParsing complete:")
    print(f"  Total sections: {len(sections)}")
    print(f"  Chapters: {chapters_found}")
    flagged_sections = [s for s in sections if s["flags"]]
    if flagged_sections:
        print(f"  Sections with flags: {len(flagged_sections)}")
        for s in flagged_sections:
            print(f"    [{s['section_number']}] {', '.join(s['flags'])}")

    return sections


def save_sections(sections: list[dict], output_dir: str) -> None:
    """
    Save parsed sections to individual JSON files.

    Each section is saved as:
        output_dir/ch{chapter}_{section_number}.json

    Args:
        sections: List of section dicts from parse_handbook().
        output_dir: Directory to write JSON files to.
    """
    os.makedirs(output_dir, exist_ok=True)

    for section in sections:
        ch = section["chapter"] or 0
        sec_num = section["section_number"].replace(".", "_")
        filename = f"ch{ch:02d}_{sec_num}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(section, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(sections)} section files to {output_dir}/")


# ============================================================
# TEXT EXTRACTION
# ============================================================

def _detect_column_boundary_histogram(words, page_width: float) -> float | None:
    """
    Detect a two-column page by analyzing where words start (x0 histogram).

    A two-column page has TWO dominant x0 cluster peaks:
      - Left column (typically around x=80-100)
      - Right column (typically around x=315-330)

    Returns a column-boundary x value if the page looks two-column,
    otherwise None. More robust than per-line gap detection because
    it handles pages where left and right column rows don't share
    y-buckets (5-pixel vertical offset between columns is common).
    """
    if len(words) < 30:
        return None

    from collections import Counter
    middle = page_width * 0.5

    # Bucket word start positions in 10-pixel buckets
    x0_buckets = Counter(int(w["x0"] // 10) * 10 for w in words)

    # Find peak word-count buckets in left half and right-mid section
    left_buckets = [(count, x) for x, count in x0_buckets.items()
                    if x < middle * 0.95]
    right_buckets = [(count, x) for x, count in x0_buckets.items()
                     if middle * 1.0 <= x < page_width * 0.7]

    if not left_buckets or not right_buckets:
        return None

    left_peak_count, left_peak_x = max(left_buckets)
    right_peak_count, right_peak_x = max(right_buckets)

    # Both peaks need substantial word counts to be considered columns.
    # Tables or random scattered right-side words wouldn't accumulate.
    if left_peak_count < 8 or right_peak_count < 8:
        return None

    # Peaks should be at least 100 pixels apart for clear two-column structure
    if right_peak_x - left_peak_x < 100:
        return None

    return (left_peak_x + right_peak_x) / 2


def _extract_columns(page) -> tuple[str, str | None, bool]:
    """
    Extract text from a page with side-by-side content by separating
    left (policy text) and right (example box) columns.

    Two-stage detection:
      1. Per-line gap detection: scan each y-bucket for wide horizontal
         gaps in the middle of the page. Robust when 3+ lines align well.
      2. Histogram fallback: count word x-start positions, look for a
         bimodal distribution. Handles pages where left/right rows don't
         share y-buckets (typical 5-pixel vertical offset between cols).

    If neither detects columns, falls back to single-column extract_text().

    Returns:
        (main_text, example_text, extraction_ok)
        - main_text: Left column text (the actual policy)
        - example_text: Right column text (illustrative example) or None
        - extraction_ok: True if separation looked reliable
    """
    words = page.extract_words(keep_blank_chars=True, y_tolerance=3, x_tolerance=3)

    if not words:
        return page.extract_text() or "", None, True

    page_width = page.width
    midpoint = page_width * 0.45

    # Group words by y-position (same line)
    lines = {}
    for w in words:
        y_key = round(w["top"] / 5) * 5
        lines.setdefault(y_key, [])
        lines[y_key].append(w)

    # Stage 1: per-line gap detection
    gap_x_positions = []
    for y_key in sorted(lines.keys()):
        line_words = sorted(lines[y_key], key=lambda w: w["x0"])
        for j in range(1, len(line_words)):
            gap = line_words[j]["x0"] - line_words[j - 1]["x1"]
            if gap > 35:
                gap_x = (line_words[j - 1]["x1"] + line_words[j]["x0"]) / 2
                if midpoint * 0.7 < gap_x < page_width * 0.65:
                    gap_x_positions.append(gap_x)

    if len(gap_x_positions) >= 3:
        # Use the median gap position as the column boundary
        gap_x_positions.sort()
        boundary = gap_x_positions[len(gap_x_positions) // 2]
    else:
        # Stage 2: histogram fallback
        boundary = _detect_column_boundary_histogram(words, page_width)
        if boundary is None:
            return page.extract_text() or "", None, True

    # Identify the two-column y-range. A page may have full-width content
    # at the top (preceding section that ended on this page, or a section
    # heading paragraph that wraps full width) AND two-column content
    # below. Apply column split ONLY where both sides have a wide gap
    # at the boundary (i.e., a true two-column row, not a full-width
    # line whose words happen to span the boundary).
    line_buckets = {}
    for w in words:
        y_bucket = round(w["top"] / 12) * 12
        line_buckets.setdefault(y_bucket, []).append(w)

    def _is_two_col_row(ws) -> bool:
        """A row is two-column when there's a >25px gap at the boundary."""
        left_xs = [w["x1"] for w in ws if w["x0"] < boundary - 5]
        right_xs = [w["x0"] for w in ws if w["x0"] > boundary + 5]
        if not left_xs or not right_xs:
            return False
        return min(right_xs) - max(left_xs) > 25

    two_col_ys = sorted(
        y for y, ws in line_buckets.items() if _is_two_col_row(ws)
    )

    if len(two_col_ys) < 3:
        # Histogram suggested two columns but row alignment doesn't
        # confirm — fall back to single-column extraction
        return page.extract_text() or "", None, True

    two_col_min_y = two_col_ys[0] - 6
    two_col_max_y = two_col_ys[-1] + 6

    # Extend the range forward AND backward to cover example-box headers
    # and trailers that may not have left-column counterparts at the same
    # y-position. Example boxes often begin with a header line that's
    # right-only and end with content that continues past where the left
    # column has stopped (sometimes with stray punctuation remnants).
    sorted_ys = sorted(line_buckets.keys())

    # Forward extension. Extend over right-dominant rows AND sparse
    # left-only rows (single trailing word like "covered." that punctuates
    # the end of left content while right column continues with example
    # box prose). STOP only when we hit substantial left-side content
    # or gap too far.
    last_y = two_col_max_y
    for y in sorted_ys:
        if y <= last_y:
            continue
        if y - last_y > 40:
            break
        ws = line_buckets[y]
        left_count = sum(1 for w in ws if w["x0"] < boundary - 5)
        right_count = sum(1 for w in ws if w["x0"] > boundary + 5)
        if left_count > 3:
            # Substantial left content — full-width has resumed
            break
        if right_count >= 1 or left_count <= 2:
            last_y = y + 6
            continue
        break
    two_col_max_y = last_y

    # Backward extension (mirror of forward)
    first_y = two_col_min_y
    for y in reversed(sorted_ys):
        if y >= first_y:
            continue
        if first_y - y > 40:
            break
        ws = line_buckets[y]
        left_count = sum(1 for w in ws if w["x0"] < boundary - 5)
        right_count = sum(1 for w in ws if w["x0"] > boundary + 5)
        if left_count > 3:
            break
        if right_count >= 1 or left_count <= 2:
            first_y = y - 6
            continue
        break
    two_col_min_y = first_y

    # Split words into left and right columns. Words OUTSIDE the
    # two-column y-range (full-width content above or below the columned
    # region) all go to the main (left) text — their x-position past the
    # boundary is just trailing-word position in a full-width line.
    left_lines = {}
    right_lines = {}

    for y_key in sorted(lines.keys()):
        in_two_col_range = two_col_min_y <= y_key <= two_col_max_y
        for w in lines[y_key]:
            if in_two_col_range and w["x0"] > boundary:
                right_lines.setdefault(y_key, [])
                right_lines[y_key].append(w)
            else:
                left_lines.setdefault(y_key, [])
                left_lines[y_key].append(w)

    # Reconstruct text from each column
    main_text = _words_to_text(left_lines)
    example_text = _words_to_text(right_lines)

    # Sanity check: both columns should have meaningful content
    extraction_ok = len(main_text.strip()) > 50 and len(example_text.strip()) > 20

    return main_text, example_text, extraction_ok


def _words_to_text(line_groups: dict[int, list]) -> str:
    """
    Reconstruct readable text from grouped words.

    Words on the same y-line are joined with spaces. Lines are joined
    with newlines. Paragraph breaks (larger y-gaps) get double newlines.
    """
    if not line_groups:
        return ""

    result_lines = []
    prev_y = None

    for y_key in sorted(line_groups.keys()):
        words = sorted(line_groups[y_key], key=lambda w: w["x0"])
        line_text = " ".join(w["text"] for w in words)

        # Detect paragraph breaks (gap > 15 units between lines)
        if prev_y is not None and (y_key - prev_y) > 15:
            result_lines.append("")

        result_lines.append(line_text)
        prev_y = y_key

    return "\n".join(result_lines)


def _extract_handbook_page_number(raw_text: str) -> str | None:
    """
    Find the handbook page number (like "10-4" or "8-22") from the
    raw page text, typically the last line.
    """
    if not raw_text:
        return None

    lines = raw_text.strip().split("\n")
    # Check last few lines (sometimes there's trailing whitespace)
    for line in reversed(lines[-3:]):
        line = line.strip()
        # Match patterns like "1-2", "10-4", "8-22"
        if re.match(r"^\d{1,2}[–—-]\d{1,2}$", line):
            return line.replace("–", "-").replace("—", "-")
        # Match "A-1", "B-1" etc.
        if re.match(r"^[A-Z][–—-]\d{1,2}$", line):
            return line.replace("–", "-").replace("—", "-")

    return None


# ============================================================
# TEXT CLEANING
# ============================================================

def _clean_page_text(text: str) -> str:
    """
    Clean extracted page text by stripping headers, footers, chapter
    divider lines, and fixing special characters.
    """
    if not text:
        return ""

    # Build the chapter title strip set lazily — uppercase forms of every
    # chapter title appear on divider pages and should be removed so they
    # don't bleed into the previous chapter's last section.
    upper_titles = {t.upper() for t in CHAPTER_TITLES.values()}

    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # Skip page header
        if PAGE_HEADER_PATTERN.match(stripped):
            continue

        # Skip page footers
        if any(p.match(stripped) for p in PAGE_FOOTER_PATTERNS):
            continue

        # Skip chapter divider lines ("Chapter 12" or "Chapter 12 MAKING THE...")
        if any(p.match(stripped) for p in CHAPTER_DIVIDER_PATTERNS):
            continue

        # Skip an isolated chapter title line on a divider page
        # (e.g. "MAKING THE REVIEW DECISION" alone on a line)
        if stripped in upper_titles:
            continue

        # Replace Wingdings bullet with standard bullet
        line = line.replace(WINGDINGS_BULLET, "- ")

        cleaned.append(line)

    text = "\n".join(cleaned)

    # Collapse excessive blank lines (more than 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# SECTION SPLITTING
# ============================================================

def _split_into_sections(raw_pages: list[dict]) -> list[dict]:
    """
    Walk through all extracted page text and split into sections
    at numbered section boundaries.

    A section heading is identified by the pattern:
        NNN.N  Section Title Text

    where NNN is a 3-4 digit number, optionally followed by dot-subsections,
    followed by at least 2 spaces, then text starting with a capital letter.

    The key challenge is distinguishing headings from inline references like
    "See Section 622" or "as described in 1021.1". We handle this by:
    1. Requiring the pattern to appear at the START of a line (after stripping)
    2. Requiring at least 2 spaces between the number and the title
    3. Requiring the text after the number to start with a capital letter
    """
    sections = []
    current_section = None
    current_text_parts = []
    current_pages = []
    current_handbook_pages = []
    current_tables = []
    current_flags = []
    current_example_texts = []

    # Collect all lines across all pages with their page metadata
    all_lines = []
    for raw_page in raw_pages:
        page_num = raw_page["pdf_page"]
        page_text = raw_page["text"]
        page_tables = raw_page["tables"]
        page_flags = raw_page["flags"]
        example_text = raw_page["example_text"]
        handbook_page = raw_page["handbook_page"]

        if not page_text:
            continue

        lines = page_text.split("\n")
        for line in lines:
            all_lines.append({
                "text": line.strip(),
                "page_num": page_num,
                "page_tables": page_tables,
                "page_flags": page_flags,
                "example_text": example_text,
                "handbook_page": handbook_page,
            })

    # Walk through all lines, detecting section boundaries
    i = 0
    while i < len(all_lines):
        entry = all_lines[i]
        stripped = entry["text"]
        page_num = entry["page_num"]
        page_tables = entry["page_tables"]
        page_flags = entry["page_flags"]
        example_text = entry["example_text"]
        handbook_page = entry["handbook_page"]

        if not stripped:
            current_text_parts.append("")
            i += 1
            continue

        # Check if this line starts a new section
        match = SECTION_HEADING_PATTERN.match(stripped)

        if match:
            section_num = match.group(1)
            title_text = match.group(2).strip()

            # Validate: the section number should be in a known chapter range
            base_num = int(section_num.split(".")[0])
            is_valid_section = any(
                lo <= base_num <= hi
                for lo, hi in CHAPTER_RANGES.values()
            )

            if is_valid_section:
                # Flush the current section
                if current_section is not None:
                    _flush_section(
                        sections, current_section, current_text_parts,
                        current_pages, current_handbook_pages,
                        current_tables, current_flags, current_example_texts,
                    )

                # Absorb continuation lines that are part of the heading.
                # A heading can span multiple lines in the PDF. The heading
                # ends when we hit: a period followed by a space and then
                # body text, a blank line, or the next section heading.
                full_heading_text = title_text
                j = i + 1
                while j < len(all_lines):
                    next_stripped = all_lines[j]["text"]
                    # Stop at blank lines
                    if not next_stripped:
                        break
                    # Stop at next section heading
                    if SECTION_HEADING_PATTERN.match(next_stripped):
                        next_base = int(
                            next_stripped.split()[0].split(".")[0]
                        )
                        if any(
                            lo <= next_base <= hi
                            for lo, hi in CHAPTER_RANGES.values()
                        ):
                            break
                    # Check if the current accumulated heading has ended
                    # (contains a sentence-ending pattern: ". " followed by
                    # body text, or just ends with a period)
                    if re.search(
                        r"\.\s+(?:[A-Z]|This|The|In|If|When|Each|A\s|An\s|For\s)",
                        full_heading_text,
                    ):
                        break
                    if full_heading_text.rstrip().endswith("."):
                        break
                    # Stop at bullet points — they indicate body content
                    if next_stripped.startswith(("- ", "* ", "• ")):
                        break
                    # This line is a continuation of the heading
                    full_heading_text += " " + next_stripped
                    j += 1

                # Start a new section with the full heading
                current_section = {
                    "section_number": section_num,
                    "raw_title": full_heading_text,
                }
                current_text_parts = [full_heading_text]
                current_pages = [page_num]
                current_handbook_pages = (
                    [handbook_page] if handbook_page else []
                )
                current_tables = list(page_tables)
                current_flags = list(page_flags)
                current_example_texts = (
                    [example_text] if example_text else []
                )
                # Skip past the continuation lines we consumed
                i = j
                continue

        # Not a section heading — append to current section text
        current_text_parts.append(stripped)

        # Track which pages this section spans
        if current_pages and page_num != current_pages[-1]:
            current_pages.append(page_num)
            if handbook_page and handbook_page not in current_handbook_pages:
                current_handbook_pages.append(handbook_page)
            current_tables.extend(page_tables)
            for flag in page_flags:
                if flag not in current_flags:
                    current_flags.append(flag)
            if example_text and example_text not in current_example_texts:
                    current_example_texts.append(example_text)

        i += 1

    # Don't forget the last section
    if current_section is not None:
        _flush_section(
            sections, current_section, current_text_parts,
            current_pages, current_handbook_pages,
            current_tables, current_flags, current_example_texts,
        )

    return sections


def _flush_section(
    sections: list[dict],
    section_info: dict,
    text_parts: list[str],
    pdf_pages: list[int],
    handbook_pages: list[str],
    tables: list[dict],
    flags: list[str],
    example_texts: list[str],
) -> None:
    """
    Finalize a section and append it to the sections list.
    """
    # Join text parts, collapsing excessive blank lines
    text = "\n".join(text_parts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text and not tables:
        return

    # Parse the section title from the raw title
    # The raw title often includes the first sentence of the section body.
    # The actual title ends at the first period followed by a space, or at
    # a long dash (—), whichever comes first.
    raw_title = section_info["raw_title"]
    title = _extract_section_title(raw_title)

    section = {
        "source": "FNS Handbook 310",
        "source_edition": "October 2025, Change 2 (January 13, 2026)",
        "chapter": None,  # filled by _enrich_section
        "chapter_title": None,
        "section_number": section_info["section_number"],
        "section_title": title,
        "level": None,  # filled by _enrich_section
        "parent_section": None,  # filled by _enrich_section
        "text": text,
        "tables": tables,
        "cross_references": [],  # filled by _enrich_section
        "pdf_pages": pdf_pages,
        "handbook_pages": handbook_pages,
        "flags": flags,
    }

    # Attach example box text if present
    if example_texts:
        section["example_text"] = "\n\n".join(example_texts)

    sections.append(section)


def _extract_section_title(raw_title: str) -> str:
    """
    Extract just the section title from the raw heading text.

    The raw title is everything after the section number on the heading line,
    which often includes the beginning of the section body. For example:

        "GENERAL. This handbook provides procedures for..."
        → title: "GENERAL"

        "Positive Allegation. When the household states..."
        → title: "Positive Allegation"

        "CITIZENSHIP AND NON-CITIZEN STATUS — 130."
        → title: "CITIZENSHIP AND NON-CITIZEN STATUS"

    We look for the title-ending pattern: a period followed by a space and
    more text (indicating the body has started), or a long dash.
    """
    # Try splitting at ". " (period-space) — the title is everything before
    # But only if what follows looks like a sentence (starts with capital
    # letter or "The", "This", etc.)
    match = re.match(
        r"^(.+?)\.\s+(?:[A-Z]|This|The|In|If|When|A\s|An\s|For\s)", raw_title
    )
    if match:
        return match.group(1).strip().rstrip(".")

    # Try splitting at em-dash
    if "—" in raw_title:
        parts = raw_title.split("—")
        return parts[0].strip().rstrip(".")

    # If no clear split point, take up to the first period
    if ". " in raw_title:
        return raw_title.split(". ")[0].strip()

    # Fall back to the whole thing (short headings without body text)
    return raw_title.strip().rstrip(".")


# ============================================================
# SOFT LINE-WRAP FLATTENING
# ============================================================

# Detect sentence terminators at end of a line (handles trailing close
# quotes / parens). Used to distinguish real paragraph breaks from PDF
# line-wrap artifacts.
_SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]?\s*$")

# Detect lines that are structural elements (bullets, list items, table
# rows) — these must stay on their own lines.
_STRUCTURAL_RE = re.compile(
    r"^(?:[•·➢▪○\-—–]\s+|\d+\.\s+|[A-Za-z]\.\s+|\([A-Za-z\d]{1,2}\)\s+|\|.*\|\s*$)"
)


def _flatten_soft_wraps(text: str) -> str:
    """
    Join consecutive prose lines that are PDF line-wrap artifacts rather
    than real paragraph breaks. PDF text extraction wraps lines at the
    visual column width, leaving every wrap point as a `\\n`. These
    wraps have no semantic meaning and should be flattened so chunk
    text reads as flowing prose.

    A line break is preserved when:
      - The next line is a structural element (bullet, numbered/lettered
        item, table row).
      - The next line is blank (paragraph separator).
      - The previous line ends with `.!?` AND the next line starts with
        a capital letter (real paragraph break).

    Otherwise the line break is treated as a soft wrap and replaced with
    a single space.

    Visual paragraph clarity: where a paragraph break is preserved AND it
    transitions from a prose line OR a structural list item BACK to prose,
    a blank line is inserted between them. This makes list-end visually
    obvious in the chunk text — readers can tell where a list stops and
    new prose begins.
    """
    if not text:
        return text

    lines = text.split("\n")
    out = []

    def append_with_blank():
        """Insert a blank-line separator before adding the next line, but
        only if there isn't already one."""
        if out and out[-1].strip():
            out.append("")

    for line in lines:
        stripped = line.strip()

        # Blank line: paragraph separator. Keep.
        if not stripped:
            out.append(line)
            continue

        if not out:
            out.append(line)
            continue

        prev_line = out[-1]
        prev_stripped = prev_line.strip()

        # If previous line is blank, can't merge into it
        if not prev_stripped:
            out.append(line)
            continue

        prev_is_structural = bool(_STRUCTURAL_RE.match(prev_stripped))
        cur_is_structural = bool(_STRUCTURAL_RE.match(stripped))

        # Current line is a structural element (bullet, table row, etc.)
        if cur_is_structural:
            # Insert a blank when transitioning from prose to a list start
            # (only when prev didn't end with a colon — colon-ending lines
            # are list intros that should flow directly into the list).
            if not prev_is_structural and not prev_stripped.endswith(":"):
                append_with_blank()
            out.append(line)
            continue

        # Real paragraph break: prev ends with sentence terminator AND
        # cur starts with a capital letter
        prev_terminates = bool(_SENTENCE_END_RE.search(prev_stripped))
        cur_capital = stripped[0].isupper()
        if prev_terminates and cur_capital:
            # Insert a blank before the new paragraph for visual clarity.
            # This is especially important for bullet → prose transitions
            # (list end) and prose → prose paragraph breaks.
            append_with_blank()
            out.append(line)
            continue

        # Otherwise: soft wrap. Merge into previous line with a space.
        out[-1] = prev_line.rstrip() + " " + stripped

    return "\n".join(out)


# ============================================================
# SECTION ENRICHMENT
# ============================================================

def _enrich_section(section: dict) -> None:
    """
    Add derived metadata to a section: chapter, level, parent, and
    cross-references.
    """
    sec_num = section["section_number"]

    # Flatten soft line wraps (PDF column-width artifacts) in the section
    # text and example_text. After this, line breaks are semantically
    # meaningful (paragraph or structural), not visual layout noise.
    section["text"] = _flatten_soft_wraps(section["text"])
    if section.get("example_text"):
        section["example_text"] = _flatten_soft_wraps(section["example_text"])

    # Determine chapter from section number
    base_num = int(sec_num.split(".")[0])
    chapter = None
    for ch, (lo, hi) in CHAPTER_RANGES.items():
        if lo <= base_num <= hi:
            chapter = ch
            break
    section["chapter"] = chapter
    section["chapter_title"] = CHAPTER_TITLES.get(chapter)

    # Determine hierarchy level
    # Level 0: x00 numbers (chapter-level, e.g., 100, 200, 800, 1000)
    # Level 1: x10, x20, etc. (major sections, e.g., 110, 820, 1020)
    # Level 2: x11, x12, etc. (sections, e.g., 811, 1021)
    # Level 3: dot-subsections (e.g., 154.1, 1021.1)
    if "." in sec_num:
        section["level"] = 3
        section["parent_section"] = sec_num.rsplit(".", 1)[0]
    elif base_num % 100 == 0:
        section["level"] = 0
        section["parent_section"] = None
    elif base_num % 10 == 0:
        section["level"] = 1
        section["parent_section"] = str((base_num // 100) * 100)
    else:
        section["level"] = 2
        section["parent_section"] = str((base_num // 10) * 10)

    # Extract cross-references from the text
    # Normalize the text first — remove newlines that break references
    normalized_text = re.sub(r"\n\s*", " ", section["text"])

    cross_refs = set()
    for pattern in CROSS_REF_PATTERNS:
        for match in pattern.finditer(normalized_text):
            groups = [g for g in match.groups() if g is not None]
            for g in groups:
                # Normalize: just keep the reference number/identifier
                g = g.strip()
                if re.match(r"^\d{3,4}(\.\d+)*$", g):
                    cross_refs.add(f"Section {g}")
                elif re.match(r"^\d{1,2}$", g):
                    cross_refs.add(f"Chapter {g}")

    section["cross_references"] = sorted(cross_refs)


# ============================================================
# TABLE EXTRACTION
# ============================================================

def _extract_tables(page) -> list[dict]:
    """
    Extract tables from a PDF page using pdfplumber.

    Returns a list of table dicts, each with:
        - headers: first row if it looks like headers, else None
        - rows: list of lists of cell text
    """
    try:
        raw_tables = page.extract_tables()
    except Exception:
        return []

    if not raw_tables:
        return []

    tables = []
    for raw_table in raw_tables:
        if not raw_table or len(raw_table) < 2:
            continue

        # Clean cell text
        cleaned_rows = []
        for row in raw_table:
            cleaned_row = [
                _clean_cell(cell) for cell in row
            ]
            cleaned_rows.append(cleaned_row)

        # Heuristic: if the first row has shorter text than average
        # and no empty cells, treat it as headers
        first_row = cleaned_rows[0]
        data_rows = cleaned_rows[1:]

        has_headers = (
            all(cell for cell in first_row)  # no empty header cells
            and len(first_row) > 1
        )

        if has_headers:
            tables.append({
                "headers": first_row,
                "rows": data_rows,
            })
        else:
            tables.append({
                "headers": None,
                "rows": cleaned_rows,
            })

    return tables


def _clean_cell(cell) -> str:
    """Clean a table cell value."""
    if cell is None:
        return ""
    text = str(cell).strip()
    # Replace Wingdings bullets
    text = text.replace(WINGDINGS_BULLET, "- ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text


# ============================================================
# CLI
# ============================================================

def main():
    """Command-line interface for the FNS Handbook parser."""
    parser = argparse.ArgumentParser(
        description="Parse FNS Handbook 310 PDF into structured JSON sections."
    )
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Only parse sections from this chapter number (1-14)"
    )
    parser.add_argument(
        "--pages", type=str, default=None,
        help="Only process these PDF pages (e.g., '195-200')"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show sections found without writing JSON files"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: parsed_sections/)"
    )

    args = parser.parse_args()

    # Load config
    project_root = Path(__file__).resolve().parents[2]
    config = configparser.ConfigParser()
    config_path = project_root / "config.ini"
    if not config_path.exists():
        print(f"Error: config.ini not found at {config_path}")
        sys.exit(1)
    config.read(config_path)

    pdf_path = config.get("fns", "pdf_path")
    # Resolve relative paths against the project root
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.join(project_root, pdf_path)

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    content_start = config.getint("fns", "content_start_page", fallback=18)
    content_end = config.getint("fns", "content_end_page", fallback=298)
    side_by_side_str = config.get("fns", "side_by_side_pages", fallback="")
    side_by_side_pages = [
        int(p.strip()) for p in side_by_side_str.split(",") if p.strip()
    ]

    # Parse page range if specified
    page_range = None
    if args.pages:
        parts = args.pages.split("-")
        if len(parts) == 2:
            page_range = (int(parts[0]), int(parts[1]))
        else:
            page_range = (int(parts[0]), int(parts[0]))

    # Run the parser
    sections = parse_handbook(
        pdf_path=pdf_path,
        content_start=content_start,
        content_end=content_end,
        side_by_side_pages=side_by_side_pages,
        chapter_filter=args.chapter,
        page_range=page_range,
    )

    if args.dry_run:
        print(f"\n{'='*70}")
        print("DRY RUN - Sections found:")
        print(f"{'='*70}")
        for s in sections:
            ch = s["chapter"] or "?"
            level_indent = "  " * (s["level"] or 0)
            flags = f" [{', '.join(s['flags'])}]" if s["flags"] else ""
            text_preview = s["text"][:80].replace("\n", " ")
            print(
                f"  Ch{ch:>2} {level_indent}[{s['section_number']}] "
                f"{s['section_title']}{flags}"
            )
            print(f"       {level_indent}  > {text_preview}...")
        print(f"\nTotal: {len(sections)} sections")
    else:
        output_dir = args.output or os.path.join(
            project_root, "index", "fns", "parsed_sections"
        )
        save_sections(sections, output_dir)


if __name__ == "__main__":
    main()
