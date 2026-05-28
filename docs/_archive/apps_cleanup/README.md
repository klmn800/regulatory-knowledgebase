# Apps Cleanup — Charter

## Why we're doing this

Policy Navigator's apps (comparator, author, qc, search) grew fast while we were learning the system. Features got built in waves, each one imitating earlier patterns by hand instead of factoring them out. The result is a working system where:

- The same conceptual operation (e.g., "agentic search loop with a `search_*` tool") is implemented multiple ways across modules
- Helpers like `format_results_for_prompt()` are duplicated across three files
- Some apps reach the RAG directly when they should go through synthesis; others wrap synthesis when a direct call would be simpler
- Deviations from the dominant pattern *exist*, but they aren't **intentional** — they're accidents of when each module was written

Nothing here is broken. Everything works. But the seams show, and the seams will compound as we add more.

## Goal

Revisit each app in turn and make sure it:

1. **Works the way it's supposed to work.** The actual code matches the intended design. No silent behaviors no one remembers adding. No dead branches.
2. **Is structured cleanly.** No drift between files that do similar things. Shared concerns live in shared modules. The layering (RAG → synthesis / loop primitive → app) is respected.
3. **Isn't overengineered.** No premature abstractions. No flags or branches for cases that never happened. No defensive code for impossible states. Three similar lines is better than a wrong abstraction.
4. **Has intentional deviations only.** When an app does something different from the dominant pattern, there should be a stated reason — captured in code, the cleanup notes, or the app's documentation. "Different because it was written first" is not a reason; it's a finding.

## What this is not

- **Not a prompt cleanup.** Prompts will be standardized in a separate effort. Don't conflate.
- **Not a re-architecture.** We are not rewriting from scratch. We are looking, finding the drift, and steering it back.
- **Not a bug hunt.** If we find a bug, we log it; we don't necessarily fix it during this arc.
- **Not a feature pass.** No new capabilities introduced — only existing ones tightened.

## Order

**Audit phase complete** (2026-05-06). All four apps audited (QC, comparator, search, author) plus synthesis. Cross-app findings consolidated. Decision pass complete.

**Execution phase** is laid out in `execution_plan.md`:

1. **Build shared modules** — `tools/retry.py`, `tools/cost_tracker.py`, `tools/result_formatters.py`, `tools/policy_tools.py`. Validated on synthesis first (no behavior change).
2. **QC analyzer** — first migration target. Phased pipeline becomes canonical (CLI deleted), cross-checks parameterized, all four shared modules wired in.
3. **Comparator** — same module imports + B1 cost-rate fix + retry coverage + budget config.
4. **Search (Ask tab)** — history persistence adopts author's evidence shape, vestigial `/search` endpoint killed, `init_clients` degrade-gracefully banner.
5. **Author** — focused 1-2 day cleanup pass: delete CLI, unify Claude Code subprocess via `tools/claude_code_runner.py`, wire program filter into research, dedupe Author's Notes guidance.
6. **Tail** — docstring sweep across all five files; CA-12 progress JS helper; CA-15 conventions docs.

## Architectural principles already set

Captured in Claude's project memory (`memory/architecture_principles.md`). Summary:

- **API-only path stays viable.** Enterprise deployment must work without a Claude Code CLI on the workstation. Don't make Claude Code the only way to do anything important.
- **Claude Code routing earns its keep beyond cost.** Session resumability, agentic exploration, observability are real benefits. Use it where it fits — just don't make it the only path.
- **Formatting helpers belong in a shared layer.** Three near-duplicates exist today across synthesis, comparator, qc.
- **Program-filter design must be reconciled with the chunk-refactor work.** New filter design lands at the same time as consumer calibration, not later.
- **Each app should leave this arc with a stated relationship to RAG / synthesis / loop primitives** — not an accidental one.

## Terminology

The folder `programs/` collides with the chunk metadata field `program` (SNAP, EAEDC, Hearings, ...). In conversation and docs, we use **apps** / **applications** to refer to these modules. Folder rename (`programs/ → apps/`) is deferred to a dedicated task so it doesn't muddy cleanup work with rename churn.

## Working pattern

Each app gets a subfolder under `docs/apps_cleanup/{app}_cleanup/` with a `README.md` that holds:

- **Purpose** — what the app does and what it produces
- **Architectural findings** — drift, duplication, dead code, surprising behaviors
- **Opportunities** — options for fixing each finding, with tradeoffs (we don't pick on first sight)
- **Decisions log** — when we commit to an option, it's recorded here with the date and the reason
- **Bug log** — issues surfaced during review; fixed inline if trivial, deferred otherwise
- **Open questions** — anything we don't know yet

Notes accumulate across sessions. Deletions are rare — we'd rather mark something resolved than lose the trail.

## Audit methodology

Each app gets the same examination pass before any cleanup edits. **Findings, not fixes.** Cleanup decisions come after we've audited enough apps to see cross-cutting patterns. The goal of an audit is to describe state, not propose changes.

### Steps

1. **Module read-through.** Read the main module(s) end-to-end. Note total line count, banner-separated sections, the sequence of pipeline stages. Watch for outdated docstrings — a module's description of itself often lags behind what was added.
2. **Layer mapping.** For each pipeline stage / public function, note which layer it touches:
   - Direct `rag/query.py` calls (`search_with_client`, `create_client`)
   - `tools/synthesis.py` (`run_synthesis`)
   - `tools/claude_code_runner.py` (Claude Code subprocess)
   - Direct Anthropic SDK calls (one-shot or tool-use loop)
   - Something else

   Two stages doing the same conceptual operation through different layers is drift.
3. **UI surface.** Find the templates and routes that expose this app. Map each user action → route → backend function → template partial. Flag redundant routes, duplicated view-vs-run paths, orphaned endpoints.
4. **JS surface.** Read `ui/static/app.js` (or equivalent). Watch for progress text disconnected from backend state, near-duplicate functions (`xRun` / `xRerun`), naming-convention mismatches between backend and UI, `setTimeout` race conditions.
5. **Config audit.** Read the relevant `[section]` in `config.ini`. Compare to every `config.get` / `config.getint` call in the module. Flag missing keys (silent fallbacks), keys that always have the same value (premature flexibility), values that should be config but are hardcoded (model pricing, top-N, retry counts).

### Categorizing findings

Each finding gets a number (`F1`, `F2`, ...) and a category:

- **Drift** — same conceptual operation done two different ways
- **Duplication** — copy-paste between functions or routes
- **Outdated** — docs, comments, or fallbacks that no longer match reality
- **Inconsistency** — different defaults, retry policies, or filters across similar code paths
- **Suspect choice** — a decision that looks accidental; should be confirmed deliberate or fixed
- **Under-design** — a missing capability that's papered over (kept distinct from drift, because the fix is feature work, not cleanup)
- **Bug** — actual incorrectness; logged separately as `B1`, `B2`, ...

Severity tags `[MAJOR]` / `[DOWNGRADED]` / `[RETRACTED]` are reserved for findings that change the cleanup picture; don't tag everything. All findings include file:line citations so a reader can jump straight to the code.

**Keep "feature work" separate from "cleanup work."** Cleanup removes drift, duplication, dead code, inconsistencies. Feature work adds missing capabilities (streaming progress, abort, cost surfacing). Both go in the notes; keep the boundary clear so they don't get conflated when planning.

### What the audit does NOT include

- No proposed fixes — opportunities are listed as options with tradeoffs, not chosen paths
- No empirical runs — those happen when we have specific questions to test
- No prompt review — prompts are a separate cleanup arc
- No code changes

The QC analyzer audit (`qc-analyzer_cleanup/README.md`) is the worked example for this methodology.
