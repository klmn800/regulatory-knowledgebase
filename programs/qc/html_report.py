"""
QC analysis HTML report — single-file, self-contained, dark-mode-aware.

Mirrors `programs/comparator/report.py` in shape: embedded CSS + JS,
generate_html() returns a full HTML document, main() writes it to disk.

Cross-analysis is the headline value-add. Default scope = all analyses
under output/qc_analysis/. Analysis-scope pill buttons let the user
narrow to one or several. Recurring-gap callout aggregates Partial
findings by OLG URL across whatever analyses are loaded — surfacing
*systemic* OLG holes that show up in multiple QC batches.

Public API:
    load_analyses(names)            -> [{name, label, meta, rows, flat_findings}]
    namespace_findings(analyses)    -> flat list with analysis identity merged in
    compute_recurring_across(flat)  -> wrapper around find_recurring_gaps that
                                        namespaces row_index so cross-batch
                                        row counts aren't understated
    compute_stats(flat_findings)    -> totals dict
    generate_html(analyses, ...)    -> str (full HTML doc)
    main()                          -> CLI entry: --output, --open, --names
"""

import argparse
import json
import re
import sys
import webbrowser
from collections import Counter
from datetime import datetime
from html import escape as _esc
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from programs.qc.qc_analyzer import (
    ANALYSIS_DIR,
    find_recurring_gaps,
    flatten_findings,
    get_analysis_dir,
    load_all_findings,
    load_meta,
)


# ---------------------------------------------------------------------------
# Analysis loading + namespacing
# ---------------------------------------------------------------------------

# Strip trailing `_YYYY-MM-DD_HHMM` and a trailing `-QC-Report` (case-insensitive)
# to get a short label like "Oct-2025" from "Oct-2025-QC-Report_2026-05-07_1428".
_TS_SUFFIX_RE = re.compile(r"_\d{4}-\d{2}-\d{2}_\d{4}$")
_QC_REPORT_SUFFIX_RE = re.compile(r"[-_]QC[-_]Report$", re.IGNORECASE)
_DOM_UNSAFE_RE = re.compile(r"[^A-Za-z0-9_-]")


def _label_for(name: str) -> str:
    """Short pretty label for an analysis name (used on filter pills)."""
    base = _TS_SUFFIX_RE.sub("", name)
    base = _QC_REPORT_SUFFIX_RE.sub("", base)
    return base or name


def _dom_safe(s: str) -> str:
    return _DOM_UNSAFE_RE.sub("_", s)


def list_analysis_names() -> list[str]:
    """All analysis directory names under output/qc_analysis/, sorted."""
    if not ANALYSIS_DIR.exists():
        return []
    return sorted(d.name for d in ANALYSIS_DIR.iterdir() if d.is_dir())


def load_analyses(names: list[str] | None = None) -> list[dict]:
    """Load named analyses (or all when names is None).

    Returns a dict per analysis with name/label/meta/rows/flat_findings.
    Skips names whose directories don't exist (rather than erroring) so
    a stale URL doesn't blow up the page.
    """
    if names is None:
        names = list_analysis_names()
    out = []
    for name in names:
        # Don't use get_analysis_dir() here — it creates the directory as a
        # side effect, which would silently materialize bad ?names= URLs as
        # empty analyses. Check pre-existence against ANALYSIS_DIR directly.
        d = ANALYSIS_DIR / name
        if not d.exists():
            continue
        rows = load_all_findings(d)
        meta = load_meta(d) or {}
        flat = flatten_findings(rows)
        out.append({
            "name": name,
            "label": _label_for(name),
            "meta": meta,
            "rows": rows,
            "flat_findings": flat,
        })
    return out


def namespace_findings(analyses: list[dict]) -> list[dict]:
    """Flatten across analyses, merging in analysis identity.

    Adds:
        analysis_name      directory name (stable id)
        analysis_label     short pretty label (e.g., "Oct-2025")
        ns_display_index   "<label>/<display_index>" — disambiguates 5.1 across batches
        ns_detail_id       DOM-safe (analysis_name + "_" + detail_id)

    Leaves row_index, finding_index, display_index untouched for back-compat.
    """
    out = []
    for a in analyses:
        for entry in a["flat_findings"]:
            ns = dict(entry)
            ns["analysis_name"] = a["name"]
            ns["analysis_label"] = a["label"]
            disp = entry.get("display_index", "")
            ns["ns_display_index"] = f"{a['label']}/{disp}" if disp else a["label"]
            detail_id = entry.get("detail_id") or (
                f"{entry.get('row_index')}_{entry.get('finding_index')}"
            )
            ns["ns_detail_id"] = f"{_dom_safe(a['name'])}_{detail_id}"
            out.append(ns)
    return out


# ---------------------------------------------------------------------------
# Recurring-gap detection — wrapper that namespaces row_index across analyses
# ---------------------------------------------------------------------------

def compute_recurring_across(flat_findings: list[dict],
                             min_rows: int = 2) -> list[dict]:
    """Find OLG URLs cited in Partial findings across multiple rows.

    `find_recurring_gaps()` correctly keys gaps by URL, but its row-count
    set keys on raw row_index — which collides across analyses (Oct row 5
    and Sept row 5 collapse). To avoid understating cross-batch frequency,
    namespace row_index before the call, then unwrap after. Each returned
    gap's `findings` list is enriched with analysis_name and ns_display_index
    so the UI can deep-link to a specific (analysis, finding).
    """
    namespaced = []
    for entry in flat_findings:
        copy = dict(entry)
        an = entry.get("analysis_name", "")
        copy["row_index"] = f"{an}#{entry.get('row_index')}"
        copy["display_index"] = entry.get("ns_display_index", copy.get("display_index"))
        namespaced.append(copy)

    gaps = find_recurring_gaps(namespaced, min_rows=min_rows)

    for gap in gaps:
        for f in gap.get("findings", []):
            ns_row = f.get("row_index")
            if isinstance(ns_row, str) and "#" in ns_row:
                an, raw = ns_row.split("#", 1)
                f["analysis_name"] = an
                try:
                    f["row_index"] = int(raw)
                except (TypeError, ValueError):
                    f["row_index"] = raw
    return gaps


# ---------------------------------------------------------------------------
# Per-finding derived attributes
# ---------------------------------------------------------------------------

# Maps the path segment after `/WebHelp/` in an OLG URL to a human label.
# The OLG site uses path-based namespacing for programs.
_PROGRAM_FROM_PATH = {
    "snap": "SNAP",
    "tafdc": "TAFDC",
    "eaedc": "EAEDC",
    "crossprog": "Cross-Program",
    "bp": "BP",
    "pathways": "Pathways",
    "harper": "Harper",
    "selfservice": "Self-Service",
    "self-service": "Self-Service",
    "domesticviolence": "Domestic Violence",
    "policiesproc": "Policies & Procedures",
    "sunbucks": "SUN Bucks",
    "general": "General",
}


def _program_from_url(url: str) -> str:
    """Derive an OLG program label from a URL.

    OLG URLs are shaped like `.../WebHelp/SNAP/...` or `.../WebHelp/CrossProg/...`.
    We pull the segment after `/WebHelp/` and map it to a known program label.
    Returns "" when the path isn't recognizable.
    """
    if not url:
        return ""
    try:
        path = urlparse(url).path
    except (ValueError, TypeError):
        return ""
    parts = [p for p in path.split("/") if p]
    try:
        idx = parts.index("WebHelp")
    except ValueError:
        return ""
    if idx + 1 >= len(parts):
        return ""
    return _PROGRAM_FROM_PATH.get(parts[idx + 1].lower(), parts[idx + 1])


_REF_URL_RE = re.compile(r"\((https?://[^)\s]+)\)\s*$")


def _ref_url(ref: str) -> str:
    """Pull the URL out of an olg_references entry."""
    if not isinstance(ref, str):
        return ""
    m = _REF_URL_RE.search(ref)
    return m.group(1) if m else ""


def _ref_label(ref: str) -> str:
    """Pull the human-readable part (everything before the URL) out of an olg_references entry."""
    if not isinstance(ref, str):
        return ""
    m = _REF_URL_RE.search(ref)
    if not m:
        return ref
    return ref[:m.start()].strip()


def _programs_for_finding(entry: dict) -> set[str]:
    """Set of programs derived from a finding's olg_references URLs."""
    progs = set()
    for ref in entry.get("olg_references", []) or []:
        url = _ref_url(ref)
        prog = _program_from_url(url)
        if prog:
            progs.add(prog)
    return progs


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(flat_findings: list[dict]) -> dict:
    """Totals across the flat list."""
    by_coverage = Counter(e.get("coverage", "Unknown") for e in flat_findings)
    by_analysis = Counter(e.get("analysis_label", "?") for e in flat_findings)
    confidence = Counter(e.get("confidence", "?") for e in flat_findings)

    by_program = Counter()
    for e in flat_findings:
        for p in _programs_for_finding(e):
            by_program[p] += 1

    cross_check_classes = {"cmr": Counter(), "fns": Counter(), "cfr": Counter()}
    for e in flat_findings:
        for src in ("cmr", "fns", "cfr"):
            blk = e.get(f"_{src}_check") or {}
            cls = blk.get("classification")
            if cls:
                cross_check_classes[src][cls] += 1

    return {
        "total": len(flat_findings),
        "by_coverage": by_coverage,
        "by_analysis": by_analysis,
        "by_program": by_program,
        "by_confidence": confidence,
        "cross_check_classes": cross_check_classes,
    }


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def esc(text: str) -> str:
    return _esc(text or "", quote=True)


# Coverage badge colors — same palette as comparator's classification badges
COVERAGE_STYLES = {
    "Adequate": ("#166534", "#dcfce7"),
    "Partial":  ("#92400e", "#fef3c7"),
    "Gap":      ("#991b1b", "#fee2e2"),
    "Error":    ("#6b21a8", "#f3e8ff"),
    "Skipped":  ("#374151", "#f3f4f6"),
    "Unknown":  ("#374151", "#f3f4f6"),
}

CONFIDENCE_COLORS = {
    "HIGH":   "#166534",
    "MEDIUM": "#92400e",
    "LOW":    "#991b1b",
    "N/A":    "#6b7280",
}

# Bucket cross-check classifications into 3 alignment buckets so each source
# uses the same filter labels (Aligns / Silent / Differs).
CROSS_CHECK_BUCKETS = {
    # CMR
    "cmr_covers_topic": "aligns",
    "cmr_silent":       "silent",
    "cmr_differs":      "differs",
    # FNS
    "fns_requires":     "aligns",
    "fns_covers_topic": "aligns",
    "fns_silent":       "silent",
    "fns_differs":      "differs",
    # CFR
    "cfr_covers_topic": "aligns",
    "cfr_silent":       "silent",
    "cfr_differs":      "differs",
}


def _bucket(classification: str) -> str:
    return CROSS_CHECK_BUCKETS.get(classification, "")


# ---------------------------------------------------------------------------
# Recurring set: which findings are part of any recurring URL group
# ---------------------------------------------------------------------------

def _recurring_finding_ids(recurring_gaps: list[dict]) -> set[tuple]:
    """Set of (analysis_name, row_index, finding_index) tuples that show up
    in any recurring gap. Used to mark `data-recurring="true"` on rows."""
    ids = set()
    for gap in recurring_gaps:
        for f in gap.get("findings", []):
            an = f.get("analysis_name", "")
            ri = f.get("row_index")
            fi = f.get("finding_index")
            ids.add((an, ri, fi))
    return ids


def _is_recurring(entry: dict, recurring_ids: set[tuple]) -> bool:
    return (
        entry.get("analysis_name", ""),
        entry.get("row_index"),
        entry.get("finding_index"),
    ) in recurring_ids


# ===========================================================================
# CSS  ----------------------------------------------------------------------
# ===========================================================================

CSS = r"""
:root {
    --bg-page: #f3f4f6;
    --bg-surface: #fff;
    --bg-surface-alt: #f9fafb;
    --bg-hover: #e5e7eb;
    --bg-expanded: #dbeafe;
    --bg-input: #e5e7eb;
    --bg-input-hover: #d1d5db;
    --text-primary: #111827;
    --text-heading: #030712;
    --text-secondary: #1f2937;
    --text-muted: #4b5563;
    --text-faint: #6b7280;
    --border: #cbd5e1;
    --border-light: #d1d5db;
    --link: #1d4ed8;
    --expand-bg: #bfdbfe;
    --expand-text: #1d4ed8;
    --accent: #2563eb;
    --accent-fg: #fff;
    --chip-bg: #bfdbfe;
    --chip-fg: #1e3a8a;
    --recurring-bg: #fef3c7;
    --recurring-border: #f59e0b;
    --flag-color: #dc2626;
    --toast-bg: #1f2937;
    --toast-text: #fff;
}

body.dark {
    --bg-page: #0a0f1c;
    --bg-surface: #243049;
    --bg-surface-alt: #1a2238;
    --bg-hover: #334155;
    --bg-expanded: #234876;
    --bg-input: #334155;
    --bg-input-hover: #475569;
    --text-primary: #f1f5f9;
    --text-heading: #ffffff;
    --text-secondary: #e2e8f0;
    --text-muted: #cbd5e1;
    --text-faint: #94a3b8;
    --border: #475569;
    --border-light: #334155;
    --link: #93c5fd;
    --expand-bg: #234876;
    --expand-text: #bfdbfe;
    --accent: #3b82f6;
    --chip-bg: #234876;
    --chip-fg: #bfdbfe;
    --recurring-bg: #4a2e0a;
    --recurring-border: #fbbf24;
    --toast-bg: #f1f5f9;
    --toast-text: #0f172a;
}

/* Robust hidden support — UA rules can be overridden by display:flex
   on parent rules, so make `hidden` win unconditionally. */
[hidden] { display: none !important; }

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text-primary);
    background: var(--bg-page);
    line-height: 1.5;
    padding: 1.5rem 2rem;
    transition: background 0.2s, color 0.2s;
}

header { margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
h1 { font-size: 1.5rem; color: var(--text-heading); margin-bottom: 0.125rem; }
.subtitle { font-size: 0.875rem; color: var(--text-muted); }
.theme-toggle, .header-action {
    background: var(--bg-input); border: 1px solid var(--border);
    border-radius: 0.5rem; padding: 0.375rem 0.75rem;
    font-size: 0.8125rem; color: var(--text-muted);
    cursor: pointer; margin-top: 0.25rem;
    text-decoration: none; display: inline-block;
}
.theme-toggle:hover, .header-action:hover {
    background: var(--bg-input-hover); color: var(--text-primary);
}
.header-actions {
    display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: flex-start;
}

/* ── Stats row ─────────────────────────────────────────── */
.summary {
    display: flex; gap: 0.625rem; margin-bottom: 1rem; flex-wrap: wrap;
}
.card {
    background: var(--bg-surface); border: 1px solid var(--border);
    border-radius: 0.5rem; padding: 0.625rem 1rem; min-width: 90px;
    text-align: center; border-top: 3px solid var(--border);
}
.card-num { font-size: 1.25rem; font-weight: 700; }
.card-label { font-size: 0.6875rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.card.total { border-top-color: #2563eb; }
.card.total .card-num { color: #2563eb; }

/* ── Recurring callout (collapsed by default) ─────────── */
details.recurring-panel {
    background: var(--bg-surface); border: 1px solid var(--recurring-border);
    border-left-width: 4px;
    border-radius: 0.5rem; padding: 0.625rem 1rem; margin-bottom: 1rem;
}
details.recurring-panel[open] { padding-bottom: 0.875rem; }
details.recurring-panel > summary {
    cursor: pointer; list-style: none;
    font-size: 0.875rem; font-weight: 600; color: var(--text-heading);
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.125rem 0;
}
details.recurring-panel > summary::-webkit-details-marker { display: none; }
details.recurring-panel > summary::before {
    content: "▸"; display: inline-block; transition: transform 0.15s;
    color: var(--text-muted); font-size: 0.75rem; min-width: 0.875rem;
}
details.recurring-panel[open] > summary::before { transform: rotate(90deg); }
details.recurring-panel[open] > summary { margin-bottom: 0.5rem; }
details.recurring-panel .badge-count {
    background: var(--recurring-bg); color: var(--text-secondary);
    padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.75rem;
    font-weight: 600;
}
.recurring-panel ul { list-style: none; }
.recurring-panel li {
    padding: 0.4375rem 0; border-top: 1px solid var(--border-light);
    font-size: 0.8125rem; display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: baseline;
}
.recurring-panel li:first-child { border-top: none; }
.recurring-panel a.page-link {
    color: var(--link); text-decoration: none; font-weight: 500;
}
.recurring-panel a.page-link:hover { text-decoration: underline; }
.recurring-panel .row-count {
    font-size: 0.75rem; color: var(--text-muted); white-space: nowrap;
}
.recurring-panel .finding-chip {
    display: inline-block; padding: 0.0625rem 0.4375rem;
    background: var(--chip-bg); color: var(--chip-fg);
    border-radius: 9999px; font-size: 0.6875rem; font-weight: 600;
    cursor: pointer; text-decoration: none;
    transition: filter 0.15s;
}
.recurring-panel .finding-chip:hover { filter: brightness(1.1); }
.recurring-panel .show-more {
    background: none; border: none; color: var(--link);
    font-size: 0.75rem; cursor: pointer; padding: 0.25rem 0;
}
.recurring-panel .hidden-row { display: none; }
.recurring-panel.show-all .hidden-row { display: flex; }
.agent-notes-panel .agent-notes-aux {
    font-size: 0.78rem; color: var(--text-muted);
    margin: 0 0 0.5rem 0;
}
.agent-notes-list { list-style: none; }
.agent-notes-list li {
    padding: 0.5rem 0; border-top: 1px solid var(--border-light);
    font-size: 0.8125rem; display: block;
}
.agent-notes-list li:first-child { border-top: none; }
.agent-notes-body {
    margin-top: 0.3125rem; white-space: pre-wrap;
    color: var(--text);
}

/* ── Filters ──────────────────────────────────────────── */
.filters { margin-bottom: 0.875rem; }
.active-chips {
    display: flex; gap: 0.375rem; flex-wrap: wrap;
    margin-bottom: 0.625rem; min-height: 1.5rem;
}
.active-chip {
    display: inline-flex; align-items: center; gap: 0.3125rem;
    background: var(--accent); color: var(--accent-fg);
    border-radius: 9999px; padding: 0.1875rem 0.5rem 0.1875rem 0.625rem;
    font-size: 0.75rem; font-weight: 600; cursor: pointer;
}
.active-chip .x { font-size: 0.875rem; line-height: 1; opacity: 0.8; }
.active-chip:hover .x { opacity: 1; }
.active-chips .clear-all {
    background: none; border: 1px solid var(--border);
    color: var(--text-muted);
    border-radius: 9999px; padding: 0.1875rem 0.625rem;
    font-size: 0.75rem; cursor: pointer;
}

.search-row { display: flex; gap: 0.5rem; margin-bottom: 0.625rem; align-items: center; }
.search-row input {
    flex: 1; max-width: 480px;
    padding: 0.4375rem 0.75rem; border: 1px solid var(--border);
    border-radius: 0.375rem; background: var(--bg-surface);
    color: var(--text-primary); font-size: 0.875rem;
}
.search-row input:focus { outline: none; border-color: var(--accent); }
.search-row button.toggle-more {
    background: var(--bg-input); border: 1px solid var(--border);
    color: var(--text-secondary);
    border-radius: 0.375rem; padding: 0.4375rem 0.75rem;
    font-size: 0.8125rem; cursor: pointer; white-space: nowrap;
}

.filter-rows { display: flex; flex-direction: column; gap: 0.375rem; }
.filter-row {
    display: flex; align-items: center; gap: 0.375rem; flex-wrap: wrap;
}
.filter-row .filter-label {
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em; min-width: 70px;
}
.filter-btn {
    background: var(--bg-surface); border: 1px solid var(--border);
    border-radius: 9999px; padding: 0.1875rem 0.625rem;
    font-size: 0.75rem; color: var(--text-secondary);
    cursor: pointer; transition: all 0.15s;
}
.filter-btn:hover { background: var(--bg-hover); }
.filter-btn.active { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }
.filter-btn[disabled] { opacity: 0.45; cursor: not-allowed; }

.more-filters[hidden] { display: none !important; }

/* ── Toolbar ──────────────────────────────────────────── */
.toolbar {
    display: flex; gap: 0.5rem; align-items: center;
    margin-bottom: 0.5rem;
}
#row-count { font-size: 0.8125rem; color: var(--text-muted); flex: 1; }
.toolbar-btn {
    background: none; border: 1px solid var(--border);
    border-radius: 0.375rem; padding: 0.25rem 0.625rem;
    font-size: 0.75rem; color: var(--text-muted); cursor: pointer;
}
.toolbar-btn:hover { background: var(--bg-hover); color: var(--text-primary); }

/* ── Table ────────────────────────────────────────────── */
table {
    width: 100%; border-collapse: collapse; background: var(--bg-surface);
    border: 1px solid var(--border); border-radius: 0.5rem; overflow: hidden;
}
thead { position: sticky; top: 0; z-index: 10; }
th {
    background: var(--bg-page); border-bottom: 2px solid var(--border);
    padding: 0.5rem 0.75rem; text-align: left;
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em;
}
th.sortable { cursor: pointer; user-select: none; }
th.sortable:hover { color: var(--text); }
th.sortable .sort-arrow { font-size: 0.625rem; opacity: 0.65; margin-left: 0.125rem; }
th.sortable:hover .sort-arrow { opacity: 1; }
.main-row { cursor: pointer; }
.main-row:hover { background: var(--bg-hover); }
.main-row td {
    padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-light);
    font-size: 0.8125rem; vertical-align: top;
}
.main-row.expanded { background: var(--bg-expanded); }
.main-row[data-recurring="true"] td.col-flag { box-shadow: inset 3px 0 0 var(--recurring-border); }
.main-row[data-coverage="Gap"] td.col-flag { box-shadow: inset 3px 0 0 var(--flag-color); }

.col-flag { width: 2rem; text-align: center; padding-left: 0.5rem !important; padding-right: 0 !important; }
.col-analysis { width: 6rem; }
.col-disp { width: 4rem; font-weight: 600; white-space: nowrap; }
.col-cov { width: 6rem; }
.col-conf { width: 3.5rem; text-align: center; }
.col-issue { color: var(--text-secondary); }
.col-expand { width: 2rem; text-align: center; }

.flag-btn {
    background: none; border: none; cursor: pointer;
    font-size: 0.875rem; line-height: 1; padding: 0;
    color: var(--border); transition: color 0.15s, transform 0.1s;
}
.flag-btn:hover { color: var(--flag-color); transform: scale(1.2); }
.flag-btn.active { color: var(--flag-color); }

.badge {
    display: inline-block; padding: 0.0625rem 0.4375rem;
    border-radius: 9999px; font-size: 0.6875rem; font-weight: 600;
    white-space: nowrap;
}

.expand-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.375rem; height: 1.375rem; border-radius: 50%;
    background: var(--bg-input); color: var(--text-muted); font-size: 0.8125rem;
    font-weight: 600;
}
.main-row.expanded .expand-icon {
    transform: rotate(45deg); background: var(--expand-bg); color: var(--expand-text);
}

/* ── Detail row ──────────────────────────────────────── */
.detail-row { display: none; }
.detail-row.visible { display: table-row; }
.detail-row > td { padding: 0; border-bottom: 2px solid var(--border); }
.detail-panel {
    padding: 1rem 1.25rem; background: var(--bg-surface-alt);
    border-top: 1px solid var(--border);
}
.detail-section { margin-bottom: 0.875rem; }
.detail-section h4 {
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;
    padding-bottom: 0.1875rem; border-bottom: 1px solid var(--border);
}
.detail-section p {
    font-size: 0.8125rem; line-height: 1.65; color: var(--text-secondary);
    white-space: pre-wrap;
}

.olg-refs { list-style: none; margin-top: 0.25rem; }
.olg-refs li { padding: 0.125rem 0; font-size: 0.8125rem; line-height: 1.5; }
.olg-refs a { color: var(--link); text-decoration: none; }
.olg-refs a:hover { text-decoration: underline; }

/* ── Cross-check blocks (stacked) ─────────────────────── */
.crosscheck-stack { display: flex; flex-direction: column; gap: 0.625rem; margin-top: 0.5rem; }
.crosscheck-block {
    border: 1px solid var(--border); border-left-width: 3px;
    border-radius: 0.375rem; padding: 0.625rem 0.875rem;
    background: var(--bg-surface);
}
.crosscheck-block.aligns { border-left-color: #16a34a; }
.crosscheck-block.silent { border-left-color: #6b7280; }
.crosscheck-block.differs { border-left-color: #dc2626; }
.crosscheck-block.silent { opacity: 0.85; }
.crosscheck-head {
    display: flex; align-items: center; gap: 0.5rem;
    margin-bottom: 0.25rem; font-size: 0.75rem;
}
.crosscheck-head .src {
    font-weight: 700; color: var(--text-heading);
    background: var(--bg-input); padding: 0.0625rem 0.4375rem;
    border-radius: 0.25rem; min-width: 2.5rem; text-align: center;
}
.crosscheck-head .cls {
    font-weight: 600; color: var(--text-secondary); font-size: 0.6875rem;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.crosscheck-block .secs {
    font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.1875rem;
    font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
}
.crosscheck-block .note {
    font-size: 0.8125rem; line-height: 1.55; color: var(--text-secondary);
}

/* ── Judge trace (collapsible) ────────────────────────── */
details.judge-trace {
    margin-top: 0.625rem; padding: 0.5rem 0.75rem;
    background: var(--bg-surface); border: 1px solid var(--border-light);
    border-radius: 0.375rem; font-size: 0.8125rem;
}
details.judge-trace > summary {
    cursor: pointer; color: var(--text-muted);
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
}
.trace-turn {
    margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-light);
}
.trace-turn .trace-head {
    font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;
    font-family: "Cascadia Code", Consolas, monospace;
}
.trace-turn p { font-size: 0.8125rem; line-height: 1.5; color: var(--text-secondary); white-space: pre-wrap; }
.trace-turn .tool-call { font-size: 0.75rem; color: var(--text-muted); padding: 0.125rem 0; font-family: monospace; }

/* ── Coverage / case identity meta ────────────────────── */
.case-meta { display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.case-meta dt { font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.6875rem; }
.case-meta dd { margin-top: 0.0625rem; color: var(--text-secondary); font-size: 0.8125rem; }

/* ── Hidden (filtered) ───────────────────────────────── */
.main-row.hidden, .detail-row.hidden { display: none !important; }

/* ── Empty state ─────────────────────────────────────── */
.empty-state {
    padding: 2rem; text-align: center; color: var(--text-muted);
    font-size: 0.875rem;
}

/* ── Footer ──────────────────────────────────────────── */
footer {
    margin-top: 1.25rem; padding: 1rem 1.25rem; background: var(--bg-surface);
    border: 1px solid var(--border); border-radius: 0.5rem;
    font-size: 0.8125rem; color: var(--text-secondary);
}
footer h3 { font-size: 0.9375rem; margin-bottom: 0.375rem; color: var(--text-heading); }
footer ul { padding-left: 1.25rem; margin-top: 0.25rem; }
footer li { margin-bottom: 0.1875rem; line-height: 1.5; }

/* Scroll-target highlight pulse when a row is jumped to */
@keyframes pulse-highlight {
    0% { background: var(--bg-expanded); }
    100% { background: var(--bg-surface); }
}
.main-row.pulse { animation: pulse-highlight 1.5s ease-out; }

@media (max-width: 720px) {
    body { padding: 0.75rem; }
    .col-analysis { width: auto; }
}

/* ── Session ID resume chip ───────────────────────────── */
.session-id-row { margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted); }
.session-id {
    font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
    font-size: 0.6875rem; background: var(--bg-input);
    padding: 0.0625rem 0.4375rem; border-radius: 0.25rem;
    cursor: pointer; word-break: break-all; transition: background 0.15s;
    color: var(--text-secondary);
}
.session-id:hover { background: var(--bg-input-hover); }

/* ── Per-row collapse footer ──────────────────────────── */
.detail-footer {
    margin-top: 1rem; padding-top: 0.625rem;
    border-top: 1px solid var(--border-light);
    display: flex; justify-content: flex-end;
}
.btn-collapse {
    background: var(--bg-input); border: 1px solid var(--border);
    border-radius: 0.375rem; padding: 0.3125rem 0.75rem;
    font-size: 0.75rem; color: var(--text-secondary);
    cursor: pointer;
}
.btn-collapse:hover { background: var(--bg-input-hover); color: var(--text-primary); }

/* ── Toast ────────────────────────────────────────────── */
.toast {
    position: fixed; bottom: 1.5rem; right: 1.5rem;
    background: var(--toast-bg); color: var(--toast-text);
    padding: 0.625rem 1rem; border-radius: 0.5rem;
    font-size: 0.8125rem; opacity: 0;
    transition: opacity 0.3s; z-index: 1000;
    pointer-events: none;
}
.toast.show { opacity: 1; }
"""


# ===========================================================================
# JavaScript  ---------------------------------------------------------------
# ===========================================================================

JS = r"""
/* ── Active filter state ─────────────────────────────── */
var FILTER_STATE = {
    scope: "",        // "" = all
    coverage: "",     // "Adequate" | "Partial" | "Gap" | "Error" | "Skipped"
    program: "",      // OLG program label
    cmr: "",          // "aligns" | "silent" | "differs"
    fns: "",
    cfr: "",
    confidence: "",   // "HIGH" | "MEDIUM" | "LOW"
    recurring: "",    // "yes" | "no"
    flag: "",         // "yes" | "no"
    search: "",       // free text
};

var FILTER_LABELS = {
    scope: "Scope",
    coverage: "Coverage",
    program: "Program",
    cmr: "CMR",
    fns: "FNS",
    cfr: "CFR",
    confidence: "Confidence",
    recurring: "Recurring",
    flag: "Flag",
    search: "Search",
};

/* ── Theme ───────────────────────────────────────────── */
function initTheme() {
    var saved = localStorage.getItem("qc_report_theme");
    if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
        document.body.classList.add("dark");
    }
    updateThemeBtn();
}
function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem("qc_report_theme",
        document.body.classList.contains("dark") ? "dark" : "light");
    updateThemeBtn();
}
function updateThemeBtn() {
    var btn = document.getElementById("theme-btn");
    if (!btn) return;
    btn.textContent = document.body.classList.contains("dark") ? "☀ Light mode" : "☾ Dark mode";
}

/* ── Flags (localStorage; keyed by ns_detail_id) ─────── */
var FLAGS = new Set(JSON.parse(localStorage.getItem("qc_report_flags") || "[]"));

function initFlags() {
    document.querySelectorAll(".main-row").forEach(function(r) {
        var key = r.dataset.key;
        var on = FLAGS.has(key);
        r.dataset.flag = on ? "yes" : "no";
        var btn = r.querySelector(".flag-btn");
        if (btn) btn.classList.toggle("active", on);
    });
    updateFlagCount();
}
function toggleFlag(btn, evt) {
    evt.stopPropagation();
    var row = btn.closest("tr");
    if (!row) return;
    var key = row.dataset.key;
    if (FLAGS.has(key)) { FLAGS.delete(key); }
    else { FLAGS.add(key); }
    var on = FLAGS.has(key);
    btn.classList.toggle("active", on);
    row.dataset.flag = on ? "yes" : "no";
    var detail = row.nextElementSibling;
    if (detail && detail.classList.contains("detail-row")) detail.dataset.flag = row.dataset.flag;
    localStorage.setItem("qc_report_flags", JSON.stringify(Array.from(FLAGS)));
    updateFlagCount();
    applyFilters();
}
function updateFlagCount() {
    var el = document.getElementById("flag-count");
    if (el) el.textContent = FLAGS.size;
}

/* ── Filters ─────────────────────────────────────────── */
function setFilter(dim, value) {
    if (FILTER_STATE[dim] === value) {
        FILTER_STATE[dim] = "";
    } else {
        FILTER_STATE[dim] = value;
    }
    applyFilters();
}

function clearFilter(dim) {
    FILTER_STATE[dim] = "";
    applyFilters();
}

function clearAllFilters() {
    Object.keys(FILTER_STATE).forEach(function(k) { FILTER_STATE[k] = ""; });
    var input = document.getElementById("search-input");
    if (input) input.value = "";
    applyFilters();
}

function rowMatches(r) {
    var s = FILTER_STATE;
    if (s.scope && r.dataset.scope !== s.scope) return false;
    if (s.coverage && r.dataset.coverage !== s.coverage) return false;
    if (s.program && (r.dataset.programs || "").split("|").indexOf(s.program) < 0) return false;
    if (s.cmr && r.dataset.cmrBucket !== s.cmr) return false;
    if (s.fns && r.dataset.fnsBucket !== s.fns) return false;
    if (s.cfr && r.dataset.cfrBucket !== s.cfr) return false;
    if (s.confidence && r.dataset.confidence !== s.confidence) return false;
    if (s.recurring && r.dataset.recurring !== (s.recurring === "yes" ? "true" : "false")) return false;
    if (s.flag && r.dataset.flag !== s.flag) return false;
    if (s.search) {
        var hay = (r.dataset.search || "").toLowerCase();
        if (hay.indexOf(s.search.toLowerCase()) < 0) return false;
    }
    return true;
}

function applyFilters() {
    var rows = document.querySelectorAll(".main-row");
    var visible = 0;
    rows.forEach(function(r) {
        var show = rowMatches(r);
        r.classList.toggle("hidden", !show);
        if (show) visible++;
        var detail = r.nextElementSibling;
        if (detail && detail.classList.contains("detail-row")) {
            detail.classList.toggle("hidden", !show);
            if (!show) {
                detail.classList.remove("visible");
                r.classList.remove("expanded");
            }
        }
    });
    document.getElementById("row-count").textContent =
        (visible === rows.length)
            ? "Showing all " + rows.length + " findings"
            : "Showing " + visible + " of " + rows.length + " findings";
    var empty = document.getElementById("empty-state");
    if (empty) empty.style.display = visible === 0 ? "block" : "none";
    syncFilterButtons();
    renderActiveChips();
}

function syncFilterButtons() {
    document.querySelectorAll(".filter-btn[data-dim]").forEach(function(b) {
        var dim = b.dataset.dim;
        var val = b.dataset.value || "";
        b.classList.toggle("active", FILTER_STATE[dim] === val);
    });
}

function renderActiveChips() {
    var box = document.getElementById("active-chips");
    if (!box) return;
    box.innerHTML = "";
    var any = false;
    Object.keys(FILTER_STATE).forEach(function(dim) {
        var v = FILTER_STATE[dim];
        if (!v) return;
        any = true;
        var chip = document.createElement("button");
        chip.className = "active-chip";
        chip.title = "Click to remove this filter";
        var prettyVal = (dim === "search") ? '"' + v + '"' : v;
        chip.innerHTML = '<span>' + FILTER_LABELS[dim] + ': ' + escapeHtml(prettyVal) + '</span><span class="x">×</span>';
        chip.onclick = function() {
            if (dim === "search") {
                var input = document.getElementById("search-input");
                if (input) input.value = "";
            }
            clearFilter(dim);
        };
        box.appendChild(chip);
    });
    if (any) {
        var clearBtn = document.createElement("button");
        clearBtn.className = "clear-all";
        clearBtn.textContent = "Clear all";
        clearBtn.onclick = clearAllFilters;
        box.appendChild(clearBtn);
    }
}

function escapeHtml(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

/* Debounced search input handler */
var _searchTimer;
function onSearchInput(input) {
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(function() {
        FILTER_STATE.search = input.value.trim();
        applyFilters();
    }, 200);
}

/* ── Sort by # column ────────────────────────────────── */
function sortByDisp(th) {
    var dir = th.dataset.sortDir === "asc" ? "desc" : "asc";
    th.dataset.sortDir = dir;
    var arrow = th.querySelector(".sort-arrow");
    if (arrow) arrow.textContent = dir === "asc" ? "▲" : "▼";

    var tbody = th.closest("table").querySelector("tbody");
    if (!tbody) return;
    var mains = Array.prototype.slice.call(tbody.querySelectorAll(".main-row"));
    var pairs = mains.map(function(m) {
        return { main: m, detail: m.nextElementSibling, key: parseInt(m.dataset.sortDisp || "0", 10) };
    });
    pairs.sort(function(a, b) { return dir === "asc" ? a.key - b.key : b.key - a.key; });
    pairs.forEach(function(p) {
        tbody.appendChild(p.main);
        if (p.detail && p.detail.classList.contains("detail-row")) tbody.appendChild(p.detail);
    });
}

/* ── Expand / collapse ───────────────────────────────── */
function toggleRow(key) {
    var row = document.querySelector('.main-row[data-key="' + key + '"]');
    if (!row) return;
    var detail = row.nextElementSibling;
    if (!detail) return;
    var open = detail.classList.toggle("visible");
    row.classList.toggle("expanded", open);
}

function expandAll() {
    document.querySelectorAll(".main-row:not(.hidden)").forEach(function(r) {
        var d = r.nextElementSibling;
        if (d && d.classList.contains("detail-row") && !d.classList.contains("hidden")) {
            d.classList.add("visible");
            r.classList.add("expanded");
        }
    });
}
function collapseAll() {
    document.querySelectorAll(".detail-row.visible").forEach(function(d) {
        d.classList.remove("visible");
    });
    document.querySelectorAll(".main-row.expanded").forEach(function(r) {
        r.classList.remove("expanded");
    });
}

/* ── More-filters disclosure ─────────────────────────── */
function toggleMore() {
    var more = document.getElementById("more-filters");
    var btn = document.getElementById("toggle-more-btn");
    if (!more) return;
    var hidden = more.hasAttribute("hidden");
    if (hidden) {
        more.removeAttribute("hidden");
        if (btn) btn.textContent = "▴ Hide more filters";
    } else {
        more.setAttribute("hidden", "");
        if (btn) btn.textContent = "▾ More filters";
    }
}

/* ── Recurring callout: show-all toggle + jump-to ────── */
function toggleRecurringShowAll(btn) {
    var panel = document.getElementById("recurring-panel");
    if (!panel) return;
    var on = panel.classList.toggle("show-all");
    btn.textContent = on ? "Show fewer" : btn.dataset.fullLabel;
}

function jumpToFinding(key) {
    /* Clearing all filters first ensures the target row is visible.
       (The row may be hidden by an active filter that excludes it.) */
    clearAllFilters();
    var row = document.querySelector('.main-row[data-key="' + key + '"]');
    if (!row) return;
    var detail = row.nextElementSibling;
    if (detail) {
        detail.classList.add("visible");
        row.classList.add("expanded");
    }
    row.scrollIntoView({behavior: "smooth", block: "center"});
    row.classList.remove("pulse");
    /* Force reflow so the animation re-runs even if pulse was already applied */
    void row.offsetWidth;
    row.classList.add("pulse");
}

/* ── Per-row collapse (back-to-row-top) ──────────────── */
function collapseRow(key) {
    var row = document.querySelector('.main-row[data-key="' + key + '"]');
    if (!row) return;
    var detail = row.nextElementSibling;
    if (detail) detail.classList.remove("visible");
    row.classList.remove("expanded");
    row.scrollIntoView({behavior: "smooth", block: "start"});
}

/* ── Clipboard + toast (for `claude --resume <UUID>`) ── */
function copyResume(el, evt) {
    evt.stopPropagation();
    var sid = el.dataset.sessionId || el.textContent.trim();
    var cmd = "claude --resume " + sid;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(cmd).then(function() { showToast("Copied: " + cmd); });
    } else {
        var ta = document.createElement("textarea");
        ta.value = cmd;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        showToast("Copied: " + cmd);
    }
}

function showToast(msg) {
    var toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function() { toast.classList.remove("show"); }, 2500);
}

/* ── Init ────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function() {
    initTheme();
    initFlags();
    applyFilters();
    // Hide download link on saved snapshots — the localhost route is
    // unreachable from a file:// page, so the button would just 404.
    if (window.location.protocol === "file:") {
        var dl = document.getElementById("download-html-btn");
        if (dl) dl.style.display = "none";
    }
});
"""


# ===========================================================================
# Per-finding row builders  -------------------------------------------------
# ===========================================================================

CROSS_CHECK_LABELS = {
    "cmr_covers_topic": "Aligns (covers topic)",
    "cmr_silent":       "Silent",
    "cmr_differs":      "Differs",
    "fns_requires":     "Aligns (requires it)",
    "fns_covers_topic": "Aligns (covers topic)",
    "fns_silent":       "Silent",
    "fns_differs":      "Differs",
    "cfr_covers_topic": "Aligns (covers topic)",
    "cfr_silent":       "Silent",
    "cfr_differs":      "Differs",
}

NCOLS = 7  # flag + analysis + disp + coverage + conf + issue + expand


def _render_olg_refs(refs: list) -> str:
    if not refs:
        return '<p class="muted">None</p>'
    html = ['<ul class="olg-refs">']
    for r in refs:
        url = _ref_url(r)
        label = _ref_label(r) or url or "(unparsed)"
        if url:
            html.append(
                f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a></li>'
            )
        else:
            html.append(f'<li>{esc(label)}</li>')
    html.append("</ul>")
    return "".join(html)


def _render_cross_check(source: str, block: dict | None) -> str:
    if not block:
        return ""
    cls = block.get("classification", "")
    bucket = _bucket(cls) or "silent"
    label = CROSS_CHECK_LABELS.get(cls, cls or "(no classification)")
    secs_key = f"{source}_sections"
    secs = block.get(secs_key, [])
    if isinstance(secs, list):
        secs_text = " · ".join(str(s) for s in secs)
    else:
        secs_text = str(secs or "")
    note = block.get("note", "")

    parts = [
        f'<div class="crosscheck-block {bucket}">',
        '<div class="crosscheck-head">',
        f'<span class="src">{source.upper()}</span>',
        f'<span class="cls">{esc(label)}</span>',
        '</div>',
    ]
    if secs_text:
        parts.append(f'<div class="secs">{esc(secs_text)}</div>')
    if note:
        parts.append(f'<div class="note">{esc(note)}</div>')
    parts.append("</div>")
    return "".join(parts)


def _render_judge_trace(trace: list) -> str:
    if not trace:
        return ""
    parts = ['<details class="judge-trace">']
    n_turns = len(trace)
    n_searches = sum(
        len([c for c in (t.get("tool_calls") or []) if c.get("query")])
        for t in trace
    )
    parts.append(
        f'<summary>Judge trace — {n_turns} turn{"s" if n_turns != 1 else ""}, '
        f'{n_searches} search{"es" if n_searches != 1 else ""}</summary>'
    )
    for t in trace:
        turn_num = t.get("turn", "?")
        stop = t.get("stop_reason", "?")
        tokens = t.get("tokens", {}) or {}
        tin = tokens.get("input", 0)
        tout = tokens.get("output", 0)
        parts.append('<div class="trace-turn">')
        parts.append(
            f'<div class="trace-head">turn {turn_num} · {esc(stop)} '
            f'· tokens: in {tin} / out {tout}</div>'
        )
        reasoning = (t.get("reasoning") or "").strip()
        if reasoning:
            parts.append(f"<p>{esc(reasoning)}</p>")
        for tc in t.get("tool_calls") or []:
            q = tc.get("query", "")
            sn = tc.get("search_number", "?")
            if q:
                parts.append(
                    f'<div class="tool-call">→ search #{esc(str(sn))}: {esc(q)}</div>'
                )
            elif tc.get("budget_exhausted"):
                parts.append('<div class="tool-call">→ (budget exhausted)</div>')
        parts.append("</div>")
    parts.append("</details>")
    return "".join(parts)


def _render_finding_row(entry: dict, recurring_ids: set[tuple]) -> str:
    """Return main-row + detail-row HTML for one finding."""
    key = entry["ns_detail_id"]
    coverage = entry.get("coverage", "Unknown")
    confidence = entry.get("confidence", "?")
    cmr_blk = entry.get("_cmr_check") or {}
    fns_blk = entry.get("_fns_check") or {}
    cfr_blk = entry.get("_cfr_check") or {}
    cmr_bucket = _bucket(cmr_blk.get("classification", ""))
    fns_bucket = _bucket(fns_blk.get("classification", ""))
    cfr_bucket = _bucket(cfr_blk.get("classification", ""))

    programs = sorted(_programs_for_finding(entry))

    is_recurring = _is_recurring(entry, recurring_ids)
    policy = entry.get("policy_issues", "") or ""
    gap_desc = entry.get("gap_description", "") or ""
    reasoning = entry.get("reasoning", "") or ""

    # Search text — what the search box matches against. Joined into a
    # single attribute so the JS can do a substring check without any
    # parsing. Keep the corpus tight (policy, gap, reasoning, page titles)
    # so a one-word search isn't drowned out by judge-trace noise.
    search_corpus_parts = [
        policy, gap_desc, reasoning,
        " ".join(_ref_label(r) for r in entry.get("olg_references", []) or []),
        cmr_blk.get("note", "") or "",
        fns_blk.get("note", "") or "",
        cfr_blk.get("note", "") or "",
    ]
    search_corpus = " ".join(p for p in search_corpus_parts if p)

    # Trim policy issue for table display — full text in the detail row.
    issue_short = policy.strip()
    if len(issue_short) > 140:
        cut = issue_short[:140].rsplit(" ", 1)[0]
        issue_short = cut + "…"

    cov_fg, cov_bg = COVERAGE_STYLES.get(coverage, ("#374151", "#f3f4f6"))
    conf_color = CONFIDENCE_COLORS.get(confidence, "#6b7280")

    sort_disp = (entry.get("row_index") or 0) * 1000 + (entry.get("finding_index") or 1)

    data_attrs = (
        f'data-key="{esc(key)}" '
        f'data-scope="{esc(entry.get("analysis_label", ""))}" '
        f'data-analysis="{esc(entry.get("analysis_name", ""))}" '
        f'data-coverage="{esc(coverage)}" '
        f'data-confidence="{esc(confidence)}" '
        f'data-cmr-bucket="{esc(cmr_bucket)}" '
        f'data-fns-bucket="{esc(fns_bucket)}" '
        f'data-cfr-bucket="{esc(cfr_bucket)}" '
        f'data-recurring="{"true" if is_recurring else "false"}" '
        f'data-flag="no" '
        f'data-programs="{esc("|".join(programs))}" '
        f'data-sort-disp="{sort_disp}" '
        f'data-search="{esc(search_corpus)}"'
    )

    # ── Main row ──
    parts = [
        f'<tr class="main-row" {data_attrs} onclick="toggleRow(\'{esc(key)}\')">',
        '<td class="col-flag">'
        f'<button class="flag-btn" onclick="toggleFlag(this,event)" title="Flag this finding">⚑</button>'
        '</td>',
        f'<td class="col-analysis">{esc(entry.get("analysis_label", ""))}</td>',
        f'<td class="col-disp">{esc(entry.get("display_index", ""))}</td>',
        f'<td class="col-cov">'
        f'<span class="badge" style="color:{cov_fg};background:{cov_bg}">{esc(coverage)}</span>'
        f'</td>',
        f'<td class="col-conf" style="color:{conf_color};font-weight:600">{esc(confidence)}</td>',
        f'<td class="col-issue">{esc(issue_short)}</td>',
        '<td class="col-expand"><span class="expand-icon">+</span></td>',
        '</tr>',
    ]

    # ── Detail row ──
    parts.extend([
        f'<tr class="detail-row" {data_attrs}>',
        f'<td colspan="{NCOLS}">',
        '<div class="detail-panel">',
    ])

    # Case identity strip
    review_no = entry.get("review_number", "")
    tao = entry.get("tao", "")
    determination = entry.get("determination", "")
    error_type = entry.get("error_type", "")
    case_meta_parts = []
    if review_no:
        case_meta_parts.append(("Review #", review_no))
    if tao:
        case_meta_parts.append(("TAO", tao))
    if determination:
        case_meta_parts.append(("Determination", determination))
    if error_type:
        case_meta_parts.append(("Error type", error_type))
    if case_meta_parts:
        parts.append('<dl class="case-meta">')
        for lbl, val in case_meta_parts:
            parts.append(
                f'<div><dt>{esc(lbl)}</dt><dd>{esc(str(val))}</dd></div>'
            )
        parts.append('</dl>')

    if policy:
        parts.append('<div class="detail-section"><h4>Policy issue</h4>'
                     f'<p>{esc(policy)}</p></div>')
    if gap_desc:
        parts.append('<div class="detail-section"><h4>Gap description</h4>'
                     f'<p>{esc(gap_desc)}</p></div>')
    if reasoning:
        parts.append('<div class="detail-section"><h4>Reasoning</h4>'
                     f'<p>{esc(reasoning)}</p></div>')

    parts.append('<div class="detail-section"><h4>OLG references cited</h4>')
    parts.append(_render_olg_refs(entry.get("olg_references", []) or []))
    parts.append('</div>')

    # Cross-checks (stacked vertically). Only render the section when at
    # least one source has a result — Adequate findings typically don't
    # carry cross-checks (the analyzer skips them).
    if cmr_blk or fns_blk or cfr_blk:
        parts.append('<div class="detail-section"><h4>Cross-checks</h4>')
        parts.append('<div class="crosscheck-stack">')
        parts.append(_render_cross_check("cmr", cmr_blk))
        parts.append(_render_cross_check("fns", fns_blk))
        parts.append(_render_cross_check("cfr", cfr_blk))
        parts.append('</div></div>')

    parts.append(_render_judge_trace(entry.get("judge_trace") or []))

    # Session-ID resume chip — only rendered when the finding actually
    # carries a Claude Code session (judge_claude_code path). The
    # API-only judge path doesn't capture a session, so the chip stays
    # hidden for those findings.
    sid = entry.get("_session_id") or ""
    if sid:
        parts.append(
            '<div class="session-id-row">'
            'Session: '
            f'<code class="session-id" data-session-id="{esc(sid)}" '
            f'onclick="copyResume(this,event)" '
            f'title="Click to copy: claude --resume {esc(sid)}">'
            f'{esc(sid)}</code>'
            '</div>'
        )

    # Per-row collapse footer — closes the detail and scrolls back to the
    # row header. Targeted fix for long judge traces (otherwise the user
    # has to scroll up by hand to find the close affordance).
    parts.append(
        '<div class="detail-footer">'
        f'<button class="btn-collapse" onclick="collapseRow(\'{esc(key)}\')" '
        f'title="Close this finding and scroll back to its row">'
        '▴ Collapse'
        '</button>'
        '</div>'
    )

    parts.extend(['</div>', '</td>', '</tr>'])
    return "".join(parts)


# ===========================================================================
# Filter-pill builders
# ===========================================================================

def _pill_button(dim: str, value: str, label: str, count: int | None = None,
                 is_default: bool = False) -> str:
    cls = "filter-btn"
    if is_default:
        cls += " active"
    label_html = esc(label)
    if count is not None:
        label_html += f' <span style="opacity:0.7">({count})</span>'
    return (
        f'<button class="{cls}" data-dim="{esc(dim)}" data-value="{esc(value)}" '
        f'onclick="setFilter(\'{esc(dim)}\', \'{esc(value)}\')">{label_html}</button>'
    )


def _all_pill(dim: str, total: int) -> str:
    return (
        f'<button class="filter-btn active" data-dim="{esc(dim)}" data-value="" '
        f'onclick="setFilter(\'{esc(dim)}\', \'\')">All ({total})</button>'
    )


def _filter_row(label: str, pills_html: str) -> str:
    return (
        '<div class="filter-row">'
        f'<span class="filter-label">{esc(label)}</span>'
        f'{pills_html}'
        '</div>'
    )


# ===========================================================================
# Recurring callout
# ===========================================================================

# Show this many recurring URLs by default; the rest hide behind "Show all".
RECURRING_INITIAL = 8


def _render_agent_notes_panel(flat: list[dict]) -> str:
    """Render the agent-notes aggregation panel, default-collapsed.

    Pulls every finding with a non-empty `agent_notes` string and lists
    them with row/finding identifier. Empty list → empty string (no
    panel). Mirrors the live UI panel; closed by default since these
    are introspective notes, not gating signal.
    """
    notes = [f for f in flat if (f.get("agent_notes") or "").strip()]
    if not notes:
        return ""

    parts = [
        '<details class="recurring-panel agent-notes-panel" id="agent-notes-panel">',
        '<summary>',
        '<span>Agent notes</span>',
        f'<span class="badge-count">{len(notes)} finding'
        f'{"s" if len(notes) != 1 else ""}</span>',
        '</summary>',
        '<p class="agent-notes-aux">Freeform commentary each judge agent '
        'left after investigating its finding — tool gaps, unfamiliar '
        'terminology, prompt ambiguities, suspected corpus holes. Same '
        'content lives in <code>agent_notes.md</code> in each analysis '
        'folder for copy-paste.</p>',
        '<ul class="agent-notes-list">',
    ]
    for entry in notes:
        disp = entry.get("display_index") or entry.get("ns_display_index") or "?"
        an = entry.get("analysis_name", "")
        ri = entry.get("row_index")
        fi = entry.get("finding_index")
        key = f"{_dom_safe(an)}_{ri}_{fi}" if an else ""
        coverage = entry.get("coverage", "")
        error_type = entry.get("error_type", "")
        meta_bits = " · ".join(b for b in (coverage, error_type) if b)
        link_opener = (
            f'<a class="finding-chip" href="#" '
            f'onclick="event.preventDefault();jumpToFinding(\'{esc(key)}\')" '
            f'title="Jump to this finding">{esc(str(disp))}</a>'
        ) if key else f'<strong>Row {esc(str(disp))}</strong>'
        parts.append(
            f'<li>{link_opener}'
            f'{" · " + esc(meta_bits) if meta_bits else ""}'
            f'<div class="agent-notes-body">{esc(entry["agent_notes"].strip())}</div>'
            f'</li>'
        )
    parts.append('</ul>')
    parts.append('</details>')
    return "".join(parts)


def _render_recurring_panel(recurring: list[dict]) -> str:
    if not recurring:
        return ""

    parts = [
        '<details class="recurring-panel" id="recurring-panel">',
        '<summary>',
        '<span>Recurring across batches</span>',
        f'<span class="badge-count">{len(recurring)} URL'
        f'{"s" if len(recurring) != 1 else ""}</span>',
        '</summary>',
        '<ul>',
    ]
    full_label = f"Show all ({len(recurring) - RECURRING_INITIAL} more)"
    for i, gap in enumerate(recurring):
        is_overflow = i >= RECURRING_INITIAL
        cls = "hidden-row" if is_overflow else ""
        chips = []
        for f in gap.get("findings", []):
            disp = f.get("display_index", "")
            an = f.get("analysis_name", "")
            ri = f.get("row_index")
            fi = f.get("finding_index")
            key = f"{_dom_safe(an)}_{ri}_{fi}"
            chips.append(
                f'<a class="finding-chip" '
                f'onclick="event.preventDefault();jumpToFinding(\'{esc(key)}\')" '
                f'href="#" title="Jump to this finding">{esc(disp or "?")}</a>'
            )
        parts.append(
            f'<li class="{cls}">'
            f'<a class="page-link" href="{esc(gap.get("url", ""))}" '
            f'target="_blank" rel="noopener">{esc(gap.get("page_title") or "(no title)")}</a>'
            f'<span class="row-count">{gap.get("row_count")} (analysis,row) · '
            f'{len(gap.get("findings", []))} findings</span>'
            f'<span class="chips">{"".join(chips)}</span>'
            f'</li>'
        )
    parts.append('</ul>')
    if len(recurring) > RECURRING_INITIAL:
        parts.append(
            f'<button class="show-more" data-full-label="{esc(full_label)}" '
            f'onclick="toggleRecurringShowAll(this)">{esc(full_label)}</button>'
        )
    parts.append('</details>')
    return "".join(parts)


# ===========================================================================
# generate_html
# ===========================================================================

def generate_html(analyses: list[dict],
                  selected: list[str] | None = None,
                  embed_assets: bool = True) -> str:
    """Render the full QC HTML report.

    Args:
        analyses: List of analysis dicts (from load_analyses).
        selected: When non-None, becomes the initial value of the
                  `scope` filter — the report still loads ALL analyses,
                  but the filter pills start with `selected` selected
                  so the user lands on a pre-filtered view.
        embed_assets: Forward-looking knob; CSS+JS are always inlined
                      to keep the file self-contained for emailing.
    """
    flat = namespace_findings(analyses)
    stats = compute_stats(flat)
    recurring = compute_recurring_across(flat)
    recurring_ids = _recurring_finding_ids(recurring)

    # Pre-flag findings so the filter dataset reflects current state
    # without waiting for client-side init.
    for entry in flat:
        entry["_is_recurring"] = _is_recurring(entry, recurring_ids)

    initial_scope = ""
    if selected and len(selected) == 1:
        initial_scope = _label_for(selected[0])

    h = []
    h.append("<!DOCTYPE html>")
    h.append('<html lang="en">')
    h.append("<head>")
    h.append('<meta charset="UTF-8">')
    h.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h.append("<title>QC Coverage Report</title>")
    h.append(f"<style>{CSS}</style>")
    h.append("</head>")
    h.append("<body>")

    # ── Header ──
    h.append("<header>")
    h.append('<div>')
    h.append('<h1>QC Coverage Report</h1>')
    n_an = len(analyses)
    h.append(
        f'<p class="subtitle">{stats["total"]} findings across '
        f'{n_an} analysis{"es" if n_an != 1 else ""} · '
        f'Generated {datetime.now().strftime("%B %d, %Y")}</p>'
    )
    h.append('</div>')
    h.append('<div class="header-actions">')
    # JS-driven href so the download URL inherits whatever ?selected /
    # ?names brought the user to this view. Hidden on file:// since a
    # saved snapshot can't call back to the localhost route.
    h.append('<a class="header-action" id="download-html-btn" '
             'href="/qc/report/download" '
             'onclick="this.href=\'/qc/report/download\'+window.location.search">'
             '⬇ Download .html</a>')
    h.append('<button class="theme-toggle" id="theme-btn" onclick="toggleTheme()">'
             '☾ Dark mode</button>')
    h.append('</div>')
    h.append("</header>")

    # ── Stats cards ──
    h.append('<section class="summary">')
    h.append(f'<div class="card total"><div class="card-num">{stats["total"]}</div>'
             '<div class="card-label">Total</div></div>')
    for cov in ["Adequate", "Partial", "Gap", "Error", "Skipped"]:
        n = stats["by_coverage"].get(cov, 0)
        if n == 0 and cov in ("Error", "Skipped"):
            continue
        fg, bg = COVERAGE_STYLES[cov]
        h.append(
            f'<div class="card" style="border-top-color:{fg}">'
            f'<div class="card-num" style="color:{fg}">{n}</div>'
            f'<div class="card-label">{cov}</div></div>'
        )
    h.append("</section>")

    # ── Recurring panel ──
    h.append(_render_recurring_panel(recurring))

    # ── Agent notes panel ──
    h.append(_render_agent_notes_panel(flat))

    # ── Filters ──
    h.append('<section class="filters">')
    h.append('<div class="active-chips" id="active-chips"></div>')

    h.append('<div class="search-row">')
    h.append('<input type="text" id="search-input" placeholder="Search policy / gap / reasoning…" '
             'oninput="onSearchInput(this)">')
    h.append('<button class="toggle-more" id="toggle-more-btn" onclick="toggleMore()">'
             '▾ More filters</button>')
    h.append('</div>')

    # Primary filter rows: scope + coverage
    h.append('<div class="filter-rows">')

    # Scope
    scope_pills = [_all_pill("scope", stats["total"])]
    for label, count in sorted(stats["by_analysis"].items()):
        scope_pills.append(_pill_button("scope", label, label, count))
    h.append(_filter_row("Scope", "".join(scope_pills)))

    # Coverage
    cov_pills = [_all_pill("coverage", stats["total"])]
    for cov in ["Adequate", "Partial", "Gap", "Error", "Skipped"]:
        n = stats["by_coverage"].get(cov, 0)
        if n == 0 and cov in ("Error", "Skipped"):
            continue
        cov_pills.append(_pill_button("coverage", cov, cov, n))
    h.append(_filter_row("Coverage", "".join(cov_pills)))

    # Program (only show if more than one program is present)
    program_counts = stats["by_program"]
    if len(program_counts) > 1:
        prog_pills = [_all_pill("program", stats["total"])]
        for prog, count in program_counts.most_common():
            prog_pills.append(_pill_button("program", prog, prog, count))
        h.append(_filter_row("Program", "".join(prog_pills)))

    h.append('</div>')

    # Disclosure ("More filters") — hidden by default
    h.append('<div class="filter-rows" id="more-filters" hidden style="margin-top:0.625rem">')

    # CMR / FNS / CFR alignment buckets
    bucket_labels = [("aligns", "Aligns"), ("silent", "Silent"), ("differs", "Differs")]
    for src in ("cmr", "fns", "cfr"):
        src_counts = Counter()
        for cls, n in stats["cross_check_classes"][src].items():
            b = _bucket(cls)
            if b:
                src_counts[b] += n
        if not any(src_counts.values()):
            continue
        pills = [_all_pill(src, sum(src_counts.values()))]
        for bkey, blabel in bucket_labels:
            pills.append(_pill_button(src, bkey, blabel, src_counts.get(bkey, 0)))
        h.append(_filter_row(src.upper(), "".join(pills)))

    # Confidence
    conf_counts = stats["by_confidence"]
    if conf_counts:
        pills = [_all_pill("confidence", stats["total"])]
        for clvl in ["HIGH", "MEDIUM", "LOW"]:
            n = conf_counts.get(clvl, 0)
            if n == 0:
                continue
            pills.append(_pill_button("confidence", clvl, clvl, n))
        h.append(_filter_row("Confidence", "".join(pills)))

    # Recurring
    if recurring:
        rec_yes = sum(1 for e in flat if e["_is_recurring"])
        rec_no = len(flat) - rec_yes
        pills = [
            _all_pill("recurring", stats["total"]),
            _pill_button("recurring", "yes", "Yes", rec_yes),
            _pill_button("recurring", "no", "No", rec_no),
        ]
        h.append(_filter_row("Recurring", "".join(pills)))

    # Flag (counts populated client-side)
    pills = [
        _all_pill("flag", stats["total"]),
        _pill_button("flag", "yes", "Flagged"),
        _pill_button("flag", "no", "Unflagged"),
    ]
    h.append(_filter_row("Flag", "".join(pills)))

    h.append('</div>')  # /more-filters
    h.append('</section>')  # /filters

    # ── Toolbar ──
    h.append('<div class="toolbar">')
    h.append(f'<span id="row-count">Showing all {stats["total"]} findings</span>')
    h.append('<button class="toolbar-btn" onclick="expandAll()">Expand visible</button>')
    h.append('<button class="toolbar-btn" onclick="collapseAll()">Collapse all</button>')
    h.append('</div>')

    # ── Findings table ──
    if not flat:
        h.append('<div class="empty-state">No findings to display.</div>')
    else:
        h.append('<table>')
        h.append('<thead><tr>')
        h.append('<th class="col-flag"></th>')
        h.append('<th class="col-analysis">Analysis</th>')
        h.append('<th class="col-disp sortable" onclick="sortByDisp(this)" data-sort-dir="asc" title="Click to sort by row number">#&nbsp;<span class="sort-arrow">▲</span></th>')
        h.append('<th class="col-cov">Coverage</th>')
        h.append('<th class="col-conf">Conf</th>')
        h.append('<th class="col-issue">Policy issue</th>')
        h.append('<th class="col-expand"></th>')
        h.append('</tr></thead><tbody>')
        for entry in flat:
            h.append(_render_finding_row(entry, recurring_ids))
        h.append('</tbody></table>')
        h.append(
            '<div id="empty-state" class="empty-state" style="display:none">'
            'No findings match the active filters.</div>'
        )

    # ── Footer ──
    h.append('<footer>')
    h.append('<h3>About this report</h3>')
    h.append(
        '<p>Generated from completed QC analyses. Each finding represents one '
        'abstract policy issue extracted from a QC reviewer\'s narrative, '
        'with an OLG-coverage verdict (Adequate / Partial / Gap) plus '
        'cross-checks against 106 CMR, FNS Handbook 310, and 7 CFR.</p>'
    )
    h.append('<ul>')
    h.append('<li><strong>Recurring across batches</strong> — OLG pages cited '
             'as gap evidence in Partial findings from ≥2 distinct '
             '(analysis, row) pairs. Cross-batch repetition is a stronger '
             'systemic signal than within-row repetition.</li>')
    h.append('<li><strong>Flag</strong> — local-only marking saved in your '
             'browser (localStorage). Useful for queueing items for review; '
             'flags do not persist across machines.</li>')
    h.append('<li><strong>Cross-check buckets</strong>: '
             '<em>Aligns</em> means the source covers the same topic; '
             '<em>Silent</em> means the source doesn\'t address it; '
             '<em>Differs</em> means the source takes a different position.</li>')
    h.append('</ul>')
    h.append('</footer>')

    # Toast container for clipboard feedback
    h.append('<div class="toast" id="toast"></div>')

    # ── Init script ──
    h.append('<script>')
    h.append(JS)
    h.append('</script>')

    # Apply selected scope after JS loads (overrides default "All").
    if initial_scope:
        h.append('<script>')
        h.append(
            f'document.addEventListener("DOMContentLoaded", function() {{'
            f'  FILTER_STATE.scope = {json.dumps(initial_scope)};'
            f'  applyFilters();'
            f'}});'
        )
        h.append('</script>')

    h.append("</body>")
    h.append("</html>")
    return "\n".join(h)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML report for QC analyses"
    )
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output HTML file path")
    parser.add_argument("--open", action="store_true",
                        help="Open report in default browser after generation")
    parser.add_argument("--names", type=str, default=None,
                        help="Comma-separated analysis names; defaults to all")
    parser.add_argument("--selected", type=str, default=None,
                        help="Single analysis name to pre-select as scope")
    args = parser.parse_args()

    names = None
    if args.names:
        names = [n.strip() for n in args.names.split(",") if n.strip()]
    selected = [args.selected] if args.selected else None

    analyses = load_analyses(names)
    if not analyses:
        print("No QC analyses found under", ANALYSIS_DIR)
        return

    html = generate_html(analyses, selected=selected)

    if args.output:
        out_path = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out_path = ANALYSIS_DIR / f"report_{ts}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    flat = namespace_findings(analyses)
    print(f"Report generated: {out_path}")
    print(f"  {len(analyses)} analysis(es), {len(flat)} findings")
    if args.open:
        webbrowser.open(str(out_path.resolve()))


if __name__ == "__main__":
    main()
