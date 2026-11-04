"""Reference documents uploaded to an Author assignment.

The author's own, unpublished pages (``.docx``, ``.md``, ``.txt``) are stored per
assignment and converted to Markdown, so the Draft phase can put their text into the
prompt. Used by the web UI (``ui/app.py``) and the CLI (``apps/author/author.py``).

Layout, one folder per upload::

    output/author/<name>/references/<ref_id>/
        <original filename>
        converted.md        text used in prompts
        meta.json           filename, type, counts, tracked changes, description
        images/             images extracted from a .docx (only if it has any)

``ref_id`` is a slug of the filename stem. Uploading a file with the same slug replaces
the earlier upload and keeps its description.
"""

from __future__ import annotations

import json
import re
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_EXTENSIONS = (".docx", ".md", ".txt")
DEFAULT_MAX_MB = 25

REFERENCES_DIRNAME = "references"
CONVERTED_FILE = "converted.md"
META_FILE = "meta.json"
IMAGES_DIRNAME = "images"
STAGING_PREFIX = ".staging-"

_WINDOWS_RESERVED = (
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)
_REF_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ReferenceDocError(ValueError):
    """A user-facing problem with an upload (bad type, too large, no text, ...)."""


@dataclass
class AddResult:
    """Outcome of adding one file. ``error`` is set when the file was rejected."""

    filename: str
    ref_id: str | None = None
    replaced: bool = False
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class Reference:
    """A stored upload, as loaded from disk."""

    ref_id: str
    meta: dict
    text: str = field(repr=False, default="")

    @property
    def filename(self) -> str:
        return self.meta.get("filename", self.ref_id)

    @property
    def description(self) -> str:
        return self.meta.get("description", "") or ""


# ------------------------------------------------------------
# Names and paths
# ------------------------------------------------------------

def safe_filename(filename: str) -> str:
    """Basename only, safe to create on Windows.

    Drops any directory part, characters Windows forbids in names (``<>:"|?*`` and
    control characters), leading dots, and trailing dots/spaces.
    """
    name = re.split(r"[\\/]", filename or "")[-1]
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "", name)
    name = name.strip().lstrip(".").rstrip(". ")
    return name


def _retry_on_lock(op, *args, attempts: int = 10, delay: float = 0.2):
    """Run a filesystem operation, retrying while Windows reports the target in use.

    Antivirus and the search indexer briefly hold files that were just written, which
    makes a folder rename or delete fail with PermissionError for a moment.
    """
    for i in range(attempts):
        try:
            return op(*args)
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(delay)


def make_ref_id(filename: str) -> str:
    """Slug of the filename stem: lowercase, runs of non-alphanumerics become ``-``.

    Raises ReferenceDocError if nothing usable is left.
    """
    stem = Path(safe_filename(filename)).stem
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    if not slug:
        raise ReferenceDocError(f"Can't make a usable name from '{filename}'.")
    if slug in _WINDOWS_RESERVED:
        slug = f"{slug}-file"
    return slug


def references_root(output_dir: Path) -> Path:
    return Path(output_dir) / REFERENCES_DIRNAME


def _ref_dir(output_dir: Path, ref_id: str) -> Path:
    """Folder for ``ref_id``. Rejects anything that isn't a well-formed slug."""
    if not isinstance(ref_id, str) or not _REF_ID_RE.match(ref_id):
        raise ReferenceDocError(f"Unknown reference '{ref_id}'.")
    return references_root(output_dir) / ref_id


# ------------------------------------------------------------
# Conversion
# ------------------------------------------------------------

def _decode_text(data: bytes) -> str:
    """UTF-8 (BOM tolerated), falling back to cp1252, Windows Notepad's old default."""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _convert(folder: Path, original: Path, change_mode: str) -> dict:
    """Convert ``original`` (inside ``folder``) and write ``converted.md``.

    Returns the conversion fields for meta.json. Raises ReferenceDocError on empty text.
    """
    ext = original.suffix.lower()
    images_dir = folder / IMAGES_DIRNAME
    if images_dir.exists():
        _retry_on_lock(shutil.rmtree, images_dir)

    tracked = None
    image_count = 0
    if ext == ".docx":
        from tools.docx_reader import has_tracked_changes, read_docx, to_markdown

        try:
            tracked = has_tracked_changes(original)
            blocks = read_docx(original, change_mode, str(images_dir))
        except Exception as e:  # python-docx raises several types for bad files
            raise ReferenceDocError(f"Couldn't read this .docx file ({e}).") from e
        text = to_markdown(blocks)
        image_count = sum(1 for b in blocks if b["type"] == "image_placeholder")
    else:
        text = _decode_text(original.read_bytes())
        change_mode = None

    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()

    if not text.strip():
        raise ReferenceDocError("No text found in this file.")

    (folder / CONVERTED_FILE).write_text(text, encoding="utf-8")
    return {
        "char_count": len(text),
        "tracked_changes": tracked,
        "change_mode": change_mode,
        "image_count": image_count,
    }


def _write_meta(folder: Path, meta: dict) -> None:
    (folder / META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _read_meta(folder: Path) -> dict:
    return json.loads((folder / META_FILE).read_text(encoding="utf-8"))


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def add_reference(
    output_dir: Path,
    filename: str,
    data: bytes,
    max_mb: float = DEFAULT_MAX_MB,
) -> AddResult:
    """Store and convert one uploaded file. Never raises for user-facing problems.

    The file is converted in a staging folder and only swapped into place once
    conversion succeeds, so a failed upload never replaces a good one.
    """
    name = safe_filename(filename)
    result = AddResult(filename=name or filename)
    try:
        if not name:
            raise ReferenceDocError("The file has no name.")
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ReferenceDocError(
                f"Unsupported file type '{ext or '(none)'}'. "
                f"Upload {', '.join(ALLOWED_EXTENSIONS)} files."
            )
        if len(data) > max_mb * 1024 * 1024:
            raise ReferenceDocError(f"File is larger than {max_mb:g} MB.")
        if not data:
            raise ReferenceDocError("The file is empty.")

        ref_id = make_ref_id(name)
        root = references_root(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        final = _ref_dir(output_dir, ref_id)
        staging = root / f"{STAGING_PREFIX}{ref_id}-{uuid.uuid4().hex[:8]}"
        staging.mkdir()
        try:
            original = staging / name
            original.write_bytes(data)
            conv = _convert(staging, original, "accept")

            # Image links in converted.md point at the staging folder; repoint them.
            if conv["image_count"]:
                md_file = staging / CONVERTED_FILE
                md = md_file.read_text(encoding="utf-8")
                md_file.write_text(md.replace(str(staging), str(final)), encoding="utf-8")

            previous = None
            if final.exists():
                try:
                    previous = _read_meta(final)
                except (OSError, ValueError):
                    previous = {}

            meta = {
                "ref_id": ref_id,
                "filename": name,
                "file_type": ext.lstrip("."),
                "uploaded": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "first_uploaded": (previous or {}).get("first_uploaded")
                                  or time.strftime("%Y-%m-%dT%H:%M:%S"),
                "description": (previous or {}).get("description", ""),
                **conv,
            }
            _write_meta(staging, meta)

            if final.exists():
                _retry_on_lock(shutil.rmtree, final)
            _retry_on_lock(staging.rename, final)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

        result.ref_id = ref_id
        result.replaced = previous is not None
    except ReferenceDocError as e:
        result.error = str(e)
    return result


def list_references(output_dir: Path) -> list[Reference]:
    """All stored uploads (metadata only), oldest first."""
    root = references_root(output_dir)
    if not root.exists():
        return []
    refs = []
    for d in root.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        try:
            meta = _read_meta(d)
        except (OSError, ValueError):
            continue
        refs.append(Reference(ref_id=d.name, meta=meta))
    refs.sort(key=lambda r: (r.meta.get("first_uploaded", ""), r.ref_id))
    return refs


def load_reference(output_dir: Path, ref_id: str) -> Reference:
    """One upload with its converted text. Raises ReferenceDocError if missing."""
    folder = _ref_dir(output_dir, ref_id)
    if not (folder / META_FILE).exists():
        raise ReferenceDocError(f"Unknown reference '{ref_id}'.")
    meta = _read_meta(folder)
    text = (folder / CONVERTED_FILE).read_text(encoding="utf-8")
    return Reference(ref_id=ref_id, meta=meta, text=text)


def update_description(output_dir: Path, ref_id: str, description: str) -> Reference:
    folder = _ref_dir(output_dir, ref_id)
    if not (folder / META_FILE).exists():
        raise ReferenceDocError(f"Unknown reference '{ref_id}'.")
    meta = _read_meta(folder)
    meta["description"] = (description or "").strip()
    _write_meta(folder, meta)
    return Reference(ref_id=ref_id, meta=meta)


def remove_reference(output_dir: Path, ref_id: str) -> None:
    folder = _ref_dir(output_dir, ref_id)
    if not folder.exists():
        raise ReferenceDocError(f"Unknown reference '{ref_id}'.")
    _retry_on_lock(shutil.rmtree, folder)


def reconvert_reference(output_dir: Path, ref_id: str, change_mode: str) -> Reference:
    """Re-run a .docx conversion with tracked changes accepted or rejected."""
    if change_mode not in ("accept", "reject"):
        raise ReferenceDocError(f"Unknown tracked-changes mode '{change_mode}'.")
    folder = _ref_dir(output_dir, ref_id)
    if not (folder / META_FILE).exists():
        raise ReferenceDocError(f"Unknown reference '{ref_id}'.")
    meta = _read_meta(folder)
    if meta.get("file_type") != "docx":
        raise ReferenceDocError("Only .docx files have tracked changes to re-convert.")
    original = folder / meta["filename"]
    meta.update(_convert(folder, original, change_mode))
    _write_meta(folder, meta)
    return load_reference(output_dir, ref_id)


def select_references(output_dir: Path, ref_ids: list[str]) -> list[Reference]:
    """Load the given uploads with text, in upload order. Unknown ids are skipped."""
    wanted = set(ref_ids)
    selected = []
    for ref in list_references(output_dir):
        if ref.ref_id in wanted:
            selected.append(load_reference(output_dir, ref.ref_id))
    return selected
