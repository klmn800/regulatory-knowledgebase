"""
HTML Parser for DTA Online Policy Guide pages.

Takes raw HTML from MadCap Flare WebHelp pages and extracts structured
content suitable for downstream RAG chunking.

The parser targets the content inside <div id="rh-topic"> and extracts:
  - Page title (from the H1 tag)
  - Sections split at H2/H3 boundaries, each with heading, level, and text
  - Tables preserved as structured data (headers + rows)
  - Internal cross-reference links with resolved URLs
  - "Last Update" date from the bottom of the page

Design notes:
  - This module is a pure parser — no network calls, no file I/O.
  - The scraper calls parse_page() with raw HTML and gets back a dict.
  - Tables with images but no real text are treated as layout/decorative
    and skipped. Data tables (often class="MA") are preserved.
  - Sections are returned as a flat list with a "level" field (0 = intro
    before first heading, 2 = H2, 3 = H3) so the chunker can iterate
    sequentially while still knowing the hierarchy.

Usage:
    from parser import parse_page

    result = parse_page(html_string, page_url="https://...")
    # result is a dict with keys: title, last_updated, sections, tables,
    #   internal_links
"""

import re
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin


# ============================================================
# PUBLIC API
# ============================================================

def parse_page(html: str, page_url: str = "") -> dict:
    """
    Parse a single DTA Online Guide HTML page into structured data.

    Args:
        html: Raw HTML string of the full page.
        page_url: The source URL of the page. Used to resolve relative
                  links into absolute URLs. Optional but recommended.

    Returns:
        A dictionary with the following structure:
        {
            "title": "Page Title from H1",
            "last_updated": "October 18, 2014" or None,
            "sections": [
                {"heading": None, "level": 0, "text": "Intro text..."},
                {"heading": "Section Name", "level": 2, "text": "..."},
                {"heading": "Subsection", "level": 3, "text": "..."},
            ],
            "tables": [
                {
                    "context_heading": "nearest heading above",
                    "headers": ["Col1", "Col2"] or None,
                    "rows": [["cell1", "cell2"], ...]
                }
            ],
            "internal_links": [
                {"text": "Link Text", "href": "https://resolved/url"}
            ]
        }
    """
    soup = BeautifulSoup(html, "html.parser")

    # All content lives inside <div id="rh-topic">
    topic_div = soup.find("div", id="rh-topic")
    if not topic_div:
        return {
            "title": _extract_title_fallback(soup),
            "last_updated": None,
            "sections": [],
            "tables": [],
            "internal_links": [],
        }

    title = _extract_title(topic_div)
    last_updated = _extract_last_updated(topic_div)
    sections = _extract_sections(topic_div)
    tables = _extract_tables(topic_div)
    internal_links = _extract_internal_links(topic_div, page_url)

    return {
        "title": title,
        "last_updated": last_updated,
        "sections": sections,
        "tables": tables,
        "internal_links": internal_links,
    }


# ============================================================
# TITLE EXTRACTION
# ============================================================

def _extract_title(topic_div: Tag) -> str:
    """
    Pull the page title from the first H1 tag inside the content div.
    """
    h1 = topic_div.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return ""


def _extract_title_fallback(soup: BeautifulSoup) -> str:
    """
    If there's no content div at all, try the <title> tag as a fallback.
    """
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""


# ============================================================
# LAST UPDATED DATE
# ============================================================

def _extract_last_updated(topic_div: Tag) -> str | None:
    """
    The "Last Update" date typically appears at the very bottom of the
    page as an H3 like: <h3>Last Update: October 18, 2014</h3>

    We search for it and extract just the date portion.
    """
    # Look for H3 tags containing "Last Update"
    for h3 in topic_div.find_all("h3"):
        text = h3.get_text(strip=True)
        match = re.match(r"Last\s+Update[:\s]*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Some pages might use a different tag or format — try a broader search
    full_text = topic_div.get_text()
    match = re.search(r"Last\s+Update[:\s]*([A-Z][a-z]+ \d{1,2},?\s*\d{4})", full_text)
    if match:
        return match.group(1).strip()

    return None


# ============================================================
# SECTION EXTRACTION
# ============================================================

def _extract_sections(topic_div: Tag) -> list[dict]:
    """
    Split page content into sections at H2/H3 boundaries.

    Walks through the direct children of the content div. Everything
    before the first heading becomes a level-0 "intro" section. Each
    H2 starts a level-2 section, each H3 a level-3 section.

    The text for each section includes all paragraphs, lists, and other
    content up until the next heading (or end of page).

    The "Last Update" H3 at the bottom is excluded from sections.
    """
    sections = []
    current_heading = None
    current_level = 0
    current_parts = []

    for element in topic_div.children:
        if isinstance(element, NavigableString):
            text = element.strip()
            # Filter out CDATA blocks and other script remnants
            if text and not re.match(r"^//\s*<!\[CDATA\[", text) and not re.match(r"^//\s*\]\]>", text):
                current_parts.append(text)
            continue

        if not isinstance(element, Tag):
            continue

        tag_name = element.name.lower() if element.name else ""

        # Skip script and style tags entirely — they sometimes appear
        # inline in the content div and leak CDATA blocks into text
        if tag_name in ("script", "style", "link", "meta"):
            continue

        # Check if this is a section heading (H2 or H3)
        if tag_name in ("h2", "h3"):
            heading_text = element.get_text(strip=True)

            # Skip the "Last Update" heading — we extract that separately
            if re.match(r"Last\s+Update", heading_text, re.IGNORECASE):
                continue

            # Save the current section before starting a new one
            _flush_section(sections, current_heading, current_level, current_parts)

            # Start a new section
            current_heading = heading_text
            current_level = int(tag_name[1])  # 2 or 3
            current_parts = []

        elif tag_name == "h1":
            # Skip the title — we extract that separately
            continue

        elif tag_name == "hr":
            # Horizontal rules are section separators, not content
            continue

        elif tag_name == "table":
            # Tables are extracted separately — skip them in section text,
            # but add a placeholder so we know a table was here
            current_parts.append("[Table]")

        else:
            # Extract text content from paragraphs, lists, etc.
            text = _element_to_text(element)
            if text:
                current_parts.append(text)

    # Don't forget the last section
    _flush_section(sections, current_heading, current_level, current_parts)

    return sections


def _flush_section(
    sections: list[dict],
    heading: str | None,
    level: int,
    parts: list[str],
) -> None:
    """
    Finalize a section and append it to the sections list, but only
    if there's actual content (heading or text).
    """
    text = "\n\n".join(part for part in parts if part.strip())

    if heading or text.strip():
        sections.append({
            "heading": heading,
            "level": level,
            "text": text.strip(),
        })


def _element_to_text(element: Tag) -> str:
    """
    Convert an HTML element into clean text, preserving list structure
    with bullet/number markers so lists remain readable.

    Handles: <p>, <ul>, <ol>, <div>, <span>, <strong>, <em>, etc.
    """
    tag_name = element.name.lower() if element.name else ""

    if tag_name == "ul":
        return _list_to_text(element, ordered=False)

    if tag_name == "ol":
        return _list_to_text(element, ordered=True)

    # For everything else, just get the text with whitespace cleaned up
    text = element.get_text(separator=" ", strip=True)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def _list_to_text(list_element: Tag, ordered: bool = False) -> str:
    """
    Convert a <ul> or <ol> into readable text with bullet markers.

    Nested lists are indented. For example:
        - First item
        - Second item
          1. Nested ordered item
          2. Another nested item
        - Third item
    """
    lines = []
    for i, li in enumerate(list_element.find_all("li", recursive=False), start=1):
        marker = f"{i}." if ordered else "-"

        # Get the direct text of this <li> (excluding nested lists)
        parts = []
        for child in li.children:
            if isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    parts.append(text)
            elif isinstance(child, Tag):
                if child.name in ("ul", "ol"):
                    # Handle nested list — will be appended as indented block
                    nested = _list_to_text(child, ordered=(child.name == "ol"))
                    # Indent nested list
                    indented = "\n".join(
                        "  " + line for line in nested.split("\n") if line
                    )
                    parts.append("\n" + indented)
                else:
                    text = child.get_text(separator=" ", strip=True)
                    if text:
                        parts.append(text)

        li_text = " ".join(
            p for p in parts if p and not p.startswith("\n")
        )
        nested_text = "\n".join(
            p for p in parts if p and p.startswith("\n")
        )

        lines.append(f"{marker} {li_text}")
        if nested_text:
            lines.append(nested_text)

    return "\n".join(lines)


# ============================================================
# TABLE EXTRACTION
# ============================================================

def _extract_tables(topic_div: Tag) -> list[dict]:
    """
    Extract all data tables from the page content.

    Skips "layout" tables that are just used for decorative purposes
    (e.g., the "New Update" image banner). A table is considered
    layout/decorative if it contains images but very little text.

    For each real data table, we extract:
      - context_heading: the nearest H2/H3 above the table
      - headers: first row if it looks like a header row, else None
      - rows: all data rows as lists of cell text

    Handles colspan by repeating cell values, and rowspan by carrying
    cell values down into subsequent rows.
    """
    tables = []

    for table_el in topic_div.find_all("table"):
        # Skip decorative/layout tables
        if _is_layout_table(table_el):
            continue

        context_heading = _find_nearest_heading(table_el)
        headers, rows = _parse_table_data(table_el)

        if rows or headers:
            tables.append({
                "context_heading": context_heading,
                "headers": headers,
                "rows": rows,
            })

    return tables


def _is_layout_table(table_el: Tag) -> bool:
    """
    Heuristic to detect layout/decorative tables.

    A table is likely decorative if:
    - It contains <img> tags and has very little text content
    - It has only 1 row and the text is minimal
    """
    imgs = table_el.find_all("img")
    text = table_el.get_text(strip=True)

    # If it has images and the text-to-image ratio is low, it's layout
    if imgs and len(text) < 200:
        return True

    # Single-row tables with very little text are often layout
    rows = table_el.find_all("tr")
    if len(rows) == 1 and len(text) < 50:
        return True

    return False


def _find_nearest_heading(element: Tag) -> str | None:
    """
    Walk backwards through previous siblings and parents to find the
    nearest H2 or H3 heading above this element.
    """
    current = element

    while current:
        # Check previous siblings
        sibling = current.previous_sibling
        while sibling:
            if isinstance(sibling, Tag) and sibling.name in ("h2", "h3"):
                text = sibling.get_text(strip=True)
                if not re.match(r"Last\s+Update", text, re.IGNORECASE):
                    return text
            sibling = sibling.previous_sibling

        # Move up to parent and keep looking
        current = current.parent
        if current and isinstance(current, Tag) and current.get("id") == "rh-topic":
            break

    return None


def _parse_table_data(table_el: Tag) -> tuple[list[str] | None, list[list[str]]]:
    """
    Parse an HTML table into headers and rows.

    Looks for <thead> first; if not present, checks whether the first
    row contains <th> elements. If neither, returns headers as None.

    Handles colspan by repeating cell text across columns, and rowspan
    by carrying cell text down into subsequent rows.
    """
    # Collect all rows from thead + tbody, or just all <tr> tags
    thead = table_el.find("thead")
    tbody = table_el.find("tbody")

    header_rows = []
    data_rows = []

    if thead:
        header_rows = thead.find_all("tr")
    if tbody:
        data_rows = tbody.find_all("tr")
    else:
        # No explicit tbody — all <tr> tags are data rows
        all_rows = table_el.find_all("tr")
        if thead:
            data_rows = [r for r in all_rows if r.parent != thead]
        else:
            data_rows = all_rows

    # Parse header rows
    headers = None
    if header_rows:
        # Use the first header row
        headers = _parse_row_cells(header_rows[0])
    elif data_rows:
        # Check if the first data row uses <th> tags
        first_row = data_rows[0]
        th_cells = first_row.find_all("th")
        if th_cells and not first_row.find_all("td"):
            headers = [_extract_cell_text(cell) for cell in th_cells]
            data_rows = data_rows[1:]  # remove header from data

    # Parse data rows with colspan/rowspan handling
    rows = _parse_rows_with_spans(data_rows)

    return headers, rows


def _extract_cell_text(cell: Tag) -> str:
    """
    Extract text from a table cell, inserting separators between
    block-level elements so items don't run together.

    For example, a cell containing:
        <td>Sign forms<br/>Report info<br/>Discuss case</td>
    becomes:
        "Sign forms; Report info; Discuss case"
    """
    # Work on a copy so we don't modify the original soup tree
    import copy
    cell_copy = copy.copy(cell)

    # Insert a marker before each <br> and block-level element
    # so get_text() produces separable segments
    for br in cell_copy.find_all("br"):
        br.replace_with("\n")
    for block in cell_copy.find_all(["p", "div", "li"]):
        block.insert_before("\n")

    raw = cell_copy.get_text()

    # Split on newlines, clean each segment, rejoin with semicolons
    segments = [seg.strip() for seg in raw.split("\n") if seg.strip()]

    if len(segments) <= 1:
        return raw.strip()
    return "; ".join(segments)


def _parse_row_cells(row: Tag) -> list[str]:
    """Extract cell text from a single <tr>, handling colspan."""
    cells = []
    for cell in row.find_all(["td", "th"]):
        text = _extract_cell_text(cell)
        colspan = int(cell.get("colspan", 1))
        for _ in range(colspan):
            cells.append(text)
    return cells


def _parse_rows_with_spans(rows: list[Tag]) -> list[list[str]]:
    """
    Parse table rows handling both colspan and rowspan.

    For rowspan, we carry the cell's value down into subsequent rows
    at the same column position. For colspan, we repeat the cell's
    value across multiple columns.
    """
    if not rows:
        return []

    parsed = []
    # Track active rowspans: {col_index: (text, remaining_rows)}
    active_rowspans: dict[int, tuple[str, int]] = {}

    for row in rows:
        cells = row.find_all(["td", "th"])
        row_data = []
        cell_idx = 0

        for cell in cells:
            # Skip columns that are filled by an active rowspan
            while cell_idx in active_rowspans:
                text, remaining = active_rowspans[cell_idx]
                row_data.append(text)
                if remaining <= 1:
                    del active_rowspans[cell_idx]
                else:
                    active_rowspans[cell_idx] = (text, remaining - 1)
                cell_idx += 1

            text = _extract_cell_text(cell)
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))

            for col_offset in range(colspan):
                row_data.append(text)
                if rowspan > 1:
                    active_rowspans[cell_idx + col_offset] = (text, rowspan - 1)

            cell_idx += colspan

        # Fill any remaining rowspan columns at the end
        while cell_idx in active_rowspans:
            text, remaining = active_rowspans[cell_idx]
            row_data.append(text)
            if remaining <= 1:
                del active_rowspans[cell_idx]
            else:
                active_rowspans[cell_idx] = (text, remaining - 1)
            cell_idx += 1

        parsed.append(row_data)

    return parsed


# ============================================================
# INTERNAL LINK EXTRACTION
# ============================================================

def _extract_internal_links(topic_div: Tag, page_url: str) -> list[dict]:
    """
    Find all <a href="..."> links that point to other pages in the
    policy guide (internal cross-references).

    Returns a list of {"text": "...", "href": "resolved_url"} dicts.
    External links (http to other domains) are excluded.
    """
    links = []
    seen_hrefs = set()
    base_domain = "eohhs.ehs.state.ma.us"

    for a_tag in topic_div.find_all("a", href=True):
        href = a_tag["href"]

        # Skip anchors, javascript, and mailto links
        if href.startswith(("#", "javascript:", "mailto:")):
            continue

        # Resolve relative URLs
        if page_url:
            resolved = urljoin(page_url, href)
        else:
            resolved = href

        # Strip any fragment identifier
        resolved = resolved.split("#")[0]

        # Only keep links to the same domain (internal links)
        if base_domain not in resolved:
            continue

        # Deduplicate
        if resolved in seen_hrefs:
            continue
        seen_hrefs.add(resolved)

        link_text = a_tag.get_text(strip=True)
        if link_text:
            links.append({
                "text": link_text,
                "href": resolved,
            })

    return links
