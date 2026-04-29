"""
Parser for 7 CFR (Code of Federal Regulations) SNAP regulation PDFs.

Extracts structured sections from 7 CFR Parts 271-292 using pdfplumber.
Each PDF covers one CFR part (e.g., 7 CFR 273 = Certification of Eligible
Households).

Process:
  1. Open each PDF with pdfplumber
  2. Strip page headers (3 lines) and footers (1 line)
  3. Extract subpart structure from TOC for context prefixes
  4. Detect TOC boundary (first duplicate section number)
  5. Extract sections by part-filtered regex (§ {part}.{section} Title)
  6. Strip amendment notes and editorial notes
  7. Extract cross-references
  8. Output one JSON file per section to index/cfr/parsed_sections/

Output: ~118 JSON files in index/cfr/parsed_sections/

Usage:
    python parser.py                     # Parse all 7 PDFs
    python parser.py --part 273          # Parse one part
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
OUTPUT_DIR = PROJECT_ROOT / "index" / "cfr" / "parsed_sections"

# Page header: 3 lines at top of every page
# Line 0: "7 CFR Part 273 (up to date as of 4/20/2026)"
# Line 1: "7 CFR Part 273 (Apr. 20, 2026)" or "7 CFR 273.9(d)(4)(i)" (breadcrumb)
# Line 2: "Certification of Eligible Households" (part title)
PAGE_HEADER_LINE0 = re.compile(
    r"^7\s+CFR\s+Part\s+\d+\s+\(up\s+to\s+date\s+as\s+of\s+", re.IGNORECASE
)
PAGE_HEADER_LINE1 = re.compile(
    r"^7\s+CFR\s+(?:Part\s+)?\d+", re.IGNORECASE
)

# Page footer: last line of every page
# "7 CFR 273.9(d)(4)(i) (enhanced display) page 2 of 252"
PAGE_FOOTER = re.compile(
    r"^7\s+CFR\s+.*\(enhanced\s+display\)\s+page\s+\d+\s+of\s+\d+\s*$",
    re.IGNORECASE,
)

# Amendment note patterns
# [Amdt. 132,43 FR 47882, Oct. 17, 1978]
# [82 FR 2034, Jan. 6, 2017, as amended at 89 FR 90568, Nov. 18, 2024]
AMENDMENT_NOTE = re.compile(
    r"\[(?:Amdt\.\s*\d+,?)?\s*\d+\s+FR\s+\d+.*?\]",
    re.DOTALL,
)

# Editorial notes that follow amendment blocks
EDITORIAL_NOTE = re.compile(
    r"Editorial\s+Note:.*?(?=\n§|\n[A-Z]|\Z)",
    re.DOTALL,
)

# Subpart heading in body text: "Subpart A—General Rules"
SUBPART_HEADING = re.compile(
    r"^Subpart\s+([A-Z])\s*[\u2014\u2013—-]+\s*(.+?)$",
    re.MULTILINE,
)

# Part number from filename: "7 CFR Part 273 (up to date as of 4-20-2026).pdf"
FILENAME_PART = re.compile(r"Part\s+(\d+)")


def load_config() -> configparser.ConfigParser:
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_page_text(page: pdfplumber.page.Page) -> str:
    """
    Extract text from a PDF page, stripping header (3 lines) and
    footer (1 line).
    """
    text = page.extract_text() or ""
    lines = text.split("\n")

    if not lines:
        return ""

    # Strip header: first 3 lines match known patterns
    strip_top = 0
    if lines and PAGE_HEADER_LINE0.match(lines[0]):
        strip_top = 1
        if len(lines) > 1 and PAGE_HEADER_LINE1.match(lines[1]):
            strip_top = 2
            # Line 2 is the part title — always present on body pages
            if len(lines) > 2:
                strip_top = 3

    # Strip footer: last line matches "(enhanced display) page N of M"
    strip_bottom = 0
    if lines and PAGE_FOOTER.match(lines[-1]):
        strip_bottom = 1

    end = len(lines) - strip_bottom if strip_bottom else len(lines)
    body_lines = lines[strip_top:end]

    return "\n".join(body_lines).strip()


# ============================================================
# PART TITLE AND METADATA EXTRACTION
# ============================================================

def get_part_num(filename: str) -> int | None:
    """Extract the CFR part number from a PDF filename."""
    match = FILENAME_PART.search(filename)
    if match:
        return int(match.group(1))
    return None


def extract_part_title(raw_first_page: str, part_num: int) -> str:
    """
    Extract the part title from the raw first page of a CFR PDF.

    Primary method: line 2 of raw first page is always the title
    (e.g., "Certification of Eligible Households").
    Fallback: look for "PART {num}—TITLE" in the provided text.
    """
    lines = raw_first_page.split("\n")

    # Primary: line 2 is always the part title in these eCFR PDFs
    if len(lines) > 2:
        candidate = lines[2].strip()
        if (candidate and not candidate.startswith("7 CFR")
                and not candidate.startswith("This content")):
            return candidate

    # Fallback: look for "PART 273—CERTIFICATION OF ELIGIBLE HOUSEHOLDS"
    # Title may wrap to the next line (Part 280)
    pattern = rf"PART\s+{part_num}\s*[\u2014\u2013—-]+\s*(.+?)$"
    match = re.search(pattern, raw_first_page, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        for i, line in enumerate(lines):
            if line.strip().startswith(f"PART {part_num}"):
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith("Authority:") or not next_line:
                        break
                    if next_line.isupper() or next_line[0].isupper():
                        title += " " + next_line
                    else:
                        break
                break
        return title

    return f"7 CFR {part_num}"


# ============================================================
# SUBPART EXTRACTION
# ============================================================

def extract_subpart_map(full_text: str, part_num: int) -> dict[str, dict]:
    """
    Build a mapping of section_number -> subpart info.

    Parses the TOC to find which sections belong to which subpart.
    Returns: {section_num: {"letter": "D", "title": "Eligibility and Benefit Levels"}}
    """
    section_pattern = re.compile(
        rf"§\s*{part_num}\.(\d{{1,2}})\s+"
    )

    # Parse subpart headings and following section entries from TOC
    lines = full_text.split("\n")
    current_subpart = None
    section_to_subpart: dict[str, dict] = {}
    seen_sections = set()

    for line in lines:
        # Check for subpart heading (both TOC and body formats)
        sub_match = re.match(
            r"Subpart\s+([A-Z])\s*[\u2014\u2013—\-\s]+(.+?)$", line.strip()
        )
        if sub_match:
            current_subpart = {
                "letter": sub_match.group(1),
                "title": sub_match.group(2).strip(),
            }
            continue

        # Check for section entry
        sec_match = section_pattern.match(line.strip())
        if sec_match and current_subpart:
            sec_num = f"{part_num}.{sec_match.group(1)}"
            if sec_num not in seen_sections:
                seen_sections.add(sec_num)
                section_to_subpart[sec_num] = dict(current_subpart)

    return section_to_subpart


# ============================================================
# TOC BOUNDARY DETECTION
# ============================================================

def find_toc_boundary(full_text: str, part_num: int) -> int:
    """
    Find where the Table of Contents ends and body content begins.

    The TOC lists section numbers, then those same numbers appear again
    in the body text. The first duplicate section number marks the boundary.

    Returns the character index in full_text where body content starts,
    or 0 if no TOC is detected.
    """
    lines = full_text.split("\n")
    seen = set()
    pattern = re.compile(rf"§\s*{part_num}\.(\d{{1,2}})\b")

    char_pos = 0
    for line in lines:
        match = pattern.search(line.strip())
        if match:
            sec_id = match.group(1)
            if sec_id in seen:
                return char_pos
            seen.add(sec_id)
        char_pos += len(line) + 1  # +1 for newline

    return 0


# ============================================================
# AMENDMENT/EDITORIAL NOTE STRIPPING
# ============================================================

def strip_amendment_notes(text: str) -> str:
    """
    Remove amendment citation blocks and editorial notes from section text.

    These add noise to embeddings without policy content.
    """
    text = AMENDMENT_NOTE.sub("", text)
    text = EDITORIAL_NOTE.sub("", text)
    return text.strip()


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(full_text: str, part_num: int, part_title: str,
                     subpart_map: dict, pdf_file: str) -> list[dict]:
    """
    Extract sections from the body text of a CFR part.

    Splits text at section heading boundaries (§ {part}.{section} Title).
    Skips [Reserved] sections.
    """
    body_start = find_toc_boundary(full_text, part_num)
    body_text = full_text[body_start:]

    # Section heading pattern: "§ 273.9 Income and deductions."
    # Must start at line beginning (not inline cross-references)
    heading_pattern = re.compile(
        rf"^§\s*({part_num}\.\d{{1,2}})\s+(.+?)$", re.MULTILINE
    )

    matches = list(heading_pattern.finditer(body_text))

    if not matches:
        return []

    sections_raw: dict[str, dict] = {}

    for i, match in enumerate(matches):
        sec_num = match.group(1)
        title = match.group(2).strip()

        # Skip [Reserved] sections
        if "[Reserved]" in title:
            continue

        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        section_text = body_text[text_start:text_end].strip()

        # If we see the same section number again (shouldn't happen post-TOC,
        # but defensive), merge the text
        if sec_num in sections_raw:
            sections_raw[sec_num]["text"] += "\n" + section_text
        else:
            sections_raw[sec_num] = {
                "section_number": sec_num,
                "section_title": title.rstrip("."),
                "text": section_text,
            }

    result = []
    for sec_num, sec_data in sections_raw.items():
        text = sec_data["text"].strip()
        text = strip_amendment_notes(text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        cross_refs = extract_cross_references(text)
        subpart = subpart_map.get(sec_num)

        section = {
            "source": "7 CFR",
            "part": part_num,
            "part_title": part_title,
            "section_number": sec_num,
            "section_title": sec_data["section_title"],
            "text": text,
            "tables": [],
            "cross_references": cross_refs,
            "pdf_file": pdf_file,
        }

        if subpart:
            section["subpart_letter"] = subpart["letter"]
            section["subpart_title"] = subpart["title"]

        result.append(section)

    return result


# ============================================================
# CROSS-REFERENCE EXTRACTION
# ============================================================

def extract_cross_references(text: str) -> list[str]:
    """
    Extract CFR cross-references from section text.

    Matches patterns like:
      - § 273.9
      - § 273.9(d)(6)
      - 7 U.S.C. 2015
    """
    cfr_refs = re.findall(
        r"§\s*(\d{3}\.\d{1,2}(?:\([A-Za-z0-9]+\))*)", text
    )
    unique_cfr = sorted(set(f"§ {r}" for r in cfr_refs))

    usc_refs = re.findall(
        r"(\d+\s+U\.S\.C\.\s+\d+[a-z]*(?:-\d+[a-z]*)?)", text
    )
    unique_usc = sorted(set(usc_refs))

    return unique_cfr + unique_usc


# ============================================================
# TABLE EXTRACTION
# ============================================================

def extract_tables_from_pages(pdf: pdfplumber.PDF,
                              part_num: int) -> dict[str, list[dict]]:
    """
    Extract tables from PDF pages and associate them with sections.

    Returns a dict mapping section_number to list of table dicts.
    """
    tables_by_section: dict[str, list[dict]] = {}
    sec_pattern = re.compile(rf"§\s*({part_num}\.\d{{1,2}})\b")

    for page in pdf.pages:
        raw_tables = page.extract_tables()
        if not raw_tables:
            continue

        page_text = extract_page_text(page)
        # Find the last section heading on this page
        sec_matches = list(sec_pattern.finditer(page_text))
        sec_num = sec_matches[-1].group(1) if sec_matches else None

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

def parse_pdf(pdf_path: Path) -> list[dict]:
    """Parse a single CFR PDF into structured sections."""
    filename = pdf_path.name
    part_num = get_part_num(filename)
    if part_num is None:
        print(f"  Warning: Could not determine part from {filename}")
        return []

    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from all pages
        page_texts = []
        for page in pdf.pages:
            page_texts.append(extract_page_text(page))

        full_text = "\n".join(page_texts)

        # Get part title from raw first page (before header stripping)
        raw_first_page = pdf.pages[0].extract_text() or ""
        part_title = extract_part_title(raw_first_page, part_num)

        # Extract subpart mapping from TOC pages (may span 2-3 pages)
        toc_pages = min(3, len(pdf.pages))
        raw_toc_text = "\n".join(
            pdf.pages[i].extract_text() or "" for i in range(toc_pages)
        )
        subpart_map = extract_subpart_map(raw_toc_text, part_num)

        # Extract sections
        sections = extract_sections(
            full_text, part_num, part_title,
            subpart_map, filename
        )

        # Extract and associate tables
        tables_by_section = extract_tables_from_pages(pdf, part_num)
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
    part_filter: int | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Parse all CFR PDFs and return/write structured sections."""
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return []

    if part_filter:
        pdf_files = [f for f in pdf_files if f"Part {part_filter}" in f.name]
        if not pdf_files:
            print(f"No PDF found for part {part_filter}")
            return []

    all_sections = []
    total_files = len(pdf_files)

    for i, pdf_path in enumerate(pdf_files):
        print(f"  [{i+1}/{total_files}] {pdf_path.name}...")
        sections = parse_pdf(pdf_path)
        all_sections.extend(sections)
        print(f"         {len(sections)} sections extracted")

    print()
    print_statistics(all_sections)

    if dry_run:
        print("\nDry run -- no files written.")
        return all_sections

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for section in all_sections:
        sec_num = section["section_number"].replace(".", "_")
        part = section["part"]
        filename = f"cfr{part}_{sec_num}.json"
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
    print("7 CFR Parsing Statistics")
    print("=" * 60)
    print()

    print(f"Total sections: {len(sections)}")

    parts = {}
    for s in sections:
        part = s["part"]
        title = s["part_title"]
        key = (part, title)
        parts[key] = parts.get(key, 0) + 1

    print(f"Parts: {len(parts)}")
    print()

    for (part, title), count in sorted(parts.items()):
        subparts_in_part = set()
        for s in sections:
            if s["part"] == part and "subpart_letter" in s:
                subparts_in_part.add(s["subpart_letter"])
        sub_tag = f"  [{len(subparts_in_part)} subparts]" if subparts_in_part else ""
        print(f"  Part {part:>3}: {title[:50]:50s} ({count} sections){sub_tag}")
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
    with_subpart = sum(1 for s in sections if "subpart_letter" in s)
    short = sum(1 for s in sections if len(s["text"]) < 100)
    long = sum(1 for s in sections if len(s["text"]) > 10000)
    print(f"Sections with tables:           {with_tables}")
    print(f"Sections with cross-references: {with_xrefs}")
    print(f"Sections with subpart info:     {with_subpart}")
    print(f"Short sections (<100 chars):    {short}")
    print(f"Long sections (>10k chars):     {long}")


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the CFR parser."""
    parser = argparse.ArgumentParser(
        description="Parse 7 CFR regulation PDFs into structured JSON sections.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parser.py                  # Parse all 7 PDFs
  python parser.py --part 273       # Parse one part
  python parser.py --dry-run        # Show sections found, don't write
        """,
    )
    parser.add_argument(
        "--part", type=int, default=None,
        help="Parse only this CFR part number (e.g., 273)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show sections found without writing files",
    )
    args = parser.parse_args()

    config = load_config()

    pdf_dir_str = config.get("cfr", "pdf_dir", fallback="raw/cfr")
    pdf_dir = PROJECT_ROOT / pdf_dir_str

    print(f"PDF directory: {pdf_dir}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    parse_all(
        pdf_dir=pdf_dir,
        part_filter=args.part,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
