# Synthesis Review — Cross-App Observations

Working document for observations about how each app interacts (or fails to interact) with `tools/synthesis.py`. Created 2026-05-06 as scaffolding for the eventual full synthesis audit.

## Why this doc exists

Synthesis is **not an app** — it's a tool/library that apps consume. It will get its own full audit pass, but in the meantime each app's audit reveals something about synthesis's shape and reach. Rather than scattering those observations across app-specific notes (where they'd be hard to assemble later), they collect here.

When the synthesis audit happens, this doc is the input — every observation here should already have a citation back to which app's audit surfaced it.

## What synthesis does (factual summary)

`tools/synthesis.py` is a 650-line module providing one public entry point:

```python
run_synthesis(question, sources, programs_by_source, program, exclude_programs,
              deep, max_searches, prompt_name, config_overrides) -> SynthesisResult
```

Two modes:

- **Standard** (`run_standard`, L258-327): pre-fetches results from each requested source, single Claude call to synthesize an answer.
- **Deep** (`run_deep`, L334-535): pre-fetches initial results, then runs an agentic tool-use loop with a single `search_policy` tool whose `source` enum is restricted to the requested sources. Configurable max-search budget; `max_turns = 15` hardcoded.

Both modes return a `SynthesisResult` dataclass (markdown answer + accumulated evidence + cost + duration + searches log).

Other API surface:
- `SEARCH_POLICY_TOOL` — single tool definition shared with deep mode
- `format_results_for_prompt(results, source)` — unified per-source formatter (handles olg/cmr/fns/cfr in one function with `if/elif` dispatch)
- `MODEL_PRICING` dict + `calculate_cost()` function
- `do_search()` thin wrapper around `rag/query.py`'s `search_with_client`
- `_search_clients` module-level cache of per-source ChromaDB clients
- `load_config()`, `load_prompt()` helpers

## Per-app observations

### Comparator (audit in progress 2026-05-06)

#### Direct usage

**Comparator does not call into synthesis at all.** Verified during comparator audit (layer mapping table in `comparator_cleanup/README.md` — every Anthropic call is hand-rolled from the SDK; `tools/synthesis.py` is never imported).

#### Why comparator doesn't use synthesis (analysis)

Three reasons synthesis isn't shaped to serve comparator's needs as it currently exists:

1. **Comparator L2 needs multi-tool agentic loops.** L2's tool list is `search_olg` + `lookup_fns_section` (the lookup tool fetches a specific FNS section by number — not a search). Synthesis's `run_deep` exposes exactly one tool (`search_policy`). To absorb L2, synthesis would need to accept a caller-provided tool list, including non-search tools. That's a substantive shape change to a function that today is purpose-fit for "human asks a policy question, synthesis answers."

2. **Comparator returns structured JSON, not markdown.** Every layer (L0/L1/L2/L3) parses the model's response with `extract_json()` into a strict shape (`{classification, confidence, note, ...}`). Synthesis returns raw markdown. Adding structured-output extraction to synthesis means either a parameter for "result schema/extractor" (which bloats the API) or a separate function (which means duplication anyway).

3. **Comparator has engine routing (API vs Claude Code).** L2 dispatches to `run_layer2` (API) or `run_layer2_claude_code` (subprocess) based on `--engine`, with a shared file cache between them. Synthesis is API-only. Engine routing would be a third dimension on top of multi-tool and structured output.

**What synthesis would need to grow** to absorb comparator L2: caller-supplied tool list, optional structured-output extractor, optional engine routing. At that point synthesis is no longer "the human-Ask helper" — it's a generic agentic-search-loop primitive. This is exactly the A2 vs A1 choice flagged in QC notes, restated from comparator's angle.

#### What comparator could borrow if synthesis grew (or if shared utilities were extracted)

Even without consolidating L2 into synthesis's loop, comparator has clear duplicates that synthesis already has cleaner versions of:

- **`format_results_for_prompt(results, source)` (synthesis L124-210)** — synthesis has *one* dispatcher that handles all four sources. Comparator has four separate functions (`format_olg_results_for_prompt`, `format_cmr_results_for_prompt`, `format_fns_for_prompt`, `format_cfr_results_for_prompt`). Synthesis's shape is the candidate canonical form.
- **`MODEL_PRICING` (synthesis L36-40)** — synthesis has the **correct** Haiku 4.5 rates (`$1.00/$5.00`); comparator's `PRICING` dict has stale Haiku 3.5 rates carried against the new model ID (`$0.80/$4.00`, comparator B1). If a shared pricing module emerges, synthesis's values are the source of truth.
- **`load_config` / `load_prompt`** — same shape across the three modules. Synthesis's `load_prompt` reads from `prompts/` (project-shared); comparator's reads from `programs/comparator/prompts/` (app-local). Any shared helper needs to support both project-shared and app-local prompts.
- **`do_search()` wrapper + `_search_clients` module cache** — synthesis caches search clients across calls in a module-level dict (L226-233). Comparator builds clients once at run start in `run_comparison` and threads them through call args. **Synthesis's cache is more reusable for an agent-loop callsite; comparator's explicit threading is more testable.** Different tradeoffs, both defensible — just worth noting that the pattern diverges.

#### Where comparator pre-fetches differently from synthesis

Synthesis pre-fetches results *per source* before the loop starts (L283-296 standard, L361-374 deep) and includes them in the user message as "Initial Search Results."

Comparator pre-fetches via L1 (`run_layer1`, L609-637) which itself does an OLG search and a Haiku triage, then passes those `olg_results` into L2 via `investigate_section`. So comparator's "pre-fetch" is more elaborate — it's a separate Haiku call that classifies the section before deciding whether L2 should even run. Synthesis has no analog to "decide whether to deep-investigate based on a triage" — every Ask-tab question gets the same treatment.

This is **not drift**, it's a domain difference: comparator processes ~70 sections per FNS chapter and L1 triage saves L2 investigation cost on ~half of them. Synthesis serves one human question at a time and the cost ratio doesn't justify a triage step.

#### Retry / error handling comparison (preliminary, full pass during comparator deep findings)

Synthesis's `run_deep` has explicit retry on `RateLimitError`: one retry after `time.sleep(60)`, then return failure (L412-448). Comparator's L2 API retry behavior hasn't been catalogued yet — flagged for the comparator deep-findings pass. Worth confirming whether comparator matches synthesis's pattern, diverges, or has no retry at all (which would be a finding).

#### Implications for A1/A2/B

The comparator dip's biggest A1/A2/B-relevant takeaway:

- **A1 (extend `run_synthesis()` with new params)** is structurally feasible — synthesis already has `prompt_name` and `config_overrides`, so adding `tools=[...]`, `result_extractor=...`, `engine="api"|"claude-code"` is mechanically straightforward — **but it would clearly bloat synthesis past its current job**. The signature would have ~13 parameters, and the new params would be unused for every Ask-tab call. This is the "wrong-shaped abstraction" objection from QC notes, made concrete.

- **A2 (extract shared `agentic_search_loop` primitive)** stays the most-defensible option, but the multi-tool + structured-output + engine-routing requirements mean the primitive will be **substantively bigger than just QC's loop with a few parameters**. Worth confirming during the cross-app comparison pass whether A2's value still beats B once we've sized the primitive honestly.

- **B (factor only duplicates)** has more value than QC's analysis suggested. The cleanest factorings — `format_results_for_prompt`, `MODEL_PRICING`, `load_config`/`load_prompt`, possibly retry-with-rate-limit — solve real cross-app duplication without requiring the agentic loops to share code at all. **B partially funded** could be a respectable end state even if A2 doesn't pan out.

### QC Analyzer (audit complete)

QC notes (`qc-analyzer_cleanup/README.md`) already establish the synthesis relationship:

- QC's judge loop is **structurally identical to synthesis deep-mode** (their finding #1, side-by-side at qc_analyzer.py:L617-799 vs synthesis.py:L401-535).
- Three blockers prevent collapsing the judge into `run_synthesis()` as-is (QC finding #2): seed-results-as-message-history, strict-JSON output shape, OLG-specific result formatter.
- QC is **API-only**. No Claude Code path. (QC F4; per the architecture principles 2026-05-06 update, this is now treated as a **gap** that becomes feature work, not an intentional design.)

QC's relationship to synthesis is the **strongest evidence for A2** because the structural identity is highest there. Comparator's relationship is more nuanced because of the multi-tool requirement.

### Author (audit complete 2026-05-06)

#### Direct usage

Author's `run_research` (`programs/author/author.py:L78-202`) calls `run_synthesis()` directly with the deepest customization in the codebase:

```python
result = run_synthesis(
    question=question,                 # assignment + optional task_instructions
    sources=sources,                   # default ["olg", "cmr", "fns", "cfr"]
    deep=True,                         # hardcoded
    max_searches=max_searches,         # config-driven (12)
    prompt_name="author_research",     # custom prompt
    config_overrides={                 # per-call overrides
        "model": model,                # config-driven (Sonnet 4.5)
        "max_tokens": max_tokens,      # config-driven (8192)
        "results_per_search": results_per_search,  # config-driven (8)
    },
)
```

**Author exercises 5 of synthesis's 9 parameters**: `question`, `sources`, `deep`, `max_searches`, `prompt_name`, `config_overrides`. (Search uses 4: `question`, `sources`, `programs_by_source`, `deep`.) Together search + author exercise 5 distinct synthesis params; the remaining 4 (`program`, `exclude_programs`, `programs_by_source` for author, lone-parameter `question`) are either legacy or unused-by-author.

**Author is the only caller of `prompt_name`, `config_overrides`, and custom `max_searches` in the entire codebase** (verified). If author goes away, those three synthesis features have zero users.

#### What the author audit revealed about synthesis

The full deep dive is in `author_cleanup/README.md`. Synthesis-relevant takeaways:

- **F18 — Author is the deepest synthesis caller**: 5 of 9 params used; intentionally hardcodes deep=True and prompt_name (not user-tunable). This is correct design — research's prompt and budgets are part of the system, not the user's choice. Confirms synthesis's flexible-param shape is justified by author specifically.

- **F19 — Author's `evidence.json` is the canonical SynthesisResult-on-disk pattern**: persists `search_queries`, `model`, `tokens` (input/output dict), `cost`, `duration_seconds`, and full `evidence` (rank, score, text, metadata, id per result). This is what search NS1 says search's `save_search` should do but doesn't. **Synthesis-cleanup direction**: search adopts author's pattern. New CA-14 in `cross_app_findings.md`.

- **F2 — Author's research uses NO program filter**: hardcodes `["olg","cmr","fns","cfr"]` in five layers (function default, route default, two template fallbacks, JS hardcode). For SNAP-specific assignments, surfaces TAFDC/EAEDC noise. The Ask tab exposes per-source program checkboxes via `PROGRAM_REGISTRY`; author does not. Synthesis supports `programs_by_source`; author doesn't pass it. Connects to the deferred per-source program filter UI work.

- **F1 — Author hand-rolls Claude Code subprocess** (Phase 2 draft): writes .bat files + subprocess.Popen with CREATE_NEW_CONSOLE, instead of using `tools/claude_code_runner.py`. Comparator imports the canonical wrapper; author bypasses it. **Two independent Claude Code subprocess implementations** in the codebase. New CA-13 in `cross_app_findings.md`. Not a synthesis concern, but worth flagging because author's three-engine routing (synthesis / Claude Code / pure Python) is the canonical engine-routing example, and the Claude Code engine is currently implemented twice.

- **No synthesis bugs surfaced**: `run_synthesis` works correctly for author; deep mode performs well within the 12-search budget; `prompt_name="author_research"` resolves correctly to `prompts/author_research.md` (the project-shared location); `config_overrides` is correctly passed through and applied per-call.

#### What synthesis would need to grow to absorb author's draft phase (F1 cross-cut)

Author's Phase 2 (Draft) currently runs Claude Code in a visible terminal — interactive, session-resumable, $0 on subscription. Synthesis is API-only.

If a future "extend synthesis to support Claude Code engine" lands (per architecture principles, this is a separate deferred decision), author's Phase 2 *could* potentially become a synthesis call with `engine="claude-code"` + a custom prompt. But:

1. **Author's Draft phase is not search-shaped**: it doesn't ask a question and get a markdown answer; it writes a file (`draft.md`) based on extensive context (assignment + research + style guide).
2. **The visible-terminal pattern is intentional** (F25): the user owns the terminal, can interject, can resume. Synthesis's deep mode is a one-shot inference — different shape.
3. **Author's Draft uses Claude Code's tool-use loop autonomously**: the Claude Code session can run additional `python rag/query.py` invocations during drafting. Synthesis could in principle wrap this, but the value of the visible terminal vs a synthesis call is the user's ability to *intervene*.

**Conclusion**: Phase 2 should stay engine-routed-as-Claude-Code, and the cleanup direction is CA-13 (extract Claude Code subprocess to a shared wrapper) — *not* extending synthesis to absorb it. Author's three-engine pattern is the canonical engine-routing example; synthesis doesn't need to absorb non-synthesis engines.

#### Implications for A1/A2/B (reaffirmed)

Author audit **reaffirms B**:

- **Synthesis is structurally healthy.** The two apps that use synthesis (search and author) get good outcomes. Author specifically validates synthesis's flexible param shape — the customization API author needs (custom prompt, custom model/max_tokens, custom max_searches) is exactly what `prompt_name` + `config_overrides` provide.

- **Drift is in QC and comparator drifting from synthesis's idioms**, not in synthesis being the wrong shape. Author and search already converge on synthesis's pattern.

- **The cleanest cross-app cleanup direction**: pull QC and comparator toward synthesis's idioms via the helper extractions (CA-1, CA-3, CA-8, CA-9). Search and author already align — they just need the duplicate-helpers cleanup that B funds.

The data point author adds: **synthesis's customization surface (prompt_name + config_overrides + max_searches) is justified by exactly one caller** — author. That's enough to keep it. If A2 ever becomes attractive, the primitive must absorb the same customization shape, since author's customization is real and not collapsible to defaults.

#### Author's pattern as a template for future synthesis callers

Any future agentic or RAG-driven app should follow author's pattern:
1. Use `run_synthesis(prompt_name=..., config_overrides=..., deep=True, max_searches=...)` for the structured-research phase
2. Persist the full SynthesisResult to disk in author's `evidence.json` shape — including `search_queries`
3. Use the appropriate engine per phase: API for structured/cheap, Claude Code for agentic/interactive, pure Python for deterministic transforms
4. Keep agentic loops separate (per A1/A2/B option B) — extract only the duplicates

The **prompt-location convention** author follows (per F17): project-shared `prompts/` for the synthesis-prompt, app-local `programs/{app}/prompts/` for app-specific Claude Code prompts. This is the right convention for any synthesis caller that ships a custom prompt.

#### Open questions surfaced (input to eventual full synthesis audit)

- **`prompt_name` is loaded by `tools/synthesis.py:load_prompt`** — does it correctly handle the project-shared location? (Yes, verified — author works.) But the path resolution is implicit. Cleanup: explicit doc on which prompt-name resolves where.
- **`config_overrides` accepts arbitrary keys**: author uses `model`, `max_tokens`, `results_per_search`. What other keys does synthesis honor? Is the contract documented? (Spot check: read synthesis to confirm the override-resolution logic at the eventual synthesis audit.)
- **`max_searches` separately from config_overrides?** Author passes `max_searches=12` as a top-level kwarg, while `results_per_search` goes in `config_overrides`. Why the asymmetry? Probably accidental — both should pick the same convention. Worth aligning during synthesis audit.

### Search / Ask tab (audit complete 2026-05-06)

#### Direct usage

Search is the **canonical synthesis caller** — `/ask` POST handler at `app.py:L141-147` calls `run_synthesis(question, sources, programs_by_source, deep)` directly. No other apps in the codebase call `run_synthesis()` (verified). Search exposes 4 of synthesis's 9 parameters; full mapping in `search_cleanup/README.md` "Synthesis-interaction findings" section.

#### What the search audit revealed about synthesis (NS1-NS9)

The full deep dive is in `search_cleanup/README.md`. Summary of synthesis-relevant findings:

- **NS1 — `search_queries` is a provenance leak.** Synthesis returns `SynthesisResult.search_queries` (the list of queries Claude actually ran). Search shows the **count** in answer.html and **does not persist it** in SQLite. Especially impactful in deep mode where Claude runs up to 8 iterative searches. The data is there; nobody surfaces it. **First synthesis-audit fix candidate** because synthesis already produces it correctly.

- **NS2 — `do_search` signatures mismatch between `ui/search.py` and `tools/synthesis.py`.** Same name, reversed positional args (`query, source` vs `source, query`). search.py exposes `threshold` parameter; synthesis.py hardcodes it to 0.0 internally. Both call `search_with_client`. Cross-app **CA-N** candidate; consolidation needs to pick a signature.

- **NS3 — `ui/search.py:_clients` (eager) is dead for the canonical /ask path.** Synthesis's lazy `_search_clients` cache is what gets populated when /ask runs. The eager init at app startup decorates a cache the canonical path never reads. **This is significant for the synthesis audit**: synthesis's lazy cache vs UI's eager cache aren't competing implementations — UI's is dead-wired. Either drop UI's (if F2 vestigial endpoint dies) or share a cache via dep injection or `rag/query.py`.

- **NS5 — Deep-mode evidence accumulation has no dedup.** `all_evidence[source].extend(results)` per iteration (synthesis.py:L489-491). Deep mode with 8 searches × 5 results = up to 40 evidence cards rendered, possibly duplicate chunks scored differently. Worth a dedup-by-id step.

- **NS6 — `run_standard` has no retry; `run_deep` does.** The standard path is bare-handed despite being the default. Standard rate-limit hit → uncaught exception → `/ask` returns 500. Asymmetric reliability **within synthesis itself**. Feeds CA-8.

- **NS7 — Deep-mode error path returns a "fake answer" with the error message in `answer` field.** No way for callers to distinguish success from failure in `SynthesisResult`. Search renders the error as a normal answer card and **persists it to history**. Needs a `success: bool` or `error: str | None` field. Same anti-pattern as comparator F25.

- **NS8 — `max_turns = 15` hardcoded.** Same magic number as comparator's L2 hardcoded 15 (CA-10). QC uses `max_searches + 5` formula. Should be config-tunable.

- **NS9 — `_search_clients` is module-level mutable state.** Threadsafe? Used by FastAPI threadpool. Low-impact in practice (single user) but worth flagging during the full synthesis audit.

#### Implications for A1/A2/B (refined)

The search audit **flips the framing** on whether synthesis is portable. Before, the question was "should other apps use synthesis?" Now it's clearer:

**Synthesis is the cleanest of the three agentic-loop apps.** The drift is mostly QC and comparator duplicating what synthesis has cleaner versions of:

| Helper / pattern | Synthesis | Comparator | QC |
|---|---|---|---|
| `format_results_for_prompt` | ✅ unified dispatcher | ❌ four separate fns | ❌ OLG-specific |
| `MODEL_PRICING` | ✅ correct rates | ❌ wrong rates (B1) | ✅ correct rates |
| Retry on `RateLimitError` | ✅ in deep mode (NS6 in standard) | ❌ zero anywhere | 🟡 mixed |
| Search/turn budget split | ✅ separate caps | ❌ turn-only | 🟡 formula |
| Single-tool agentic loop | ✅ shipped | ❌ two tools (L2) | ✅ single-tool |

**A1 (extend run_synthesis) bloats it badly** — adding `tools=[...]`, `result_extractor=...`, `engine="api"|"claude-code"`, `seed_results=[...]` turns a 9-param function into a 13-param function with most new params unused for /ask. **Wrong-shaped abstraction confirmed.**

**A2 (extract `agentic_search_loop` primitive)** — the primitive must absorb multi-tool, structured-output extractor, engine routing, seed-message-history. Substantial primitive. Worth doing IF the absorbed scope justifies the new module — but synthesis's deep mode is already healthy, so most of A2's value comes from rationalizing comparator + QC, not from changing synthesis.

**B (factor only duplicates) is the realistic answer.** The clear extractions are:
- `tools/llm_helpers.py` → `extract_json`, `MODEL_PRICING`, `calculate_cost`, `format_results_for_prompt`, `SOURCE_LABELS`
- `tools/retry.py` → uniform retry decorator (CA-8)
- `tools/policy_tools.py` → `SEARCH_OLG_TOOL` / `SEARCH_POLICY_TOOL` definitions

**These extractions don't require the agentic loops to share code.** Each app keeps its purpose-fit loop, but they pull from the same helper toolbox. **B "fully funded" delivers ~80% of A2's structural value with a fraction of the change surface.**

A2 stays viable as a longer-term option if a fourth agentic-loop callsite emerges (e.g., a future "compare two policy passages" tool), at which point the case for a shared primitive gets stronger.

#### What synthesis would need to grow to absorb everything

For completeness — what A1 + A2 require synthesis to support:

1. Multi-tool calling (comparator L2)
2. Structured-output extraction (comparator L0/L1/L2/L3, QC judge)
3. Engine routing API ↔ Claude Code (comparator L2)
4. Seed-results injection as message history (QC judge)
5. Custom result formatter per caller (QC's OLG-specific)
6. Custom budget design (comparator's turn-only vs synthesis's split)
7. Custom error-result shape (currently synthesis returns `answer="error: ..."`)

Seven dimensions of caller-specific flexibility. A1 makes synthesis carry all seven. A2 makes a new primitive carry all seven. B punts the question — each app keeps its loop.

Decision input: how many of these seven do we expect to keep customizing per-caller vs converging on a shared default?

## Open questions for the eventual full synthesis audit

- **Module-level state**: `_search_clients` (synthesis L226-233) is a module-level mutable dict that caches ChromaDB clients across calls. Threadsafe? Reset between requests? In the FastAPI UI's threadpool, what guarantees does this make about client lifetime?
- **`max_turns = 15` hardcode** (synthesis L350): why 15? Tunable? Same magic-number question as QC's `max_turns = max_searches + 5` (QC F11).
- **Engine routing for synthesis**: per the architecture principles, every app's API path must remain viable, but the user defaults to Claude Code for agentic work. Should synthesis grow a Claude Code engine for its deep mode? Same question as QC's engine routing decision (now answered: yes, develop a pattern). Synthesis is the natural place to land that pattern first since deep mode is the most generic agentic loop.
- **`run_standard` vs `run_deep` divergence**: the two functions duplicate the pre-fetch-and-format block (L283-296 vs L361-374). Could be a helper.
- **Prompt path resolution**: `load_prompt` reads from `PROMPTS_DIR = PROJECT_ROOT / "prompts"`. Comparator's `load_prompt` reads from `programs/comparator/prompts/`. Different conventions. Project-shared vs app-local prompts is a real distinction; the question is whether the convention should be unified.
- **Outdated CLI docstring** (synthesis L7-11): shows `python agents/synthesis.py "..."` — pre-restructure path. Same docstring drift as comparator F2 and CA-5.

## To do

- ~~Populate **search** section~~ — DONE 2026-05-06.
- ~~Populate **author** section~~ — DONE 2026-05-06.
- ~~Revisit **comparator** section after the comparator deep-findings pass~~ — comparator notes already updated with retry-policy findings (F24 zero retries; CA-8 logged).
- This doc is input for the eventual full synthesis audit; expect to be opened then. **Specific items to investigate during that audit:**
  - NS1 — wire `search_queries` into history persistence (cheapest win) — **search adopts author's `evidence.json` pattern; CA-14 in cross-app findings**
  - NS3 — resolve dead `_clients` cache (search.py vs synthesis.py); decide on dependency injection or shared module
  - NS6 — add retry to `run_standard`
  - NS7 — distinguish error from success in `SynthesisResult` (add `success` or `error` field)
  - NS8 — config-tune `max_turns`
  - NS9 — assess `_search_clients` thread safety
  - **From author audit (2026-05-06)**: confirm `prompt_name` resolution path; document `config_overrides` accepted keys; align `max_searches` placement (top-level kwarg vs `config_overrides` — author uses one of each, asymmetric)
  - **A1/A2/B decision** — **REAFFIRMED (B)** based on cross-app pass + author audit; no further evidence needed unless a fourth agentic-loop callsite emerges
