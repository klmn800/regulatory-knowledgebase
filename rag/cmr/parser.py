"""
Parser for 106 CMR (Code of Massachusetts Regulations) PDFs.

Extracts structured sections from 18 CMR chapter PDFs using pdfplumber.
Each PDF covers one CMR chapter (e.g., 106 CMR 362 = SNAP Nonfinancial
Eligibility Standards).

Process:
  1. Open each PDF with pdfplumber
  2. Strip page headers ("106 CMR: DEPARTMENT OF TRANSITIONAL ASSISTANCE")
  3. Detect TOC boundary (first duplicate section number)
  4. Extract sections by chapter-filtered regex (XXX.XXX: Title)
  5. Merge continuation pages back into parent sections
  6. Handle one doubled-character PDF (704) via character-level dedup
  7. Extract cross-references and tables
  8. Output one JSON file per section to data/cmr/parsed_sections/

Output: ~600 JSON files in data/cmr/parsed_sections/

Usage:
    python parser.py                     # Parse all 18 PDFs
    python parser.py --chapter 362       # Parse one chapter
    python parser.py --dry-run           # Show sections found, don't write
"""

import argparse
import configparser
import json
import re
from pathlib import Path

import pdfplumber


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config.ini"
OUTPUT_DIR = PROJECT_ROOT / "index" / "cmr" / "parsed_sections"

PAGE_HEADER_PATTERN = re.compile(
    r"^106\s+CMR:?\s+DEPARTMENT\s+OF\s+TRANSITIONAL\s+ASSISTANCE\s*$",
    re.MULTILINE,
)

CHAPTER_PROGRAMS = {
    327: "Cross-Program",
    343: "Cross-Program",
    360: "SNAP",
    361: "SNAP",
    362: "SNAP",
    363: "SNAP",
    364: "SNAP",
    365: "SNAP",
    366: "SNAP",
    367: "SNAP",
    701: "TAFDC/EAEDC",
    702: "TAFDC/EAEDC",
    703: "TAFDC/EAEDC",
    704: "TAFDC/EAEDC",
    705: "TAFDC/EAEDC",
    706: "TAFDC/EAEDC",
    707: "TAFDC/EAEDC",
    708: "TAFDC/EAEDC",
}


def load_config() -> configparser.ConfigParser:
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


# ============================================================
# TEXT EXTRACTION
# ============================================================

def dedup_line(line: str) -> str:
    """
    Deduplicate a line with doubled characters.

    Some PDFs have font metrics that cause pdfplumber to double every
    character in extract_text() output. This removes consecutive
    identical non-space characters.
    """
    if not line.strip():
        return line
    result = []
    i = 0
    while i < len(line):
        result.append(line[i])
        if i + 1 < len(line) and line[i] == line[i + 1] and line[i] != " ":
            i += 2
        else:
            i += 1
    return "".join(result)


def extract_page_text(page: pdfplumber.page.Page, is_doubled: bool) -> str:
    """
    Extract text from a PDF page, handling doubled-character PDFs
    and stripping the standard page header.
    """
    text = page.extract_text() or ""

    if is_doubled:
        lines = text.split("\n")
        lines = [dedup_line(line) for line in lines]
        text = "\n".join(lines)

    text = PAGE_HEADER_PATTERN.sub("", text).strip()
    return text


# ============================================================
# CHAPTER TITLE EXTRACTION
# ============================================================

def extract_chapter_title(first_page_text: str, chapter_num: int) -> str:
    """
    Extract the chapter title from the first page of a CMR PDF.

    Looks for the pattern: 106 CMR XXX.000: TITLE
    """
    pattern = rf"106\s*CMR\s*{chapter_num}\.000:?\s+(.+?)(?:\n|Section)"
    match = re.search(pattern, first_page_text, re.DOTALL)
    if match:
        title = match.group(1).strip().replace("\n", " ")
        return title
    return f"CMR {chapter_num}"


# ============================================================
# TOC BOUNDARY DETECTION
# ============================================================

def find_toc_boundary(full_text: str, chapter_prefix: str) -> int:
    """
    Find where the Table of Contents ends and body content begins.

    The TOC lists section numbers, then those same numbers appear again
    with body text. The first duplicate section number marks the boundary.

    Returns the character index in full_text where body content starts,
    or 0 if no TOC is detected.
    """
    lines = full_text.split("\n")
    seen = set()
    pattern = re.compile(rf"^({chapter_prefix}\.\d{{3}}):?\s+")

    char_pos = 0
    for line in lines:
        match = pattern.match(line)
        if match:
            sec_num = match.group(1)
            if sec_num in seen:
                return char_pos
            seen.add(sec_num)
        char_pos += len(line) + 1  # +1 for newline

    return 0


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(full_text: str, chapter_prefix: str,
                     chapter_num: int, chapter_title: str,
                     pdf_file: str) -> list[dict]:
    """
    Extract sections from the body text of a CMR chapter.

    Splits text at section heading boundaries (XXX.XXX: Title),
    merges continuation pages, and builds structured section dicts.
    """
    body_start = find_toc_boundary(full_text, chapter_prefix)
    body_text = full_text[body_start:]

    heading_pattern = re.compile(
        rf"^({chapter_prefix}\.\d{{3}}):?\s+(.+?)$", re.MULTILINE
    )

    matches = list(heading_pattern.finditer(body_text))

    if not matches:
        return []

    sections_raw: dict[str, dict] = {}

    for i, match in enumerate(matches):
        sec_num = match.group(1)
        title_or_continued = match.group(2).strip()

        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        section_text = body_text[text_start:text_end].strip()

        is_continuation = title_or_continued.lower() == "continued"

        if is_continuation:
            if sec_num in sections_raw:
                sections_raw[sec_num]["text"] += "\n" + section_text
            continue

        if sec_num in sections_raw:
            sections_raw[sec_num]["text"] += "\n" + section_text
        else:
            sections_raw[sec_num] = {
                "section_number": sec_num,
                "section_title": title_or_continued,
                "text": section_text,
            }

    program = CHAPTER_PROGRAMS.get(chapter_num, "Unknown")

    result = []
    for sec_num, sec_data in sections_raw.items():
        text = sec_data["text"].strip()
        text = re.sub(r"\n{3,}", "\n\n", text)

        cross_refs = extract_cross_references(text)

        result.append({
            "source": "106 CMR",
            "chapter": chapter_num,
            "chapter_title": chapter_title,
            "section_number": sec_num,
            "section_title": sec_data["section_title"],
            "program": program,
            "text": text,
            "tables": [],
            "cross_references": cross_refs,
            "pdf_file": pdf_file,
        })

    return result


# ============================================================
# CROSS-REFERENCE EXTRACTION
# ============================================================

def extract_cross_references(text: str) -> list[str]:
    """
    Extract 106 CMR cross-references from section text.

    Matches patterns like:
      - 106 CMR 362.330
      - 106 CMR 362.330(A)
      - 106 CMR 362.330(A)(1)
    """
    refs = re.findall(r"106\s+CMR\s+(\d{3}\.\d{3}(?:\([A-Za-z0-9]+\))*)", text)
    unique = sorted(set(f"106 CMR {r}" for r in refs))
    return unique


# ============================================================
# TABLE EXTRACTION
# ============================================================

def extract_tables_from_pages(pdf: pdfplumber.PDF, chapter_prefix: str,
                              is_doubled: bool) -> dict[str, list[dict]]:
    """
    Extract tables from PDF pages and associate them with sections.

    Returns a dict mapping section_number to list of table dicts.
    """
    tables_by_section: dict[str, list[dict]] = {}

    for page in pdf.pages:
        raw_tables = page.extract_tables()
        if not raw_tables:
            continue

        page_text = extract_page_text(page, is_doubled)
        section_match = re.search(
            rf"^({chapter_prefix}\.\d{{3}}):?\s+", page_text, re.MULTILINE
        )
        sec_num = section_match.group(1) if section_match else None

        if not sec_num:
            continue

        for raw_table in raw_tables:
            if not raw_table or len(raw_table) < 2:
                continue

            headers = [str(cell or "") for cell in raw_table[0]]
            rows = []
            for row in raw_table[1:]:
                rows.append([str(cell or "") for cell in row])

            table = {"headers": headers, "rows": rows}

            if sec_num not in tables_by_section:
                tables_by_section[sec_num] = []
            tables_by_section[sec_num].append(table)

    return tables_by_section


# ============================================================
# PDF PROCESSING
# ============================================================

def get_chapter_num(filename: str) -> int | None:
    """Extract the CMR chapter number from a PDF filename."""
    match = re.search(r"(\d{3,4})\.pdf$", filename)
    if match:
        return int(match.group(1))
    return None


def parse_pdf(pdf_path: Path, is_doubled: bool = False) -> list[dict]:
    """
    Parse a single CMR PDF into structured sections.
    """
    filename = pdf_path.name
    chapter_num = get_chapter_num(filename)
    if chapter_num is None:
        print(f"  Warning: Could not determine chapter from {filename}")
        return []

    chapter_prefix = str(chapter_num)

    with pdfplumber.open(pdf_path) as pdf:
        page_texts = []
        for page in pdf.pages:
            page_texts.append(extract_page_text(page, is_doubled))

        full_text = "\n".join(page_texts)

        chapter_title = extract_chapter_title(page_texts[0], chapter_num)

        sections = extract_sections(
            full_text, chapter_prefix, chapter_num,
            chapter_title, filename
        )

        tables_by_section = extract_tables_from_pages(
            pdf, chapter_prefix, is_doubled
        )
        for section in sections:
            sec_num = section["section_number"]
            if sec_num in tables_by_section:
                section["tables"] = tables_by_section[sec_num]

    return sections


# ============================================================
# MAIN PROCESSING
# ============================================================

def parse_all(
    pdf_dir: Path,
    doubled_pdfs: set[str],
    chapter_filter: int | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """
    Parse all CMR PDFs and return/write structured sections.
    """
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return []

    if chapter_filter:
        pdf_files = [f for f in pdf_files if str(chapter_filter) in f.stem]
        if not pdf_files:
            print(f"No PDF found for chapter {chapter_filter}")
            return []

    all_sections = []
    total_files = len(pdf_files)

    for i, pdf_path in enumerate(pdf_files):
        is_doubled = pdf_path.name in doubled_pdfs
        doubled_tag = " [doubled-char fix]" if is_doubled else ""

        print(f"  [{i+1}/{total_files}] {pdf_path.name}{doubled_tag}...")

        sections = parse_pdf(pdf_path, is_doubled=is_doubled)
        all_sections.extend(sections)

        chapter_num = get_chapter_num(pdf_path.name)
        print(f"         {len(sections)} sections extracted")

    print()
    print_statistics(all_sections)

    if dry_run:
        print("\nDry run — no files written.")
        return all_sections

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for section in all_sections:
        sec_num = section["section_number"].replace(".", "_")
        ch = section["chapter"]
        filename = f"cmr{ch}_{sec_num}.json"
        filepath = OUTPUT_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(section, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(all_sections)} section files to {OUTPUT_DIR}")

    return all_sections


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(sections: list[dict]) -> None:
    """Print a summary of the parsing results."""
    if not sections:
        print("No sections parsed.")
        return

    print("=" * 60)
    print("106 CMR Parsing Statistics")
    print("=" * 60)
    print()

    print(f"Total sections: {len(sections)}")

    chapters = {}
    for s in sections:
        ch = s["chapter"]
        title = s["chapter_title"]
        key = (ch, title)
        chapters[key] = chapters.get(key, 0) + 1

    print(f"Chapters: {len(chapters)}")
    print()

    for (ch, title), count in sorted(chapters.items()):
        program = CHAPTER_PROGRAMS.get(ch, "?")
        print(f"  CMR {ch:>3}: {title[:50]:50s} {program:>12s}  ({count} sections)")
    print()

    sizes = [len(s["text"]) for s in sections]
    import statistics as stats_mod
    print(f"Section sizes:")
    print(f"  Median: {stats_mod.median(sizes):.0f} chars")
    print(f"  Mean:   {stats_mod.mean(sizes):.0f} chars")
    print(f"  Min:    {min(sizes)} chars")
    print(f"  Max:    {max(sizes)} chars")
    print()

    with_tables = sum(1 for s in sections if s["tables"])
    with_xrefs = sum(1 for s in sections if s["cross_references"])
    short = sum(1 for s in sections if len(s["text"]) < 100)
    print(f"Sections with tables:           {with_tables}")
    print(f"Sections with cross-references: {with_xrefs}")
    print(f"Short sections (<100 chars):    {short}")


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the CMR parser."""
    parser = argparse.ArgumentParser(
        description="Parse 106 CMR regulation PDFs into structured JSON sections.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parser.py                  # Parse all 18 PDFs
  python parser.py --chapter 362    # Parse one chapter
  python parser.py --dry-run        # Show sections found, don't write
        """,
    )
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Parse only this CMR chapter number (e.g., 362)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show sections found without writing files",
    )
    args = parser.parse_args()

    config = load_config()

    pdf_dir_str = config.get("cmr", "pdf_dir", fallback="raw/cmr")
    pdf_dir = PROJECT_ROOT / pdf_dir_str

    doubled_str = config.get("cmr", "doubled_pdfs", fallback="")
    doubled_pdfs = set(s.strip() for s in doubled_str.split(",") if s.strip())

    print(f"PDF directory: {pdf_dir}")
    print(f"Output directory: {OUTPUT_DIR}")
    if doubled_pdfs:
        print(f"Doubled-char PDFs: {', '.join(doubled_pdfs)}")
    print()

    parse_all(
        pdf_dir=pdf_dir,
        doubled_pdfs=doubled_pdfs,
        chapter_filter=args.chapter,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
