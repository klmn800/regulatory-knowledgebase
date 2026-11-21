"""
Index build record: when each pipeline stage last ran, per source.

Each source has one small JSON record at ``index/{source}/build_record.json``.
Pipeline stages write their own entry when they finish, and the query CLI
reads the record to tell callers how old the index is.

Why a record instead of file timestamps: ``index/`` is copied between
machines by flash drive, and copying changes file times. The record travels
inside ``index/`` with the data it describes.

Two kinds of date, deliberately kept apart:

- **Build dates** (this record): when *we* fetched or built each stage.
- **Agency dates** (chunk metadata, e.g. OLG ``last_updated``): when the
  agency last changed a page. Those live on each result, not here.

Record shape (``schema_version`` 1)::

    {
      "schema_version": 1,
      "source": "olg",
      "stages": {
        "scrape": {"date": "2026-04-30", "completed_at": "2026-04-30T17:04:33-04:00",
                   "counts": {...}, "details": {...}, "note": "..."},
        "chunk":  {...},
        "embed":  {..., "details": {"collections": {"pages": {...}, "sections": {...}}}},
        "sparse": {...}
      }
    }

Stage names per source: OLG has ``scrape`` (its HTML parse happens inside the
scraper); FNS, CMR and CFR have ``parse``. All have ``chunk``, ``embed`` and
``sparse``.

Writes never fail a pipeline run: any error is printed as a warning and the
writer returns False.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX_ROOT = PROJECT_ROOT / "index"
RECORD_FILENAME = "build_record.json"
SCHEMA_VERSION = 1
UNKNOWN = "unknown"

SOURCE_STAGES: dict[str, tuple[str, ...]] = {
    "olg": ("scrape", "chunk", "embed", "sparse"),
    "fns": ("parse", "chunk", "embed", "sparse"),
    "cmr": ("parse", "chunk", "embed", "sparse"),
    "cfr": ("parse", "chunk", "embed", "sparse"),
}

STAGE_LABELS = {
    "scrape": "scraped",
    "parse": "parsed",
    "chunk": "chunked",
    "embed": "embedded",
    "sparse": "sparse index built",
}


# ------------------------------------------------------------
# Paths and low-level I/O
# ------------------------------------------------------------

def record_path(source: str, index_root: Path | None = None) -> Path:
    """Return the path of a source's build record."""
    root = Path(index_root) if index_root is not None else DEFAULT_INDEX_ROOT
    return root / source / RECORD_FILENAME


def _check_stage(source: str, stage: str) -> None:
    """Raise ValueError for an unknown source or a stage the source lacks."""
    if source not in SOURCE_STAGES:
        raise ValueError(f"unknown source {source!r}")
    if stage not in SOURCE_STAGES[source]:
        raise ValueError(
            f"stage {stage!r} is not valid for source {source!r}; "
            f"expected one of {SOURCE_STAGES[source]}"
        )


def _load_raw(path: Path) -> dict:
    """Load a record file. Missing file → empty record. Bad JSON raises."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("build record is not a JSON object")
    return data


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON via a temp file and os.replace, so a crash can't leave
    a half-written record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def _warn(message: str) -> None:
    """Print a build-record warning to stderr (never stdout)."""
    print(f"Warning: build record: {message}", file=sys.stderr)


def _stage_entry(
    when: datetime | None,
    date: str | None,
    counts: dict | None,
    details: dict | None,
    note: str | None,
) -> dict:
    """Build one stage entry. `date` overrides the date part of `when`;
    with `date` and no `when`, completed_at is null (date known, time not)."""
    if when is None and date is None:
        when = datetime.now().astimezone()
    if when is not None and when.tzinfo is None:
        when = when.astimezone()
    entry = {
        "date": date or when.date().isoformat(),
        "completed_at": when.isoformat(timespec="seconds") if when else None,
        "counts": dict(counts or {}),
    }
    if details:
        entry["details"] = dict(details)
    if note:
        entry["note"] = note
    return entry


def _merge_and_write(source: str, stage: str, entry: dict,
                     index_root: Path | None) -> None:
    """Read the record, replace one stage, write it back atomically."""
    path = record_path(source, index_root)
    try:
        data = _load_raw(path)
    except (ValueError, OSError) as e:
        _warn(f"{path} was unreadable ({e}); starting a fresh record")
        data = {}
    data["schema_version"] = SCHEMA_VERSION
    data["source"] = source
    stages = data.get("stages")
    if not isinstance(stages, dict):
        stages = {}
    stages[stage] = entry
    data["stages"] = stages
    _atomic_write(path, data)


# ------------------------------------------------------------
# Writers
# ------------------------------------------------------------

def record_stage(
    source: str,
    stage: str,
    counts: dict | None = None,
    details: dict | None = None,
    note: str | None = None,
    index_root: Path | None = None,
    when: datetime | None = None,
    date: str | None = None,
) -> bool:
    """Record that a pipeline stage finished.

    Args:
        source: "olg", "fns", "cmr" or "cfr".
        stage: One of the source's stages (see SOURCE_STAGES).
        counts: Stage-specific counts, e.g. {"pages": 1195}.
        details: Optional extra facts, e.g. {"chunk_file": "..."}.
        note: Optional free-text note.
        index_root: Override the index directory (tests).
        when: Completion time; defaults to now.
        date: Override the date (YYYY-MM-DD). Without `when`, the entry's
            completed_at is null. Used for reconstructed records.

    Returns:
        True if written, False on any error (a warning is printed). Never
        raises, so a record problem can't fail a pipeline run.
    """
    try:
        _check_stage(source, stage)
        entry = _stage_entry(when, date, counts, details, note)
        _merge_and_write(source, stage, entry, index_root)
        return True
    except Exception as e:  # noqa: BLE001 — must never break the pipeline
        _warn(f"could not record {source}/{stage}: {e}")
        return False


def record_embed_collection(
    source: str,
    tier: str,
    collection: str,
    model: str,
    count: int,
    index_root: Path | None = None,
    when: datetime | None = None,
    date: str | None = None,
    note: str | None = None,
) -> bool:
    """Record that one collection (broad or section tier) was embedded.

    The embed stage keeps one sub-entry per collection under
    ``details.collections``, because ``embedder.py --only`` can re-embed one
    tier alone. The stage's own date is the **oldest** collection date, so
    the index is never reported as fresher than its stalest tier.

    Returns True if written, False on error (warning printed). Never raises.
    """
    try:
        _check_stage(source, "embed")
        path = record_path(source, index_root)
        try:
            existing = _load_raw(path).get("stages", {}).get("embed", {})
        except (ValueError, OSError):
            existing = {}
        collections = dict(
            (existing.get("details") or {}).get("collections") or {}
        )
        coll_entry = _stage_entry(when, date, None, None, None)
        collections[tier] = {
            "collection": collection,
            "model": model,
            "count": count,
            "date": coll_entry["date"],
            "completed_at": coll_entry["completed_at"],
        }
        oldest = min(collections.values(), key=lambda c: c["date"])
        entry = {
            "date": oldest["date"],
            "completed_at": oldest["completed_at"],
            "counts": {t: c["count"] for t, c in collections.items()},
            "details": {"collections": collections},
        }
        if note:
            entry["note"] = note
        _merge_and_write(source, "embed", entry, index_root)
        return True
    except Exception as e:  # noqa: BLE001
        _warn(f"could not record {source}/embed ({tier}): {e}")
        return False


def record_scrape_from_progress(
    progress: dict,
    index_root: Path | None = None,
    when: datetime | None = None,
) -> bool:
    """Record the OLG ``scrape`` stage from the scraper's progress map.

    The stage date is the **oldest** fetch time among successfully scraped
    pages, not the time this run finished: a ``--batch`` or ``--program``
    run refreshes only some pages, and the index is only as fresh as its
    stalest page. ``completed_at`` is when this run finished.

    Args:
        progress: url → {"status": "success"|"404"|"failed",
                         "scraped_at": ISO-8601 (success only), ...}

    Returns True if written, False otherwise (warning printed). Never raises.
    """
    try:
        statuses = [v.get("status") for v in progress.values()]
        fetched = []
        for v in progress.values():
            if v.get("status") == "success" and v.get("scraped_at"):
                fetched.append(datetime.fromisoformat(v["scraped_at"]).astimezone())
        if not fetched:
            _warn("no successfully scraped pages; scrape stage not recorded")
            return False
        oldest, newest = min(fetched), max(fetched)
        return record_stage(
            "olg", "scrape",
            counts={
                "pages_scraped": statuses.count("success"),
                "not_found_404": statuses.count("404"),
                "failed": statuses.count("failed"),
            },
            details={
                "oldest_page_fetched_at": oldest.isoformat(timespec="seconds"),
                "newest_page_fetched_at": newest.isoformat(timespec="seconds"),
            },
            index_root=index_root,
            when=when or datetime.now().astimezone(),
            date=oldest.date().isoformat(),
        )
    except Exception as e:  # noqa: BLE001
        _warn(f"could not record olg/scrape: {e}")
        return False


# ------------------------------------------------------------
# Readers
# ------------------------------------------------------------

def _unknown_stage() -> dict:
    """Stage entry used when nothing is recorded."""
    return {"date": UNKNOWN, "completed_at": None, "counts": {}}


def read_index_info(source: str, index_root: Path | None = None) -> dict:
    """Return the ``index`` block for CLI responses. Never raises.

    Shape::

        {"source": "olg",
         "record_status": "present" | "missing" | "unreadable",
         "stages": {"scrape": {"date": "2026-04-30" | "unknown",
                               "completed_at": str | None,
                               "counts": {...},
                               "details": {...}?, "note": str?}, ...}}

    Every stage the source has is always present; unrecorded stages carry
    ``date: "unknown"``.
    """
    stage_names = SOURCE_STAGES.get(source, ())
    status = "present"
    recorded: dict = {}
    try:
        path = record_path(source, index_root)
        if not path.exists():
            status = "missing"
        else:
            raw = _load_raw(path)
            stages = raw.get("stages")
            recorded = stages if isinstance(stages, dict) else {}
    except Exception:  # noqa: BLE001 — reading must never fail a query
        status = "unreadable"
        recorded = {}

    stages_out = {}
    for name in stage_names:
        entry = recorded.get(name)
        if isinstance(entry, dict) and entry.get("date"):
            out = {
                "date": entry["date"],
                "completed_at": entry.get("completed_at"),
                "counts": entry.get("counts") or {},
            }
            if entry.get("details"):
                out["details"] = entry["details"]
            if entry.get("note"):
                out["note"] = entry["note"]
            stages_out[name] = out
        else:
            stages_out[name] = _unknown_stage()
    return {"source": source, "record_status": status, "stages": stages_out}


def format_index_info_text(info: dict) -> str:
    """One-line human summary, e.g.
    ``Index build (olg): scraped 2026-04-30 | chunked 2026-05-01 | ...``"""
    parts = [
        f"{STAGE_LABELS.get(name, name)} {entry.get('date', UNKNOWN)}"
        for name, entry in info.get("stages", {}).items()
    ]
    line = f"Index build ({info.get('source', '?')}): " + " | ".join(parts)
    if info.get("record_status") != "present":
        line += f"  [build record {info.get('record_status')}]"
    return line
