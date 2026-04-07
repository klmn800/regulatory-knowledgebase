"""
Author output versioning — track numbered versions of research, drafts, and formats.

Pure helper functions, no external dependencies beyond stdlib.
Each phase run creates a version directory like:
    output/author/{name}/research/001_20260406-1430/
    output/author/{name}/drafts/001_20260406-1600/
    output/author/{name}/formats/001_20260406-1630/

Top-level files (research_report.md, draft.md, output.docx) always hold the latest
version for phase-to-phase handoff. Version dirs preserve the full history.
"""

import json
import shutil
import time
from pathlib import Path

# Phase name → subdirectory name
PHASE_DIRS = {
    "research": "research",
    "draft": "drafts",
    "format": "formats",
}


def _phase_dir(output_dir: Path, phase: str) -> Path:
    """Return the phase subdirectory (e.g. output/author/name/research/)."""
    return output_dir / PHASE_DIRS[phase]


def _parse_version_num(dirname: str) -> int:
    """Extract the version number from a dir name like '003_20260406-1545'."""
    try:
        return int(dirname.split("_", 1)[0])
    except (ValueError, IndexError):
        return 0


def next_version_dir(output_dir: Path, phase: str) -> Path:
    """Create and return the next numbered version directory for a phase."""
    phase_root = _phase_dir(output_dir, phase)
    phase_root.mkdir(parents=True, exist_ok=True)

    # Find the highest existing version number
    existing = sorted(
        (d for d in phase_root.iterdir() if d.is_dir()),
        key=lambda d: _parse_version_num(d.name),
    )
    if existing:
        next_num = _parse_version_num(existing[-1].name) + 1
    else:
        next_num = 1

    timestamp = time.strftime("%Y%m%d-%H%M")
    version_dir = phase_root / f"{next_num:03d}_{timestamp}"
    version_dir.mkdir(parents=True, exist_ok=True)
    return version_dir


def latest_version(output_dir: Path, phase: str) -> Path | None:
    """Return the latest version directory for a phase, or None."""
    phase_root = _phase_dir(output_dir, phase)
    if not phase_root.exists():
        return None

    dirs = sorted(
        (d for d in phase_root.iterdir() if d.is_dir()),
        key=lambda d: _parse_version_num(d.name),
    )
    return dirs[-1] if dirs else None


def list_versions(output_dir: Path, phase: str) -> list[Path]:
    """Return sorted list of version directories for a phase."""
    phase_root = _phase_dir(output_dir, phase)
    if not phase_root.exists():
        return []

    return sorted(
        (d for d in phase_root.iterdir() if d.is_dir()),
        key=lambda d: _parse_version_num(d.name),
    )


def version_count(output_dir: Path, phase: str) -> int:
    """Return the number of versions for a phase."""
    return len(list_versions(output_dir, phase))


# ============================================================
# SAVE helpers — called after each phase run
# ============================================================

def save_research_version(
    output_dir: Path,
    assignment_text: str,
    result,  # SynthesisResult
) -> Path:
    """Copy top-level research files into a new version directory."""
    version_dir = next_version_dir(output_dir, "research")

    # Save the assignment text used for this run
    (version_dir / "input.txt").write_text(assignment_text, encoding="utf-8")

    # Copy top-level files into version dir with shorter names
    for filename, dest_name in [
        ("research_report.md", "report.md"),
        ("research_evidence.json", "evidence.json"),
    ]:
        src = output_dir / filename
        if src.exists():
            shutil.copy2(src, version_dir / dest_name)

    # Save metadata
    meta = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": round(result.duration_seconds, 1),
        "cost": round(result.cost, 4),
        "searches": len(result.search_queries),
        "model": result.model,
    }
    (version_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    return version_dir


def save_draft_version(
    output_dir: Path,
    assignment_text: str,
    session_id: str,
) -> Path:
    """Create a version directory for a draft run.

    The draft.md itself is copied by the .bat file after Claude exits,
    since the web app doesn't wait for the terminal to finish.
    """
    version_dir = next_version_dir(output_dir, "draft")

    (version_dir / "input.txt").write_text(assignment_text, encoding="utf-8")
    (version_dir / "session_id.txt").write_text(session_id, encoding="utf-8")

    return version_dir


def save_format_version(output_dir: Path) -> Path:
    """Copy the generated .docx into a new version directory."""
    version_dir = next_version_dir(output_dir, "format")

    src = output_dir / "output.docx"
    if src.exists():
        shutil.copy2(src, version_dir / "output.docx")

    return version_dir


# ============================================================
# LOAD helpers — called to render view templates
# ============================================================

def load_version_view(output_dir: Path, phase: str) -> dict | None:
    """Load the latest version's data for template rendering.

    Returns None if no output exists (neither versioned nor unversioned).
    """
    latest = latest_version(output_dir, phase)
    if latest:
        return _load_from_version_dir(latest, phase)

    # Fallback: check for pre-versioning top-level files
    return _load_unversioned_view(output_dir, phase)


def _load_from_version_dir(version_dir: Path, phase: str) -> dict:
    """Load data from a specific version directory."""
    # Parse version number and timestamp from dir name
    dirname = version_dir.name
    parts = dirname.split("_", 1)
    version_num = parts[0] if parts else "?"
    version_ts = parts[1] if len(parts) > 1 else ""

    data = {
        "version_num": version_num,
        "version_ts": version_ts,
        "version_label": f"v{version_num}",
        "version_dir": str(version_dir),
        "is_unversioned": False,
    }

    # Load assignment text used
    input_file = version_dir / "input.txt"
    data["input_text"] = input_file.read_text(encoding="utf-8") if input_file.exists() else None

    if phase == "research":
        report_file = version_dir / "report.md"
        data["report"] = report_file.read_text(encoding="utf-8") if report_file.exists() else None

        meta_file = version_dir / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            data["duration"] = meta.get("duration")
            data["cost"] = meta.get("cost")
            data["searches"] = meta.get("searches")
            data["model"] = meta.get("model")
        else:
            data["duration"] = data["cost"] = data["searches"] = data["model"] = None

    elif phase == "draft":
        draft_file = version_dir / "draft.md"
        data["draft"] = draft_file.read_text(encoding="utf-8") if draft_file.exists() else None

        sid_file = version_dir / "session_id.txt"
        data["session_id"] = sid_file.read_text(encoding="utf-8").strip() if sid_file.exists() else None

    elif phase == "format":
        docx_file = version_dir / "output.docx"
        data["has_docx"] = docx_file.exists()

    return data


def _load_unversioned_view(output_dir: Path, phase: str) -> dict | None:
    """Fallback for pre-versioning assignments that have top-level files only."""
    data = {
        "version_num": "0",
        "version_ts": "",
        "version_label": "unversioned",
        "version_dir": str(output_dir),
        "is_unversioned": True,
        "input_text": None,
    }

    if phase == "research":
        report_file = output_dir / "research_report.md"
        if not report_file.exists():
            return None
        data["report"] = report_file.read_text(encoding="utf-8")
        data["duration"] = data["cost"] = data["searches"] = data["model"] = None

    elif phase == "draft":
        draft_file = output_dir / "draft.md"
        if not draft_file.exists():
            return None
        data["draft"] = draft_file.read_text(encoding="utf-8")

        sid_file = output_dir / "session_id.txt"
        data["session_id"] = sid_file.read_text(encoding="utf-8").strip() if sid_file.exists() else None

    elif phase == "format":
        docx_file = output_dir / "output.docx"
        if not docx_file.exists():
            return None
        data["has_docx"] = True

    return data
