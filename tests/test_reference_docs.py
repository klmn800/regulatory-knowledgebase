"""Tests for apps/author/reference_docs.py (synthetic fixtures only)."""

import json

import pytest

from apps.author import reference_docs as rd


def test_docx_upload_converts_and_writes_meta(assignment_dir, make_docx):
    res = rd.add_reference(assignment_dir, "Expedited Overview v3.docx",
                           make_docx(body="Expedited benefits text."))
    assert res.ok and res.ref_id == "expedited-overview-v3" and not res.replaced

    folder = assignment_dir / "references" / res.ref_id
    assert (folder / "Expedited Overview v3.docx").exists()
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["file_type"] == "docx"
    assert meta["tracked_changes"] is None
    assert meta["change_mode"] == "accept"
    assert meta["description"] == ""

    ref = rd.load_reference(assignment_dir, res.ref_id)
    assert "Expedited benefits text." in ref.text
    assert meta["char_count"] == len(ref.text)


def test_md_and_txt_stored_as_is(assignment_dir):
    md = rd.add_reference(assignment_dir, "notes.md", "# Heading\n\nBody".encode("utf-8"))
    txt = rd.add_reference(assignment_dir, "plain.txt", "﻿With BOM".encode("utf-8"))
    assert md.ok and txt.ok
    assert rd.load_reference(assignment_dir, "notes").text == "# Heading\n\nBody"
    assert rd.load_reference(assignment_dir, "plain").text == "With BOM"
    assert rd.load_reference(assignment_dir, "notes").meta["tracked_changes"] is None
    assert rd.load_reference(assignment_dir, "notes").meta["change_mode"] is None


def test_cp1252_txt_falls_back(assignment_dir):
    res = rd.add_reference(assignment_dir, "old.txt", b"caf\xe9 \x96 dash")  # raw cp1252 bytes
    assert res.ok
    assert rd.load_reference(assignment_dir, "old").text == "café – dash"


def test_tracked_changes_flagged_and_reconvert(assignment_dir, make_docx):
    res = rd.add_reference(assignment_dir, "tracked.docx", make_docx(tracked=True))
    ref = rd.load_reference(assignment_dir, res.ref_id)
    assert ref.meta["tracked_changes"]["insertions"] == 1
    assert ref.meta["tracked_changes"]["deletions"] == 1
    assert "Limit is 200" in ref.text and "100" not in ref.text

    rejected = rd.reconvert_reference(assignment_dir, res.ref_id, "reject")
    assert "Limit is 100" in rejected.text and "200" not in rejected.text
    assert rejected.meta["change_mode"] == "reject"
    assert rejected.meta["char_count"] == len(rejected.text)


def test_image_extracted_and_link_points_at_final_folder(assignment_dir, make_docx):
    res = rd.add_reference(assignment_dir, "with pic.docx", make_docx(image=True))
    ref = rd.load_reference(assignment_dir, res.ref_id)
    assert ref.meta["image_count"] == 1
    folder = assignment_dir / "references" / res.ref_id
    images = list((folder / "images").iterdir())
    assert len(images) == 1
    assert str(folder) in ref.text
    assert ".staging-" not in ref.text


def test_no_images_folder_when_none(assignment_dir, make_docx):
    res = rd.add_reference(assignment_dir, "plain.docx", make_docx())
    assert not (assignment_dir / "references" / res.ref_id / "images").exists()


def test_replace_keeps_description(assignment_dir, make_docx):
    first = rd.add_reference(assignment_dir, "Page.docx", make_docx(body="Old text."))
    rd.update_description(assignment_dir, first.ref_id, "  The new Expedited page.  ")
    second = rd.add_reference(assignment_dir, "page.docx", make_docx(body="New text."))
    assert second.replaced and second.ref_id == first.ref_id
    ref = rd.load_reference(assignment_dir, second.ref_id)
    assert ref.description == "The new Expedited page."
    assert "New text." in ref.text and "Old text." not in ref.text
    assert ref.filename == "page.docx"
    assert len(rd.list_references(assignment_dir)) == 1


def test_failed_replace_keeps_original(assignment_dir, make_docx):
    rd.add_reference(assignment_dir, "keep.docx", make_docx(body="Good text."))
    bad = rd.add_reference(assignment_dir, "keep.docx", b"not a real docx")
    assert not bad.ok
    assert "Good text." in rd.load_reference(assignment_dir, "keep").text
    leftovers = [p for p in (assignment_dir / "references").iterdir() if p.name.startswith(".")]
    assert leftovers == []


@pytest.mark.parametrize("filename,data,message", [
    ("slides.pdf", b"%PDF", "Unsupported file type"),
    ("noext", b"x", "Unsupported file type"),
    ("empty.txt", b"", "empty"),
    ("blank.md", b"   \n\n ", "No text found"),
    ("---.txt", b"x", "usable name"),
])
def test_rejections(assignment_dir, filename, data, message):
    res = rd.add_reference(assignment_dir, filename, data)
    assert not res.ok and message in res.error
    assert rd.list_references(assignment_dir) == []


def test_oversize_rejected(assignment_dir):
    res = rd.add_reference(assignment_dir, "big.txt", b"x" * 2048, max_mb=0.001)
    assert not res.ok and "larger than" in res.error


def test_path_traversal_and_reserved_names(assignment_dir):
    res = rd.add_reference(assignment_dir, "..\\..\\evil.txt", b"text")
    assert res.ok and res.ref_id == "evil" and res.filename == "evil.txt"
    assert (assignment_dir / "references" / "evil" / "evil.txt").exists()

    con = rd.add_reference(assignment_dir, "CON.txt", b"text")
    assert con.ok and con.ref_id == "con-file"

    for bad_id in ("../x", "..", "a/b", "A", ""):
        with pytest.raises(rd.ReferenceDocError):
            rd.load_reference(assignment_dir, bad_id)


def test_list_order_remove_and_select(assignment_dir):
    for name in ("b.txt", "a.txt", "c.txt"):
        rd.add_reference(assignment_dir, name, name.encode())
    ids = [r.ref_id for r in rd.list_references(assignment_dir)]
    assert sorted(ids) == ["a", "b", "c"]

    rd.remove_reference(assignment_dir, "b")
    assert {r.ref_id for r in rd.list_references(assignment_dir)} == {"a", "c"}
    with pytest.raises(rd.ReferenceDocError):
        rd.remove_reference(assignment_dir, "b")

    picked = rd.select_references(assignment_dir, ["c", "missing", "a"])
    assert [r.ref_id for r in picked] == [r for r in ids if r in ("a", "c")]
    assert all(r.text for r in picked)


def test_reconvert_refuses_non_docx_and_bad_mode(assignment_dir, make_docx):
    rd.add_reference(assignment_dir, "n.md", b"text")
    with pytest.raises(rd.ReferenceDocError, match="Only .docx"):
        rd.reconvert_reference(assignment_dir, "n", "reject")
    rd.add_reference(assignment_dir, "d.docx", make_docx())
    with pytest.raises(rd.ReferenceDocError, match="mode"):
        rd.reconvert_reference(assignment_dir, "d", "maybe")


def test_windows_invalid_characters_stripped(assignment_dir):
    res = rd.add_reference(assignment_dir, 'say "hi"?.txt.', b"text")
    assert res.ok and res.filename == "say hi.txt"
    assert (assignment_dir / "references" / res.ref_id / "say hi.txt").exists()
