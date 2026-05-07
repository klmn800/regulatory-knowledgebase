# QC investigate audit tooling

Reusable scripts for auditing a completed QC `investigate` run. Outputs land
inside the analysis directory so they don't litter the project root.

## Usage

All scripts run from the project root and take an analysis name (the folder
under `output/qc_analysis/`) as their first argument.

### `walker.py` — bulk per-finding extraction + citation grounding

```
python tools/qc_audit/walker.py <analysis_name>
```

Walks every row JSON, validates each `olg_references` entry against the
trace and corpus, dumps a structured `audit_walk.json` into the analysis
directory, and prints high-level stats (coverage / confidence / search
budget / citation grounding).

Citation status values:

- `in_trace` — URL or page_title appears in `judge_trace[*].tool_results`
- `in_corpus` — page exists in `index/olg/section_chunks.json` but didn't
  surface in the post-seed trace. Often means the seed search returned it
  (seed results are stored in `judge_trace[0]` since 2026-05-07; older
  runs lack the seed turn). Verify via `rag.query` replay before claiming
  ungrounded.
- `unverified` — neither in trace nor corpus. **Real hallucination
  candidate**, investigate before reporting.

### `inspect_finding.py` — full-depth view of a single finding

```
python tools/qc_audit/inspect_finding.py <analysis_name> <row> <finding>
```

Prints the full QC narrative, extracted policy issue, all queries (extractor
+ judge), full reasoning, gap description, citation grounding, and turn-by-
turn judge trace. Use when `walker.py` flags something worth digging into.

### `inspect_compact.py` — batch compact view of multiple findings

```
python tools/qc_audit/inspect_compact.py <analysis_name> <row.finding> [<row.finding> ...]
```

Same content as `inspect_finding.py` but more compact, designed for reading
several findings in one pass. Use when validating a pattern across rows.

## Field-path trap

URLs and titles in `index/olg/section_chunks.json` live at:

```
chunk["metadata"]["url"]
chunk["metadata"]["page_title"]
```

**not** at top-level `chunk["url"]`. Audit code that uses `c.get("url")`
will silently return `None` for every chunk and produce false hallucination
reports. The 2026-05-07 audit hit this trap before catching it on row 3.1's
"Contribution Income" citation.

## Recommended audit workflow

1. Run `walker.py` to dump structured data + see top-line stats.
2. Read `audit_walk.json` (or grep for `unverified` / `in_corpus`).
3. For any unverified citations: re-run the seed search via `rag.query` to
   confirm whether the page was retrieved by the extractor's seed queries
   but lost from trace storage.
4. For any spotted Partial verdict that smells fishy: open the cited
   chunks via `inspect_finding.py` and read the full chunk text from
   `section_chunks.json` — the trace's `text_preview` is capped at 300
   chars and may not show the load-bearing detail.
5. Write findings into `AUDIT_REPORT.md` next to the analysis folder.
