"""
OLG Document Reader — extracts structured content from .docx files.

Resolves tracked changes (OOXML revision markup) to produce clean text.
Outputs structured blocks or markdown, complementing docx_writer.py.

Usage:
    from tools.docx_reader import read_docx, to_markdown, has_tracked_changes

    blocks = read_docx("input.docx", change_mode="accept")
    markdown = to_markdown(blocks)

    info = has_tracked_changes("input.docx")
    if info:
        print(f"{info['total']} tracked changes found")

CLI:
    python tools/docx_reader.py input.docx --to-markdown --accept-changes
    python tools/docx_reader.py input.docx --to-markdown --reject-changes -o output.md
    python tools/docx_reader.py input.docx --extract-images images/
    python tools/docx_reader.py input.docx --info
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# CONSTANTS
# ============================================================

CALLOUT_LABELS = {"note", "important", "reminder", "warning", "tip"}

# Max character length for a bold paragraph to be detected as a heading
BOLD_HEADING_MAX_CHARS = 100


# ============================================================
# TRACKED CHANGES — DETECTION
# ============================================================

def has_tracked_changes(path):
    """Check if a .docx file contains tracked changes.

    Returns None if no tracked changes, or a dict with counts:
        {"insertions": int, "deletions": int, "total": int, "format_changes": int}
    """
    doc = Document(str(path))
    body = doc.element.body

    ins_count = len(body.findall(".//" + qn("w:ins")))
    del_count = len(body.findall(".//" + qn("w:del")))
    fmt_count = (
        len(body.findall(".//" + qn("w:rPrChange")))
        + len(body.findall(".//" + qn("w:pPrChange")))
        + len(body.findall(".//" + qn("w:tblPrChange")))
    )

    total = ins_count + del_count + fmt_count
    if total == 0:
        return None

    return {
        "insertions": ins_count,
        "deletions": del_count,
        "format_changes": fmt_count,
        "total": total,
    }


def _prompt_tracked_changes(info):
    """Interactive prompt when tracked changes are detected but no flag given.

    Returns "accept" or "reject", or raises SystemExit.
    """
    print(
        f"\n  Tracked changes detected: "
        f"{info['insertions']} insertions, "
        f"{info['deletions']} deletions, "
        f"{info['format_changes']} format changes"
    )
    print("  [a] Accept all changes (keep insertions, drop deletions)")
    print("  [r] Reject all changes (keep deletions, drop insertions)")
    print("  [q] Quit")

    while True:
        choice = input("  Choice [a/r/q]: ").strip().lower()
        if choice == "a":
            return "accept"
        if choice == "r":
            return "reject"
        if choice == "q":
            raise SystemExit(0)
        print("  Invalid choice. Enter a, r, or q.")


# ============================================================
# TRACKED CHANGES — RESOLUTION
# ============================================================

def _unwrap_element(elem):
    """Replace an element with its children in the parent.

    The element is removed and its children are inserted at its
    position in the parent, preserving document order.
    """
    parent = elem.getparent()
    if parent is None:
        return
    index = list(parent).index(elem)
    for child in list(elem):
        elem.remove(child)
        parent.insert(index, child)
        index += 1
    parent.remove(elem)


def _is_inside_tag(elem, tag):
    """Check if elem has an ancestor with the given tag."""
    parent = elem.getparent()
    while parent is not None:
        if parent.tag == tag:
            return True
        parent = parent.getparent()
    return False


def _resolve_tracked_changes(body, mode):
    """Resolve all tracked changes in the XML tree (in-place mutation).

    Args:
        body: The w:body lxml element.
        mode: "accept" or "reject".
    """
    if mode == "accept":
        _accept_changes(body)
    elif mode == "reject":
        _reject_changes(body)


def _accept_changes(body):
    """Accept all tracked changes: keep insertions, drop deletions."""
    # 1. Remove all w:del elements (deleted content goes away)
    for del_elem in body.findall(".//" + qn("w:del")):
        parent = del_elem.getparent()
        if parent is not None:
            parent.remove(del_elem)

    # 2. Unwrap all w:ins elements (inserted content is promoted)
    for ins_elem in body.findall(".//" + qn("w:ins")):
        _unwrap_element(ins_elem)

    # 3. Clean up format change markers
    for tag in ("w:rPrChange", "w:pPrChange", "w:tblPrChange",
                "w:sectPrChange", "w:tblGridChange", "w:tcPrChange",
                "w:trPrChange"):
        for elem in body.findall(".//" + qn(tag)):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)


def _reject_changes(body):
    """Reject all tracked changes: keep deletions, drop insertions."""
    # 1. Remove all w:ins elements (inserted content goes away)
    for ins_elem in body.findall(".//" + qn("w:ins")):
        parent = ins_elem.getparent()
        if parent is not None:
            parent.remove(ins_elem)

    # 2. Unwrap w:del elements and convert w:delText -> w:t
    for del_elem in body.findall(".//" + qn("w:del")):
        for dt in del_elem.findall(".//" + qn("w:delText")):
            dt.tag = qn("w:t")
        _unwrap_element(del_elem)

    # 3. Clean up format change markers
    for tag in ("w:rPrChange", "w:pPrChange", "w:tblPrChange",
                "w:sectPrChange", "w:tblGridChange", "w:tcPrChange",
                "w:trPrChange"):
        for elem in body.findall(".//" + qn(tag)):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)


# ============================================================
# NUMBERING RESOLVER
# ============================================================

class _NumberingResolver:
    """Resolves numId + ilvl to a list format (bullet or decimal).

    Built from the document's numbering part XML.
    """

    def __init__(self, doc):
        self._format_map = {}  # (numId, ilvl) -> "bullet" | "decimal"
        self._abstract_map = {}  # numId -> abstractNumId
        self._abstract_formats = {}  # (abstractNumId, ilvl) -> numFmt
        self._build(doc)

    def _build(self, doc):
        try:
            numbering_part = doc.part.numbering_part
            numbering_xml = numbering_part._element
        except Exception:
            return

        # Build abstractNum format map
        for abstract in numbering_xml.findall(qn("w:abstractNum")):
            abs_id = abstract.get(qn("w:abstractNumId"))
            for lvl in abstract.findall(qn("w:lvl")):
                ilvl = lvl.get(qn("w:ilvl"))
                num_fmt_elem = lvl.find(qn("w:numFmt"))
                if num_fmt_elem is not None:
                    fmt = num_fmt_elem.get(qn("w:val"), "")
                    self._abstract_formats[(abs_id, ilvl)] = fmt

        # Build num -> abstractNum map
        for num in numbering_xml.findall(qn("w:num")):
            num_id = num.get(qn("w:numId"))
            abs_ref = num.find(qn("w:abstractNumId"))
            if abs_ref is not None:
                self._abstract_map[num_id] = abs_ref.get(qn("w:val"))

    def get_format(self, num_id, ilvl):
        """Get the list format for a numId + ilvl combination.

        Returns "bullet", "numbered", or "numbered" (default).
        """
        abs_id = self._abstract_map.get(num_id)
        if abs_id is None:
            return "numbered"

        fmt = self._abstract_formats.get((abs_id, ilvl), "")
        if fmt == "bullet":
            return "bullet"
        return "numbered"


# ============================================================
# IMAGE EXTRACTION
# ============================================================

class _ImageExtractor:
    """Extracts embedded images from a .docx to a directory."""

    def __init__(self, doc, output_dir=None):
        self._doc = doc
        self._output_dir = Path(output_dir) if output_dir else None
        self._counter = 0

        if self._output_dir:
            self._output_dir.mkdir(parents=True, exist_ok=True)

    def extract_from_element(self, elem):
        """Find and extract images from an element (paragraph or table cell).

        Returns a list of dicts: [{"caption": str, "image_path": str|None}]
        """
        results = []
        blips = elem.findall(".//" + qn("a:blip"))
        for blip in blips:
            r_embed = blip.get(qn("r:embed"))
            if not r_embed:
                continue

            image_path = None
            if self._output_dir:
                image_path = self._save_image(r_embed, elem)

            results.append({"image_path": str(image_path) if image_path else None})

        return results

    def _save_image(self, r_id, context_elem):
        """Save an image referenced by relationship ID."""
        try:
            # Walk up to find the part that owns this relationship
            part = self._find_part_for_element(context_elem)
            if part is None:
                return None

            rel = part.rels.get(r_id)
            if rel is None:
                return None

            image_part = rel.target_part
            content_type = image_part.content_type
            ext = _content_type_to_ext(content_type)

            self._counter += 1
            filename = f"image_{self._counter:03d}{ext}"
            output_path = self._output_dir / filename
            output_path.write_bytes(image_part.blob)
            return output_path
        except Exception:
            return None

    def _find_part_for_element(self, elem):
        """Find the document part that owns the element's relationships."""
        return self._doc.part


def _content_type_to_ext(content_type):
    """Map image content type to file extension."""
    mapping = {
        "image/jpeg": ".jpeg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
        "image/x-emf": ".emf",
        "image/x-wmf": ".wmf",
    }
    return mapping.get(content_type, ".bin")


# ============================================================
# INLINE TEXT EXTRACTION
# ============================================================

def _format_run(run_elem, with_formatting):
    """Extract text from a single w:r element with optional markdown."""
    text = ""
    for child in run_elem:
        if child.tag == qn("w:t"):
            text += child.text or ""
        elif child.tag == qn("w:br"):
            text += "\n"

    if not text:
        return ""

    if not with_formatting:
        return text

    rPr = run_elem.find(qn("w:rPr"))
    is_bold = False
    is_italic = False
    if rPr is not None:
        b = rPr.find(qn("w:b"))
        if b is not None and b.get(qn("w:val"), "true") != "false":
            is_bold = True
        i = rPr.find(qn("w:i"))
        if i is not None and i.get(qn("w:val"), "true") != "false":
            is_italic = True

    if is_bold and is_italic:
        return f"***{text}***"
    if is_bold:
        return f"**{text}**"
    if is_italic:
        return f"*{text}*"
    return text


def _resolve_hyperlink_url(hl_elem, doc_rels):
    """Resolve a w:hyperlink element to a URL string or None."""
    r_id = hl_elem.get(qn("r:id"))
    if r_id and doc_rels:
        rel = doc_rels.get(r_id)
        if rel:
            return rel.target_ref
    return None


def _walk_inline(elem, parts, with_formatting, doc_rels):
    """Recursively walk inline elements, collecting text parts.

    Handles w:r (runs), w:hyperlink (links), w:ins (tracked change
    insertions — recurse into), and w:del (skip).
    """
    for child in elem:
        tag = child.tag

        if tag == qn("w:r"):
            parts.append(_format_run(child, with_formatting))

        elif tag == qn("w:hyperlink"):
            url = _resolve_hyperlink_url(child, doc_rels)
            # Collect display text from runs inside the hyperlink
            link_parts = []
            _walk_inline(child, link_parts, False, doc_rels)
            display = "".join(link_parts).strip()

            if display and url and with_formatting:
                # Escape parentheses in URL to avoid breaking markdown link syntax
                url_safe = url.replace("(", "%28").replace(")", "%29")
                parts.append(f"[{display}]({url_safe})")
            elif display:
                parts.append(display)

        elif tag == qn("w:ins"):
            _walk_inline(child, parts, with_formatting, doc_rels)

        elif tag == qn("w:del"):
            continue


def _extract_paragraph_text(p_elem, with_formatting=True, doc_rels=None):
    """Extract text from a paragraph element with optional inline markdown.

    Walks children in document order handling runs, hyperlinks, and
    tracked change wrappers. Produces [text](url) for external links.

    Args:
        p_elem: The w:p XML element.
        with_formatting: Apply **bold**, *italic*, [link](url) markers.
        doc_rels: The document part's relationship dict (doc.part.rels)
                  for resolving hyperlink URLs. Optional.
    """
    parts = []
    _walk_inline(p_elem, parts, with_formatting, doc_rels)

    result = "".join(parts)

    # Clean up adjacent formatting markers: **text****more** -> **textmore**
    result = re.sub(r"\*\*\*\*", "", result)
    result = re.sub(r"\*\*\s*\*\*", " ", result)

    return result.strip()


def _extract_cell_text(cell_elem, with_formatting=True, doc_rels=None):
    """Extract text from a table cell, joining paragraphs with spaces."""
    parts = []
    for p in cell_elem.findall(qn("w:p")):
        text = _extract_paragraph_text(p, with_formatting, doc_rels)
        if text:
            parts.append(text)
    return " ".join(parts)


# ============================================================
# ELEMENT TYPE DETECTION
# ============================================================

def _get_paragraph_style(p_elem):
    """Get the style name from a paragraph element."""
    pPr = p_elem.find(qn("w:pPr"))
    if pPr is not None:
        pStyle = pPr.find(qn("w:pStyle"))
        if pStyle is not None:
            return pStyle.get(qn("w:val"), "")
    return ""


def _get_num_pr(p_elem):
    """Get numId and ilvl from a paragraph's numbering properties.

    Returns (num_id, ilvl) or (None, None).
    """
    pPr = p_elem.find(qn("w:pPr"))
    if pPr is None:
        return None, None
    numPr = pPr.find(qn("w:numPr"))
    if numPr is None:
        return None, None

    num_id_elem = numPr.find(qn("w:numId"))
    ilvl_elem = numPr.find(qn("w:ilvl"))

    num_id = num_id_elem.get(qn("w:val")) if num_id_elem is not None else None
    ilvl = ilvl_elem.get(qn("w:val"), "0") if ilvl_elem is not None else "0"

    # numId of "0" means no numbering
    if num_id == "0":
        return None, None

    return num_id, ilvl


def _is_all_bold(p_elem):
    """Check if all text-bearing runs in a paragraph are bold."""
    runs = p_elem.findall(".//" + qn("w:r"))
    text_runs = []
    for run in runs:
        # Skip runs inside deleted content
        parent = run.getparent()
        if parent is not None and parent.tag == qn("w:del"):
            continue
        has_text = any((t.text or "").strip() for t in run.findall(qn("w:t")))
        if has_text:
            text_runs.append(run)

    if not text_runs:
        return False

    for run in text_runs:
        rPr = run.find(qn("w:rPr"))
        if rPr is None:
            return False
        b = rPr.find(qn("w:b"))
        if b is None:
            return False
        if b.get(qn("w:val"), "true") == "false":
            return False

    return True


def _read_paragraph_element(p_elem, numbering, is_title_candidate=False,
                            doc_rels=None):
    """Extract a block dict from a paragraph element.

    Returns a block dict or None for empty paragraphs.
    """
    style = _get_paragraph_style(p_elem)
    num_id, ilvl = _get_num_pr(p_elem)

    # Check for heading style
    heading_match = re.match(r"^Heading\s+(\d+)$", style, re.IGNORECASE)

    # Get text
    text = _extract_paragraph_text(p_elem, with_formatting=True,
                                   doc_rels=doc_rels)
    if not text:
        return None

    # 1. Heading style takes priority
    if heading_match:
        level = int(heading_match.group(1))
        # Strip bold markers from heading text since heading style implies bold
        clean_text = text.replace("**", "")
        return {"type": "heading", "level": level, "text": clean_text}

    # 2. Numbered or bulleted list
    if num_id is not None:
        fmt = numbering.get_format(num_id, ilvl)
        level = int(ilvl)
        return {"type": fmt, "text": text, "level": level}

    # 3. Bold-only short paragraph = heading heuristic
    if (_is_all_bold(p_elem)
            and len(text.replace("**", "")) <= BOLD_HEADING_MAX_CHARS
            and style not in ("List Paragraph",)):
        clean_text = text.replace("**", "")
        level = 1 if is_title_candidate else 2
        return {"type": "heading", "level": level, "text": clean_text}

    # 4. Regular paragraph — strip bold wrapping if entire paragraph is bold
    # (this handles edge cases where bold is applied to the whole paragraph
    # but it's too long to be a heading)
    return {"type": "paragraph", "text": text}


# ============================================================
# TABLE CLASSIFICATION & READING
# ============================================================

def _get_table_dimensions(tbl_elem):
    """Get (rows, cols) for a table element."""
    rows = tbl_elem.findall(qn("w:tr"))
    if not rows:
        return 0, 0
    max_cols = 0
    for row in rows:
        cols = len(row.findall(qn("w:tc")))
        if cols > max_cols:
            max_cols = cols
    return len(rows), max_cols


def _table_has_images(tbl_elem):
    """Check if a table contains any embedded images."""
    return len(tbl_elem.findall(".//" + qn("a:blip"))) > 0


def _classify_table(tbl_elem):
    """Classify a table element into a known type.

    Returns: "callout", "image", "toc", "data", or "spacer".
    """
    rows, cols = _get_table_dimensions(tbl_elem)
    if rows == 0:
        return "spacer"

    # Get all cell text to check for empty tables
    all_text = ""
    for tc in tbl_elem.findall(".//" + qn("w:tc")):
        all_text += _extract_cell_text(tc, with_formatting=False)
    all_text = all_text.strip()

    if not all_text and not _table_has_images(tbl_elem):
        return "spacer"

    # Callout: 1 row, 2 cols, first cell is a known label
    if rows == 1 and cols == 2:
        first_row = tbl_elem.findall(qn("w:tr"))[0]
        cells = first_row.findall(qn("w:tc"))
        label_text = _extract_cell_text(cells[0], with_formatting=False).strip()
        if label_text.lower().rstrip(":") in CALLOUT_LABELS:
            return "callout"

    # Image container: has images (typically 2x1 but could vary)
    if _table_has_images(tbl_elem):
        return "image"

    # TOC/Index: 1 row, 1-2 cols, multiline text with short lines
    if rows == 1 and cols <= 2:
        first_row = tbl_elem.findall(qn("w:tr"))[0]
        cells = first_row.findall(qn("w:tc"))
        # Check all cells for multiline content
        for cell in cells:
            paragraphs = cell.findall(qn("w:p"))
            non_empty = [p for p in paragraphs
                         if _extract_paragraph_text(p, False).strip()]
            if len(non_empty) >= 3:
                return "toc"

    # Data table: multiple rows
    if rows >= 2:
        return "data"

    return "spacer"


def _read_table_element(tbl_elem, doc, image_extractor, doc_rels=None):
    """Extract a block dict from a table element.

    Returns a block dict or None for spacers/TOC tables.
    """
    table_type = _classify_table(tbl_elem)

    if table_type in ("spacer", "toc"):
        return None

    if table_type == "callout":
        first_row = tbl_elem.findall(qn("w:tr"))[0]
        cells = first_row.findall(qn("w:tc"))
        label_raw = _extract_cell_text(cells[0], with_formatting=False).strip()
        # Normalize label: "Note" -> "Note:", "important" -> "Important:"
        label = label_raw.rstrip(":").strip().capitalize() + ":"
        body = _extract_cell_text(cells[1], with_formatting=True,
                                  doc_rels=doc_rels)
        return {"type": "note", "label": label, "text": body}

    if table_type == "image":
        rows = tbl_elem.findall(qn("w:tr"))
        # Extract images from the table
        images = image_extractor.extract_from_element(tbl_elem)
        # Get caption from non-image rows/cells
        caption = ""
        for row in rows:
            for cell in row.findall(qn("w:tc")):
                if not cell.findall(".//" + qn("a:blip")):
                    cell_text = _extract_cell_text(cell, with_formatting=False)
                    if cell_text.strip():
                        caption = cell_text.strip()
                        break
            if caption:
                break

        image_path = images[0]["image_path"] if images else None
        return {
            "type": "image_placeholder",
            "caption": caption,
            "image_path": image_path,
        }

    if table_type == "data":
        rows_data = []
        for tr in tbl_elem.findall(qn("w:tr")):
            row_cells = []
            for tc in tr.findall(qn("w:tc")):
                cell_text = _extract_cell_text(tc, with_formatting=True,
                                               doc_rels=doc_rels)
                row_cells.append(cell_text)
            rows_data.append(row_cells)
        return {"type": "table", "rows": rows_data}

    return None


# ============================================================
# INLINE IMAGE DETECTION (in paragraphs)
# ============================================================

def _paragraph_has_image(p_elem):
    """Check if a paragraph contains an inline image."""
    return len(p_elem.findall(".//" + qn("a:blip"))) > 0


# ============================================================
# PUBLIC API
# ============================================================

def read_docx(path, change_mode=None, extract_images_to=None):
    """Read a .docx file into a list of block dicts.

    Args:
        path: Path to the .docx file.
        change_mode: "accept", "reject", or None (no resolution).
        extract_images_to: Directory to save extracted images.

    Returns:
        List of block dicts with "type" key and type-specific fields:
        - heading: {type, level, text}
        - paragraph: {type, text}
        - bullet: {type, text, level}
        - numbered: {type, text, level}
        - table: {type, rows}
        - note: {type, label, text}
        - image_placeholder: {type, caption, image_path}
    """
    path = Path(path)
    doc = Document(str(path))

    if change_mode in ("accept", "reject"):
        _resolve_tracked_changes(doc.element.body, change_mode)

    numbering = _NumberingResolver(doc)
    image_extractor = _ImageExtractor(doc, extract_images_to)
    doc_rels = doc.part.rels

    blocks = []
    body = doc.element.body

    # Track whether we've seen the title yet (for heading level heuristic)
    found_first_text = False
    found_title = False

    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            # Check for inline images first
            if _paragraph_has_image(child):
                images = image_extractor.extract_from_element(child)
                text = _extract_paragraph_text(child, with_formatting=False)
                for img in images:
                    blocks.append({
                        "type": "image_placeholder",
                        "caption": text.strip() if text.strip() else "",
                        "image_path": img["image_path"],
                    })
                # If there's also text beyond the image, add it as a paragraph
                if not images:
                    block = _read_paragraph_element(
                        child, numbering, is_title_candidate=False,
                        doc_rels=doc_rels)
                    if block:
                        blocks.append(block)
                continue

            # Determine if this is a title candidate
            is_title = False
            if found_first_text and not found_title:
                is_title = True

            block = _read_paragraph_element(child, numbering, is_title,
                                            doc_rels=doc_rels)
            if block:
                if not found_first_text:
                    found_first_text = True
                elif is_title and block["type"] == "heading":
                    found_title = True
                blocks.append(block)

        elif tag == "tbl":
            block = _read_table_element(child, doc, image_extractor,
                                        doc_rels=doc_rels)
            if block:
                blocks.append(block)

    return blocks


def to_markdown(blocks, strip_breadcrumb=True, strip_toc=True,
                strip_back_to_index=True):
    """Convert block list to markdown text.

    Args:
        blocks: List of block dicts from read_docx().
        strip_breadcrumb: Remove first paragraph matching breadcrumb pattern.
        strip_toc: Remove "INDEX" headings/paragraphs.
        strip_back_to_index: Remove "(Back to Index)" suffix from headings.

    Returns:
        Markdown string.
    """
    # Pre-process: filter/clean blocks
    processed = list(blocks)

    if strip_breadcrumb and processed:
        # Check first few blocks for breadcrumb pattern
        for i in range(min(3, len(processed))):
            block = processed[i]
            if block["type"] == "paragraph":
                text = block["text"].replace("**", "")
                if re.search(r"Home\s*>|^[^>]+>.*>", text, re.IGNORECASE):
                    processed.pop(i)
                    break

    if strip_toc:
        # Remove "INDEX" paragraphs and headings
        processed = [
            b for b in processed
            if not (b["type"] in ("paragraph", "heading")
                    and b.get("text", "").strip().upper() == "INDEX")
        ]

    lines = []

    for block in processed:
        btype = block["type"]

        if btype == "heading":
            text = block["text"]
            if strip_back_to_index:
                text = re.sub(r"\s*\(Back to Index\)\s*$", "", text,
                              flags=re.IGNORECASE)
            level = block["level"]
            prefix = "#" * level
            lines.append(f"{prefix} {text}")
            lines.append("")

        elif btype == "paragraph":
            lines.append(block["text"])
            lines.append("")

        elif btype == "bullet":
            level = block.get("level", 0)
            indent = "  " * level
            lines.append(f"{indent}- {block['text']}")

        elif btype == "numbered":
            level = block.get("level", 0)
            indent = "   " * level
            lines.append(f"{indent}1. {block['text']}")

        elif btype == "table":
            rows = block["rows"]
            if not rows:
                continue
            # Determine column count
            num_cols = max(len(r) for r in rows)
            # Header row
            header = rows[0]
            while len(header) < num_cols:
                header.append("")
            lines.append("| " + " | ".join(header) + " |")
            # Separator
            lines.append("| " + " | ".join(["---"] * num_cols) + " |")
            # Data rows
            for row in rows[1:]:
                while len(row) < num_cols:
                    row.append("")
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

        elif btype == "note":
            lines.append(f"{block['label']} {block['text']}")
            lines.append("")

        elif btype == "image_placeholder":
            caption = block.get("caption", "")
            image_path = block.get("image_path")
            if image_path:
                lines.append(f"![{caption}]({image_path})")
            else:
                label = caption if caption else "image"
                lines.append(f"[Image: {label}]")
            lines.append("")

    # Join and clean up excessive blank lines
    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"


# ============================================================
# DOCUMENT INFO
# ============================================================

def _print_info(path):
    """Print document information: styles, tracked changes, tables, images."""
    path = Path(path)
    doc = Document(str(path))

    print(f"\n=== {path.name} ===")

    # Styles
    styles = sorted(set(p.style.name for p in doc.paragraphs))
    print(f"  Styles: {', '.join(styles)}")

    # Paragraphs
    print(f"  Paragraphs: {len(doc.paragraphs)}")

    # Tracked changes
    info = has_tracked_changes(path)
    if info:
        print(f"  Tracked changes: {info['insertions']} ins, "
              f"{info['deletions']} del, {info['format_changes']} fmt "
              f"({info['total']} total)")
    else:
        print("  Tracked changes: none")

    # Tables
    table_types = []
    for tbl in doc.element.body.findall(".//" + qn("w:tbl")):
        # Only classify top-level tables (not nested)
        if not _is_inside_tag(tbl, qn("w:tc")):
            table_types.append(_classify_table(tbl))
    if table_types:
        from collections import Counter
        counts = Counter(table_types)
        parts = [f"{v} {k}" for k, v in sorted(counts.items())]
        print(f"  Tables: {sum(counts.values())} ({', '.join(parts)})")
    else:
        print("  Tables: 0")

    # Images
    image_count = sum(
        1 for rel in doc.part.rels.values() if "image" in rel.reltype
    )
    print(f"  Images: {image_count}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Read .docx files and convert to markdown or extract images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python tools/docx_reader.py input.docx --to-markdown --accept-changes
              python tools/docx_reader.py input.docx --to-markdown --reject-changes -o output.md
              python tools/docx_reader.py input.docx --extract-images images/
              python tools/docx_reader.py input.docx --info
              python tools/docx_reader.py *.docx --to-markdown --accept-changes --output-dir converted/
        """),
    )

    parser.add_argument(
        "files", nargs="+", help="One or more .docx files to process",
    )

    # Tracked changes
    change_group = parser.add_mutually_exclusive_group()
    change_group.add_argument(
        "--accept-changes", action="store_true",
        help="Accept tracked changes (keep insertions, drop deletions)",
    )
    change_group.add_argument(
        "--reject-changes", action="store_true",
        help="Reject tracked changes (keep deletions, drop insertions)",
    )

    # Output modes
    parser.add_argument(
        "--to-markdown", action="store_true",
        help="Convert to markdown output",
    )
    parser.add_argument(
        "--extract-images", metavar="DIR",
        help="Extract embedded images to this directory",
    )
    parser.add_argument(
        "--info", action="store_true",
        help="Print document info (styles, tracked changes, tables, images)",
    )

    # Output control
    parser.add_argument(
        "-o", "--output", metavar="FILE",
        help="Output file path (single file mode)",
    )
    parser.add_argument(
        "--output-dir", metavar="DIR",
        help="Output directory for batch mode",
    )

    # OLG stripping
    parser.add_argument(
        "--no-strip", action="store_true",
        help="Disable OLG-specific stripping (breadcrumb, INDEX, Back to Index)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.to_markdown and not args.info and not args.extract_images:
        parser.error("Must specify --to-markdown, --info, or --extract-images")

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Determine change mode
    if args.accept_changes:
        change_mode = "accept"
    elif args.reject_changes:
        change_mode = "reject"
    else:
        change_mode = None

    for filepath in args.files:
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"  Error: {filepath} not found", file=sys.stderr)
            continue

        # Info mode
        if args.info:
            _print_info(filepath)
            continue

        # Determine change mode, prompting if needed
        file_change_mode = change_mode
        if file_change_mode is None and (args.to_markdown or args.extract_images):
            tc_info = has_tracked_changes(filepath)
            if tc_info:
                print(f"\n  {filepath.name}:")
                file_change_mode = _prompt_tracked_changes(tc_info)

        # Read the document
        image_dir = args.extract_images
        if image_dir and len(args.files) > 1:
            # Per-file image subdirectory in batch mode
            image_dir = str(Path(args.extract_images) / filepath.stem)

        blocks = read_docx(
            filepath,
            change_mode=file_change_mode,
            extract_images_to=image_dir,
        )

        # Convert to markdown
        if args.to_markdown:
            strip = not args.no_strip
            md = to_markdown(
                blocks,
                strip_breadcrumb=strip,
                strip_toc=strip,
                strip_back_to_index=strip,
            )

            # Determine output path
            if args.output:
                out_path = Path(args.output)
            elif args.output_dir:
                out_path = Path(args.output_dir) / (filepath.stem + ".md")
            else:
                out_path = None

            if out_path:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(md, encoding="utf-8")
                print(f"  {filepath.name} -> {out_path}")
            else:
                print(md)

        # Extract images only (no markdown)
        elif args.extract_images and not args.to_markdown:
            blocks = read_docx(
                filepath,
                change_mode=file_change_mode,
                extract_images_to=image_dir,
            )
            img_count = sum(
                1 for b in blocks if b["type"] == "image_placeholder"
            )
            print(f"  {filepath.name}: {img_count} images extracted to {image_dir}")


if __name__ == "__main__":
    main()
