"""
QC Gap Analyzer — phased pipeline for assessing OLG coverage of QC errors.

Driven by the FastAPI UI (ui/app.py); no CLI entry point. Each analysis
lives in its own directory under output/qc_analysis/{name}_{timestamp}/
with one JSON per finding plus a meta.json.

Phases (UI buttons):
  1. extract — Haiku distills each QC finding into a policy issue +
     seed search queries. Cheap; covers all rows.
  2. investigate — Sonnet judges whether the OLG covers the policy issue.
     Runs a seed OLG search from the extractor's queries, then an
     agentic loop with iterative search_olg calls. Per-row; output
     includes a judge_trace array of per-turn reasoning + tool calls.
  3. cmr_check / fns_check / cfr_check — Haiku cross-checks each
     Partial/Gap finding against the relevant regulation source. These
     three are independent and can run in any order (or be skipped).

Per-source program filters are read from [qc_analyzer] in config.ini
({source}_include / {source}_exclude). The active filter is captured
into each analysis's meta.json as filter_snapshot at upload time.

Output shape:
  results/row_NNN.json — one per finding; carries phase, extracted policy
                         issue, judge result + trace, and per-source
                         _check blocks.
  meta.json           — name, timestamps, phase flags, cost per stage,
                         filter_snapshot.
  summary.csv         — flattened view, refreshed at the tail of each
                         phase (investigate / cross-checks) plus on
                         download. Always reflects the latest results.
"""

import configparser
import csv
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rag.query import (
    create_client,
    fetch_chunk_neighbors,
    fetch_page_chunks,
    search_with_client,
)
from tools.cost_tracker import Tracker
from tools.policy_tools import (
    FETCH_OLG_NEIGHBORS_TOOL,
    FETCH_OLG_PAGE_TOOL,
    SEARCH_OLG_TOOL,
)
from tools.result_formatters import format_results_for_prompt
from tools.retry import with_rate_limit_retry

# Soft cap on assembled page text returned by fetch_olg_page. Pages above
# this length are truncated with a continuation marker so a single page
# fetch can't blow out the judge's context window.
PAGE_FETCH_CHAR_CAP = 6000


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config.ini"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "output" / "qc_analysis"
ANALYSIS_DIR = OUTPUT_DIR  # alias for UI imports


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_prompt(name: str, with_preamble: bool = False) -> str:
    filepath = PROMPTS_DIR / f"{name}.md"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if with_preamble:
        preamble_path = PROJECT_ROOT / "prompts" / "domain_preamble.md"
        if preamble_path.exists():
            with open(preamble_path, "r", encoding="utf-8") as f:
                preamble = f.read()
            content = preamble + "\n\n---\n\n" + content
    return content


FILTER_SOURCES = ("olg", "cmr", "fns", "cfr")


def _load_filters(config: configparser.ConfigParser) -> dict:
    """Read per-source program filter lists from [qc_analyzer]. Returns
    {source: {"include": [...], "exclude": [...]}}. Both lists are
    informational; the include list is the active whitelist."""
    filters = {}
    for src in FILTER_SOURCES:
        include_raw = config.get("qc_analyzer", f"{src}_include", fallback="")
        exclude_raw = config.get("qc_analyzer", f"{src}_exclude", fallback="")
        filters[src] = {
            "include": [p.strip() for p in include_raw.split(",") if p.strip()],
            "exclude": [p.strip() for p in exclude_raw.split(",") if p.strip()],
        }
    return filters


# ============================================================
# UTILITIES
# ============================================================

def extract_json(text: str, fallback: dict | None = None) -> dict:
    """Extract a JSON object from a response that may contain surrounding
    prose or markdown. Tries fenced-code, raw, and inline-object patterns.
    On parse failure returns a copy of `fallback` (or {} if no fallback).
    Callers handle missing keys via .get() defaults — no implicit shape."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if text.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", text)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return dict(fallback) if fallback is not None else {}


# ============================================================
# CSV I/O
# ============================================================

def load_csv(filepath: Path) -> tuple[list[str], list[dict]]:
    """Load QC report CSV. Returns (fieldnames, rows_as_dicts).
    Tries UTF-8 (with BOM), falls back to cp1252 for Windows-exported CSVs."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(filepath, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames)
                rows = list(reader)
            return fieldnames, rows
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {filepath.name} as UTF-8 or CP1252")


# ============================================================
# PER-ANALYSIS DIRECTORY MANAGEMENT
# ============================================================

def get_analysis_dir(name: str) -> Path:
    """Return (and create) the directory for a named analysis."""
    d = ANALYSIS_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "results").mkdir(exist_ok=True)
    return d


_TS_SUFFIX_RE = re.compile(r"_\d{4}-\d{2}-\d{2}_\d{4}$")


def make_forked_name(old_name: str) -> str:
    """Build a fresh timestamped name for a forked analysis.

    Strips an existing `_YYYY-MM-DD_HHMM` suffix off the source name and
    appends one based on the current minute. If a folder already exists
    at that path (rare, same-minute collision), bumps a counter suffix.
    """
    base = _TS_SUFFIX_RE.sub("", old_name)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    candidate = f"{base}_{ts}"
    counter = 2
    while (ANALYSIS_DIR / candidate).exists():
        candidate = f"{base}_{ts}_{counter}"
        counter += 1
    return candidate


_DOWNSTREAM_PHASES = ("investigated", "cmr_checked", "fns_checked", "cfr_checked")
_DOWNSTREAM_STAGES = ("judge", "cmr_check", "fns_check", "cfr_check")
_DOWNSTREAM_STAT_KEYS = (
    "investigate_stats", "cmr_check_stats", "fns_check_stats", "cfr_check_stats",
)


def downstream_summary(analysis_dir: Path) -> dict:
    """Summarize what re-extracting in place would wipe.

    Returns a dict with `populated: bool` and per-phase counts of findings
    that would lose data. Counts are at finding granularity since the new
    schema nests results inside `row["findings"][i]`.
    """
    rows = load_all_findings(analysis_dir)
    investigated = 0
    cmr = 0
    fns = 0
    cfr = 0
    for row in rows:
        for f in row.get("findings", []):
            if f.get("coverage"):
                investigated += 1
            if "_cmr_check" in f:
                cmr += 1
            if "_fns_check" in f:
                fns += 1
            if "_cfr_check" in f:
                cfr += 1
    return {
        "populated": any((investigated, cmr, fns, cfr)),
        "investigated": investigated,
        "cmr": cmr,
        "fns": fns,
        "cfr": cfr,
    }


def clear_downstream_meta(analysis_dir: Path) -> None:
    """Strip downstream-phase flags, costs, and stat blocks from meta.json.

    Called before an in-place re-extract so the analysis returns to an
    extract-only state. The actual judge/cross-check data lives nested
    inside row findings; that wipes automatically when run_extract
    rewrites the findings list.
    """
    meta = load_meta(analysis_dir)
    if not meta:
        return
    phases = meta.get("phases", {})
    for p in _DOWNSTREAM_PHASES:
        phases.pop(p, None)
    costs = meta.get("cost", {})
    for c in _DOWNSTREAM_STAGES:
        costs.pop(c, None)
    for k in _DOWNSTREAM_STAT_KEYS:
        meta.pop(k, None)
    meta.pop("investigated_rows", None)
    save_meta(analysis_dir, meta)


def save_finding(analysis_dir: Path, row_index: int, data: dict) -> Path:
    """Write a per-finding JSON to results/row_NNN.json."""
    path = analysis_dir / "results" / f"row_{row_index:03d}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


_PER_FINDING_KEYS = (
    "policy_issues", "search_queries", "coverage", "confidence",
    "olg_references", "gap_description", "reasoning",
    "searches_performed", "all_search_queries", "judge_trace",
    "_cmr_check", "_fns_check", "_cfr_check",
)


def _migrate_legacy_row(row: dict) -> dict:
    """Wrap a legacy single-finding row into the multi-finding shape.

    Pre-2026-05-07 row JSONs stored policy_issues, search_queries, and
    judge/cross-check results at row level. New shape nests them inside
    `row["findings"][i]`. This migration runs on read so legacy data
    keeps loading; re-running any phase rewrites in the new shape.

    Also normalizes legacy "API error" stubs (coverage=Partial,
    confidence=LOW, gap_description starts with "Judge API error:")
    into the new coverage=Error / confidence=N/A shape so the UI
    doesn't show them as real Partial verdicts.
    """
    if "findings" not in row:
        finding = {"finding_index": 1}
        for k in _PER_FINDING_KEYS:
            if k in row:
                finding[k] = row.pop(k)
        if finding.get("policy_issues"):
            row["findings"] = [finding]
        else:
            row["findings"] = []
    for f in row.get("findings", []):
        gap = f.get("gap_description") or ""
        if (f.get("coverage") == "Partial"
                and f.get("confidence") == "LOW"
                and gap.startswith("Judge API error:")):
            f["coverage"] = "Error"
            f["confidence"] = "N/A"
            if not f.get("error"):
                f["error"] = gap[len("Judge API error: "):]
    return row


def load_finding(analysis_dir: Path, row_index: int) -> dict | None:
    """Read a single row JSON (with nested findings). Returns None if not found."""
    path = analysis_dir / "results" / f"row_{row_index:03d}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return _migrate_legacy_row(json.load(f))
    return None


def load_all_findings(analysis_dir: Path) -> list[dict]:
    """Read all row JSONs (with nested findings), sorted by row_index.

    Each entry is a row with `findings: [...]`. Use `flatten_findings`
    when a per-finding view is needed (UI tables, summary CSV).
    """
    results_dir = analysis_dir / "results"
    if not results_dir.exists():
        return []
    rows = []
    for path in sorted(results_dir.glob("row_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            rows.append(_migrate_legacy_row(json.load(f)))
    rows.sort(key=lambda r: r.get("row_index", 0))
    return rows


_ROW_LEVEL_KEYS = (
    "row_index", "review_number", "apid", "tao",
    "determination", "error_type", "finding_narrative",
    "non_concur_reason", "phase",
)


def flatten_findings(rows: list[dict]) -> list[dict]:
    """Flatten nested rows into one entry per (row, finding) for display.

    Each output entry merges row-level identity fields with the per-finding
    fields, plus `display_index` ("5" if row 5 has one finding,
    "5.1"/"5.2"/"5.3" if it has multiple). Rows with no findings produce
    no output entries.
    """
    out = []
    for row in rows:
        row_fields = {k: row.get(k, "") for k in _ROW_LEVEL_KEYS if k in row}
        findings = row.get("findings", [])
        multi = len(findings) > 1
        for f in findings:
            entry = {**row_fields, **f}
            entry["row_index"] = row.get("row_index")
            fi = f.get("finding_index", 1)
            entry["finding_index"] = fi
            entry["display_index"] = (
                f"{row.get('row_index')}.{fi}" if multi else str(row.get("row_index"))
            )
            entry["detail_id"] = f"{row.get('row_index')}_{fi}"
            out.append(entry)
    return out


_REF_URL_RE = re.compile(r"\((https?://[^)\s]+)\)\s*$")


def _parse_olg_ref(ref: str) -> tuple[str, str]:
    """Parse an olg_references entry into (page_title, url).

    Refs are stored as 'Page Title > Section Heading (https://...)'.
    Returns ('', '') if the format doesn't match.
    """
    m = _REF_URL_RE.search(ref)
    if not m:
        return ("", "")
    url = m.group(1)
    title_part = ref[:m.start()].strip()
    page_title = title_part.split(" > ")[0] if title_part else ""
    return page_title, url


def find_recurring_gaps(flat_findings: list[dict],
                        min_rows: int = 2) -> list[dict]:
    """Detect OLG pages cited as gap evidence across multiple ROWS.

    Heuristic: group Partial findings by the URLs in their olg_references.
    A URL is surfaced when it shows up in Partial findings from at least
    `min_rows` distinct rows — that's a *systemic* OLG hole rather than
    a per-row issue. Multiple findings within the same row often share
    citations naturally (different facets of the same case) so within-row
    repetition is not signal.

    Returns a list of {url, page_title, findings: [...]} dicts ordered by
    distinct row count (highest first), tie-broken by total finding count.
    `findings` entries carry display_index so the UI can link them.
    """
    by_url: dict[str, dict] = {}
    for entry in flat_findings:
        if entry.get("coverage") != "Partial":
            continue
        seen_urls_for_entry = set()
        for ref in entry.get("olg_references", []) or []:
            if not isinstance(ref, str):
                continue
            page_title, url = _parse_olg_ref(ref)
            if not url or url in seen_urls_for_entry:
                continue
            seen_urls_for_entry.add(url)
            grp = by_url.setdefault(url, {
                "url": url,
                "page_title": page_title,
                "findings": [],
                "rows": set(),
            })
            grp["findings"].append({
                "display_index": entry.get("display_index"),
                "row_index": entry.get("row_index"),
                "finding_index": entry.get("finding_index"),
            })
            grp["rows"].add(entry.get("row_index"))

    recurring = []
    for grp in by_url.values():
        if len(grp["rows"]) < min_rows:
            continue
        out = {
            "url": grp["url"],
            "page_title": grp["page_title"],
            "findings": grp["findings"],
            "row_count": len(grp["rows"]),
        }
        recurring.append(out)
    recurring.sort(key=lambda g: (-g["row_count"], -len(g["findings"]),
                                  g["page_title"]))
    return recurring


def save_meta(analysis_dir: Path, meta: dict) -> None:
    """Write meta.json for an analysis."""
    path = analysis_dir / "meta.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def load_meta(analysis_dir: Path) -> dict | None:
    """Read meta.json. Returns None if not found."""
    path = analysis_dir / "meta.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_agent_notes_md(analysis_dir: Path) -> Path | None:
    """Compile per-finding `agent_notes` into a single markdown file at
    the analysis root for easy copy-paste review.

    Notes live in each finding's row JSON (`findings[].agent_notes`) —
    that's the source of truth. This file is a deterministic byproduct,
    safe to regenerate any time from the row JSONs.

    Returns the written path, or None if no notes are present.
    """
    rows = load_all_findings(analysis_dir)
    if not rows:
        return None

    flat = flatten_findings(rows)
    notes_entries = [
        f for f in flat
        if (f.get("agent_notes") or "").strip()
    ]
    if not notes_entries:
        # If a previous run wrote a notes file but none survive now,
        # remove it so the artifact stays in sync with the row JSONs.
        existing = analysis_dir / "agent_notes.md"
        if existing.exists():
            existing.unlink()
        return None

    lines = [
        f"# Agent notes — {analysis_dir.name}",
        "",
        f"Compiled from {len(notes_entries)} finding(s) with non-empty notes. "
        "Each entry is the freeform commentary the judge agent left after "
        "investigating its finding.",
        "",
    ]
    for entry in notes_entries:
        display = entry.get("display_index", entry.get("row_index", ""))
        coverage = entry.get("coverage", "")
        error_type = entry.get("error_type", "")
        header = f"## Row {display}"
        meta_bits = []
        if coverage:
            meta_bits.append(coverage)
        if error_type:
            meta_bits.append(error_type)
        if meta_bits:
            header += f" ({', '.join(meta_bits)})"
        lines.append(header)
        lines.append("")
        lines.append(entry["agent_notes"].strip())
        lines.append("")

    path = analysis_dir / "agent_notes.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_summary_csv(analysis_dir: Path) -> Path:
    """Build a summary CSV — one row per (row, finding).

    Column order mirrors the HTML report: verdict + investigation
    detail up front, cross-checks next, engine metadata after, case
    identity at the far right. Cross-check columns are always emitted
    (empty when the phase didn't run) so CSVs from different runs are
    diff-comparable for engine A/B testing.
    """
    rows = load_all_findings(analysis_dir)
    if not rows:
        return None

    flat = flatten_findings(rows)
    if not flat:
        return None

    csv_path = analysis_dir / "summary.csv"

    summary_columns = [
        # Verdict
        "display_index", "coverage", "confidence",
        # Investigation detail
        "policy_issues", "reasoning", "gap_description",
        "olg_references", "searches_performed",
        # Cross-checks
        "cmr_classification", "cmr_sections", "cmr_note",
        "fns_classification", "fns_sections", "fns_note",
        "cfr_classification", "cfr_sections", "cfr_note",
        # Engine metadata (A/B columns)
        "engine", "session_id", "elapsed_sec", "error",
        # Case identity (far right)
        "row_index", "finding_index", "review_number", "apid", "tao",
        "determination", "error_type",
    ]

    def _join(value):
        if isinstance(value, list):
            return "; ".join(str(v) for v in value)
        return str(value) if value else ""

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=summary_columns,
                                extrasaction="ignore")
        writer.writeheader()
        for entry in flat:
            row = {k: entry.get(k, "") for k in summary_columns}
            row["olg_references"] = _join(entry.get("olg_references", []))

            cmr = entry.get("_cmr_check") or {}
            row["cmr_classification"] = cmr.get("classification", "")
            row["cmr_sections"] = _join(cmr.get("cmr_sections", []))
            row["cmr_note"] = cmr.get("note", "")

            fns = entry.get("_fns_check") or {}
            row["fns_classification"] = fns.get("classification", "")
            row["fns_sections"] = _join(fns.get("fns_sections", []))
            row["fns_note"] = fns.get("note", "")

            cfr = entry.get("_cfr_check") or {}
            row["cfr_classification"] = cfr.get("classification", "")
            row["cfr_sections"] = _join(cfr.get("cfr_sections", []))
            row["cfr_note"] = cfr.get("note", "")

            row["engine"] = entry.get("_engine", "")
            row["session_id"] = entry.get("_session_id", "")
            elapsed = entry.get("_elapsed")
            row["elapsed_sec"] = (
                f"{elapsed:.1f}" if isinstance(elapsed, (int, float)) else ""
            )

            writer.writerow(row)

    return csv_path


# ============================================================
# CALL 1: EXTRACTOR
# ============================================================

def build_extractor_input(row: dict) -> str:
    """Assemble the input for the Extractor from a QC CSV row."""
    parts = []

    findings = row.get("QC Findings", "").strip()
    if findings:
        parts.append(f"## QC Finding Narrative\n{findings}")

    determination = row.get("Food Stamp Determination", "").strip()
    error_type = row.get("Type Of Errors", "").strip()
    if determination:
        parts.append(f"Determination: {determination}")
    if error_type:
        parts.append(f"Error Type: {error_type}")

    qc_comments = row.get("QC Comments", "").strip()
    if qc_comments:
        parts.append(f"## QC Comments\n{qc_comments}")

    disagree = row.get("Disagree Specific Reason(s)", "").strip()
    if disagree:
        parts.append(f"## Disagree Reason\n{disagree}")

    non_concur = row.get("Non-Concur Reason", "").strip()
    if non_concur:
        parts.append(f"## Non-Concur Reason\n{non_concur}")

    return "\n\n".join(parts)


def _resolve_temperature(config: configparser.ConfigParser | None,
                          key: str, baseline: float | None) -> float | None:
    """Return the API temperature for a call site.

    Honors [debug] overrides only when [debug] debug_mode = true. When
    debug mode is off, missing, or the override is blank/invalid, the
    in-code `baseline` is returned. A baseline of None means "do not pass
    temperature to the API" (the call uses the Anthropic default, ~1.0).
    """
    if config is None or not config.has_section("debug"):
        return baseline
    if not config.getboolean("debug", "debug_mode", fallback=False):
        return baseline
    raw = config.get("debug", key, fallback="").strip()
    if not raw:
        return baseline
    try:
        return float(raw)
    except ValueError:
        return baseline


def run_extractor(user_message: str, client: anthropic.Anthropic,
                  model: str, system_prompt: str,
                  cost_tracker: Tracker | None = None,
                  temperature: float | None = 0.0) -> dict:
    """Call 1: Extract policy issues and search queries from a QC finding.

    Returns a dict with a `findings` list. Each finding has policy_issues
    and search_queries. Multi-finding extraction is supported — see
    qc_extractor.md for the split rule.
    """

    @with_rate_limit_retry()
    def _do_extractor_call():
        kwargs = {
            "model": model,
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        return client.messages.create(**kwargs)

    try:
        response = _do_extractor_call()
    except anthropic.APIError:
        return {
            "findings": [{
                "policy_issues": "Extraction failed due to API error.",
                "search_queries": [user_message[:200]],
            }],
        }

    if cost_tracker:
        cost_tracker.record("extractor", model, response.usage)
    text = response.content[0].text.strip()
    parsed = extract_json(text, fallback={"findings": []})

    # Backwards compat: handle legacy single-issue shape if a model
    # ignores the new schema and emits the old one. Wraps into a
    # 1-element findings list.
    if "findings" not in parsed and "policy_issues" in parsed:
        parsed = {"findings": [{
            "policy_issues": parsed.get("policy_issues", ""),
            "search_queries": parsed.get("search_queries", []),
        }]}
    return parsed


# ============================================================
# SEED SEARCH
# ============================================================

def run_seed_searches(queries: list[str], olg_clients: dict,
                      results_per_query: int = 5,
                      programs: list[str] | None = None) -> list[dict]:
    """Run extractor's queries against OLG and deduplicate results."""
    seen_ids = set()
    all_results = []

    for query in queries:
        if not query or not query.strip():
            continue
        response = search_with_client(
            query, olg_clients,
            collection="sections",
            programs=programs,
            top_n=results_per_query,
            threshold=0.0,
        )
        for result in response["results"]:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                all_results.append(result)

    all_results.sort(key=lambda r: r["score"], reverse=True)
    return all_results


# ============================================================
# CALL 2: JUDGE (AGENTIC)
# ============================================================
#
# CANONICAL JUDGE TRACE SCHEMA
# ----------------------------
# Every judge engine (API, Claude Code, future) MUST return a trace
# conforming to this shape so the audit walker, inspect_finding.py,
# recurring-gap heuristic, and UI rendering stay engine-agnostic.
#
# judge_trace: list[turn_entry]
#
# turn_entry = {
#     "turn":         int,           # 0 = seed (no LLM call); 1+ = LLM turns
#     "stop_reason":  str,            # "seed" | "tool_use" | "end_turn"
#                                     # | "max_tokens" | "budget_exhausted"
#     "tokens": {
#         "input":    int,            # 0 for the seed entry
#         "output":   int,
#     },
#     "reasoning":    str,            # The model's text reasoning for this
#                                     # turn (empty string for seed)
#     "tool_calls":   list[tool_call],
#     "tool_results": list[tool_result],
# }
#
# tool_call = {
#     "tool_name":        str,        # "search_olg" | "fetch_olg_neighbors"
#                                     # | "fetch_olg_page". Absent in
#                                     # pre-2026-05-11 traces (assume
#                                     # "search_olg").
#     "query":            str,        # search_olg only: the search query.
#     "chunk_id":         str,        # fetch_olg_neighbors only.
#     "n":                int,        # fetch_olg_neighbors only.
#     "direction":        str,        # fetch_olg_neighbors only.
#     "url":              str,        # fetch_olg_page only.
#     "search_number":    int,        # search_olg only; globally unique
#                                     # within this finding; 0 for seed.
#     "fetch_number":     int,        # fetch_olg_* only; per-tool counter.
#     "budget_exhausted": bool,       # Optional; True iff the budget guard
#                                     # rejected this call
# }
#
# tool_result = {
#     "tool_name":        str,        # Same values as in tool_call above.
#     "result_count":     int,
#     "results":          list[result_summary],   # Empty if budget exhausted
#     "page_text_chars":  int,        # fetch_olg_page only; length of the
#                                     # assembled page text before truncation
#     "truncated":        bool,       # fetch_olg_page only; whether the
#                                     # assembled text was soft-capped
#     "status":           str,        # Optional; e.g. "budget_exhausted"
# }
#
# result_summary = {
#     "id":               str,        # ChromaDB chunk id
#     "score":            float,
#     "page_title":       str,
#     "section_heading":  str,
#     "url":              str,
#     "text_preview":     str,         # Capped (~300 chars)
# }
#
# Engines that wrap a different toolset (e.g. Claude Code calling
# `python rag/query.py ... --json` via Bash) must translate their
# native event stream into this shape before persisting. Citations
# referenced by olg_references are validated against
# tool_results[*].results[*].url and result_summary.page_title.

def run_judge(row: dict, extractor_result: dict, seed_results: list[dict],
              olg_clients: dict, client: anthropic.Anthropic,
              model: str, system_prompt: str,
              max_searches: int = 10,
              max_neighbor_fetches: int = 8,
              max_page_fetches: int = 3,
              results_per_search: int = 5,
              cost_tracker: Tracker | None = None,
              olg_programs: list[str] | None = None,
              temperature: float | None = None) -> tuple[dict, list[dict]]:
    """Call 2: Agentic OLG coverage assessment with iterative search.

    Returns (result, judge_trace) — the final classification dict plus an
    array of per-turn entries (turn / stop_reason / tokens / reasoning /
    tool_calls / tool_results). The trace is appended to the per-finding
    JSON so prompt-tuning consumers can see how the judge reasoned.

    Three tools, with separate budgets:
      - search_olg: semantic search (scalpel for discovery)
      - fetch_olg_neighbors: ±N chunks around an anchor (scalpel for context)
      - fetch_olg_page: whole page (hacksaw, soft-capped at PAGE_FETCH_CHAR_CAP)
    """

    seed_formatted = format_results_for_prompt(seed_results, "olg")
    extractor_queries = extractor_result.get("search_queries", [])

    user_message = (
        f"## QC Finding\n\n"
        f"{row.get('QC Findings', '').strip()}\n\n"
        f"## Extracted Policy Issues\n\n"
        f"{extractor_result.get('policy_issues', 'Not available')}\n\n"
        f"## Initial OLG Search Results\n\n"
        f"The following results were found using {len(extractor_queries)} "
        f"automated search queries:\n\n"
        f"{seed_formatted}\n\n"
        f"## Your Tool Budgets\n\n"
        f"- search_olg: {max_searches} calls (discovery)\n"
        f"- fetch_olg_neighbors: {max_neighbor_fetches} calls "
        f"(stitch context around a specific chunk; cheap)\n"
        f"- fetch_olg_page: {max_page_fetches} calls (read a whole page; "
        f"reserve for when neighbors aren't enough)\n\n"
        f"Each tool has its own budget; using one does NOT consume "
        f"another's. Prefer the scalpel (search then neighbors) over the "
        f"hacksaw (full page). Review the seed results above before "
        f"deciding which tool to reach for first."
    )

    messages = [{"role": "user", "content": user_message}]

    searches_performed = 0
    neighbor_fetches_performed = 0
    page_fetches_performed = 0
    all_search_queries = list(extractor_queries)
    # Budget = max_searches tool-use turns + 1 final-reasoning turn + a
    # 4-turn buffer for cases where the model loops or re-plans before
    # settling on the final answer. Fetch tools may add additional turns
    # since they're separately budgeted; we add half of (neighbors + pages)
    # to the turn cap so the agent can interleave fetches with searches.
    max_turns = max_searches + 5 + (max_neighbor_fetches + max_page_fetches) // 2

    # Synthetic "turn 0" capturing the seed search so audits can verify
    # citations against the seed without re-running it. The seed is what
    # the judge reads in `## Initial OLG Search Results` of the user
    # message, but isn't otherwise stored anywhere queryable. Without
    # this, citations grounded in seed-only retrieval look "missing from
    # trace" to an offline auditor.
    judge_trace: list[dict] = [{
        "turn": 0,
        "stop_reason": "seed",
        "tokens": {"input": 0, "output": 0},
        "reasoning": "",
        "tool_calls": [{"query": q, "search_number": 0} for q in extractor_queries],
        "tool_results": [{
            "result_count": len(seed_results),
            "results": _summarize_search_results(seed_results),
        }],
    }]

    def _api_error_result(error: Exception) -> dict:
        return {
            "coverage": "Error",
            "olg_references": [],
            "gap_description": f"Judge API error: {error}",
            "confidence": "N/A",
            "reasoning": "Analysis incomplete due to API error.",
            "error": str(error),
            "searches_performed": searches_performed,
            "neighbor_fetches_performed": neighbor_fetches_performed,
            "page_fetches_performed": page_fetches_performed,
            "all_search_queries": all_search_queries,
            "agent_notes": "",
        }

    @with_rate_limit_retry()
    def _do_judge_call():
        kwargs = {
            "model": model,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": messages,
            "tools": [SEARCH_OLG_TOOL, FETCH_OLG_NEIGHBORS_TOOL, FETCH_OLG_PAGE_TOOL],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        return client.messages.create(**kwargs)

    for turn in range(max_turns):
        try:
            response = _do_judge_call()
        except anthropic.APIError as e:
            return _api_error_result(e), judge_trace

        if cost_tracker:
            cost_tracker.record("judge", model, response.usage)

        reasoning_text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text.strip():
                reasoning_text = block.text.strip()

        if response.stop_reason == "tool_use":
            tool_results = []
            trace_tool_calls = []
            trace_tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type != "tool_use":
                    continue

                if block.name == "search_olg":
                    query = block.input.get("query", "")

                    if searches_performed >= max_searches:
                        budget_msg = (
                            f"Search budget exhausted ({searches_performed} "
                            f"searches used). Please provide your final "
                            f"assessment now based on all results seen."
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": budget_msg,
                        })
                        trace_tool_calls.append({
                            "tool_name": "search_olg",
                            "query": query,
                            "budget_exhausted": True,
                        })
                        trace_tool_results.append({
                            "tool_name": "search_olg",
                            "status": "budget_exhausted",
                        })
                        continue

                    searches_performed += 1
                    all_search_queries.append(query)
                    print(f".", end="", flush=True)

                    search_response = search_with_client(
                        query, olg_clients,
                        collection="sections",
                        programs=olg_programs,
                        top_n=results_per_search,
                        threshold=0.0,
                    )

                    formatted = format_results_for_prompt(
                        search_response["results"], "olg"
                    )
                    remaining = max_searches - searches_performed
                    formatted += f"\n\n[{remaining} searches remaining]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": formatted,
                    })

                    trace_tool_calls.append({
                        "tool_name": "search_olg",
                        "query": query,
                        "search_number": searches_performed,
                    })
                    trace_tool_results.append({
                        "tool_name": "search_olg",
                        "result_count": len(search_response["results"]),
                        "results": _summarize_search_results(search_response["results"]),
                    })

                elif block.name == "fetch_olg_neighbors":
                    chunk_id = block.input.get("chunk_id", "")
                    n = block.input.get("n", 1)
                    direction = block.input.get("direction", "both")

                    if neighbor_fetches_performed >= max_neighbor_fetches:
                        budget_msg = (
                            f"Neighbor-fetch budget exhausted "
                            f"({neighbor_fetches_performed} fetches used). "
                            f"Use remaining searches or provide your final "
                            f"assessment."
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": budget_msg,
                        })
                        trace_tool_calls.append({
                            "tool_name": "fetch_olg_neighbors",
                            "chunk_id": chunk_id,
                            "n": n,
                            "direction": direction,
                            "budget_exhausted": True,
                        })
                        trace_tool_results.append({
                            "tool_name": "fetch_olg_neighbors",
                            "status": "budget_exhausted",
                        })
                        continue

                    neighbor_fetches_performed += 1
                    print(f"n", end="", flush=True)

                    try:
                        neighbors = fetch_chunk_neighbors(
                            chunk_id, olg_clients, n=n, direction=direction
                        )
                    except Exception as e:
                        neighbors = []
                        fetch_error = str(e)
                    else:
                        fetch_error = None

                    formatted = _format_neighbor_results(
                        neighbors, chunk_id, direction, fetch_error
                    )
                    remaining_n = max_neighbor_fetches - neighbor_fetches_performed
                    formatted += f"\n\n[{remaining_n} neighbor fetches remaining]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": formatted,
                    })
                    trace_tool_calls.append({
                        "tool_name": "fetch_olg_neighbors",
                        "chunk_id": chunk_id,
                        "n": n,
                        "direction": direction,
                        "fetch_number": neighbor_fetches_performed,
                    })
                    trace_tool_results.append({
                        "tool_name": "fetch_olg_neighbors",
                        "result_count": len(neighbors),
                        "results": _summarize_search_results(neighbors),
                    })

                elif block.name == "fetch_olg_page":
                    url = block.input.get("url", "")

                    if page_fetches_performed >= max_page_fetches:
                        budget_msg = (
                            f"Page-fetch budget exhausted "
                            f"({page_fetches_performed} pages used). "
                            f"Use neighbor fetches or provide your final "
                            f"assessment."
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": budget_msg,
                        })
                        trace_tool_calls.append({
                            "tool_name": "fetch_olg_page",
                            "url": url,
                            "budget_exhausted": True,
                        })
                        trace_tool_results.append({
                            "tool_name": "fetch_olg_page",
                            "status": "budget_exhausted",
                        })
                        continue

                    page_fetches_performed += 1
                    print(f"P", end="", flush=True)

                    try:
                        page_chunks = fetch_page_chunks(url, olg_clients)
                    except Exception as e:
                        page_chunks = []
                        fetch_error = str(e)
                    else:
                        fetch_error = None

                    formatted, full_chars, truncated = _format_page_result(
                        page_chunks, url, fetch_error
                    )
                    remaining_p = max_page_fetches - page_fetches_performed
                    formatted += f"\n\n[{remaining_p} page fetches remaining]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": formatted,
                    })
                    trace_tool_calls.append({
                        "tool_name": "fetch_olg_page",
                        "url": url,
                        "fetch_number": page_fetches_performed,
                    })
                    trace_tool_results.append({
                        "tool_name": "fetch_olg_page",
                        "result_count": len(page_chunks),
                        "page_text_chars": full_chars,
                        "truncated": truncated,
                        "results": _summarize_search_results(page_chunks),
                    })

            judge_trace.append({
                "turn": turn + 1,
                "stop_reason": "tool_use",
                "tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                "reasoning": reasoning_text,
                "tool_calls": trace_tool_calls,
                "tool_results": trace_tool_results,
            })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            continue

        judge_trace.append({
            "turn": turn + 1,
            "stop_reason": response.stop_reason,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
            "reasoning": reasoning_text,
            "tool_calls": [],
            "tool_results": [],
        })

        result = extract_json(reasoning_text, fallback={
            "coverage": "Partial",
            "confidence": "LOW",
            "reasoning": reasoning_text[:300],
        })
        result["searches_performed"] = searches_performed
        result["neighbor_fetches_performed"] = neighbor_fetches_performed
        result["page_fetches_performed"] = page_fetches_performed
        result["all_search_queries"] = all_search_queries
        result.setdefault("agent_notes", "")
        return result, judge_trace

    return {
        "coverage": "Partial",
        "olg_references": [],
        "gap_description": "Judge exhausted maximum turns without conclusion.",
        "confidence": "LOW",
        "reasoning": "Maximum conversation turns reached.",
        "error": "max_turns_exhausted",
        "searches_performed": searches_performed,
        "neighbor_fetches_performed": neighbor_fetches_performed,
        "page_fetches_performed": page_fetches_performed,
        "all_search_queries": all_search_queries,
        "agent_notes": "",
    }, judge_trace


def _format_neighbor_results(
    neighbors: list[dict],
    anchor_chunk_id: str,
    direction: str,
    error: str | None,
) -> str:
    """Format neighbor-fetch output for the judge prompt.

    Same shape as format_results_for_prompt's OLG branch — header line
    with chunk_id / page / section / chunk_n + text body — but introduced
    as neighbor matches rather than search matches.
    """
    if error:
        return f"fetch_olg_neighbors error for {anchor_chunk_id}: {error}"
    if not neighbors:
        return (
            f"No neighbors found for {anchor_chunk_id} (direction={direction}). "
            f"The anchor may be at the start/end of its page."
        )

    label_dir = {"prev": "before", "next": "after", "both": "around"}.get(
        direction, direction
    )
    parts = [
        f"Neighbors of {anchor_chunk_id} ({label_dir} the anchor, "
        f"in reading order):\n"
    ]
    for n in neighbors:
        meta = n.get("metadata", {})
        chunk_id = n.get("id", "")
        page_title = meta.get("page_title", meta.get("title", ""))
        heading = meta.get("section_heading", "")
        chunk_n = meta.get("chunk_n")
        chunk_total = meta.get("chunk_total")
        url = meta.get("url", "")
        header = f"[Neighbor] id: {chunk_id}"
        if page_title:
            header += f" | Page: {page_title}"
        if heading:
            header += f" | Section: {heading}"
        if chunk_total is not None and chunk_total > 1:
            header += f" (part {chunk_n} of {chunk_total})"
        if url:
            header += f"\n  URL: {url}"
        text = n.get("text", "")[:1000]
        parts.append(f"{header}\n{text}")
        if len(n.get("text", "")) > 1000:
            parts.append("... (truncated)")
        parts.append("")
    return "\n".join(parts)


def _format_page_result(
    chunks: list[dict],
    url: str,
    error: str | None,
) -> tuple[str, int, bool]:
    """Assemble a full-page fetch into a single text body for the judge.

    Returns (formatted_text, full_chars, truncated_bool). Body is the
    concatenated chunk texts in reading order. If the assembled length
    exceeds PAGE_FETCH_CHAR_CAP, the tail is replaced with a continuation
    marker; full_chars reports the un-truncated length so the trace can
    show how much was dropped.
    """
    if error:
        return f"fetch_olg_page error for {url}: {error}", 0, False
    if not chunks:
        return f"No chunks found for URL {url}.", 0, False

    first_meta = chunks[0].get("metadata", {})
    page_title = first_meta.get("page_title", first_meta.get("title", ""))
    breadcrumb = first_meta.get("breadcrumb", "")
    program = first_meta.get("program", "")

    body_parts = [chunk.get("text", "") for chunk in chunks]
    body = "\n\n".join(body_parts)
    full_chars = len(body)
    truncated = False
    if full_chars > PAGE_FETCH_CHAR_CAP:
        body = body[:PAGE_FETCH_CHAR_CAP]
        body += (
            f"\n\n[... page truncated at {PAGE_FETCH_CHAR_CAP} chars; "
            f"full page is {full_chars} chars. Use fetch_olg_neighbors "
            f"against a specific chunk_id below to read further.]"
        )
        truncated = True

    header_lines = [f"Full page: {page_title or '(untitled)'}"]
    if program:
        header_lines.append(f"Program: {program}")
    if breadcrumb:
        header_lines.append(f"Path: {breadcrumb}")
    header_lines.append(f"URL: {url}")
    header_lines.append(f"Chunks: {len(chunks)}")
    chunk_ids = [c.get("id", "") for c in chunks]
    header_lines.append("Chunk IDs (in order): " + ", ".join(chunk_ids))
    header = "\n".join(header_lines)

    return f"{header}\n\n{body}", full_chars, truncated


def _summarize_search_results(results: list[dict]) -> list[dict]:
    """Compact summary of OLG search results for the trace log."""
    summaries = []
    for r in results:
        meta = r.get("metadata", {})
        summaries.append({
            "id": r.get("id", ""),
            "score": round(r.get("score", 0), 3),
            "page_title": meta.get("page_title", meta.get("title", "")),
            "section_heading": meta.get("section_heading", ""),
            "url": meta.get("url", ""),
            "text_preview": r.get("text", "")[:300],
        })
    return summaries


# ============================================================
# OUTPUT ROW BUILDING
# ============================================================

# ============================================================
# UI-FACING PIPELINE FUNCTIONS
# ============================================================

def run_extract(analysis_dir: Path, rows: list[dict],
                config: configparser.ConfigParser = None) -> list[dict]:
    """Run the Extractor on CSV rows and save per-finding JSONs.

    Args:
        analysis_dir: Path to the analysis directory (from get_analysis_dir).
        rows: List of CSV row dicts (from load_csv).
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of extracted finding dicts.
    """
    if config is None:
        config = load_config()

    extractor_model = config.get("qc_analyzer", "extractor_model")
    extractor_prompt = load_prompt("qc_extractor", with_preamble=True)
    extractor_temperature = _resolve_temperature(
        config, "extractor_temperature", 0.0
    )

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)

    cost_tracker = Tracker(
        stages=["extractor", "judge", "cmr_check", "fns_check", "cfr_check"]
    )

    start_time = time.time()
    rows_out = []
    for row_idx, row in enumerate(rows, start=1):
        findings_text = row.get("QC Findings", "").strip()
        if not findings_text:
            continue

        extractor_input = build_extractor_input(row)
        extractor_result = run_extractor(
            extractor_input, claude, extractor_model, extractor_prompt,
            cost_tracker=cost_tracker,
            temperature=extractor_temperature,
        )

        # Normalize findings list: ensure each has policy_issues +
        # search_queries (list) + 1-based finding_index. Drop empty
        # entries (no policy_issues) so we don't fabricate phantom rows.
        raw_findings = extractor_result.get("findings", [])
        if not isinstance(raw_findings, list):
            raw_findings = []
        findings_list = []
        for fi, raw in enumerate(raw_findings, start=1):
            if not isinstance(raw, dict):
                continue
            policy = (raw.get("policy_issues") or "").strip()
            if not policy:
                continue
            queries = raw.get("search_queries", [])
            if not isinstance(queries, list):
                queries = [str(queries)] if queries else []
            findings_list.append({
                "finding_index": len(findings_list) + 1,
                "policy_issues": policy,
                "search_queries": queries,
            })

        # Defensive: if extractor returned no usable findings, write a
        # placeholder so the row stays visible in the UI rather than
        # disappearing silently.
        if not findings_list:
            findings_list.append({
                "finding_index": 1,
                "policy_issues": "Extraction returned no findings.",
                "search_queries": [],
            })

        # Clean parenthetical noise from determination
        det = row.get("Food Stamp Determination", "")
        det = re.sub(r"\s*\(Complete [^)]+\)", "", det).strip()

        raw_error_type = row.get("Type Of Errors", "")
        error_type = " / ".join(p.strip() for p in raw_error_type.split(";") if p.strip())

        row_out = {
            "row_index": row_idx,
            "review_number": row.get("Review Number", ""),
            "apid": row.get("APID", ""),
            "tao": row.get("TAO", ""),
            "determination": det,
            "error_type": error_type,
            "finding_narrative": findings_text,
            "non_concur_reason": row.get("Non-Concur Reason", "").strip(),
            "findings": findings_list,
            "phase": "extracted",
        }
        save_finding(analysis_dir, row_idx, row_out)
        rows_out.append(row_out)

    elapsed = round(time.time() - start_time, 1)
    findings = rows_out  # preserved for back-compat with callers expecting `findings`

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"]["extracted"] = True
    if "cost" not in meta:
        meta["cost"] = {}
    if "filter_snapshot" not in meta:
        meta["filter_snapshot"] = _load_filters(config)
    extractor_data = cost_tracker.by_stage()["extractor"]
    meta["cost"]["extractor"] = round(extractor_data["cost"], 4)
    meta["extract_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(findings),
        "model": extractor_model,
        "tokens_in": extractor_data["input_tokens"],
        "tokens_out": extractor_data["output_tokens"],
        "cost": round(extractor_data["cost"], 4),
    }
    save_meta(analysis_dir, meta)

    return findings


# ============================================================
# INVESTIGATE PROGRESS STATE
# ============================================================
#
# Module-level dict + lock. Single-process Uvicorn — fine. If we ever
# scale to multi-worker, swap this for a file or shared store.

_INVESTIGATE_PROGRESS: dict[str, dict] = {}
_PROGRESS_LOCK = threading.Lock()


def get_investigate_progress(name: str) -> dict | None:
    """Return a copy of the current progress entry for an analysis, or None."""
    with _PROGRESS_LOCK:
        entry = _INVESTIGATE_PROGRESS.get(name)
        if entry is None:
            return None
        snapshot = dict(entry)
        snapshot["in_flight"] = list(entry.get("in_flight", []))
        return snapshot


def clear_investigate_progress(name: str) -> None:
    """Drop the progress entry for an analysis."""
    with _PROGRESS_LOCK:
        _INVESTIGATE_PROGRESS.pop(name, None)


def _progress_init(name: str, total: int, skipped: int) -> None:
    with _PROGRESS_LOCK:
        _INVESTIGATE_PROGRESS[name] = {
            "state": "running",
            "total": total,
            "completed": 0,
            "skipped": skipped,
            "errors": 0,
            "in_flight": [],
            "started_at": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
        }


def _progress_mark_in_flight(name: str, row_idx: int, finding_idx: int) -> None:
    with _PROGRESS_LOCK:
        entry = _INVESTIGATE_PROGRESS.get(name)
        if entry is None:
            return
        entry["in_flight"].append([row_idx, finding_idx])
        entry["last_update"] = datetime.now().isoformat()


def _progress_mark_done(name: str, row_idx: int, finding_idx: int,
                        error: bool = False) -> None:
    with _PROGRESS_LOCK:
        entry = _INVESTIGATE_PROGRESS.get(name)
        if entry is None:
            return
        try:
            entry["in_flight"].remove([row_idx, finding_idx])
        except ValueError:
            pass
        entry["completed"] = entry.get("completed", 0) + 1
        if error:
            entry["errors"] = entry.get("errors", 0) + 1
        entry["last_update"] = datetime.now().isoformat()


def _progress_mark_state(name: str, state: str) -> None:
    with _PROGRESS_LOCK:
        entry = _INVESTIGATE_PROGRESS.get(name)
        if entry is None:
            return
        entry["state"] = state
        entry["last_update"] = datetime.now().isoformat()


# ============================================================
# THREAD-SAFE COST TRACKER WRAPPER
# ============================================================

class _LockedTracker:
    """Thin lock around Tracker.record() so concurrent workers don't
    race on stage counters. by_stage() / total() are read after all
    workers complete, so no read-side locking needed."""

    def __init__(self, tracker: Tracker, lock: threading.Lock):
        self._tracker = tracker
        self._lock = lock

    def record(self, stage: str, model: str, usage) -> None:
        with self._lock:
            self._tracker.record(stage, model, usage)


# ============================================================
# SKIPPED-FINDING SHAPE
# ============================================================

_SKIPPED_FINDING_FIELDS = {
    "coverage": "Skipped",
    "confidence": "N/A",
    "reasoning": (
        "Skipped — extractor returned no actionable policy issue "
        "(narrative may indicate the case is correct)."
    ),
    "olg_references": [],
    "gap_description": "",
    "searches_performed": 0,
    "all_search_queries": [],
    "judge_trace": [],
}


def _investigate_one_finding(
    finding: dict, original_row: dict,
    olg_clients, claude, judge_model: str, judge_prompt: str,
    max_judge_searches: int, olg_results_per_search: int,
    seed_results_per_query: int,
    olg_programs, locked_tracker,
    judge_engine: str = "claude-code",
    judge_cc_model: str = "",
    max_neighbor_fetches: int = 8,
    max_page_fetches: int = 3,
    analysis_dir: Path | None = None,
    row_index: int | None = None,
    finding_index: int | None = None,
    judge_api_temperature: float | None = None,
) -> dict:
    """Run seed search + judge for one finding. Returns the field updates
    to merge into the finding dict.

    Pure function — does not mutate `finding`. Thread-safe given thread-safe
    inputs (claude HTTP client is, ChromaDB clients are shared safely per
    comparator pattern, locked_tracker wraps Tracker.record()).

    Routes to the API or Claude Code judge engine based on `judge_engine`.
    Both engines return a (judge_result, judge_trace) tuple conforming to
    the canonical judge trace schema (see qc_analyzer.py just above
    run_judge for the schema).
    """
    extractor_result = {
        "policy_issues": finding.get("policy_issues", ""),
        "search_queries": finding.get("search_queries", []),
    }

    seed_results = run_seed_searches(
        extractor_result["search_queries"], olg_clients,
        results_per_query=seed_results_per_query,
        programs=olg_programs,
    )

    if judge_engine == "claude-code":
        from programs.qc.judge_claude_code import run_judge_claude_code
        judge_result, judge_trace = run_judge_claude_code(
            original_row, extractor_result, seed_results,
            analysis_dir=analysis_dir,
            row_index=row_index,
            finding_index=finding_index,
            max_searches=max_judge_searches,
            model=(judge_cc_model or None),
        )
    else:
        judge_result, judge_trace = run_judge(
            original_row, extractor_result, seed_results, olg_clients,
            claude, judge_model, judge_prompt,
            max_searches=max_judge_searches,
            max_neighbor_fetches=max_neighbor_fetches,
            max_page_fetches=max_page_fetches,
            results_per_search=olg_results_per_search,
            cost_tracker=locked_tracker,
            olg_programs=olg_programs,
            temperature=judge_api_temperature,
        )

    return {
        "coverage": judge_result.get("coverage", "Unknown"),
        "confidence": judge_result.get("confidence", "LOW"),
        "olg_references": judge_result.get("olg_references", []),
        "gap_description": judge_result.get("gap_description", ""),
        "reasoning": judge_result.get("reasoning", ""),
        "searches_performed": judge_result.get("searches_performed", 0),
        "neighbor_fetches_performed": judge_result.get("neighbor_fetches_performed", 0),
        "page_fetches_performed": judge_result.get("page_fetches_performed", 0),
        "all_search_queries": judge_result.get("all_search_queries", []),
        "agent_notes": judge_result.get("agent_notes", ""),
        "error": judge_result.get("error"),
        "judge_trace": judge_trace,
        "_session_id": judge_result.get("_session_id"),
        "_engine": judge_result.get("_engine", judge_engine),
        "_elapsed": judge_result.get("_elapsed"),
    }


def run_investigate(analysis_dir: Path, row_indices: list[int] = None,
                    config: configparser.ConfigParser = None) -> list[dict]:
    """Run Seed Search + Judge on extracted findings, in parallel.

    Args:
        analysis_dir: Path to the analysis directory.
        row_indices: Optional list of 1-based row indices to investigate.
                     Defaults to all extracted findings.
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of updated row dicts (each with nested findings) with
        investigation results.

    Concurrency: parallelizes at the (row, finding) level via a
    ThreadPoolExecutor with `investigate_parallel` workers (default 4).
    Skipped findings (no search queries) are applied synchronously up
    front so the parallel pool only handles real work, and the progress
    counter reflects actual judge calls.
    """
    if config is None:
        config = load_config()

    judge_model = config.get("qc_analyzer", "judge_model")
    max_judge_searches = config.getint("qc_analyzer", "max_judge_searches",
                                       fallback=7)
    max_neighbor_fetches = config.getint("qc_analyzer",
                                         "max_neighbor_fetches",
                                         fallback=8)
    max_page_fetches = config.getint("qc_analyzer",
                                     "max_page_fetches",
                                     fallback=3)
    olg_results_per_search = config.getint("qc_analyzer",
                                           "olg_results_per_search",
                                           fallback=5)
    seed_results_per_query = config.getint("qc_analyzer",
                                           "seed_results_per_query",
                                           fallback=5)
    parallel = config.getint("qc_analyzer", "investigate_parallel",
                             fallback=4)
    judge_engine = config.get("qc_analyzer", "judge_engine",
                              fallback="claude-code").strip()
    if judge_engine not in ("claude-code", "api"):
        raise ValueError(
            f"qc_analyzer.judge_engine must be 'claude-code' or 'api', "
            f"got {judge_engine!r}"
        )
    judge_cc_model = config.get("qc_analyzer", "judge_cc_model",
                                fallback="").strip()
    judge_prompt = load_prompt("qc_judge", with_preamble=True)
    judge_api_temperature = _resolve_temperature(
        config, "judge_api_temperature", None
    )

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    olg_clients = create_client(source="olg")

    csv_path = analysis_dir / "upload.csv"
    if csv_path.exists():
        _, all_rows = load_csv(csv_path)
    else:
        all_rows = []

    if row_indices is None:
        all_findings = load_all_findings(analysis_dir)
        row_indices = [f["row_index"] for f in all_findings
                       if f.get("phase") == "extracted"]

    cost_tracker = Tracker(
        stages=["extractor", "judge", "cmr_check", "fns_check", "cfr_check"]
    )
    tracker_lock = threading.Lock()
    locked_tracker = _LockedTracker(cost_tracker, tracker_lock)

    olg_programs = _load_filters(config)["olg"]["include"] or None

    # Load all rows up front into a shared map; workers mutate finding
    # entries inside `rows_by_idx[row_idx]["findings"][finding_idx]`,
    # protected by per-row locks during the merge+save step.
    rows_by_idx: dict[int, dict] = {}
    original_rows: dict[int, dict] = {}
    skipped_units: list[tuple[int, int]] = []
    real_units: list[tuple[int, int]] = []

    for row_idx in row_indices:
        row = load_finding(analysis_dir, row_idx)
        if not row:
            continue
        rows_by_idx[row_idx] = row
        if 1 <= row_idx <= len(all_rows):
            original_rows[row_idx] = all_rows[row_idx - 1]
        else:
            original_rows[row_idx] = {
                "QC Findings": row.get("finding_narrative", "")
            }
        for fi, finding in enumerate(row.get("findings", [])):
            queries = finding.get("search_queries") or []
            if not queries:
                # Skipped findings (placeholders for clean QC cases) bypass
                # the judge entirely. Apply Skipped fields synchronously so
                # the parallel pool only handles real work.
                finding.update(_SKIPPED_FINDING_FIELDS)
                skipped_units.append((row_idx, fi))
            else:
                real_units.append((row_idx, fi))

    analysis_name = analysis_dir.name
    _progress_init(analysis_name, total=len(real_units),
                   skipped=len(skipped_units))

    # Save rows that have only skipped findings now so the UI sees them
    # immediately if the user polls early. Rows with mixed skipped/real
    # findings get re-saved as their real findings complete (per-row lock
    # ensures no torn writes).
    skipped_only_rows = (
        {ri for (ri, _) in skipped_units}
        - {ri for (ri, _) in real_units}
    )
    for row_idx in skipped_only_rows:
        rows_by_idx[row_idx]["phase"] = "investigated"
        save_finding(analysis_dir, row_idx, rows_by_idx[row_idx])

    row_locks: dict[int, threading.Lock] = {
        ri: threading.Lock() for ri in rows_by_idx
    }

    start_time = time.time()

    def _process(row_idx: int, finding_idx: int):
        finding = rows_by_idx[row_idx]["findings"][finding_idx]
        original_row = original_rows[row_idx]
        _progress_mark_in_flight(analysis_name, row_idx, finding_idx)
        try:
            updates = _investigate_one_finding(
                finding, original_row,
                olg_clients, claude, judge_model, judge_prompt,
                max_judge_searches, olg_results_per_search,
                seed_results_per_query,
                olg_programs, locked_tracker,
                judge_engine=judge_engine,
                judge_cc_model=judge_cc_model,
                max_neighbor_fetches=max_neighbor_fetches,
                max_page_fetches=max_page_fetches,
                analysis_dir=analysis_dir,
                row_index=row_idx,
                finding_index=finding_idx,
                judge_api_temperature=judge_api_temperature,
            )
            return row_idx, finding_idx, updates, None
        except Exception as e:  # noqa: BLE001 — surface error in result
            return row_idx, finding_idx, None, e

    workers = max(1, min(parallel, len(real_units))) if real_units else 1

    try:
        if real_units:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_process, r, f) for (r, f) in real_units]
                for future in as_completed(futures):
                    row_idx, finding_idx, updates, error = future.result()
                    with row_locks[row_idx]:
                        finding = rows_by_idx[row_idx]["findings"][finding_idx]
                        if error is not None:
                            finding.update({
                                "coverage": "Error",
                                "confidence": "N/A",
                                "reasoning": f"Investigate failed: {error}",
                                "olg_references": [],
                                "gap_description": str(error),
                                "error": str(error),
                                "searches_performed": 0,
                                "all_search_queries": [],
                                "judge_trace": [],
                            })
                        else:
                            finding.update(updates)
                        rows_by_idx[row_idx]["phase"] = "investigated"
                        save_finding(analysis_dir, row_idx,
                                     rows_by_idx[row_idx])
                    _progress_mark_done(analysis_name, row_idx, finding_idx,
                                        error=error is not None)
    finally:
        elapsed = round(time.time() - start_time, 1)
        results = list(rows_by_idx.values())

        meta = load_meta(analysis_dir) or {}
        if "phases" not in meta:
            meta["phases"] = {}
        meta["phases"]["investigated"] = True
        meta["investigated_rows"] = row_indices
        meta["judge_engine"] = judge_engine
        if judge_engine == "claude-code":
            meta["judge_cc_model"] = judge_cc_model
        if "cost" not in meta:
            meta["cost"] = {}
        judge_data = cost_tracker.by_stage()["judge"]
        meta["cost"]["judge"] = round(judge_data["cost"], 4)
        if judge_engine == "claude-code":
            stats_model = judge_cc_model or "(claude code default)"
        else:
            stats_model = judge_model
        meta["investigate_stats"] = {
            "timestamp": datetime.now().isoformat(),
            "duration_sec": elapsed,
            "rows_processed": len(results),
            "model": stats_model,
            "tokens_in": judge_data["input_tokens"],
            "tokens_out": judge_data["output_tokens"],
            "cost": round(judge_data["cost"], 4),
            "parallel": workers,
        }
        save_meta(analysis_dir, meta)
        _progress_mark_state(analysis_name, "done")
        # Refresh summary.csv on disk so it's always present after a
        # phase completes — callers no longer have to remember to
        # click "Generate" / "Download" to materialize it.
        try:
            generate_summary_csv(analysis_dir)
        except Exception:
            pass
        try:
            generate_agent_notes_md(analysis_dir)
        except Exception:
            pass

    return results


# ============================================================
# CROSS-CHECK FUNCTIONS (CMR / FNS / CFR)
# ============================================================

def _build_crosscheck_user_message(finding: dict, row: dict,
                                   source_results_formatted: str,
                                   source: str) -> str:
    """Build the user message for a CMR / FNS / CFR cross-check call.

    `row` carries case identity (review #, TAO, narrative) — those live at
    the row level since multiple findings can share the same case. `finding`
    carries the per-issue policy question and judge verdict.
    """
    parts = [
        f"## QC Error\n",
        f"Review #{row.get('review_number', '?')} ({row.get('tao', '?')})",
        f"Determination: {row.get('determination', '?')}",
        f"Error Type: {row.get('error_type', '?')}",
        f"Narrative: {row.get('finding_narrative', 'N/A')}",
        f"",
        f"## Extracted Policy Issue\n",
        f"{finding.get('policy_issues', 'N/A')}",
        f"",
        f"## OLG Coverage Finding\n",
        f"Coverage: {finding.get('coverage', 'Unknown')}",
    ]
    gap = finding.get("gap_description", "")
    if gap:
        parts.append(f"Gap: {gap}")
    reasoning = finding.get("reasoning", "")
    if reasoning:
        parts.append(f"Reasoning: {reasoning}")

    parts.extend([
        f"",
        f"## {source.upper()} Search Results\n",
        source_results_formatted,
    ])
    return "\n".join(parts)


# SOURCE_CHECK_CONFIG drives run_source_check. Each entry collapses what
# was once a near-duplicate run_X_check function into a single row in this
# table. Program filtering is driven uniformly through [qc_analyzer]
# {source}_include / {source}_exclude config keys (see _load_filters).
SOURCE_CHECK_CONFIG = {
    "cmr": {
        "prompt_name": "qc_cmr_check",
        "model_config_key": "cmr_check_model",
        "fallback_classification": "cmr_silent",
        "result_key": "_cmr_check",
        "sections_key": "cmr_sections",
        "phase_name": "cmr_checked",
    },
    "fns": {
        "prompt_name": "qc_fns_check",
        "model_config_key": "fns_check_model",
        "fallback_classification": "fns_silent",
        "result_key": "_fns_check",
        "sections_key": "fns_sections",
        "phase_name": "fns_checked",
    },
    "cfr": {
        "prompt_name": "qc_cfr_check",
        "model_config_key": "cfr_check_model",
        "fallback_classification": "cfr_silent",
        "result_key": "_cfr_check",
        "sections_key": "cfr_sections",
        "phase_name": "cfr_checked",
    },
}


@with_rate_limit_retry()
def _do_crosscheck_call(claude, model: str, system_prompt: str,
                        user_message: str,
                        temperature: float | None = 0.0):
    """Single Anthropic message call for a cross-check row.

    Wrapped with retry so transient rate-limit / overload errors don't kill
    a multi-row check. Per QC F7 — cross-checks previously had zero retry
    coverage.
    """
    kwargs = {
        "model": model,
        "max_tokens": 500,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return claude.messages.create(**kwargs)


def run_source_check(source: str, analysis_dir: Path,
                     row_indices: list[int] = None,
                     config: configparser.ConfigParser = None) -> list[dict]:
    """Run a CMR / FNS / CFR cross-check on investigated findings.

    For each Partial/Gap finding (or row in `row_indices`), searches the
    chosen source for the policy topic and asks Haiku to classify whether
    the source addresses it (`{source}_covers_topic` / `{source}_silent` /
    `{source}_differs`). Result is attached to the finding under the
    source-specific key (`_cmr_check`, `_fns_check`, `_cfr_check`).

    Args:
        source: One of "cmr", "fns", "cfr".
        analysis_dir: Path to the analysis directory.
        row_indices: Optional list of 1-based row indices. Defaults to
                     all Partial/Gap findings.
        config: Optional config; loaded from config.ini if not provided.

    Returns:
        List of updated finding dicts with the source-specific key added.
    """
    if source not in SOURCE_CHECK_CONFIG:
        raise ValueError(
            f"Unknown source {source!r}; valid sources are "
            f"{list(SOURCE_CHECK_CONFIG)}"
        )
    spec = SOURCE_CHECK_CONFIG[source]

    if config is None:
        config = load_config()

    model = config.get("qc_analyzer", spec["model_config_key"],
                       fallback="claude-haiku-4-5-20251001")
    prompt = load_prompt(spec["prompt_name"], with_preamble=True)
    cross_check_temperature = _resolve_temperature(
        config, "cross_check_temperature", 0.0
    )

    api_key = config.get("api", "anthropic_api_key")
    claude = anthropic.Anthropic(api_key=api_key)
    clients = create_client(source=source)

    # Default: rows that contain any Partial/Gap finding. Cross-check
    # then runs only on the qualifying findings inside those rows
    # (not on Adequate findings that share the row).
    if row_indices is None:
        all_rows = load_all_findings(analysis_dir)
        row_indices = [
            r["row_index"] for r in all_rows
            if any(
                f.get("coverage") in ("Partial", "Gap")
                for f in r.get("findings", [])
            )
        ]

    source_programs = _load_filters(config)[source]["include"] or None

    search_kwargs = {
        "collection": "sections",
        "programs": source_programs,
        "top_n": 5,
        "threshold": 0.0,
    }

    cost_stage = f"{source}_check"
    cost_tracker = Tracker(stages=[cost_stage])

    start_time = time.time()
    results = []
    for row_idx in row_indices:
        row = load_finding(analysis_dir, row_idx)
        if not row:
            continue

        any_checked = False
        for finding in row.get("findings", []):
            # Only cross-check Partial/Gap findings; Adequate ones
            # don't surface gaps to compare against.
            if finding.get("coverage") not in ("Partial", "Gap"):
                continue

            query = finding.get("policy_issues", "")
            if not query:
                continue

            search_response = search_with_client(query, clients, **search_kwargs)

            formatted = format_results_for_prompt(
                search_response["results"], source
            )
            user_message = _build_crosscheck_user_message(
                finding, row, formatted, source.upper()
            )

            response = _do_crosscheck_call(
                claude, model, prompt, user_message,
                temperature=cross_check_temperature,
            )
            cost_tracker.record(cost_stage, model, response.usage)

            text = response.content[0].text.strip()
            check_result = extract_json(text, fallback={
                "classification": spec["fallback_classification"],
            })

            check_block = {
                "classification": check_result.get(
                    "classification", spec["fallback_classification"]
                ),
                spec["sections_key"]: check_result.get(spec["sections_key"], []),
                "note": check_result.get("note", ""),
            }

            finding[spec["result_key"]] = check_block
            any_checked = True

        if any_checked:
            save_finding(analysis_dir, row_idx, row)
            results.append(row)

    elapsed = round(time.time() - start_time, 1)

    # Update meta
    meta = load_meta(analysis_dir) or {}
    if "phases" not in meta:
        meta["phases"] = {}
    meta["phases"][spec["phase_name"]] = True
    if "cost" not in meta:
        meta["cost"] = {}
    stage_data = cost_tracker.by_stage()[cost_stage]
    meta["cost"][cost_stage] = round(stage_data["cost"], 4)
    meta[f"{cost_stage}_stats"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": elapsed,
        "rows_processed": len(results),
        "model": model,
        "tokens_in": stage_data["input_tokens"],
        "tokens_out": stage_data["output_tokens"],
        "cost": round(stage_data["cost"], 4),
    }
    save_meta(analysis_dir, meta)
    # See note above run_investigate's tail — keep summary.csv fresh
    # so it's always on disk after any phase completes.
    try:
        generate_summary_csv(analysis_dir)
    except Exception:
        pass

    return results


