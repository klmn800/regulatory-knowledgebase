"""
Author output versioning — independent per-phase model.

Each phase (research, drafts, formats) versions independently.
A research version records the prompt used. A draft version records
which research version(s) it was based on. A format version records
which draft it formatted.

Directory layout:
    output/author/{name}/
    ├── assignment.txt
    ├── research/
    │   ├── 001_20260408-2130/
    │   │   ├── prompt.md
    │   │   ├── report.md
    │   │   ├── evidence.json
    │   │   └── meta.json
    │   └── 002_20260409-1015/
    │       └── ...
    ├── drafts/
    │   ├── 001_20260409-1100/
    │   │   ├── prompt.md
    │   │   ├── draft.md
    │   │   ├── session_id.txt
    │   │   ├── full_prompt.md
    │   │   └── meta.json
    │   └── ...
    └── formats/
        ├── 001_20260409-1130/
        │   ├── output.docx
        │   └── meta.json
        └── ...

Pure helper functions, no external dependencies beyond stdlib.
"""

import json
import time
from pathlib import Path


PHASE_DIRS = {
    "research": "research",
    "drafts": "drafts",
    "formats": "formats",
}


def _parse_version_num(dirname: str) -> int:
    """Extract the version number from a dir name like '003_20260406-1545'."""
    try:
        return int(dirname.split("_", 1)[0])
    except (ValueError, IndexError):
        return 0


def _phase_root(output_dir: Path, phase: str) -> Path:
    """Return the phase subdirectory path."""
    return output_dir / PHASE_DIRS[phase]


# ============================================================
# VERSION DIRECTORY PRIMITIVES
# ============================================================

def list_versions(output_dir: Path, phase: str) -> list[Path]:
    """Return sorted list of version directories for a phase."""
    root = _phase_root(output_dir, phase)
    if not root.exists():
        return []
    return sorted(
        (d for d in root.iterdir() if d.is_dir()),
        key=lambda d: _parse_version_num(d.name),
    )


def get_version_dir(output_dir: Path, phase: str, num: int) -> Path | None:
    """Return a specific version directory by number, or None."""
    for d in list_versions(output_dir, phase):
        if _parse_version_num(d.name) == num:
            return d
    return None


def next_version_dir(output_dir: Path, phase: str) -> Path:
    """Create and return the next numbered version directory for a phase."""
    root = _phase_root(output_dir, phase)
    root.mkdir(parents=True, exist_ok=True)

    existing = list_versions(output_dir, phase)
    if existing:
        next_num = _parse_version_num(existing[-1].name) + 1
    else:
        next_num = 1

    timestamp = time.strftime("%Y%m%d-%H%M")
    version_dir = root / f"{next_num:03d}_{timestamp}"
    version_dir.mkdir(parents=True, exist_ok=True)
    return version_dir


def version_count(output_dir: Path, phase: str) -> int:
    """Return the number of versions for a phase."""
    return len(list_versions(output_dir, phase))


def latest_version_dir(output_dir: Path, phase: str) -> Path | None:
    """Return the latest version directory for a phase, or None."""
    versions = list_versions(output_dir, phase)
    return versions[-1] if versions else None


# ============================================================
# LOAD helpers — read version data for UI display
# ============================================================

def load_version(output_dir: Path, phase: str, num: int | None = None) -> dict | None:
    """Load a version's data for template rendering, with navigation metadata.

    Returns dict with view data plus navigation keys:
        version_num, version_ts, total, index (1-based), has_prev, has_next,
        prev_num, next_num.
    Returns None if no versions exist.
    """
    versions = list_versions(output_dir, phase)
    total = len(versions)

    if total == 0:
        return None

    if num is not None:
        target_idx = None
        for i, d in enumerate(versions):
            if _parse_version_num(d.name) == num:
                target_idx = i
                break
        if target_idx is None:
            target_idx = total - 1
    else:
        target_idx = total - 1

    version_dir = versions[target_idx]
    data = _load_version_data(version_dir, phase)

    data["total"] = total
    data["index"] = target_idx + 1
    data["has_prev"] = target_idx > 0
    data["has_next"] = target_idx < total - 1

    if data["has_prev"]:
        data["prev_num"] = _parse_version_num(versions[target_idx - 1].name)
    if data["has_next"]:
        data["next_num"] = _parse_version_num(versions[target_idx + 1].name)

    return data


def load_version_list(output_dir: Path, phase: str) -> list[dict]:
    """Load summary data for all versions of a phase (for list display)."""
    versions = list_versions(output_dir, phase)
    result = []
    for d in versions:
        num = _parse_version_num(d.name)
        parts = d.name.split("_", 1)
        ts = parts[1] if len(parts) > 1 else ""

        entry = {
            "num": num,
            "ts": ts,
            "dir": str(d),
        }

        meta_file = d / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            entry["meta"] = meta
        else:
            entry["meta"] = {}

        if phase == "research":
            prompt_file = d / "prompt.md"
            if prompt_file.exists():
                text = prompt_file.read_text(encoding="utf-8")
                entry["prompt_preview"] = text[:150].replace("\n", " ")
            entry["has_report"] = (d / "report.md").exists()

        elif phase == "drafts":
            entry["has_draft"] = (d / "draft.md").exists()
            entry["has_session"] = (d / "session_id.txt").exists()
            entry["based_on"] = entry["meta"].get("based_on", [])

        elif phase == "formats":
            entry["has_docx"] = (d / "output.docx").exists()
            entry["based_on"] = entry["meta"].get("based_on", "")

        result.append(entry)

    return result


def _load_version_data(version_dir: Path, phase: str) -> dict:
    """Load phase-specific data from a version directory."""
    dirname = version_dir.name
    parts = dirname.split("_", 1)
    num = _parse_version_num(dirname)
    ts = parts[1] if len(parts) > 1 else ""

    data = {
        "version_num": num,
        "version_ts": ts,
        "version_dir": str(version_dir),
    }

    meta_file = version_dir / "meta.json"
    if meta_file.exists():
        data["meta"] = json.loads(meta_file.read_text(encoding="utf-8"))
    else:
        data["meta"] = {}

    if phase == "research":
        report_file = version_dir / "report.md"
        data["report"] = report_file.read_text(encoding="utf-8") if report_file.exists() else None

        prompt_file = version_dir / "prompt.md"
        data["prompt"] = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else None

        evidence_file = version_dir / "evidence.json"
        data["has_evidence"] = evidence_file.exists()

        data["duration"] = data["meta"].get("duration")
        data["cost"] = data["meta"].get("cost")
        data["searches"] = data["meta"].get("searches")
        data["model"] = data["meta"].get("model")

    elif phase == "drafts":
        draft_file = version_dir / "draft.md"
        data["draft"] = draft_file.read_text(encoding="utf-8") if draft_file.exists() else None

        prompt_file = version_dir / "prompt.md"
        data["prompt"] = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else None

        full_prompt_file = version_dir / "full_prompt.md"
        data["has_full_prompt"] = full_prompt_file.exists()

        sid_file = version_dir / "session_id.txt"
        data["session_id"] = sid_file.read_text(encoding="utf-8").strip() if sid_file.exists() else None

        data["based_on"] = data["meta"].get("based_on", [])

    elif phase == "formats":
        docx_file = version_dir / "output.docx"
        data["has_docx"] = docx_file.exists()
        data["based_on"] = data["meta"].get("based_on", "")

    return data
