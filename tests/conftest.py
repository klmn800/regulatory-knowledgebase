"""Shared fixtures. Every document here is synthetic and built in code: the repo is
public, so no real or agency material goes in tests/."""

import struct
import sys
import zlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402


def _tiny_png() -> bytes:
    """A valid 1x1 white PNG."""
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff")
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _tracked_run(tag: str, text: str):
    """A <w:ins> or <w:del> element wrapping one run of text."""
    wrapper = OxmlElement(tag)
    wrapper.set(qn("w:id"), "1")
    wrapper.set(qn("w:author"), "Test")
    wrapper.set(qn("w:date"), "2026-01-01T00:00:00Z")
    run = OxmlElement("w:r")
    t = OxmlElement("w:delText" if tag == "w:del" else "w:t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    run.append(t)
    wrapper.append(run)
    return wrapper


@pytest.fixture
def make_docx(tmp_path):
    """Build a synthetic .docx and return its bytes.

    tracked=True adds one paragraph reading "Limit is " + <del>100</del><ins>200</ins>.
    image=True adds one embedded picture.
    """
    def _make(heading="Sample Page", body="Synthetic policy text.", tracked=False, image=False):
        doc = Document()
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
        if tracked:
            p = doc.add_paragraph("Limit is ")
            p._p.append(_tracked_run("w:del", "100"))
            p._p.append(_tracked_run("w:ins", "200"))
        if image:
            img = tmp_path / "pic.png"
            img.write_bytes(_tiny_png())
            doc.add_picture(str(img))
        out = tmp_path / f"build-{heading.replace(' ', '_')}.docx"
        doc.save(str(out))
        return out.read_bytes()
    return _make


@pytest.fixture
def assignment_dir(tmp_path):
    d = tmp_path / "output" / "author" / "test_assignment"
    d.mkdir(parents=True)
    return d
