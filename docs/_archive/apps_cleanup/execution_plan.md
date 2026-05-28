# Apps Cleanup — Execution Plan

> **ARC CLOSED 2026-05-12 — superseded by a principles-first reset.**
>
> **Where to go for the live plan**: `docs/design_principles.md` (top-level) for the guiding principles. `docs/apps_alignment/` (or successor folder) for the new execution plan.
>
> **What landed in code under this arc** (preserved, not reverted):
> - Synthesis migration (2026-05-06, committed) — all four shared modules wired in: `tools/retry.py`, `tools/cost_tracker.py`, `tools/result_formatters.py`, `tools/policy_tools.py`. `SynthesisResult.error: str | None` added.
> - QC migration (2026-05-07, committed) — `qc_analyzer.py` 1,658 → 992 lines. CLI deleted. Cross-checks parameterized. Judge trace folded into per-finding JSON. Per-source program filters via config + UI panel. Per-run timestamped folders. Judge result has explicit error field.
> - Comparator migration (2026-05-07, committed) — `comparator.py` 1,757 → 1,700 lines. All four shared modules wired in. L3 parameterized to one function across CMR + CFR. L2 search budget separated from turn budget (`max_searches = 10`). Latent bugs fixed (CSV per-row cost columns, L0 fallback field-name mismatch, full-loop exhaustion search count).
> - Author migration (2026-05-12, coded but uncommitted at arc close) — dual-engine research path (`programs/author/research_claude_code.py`), env-var program-filter enforcement at `rag/query.py` import time, extended `tools/claude_code_runner.py` with toggle params, QC B1 filter-leak fix bundled. Working-tree state is the new baseline.
>
> **Why this arc closed**: framing drift. The plan was scoped as "factor only duplicates" (the B decision in `cross_app_findings.md`), which delivered code hygiene but did not pursue the user's actual goal — **identify the winning pattern and replicate it across apps**. Two principles the plan didn't name:
>
> 1. **Dual-engine (CC + API) for every research/investigation agent.** Author got dual-engine because the user built it; the plan didn't promote it to a pattern others should adopt.
> 2. **RAG-as-library, tools-as-public-surface, apps-as-composers.** The plan factored literal duplicate constants (`SEARCH_OLG_TOOL` defined twice) but kept each app's tool list separate. Capability gaps between apps (e.g., one agent can fetch full pages, another can't) are invisible to this framing.
>
> Decisions made under the narrower framing — especially the B decision and the per-app target states — are out of date. The QC + comparator migrations are "first-pass aligned with old framing; follow-up arc needed" (e.g., QC investigator should be dual-engine, comparator L2 tools should come from a canonical registry). The Author migration design (D1–D5) mostly survives because dual-engine is already its shape.
>
> **What carries forward**: the audit data (findings F1–F26 per app, CA-1 through CA-15) is preserved diagnostic information — those gaps in the code are still real. They get re-prioritized under new principles, not deleted. The four shared modules in `tools/` stay. The decisions table below is preserved as historical record.
>
> **Where this folder lives now**: this entire `docs/apps_cleanup/` folder is being moved to `docs/_archive/apps_cleanup/` to reduce confusion with the new arc. Treat everything below this banner as historical.
>
> ---

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
| QC architecture pass | ✅ **Complete (2026-05-07)** — three additional decisions resolved (#9 program filters, #10 folder layout, #11 trace storage). Sub-steps refined; specific filter lists locked in. |
| QC migration | ✅ **Complete (2026-05-07)** — all 5 sub-steps done. `qc_analyzer.py` 1,658 → 992 lines (-40%). Commits: `f5cf65c`, `6ad0141`, `d3ab4ed`, `f2c8d3a`, `a9d3dfc`, `d8886ea`, `48367fe`, `5edb987`. See "QC migration outcome" section below. |
| Comparator migration | ✅ **Complete (2026-05-07)** — all 4 sub-steps done. `comparator.py` 1,757 → 1,700 lines (−57 net). Commits: `93a3789`, `e017546`, `81fc5a2`, `b363f50`. See "Comparator migration outcome" section below. |
| **Next: Author migration** | **In progress (2026-05-12).** Surface grew: Phase 1 now dual-engine (CC default + API). Sub-step shape: research → draft → tail. Bundles QC B1 filter-leak fix (same `query.py` env-var touch). |
| Search migration | Deferred after Author. Smaller surface — most logic already in `tools/synthesis.py`. |

## QC migration sub-steps (added 2026-05-06, refined 2026-05-07)

Unlike the shared-module commits (which were small, isolated units), QC migration is a multi-commit effort. Sequence:

1. **Delete CLI pipeline + legacy artifact cleanup** — `analyze_csv` (L1396-1594), `save_checkpoint` / `load_checkpoint` (L358-375), `--resume` flag, `if __name__ == "__main__"` block. ~200 lines gone. Isolated; no shared-module imports yet. Per decision #6 (delete the CLI entirely). **Also**: move legacy CLI output artifacts at top of `output/qc_analysis/` (`*_analyzed.csv`, `*_trace_*.jsonl`, etc.) into `Deprecated/`.
2. **Parameterize cross-checks** — three near-identical `run_cmr_check` / `run_fns_check` / `run_cfr_check` functions → one `run_source_check(source, ...)`. UI route consolidation: `/qc/cmr_check`, `/qc/fns_check`, `/qc/cfr_check` → `/qc/source_check/{source}`. Apply the four shared modules during this rewrite (don't import three times then delete two-thirds).
3. **Move TraceLogger into per-finding JSON** — currently CLI-only and writes separate `*_trace.jsonl` files. Refined 2026-05-07: instead of moving the JSONL writer, **fold `judge_trace` into the existing `row_NNN.json`**. Single file per finding holds extractor + seed_results + judge_result + `judge_trace` + cross_checks. No separate trace files. Per decision #8 + decision #11 (2026-05-07 refinement).
4. **Apply shared modules to extractor + judge** — what step 2 didn't cover. Imports `tools/retry.py`, `tools/cost_tracker.py`, `tools/result_formatters.py`, `tools/policy_tools.py`.
5. **QC-specific finishing**:
   - **Per-source program filters** (decision #9, 2026-05-07) — replace dropped CFR `program="SNAP"` with explicit per-source `include`/`exclude` config in `[qc_analyzer]`. Specific lists locked in:
     - **OLG include**: SNAP, Cross-Program, BP, Pathways, Harper, Self-Service, Domestic Violence, Policies & Procedures, SUN Bucks, General
     - **OLG exclude**: TAFDC, EAEDC, COVID, Notices/Forms, Scheduled Mailings, Forms, microcontent
     - **FNS include**: SNAP, QC_Process — all programs (FNS keeps everything per user)
     - **FNS exclude**: (none)
     - **CMR include**: SNAP, Hearings, Program Integrity, SSP
     - **CMR exclude**: EA
     - **CFR include**: SNAP, QC, Issuance, Disaster, Summer-EBT
     - **CFR exclude**: Administration
   - **UI filter panel** — read-only summary at top of QC tab, collapsed by default, expandable to show full include/exclude lists. Format: "OLG: 10 of 16 programs · CMR: 4 of 5 · CFR: 5 of 6 · FNS: all (2)".
   - **Folder layout migration** (decision #10, 2026-05-07) — analysis dirs become `output/qc_analysis/{analysis_name}_{YYYY-MM-DD_HHMM}/`. Each upload spawns a new dir; reruns of phases stay in-place. Files inside simply named (`upload.csv`, `meta.json`, `summary.csv`, `results/row_NNN.json`). Existing analyses left as-is; new convention applies to new uploads.
   - **`meta.json` gains `filter_snapshot`** — record which programs were active for that run, so future audit can answer "what scope was this run?"
   - Fix QC F5/B1 (`extract_json` fallback misshapen for cross-checks)
   - Update QC's judge result shape to mirror synthesis's error pattern
   - Docstring sweep (F4) + max_turns formula comment (F11)

## QC migration outcome (closed 2026-05-07)

**Total reduction**: `programs/qc/qc_analyzer.py` went from 1,658 → 992 lines (-40%) across 8 commits + 1 plan-refinement commit.

**Per sub-step**:
- **5a (`d8886ea`)** — per-source program filters: `[qc_analyzer]` config keys `{source}_include`/`{source}_exclude` for OLG/CMR/CFR/FNS, applied to seed search + judge tool calls + cross-checks. CFR's `program="SNAP"` hack removed. New `ui/templates/partials/qc_filter_panel.html` (zero-JS HTML5 details/summary). Each analysis's `meta.json` captures `filter_snapshot` for audit. Captured at upload time AND backfilled at first extract for legacy analyses.
- **5b (`48367fe`)** — per-run folder layout: new uploads at `output/qc_analysis/{name}_{YYYY-MM-DD_HHMM}/`. Existing analyses (e.g., `Test/`) untouched.
- **5c (`5edb987`)** — tail cleanup:
  - Judge result gains `error: str | None` field on API failure + max-turns exhaustion paths
  - F5/B1 fix: `extract_json(text, fallback: dict | None = None)` — callers pass exact shape they want; cross-check fallback now actually populates `classification` field
  - Orphans dropped: `CHECKPOINT_FILE`, `APPENDED_COLUMNS`, `select_rows`, `_format_source_results_for_prompt`, plus `build_output_row` (5th orphan found by agent — same provenance, dropped)
  - Module docstring rewritten to describe phased pipeline accurately
  - `max_turns = max_searches + 5` formula commented

**Behavior change watch-items captured**:
- Cross-check formatter swap (sub-step 2) and judge formatter swap (sub-step 4): richer headers (program label, "Section:" prefix, parent_heading, chunk-of-N) now visible to Haiku/Sonnet. May shift classifications subtly toward "more covered." Logged in `~/.claude/projects/E--policy-navigator/memory/qc_cross_check_format_watch.md` with one observed instance (row_003 Partial → Adequate).

**Watch-items NOT yet investigated**:
- Whether the row_003 shift is correct or a confidence inflation
- Cross-check Haiku-vs-Sonnet experiment (deferred per decision)

**Config to add to fresh checkouts** (gitignored, agent documented in 5a commit body):
```ini
[qc_analyzer]
olg_include = SNAP, Cross-Program, BP, Pathways, Harper, Self-Service, Domestic Violence, Policies & Procedures, SUN Bucks, General
olg_exclude = TAFDC, EAEDC, COVID, Notices/Forms, Scheduled Mailings, Forms, microcontent
fns_include = SNAP, QC_Process
fns_exclude =
cmr_include = SNAP, Hearings, Program Integrity, SSP
cmr_exclude = EA
cfr_include = SNAP, QC, Issuance, Disaster, Summer-EBT
cfr_exclude = Administration
```

## Comparator migration outcome (closed 2026-05-07)

**Total reduction**: `programs/comparator/comparator.py` went from 1,757 → 1,700 lines (−57 net) across 4 commits. Line-count delta is small because of necessary docstring expansion in sub-step 4; internals are substantially cleaner.

**Per sub-step**:
- **1 (`93a3789`)** — apply 4 shared modules: drop local `PRICING` dict (auto-fixes B1 wrong Haiku rates), `TokenTracker` class, three near-duplicate search-result formatters (OLG/CMR/CFR; `format_fns_for_prompt` retained — different shape), and two inline tool defs. Five Anthropic call sites wrapped with `@with_rate_limit_retry()` (L0, L1, L2 agentic loop, L3 CMR, L3 CFR). L2 uses the per-iteration closure pattern to preserve agentic-loop messages state across retries. `run_layer2_claude_code` (subprocess) intentionally not wrapped. Per-layer token diffs (`_tokens_in`, `_tokens_out`, `_cost`) captured at orchestrator boundaries via `before = tracker.total(); after = tracker.total()`. Side benefit: fixed pre-existing CSV bug where every row carried the last-section's broken counters.
- **2 (`e017546`)** — collapse `run_layer3` (CMR) + `run_layer3_cfr` (CFR) into one `run_layer3(source, ...)` driven by module-level `LAYER3_CONFIG` dict (per-source: `prompt_name`, `results_header`, `fallback_extras`). Persistence keys `_layer3` / `_layer3_cfr` preserved for `report.py` compat. Converge `extract_json` signature with QC's pattern: `fallback: dict | None = None`; each callsite passes its own shape. Closed a latent L0 bug: prior fallback returned `{classification, confidence, note}` to a layer whose prompt schema is `{label, reason}`; downstream shim was patching the mismatch (deleted). Trivial collapse of `query_cmr` + `query_cfr` into `query_source(source, ...)`.
- **3 (`81fc5a2`)** — separate L2 search budget from turn budget. New `[comparator] max_searches = 10` config key; `max_turns = max_searches + 5` formula in code (15 turns total — same as prior hardcoded value, just decomposed). `search_olg` is capped; `lookup_fns_section` is uncapped (deterministic lookup, not fuzzy retrieval). Budget exhaustion returns "finalize now" tool result rather than terminating, mirroring QC's judge pattern. Up-front "You have N searches available" hint in user message; `[N searches remaining]` running counter appended to each successful search response. Bug fix: full-loop exhaustion previously returned `searches_performed: max_turns` (= 15) — now reflects the real counter.
- **4 (`b363f50`)** — tail cleanup: orphan sweep clean (zero true orphans across sub-steps 1-3); remove dead `confidence` field from L3 fallbacks (no consumer reads it); rewrite module docstring (was claiming Sonnet, actually Haiku via API engine — describes both engines + L3 parameterization + search-budget separation now); fix `report.py` docstring path (was pre-restructure `agents/report.py`); remove dead `queries_per_section` config key (zero references); dedupe `fns_chapters_to_compare` (3 reads → 1 via `_resolve_chapters` helper) and `anthropic_api_key` (2 reads → 1 via `_make_anthropic_client` helper).

**Latent bugs fixed during the migration** (worth knowing for anyone diffing pre/post-migration outputs):
- Pre-migration CSV per-row `tokens_in` / `tokens_out` / `est_cost` columns showed the *last-section's* values for every row — `reset_section()` was inside per-section loops but `build_csv_row` ran in a separate later pass. Post-migration values are per-row-accurate. (sub-step 1)
- L0 `extract_json` fallback returned `{"classification": ...}` to a layer whose prompt schema is `{"label": ...}`. Silent failure mode; downstream shim was patching the mismatch. (sub-step 2)
- `searches_performed` field on full-loop-exhaustion rows was the constant `max_turns` (= 15), not a real measurement. (sub-step 3)

**Behavior change watch-items captured**:
- **Parallel-L2 per-section diff race** — the `before = tracker.total(); ...; after = tracker.total()` pattern for per-section attribution is no worse than the prior `tracker.record` race. Aggregate cost remains correct at any `--parallel`. Per-section L2 token diffs may be slightly off when `--parallel > 1`. Acceptable; not worth resolving in cleanup.
- **Budget-aware Claude searches more thoroughly** — same section, same model, same prompt: 7 searches without budget hint (sub-step 2 baseline) → 10 searches with the up-front hint + `[N remaining]` running counter (sub-step 3). Could be helpful prompting eliciting more thorough investigation, or pacing pressure padding the count. Watch the average `searches_performed` trend.
- **`max_searches = 10` calibrated against section 980** — at `2`, returns `partial_match`; at `10`, returns `confirmed_gap`. Use 980 as the regression test if anyone proposes changing it.

**Config to add to fresh checkouts** (config.ini gitignored):
```ini
[comparator]
max_searches = 10
```
The orchestrator falls back to `10` when the key is missing, so fresh checkouts work without the explicit line — but adding it makes the budget visible at the config layer.

**Open items NOT addressed in cleanup arc** (deferrable, audit findings):
- F10/F11 (`report.py` methodology footer omits CFR; says L2 is Claude Code only) — categorized as CFR rollout follow-up per 2026-05-06 decisions, not architectural drift
- F19 (layer-model `fallback=` policy inconsistency) — premature-flexibility cleanup, separate pass
- F22 (all four `layer{0-3}_model` keys point to Haiku) — same
- F23 (`layer0_model` ordering in config.ini) — cosmetic
- F12-F17 (`report.py` findings) — separate report.py cleanup arc

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

1. **Delete CLI pipeline** (`analyze_csv` L1396-1594, `save_checkpoint`/`load_checkpoint` L358-375, `--resume` flag, `if __name__` CLI). Phased pipeline is canonical (decided 2026-05-05). **Plus**: move legacy CLI artifacts at top of `output/qc_analysis/` to `Deprecated/`.
2. **Parameterize cross-checks** — F2 sketch already in QC notes. Three `run_X_check` functions → one `run_source_check(source, ...)`. UI route `/qc/source_check/{source}` replaces three routes (F16).
3. **Fold judge trace into per-finding JSON** (decisions #8 + #11). Single `row_NNN.json` holds extractor / seed_results / judge_result / `judge_trace` array / cross_checks. No separate JSONL files. User reads these to tune prompts — trace and result belong together.
4. **Cross-check query benchmark (F10)** — small experiment, deferred to after structural cleanup.
5. **CSV output redesign (F15 / CA-7)** — out of scope, separate work item.

New actions from cross-app extractions:

6. Import `tools/retry.py`; wrap extractor + judge + parameterized cross-check. Drop handcrafted retries.
7. Import `tools/cost_tracker.py`; replace MODEL_PRICING + CostTracker with parameterized Tracker.
8. Import `tools/result_formatters.py`; drop `format_olg_results_for_prompt` and `_format_source_results_for_prompt`.
9. Import `tools/policy_tools.py`; drop inline `SEARCH_OLG_TOOL`.
10. Update QC's judge result shape to mirror synthesis's `error` field convention (parallel to synthesis F11 fix).
11. Docstring sweep (F4) — replace "Two-call architecture" with the actual phased shape.
12. Document max_turns = max_searches + 5 formula (F11) in a one-line comment.

QC-specific architecture refinements (decisions #9, #10, #11 — added 2026-05-07):

13. **Per-source program filters via config** (decision #9). Replaces the original "drop CFR program=SNAP filter" framing. `[qc_analyzer]` gains explicit `{source}_include` / `{source}_exclude` keys for OLG/CMR/CFR/FNS. Both lists in config so all available programs are visible without guessing. Cross-checks AND seed-search AND judge tool calls all honor these filters. Cross-cutting principle reframed: *filtering is allowed; what's banned is silent filtering*. Explicit visible filters honor the principle.
14. **UI filter panel** — collapsed-by-default summary at top of QC tab ("OLG: 10 of 16 programs · CMR: 4 of 5 · CFR: 5 of 6 · FNS: all (2)"), expandable to show full include/exclude lists. Visibility without clutter.
15. **Per-run analysis folders** (decision #10). `output/qc_analysis/{analysis_name}_{YYYY-MM-DD_HHMM}/` — new folder per upload, reruns within stay in-place. Files inside simply named.
16. **`meta.json` gains `filter_snapshot`** — captures which programs were active at run time, so future audit can answer "what scope was this analysis?"

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

**Status (2026-05-12)**: in progress; user pulled author ahead of search. Three sub-steps using Shape 1 (research → draft → tail).

**Current state has changed since the 2026-05-06 audit**:
- Phase 1 (Research) is now **dual-engine**: `[author] research_engine` ∈ {`claude-code` (default), `api`}. Claude Code path lives in `programs/author/research_claude_code.py` (230 lines, added between audit and migration start).
- **4 hand-rolled `.bat` launchers** instead of 2: `launch_draft`, `launch_resume`, `run_research_claude_code`, `launch_research_resume`. None use `tools/claude_code_runner.py`.
- **6 shared scratch files** in `DATA_DIR` (was 3): `.draft_prompt.md`, `.run_draft.bat`, `.run_resume.bat`, `.research_prompt.md`, `.run_research.bat`, `.run_research_resume.bat`. Race-prone footprint doubled.
- `SynthesisResult.error` handling **already wired** for the API research path (raises). UI routes still bare-handed.

**Decisions taken 2026-05-12** (D1–D4 + bundled QC fix):

- **D1**: Extend `tools/claude_code_runner.py` with toggle parameters rather than build a separate helper. New params: `session_id: str | None` (passes `--session-id <uuid>`), `initial_msg: str | None` (short command-line message vs `@prompt_file` pattern), `wait_for_result: bool = True` (False = fire-and-forget, no `result_file` polling), `title: str | None` (window title). Existing comparator L2 and QC judge call sites unchanged (defaults preserve current behavior).
- **D2**: Research program-filter UI is user-controlled (matches Ask tab), not opinionated. Per-source program checkboxes in `partials/author_prompt_editor.html` (research branch). Selection persists to `meta.json` per version so reruns and audit can see the scope used.
- **D3**: For the CC research engine, program filter is enforced at the `rag/query.py` level via an `OLG_PROGRAMS` env var (or similarly named — reuses the captured QC fix mechanism). Agent shells out to `query.py` from inside the loop; env var is read in the subprocess at import time so the agent cannot broaden past the configured whitelist. API engine passes filter through `run_synthesis` params (existing plumbing).
- **D4**: Sub-step shape is research → draft → tail.
- **Bundled (D5)**: QC B1 filter-leak fix lands as part of this arc. Same `rag/query.py` touch enforces the filter for QC's Claude Code judge spawn site too. Closes `qc_olg_program_filter_leak.md`. Same code; ~3 extra lines at the QC spawn site.

**Sub-step plan (Shape 1)**:

1. **Sub-step 1 — Research migration (both engines)**
   - Extend `tools/claude_code_runner.py` with the D1 toggles. Existing call sites unchanged.
   - Add `OLG_PROGRAMS` env-var enforcement to `rag/query.py` at import (D3 mechanism). One env var, hard intersection with `--program` / `--exclude-programs` agent flags.
   - Migrate `run_research_claude_code` + `launch_research_resume` to call the extended runner. Drop `.research_prompt.md` / `.run_research.bat` / `.run_research_resume.bat` scratch files (replaced by runner's per-call paths).
   - Wire per-source program filter UI into research: form param `programs_by_source` on `/author/{name}/research/run`, checkboxes in `partials/author_prompt_editor.html` (research branch) iterating `SOURCES` + `PROGRAM_REGISTRY`. Persist to `meta.json`. API path passes through `run_synthesis(programs_by_source=...)`; CC path sets the env var at spawn.
   - Apply QC B1 fix: bake active include-list into `qc_judge_claude_code.md` prompt template (UX) and set env var at the QC judge spawn site in `qc_analyzer.py`. Drop "you may also pass" wording.
   - `try/except` on `/author/{name}/research/run` and `/author/{name}/research/{num}/resume` — render error partial on failure.

2. **Sub-step 2 — Draft migration**
   - Migrate `launch_draft` + `launch_resume` to call the extended runner (same toggles).
   - Drop `.draft_prompt.md` / `.run_draft.bat` / `.run_resume.bat` scratch files.
   - Dedupe Author's Notes guidance (F13): keep canonical version in `programs/author/prompts/author_draft.md`; remove inline append in `compose_draft_prompt`.
   - `try/except` on `/author/{name}/drafts/run` and `/author/{name}/drafts/{num}/resume`.

3. **Sub-step 3 — Tail cleanup**
   - Delete the CLI entirely (decision #6): `main()` function, argparse setup, all CLI flags. Update README references.
   - Wire or remove dead `claude_code_timeout` config (F15) — likely wire through to `run_claude_task(timeout=...)` now that the runner is the canonical launcher.
   - `try/except` on `/author/{name}/formats/run`.
   - Docstring sweep across `author.py`, `research_claude_code.py`, `tools/claude_code_runner.py` (runner gains new param docs).
   - Orphan sweep (any helpers stranded by sub-steps 1–2).

**Deferred for author**:
- F5/F6 (partial consolidation) — feature-shaped, not pure cleanup
- F11 (JSON data endpoints replacing HTML-parsing JS) — feature-shaped
- F4 route try/except is applied opportunistically per sub-step (research routes in sub-step 1, draft routes in sub-step 2, format route in sub-step 3) rather than as its own sub-step

## Decisions resolved

8 decisions resolved 2026-05-06; 3 more 2026-05-07 (refinements during the QC architecture pass). Build phase has no remaining design ambiguity.

| # | Date | Decision | Resolution |
|---|---|---|---|
| 1 | 2026-05-06 | `init_clients()` startup failure policy | **Degrade gracefully**. UI starts with a banner explaining limited functionality; user can use whatever services initialized successfully. |
| 2 | 2026-05-06 | Failure signal on `SynthesisResult` | **Add `error: str \| None`**. On success: `error=None`. On failure: `error` holds message, `answer` empty. Caller checks `if result.error:` to branch. |
| 3 | 2026-05-06 | Unknown-model pricing fallback (F30) | **Warn loudly + use Sonnet rates + flag as estimated**. Don't halt work. Warning includes file path + Anthropic pricing URL to guide manual update. Follow-up: `python tools/cost_tracker.py --check` CLI helper that scans config and reports models missing from `MODEL_PRICING`. |
| 4 | 2026-05-06 | QC F6 cross-check program filter | **No silent filtering anywhere — cross-cutting principle**. Filtering, when it happens, is *explicit and visible* — see decision #9 for the QC implementation. Original framing was "drop CFR program=SNAP filter"; superseded by decision #9 which adds explicit per-source filtering to *all* QC sources via config + UI panel. |
| 5 | 2026-05-06 | Kill search F2 vestigial endpoint? | **Yes, kill**. Delete `/search` route, `ui/search.py:do_search`, `ui/search.py:_clients` eager cache, `init_clients()` eager wiring. Synthesis's lazy cache becomes the only cache. F3 vestigial result_card partial also goes. CA-11 collapses to nothing. |
| 6 | 2026-05-06 | Author CLI/UI parity | **Delete the CLI entirely**. No headless usage in practice; UI is the only user path. Removes the source of CLI/UI drift. If a batch-run need ever surfaces, rebuild a thin shim against whatever the code looks like then. |
| 7 | 2026-05-06 | Shared OLG tool description wording (CA-9) | **Tool description stays neutral**; per-app intent lives in prompts. Tool description: factual ("Search the DTA Online Guide for policy and procedures relevant to SNAP, TAFDC, and EAEDC"). QC's prompt emphasizes procedures (where the user specializes); comparator's emphasizes policy gaps. Decoupling tool description from caller intent. |
| 8 | 2026-05-06 | TraceLogger disposition | **Move to phased pipeline** — refined by decision #11 to "fold into per-finding JSON instead of separate JSONL." With CLI deleted, judge trace fires during UI Investigate runs and is captured as the `judge_trace` field on `row_NNN.json`. |
| 9 | 2026-05-07 | QC program filter implementation | **Explicit per-source filters via config**. `[qc_analyzer]` gains `olg_include`/`olg_exclude`/`cmr_include`/`cmr_exclude`/`cfr_include`/`cfr_exclude`/`fns_include`/`fns_exclude` keys. Both included AND excluded lists shown so all available programs are visible at the config layer (no guessing). UI surfaces a collapsible "Active filters" panel at the top of the QC tab — collapsed by default, expandable. Reasoning: QC is a SNAP-only application by design. Hard-coded scoping is *opinionated, not silent* — visible in config + UI = principle honored. Specific lists locked in (see "QC migration sub-steps" sub-step 5). |
| 10 | 2026-05-07 | QC analysis folder layout | **Per-run timestamped folders**. `output/qc_analysis/{analysis_name}_{YYYY-MM-DD_HHMM}/`. Each upload spawns a new folder; reruns of phases stay in-place within that folder. Files inside simply named (`upload.csv`, `meta.json`, `summary.csv`, `results/row_NNN.json`) — folder name carries the context. ISO-style timestamp because it sorts chronologically by default. New folder per upload prevents silent overwrites; `meta.json` gains `filter_snapshot` field so future audit can reconstruct what scope a run used. |
| 11 | 2026-05-07 | Judge trace storage | **Fold `judge_trace` into `row_NNN.json`** as an array of turn entries. No separate `traces/*.jsonl` files. Single file per finding holds extractor / seed_results / judge_result / judge_trace / cross_checks. Reasoning: user actively reads finding JSONs to tune prompts; trace and result belong together. Downstream consumers (cross-checks, summary CSV) read named keys, so the new field doesn't disturb them. |

## Cross-cutting principles surfaced during decisions

- **Filtering is allowed; silent filtering is not** (from decisions #4 and #9). Refined 2026-05-07: opinionated scoping is fine when it matches an app's purpose (e.g., QC is a SNAP-only analyzer, so excluding TAFDC/EAEDC content is intentional, not negligence). What's banned is *invisible* filtering. Filters must be visible at the config layer (both included and excluded lists shown — no guessing) AND surfaced in the UI (read-only panel showing active scope). Apps with broader scope (search, author) keep user-controlled per-source filter UI in their futures.
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
8. ✅ **QC migration** — DONE 2026-05-07. 5 sub-steps, 8 commits, `qc_analyzer.py` 1,658 → 992 lines.
9. ✅ **Comparator migration** — DONE 2026-05-07. 4 sub-steps, `comparator.py` 1,757 → 1,700 lines.
10. **Author migration** ← NEXT (2026-05-12, surface grew since audit — see Author target-state section). 3 sub-steps: research → draft → tail. Extends `tools/claude_code_runner.py` with toggle params; adds env-var program-filter enforcement to `rag/query.py`; bundles QC B1 filter-leak fix at the same `query.py` touch.
11. **Search migration**: CA-14 history persistence + F2 kill + (`/ask` error handling already done in step 4) + F5/B1 CFR template fix + decision #1 (`init_clients` degrade-gracefully banner).
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
