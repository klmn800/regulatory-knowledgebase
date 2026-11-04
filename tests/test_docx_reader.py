"""Tests for tools/docx_reader.py heading detection (synthetic documents only)."""

from docx import Document

from tools.docx_reader import read_docx, to_markdown


def _save(doc, tmp_path, name="doc.docx"):
    path = tmp_path / name
    doc.save(str(path))
    return path


def test_heading_styles_detected_by_style_name(tmp_path):
    # Word stores the style ID ("Heading1") in the paragraph, not the name ("Heading 1").
    doc = Document()
    doc.add_heading("Top", level=1)
    doc.add_paragraph("Intro text.")
    doc.add_heading("Middle", level=2)
    doc.add_heading("Lower", level=3)
    doc.add_paragraph("Body text.")
    blocks = read_docx(_save(doc, tmp_path))

    headings = [(b["level"], b["text"]) for b in blocks if b["type"] == "heading"]
    assert headings == [(1, "Top"), (2, "Middle"), (3, "Lower")]

    md = to_markdown(blocks, strip_breadcrumb=False)
    assert "# Top" in md and "## Middle" in md and "### Lower" in md


def test_bold_list_paragraph_is_not_a_heading(tmp_path):
    doc = Document()
    doc.add_paragraph("Normal text first.")
    p = doc.add_paragraph(style="List Paragraph")
    p.add_run("Short bold item").bold = True
    blocks = read_docx(_save(doc, tmp_path))
    assert not any(b["type"] == "heading" for b in blocks)


def test_bold_normal_paragraph_still_a_heading(tmp_path):
    doc = Document()
    doc.add_paragraph("Normal text first.")
    doc.add_paragraph().add_run("Bold Heading").bold = True
    doc.add_paragraph("After.")
    blocks = read_docx(_save(doc, tmp_path))
    assert any(b["type"] == "heading" and b["text"] == "Bold Heading" for b in blocks)
