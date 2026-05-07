# Apps Cleanup — Execution Plan

Created 2026-05-06. Cleanup audits complete (QC, comparator, search, author, synthesis). This document turns audit findings into concrete shapes for the upcoming cleanup execution.

**Strategy** (per user 2026-05-06): plan how all four apps need to change first, then apply to QC analyzer first. Goal is alignment — avoid building QC one way and the other three slightly differently. Per-app migration starts only after this plan is signed off.

**Inputs**:
- `cross_app_findings.md` — CA-1 through CA-15, sequencing
- `synthesis_review/audit.md` — 30 findings on `tools/synthesis.py`
- `{app}_cleanup/README.md` × 4 — per-app findings

## Status snapshot

| Item | State |
|---|---|
| Four-app audit | ✅ Complete |
| Synthesis audit | ✅ Complete (`synthesis_review/audit.md`) |
| Decision pass | ✅ Complete — all 8 decisions resolved (see "Decisions resolved" table) |
| Doc hygiene | ✅ Complete |
| Build shared modules | ✅ **Complete (2026-05-06)** — `tools/retry.py`, `tools/cost_tracker.py`, `tools/result_formatters.py`, `tools/policy_tools.py` |
| Synthesis migration | ✅ **Complete (2026-05-06)** — all four shared modules wired in. SynthesisResult `error: str | None` field added. Resolved synthesis F3 (run_standard retry), F6 (duplicated APIError handler), F11 (no error signal), F15 (manual deepcopy), F22 (FNS chunk_n/total). |
| **Next: QC migration** | **Sequenced into 5 sub-steps (see "QC migration sub-steps" below). Sub-step 1 = delete CLI pipeline.** |
| Migrate comparator → search → author | After QC validates the shapes |

## QC migration sub-steps (added 2026-05-06)

Unlike the shared-module commits (which were small, isolated units), QC migration is a multi-commit effort. Sequence:

1. **Delete CLI pipeline** — `analyze_csv` (L1396-1594), `save_checkpoint` / `load_checkpoint` (L358-375), `--resume` flag, `if __name__ == "__main__"` block. ~200 lines gone. Isolated; no shared-module imports yet. Per decision #6 (delete the CLI entirely).
2. **Parameterize cross-checks** — three near-identical `run_cmr_check` / `run_fns_check` / `run_cfr_check` functions → one `run_source_check(source, ...)`. UI route consolidation: `/qc/cmr_check`, `/qc/fns_check`, `/qc/cfr_check` → `/qc/source_check/{source}`. Apply the four shared modules during this rewrite (don't import three times then delete two-thirds).
3. **Move TraceLogger to phased pipeline** — currently CLI-only; with CLI deleted, traces need to fire during UI Investigate runs. Per decision #8.
4. **Apply shared modules to extractor + judge** — what step 2 didn't cover. Imports `tools/retry.py`, `tools/cost_tracker.py`, `tools/result_formatters.py`, `tools/policy_tools.py`.
5. **QC-specific finishing**:
   - Drop CFR cross-check's `program="SNAP"` filter (decision #4 — no silent filtering principle)
   - Fix QC F5/B1 (`extract_json` fallback misshapen for cross-checks)
   - Update QC's judge result shape to mirror synthesis's error pattern
   - Docstring sweep (F4) + max_turns formula comment (F11)

## Shared module specs

### 1. `tools/retry.py` (CA-8)

**Purpose**: uniform rate-limit / API-error retry across every Anthropic call site.

**Canonical**: synthesis's `run_deep` retry pattern (60s sleep, one retry on `RateLimitError` or `APIError`, error-result on second failure). Synthesis F3 + F6 (run_standard bare-handed; APIError handler duplicated in run_deep) means we extract the *idea* but not the verbatim code — the helper replaces what's currently inline.

**Shape (proposed)**: decorator preferred over function-wrapper. Less callsite editing; matches the "wrap a method" pattern most cleanly.

```python
# tools/retry.py
def with_rate_limit_retry(max_attempts: int = 2, sleep_seconds: int = 60):
    """Retry on anthropic.RateLimitError / APIError. Logs to stderr.
    On final failure, re-raises — caller decides how to surface to user."""
```

**Why re-raise instead of return error result**: each app surfaces errors differently (synthesis returns SynthesisResult with error in `answer` field — F11 anti-pattern; QC returns Partial-with-LOW; comparator returns confirmed_gap-with-LOW). The retry helper shouldn't impose a single error-shape — it just bounds the retry. Each caller wraps in its own try/except.

**Sites to wrap (catalog)**:
- Synthesis `run_standard` (F3 hole, MAJOR)
- Synthesis `run_deep` two `messages.create` calls (replacing F6 duplicated handler)
- Comparator L0, L1, L2 API, L3 CMR, L3 CFR (F24 — five bare-handed sites)
- QC extractor (replaces handcrafted 3-attempt loop)
- QC judge (replaces handcrafted 1-retry)
- QC cross-checks (currently zero retry — three sites)
- Search `/ask` route handler (F8 — wrap synthesis call, return partial that renders error)
- Author research phase already covered via synthesis; draft phase is Claude Code subprocess (out of scope)

**Decided**: `init_clients()` failures degrade gracefully (decision #1). UI starts with a banner naming which services failed; the rest of the app works as far as initialized services allow. Search routes that depend on a failed source return a partial render explaining the gap; don't crash on click.

### 2. `tools/cost_tracker.py` (CA-1)

**Purpose**: single source of truth for model pricing and cost arithmetic.

**Canonical**: synthesis's `MODEL_PRICING` (correct Haiku 4.5 / Sonnet 4.5 rates) + `calculate_cost()`. Comparator's PRICING dict has stale rates (B1 — fix during extraction).

**Shape (proposed)**:

```python
# tools/cost_tracker.py
MODEL_PRICING = {
    "claude-haiku-4-5":  {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-opus-4-7":   {"input": 15.00, "output": 75.00},
}

def calculate_cost(model: str, in_tok: int, out_tok: int) -> float: ...

class Tracker:
    """Stage-keyed cost accumulator. Stages declared up front so callers
    can roll up ('total') and attribute ('extractor', 'judge', 'cross_checks')."""
    def __init__(self, stages: list[str] = None): ...
    def record(self, stage: str, model: str, usage) -> None: ...
    def total(self) -> dict: ...      # {input_tokens, output_tokens, cost}
    def by_stage(self) -> dict: ...   # {stage: {input_tokens, output_tokens, cost}}
```

**Class shape decision**: parameterized stages, NOT two purpose-fit classes. Comparator's "session/total" is `Tracker(stages=["session"])`; QC's stage-keyed is `Tracker(stages=["extractor","judge","cmr","fns","cfr"])`; synthesis can pass `Tracker(stages=["synthesis"])` or use `calculate_cost()` directly without instantiating Tracker.

**Unknown-model pricing policy (synthesis F30, decision #3)**: warn loudly + use Sonnet rates as fallback + mark cost as estimated in returned data. Warning includes the file path (`tools/cost_tracker.py:MODEL_PRICING`) and the Anthropic pricing reference URL so the user knows exactly what to update. Sister CLI helper `python tools/cost_tracker.py --check` reads `config.ini` for any model strings (synthesis, comparator layers, QC stages) and reports any not present in `MODEL_PRICING`. Don't halt work — pricing reporting is informational.

**Sites to migrate**:
- Synthesis: keep `MODEL_PRICING`/`calculate_cost` imports from this module; existing call sites unchanged
- Comparator: replace PRICING dict + TokenTracker with `Tracker(stages=["session"])` (fixes B1 simultaneously)
- QC: replace MODEL_PRICING + CostTracker with `Tracker(stages=["extractor","judge","cmr","fns","cfr"])`

### 3. `tools/result_formatters.py` (CA-3 — Python layer)

**Purpose**: single per-source formatter dispatcher for prompt injection.

**Canonical**: synthesis's `format_results_for_prompt(results, source)` — single function, four sources via if/elif, richest metadata. Synthesis F21 + F22 (FNS branch missing chunk_n/total) need reconciliation **during extraction**, not after.

**Shape (proposed)**:

```python
# tools/result_formatters.py
SOURCE_LABELS = {"olg": "OLG", "fns": "FNS Handbook 310",
                 "cmr": "106 CMR", "cfr": "7 CFR"}

def format_results_for_prompt(
    results: list[dict],
    source: str,
    *,
    include_url: bool = True,
    include_breadcrumb: bool = True,
    score_format: str = "decimal",  # "decimal" → 0.85, "percent" → 85%
) -> str: ...
```

**Why options**: comparator's four formatters are slightly leaner (no URL on some). Options preserve those without forcing every caller to build a wrapper. Default values match synthesis's current behavior (so search and author are unchanged).

**FNS branch fix (F22)**: add `(part X of Y)` rendering for FNS during extraction — matches OLG/CMR/CFR. Sole reason it's missing today is oversight; FNS chunks have the metadata.

**Sites to migrate**:
- Synthesis: import from new module, drop the local function
- Comparator: drop four separate formatters, call shared one
- QC: `format_olg_results_for_prompt` + `_format_source_results_for_prompt` both call shared one

**Out of scope here**: Jinja template-layer dispatch (3 templates × per-source `if/elif`). Tracked separately in CA-3 template-layer; planned for the next coordinated change to `answer.html` / `history_detail.html` / `result_card.html`. Not blocking QC.

### 4. `tools/policy_tools.py` (CA-9)

**Purpose**: shared search-tool definitions for Anthropic tool-use loops.

**Canonical**: synthesis's `SEARCH_POLICY_TOOL` (multi-source enum). Comparator's `SEARCH_OLG_TOOL` and QC's `SEARCH_OLG_TOOL` are diverged-description specializations.

**Shape (proposed)**: factory function instead of bare constants — synthesis F15 (manual three-level dict-copy at L377) reveals callers need to *narrow* the source enum at runtime. Factory exposes that intent.

```python
# tools/policy_tools.py
def make_search_tool(sources: list[str], *, name: str = "search_policy") -> dict:
    """Build a tool definition with the source enum restricted to `sources`."""
    ...

def make_lookup_fns_section_tool() -> dict: ...  # comparator L2's second tool

# Convenience constants for common shapes:
SEARCH_OLG_TOOL = make_search_tool(["olg"], name="search_olg")
SEARCH_POLICY_TOOL = make_search_tool(["olg", "cmr", "fns", "cfr"])
```

**Description copy (decision #7)**: tool description stays neutral. Factual wording: "Search the DTA Online Guide (OLG) for policy and procedures relevant to SNAP, TAFDC, and EAEDC programs." Each caller's *prompt* — not the tool description — emphasizes the relevant aspect (QC prompt: focus on procedures gaps; comparator prompt: focus on policy comparison). Decouples shared infrastructure from caller-specific intent.

**Sites to migrate**:
- Synthesis: import `make_search_tool`, drop F15 manual deepcopy
- Comparator L2: import both factories
- QC judge: import `SEARCH_OLG_TOOL` from new module

## Synthesis-side contract change (NS7 / F5 / F11 / B1)

**Problem**: `SynthesisResult` has no success/error field. Errors return as "fake answers" with the error string in `answer`. Search persists them to history; author would write to `report.md` with no signal.

**Fix**: add `error: str | None = None` field to dataclass (synthesis.py:L66-75). On success, `error=None`, `answer` has real content. On failure, `error` has message, `answer` is empty (or a deliberate "Synthesis failed" placeholder for callers that render unconditionally).

**Why `error: str | None` over `success: bool`**: same information, but the message is preserved for logging without a second field.

**Caller updates (touched by this change)**:
- Search: `/ask` checks `result.error`; if set, renders an error partial instead of `answer.html`. History persistence skips error results (or stores with an `error` column — tied to CA-14 schema work).
- Author research: `run_research` checks `result.error`; if set, raises (don't write `report.md` / `evidence.json`). UI shows error.
- Synthesis CLI: prints `result.error` to stderr, exits non-zero.

**This change unblocks**: search NS7 (history persistence of failures), author error detection, CA-8 retry callers (helper re-raises, callers set `error` and return).

## Per-app target state

### QC analyzer (first migration target)

Already-decided actions (from QC notes):

1. **Delete CLI pipeline** (`analyze_csv` L1396-1594, `save_checkpoint`/`load_checkpoint` L358-375, `--resume` flag, `if __name__` CLI). Phased pipeline is canonical (decided 2026-05-05).
2. **Parameterize cross-checks** — F2 sketch already in QC notes. Three `run_X_check` functions → one `run_source_check(source, ...)`. UI route `/qc/source_check/{source}` replaces three routes (F16).
3. **Move TraceLogger into the phased pipeline (decision #8)**. Currently CLI-only; with the CLI gone, wire TraceLogger into the UI Investigate run. Per-finding JSONL written under `analysis_dir/traces/row_NNN.jsonl`. Useful for "why did the judge classify this Gap?" debugging.
4. **Cross-check query benchmark (F10)** — small experiment, deferred to after structural cleanup.
5. **CSV output redesign (F15 / CA-7)** — out of scope, separate work item.

New actions from cross-app extractions:

6. Import `tools/retry.py`; wrap extractor + judge + three cross-checks. Drop handcrafted retries.
7. Import `tools/cost_tracker.py`; replace MODEL_PRICING + CostTracker with parameterized Tracker.
8. Import `tools/result_formatters.py`; drop `format_olg_results_for_prompt` and `_format_source_results_for_prompt`.
9. Import `tools/policy_tools.py`; drop inline `SEARCH_OLG_TOOL`.
10. Update QC's judge result shape to mirror synthesis's `error` field convention (parallel to synthesis F11 fix).
11. Docstring sweep (F4) — replace "Two-call architecture" with the actual phased shape.
12. Document max_turns = max_searches + 5 formula (F11) in a one-line comment.

**QC F6 (program filter inconsistency, decision #4)**: drop CFR's `program="SNAP"` default; all three cross-checks pass no filter. Cross-cutting principle: no silent program filtering anywhere. If a future filter is wanted, it's explicit (e.g., user-selected via UI) and visible in the result metadata.

### Comparator

After QC validates module shapes:

1. **B1 fix** (wrong Haiku rates) — handled automatically by `tools/cost_tracker.py` migration.
2. Import `tools/retry.py`; wrap L0, L1, L2 API, L3 CMR, L3 CFR. Resolves F24 (zero retries).
3. Import `tools/cost_tracker.py`; drop PRICING + TokenTracker.
4. Import `tools/result_formatters.py`; drop four format_X_results_for_prompt functions.
5. Import `tools/policy_tools.py`; drop inline `SEARCH_OLG_TOOL` and `LOOKUP_FNS_SECTION_TOOL`.
6. **CA-10 budget convergence**: add `max_searches` separate cap to L2 (parallels synthesis). `max_turns = 15` becomes `[comparator] max_turns = 15` config key.
7. Docstring sweep (F1, F2 — outdated post-restructure paths).

### Search

After QC and comparator:

1. **CA-14 history persistence**: search `save_search` adopts author's `evidence.json` shape. Adds `search_queries`, full evidence with rank/score/text/metadata/id. New `search_queries TEXT` column on SQLite. Wires search NS1.
2. **Search F2 (vestigial `/search` endpoint)** — open question. Recommendation: kill. Nobody uses it. Collapses CA-11 from "share a cache" to "drop dead code." Removes `ui/search.py:_clients` + `ui/search.py:do_search` + `init_clients()` eager init.
3. **Search F5/B1 (CFR missing in `history_detail.html`)** — one-line fix; bundle with template-layer CA-3 work.
4. **`/ask` error handling**: wrap `run_synthesis` in try/except, render error partial when `result.error` set.
5. **`init_clients` decision** (CA-8 user open question above) → applied here.
6. Docstring sweep (search F1).

### Author

After QC, comparator, search. **Author warrants a focused 1-2 day cleanup pass** (per user 2026-05-06) — bundle these actions together rather than scatter them.

1. **Delete the CLI entirely (decision #6)**. Remove the `if __name__ == "__main__"` block, argparse setup, all CLI-specific flags (`--research-only`, `--draft-only`, `--resume`, `--no-docx`, `--assignment-file`). Eliminates the source of CLI/UI drift. Update README references. The phase functions (`run_research`, `launch_draft`, `format_output`) remain as the canonical UI-callable entry points.
2. **CA-13 Claude Code subprocess unification**: extend `tools/claude_code_runner.py` to accept `session_id` (passes `--session-id`) and resume mode. Migrate `launch_draft` and `launch_resume` to call `run_claude_task`. Eliminates author B1 (shared scratch file race), F7 (intra-module .bat duplication), and activates F15's dead `claude_code_timeout` config key.
3. **Author F2** (research phase has no program filter): wire `programs_by_source` into `run_research`. Surfaces TAFDC/EAEDC noise on SNAP-specific assignments. Inherits the cross-cutting principle from decision #4: filter selection must be explicit (UI control), not a silent default. Author exercises 5 of 9 synthesis params already; add a 6th (`programs_by_source`).
4. **Author F13** (Author's Notes guidance duplicated across two prompts): consolidate to one canonical instruction.
5. Author research result handling: check `result.error` (synthesis contract change above).
6. Docstring sweep.

**Deferred for author**:
- F5/F6 (partial consolidation) — feature-shaped, not pure cleanup
- F11 (JSON data endpoints replacing HTML-parsing JS) — feature-shaped

## Decisions resolved (2026-05-06)

All 8 open decisions answered by user. Build phase has no remaining design ambiguity.

| # | Decision | Resolution |
|---|---|---|
| 1 | `init_clients()` startup failure policy | **Degrade gracefully**. UI starts with a banner explaining limited functionality; user can use whatever services initialized successfully. |
| 2 | Failure signal on `SynthesisResult` | **Add `error: str \| None`**. On success: `error=None`. On failure: `error` holds message, `answer` empty. Caller checks `if result.error:` to branch. |
| 3 | Unknown-model pricing fallback (F30) | **Warn loudly + use Sonnet rates + flag as estimated**. Don't halt work. Warning includes file path + Anthropic pricing URL to guide manual update. Follow-up: `python tools/cost_tracker.py --check` CLI helper that scans config and reports models missing from `MODEL_PRICING`. |
| 4 | QC F6 cross-check program filter | **No silent filtering anywhere — cross-cutting principle**. Drop CFR's `program="SNAP"` default. All three QC cross-checks pass no filter. Reasoning: OLG programs that aren't EAEDC/TAFDC are largely SNAP-adjacent; silent SNAP filter would exclude relevant policy. Filtering, when it happens, is *explicit and visible*. Inherits to author F2 (research phase) and the deferred per-source program filter UI. |
| 5 | Kill search F2 vestigial endpoint? | **Yes, kill**. Delete `/search` route, `ui/search.py:do_search`, `ui/search.py:_clients` eager cache, `init_clients()` eager wiring. Synthesis's lazy cache becomes the only cache. F3 vestigial result_card partial also goes. CA-11 collapses to nothing. |
| 6 | Author CLI/UI parity | **Delete the CLI entirely**. No headless usage in practice; UI is the only user path. Removes the source of CLI/UI drift. If a batch-run need ever surfaces, rebuild a thin shim against whatever the code looks like then. |
| 7 | Shared OLG tool description wording (CA-9) | **Tool description stays neutral**; per-app intent lives in prompts. Tool description: factual ("Search the DTA Online Guide for policy and procedures relevant to SNAP, TAFDC, and EAEDC"). QC's prompt emphasizes procedures (where the user specializes); comparator's emphasizes policy gaps. Decoupling tool description from caller intent. |
| 8 | TraceLogger disposition | **Move to phased pipeline**. With CLI deleted, TraceLogger fires during UI Investigate runs. Useful for debugging "why did the judge classify this finding as Gap?" JSONL files written under `analysis_dir/traces/`. |

## Cross-cutting principles surfaced during decisions

- **No silent program filtering** (from decision #4). Anywhere we filter by program, the filter is explicit and visible. Defaults that quietly narrow scope are out. Applies to QC cross-checks, author research, future per-source filter UI.
- **Tool descriptions are neutral; intent lives in prompts** (from decision #7). Shared tool definitions describe what the tool DOES, not what each caller wants from it.
- **Don't halt on cost-tracking gaps** (from decision #3). Cost reporting is informational; pricing-dict drift shouldn't break runs. Make drift visible and fixable, not blocking.

## Build sequencing (after decisions)

Order chosen to minimize churn — extract a shape, validate it on QC, *then* propagate.

1. ✅ **Doc hygiene + decisions log entries** — DONE 2026-05-06.
2. ✅ **Build `tools/retry.py`** — DONE 2026-05-06. Applied to synthesis `run_standard` (was bare-handed) and `run_deep` (eliminated F6 duplicated APIError handler).
3. **B1 fix in comparator** — bundles with comparator migration (step 9), auto-resolved via `tools/cost_tracker.py` import.
4. ✅ **Synthesis `error` field on SynthesisResult** — DONE 2026-05-06. `error: str | None` added; `run_standard` / `run_deep` set it on failure (answer text preserved for backwards compat); `/ask` renders new `partials/answer_error.html` when set; `author.run_research` raises on `result.error`. History persistence still records errors (CA-14 cleanup).
5. ✅ **Build `tools/cost_tracker.py`** — DONE 2026-05-06. `MODEL_PRICING` + `calculate_cost` extracted; new parameterized `Tracker` class for QC/comparator. Unknown-model fallback warns once per process with file path + Anthropic pricing URL, falls through to Sonnet rates (decision #3). Synthesis migrated.
6. ✅ **Build `tools/result_formatters.py`** — DONE 2026-05-06. Single `format_results_for_prompt` with kwargs (`include_url`, `include_breadcrumb`, `score_format`). FNS branch fix (synthesis F22): now emits `(part X of Y)`. Synthesis migrated.
7. ✅ **Build `tools/policy_tools.py`** — DONE 2026-05-06. `make_search_tool(sources)` factory + `make_lookup_fns_section_tool()`. Convenience constants `SEARCH_POLICY_TOOL` and `SEARCH_OLG_TOOL`. Tool description neutral per decision #7. Synthesis migrated; F15 manual deepcopy collapsed to one factory call.
8. **QC migration** ← NEXT. Sequenced into 5 sub-steps (see "QC migration sub-steps" near the top of this doc). Sub-step 1 = delete CLI pipeline. This is the "QC up and running" milestone.
9. **Comparator migration**: same module imports + B1 verified (auto-fixed by step 5) + F24 retry coverage + CA-10 budget config.
10. **Search migration**: CA-14 history persistence + F2 kill + (`/ask` error handling already done in step 4) + F5/B1 CFR template fix + decision #1 (`init_clients` degrade-gracefully banner).
11. **Author migration**: delete CLI (decision #6) + CA-13 Claude Code unification + F2 program filter + F13 prompt dedup. Focused 1-2 day pass.
12. **Tail**: CA-5 + CA-15 docstring sweep across all five files. CA-12 progress JS helper.

After step 8 you have a clean QC analyzer running on shared modules. Steps 9-11 propagate the same shapes to the other three apps without re-deciding anything.

## What this plan deliberately defers

- **A2 shared `agentic_search_loop` primitive** — only viable when a fourth callsite emerges. Today's three loops (synthesis deep, QC judge, comparator L2) keep their purpose-fit shells.
- **CA-7 CSV output redesign** — separate end-to-end design pass for both QC and comparator outputs.
- **Streaming progress / SSE** — feature work, not cleanup.
- **Engine routing for QC and synthesis** — feature work, not cleanup.
- **Folder rename `programs/ → apps/`** — its own task to avoid muddying cleanup with rename churn.
- **Template-layer CA-3 (per-source dispatch in three Jinja templates)** — bundles with the next coordinated change to `answer.html` / `history_detail.html` / `result_card.html`.

## Appendix: finding-to-action map

For traceability — every audit finding should have either an action above or be explicitly deferred.

| Source | Finding | Resolution |
|---|---|---|
| Synthesis F1, F28 | Outdated docstring + missing CLI flag | Step 12 docstring sweep |
| Synthesis F2 | Pre-fetch block dup'd | Optional helper `_prefetch_sources` during step 5 (nice-to-have) |
| Synthesis F3 | run_standard no retry — MAJOR | Step 2 `tools/retry.py` |
| Synthesis F4 | max_turns hardcoded | Step 9 (comparator), config key applied to synthesis too |
| Synthesis F5/F11/B1 | No success/error field | Step 4 SynthesisResult contract |
| Synthesis F6 | Duplicated APIError handler | Eliminated when retry helper applied (step 2) |
| Synthesis F7 | Evidence dedup-by-id | NS5 fix; bundle with step 4 |
| Synthesis F8/F10 | do_search divergence + dead UI cache | Step 10 (kill search F2 collapses both) |
| Synthesis F9 | Module-level cache race | Documented as single-process assumption; revisit if multi-user |
| Synthesis F12, F13, F14 | Stop-reason / answer-text edge cases | Document as accepted; revisit if a real-world failure surfaces |
| Synthesis F15 | Manual deepcopy | Step 7 `make_search_tool` factory |
| Synthesis F16 | config_overrides accepts arbitrary keys | Document accepted-keys list in run_synthesis docstring (step 12) |
| Synthesis F17 | max_searches placement asymmetry | Document precedence (top-level kwarg loses to config_overrides); step 12 docstring |
| Synthesis F18 | prompt_name resolution implicit | Document strict-project-shared contract (step 12) |
| Synthesis F19 | with_preamble hardcoded | Document; revisit if a caller needs preamble-off |
| Synthesis F20 | Dead `program` / `exclude_programs` | Remove from `run_synthesis` signature (step 4 — same touch) |
| Synthesis F21, F22 | format_results dispatch + FNS branch | Step 6 (`tools/result_formatters.py`) |
| Synthesis F23 | calculate_cost called 4× | Tracker.record() collapses (step 5) |
| Synthesis F24 | Print statements | Document; logging migration is feature work |
| Synthesis F25 | do_search hardcodes threshold/mode | Document; mode plumbing only when retrieval requires it |
| Synthesis F26 | search_queries untyped | Step 4 — change to typed dict shape |
| Synthesis F27 | Budget-exhausted turns wasted | Optional: end loop on first post-budget tool_use; minor |
| Synthesis F29 | load_prompt duplicated in QC | CA-15 — documentation only |
| Synthesis F30 | Sonnet pricing fallback | Decision 3 above |
| QC F1 | Two parallel pipelines | Step 8 — delete CLI |
| QC F2 / F16 | Cross-check copy-paste | Step 8 — `run_source_check` parameterized |
| QC F3 | Two summarizers | Step 8 — keep one |
| QC F4 | Wrong docstring | Step 8 — docstring update |
| QC F5/B1 | extract_json fallback wrong-shaped | Step 8 — fix during migration |
| QC F6 | Cross-check program filter | Decision 4 above |
| QC F7 | Mixed retry strategies | Step 2 + step 8 — retry helper |
| QC F8 | Hardcoded search params | Step 8 — config-driven |
| QC F9 | MODEL_PRICING in code | Step 5 — `tools/cost_tracker.py` |
| QC F10 | Cross-check query phrasing | Deferred — small benchmark after structural cleanup |
| QC F11 | max_turns formula magic | Step 8 — one-line comment |
| QC F12 | OLG-specific tool description | Step 7 — shared tool def |
| QC F13 | Source-result label format | Step 6 — `tools/result_formatters.py` |
| QC F14 | Print-vs-log | Documented; logging is feature work |
| QC F15 | Two output formats | Deferred — CA-7 |
| QC F17-F22 (UI) | UI consolidation | Step 8 — `/qc/source_check/{source}` |
| Comparator F24 | Zero retry | Step 9 — retry helper |
| Comparator F1, F2 | Outdated docstrings | Step 12 |
| Comparator B1 | Wrong Haiku rates | Step 5 — auto-fixed by cost_tracker migration |
| Search NS1 | search_queries not persisted | Step 10 — CA-14 |
| Search F2/F3 | Vestigial endpoints | Decision 5 above |
| Search F5/B1 | CFR missing in history_detail | Step 10 — one-line fix |
| Search F8 | /ask no try/except | Step 10 — error handling |
| Search F9 | init_clients no try/except | Decision 1 above |
| Author B1 | Shared scratch file race | Step 11 — CA-13 |
| Author B2 | next_version_dir race | Step 11 — small fix during CA-13 |
| Author F1 | Hand-rolls Claude Code | Step 11 — CA-13 |
| Author F2 | No program filter | Step 11 |
| Author F3 | CLI/UI parity | Decision 6 above |
| Author F7 | .bat duplication | Step 11 — CA-13 |
| Author F13 | Author's Notes dup'd | Step 11 |
| Author F15 | Dead claude_code_timeout config | Step 11 — CA-13 activates |

Coverage: 100%. Findings not in this table are either RESOLVED, RETRACTED, or DOWNGRADED in their app's notes.
