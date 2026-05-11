"""
Presentation Renderer — converts slide outline JSON to styled .pptx files.

Uses the DTA-branded PowerPoint template for styling when available.
Falls back to a generic standalone mode if no template is found.

The template defines slide layouts, theme colors (DTA blue #073856,
gold #F6BA16, accent blue #166B9D), and fonts (Franklin Gothic Medium
for headings, Calibri for body).

Slide types:
  - title: Title slide (Section breaker layout)
  - section: Section divider (Section breaker layout)
  - content: Title + bullet list (1_Title and Content layout)
  - table: Title + data table (1_Blank layout + manual table)
  - two_column: Title + two side-by-side bullet lists (1_Comparison layout)
  - citations: References grouped by source, smaller/denser typography (1_Blank layout)

Usage:
    from tools.pptx_writer import generate_pptx
    generate_pptx(outline_dict, output_path)

CLI:
    python tools/pptx_writer.py outline.json -o slides.pptx
    python tools/pptx_writer.py --validate outline.json
"""

import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# TEMPLATE + BRANDING
# ============================================================

DEFAULT_TEMPLATE = PROJECT_ROOT / "tools" / "ppt_template.pptx"

# DTA brand colors
DTA_PRIMARY = RGBColor(0x07, 0x38, 0x56)    # Primary DTA Blue
DTA_GOLD = RGBColor(0xF6, 0xBA, 0x16)       # Gold
DTA_ACCENT = RGBColor(0x16, 0x6B, 0x9D)     # Accent blue
DTA_GREEN = RGBColor(0x00, 0x98, 0x76)       # Green
DTA_ORANGE = RGBColor(0xEC, 0x5A, 0x00)      # Orange
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = RGBColor(0xF3, 0xF4, 0xF6)       # Light gray (alt rows)
BODY_COLOR = RGBColor(0x37, 0x41, 0x51)      # Medium gray (standalone body)
SUBTLE_COLOR = RGBColor(0x6B, 0x72, 0x80)    # Muted gray

# Fonts
HEADING_FONT = "Franklin Gothic Medium"
BODY_FONT = "Calibri"

# Template layout names (from DTA template)
LAYOUT_SECTION_BREAKER = "Section breaker"
LAYOUT_CONTENT = "1_Title and Content"
LAYOUT_TWO_CONTENT = "1_Two Content"
LAYOUT_COMPARISON = "1_Comparison"
LAYOUT_BLANK = "1_Blank"

# Template slide dimensions (standard 4:3)
TEMPLATE_WIDTH = Inches(10)
TEMPLATE_HEIGHT = Inches(7.5)

# Font sizes — matched to template usage
TITLE_SIZE = Pt(44)             # Section breaker title (558800 EMU)
SUBTITLE_SIZE = Pt(18)          # Subtitle/date text
SLIDE_TITLE_SIZE = Pt(40)       # Content slide title (508000 EMU)
BODY_SIZE = Pt(24)              # Content bullets (304800 EMU)
SUB_BULLET_SIZE = Pt(20)        # Indented sub-bullets
TABLE_HEADER_SIZE = Pt(14)      # Table header text
TABLE_BODY_SIZE = Pt(13)        # Table body text
COL_HEADER_SIZE = Pt(20)        # Comparison column headers
CITATION_TITLE_SIZE = Pt(32)    # Citations slide title (smaller than regular content)
CITATION_LABEL_SIZE = Pt(16)    # Source label ("OLG", "106 CMR", etc.)
CITATION_BODY_SIZE = Pt(13)     # Citation entries

# Standalone fallback positions (when no template)
MARGIN_LEFT = Inches(0.5)
MARGIN_TOP = Inches(0.3)
CONTENT_WIDTH = Inches(9.0)
TITLE_HEIGHT = Inches(1.25)
BODY_TOP = Inches(1.75)
BODY_HEIGHT = Inches(4.95)
TABLE_TOP = Inches(1.9)
TABLE_HEIGHT_MAX = Inches(4.8)

VALID_SLIDE_TYPES = {"title", "section", "content", "table", "two_column", "citations"}

# Display labels for citation source groups (keyed by the lowercase JSON key)
CITATION_SOURCE_LABELS = {
    "olg": "OLG",
    "cmr": "106 CMR",
    "fns": "FNS Handbook 310",
    "cfr": "7 CFR",
}
CITATION_SOURCE_ORDER = ("olg", "cmr", "fns", "cfr")


# ============================================================
# VALIDATION
# ============================================================

def validate_outline(outline: dict) -> list[str]:
    """Validate a slide outline dict. Returns list of warnings (empty = valid)."""
    warnings = []

    if not isinstance(outline, dict):
        warnings.append("Outline must be a dict")
        return warnings

    if "slides" not in outline:
        warnings.append("Missing required key: 'slides'")
        return warnings

    slides = outline["slides"]
    if not isinstance(slides, list):
        warnings.append("'slides' must be a list")
        return warnings

    if len(slides) == 0:
        warnings.append("'slides' list is empty")

    for i, slide in enumerate(slides):
        prefix = f"Slide {i + 1}"

        if not isinstance(slide, dict):
            warnings.append(f"{prefix}: must be a dict")
            continue

        slide_type = slide.get("type")
        if slide_type not in VALID_SLIDE_TYPES:
            warnings.append(
                f"{prefix}: invalid type '{slide_type}' "
                f"(must be one of {sorted(VALID_SLIDE_TYPES)})"
            )
            continue

        # citations slides have an optional title (defaults to "References")
        if slide_type != "citations" and "title" not in slide:
            warnings.append(f"{prefix} ({slide_type}): missing 'title'")

        if slide_type == "content":
            bullets = slide.get("bullets")
            if bullets is None:
                warnings.append(f"{prefix}: content slide missing 'bullets'")
            elif not isinstance(bullets, list):
                warnings.append(f"{prefix}: 'bullets' must be a list")
            else:
                for j, b in enumerate(bullets):
                    text = b if isinstance(b, str) else b.get("text", "") if isinstance(b, dict) else ""
                    if len(text) > 120:
                        warnings.append(
                            f"{prefix}, bullet {j + 1}: text exceeds 120 chars ({len(text)})"
                        )

        elif slide_type == "table":
            if "headers" not in slide:
                warnings.append(f"{prefix}: table slide missing 'headers'")
            if "rows" not in slide:
                warnings.append(f"{prefix}: table slide missing 'rows'")
            elif isinstance(slide.get("headers"), list) and isinstance(slide.get("rows"), list):
                ncols = len(slide["headers"])
                for j, row in enumerate(slide["rows"]):
                    if len(row) != ncols:
                        warnings.append(
                            f"{prefix}, row {j + 1}: "
                            f"has {len(row)} cells, expected {ncols}"
                        )

        elif slide_type == "two_column":
            if "left" not in slide:
                warnings.append(f"{prefix}: two_column slide missing 'left'")
            if "right" not in slide:
                warnings.append(f"{prefix}: two_column slide missing 'right'")

        elif slide_type == "citations":
            sources = slide.get("sources")
            if sources is None:
                warnings.append(f"{prefix}: citations slide missing 'sources'")
            elif not isinstance(sources, dict):
                warnings.append(f"{prefix}: 'sources' must be a dict")
            else:
                known = set(CITATION_SOURCE_LABELS)
                for k, v in sources.items():
                    if k not in known:
                        warnings.append(
                            f"{prefix}: unknown citation source '{k}' "
                            f"(must be one of {sorted(known)})"
                        )
                    elif not isinstance(v, list):
                        warnings.append(
                            f"{prefix}: sources['{k}'] must be a list of strings"
                        )
                    else:
                        for j, entry in enumerate(v):
                            if not isinstance(entry, str):
                                warnings.append(
                                    f"{prefix}: sources['{k}'][{j}] "
                                    f"must be a string"
                                )

    return warnings


# ============================================================
# HELPERS
# ============================================================

def _find_layout(prs: Presentation, name: str, fallback_index: int):
    """Find a slide layout by name, falling back to index."""
    for layout in prs.slide_layouts:
        if layout.name == name:
            return layout
    if fallback_index < len(prs.slide_layouts):
        return prs.slide_layouts[fallback_index]
    return prs.slide_layouts[0]


def _find_placeholder(slide, name: str):
    """Find a placeholder on a slide by its name attribute."""
    for ph in slide.placeholders:
        if ph.name == name:
            return ph
    return None


def _delete_placeholders(slide):
    """Remove all placeholder shapes from a slide.

    This is needed for layouts like Section breaker where all placeholders
    share idx=0 (non-standard OOXML), making python-pptx unable to map
    them to correct layout positions. We delete them and add textboxes instead.
    """
    spTree = slide.shapes._spTree
    for ph in list(slide.placeholders):
        sp = ph._element
        spTree.remove(sp)


def _delete_all_slides(prs: Presentation):
    """Remove all existing slides from a presentation."""
    sldIdLst = prs.part._element.find(qn("p:sldIdLst"))
    if sldIdLst is None:
        return
    for sldId in list(sldIdLst):
        rId = sldId.get(qn("r:id"))
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


def _set_font(run, size, color=None, bold=False, italic=False, name=None):
    """Apply font properties to a run."""
    run.font.size = size
    if name:
        run.font.name = name
    if color:
        run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic


def _add_textbox(slide, left, top, width, height):
    """Add a textbox shape and return its text frame."""
    txbox = slide.shapes.add_textbox(left, top, width, height)
    tf = txbox.text_frame
    tf.word_wrap = True
    return tf


def _add_speaker_notes(slide, notes_text: str | None):
    """Add speaker notes to a slide."""
    if not notes_text:
        return
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text


def _populate_placeholder(slide, name: str, text: str):
    """Find a placeholder by name and set its text. Returns the placeholder."""
    ph = _find_placeholder(slide, name)
    if ph and ph.has_text_frame:
        ph.text_frame.clear()
        p = ph.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = text
        return ph
    return None


def _add_bullets_to_frame(tf, bullets: list, body_font=None, body_size=None,
                          sub_font=None, sub_size=None):
    """Populate a text frame with bullet items.

    Each item can be a string (simple bullet) or a dict with
    'text' and optional 'sub' list (sub-bullets).

    When font/size are None, the placeholder's inherited style is used.
    """
    for i, item in enumerate(bullets):
        if isinstance(item, str):
            text = item
            subs = []
        elif isinstance(item, dict):
            text = item.get("text", "")
            subs = item.get("sub", [])
        else:
            text = str(item)
            subs = []

        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.level = 0
        p.space_after = Pt(6)
        run = p.add_run()
        run.text = text
        if body_font or body_size:
            _set_font(run, body_size or BODY_SIZE, name=body_font)

        for sub_text in subs:
            sp = tf.add_paragraph()
            sp.level = 1
            sp.space_after = Pt(4)
            srun = sp.add_run()
            srun.text = sub_text
            if sub_font or sub_size:
                _set_font(srun, sub_size or SUB_BULLET_SIZE, name=sub_font,
                          color=SUBTLE_COLOR)


# ============================================================
# TEMPLATE-AWARE SLIDE RENDERERS
# ============================================================

def _render_title_slide_template(prs: Presentation, slide_data: dict):
    """Render a title slide using the Section breaker layout.

    All Section breaker placeholders share idx=0, so python-pptx can't
    map them to correct positions. We delete them and use textboxes at
    the known layout positions instead.
    """
    layout = _find_layout(prs, LAYOUT_SECTION_BREAKER, 11)
    slide = prs.slides.add_slide(layout)
    _delete_placeholders(slide)

    # Title — bottom-anchored so text sits just above gold line (at y=4.83")
    tf = _add_textbox(slide, Inches(0.8), Inches(1.0), Inches(8.4), Inches(3.7))
    tf.paragraphs[0].space_after = Pt(0)
    tf.word_wrap = True
    from pptx.enum.text import MSO_ANCHOR as _A
    tf.paragraphs[0].alignment = PP_ALIGN.LEFT
    # Bottom-anchor: text sits at bottom of textbox, just above the gold line
    txBody = tf._txBody
    bodyPr = txBody.find(qn("a:bodyPr"))
    bodyPr.set("anchor", "b")
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, TITLE_SIZE, WHITE, name=HEADING_FONT)

    # Subtitle — just below the gold line (line is at y=4.83")
    subtitle = slide_data.get("subtitle", "")
    if subtitle:
        tf2 = _add_textbox(slide, Inches(0.8), Inches(4.95), Inches(8.4), Inches(1.0))
        p2 = tf2.paragraphs[0]
        run2 = p2.add_run()
        run2.text = subtitle
        _set_font(run2, SUBTITLE_SIZE, WHITE, name=BODY_FONT)

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_section_slide_template(prs: Presentation, slide_data: dict):
    """Render a section divider using the Section breaker layout.

    Same idx=0 issue as title slide — delete placeholders, use textboxes.
    """
    layout = _find_layout(prs, LAYOUT_SECTION_BREAKER, 11)
    slide = prs.slides.add_slide(layout)
    _delete_placeholders(slide)

    # Section title — bottom-anchored so text sits just above gold line (at y=4.83")
    tf = _add_textbox(slide, Inches(0.8), Inches(1.0), Inches(8.4), Inches(3.7))
    tf.word_wrap = True
    txBody = tf._txBody
    bodyPr = txBody.find(qn("a:bodyPr"))
    bodyPr.set("anchor", "b")
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, TITLE_SIZE, WHITE, name=HEADING_FONT)

    # Subtitle — just below the gold line
    subtitle = slide_data.get("subtitle", "")
    if subtitle:
        tf2 = _add_textbox(slide, Inches(0.8), Inches(4.95), Inches(8.4), Inches(1.0))
        p2 = tf2.paragraphs[0]
        run2 = p2.add_run()
        run2.text = subtitle
        _set_font(run2, SUBTITLE_SIZE, WHITE, name=BODY_FONT, italic=True)

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_content_slide_template(prs: Presentation, slide_data: dict):
    """Render a content slide using 1_Title and Content layout.

    "Title 1" (title): slide title — Franklin Gothic Medium
    "Text Placeholder 2" (body): bullet list — Calibri
    """
    layout = _find_layout(prs, LAYOUT_CONTENT, 4)
    slide = prs.slides.add_slide(layout)

    # Title — explicitly set font since clear()+add_run() loses inheritance
    ph1 = _find_placeholder(slide, "Title 1")
    if ph1 and ph1.has_text_frame:
        ph1.text_frame.clear()
        ph1.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        p = ph1.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = slide_data.get("title", "")
        _set_font(run, SLIDE_TITLE_SIZE, DTA_PRIMARY, name=HEADING_FONT)

    # Bullets in the body placeholder
    bullets = slide_data.get("bullets", [])
    ph2 = _find_placeholder(slide, "Text Placeholder 2")
    if ph2 and ph2.has_text_frame and bullets:
        ph2.text_frame.clear()
        ph2.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        _add_bullets_to_frame(ph2.text_frame, bullets,
                              body_font=BODY_FONT, body_size=BODY_SIZE,
                              sub_font=BODY_FONT, sub_size=SUB_BULLET_SIZE)
    elif ph2 and ph2.has_text_frame:
        ph2.text_frame.clear()

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_table_slide_template(prs: Presentation, slide_data: dict):
    """Render a table slide using 1_Blank layout + manual table shape.

    Uses Blank to avoid body placeholder interference.
    Title is a manual textbox, table is positioned below it.
    """
    layout = _find_layout(prs, LAYOUT_BLANK, 7)
    slide = prs.slides.add_slide(layout)

    # Manual title textbox
    tf = _add_textbox(slide, MARGIN_LEFT, MARGIN_TOP, CONTENT_WIDTH, TITLE_HEIGHT)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, SLIDE_TITLE_SIZE, DTA_PRIMARY, name=HEADING_FONT)

    headers = slide_data.get("headers", [])
    rows = slide_data.get("rows", [])
    if not headers:
        _add_speaker_notes(slide, slide_data.get("notes"))
        return

    n_rows = len(rows) + 1  # +1 for header
    n_cols = len(headers)

    table_width = CONTENT_WIDTH
    row_height = Inches(0.45)
    table_height = min(row_height * n_rows, TABLE_HEIGHT_MAX)

    table_shape = slide.shapes.add_table(
        n_rows, n_cols, MARGIN_LEFT, TABLE_TOP, table_width, table_height
    )
    table = table_shape.table

    col_width = int(table_width / n_cols)
    for ci in range(n_cols):
        table.columns[ci].width = col_width

    # Header row — DTA primary blue
    for ci, header in enumerate(headers):
        cell = table.cell(0, ci)
        cell.text = header
        p = cell.text_frame.paragraphs[0]
        p.font.size = TABLE_HEADER_SIZE
        p.font.name = BODY_FONT
        p.font.bold = True
        p.font.color.rgb = WHITE
        cell.fill.solid()
        cell.fill.fore_color.rgb = DTA_PRIMARY

    # Data rows
    for ri, row in enumerate(rows):
        for ci, value in enumerate(row):
            cell = table.cell(ri + 1, ci)
            cell.text = str(value)
            p = cell.text_frame.paragraphs[0]
            p.font.size = TABLE_BODY_SIZE
            p.font.name = BODY_FONT
            p.font.color.rgb = BODY_COLOR
            if ri % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT_BG

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_two_column_slide_template(prs: Presentation, slide_data: dict):
    """Render a two-column slide using 1_Comparison layout.

    All Comparison placeholders share idx=0 — same issue as Section breaker.
    Delete placeholders and use textboxes at the known layout positions:
      Title:        (0.50, 0.30)  9.00x1.25
      Left header:  (0.50, 1.83)  4.42x0.54
      Left body:    (0.50, 2.38)  4.42x4.32
      Right header: (5.08, 1.83)  4.42x0.54
      Right body:   (5.08, 2.38)  4.42x4.32
    """
    layout = _find_layout(prs, LAYOUT_COMPARISON, 6)
    slide = prs.slides.add_slide(layout)
    _delete_placeholders(slide)

    # Title
    tf = _add_textbox(slide, Inches(0.50), Inches(0.30), Inches(9.00), Inches(1.25))
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, SLIDE_TITLE_SIZE, DTA_PRIMARY, name=HEADING_FONT)

    # Column headers
    left_title = slide_data.get("left_title", "")
    right_title = slide_data.get("right_title", "")

    body_top = Inches(1.83)
    body_height = Inches(4.86)

    if left_title or right_title:
        if left_title:
            lh = _add_textbox(slide, Inches(0.50), Inches(1.83), Inches(4.42), Inches(0.54))
            run = lh.paragraphs[0].add_run()
            run.text = left_title
            _set_font(run, COL_HEADER_SIZE, DTA_PRIMARY, bold=True, name=HEADING_FONT)

        if right_title:
            rh = _add_textbox(slide, Inches(5.08), Inches(1.83), Inches(4.42), Inches(0.54))
            run = rh.paragraphs[0].add_run()
            run.text = right_title
            _set_font(run, COL_HEADER_SIZE, DTA_PRIMARY, bold=True, name=HEADING_FONT)

        body_top = Inches(2.38)
        body_height = Inches(4.32)

    # Left column bullets
    left_bullets = slide_data.get("left", [])
    if left_bullets:
        ltf = _add_textbox(slide, Inches(0.50), body_top, Inches(4.42), body_height)
        _add_bullets_to_frame(ltf, left_bullets,
                              body_font=BODY_FONT, body_size=BODY_SIZE,
                              sub_font=BODY_FONT, sub_size=SUB_BULLET_SIZE)

    # Right column bullets
    right_bullets = slide_data.get("right", [])
    if right_bullets:
        rtf = _add_textbox(slide, Inches(5.08), body_top, Inches(4.42), body_height)
        _add_bullets_to_frame(rtf, right_bullets,
                              body_font=BODY_FONT, body_size=BODY_SIZE,
                              sub_font=BODY_FONT, sub_size=SUB_BULLET_SIZE)

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_citations_slide(prs: Presentation, slide_data: dict):
    """Render a citations slide using 1_Blank + manual textboxes.

    Same layout/positioning in template and standalone modes — uses a Blank
    canvas with manual textboxes, so it doesn't depend on placeholder mapping.

    Title at top (smaller than a regular content title), then one labeled
    group per source in `sources` (olg/cmr/fns/cfr), with entries listed
    under each label in small, dense type.
    """
    layout = _find_layout(prs, LAYOUT_BLANK, 7)
    slide = prs.slides.add_slide(layout)

    # Title — narrower band than a content slide title (32pt vs 40pt)
    title = slide_data.get("title") or "References"
    title_tf = _add_textbox(slide, MARGIN_LEFT, MARGIN_TOP,
                             CONTENT_WIDTH, Inches(0.8))
    run = title_tf.paragraphs[0].add_run()
    run.text = title
    _set_font(run, CITATION_TITLE_SIZE, DTA_PRIMARY, name=HEADING_FONT)

    # Body block — one labeled group per populated source
    sources = slide_data.get("sources", {}) or {}
    body_tf = _add_textbox(slide, MARGIN_LEFT, Inches(1.25),
                            CONTENT_WIDTH, Inches(5.9))
    body_tf.word_wrap = True

    first = True
    for key in CITATION_SOURCE_ORDER:
        entries = sources.get(key, []) or []
        if not entries:
            continue

        # Source label (bold, DTA blue)
        if first:
            p = body_tf.paragraphs[0]
            first = False
        else:
            p = body_tf.add_paragraph()
            p.space_before = Pt(10)
        p.space_after = Pt(2)
        run = p.add_run()
        run.text = CITATION_SOURCE_LABELS[key]
        _set_font(run, CITATION_LABEL_SIZE, DTA_PRIMARY,
                   bold=True, name=HEADING_FONT)

        # Entries indented under the label
        for entry in entries:
            ep = body_tf.add_paragraph()
            ep.level = 1
            ep.space_after = Pt(1)
            erun = ep.add_run()
            erun.text = entry
            _set_font(erun, CITATION_BODY_SIZE, BODY_COLOR, name=BODY_FONT)

    _add_speaker_notes(slide, slide_data.get("notes"))


# ============================================================
# STANDALONE (NO-TEMPLATE) SLIDE RENDERERS
# ============================================================

def _render_title_slide_standalone(prs: Presentation, slide_data: dict):
    """Render a title slide without a template."""
    layout = _find_layout(prs, "Title Slide", 0)
    slide = prs.slides.add_slide(layout)

    for ph in slide.placeholders:
        if ph.has_text_frame:
            ph.text = ""

    tf = _add_textbox(slide, Inches(0.5), Inches(2.2), Inches(9.0), Inches(1.5))
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = tf.paragraphs[0].add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, Pt(36), DTA_PRIMARY, bold=True, name=HEADING_FONT)

    subtitle = slide_data.get("subtitle", "")
    if subtitle:
        tf2 = _add_textbox(slide, Inches(0.5), Inches(3.9), Inches(9.0), Inches(1.0))
        tf2.paragraphs[0].alignment = PP_ALIGN.CENTER
        run2 = tf2.paragraphs[0].add_run()
        run2.text = subtitle
        _set_font(run2, Pt(20), SUBTLE_COLOR, name=BODY_FONT)

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_section_slide_standalone(prs: Presentation, slide_data: dict):
    """Render a section header without a template."""
    layout = _find_layout(prs, "Section Header", 2)
    slide = prs.slides.add_slide(layout)

    for ph in slide.placeholders:
        if ph.has_text_frame:
            ph.text = ""

    tf = _add_textbox(slide, MARGIN_LEFT, Inches(2.5), CONTENT_WIDTH, Inches(1.5))
    run = tf.paragraphs[0].add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, Pt(32), DTA_PRIMARY, bold=True, name=HEADING_FONT)

    subtitle = slide_data.get("subtitle", "")
    if subtitle:
        p = tf.add_paragraph()
        p.space_before = Pt(8)
        run2 = p.add_run()
        run2.text = subtitle
        _set_font(run2, Pt(18), SUBTLE_COLOR, name=BODY_FONT)

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_content_slide_standalone(prs: Presentation, slide_data: dict):
    """Render a content slide without a template."""
    layout = _find_layout(prs, "Blank", 6)
    slide = prs.slides.add_slide(layout)

    tf = _add_textbox(slide, MARGIN_LEFT, MARGIN_TOP, CONTENT_WIDTH, TITLE_HEIGHT)
    run = tf.paragraphs[0].add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, SLIDE_TITLE_SIZE, DTA_PRIMARY, bold=True, name=HEADING_FONT)

    bullets = slide_data.get("bullets", [])
    if bullets:
        btf = _add_textbox(slide, MARGIN_LEFT, BODY_TOP, CONTENT_WIDTH, BODY_HEIGHT)
        _add_bullets_to_frame(btf, bullets, body_font=BODY_FONT, body_size=BODY_SIZE,
                              sub_font=BODY_FONT, sub_size=SUB_BULLET_SIZE)

    _add_speaker_notes(slide, slide_data.get("notes"))


def _render_table_slide_standalone(prs: Presentation, slide_data: dict):
    """Render a table slide without a template (same as template version)."""
    _render_table_slide_template(prs, slide_data)


def _render_two_column_slide_standalone(prs: Presentation, slide_data: dict):
    """Render a two-column slide without a template."""
    layout = _find_layout(prs, "Blank", 6)
    slide = prs.slides.add_slide(layout)

    tf = _add_textbox(slide, MARGIN_LEFT, MARGIN_TOP, CONTENT_WIDTH, TITLE_HEIGHT)
    run = tf.paragraphs[0].add_run()
    run.text = slide_data.get("title", "")
    _set_font(run, SLIDE_TITLE_SIZE, DTA_PRIMARY, bold=True, name=HEADING_FONT)

    col_width = Inches(4.2)
    col_right_x = Inches(5.3)
    body_top = BODY_TOP

    left_title = slide_data.get("left_title", "")
    right_title = slide_data.get("right_title", "")
    if left_title or right_title:
        if left_title:
            lh = _add_textbox(slide, MARGIN_LEFT, BODY_TOP, col_width, Inches(0.5))
            run = lh.paragraphs[0].add_run()
            run.text = left_title
            _set_font(run, COL_HEADER_SIZE, DTA_PRIMARY, bold=True, name=HEADING_FONT)
        if right_title:
            rh = _add_textbox(slide, col_right_x, BODY_TOP, col_width, Inches(0.5))
            run = rh.paragraphs[0].add_run()
            run.text = right_title
            _set_font(run, COL_HEADER_SIZE, DTA_PRIMARY, bold=True, name=HEADING_FONT)
        body_top = Inches(2.3)

    body_height = Inches(7.5) - body_top - Inches(0.5)

    left_bullets = slide_data.get("left", [])
    if left_bullets:
        ltf = _add_textbox(slide, MARGIN_LEFT, body_top, col_width, body_height)
        _add_bullets_to_frame(ltf, left_bullets, body_font=BODY_FONT,
                              body_size=BODY_SIZE, sub_font=BODY_FONT,
                              sub_size=SUB_BULLET_SIZE)

    right_bullets = slide_data.get("right", [])
    if right_bullets:
        rtf = _add_textbox(slide, col_right_x, body_top, col_width, body_height)
        _add_bullets_to_frame(rtf, right_bullets, body_font=BODY_FONT,
                              body_size=BODY_SIZE, sub_font=BODY_FONT,
                              sub_size=SUB_BULLET_SIZE)

    _add_speaker_notes(slide, slide_data.get("notes"))


# ============================================================
# DISPATCH
# ============================================================

RENDERERS_TEMPLATE = {
    "title": _render_title_slide_template,
    "section": _render_section_slide_template,
    "content": _render_content_slide_template,
    "table": _render_table_slide_template,
    "two_column": _render_two_column_slide_template,
    "citations": _render_citations_slide,
}

RENDERERS_STANDALONE = {
    "title": _render_title_slide_standalone,
    "section": _render_section_slide_standalone,
    "content": _render_content_slide_standalone,
    "table": _render_table_slide_standalone,
    "two_column": _render_two_column_slide_standalone,
    "citations": _render_citations_slide,
}


# ============================================================
# GENERATION
# ============================================================

def load_outline(filepath: Path | str) -> dict:
    """Load a slide outline from a JSON file."""
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_pptx(
    outline: dict,
    output_path: Path | str,
    template_path: Path | str | None = None,
) -> Path:
    """Convert a slide outline dict to a styled .pptx file.

    Args:
        outline: Slide outline dict matching the schema.
        output_path: Where to save the .pptx file.
        template_path: Path to .pptx template. Defaults to the DTA template
                       at tools/ppt_template.pptx. Pass False to disable.

    Returns:
        The output path.
    """
    output_path = Path(output_path)

    # Validate
    warnings = validate_outline(outline)
    errors = [w for w in warnings if "missing" in w.lower() or "invalid" in w.lower() or "must be" in w.lower()]
    if errors:
        raise ValueError(f"Invalid outline:\n" + "\n".join(f"  - {e}" for e in errors))
    if warnings:
        for w in warnings:
            print(f"  Warning: {w}", file=sys.stderr)

    # Resolve template
    using_template = False
    if template_path is False:
        prs = Presentation()
    elif template_path:
        template_path = Path(template_path)
        if template_path.exists():
            prs = Presentation(str(template_path))
            _delete_all_slides(prs)
            using_template = True
        else:
            print(f"  Warning: template not found: {template_path}", file=sys.stderr)
            prs = Presentation()
    elif DEFAULT_TEMPLATE.exists():
        prs = Presentation(str(DEFAULT_TEMPLATE))
        _delete_all_slides(prs)
        using_template = True
    else:
        prs = Presentation()

    renderers = RENDERERS_TEMPLATE if using_template else RENDERERS_STANDALONE

    if not using_template:
        prs.slide_width = TEMPLATE_WIDTH
        prs.slide_height = TEMPLATE_HEIGHT

    # Render each slide
    for slide_data in outline.get("slides", []):
        slide_type = slide_data.get("type", "content")
        renderer = renderers.get(slide_type)
        if renderer:
            renderer(prs, slide_data)
        else:
            print(f"  Warning: unknown slide type '{slide_type}', skipping", file=sys.stderr)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Render a slide outline JSON to a .pptx file."
    )
    parser.add_argument("input", help="Path to slide outline JSON file")
    parser.add_argument(
        "-o", "--output",
        help="Output .pptx path (default: same name as input with .pptx extension)"
    )
    parser.add_argument(
        "--template", help="Path to a .pptx template for branding"
    )
    parser.add_argument(
        "--no-template", action="store_true",
        help="Disable template (use generic styling)"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate the outline only (no rendering)"
    )

    args = parser.parse_args()

    outline = load_outline(args.input)

    if args.validate:
        warnings = validate_outline(outline)
        if warnings:
            print("Validation warnings:")
            for w in warnings:
                print(f"  - {w}")
        else:
            n = len(outline.get("slides", []))
            print(f"Outline is valid ({n} slides)")
        return

    output_path = args.output
    if not output_path:
        output_path = Path(args.input).with_suffix(".pptx")

    template = False if args.no_template else args.template
    result = generate_pptx(outline, output_path, template_path=template)
    n = len(outline.get("slides", []))
    print(f"Generated {n}-slide presentation: {result}")


if __name__ == "__main__":
    main()
