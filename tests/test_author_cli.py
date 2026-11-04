"""Tests for author.py's --reference / --list-references handling.

Only paths that stop before any phase runs are exercised: no API calls, no terminal."""

import sys

import pytest

import apps.author.author as author_mod


@pytest.fixture
def run_cli(tmp_path, monkeypatch):
    monkeypatch.setattr(author_mod, "DATA_DIR", tmp_path / "author")

    def _run(*argv):
        monkeypatch.setattr(sys, "argv", ["author.py", *argv])
        author_mod.main()
    return _run


def test_add_then_list(run_cli, tmp_path, capsys, make_docx):
    docx = tmp_path / "Overview Draft.docx"
    docx.write_bytes(make_docx(tracked=True))
    md = tmp_path / "notes.md"
    md.write_text("# Notes", encoding="utf-8")

    run_cli("--name", "cli_test", "--reference", str(docx), "-r", str(md), "--list-references")
    out = capsys.readouterr().out
    assert "Added reference: Overview Draft.docx" in out
    assert "Added reference: notes.md" in out
    assert "Reference documents (2):" in out
    assert "tracked changes accepted" in out
    assert "(no description)" in out
    assert (tmp_path / "author" / "cli_test" / "references" / "overview-draft").is_dir()


def test_replace_reported(run_cli, tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("one", encoding="utf-8")
    run_cli("--name", "cli_test", "--reference", str(f), "--list-references")
    f.write_text("two", encoding="utf-8")
    run_cli("--name", "cli_test", "--reference", str(f), "--list-references")
    assert "Replaced reference: a.txt" in capsys.readouterr().out


def test_list_empty(run_cli, capsys):
    run_cli("--name", "cli_test", "--list-references")
    assert "No reference documents." in capsys.readouterr().out


def test_missing_or_rejected_file_exits_nonzero(run_cli, tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        run_cli("--name", "cli_test", "--reference", str(tmp_path / "nope.docx"), "--list-references")
    assert e.value.code == 1
    assert "file not found" in capsys.readouterr().out

    bad = tmp_path / "deck.pdf"
    bad.write_bytes(b"%PDF")
    with pytest.raises(SystemExit):
        run_cli("--name", "cli_test", "--reference", str(bad))
    assert "Unsupported file type" in capsys.readouterr().out


def test_draft_only_includes_all_references(run_cli, tmp_path, monkeypatch, capsys):
    captured = {}
    monkeypatch.setattr(author_mod, "launch_draft", lambda **kw: captured.update(kw))
    (tmp_path / "author" / "cli_test").mkdir(parents=True)
    (tmp_path / "author" / "cli_test" / "assignment.txt").write_text("Write it.", encoding="utf-8")
    for name in ("one.txt", "two.txt"):
        (tmp_path / name).write_text(name.upper(), encoding="utf-8")

    run_cli("--name", "cli_test", "--draft-only",
            "-r", str(tmp_path / "one.txt"), "-r", str(tmp_path / "two.txt"))
    assert [r.ref_id for r in captured["references"]] == ["one", "two"]
    assert "ONE.TXT" in captured["full_prompt"] and "TWO.TXT" in captured["full_prompt"]
    assert "Reference documents: one.txt, two.txt" in capsys.readouterr().out
