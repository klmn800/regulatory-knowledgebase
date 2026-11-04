"""Tests for the reference-document section of the Author draft prompt.

launch_draft is never called here: it opens a Claude Code terminal."""

import configparser

from apps.author import author
from apps.author import reference_docs as rd


def _config():
    cfg = configparser.ConfigParser()
    cfg.read_dict({"author": {"style_guide": "does/not/exist.md"}})
    return cfg


def _compose(tmp_path, references=None, research_paths=()):
    return author.compose_draft_prompt(
        instructions="INSTRUCTIONS",
        research_paths=list(research_paths),
        assignment="ASSIGNMENT TEXT",
        config=_config(),
        draft_file=tmp_path / "draft.md",
        references=references,
    )


def test_section_includes_framing_files_descriptions_and_text(tmp_path, assignment_dir, make_docx):
    rd.add_reference(assignment_dir, "Overview Draft.docx", make_docx(body="Full overview body."))
    rd.add_reference(assignment_dir, "notes.md", b"Note & <detail>")
    rd.update_description(assignment_dir, "overview-draft", "Replaces the current page.")
    refs = rd.select_references(assignment_dir, ["overview-draft", "notes"])

    prompt = _compose(tmp_path, refs)

    assert "## Author's Reference Documents" in prompt
    assert "not published OLG content" in prompt
    assert '<reference_document filename="Overview Draft.docx">' in prompt
    assert "Replaces the current page." in prompt
    assert "Full overview body." in prompt
    assert "Note & <detail>" in prompt  # content goes in verbatim
    assert prompt.count("(none given)") == 1  # notes.md has no description


def test_filename_attribute_is_escaped(tmp_path, assignment_dir):
    rd.add_reference(assignment_dir, "a&b.txt", b"text")
    prompt = _compose(tmp_path, rd.select_references(assignment_dir, ["a-b"]))
    assert 'filename="a&amp;b.txt"' in prompt


def test_section_absent_without_references(tmp_path):
    for refs in (None, []):
        prompt = _compose(tmp_path, refs)
        assert "## Author's Reference Documents" not in prompt
        assert "<reference_document" not in prompt


def test_section_order(tmp_path, assignment_dir):
    rd.add_reference(assignment_dir, "a.txt", b"REFTEXT")
    research = tmp_path / "research" / "001_x"
    research.mkdir(parents=True)
    (research / "report.md").write_text("RESEARCHTEXT", encoding="utf-8")

    prompt = _compose(tmp_path, rd.select_references(assignment_dir, ["a"]), [research])
    order = [prompt.index(s) for s in (
        "## Assignment", "## Author's Reference Documents", "REFTEXT",
        "## Research Findings", "RESEARCHTEXT", "## Output Instructions",
    )]
    assert order == sorted(order)
    assert "conflicts between the Author's Reference Documents" in prompt


def test_reference_meta_snapshots_description(assignment_dir):
    rd.add_reference(assignment_dir, "a.txt", b"x")
    rd.update_description(assignment_dir, "a", "first")
    meta = author.reference_meta(rd.select_references(assignment_dir, ["a"]))
    assert meta == [{"ref_id": "a", "filename": "a.txt", "description": "first"}]
