"""Smoke tests for the Author reference-document routes (synthetic files, temp output dir).

No test launches a Claude Code terminal: launch_draft is replaced where a draft runs."""

import pytest
from fastapi.testclient import TestClient

import apps.author.author as author_mod
import ui.app as app_mod

NAME = "route_test"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(author_mod, "DATA_DIR", tmp_path / "author")
    return TestClient(app_mod.app)


def _upload(client, *files):
    return client.post(
        f"/author/{NAME}/references/upload",
        files=[("files", (name, data, "application/octet-stream")) for name, data in files],
    )


def test_upload_list_detail_description_delete(client, make_docx):
    r = _upload(client, ("Overview Draft.docx", make_docx(body="Body text.")),
                ("notes.md", b"# Notes"), ("deck.pdf", b"%PDF"))
    assert r.status_code == 200
    assert "Overview Draft.docx" in r.text and "added" in r.text
    assert "Unsupported file type" in r.text  # the PDF is rejected, the others go through

    r = client.get(f"/author/{NAME}/references")
    assert "Overview Draft.docx" in r.text and "notes.md" in r.text and "deck.pdf" not in r.text

    r = client.get(f"/author/{NAME}/references/overview-draft")
    assert r.status_code == 200
    assert "Body text." in r.text and "Tell the drafting model" in r.text

    r = client.post(f"/author/{NAME}/references/overview-draft/description",
                    data={"description": "The new <overview> page."})
    assert "Description saved." in r.text
    assert "The new &lt;overview&gt; page." in r.text  # escaped in the page

    r = _upload(client, ("overview draft.docx", make_docx(body="Second version.")))
    assert "replaced the earlier upload" in r.text

    r = client.post(f"/author/{NAME}/references/notes/delete")
    assert "notes.md" not in r.text and "overview draft.docx" in r.text


def test_reconvert_tracked_changes(client, make_docx):
    _upload(client, ("tracked.docx", make_docx(tracked=True)))
    r = client.get(f"/author/{NAME}/references/tracked")
    assert "Limit is 200" in r.text and "Re-convert with changes rejected" in r.text

    r = client.post(f"/author/{NAME}/references/tracked/reconvert", data={"change_mode": "reject"})
    assert "Limit is 100" in r.text and "Re-converted with tracked changes rejected" in r.text


def test_unknown_and_malformed_ids(client):
    assert client.get(f"/author/{NAME}/references/nope").status_code == 404
    assert client.post(f"/author/{NAME}/references/..%5Cx/delete").status_code in (404, 405)
    assert client.post(f"/author/{NAME}/references/nope/description",
                       data={"description": "x"}).status_code == 404


def test_picker(client):
    r = client.get(f"/author/{NAME}/reference-picker")
    assert "No reference documents" in r.text
    _upload(client, ("a.txt", b"12345"))
    r = client.get(f"/author/{NAME}/reference-picker")
    assert 'class="reference-cb" value="a"' in r.text and 'data-chars="5"' in r.text
