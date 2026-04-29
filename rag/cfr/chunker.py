"""
Chunker for 7 CFR RAG pipeline.

Reads the parsed section JSON files and produces two sets of chunks
for embedding:

  1. Part-level documents (one per CFR part) -- for broad topic matching
  2. Section-level chunks (granular) -- for specific regulatory answers

The section chunker applies smart merge/split logic:
  - Tiny sections (< MIN_CHUNK_SIZE) are merged with their neighbors
  - Large sections (> MAX_CHUNK_SIZE) are split at hierarchy boundaries
  - Tables are rendered as pipe-delimited text and appended
  - Each chunk gets a context prefix
    (7 CFR > Part > Subpart > Section) prepended so the embedding model
    understands the hierarchy

Output:
  part_chunks.json     -- list of part-level documents with metadata
  section_chunks.json  -- list of section-level chunks with metadata

Usage:
    python chunker.py                     # Process all parsed sections
    python chunker.py --stats             # Show statistics only
    python chunker.py --preview 2         # Preview chunks for first 2 parts
"""

import argparse
import json
import re
import statistics
from pathlib import Path


# ============================================================
# CROSS-REFERENCE EXTRACTION (per-chunk)
# ============================================================

def _extract_chunk_cross_refs(text: str) -> list[str]:
    """Extract CFR cross-references from a chunk's text."""
    cfr_refs = re.findall(
        r"§\s*(\d{3}\.\d{1,2}(?:\([A-Za-z0-9]+\))*)", text
    )
    return sorted(set(f"§ {r}" for r in cfr_refs))


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = PROJECT_ROOT / "index" / "cfr"
PARSED_DIR = INDEX_DIR / "parsed_sections"
PART_CHUNKS_FILE = INDEX_DIR / "part_chunks.json"
SECTION_CHUNKS_FILE = INDEX_DIR / "section_chunks.json"
SECTION_CHUNKS_FULLPATH_FILE = INDEX_DIR / "section_chunks_fullpath.json"
SECTION_CHUNKS_CONTEXT_FILE = INDEX_DIR / "section_chunks_context.json"

MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 1500
TARGET_CHUNK_SIZE = 1000

# Sections excluded entirely from section-level indexing
# (kept in part-level docs only)
# 271.8: OMB control number table — administrative reference, no policy content
SECTION_EXCLUDES = {"271.8"}

# Sub-items to strip from section text before chunking.
# 272.1(g): 173 amendment implementation entries — procedural history noise
# (142k chars, 93% of the section)
SUBSECTION_EXCLUDES = {
    "272.1": [r"\n\(g\)\s+"],  # regex patterns marking start of excluded content
}


# ============================================================
# PROGRAM LABELS
# ============================================================
#
# Each chunk gets a `program` label so consumers can filter results to
# their relevant audience. Most parts are uniform; 271 and 272 split at
# the section level (definitions vs federal-state governance,
# operational systems vs administrative requirements).
#
# Labels:
#   SNAP            — worker-relevant policy (default visible)
#   Issuance        — technical benefit delivery (default visible, excludable)
#   Administration  — federal-state governance (default excluded)
#   QC              — quality control / performance reporting (default excluded)
#   Disaster        — emergency provisions (default visible)
#   Summer-EBT      — separate program (Summer EBT)

DEFAULT_PROGRAM_BY_PART = {
    273: "SNAP",
    274: "Issuance",
    275: "QC",
    280: "Disaster",
    292: "Summer-EBT",
}

# Per-section overrides. Keyed by section_number string.
# 271: only 271.2 (definitions) is SNAP-worker-relevant; rest is Administration
# 272: split — admin sections vs operational verification systems
SECTION_PROGRAMS = {
    "271.1": "Administration",
    "271.2": "SNAP",
    "271.3": "Administration",
    "271.4": "Administration",
    "271.5": "Administration",
    "271.6": "Administration",
    "271.7": "Administration",
    "271.8": "Administration",
    "271.9": "Administration",
    "272.1": "Administration",
    "272.2": "Administration",
    "272.3": "Administration",
    "272.4": "Administration",
    "272.5": "Administration",
    "272.6": "Administration",
    "272.7": "Administration",
    "272.8": "SNAP",
    "272.9": "SNAP",
    "272.10": "SNAP",
    "272.11": "SNAP",
    "272.12": "SNAP",
    "272.13": "SNAP",
    "272.14": "SNAP",
    "272.15": "Administration",
    "272.16": "SNAP",
    "272.17": "SNAP",
    "272.18": "SNAP",
}


def get_program(section_number: str, part_num: int) -> str:
    """Return the program label for a CFR section."""
    if section_number in SECTION_PROGRAMS:
        return SECTION_PROGRAMS[section_number]
    return DEFAULT_PROGRAM_BY_PART.get(part_num, "Unknown")


def get_part_program(part_num: int, sections: list[dict]) -> str:
    """
    Return the dominant program label for a part-level document.

    For uniform parts (273, 274, 275, 280, 292) this is the part default.
    For mixed parts (271, 272) it's the most common section-level label.
    """
    if part_num in DEFAULT_PROGRAM_BY_PART:
        return DEFAULT_PROGRAM_BY_PART[part_num]
    counts = {}
    for s in sections:
        prog = get_program(s["section_number"], part_num)
        counts[prog] = counts.get(prog, 0) + 1
    return max(counts, key=counts.get) if counts else "Unknown"


# ============================================================
# HIERARCHY PROFILES
# ============================================================

# CFR legal text hierarchy markers -- inverted from CMR's (A)(1)(a)1.
# Level 1: (a) lowercase letter
# Level 2: (1) number
# Level 3: (i) lowercase roman numeral
# Level 4: (A) uppercase letter
CFR_HIERARCHY = [
    (1, re.compile(r"^\([a-z]\)\s+(.+)")),          # (a) Topic
    (2, re.compile(r"^\(\d{1,2}\)\s+(.+)")),         # (1) Sub-topic
    (3, re.compile(r"^\([ivxlc]+\)\s+(.+)")),        # (i) Detail (roman)
    (4, re.compile(r"^\([A-Z]\)\s+(.+)")),            # (A) Sub-detail
]

# Pattern for definition entries: "{Term} means ..." at line start
# Matches "Access device means", "Active case error rate means", etc.
# Does NOT match lines starting with hierarchy markers like (a), (1), etc.
# Allows parens in terms (e.g. "Electronic Benefit Transfer (EBT) system")
# and leading digits (e.g. "2 CFR part 200 means...")
_DEFINITION_ENTRY = re.compile(
    r"^([A-Z0-9][^\n]{2,120}?)\s+means\b"
)

# Single-char markers that are ambiguous between level 1 (letter) and level 3
# (roman numeral): (i)=1/9th, (v)=5/22nd, (x)=10/24th, (l)=50/12th, (c)=100/3rd
_AMBIGUOUS_ROMAN = re.compile(r"^\([ivxlc]\)\s+")


# Extract just the marker portion from a hierarchy line: (a), (1), (i), (A)
_MARKER_EXTRACT = re.compile(r"^(\([a-zA-Z0-9]+\))")


def _build_full_hierarchy_path(state: dict) -> str:
    """Build full path like (a)(1)(i) from hierarchy state dict."""
    if not state:
        return ""
    return "".join(state[l] for l in sorted(state.keys()))


def _extract_intro(line: str, max_len: int = 150) -> str:
    """Extract the introductory clause from a hierarchy marker line.

    Takes text up to the first sentence-ending punctuation (. ; :) after
    at least 10 characters, or truncates at max_len.
    """
    for i, ch in enumerate(line):
        if ch in '.;:' and i >= 10:
            return line[:i + 1]
    if len(line) > max_len:
        return line[:max_len].rstrip() + "..."
    return line


def classify_line(line: str, hierarchy_profile: list,
                  last_marker_level: int | None = None) -> tuple:
    """
    Return (level, label_text) or (None, None) for a line.

    label_text is just the marker — (a), (1), (i), (A) — not the full line.

    For ambiguous single-char markers like (i) that could be either a
    lowercase letter (level 1) or a roman numeral (level 3), uses context:
    - After a number (level 2) or deeper -> roman (level 3)
    - After a letter (level 1) or at section start -> letter (level 1)
    """
    for level, pattern in hierarchy_profile:
        if pattern.match(line):
            # Extract just the marker as the label
            m = _MARKER_EXTRACT.match(line)
            marker = m.group(1) if m else line

            # Disambiguate single-char roman/letter overlap
            if level == 1 and _AMBIGUOUS_ROMAN.match(line):
                if last_marker_level is not None and last_marker_level >= 2:
                    return 3, marker
            return level, marker
    return None, None


def _inject_definition_markers(classified: list[tuple]) -> list[tuple]:
    """
    For definition sections, detect "{Term} means" entries and mark them
    as level 0 (above all hierarchy markers). This ensures definition
    boundaries are used as break points and the term name carries forward
    as the hierarchy label for continued chunks.
    """
    result = []
    for line, level, label in classified:
        match = _DEFINITION_ENTRY.match(line)
        if match and level is None:
            # This line starts a new definition — mark as level 0
            term = match.group(1).strip()
            result.append((line, 0, term))
        else:
            result.append((line, level, label))
    return result


# Verb patterns that indicate a definition entry.
# Primary: "{Term} means ..."
# Secondary: "{Term} refers to ...", "{Term}, as used in this part:"
# Must start with uppercase letter (lowercase/digit = continuation line).
_DEF_VERBS = [
    re.compile(r"^([A-Z][^\n]{2,120}?)\s+means\b"),
    re.compile(r"^([A-Z][^\n]{2,120}?)\s+refers to\b"),
    re.compile(r"^([A-Z][^\n]{2,120}?),\s+as used in this part"),
]

# Definitions that don't use any verb pattern. Keyed by section_number,
# each value is a list of term prefixes that mark a definition start.
# These are identified manually from the source text.
NON_VERB_DEFINITIONS = {
    "271.2": [
        "Assessment ",
        "Employment and Training (E&T) component ",
        "Employment and Training (E&T) mandatory participant ",
        "Error for active cases ",
        "Firm.",
        "Newly work registered ",
        "Underissuance error rate.",
    ],
    "292.2": [
        "2 CFR part 200 ",
    ],
}

# When the regex captures more than the actual term name (e.g. the full
# qualifying phrase before "means"), map it to the correct short name.
# Keyed by section_number → {captured_prefix: correct_term}.
TERM_NAME_OVERRIDES = {
    "271.2": {
        "Adequate notice": "Adequate notice",
        "Beginning month(s)": "Beginning month(s)",
        "Budget month": "Budget month",
        "Error for active cases": "Error",
        "Exempted for purposes of": "Exempted",
        "Issuance month": "Issuance month",
        "Prospective budgeting": "Prospective budgeting",
        "Retrospective budgeting": "Retrospective budgeting",
        "Review date": "Review date",
    },
    "292.2": {
        "Food instrument": "Food instrument",
    },
}


def _apply_term_override(term: str, section_number: str) -> str:
    """Shorten a regex-captured term to the actual defined term."""
    overrides = TERM_NAME_OVERRIDES.get(section_number, {})
    for prefix, short_name in overrides.items():
        if term.startswith(prefix):
            return short_name
    return term


def _is_definition_start(line: str, section_number: str) -> str | None:
    """
    Check if a line starts a new definition entry.

    Returns the extracted term name if it's a definition start, None otherwise.
    """
    # Check verb patterns
    for pattern in _DEF_VERBS:
        m = pattern.match(line)
        if m:
            return _apply_term_override(m.group(1).strip(), section_number)

    # Check manual non-verb definitions
    prefixes = NON_VERB_DEFINITIONS.get(section_number, [])
    for prefix in prefixes:
        if line.startswith(prefix):
            return _apply_term_override(prefix.rstrip(" ."), section_number)
    return None


def chunk_definitions(section: dict) -> list[dict]:
    """
    Chunk a Definitions section with one chunk per defined term.

    Detection uses verb patterns ("{Term} means", "{Term} refers to", etc.)
    plus a manual list for entries that don't use a standard verb.
    Sub-items (1), (i), (A) etc. belong to the preceding definition.
    If a single definition exceeds MAX_CHUNK_SIZE, it's split at sentence
    boundaries but each sub-chunk keeps the term name as its label.
    """
    text = section["text"]
    sec_num = section["section_number"]
    lines = [l for l in text.split("\n") if l.strip()]

    # Group lines into definition entries
    entries = []  # list of (term_name, [lines])
    current_term = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        term = _is_definition_start(stripped, sec_num)
        if term is not None:
            # This line starts a new definition entry
            if current_lines:
                entries.append((current_term, current_lines))
            current_term = term
            current_lines = [stripped]
        else:
            current_lines.append(stripped)

    if current_lines:
        entries.append((current_term, current_lines))

    # Convert entries to chunks, splitting oversized definitions
    raw_chunks = []
    for term, entry_lines in entries:
        entry_text = "\n".join(entry_lines)
        if len(entry_text) <= MAX_CHUNK_SIZE:
            raw_chunks.append((entry_text, term))
        else:
            # Split oversized definition at sentence boundaries
            parts = _split_long_definition(entry_lines)
            for part in parts:
                raw_chunks.append((part, term))

    # Build output dicts matching split_with_hierarchy interface
    total = len(raw_chunks)
    result = []
    for n, (chunk_text, label) in enumerate(raw_chunks, 1):
        result.append({
            **section,
            "text": chunk_text,
            "section_title": section["section_title"],
            "hierarchy_label": label,
            "chunk_n": n,
            "chunk_total": total,
        })

    return result


def _split_long_definition(lines: list[str]) -> list[str]:
    """
    Split an oversized definition into sub-chunks at sentence or
    hierarchy-marker boundaries.
    """
    chunks = []
    current_lines = []
    current_size = 0

    for line in lines:
        line_size = len(line) + 1
        if current_size + line_size > MAX_CHUNK_SIZE and current_lines:
            emit, carry = _split_at_line_boundary(current_lines)
            chunks.append("\n".join(emit))
            current_lines = carry
            current_size = sum(len(l) + 1 for l in carry)
        current_lines.append(line)
        current_size += line_size

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


def _normalize_line_breaks(text: str, hierarchy_profile: list = None) -> str:
    """
    Clean up PDF line-wrap artifacts in chunk text.

    - Joins mid-sentence line wraps into spaces
    - Preserves line breaks before hierarchy markers for readability
    """
    if hierarchy_profile is None:
        hierarchy_profile = CFR_HIERARCHY

    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    parts = [lines[0]]
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Keep line break before hierarchy markers
        is_marker = any(p.match(stripped) for _, p in hierarchy_profile)
        if is_marker:
            parts.append("\n" + stripped)
        else:
            parts.append(" " + stripped)

    return "".join(parts)


def _truncate_hierarchy_label(label: str, max_len: int = 80) -> str:
    """
    Extract a concise topic label from a hierarchy marker line.

    "(d) Income deductions." -> "(d) Income deductions."
    "(e) Very long description of something..." -> "(e) Very long description..."
    """
    if len(label) <= max_len:
        return label
    # Try to truncate at the first sentence boundary after the marker
    period_pos = label.find(".", 4)  # Skip past (x) marker
    if 0 < period_pos < max_len:
        return label[:period_pos + 1]
    return label[:max_len - 3] + "..."


# ============================================================
# TABLE RENDERING
# ============================================================

def render_table(table: dict) -> str:
    """Convert a structured table dict into pipe-delimited text."""
    lines = []
    headers = table.get("headers")
    rows = table.get("rows", [])

    if not rows and not headers:
        return ""

    all_rows = ([headers] if headers else []) + rows
    if not all_rows:
        return ""

    col_count = max(len(row) for row in all_rows)

    if headers:
        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        lines.append(header_line)
        lines.append(separator)

    for row in rows:
        padded = list(row) + [""] * (col_count - len(row))
        row_line = "| " + " | ".join(str(cell) for cell in padded) + " |"
        lines.append(row_line)

    return "\n".join(lines)


def append_tables(text: str, tables: list[dict]) -> str:
    """Render tables and append them to the section text."""
    if not tables:
        return text

    parts = [text.strip()]
    for table in tables:
        rendered = render_table(table)
        if rendered:
            parts.append(rendered)

    return "\n\n".join(parts)


# ============================================================
# CONTEXT PREFIX
# ============================================================

def build_context_prefix(part: int, part_title: str,
                         section_number: str | None = None,
                         section_title: str | None = None,
                         subpart_letter: str | None = None,
                         subpart_title: str | None = None,
                         hierarchy_path: str | None = None) -> str:
    """
    Build a hierarchical context string prepended to chunk text.

    Examples:
      "7 CFR 273 > Certification of Eligible Households"
      "7 CFR 273 > Subpart D: Eligibility and Benefit Levels > § 273.9 Income and deductions"
      "7 CFR 273 > Subpart D: Eligibility and Benefit Levels > § 273.9 Income and deductions > (d) Income deductions"
    """
    title_short = part_title
    if len(title_short) > 60:
        title_short = title_short[:57] + "..."

    parts = [f"7 CFR {part}", title_short]

    if subpart_letter and subpart_title:
        sub_title = subpart_title
        if len(sub_title) > 50:
            sub_title = sub_title[:47] + "..."
        parts.append(f"Subpart {subpart_letter}: {sub_title}")

    if section_number and section_title:
        parts.append(f"\u00a7 {section_number} {section_title}")
    elif section_number:
        parts.append(f"\u00a7 {section_number}")

    if hierarchy_path:
        parts.append(hierarchy_path)

    return " > ".join(parts)


# ============================================================
# CHUNK ID GENERATION
# ============================================================

def make_part_id(part_num: int) -> str:
    """Example: "cfr_pt273" """
    return f"cfr_pt{part_num}"


def make_section_id(section_number: str, chunk_index: int) -> str:
    """Example: "cfr_sec_273_9__000" """
    safe = section_number.replace(".", "_")
    return f"cfr_sec_{safe}__{chunk_index:03d}"


# ============================================================
# SMART MERGE LOGIC
# ============================================================

def merge_small_sections(sections: list[dict]) -> list[dict]:
    """
    Merge tiny sections (< MIN_CHUNK_SIZE) with their neighbors.
    Single-pass forward merge within a part.
    """
    if len(sections) <= 1:
        return sections

    result = []
    i = 0

    while i < len(sections):
        section = sections[i]
        text = section["text"]

        if len(text) >= MIN_CHUNK_SIZE:
            result.append(section)
            i += 1
            continue

        if i + 1 < len(sections):
            next_section = sections[i + 1]
            merged_text = _combine_text(
                section.get("section_title"), text,
                next_section.get("section_title"), next_section["text"]
            )
            merged = {
                **next_section,
                "section_title": section["section_title"] or next_section["section_title"],
                "section_number": section["section_number"],
                "text": merged_text,
            }
            sections[i + 1] = merged
            i += 1
            continue

        if result:
            prev = result[-1]
            merged_text = _combine_text(
                prev.get("section_title"), prev["text"],
                section.get("section_title"), text
            )
            result[-1] = {**prev, "text": merged_text}
            i += 1
            continue

        result.append(section)
        i += 1

    return result


def _combine_text(title_a: str | None, text_a: str,
                  title_b: str | None, text_b: str) -> str:
    """Combine two section texts, preserving the second's title as context."""
    parts = []
    if text_a.strip():
        parts.append(text_a.strip())
    if title_b:
        parts.append(f"{title_b}")
    if text_b.strip():
        parts.append(text_b.strip())
    return "\n\n".join(parts)


# ============================================================
# SMART SPLIT LOGIC
# ============================================================

def split_with_hierarchy(section: dict,
                         hierarchy_profile: list = None,
                         is_definitions: bool = False) -> list[dict]:
    """
    Split a section using hierarchy-aware boundaries.

    Prefers to break at top-level hierarchy markers (e.g., (a), (b))
    when the accumulator has reached MIN_CHUNK_SIZE. Falls back to
    size-only splitting for sections with no hierarchy markers.

    For definition sections, "{Term} means" entries are treated as
    level-0 markers so they serve as break points and carry the term
    name forward as context.

    Each output chunk carries:
      hierarchy_label  -- top-level marker text or definition term or None
      chunk_n          -- 1-indexed position within the section
      chunk_total      -- total chunks for this section
    """
    if hierarchy_profile is None:
        hierarchy_profile = CFR_HIERARCHY

    text = section["text"]

    if len(text) <= MAX_CHUNK_SIZE:
        return [{
            **section,
            "hierarchy_label": None,
            "chunk_n": 1,
            "chunk_total": 1,
        }]

    lines = [l for l in text.split("\n") if l.strip()]

    # Classify each line with context-aware disambiguation
    classified = []
    last_marker_level = None
    for line in lines:
        level, label = classify_line(line, hierarchy_profile, last_marker_level)
        classified.append((line, level, label))
        if level is not None:
            last_marker_level = level

    # For definition sections, inject term markers as level 0
    if is_definitions:
        classified = _inject_definition_markers(classified)

    # Pre-scan: find the top (lowest number) hierarchy level present
    levels_present = [level for _, level, _ in classified if level is not None]
    if not levels_present:
        return _split_by_size_only(section, lines)

    top_level = min(levels_present)

    # Accumulate with hierarchy-aware breaks
    current_lines = []
    current_size = 0
    current_label = None
    current_full_path = ""
    current_intros = {}  # intros snapshot at the START of current chunk
    hierarchy_state = {}
    hierarchy_intros = {}  # live tracking of intro text per level
    raw_chunks = []

    for line, level, label in classified:
        line_size = len(line) + 1  # +1 for \n join

        # Update hierarchy tracking
        if level is not None:
            hierarchy_state[level] = label
            hierarchy_intros[level] = _extract_intro(line)
            for l in range(level + 1, 6):
                hierarchy_state.pop(l, None)
                hierarchy_intros.pop(l, None)

        # Decide whether to start a new chunk
        must_break = (current_size + line_size > MAX_CHUNK_SIZE) and current_lines
        # Prefer break at top-level markers always, and at one level deeper
        # when the chunk is already large (avoids mid-sentence must_break)
        prefer_break = False
        if level is not None and current_lines:
            if level <= top_level:
                # Always break at top-level hierarchy markers — major
                # structural divisions start fresh chunks regardless of
                # accumulated size to avoid cross-contamination
                prefer_break = True
            elif current_size >= MIN_CHUNK_SIZE:
                if level <= top_level + 1 and current_size >= TARGET_CHUNK_SIZE:
                    prefer_break = True

        if must_break or prefer_break:
            # For must_break, back up to the last hierarchy marker boundary
            # to avoid mid-sentence splits. Only falls back to sentence
            # boundary if no marker exists (single long paragraph).
            if must_break and not prefer_break:
                emit_lines, carry_lines = _split_at_hierarchy_boundary(current_lines)
            else:
                emit_lines = list(current_lines)
                carry_lines = []

            # Emit with intros from chunk START, not current state
            raw_chunks.append((emit_lines, current_label, current_full_path,
                               current_intros))
            current_lines = carry_lines
            current_size = sum(len(l) + 1 for l in carry_lines)
            current_label = hierarchy_state.get(top_level)
            current_full_path = _build_full_hierarchy_path(hierarchy_state)
            # Snapshot current intros for the NEXT chunk
            current_intros = dict(hierarchy_intros)

        # First top-level marker in this chunk becomes its label
        if current_label is None and level is not None and level <= top_level:
            current_label = label
            current_full_path = _build_full_hierarchy_path(hierarchy_state)

        current_lines.append(line)
        current_size += line_size

    if current_lines:
        raw_chunks.append((list(current_lines), current_label,
                           current_full_path, current_intros))

    # Build output dicts
    total = len(raw_chunks)
    result = []
    for n, (chunk_lines, label, full_path, intros) in enumerate(raw_chunks, 1):
        result.append({
            **section,
            "text": "\n".join(chunk_lines),
            "section_title": section["section_title"],  # Always original
            "hierarchy_label": label,
            "hierarchy_full_path": full_path,
            "hierarchy_intros": intros,
            "chunk_n": n,
            "chunk_total": total,
        })

    return result


def _split_at_hierarchy_boundary(lines: list[str]) -> tuple[list[str], list[str]]:
    """
    Find the last hierarchy marker in accumulated lines and split before it.

    When must_break fires, this backs up to the last clean hierarchy boundary
    rather than splitting mid-sentence. The marker line and everything after
    become carry-forward for the next chunk.

    Falls back to _split_at_line_boundary only if no hierarchy marker is found
    (i.e., the accumulator is one long paragraph with no structure).
    """
    marker_re = re.compile(r"^\([a-zA-Z0-9]+\)\s+")

    # Scan backward for the last hierarchy marker
    # Skip index 0 — don't create an empty emit
    for i in range(len(lines) - 1, 0, -1):
        if marker_re.match(lines[i].strip()):
            emit_lines = lines[:i]
            carry_lines = lines[i:]
            if emit_lines:
                return emit_lines, carry_lines

    # No hierarchy marker found — fall back to sentence boundary
    return _split_at_line_boundary(lines)


def _split_at_line_boundary(lines: list[str]) -> tuple[list[str], list[str]]:
    """
    Find a clean break point in accumulated lines for must_break splits.

    Joins lines into text and scans backward for a sentence boundary
    ('. ' or '; ') since PDF line wraps don't align with sentences.
    Returns (emit_lines, carry_forward_lines).
    Falls back to emitting all lines if no clean break is found.
    """
    joined = "\n".join(lines)
    # Search the last 40% of text for a sentence boundary
    search_start = max(0, len(joined) // 2)
    search_zone = joined[search_start:]

    # Find the last sentence-ending pattern in the search zone
    best_pos = -1
    for pattern in [". ", ".\n", "; ", ";\n"]:
        pos = search_zone.rfind(pattern)
        if pos > best_pos:
            best_pos = pos

    if best_pos >= 0:
        # Split at the sentence boundary (after the period/semicolon)
        split_pos = search_start + best_pos + 1  # +1 to include the . or ;
        emit_text = joined[:split_pos].rstrip()
        carry_text = joined[split_pos:].lstrip()
        emit_lines = [l for l in emit_text.split("\n") if l.strip()]
        carry_lines = [l for l in carry_text.split("\n") if l.strip()]
        if emit_lines:
            return emit_lines, carry_lines

    # No clean break found — emit everything
    return list(lines), []


def _split_by_size_only(section: dict, lines: list[str]) -> list[dict]:
    """Fallback split for sections with no hierarchy markers."""
    raw_chunks = _group_segments(lines, separator="\n")
    total = len(raw_chunks)
    result = []
    for n, chunk_text in enumerate(raw_chunks, 1):
        result.append({
            **section,
            "text": chunk_text,
            "section_title": section["section_title"],
            "hierarchy_label": None,
            "chunk_n": n,
            "chunk_total": total,
        })
    return result


def _group_segments(segments: list[str], separator: str = "\n\n") -> list[str]:
    """Greedily group text segments into chunks up to MAX_CHUNK_SIZE."""
    chunks = []
    current_parts = []
    current_size = 0

    for segment in segments:
        seg_size = len(segment)

        if current_size + seg_size > MAX_CHUNK_SIZE and current_parts:
            # Scan backward for clean line boundary
            emit, carry = _split_at_line_boundary(current_parts)
            chunks.append(separator.join(emit))
            current_parts = carry
            current_size = sum(len(p) for p in carry)

        current_parts.append(segment)
        current_size += seg_size

    if current_parts:
        chunks.append(separator.join(current_parts))

    return chunks


def merge_small_chunks(chunks: list[dict]) -> list[dict]:
    """
    Fold sub-MIN_CHUNK_SIZE fragments into their neighbors after splitting.
    Merged chunk keeps the hierarchy_label of its first constituent.
    Recalculates chunk_n and chunk_total after merge.
    """
    if len(chunks) <= 1:
        return chunks

    result = []
    for chunk in chunks:
        if len(chunk["text"]) >= MIN_CHUNK_SIZE or not result:
            result.append(dict(chunk))
        else:
            prev = result[-1]
            prev["text"] = prev["text"] + "\n" + chunk["text"]

    total = len(result)
    for n, chunk in enumerate(result, 1):
        chunk["chunk_n"] = n
        chunk["chunk_total"] = total

    return result


# ============================================================
# PART-LEVEL DOCUMENT CREATION
# ============================================================

def create_part_document(part_num: int, part_title: str,
                         sections: list[dict]) -> dict:
    """Create a part-level document by concatenating all section text."""
    context_prefix = build_context_prefix(part_num, part_title)

    parts = [context_prefix, ""]

    for section in sections:
        sec_num = section["section_number"]
        sec_title = section.get("section_title", "")
        text = section["text"].strip()
        text = append_tables(text, section.get("tables", []))

        if sec_title:
            parts.append(f"## \u00a7 {sec_num} {sec_title}")
        if text:
            parts.append(text)
        parts.append("")

    full_text = "\n".join(parts).strip()

    # Count subparts in this part
    subpart_letters = set()
    for s in sections:
        if "subpart_letter" in s:
            subpart_letters.add(s["subpart_letter"])

    return {
        "chunk_id": make_part_id(part_num),
        "doc_type": "part",
        "text": full_text,
        "metadata": {
            "source": "7 CFR",
            "part": part_num,
            "part_title": part_title,
            "program": get_part_program(part_num, sections),
            "section_count": len(sections),
            "subpart_count": len(subpart_letters),
            "has_tables": str(any(s.get("tables") for s in sections)),
        },
    }


# ============================================================
# SECTION-LEVEL CHUNK CREATION
# ============================================================

def create_section_chunks(part_num: int, part_title: str,
                          sections: list[dict]) -> list[dict]:
    """
    Create section-level chunks applying merge/split/hierarchy logic.

    Flow: sections -> merge_small_sections -> split_with_hierarchy ->
          merge_small_chunks -> annotate with context prefix -> output
    """
    part_id = make_part_id(part_num)

    # Filter out excluded sections (kept in part-level docs only)
    sections = [s for s in sections
                if s["section_number"] not in SECTION_EXCLUDES]

    # Strip excluded sub-items from section text
    for section in sections:
        sec_num = section["section_number"]
        if sec_num in SUBSECTION_EXCLUDES:
            text = section["text"]
            for pattern in SUBSECTION_EXCLUDES[sec_num]:
                match = re.search(pattern, text)
                if match:
                    section["text"] = text[:match.start()]

    # Append table text to section bodies
    sections_with_tables = []
    for section in sections:
        text = append_tables(section["text"], section.get("tables", []))
        sections_with_tables.append({**section, "text": text})

    # Merge tiny sections
    merged = merge_small_sections(sections_with_tables)

    # Split with hierarchy awareness (or dedicated definition chunking)
    chunks = []
    for section in merged:
        is_defs = section.get("section_title", "").lower() == "definitions"
        if is_defs:
            split_chunks = chunk_definitions(section)
        else:
            split_chunks = split_with_hierarchy(section)
            split_chunks = merge_small_chunks(split_chunks)

        sec_num = section["section_number"]
        sec_title = section.get("section_title")
        subpart_letter = section.get("subpart_letter")
        subpart_title = section.get("subpart_title")

        for chunk_idx, chunk in enumerate(split_chunks):
            text = _normalize_line_breaks(chunk["text"].strip())
            if not text:
                continue

            raw_label = chunk.get("hierarchy_label")
            hierarchy_label = (
                _truncate_hierarchy_label(raw_label) if raw_label else None
            )
            # Full path for alternate version (definitions use term name)
            full_path = chunk.get("hierarchy_full_path", "")
            if is_defs:
                full_path = hierarchy_label or ""

            chunk_n = chunk["chunk_n"]
            chunk_total = chunk["chunk_total"]

            # Build context prefix -- include hierarchy label for chunks 2+
            # For definitions, always include it (every term gets labeled);
            # chunk_definitions() sets chunk_n=1 for first chunk of each def.
            include_label = hierarchy_label and (chunk_n > 1 or is_defs)
            prefix = build_context_prefix(
                part_num, part_title, sec_num, sec_title,
                subpart_letter=subpart_letter,
                subpart_title=subpart_title,
                hierarchy_path=hierarchy_label if include_label else None,
            )
            chunk_text = f"{prefix}\n\n{text}"

            # Hierarchy intros for parent context (string keys for JSON)
            raw_intros = chunk.get("hierarchy_intros", {})
            intros = {str(k): v for k, v in raw_intros.items()}

            chunks.append({
                "chunk_id": make_section_id(sec_num, chunk_idx),
                "doc_type": "section",
                "text": chunk_text,
                "metadata": {
                    "source": "7 CFR",
                    "part": part_num,
                    "part_title": part_title,
                    "section_number": sec_num,
                    "section_title": sec_title or "",
                    "subpart_letter": subpart_letter or "",
                    "subpart_title": subpart_title or "",
                    "program": get_program(sec_num, part_num),
                    "hierarchy_path": hierarchy_label or "",
                    "hierarchy_full_path": full_path,
                    "hierarchy_intros": intros,
                    "chunk_n": chunk_n,
                    "chunk_total": chunk_total,
                    "has_tables": str(bool(section.get("tables"))),
                    "cross_references": ",".join(
                        _extract_chunk_cross_refs(chunk_text)
                    ),
                    "parent_part_id": part_id,
                    "pdf_file": section.get("pdf_file", ""),
                },
            })

    return chunks


# ============================================================
# MAIN PROCESSING
# ============================================================

def load_all_sections() -> dict[int, list[dict]]:
    """Load all parsed section JSON files and group by part."""
    section_files = sorted(PARSED_DIR.glob("*.json"))

    if not section_files:
        print(f"No JSON files found in {PARSED_DIR}")
        return {}

    by_part: dict[int, list[dict]] = {}

    for filepath in section_files:
        with open(filepath, "r", encoding="utf-8") as f:
            section = json.load(f)

        part = section["part"]
        if part not in by_part:
            by_part[part] = []
        by_part[part].append(section)

    for part in by_part:
        by_part[part].sort(key=lambda s: s["section_number"])

    return by_part


def process_all_sections() -> tuple[list[dict], list[dict]]:
    """Process all parsed sections and return (part_chunks, section_chunks)."""
    by_part = load_all_sections()

    if not by_part:
        return [], []

    part_chunks = []
    section_chunks = []

    for part_num in sorted(by_part.keys()):
        sections = by_part[part_num]
        part_title = sections[0]["part_title"]

        part_doc = create_part_document(part_num, part_title, sections)
        part_chunks.append(part_doc)

        sec_chunks = create_section_chunks(part_num, part_title, sections)
        section_chunks.extend(sec_chunks)

    return part_chunks, section_chunks


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(part_chunks: list[dict],
                     section_chunks: list[dict]) -> None:
    """Print a summary of the chunking results."""
    print("=" * 60)
    print("7 CFR Chunking Statistics")
    print("=" * 60)
    print()

    pt_sizes = [len(c["text"]) for c in part_chunks]
    print(f"Part-level documents: {len(part_chunks)}")
    print(f"  Median size: {statistics.median(pt_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(pt_sizes):.0f} chars")
    print(f"  Min:         {min(pt_sizes)} chars")
    print(f"  Max:         {max(pt_sizes)} chars")
    print()

    sec_sizes = [len(c["text"]) for c in section_chunks]
    print(f"Section-level chunks: {len(section_chunks)}")
    print(f"  Median size: {statistics.median(sec_sizes):.0f} chars")
    print(f"  Mean size:   {statistics.mean(sec_sizes):.0f} chars")
    print(f"  Min:         {min(sec_sizes)} chars")
    print(f"  Max:         {max(sec_sizes)} chars")
    print()

    buckets = [0, 100, 200, 500, 1000, 1500, 2000, 3000, 5000, 999999]
    print("Section chunk size distribution:")
    for i in range(len(buckets) - 1):
        count = sum(1 for s in sec_sizes if buckets[i] <= s < buckets[i + 1])
        pct = count / len(sec_sizes) * 100
        bar = "#" * (count // 3)
        print(f"  {buckets[i]:>5}-{buckets[i+1]:>5}: {count:>4} ({pct:4.1f}%) {bar}")
    print()

    part_map = {}
    for c in section_chunks:
        pt = c["metadata"]["part"]
        pt_title = c["metadata"]["part_title"]
        key = f"Part {pt}: {pt_title[:40]}"
        part_map[key] = part_map.get(key, 0) + 1
    print("Chunks by part:")
    for pt, count in sorted(part_map.items()):
        print(f"  {pt:55s} {count}")
    print()

    still_small = sum(1 for s in sec_sizes if s < MIN_CHUNK_SIZE)
    still_large = sum(1 for s in sec_sizes if s > MAX_CHUNK_SIZE)
    print(f"Chunks still < {MIN_CHUNK_SIZE} chars after merge: "
          f"{still_small} ({still_small/len(sec_sizes)*100:.1f}%)")
    print(f"Chunks still > {MAX_CHUNK_SIZE} chars after split: "
          f"{still_large} ({still_large/len(sec_sizes)*100:.1f}%)")
    print()

    # Hierarchy-aware metrics
    with_hierarchy = sum(
        1 for c in section_chunks if c["metadata"].get("hierarchy_path")
    )
    multi_chunk_sections = sum(
        1 for c in section_chunks if c["metadata"].get("chunk_total", 1) > 1
    )
    single_chunk = sum(
        1 for c in section_chunks if c["metadata"].get("chunk_total", 1) == 1
    )
    with_subpart = sum(
        1 for c in section_chunks if c["metadata"].get("subpart_letter")
    )
    print(f"Chunks with hierarchy_path:  {with_hierarchy} "
          f"({with_hierarchy/len(section_chunks)*100:.1f}%)")
    print(f"Chunks with subpart info:    {with_subpart} "
          f"({with_subpart/len(section_chunks)*100:.1f}%)")
    print(f"Single-chunk sections:       {single_chunk}")
    print(f"Multi-chunk section parts:   {multi_chunk_sections}")


def preview_chunks(part_chunks: list[dict], section_chunks: list[dict],
                   count: int = 2) -> None:
    """Preview chunks for the first N parts."""
    for part_doc in part_chunks[:count]:
        pt_meta = part_doc["metadata"]
        print("=" * 60)
        print(f"PART: {pt_meta['part']} - {pt_meta['part_title'][:50]}")
        print(f"  Part text length: {len(part_doc['text'])} chars")
        print(f"  Sections in part: {pt_meta['section_count']}")
        print()

        part_id = part_doc["chunk_id"]
        related = [c for c in section_chunks
                   if c["metadata"]["parent_part_id"] == part_id]
        print(f"  Section chunks: {len(related)}")
        for chunk in related[:15]:
            meta = chunk["metadata"]
            sec_num = meta["section_number"]
            sec_title = meta["section_title"] or "(no title)"
            hierarchy = meta.get("hierarchy_path", "")
            h_tag = f"  [{hierarchy[:40]}]" if hierarchy else ""
            text_preview = chunk["text"][:120].replace("\n", " ")
            print(f"    \u00a7 {sec_num} {sec_title}{h_tag}")
            print(f"        {len(chunk['text'])} chars: {text_preview}...")
        if len(related) > 15:
            print(f"    ... and {len(related) - 15} more")
        print()


def build_fullpath_version(section_chunks: list[dict]) -> list[dict]:
    """
    Build an alternate version of section chunks where hierarchy_path
    uses the full path (e.g. '(a)(1)(i)') instead of just the top marker.

    The context prefix in the text is rebuilt to include the full path.
    """
    result = []
    for chunk in section_chunks:
        meta = chunk["metadata"]
        full_path = meta.get("hierarchy_full_path", "")
        old_path = meta.get("hierarchy_path", "")

        # If full_path is the same as old_path (or empty), no change needed
        if full_path == old_path or not full_path:
            result.append(chunk)
            continue

        # Rebuild the context prefix with the full path
        new_prefix = build_context_prefix(
            meta["part"], meta["part_title"],
            meta["section_number"], meta["section_title"] or None,
            subpart_letter=meta["subpart_letter"] or None,
            subpart_title=meta["subpart_title"] or None,
            hierarchy_path=full_path,
        )

        # Replace the first line (old prefix) with the new one
        text = chunk["text"]
        body_start = text.find("\n\n")
        if body_start >= 0:
            new_text = f"{new_prefix}{text[body_start:]}"
        else:
            new_text = text

        new_meta = {**meta, "hierarchy_path": full_path}

        result.append({
            **chunk,
            "text": new_text,
            "metadata": new_meta,
        })

    return result


def build_parent_context_version(section_chunks: list[dict]) -> list[dict]:
    """
    Build an alternate version where each chunk gets a preamble of ancestor
    hierarchy intros, providing semantic context for nested list items.

    Uses full hierarchy paths in the prefix (like build_fullpath_version)
    AND prepends intro lines for ancestor levels not present in the chunk.

    Example preamble for a chunk starting at (iv) under (b)(1):
        (b) Definition of income.
        (1) Earned income shall include:
    """
    # Regex to detect hierarchy markers at line start in chunk text
    marker_re = re.compile(r"^\(([a-zA-Z0-9]+)\)")

    result = []
    for chunk in section_chunks:
        meta = chunk["metadata"]
        intros = meta.get("hierarchy_intros", {})
        full_path = meta.get("hierarchy_full_path", "")

        if not intros:
            result.append(chunk)
            continue

        # Find which hierarchy markers appear in the chunk body text
        text = chunk["text"]
        body_start = text.find("\n\n")
        body = text[body_start + 2:] if body_start >= 0 else text

        markers_in_body = set()
        for line in body.split("\n"):
            m = marker_re.match(line.strip())
            if m:
                markers_in_body.add(m.group(0))  # e.g. "(b)", "(1)"
                break  # Only need the first marker to find the min level

        # Find the minimum (highest in tree) level present in the body
        # by matching the first body marker against intros
        min_body_level = None
        for level_str, intro in sorted(intros.items(), key=lambda x: int(x[0])):
            level = int(level_str)
            # Check if this level's marker appears in the body
            intro_marker = marker_re.match(intro)
            if intro_marker and intro_marker.group(0) in markers_in_body:
                min_body_level = level
                break

        if min_body_level is None:
            # No markers found in body — include all intros as context
            min_body_level = max(int(l) for l in intros.keys()) + 1

        # Build preamble from intros for levels ABOVE min_body_level
        preamble_lines = []
        for level_str in sorted(intros.keys(), key=int):
            level = int(level_str)
            if level < min_body_level:
                preamble_lines.append(intros[level_str])

        if not preamble_lines:
            # No ancestor context needed — just apply full path
            new_prefix = build_context_prefix(
                meta["part"], meta["part_title"],
                meta["section_number"], meta["section_title"] or None,
                subpart_letter=meta["subpart_letter"] or None,
                subpart_title=meta["subpart_title"] or None,
                hierarchy_path=full_path or meta.get("hierarchy_path") or None,
            )
            if body_start >= 0:
                new_text = f"{new_prefix}{text[body_start:]}"
            else:
                new_text = text
        else:
            # Build prefix with full path + preamble between prefix and body
            path_for_prefix = full_path or meta.get("hierarchy_path") or None
            new_prefix = build_context_prefix(
                meta["part"], meta["part_title"],
                meta["section_number"], meta["section_title"] or None,
                subpart_letter=meta["subpart_letter"] or None,
                subpart_title=meta["subpart_title"] or None,
                hierarchy_path=path_for_prefix,
            )
            preamble = "\n".join(preamble_lines)
            if body_start >= 0:
                body_text = text[body_start + 2:]
                new_text = f"{new_prefix}\n{preamble}\n\n{body_text}"
            else:
                new_text = f"{new_prefix}\n{preamble}\n\n{text}"

        new_meta = {
            **meta,
            "hierarchy_path": full_path or meta.get("hierarchy_path", ""),
        }

        result.append({
            **chunk,
            "text": new_text,
            "metadata": new_meta,
        })

    return result


# ============================================================
# CLI
# ============================================================

def main():
    """Parse arguments and run the chunker."""
    parser = argparse.ArgumentParser(
        description="Chunk parsed 7 CFR sections for RAG embedding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chunker.py                  # Process all sections, write output
  python chunker.py --stats          # Show statistics only
  python chunker.py --preview 2      # Preview chunks for 2 parts
        """,
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show statistics only, don't write output files",
    )
    parser.add_argument(
        "--preview", type=int, default=0,
        help="Preview chunks for the first N parts",
    )
    args = parser.parse_args()

    print(f"Reading parsed sections from {PARSED_DIR}...")
    part_chunks, section_chunks = process_all_sections()

    if not part_chunks:
        return

    print_statistics(part_chunks, section_chunks)

    if args.preview > 0:
        preview_chunks(part_chunks, section_chunks, args.preview)

    if not args.stats and not args.preview:
        with open(PART_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(part_chunks, f, indent=2, ensure_ascii=False)
        print(f"\nWrote {len(part_chunks)} part documents to {PART_CHUNKS_FILE}")

        with open(SECTION_CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(section_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(section_chunks)} section chunks to {SECTION_CHUNKS_FILE}")

        # Generate alternate version with full hierarchy paths in prefixes
        fullpath_chunks = build_fullpath_version(section_chunks)
        with open(SECTION_CHUNKS_FULLPATH_FILE, "w", encoding="utf-8") as f:
            json.dump(fullpath_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(fullpath_chunks)} section chunks to "
              f"{SECTION_CHUNKS_FULLPATH_FILE}")

        # Generate version with parent context preambles
        context_chunks = build_parent_context_version(section_chunks)
        with open(SECTION_CHUNKS_CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(context_chunks, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(context_chunks)} section chunks to "
              f"{SECTION_CHUNKS_CONTEXT_FILE}")


if __name__ == "__main__":
    main()
