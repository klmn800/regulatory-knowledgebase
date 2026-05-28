# Synthesis — Audit

Working document. Created 2026-05-06 alongside `README.md` (which is the cross-app observation log; this file is the proper audit pass).

This audit follows the 5-step methodology in `../README.md` and produces findings in the same shape as the four app audits. **Findings, not fixes.** Cleanup decisions are tracked in `../cross_app_findings.md` (especially CA-1 / CA-3 / CA-8 / CA-9, whose canonicals all live in synthesis).

## Purpose

`tools/synthesis.py` is the shared library that powers RAG-driven synthesis for two callers:

- **Search** (`/ask` route in `ui/app.py:L141-147`) — human asks a policy question, gets a synthesized markdown answer with citations and accumulated evidence. The canonical caller.
- **Author research phase** (`programs/author/author.py:L126-137`) — assignment + task instructions go in, deep-mode synthesis produces `report.md` and `evidence.json` for the downstream Draft phase.

Synthesis exposes **one public function** (`run_synthesis`) returning a `SynthesisResult` dataclass (markdown answer + accumulated evidence + cost + duration + searches log). Two modes:

- **Standard** — pre-fetch results from each requested source, single Claude call to synthesize.
- **Deep** — pre-fetch initial results, then run an agentic tool-use loop with one `search_policy` tool whose `source` enum is restricted to the requested sources. Configurable max-search budget.

It is also the source of canonical implementations for several cross-app duplicates: `MODEL_PRICING` (CA-1), `format_results_for_prompt` (CA-3), `SEARCH_POLICY_TOOL` (CA-9), and `run_deep`'s rate-limit retry (CA-8).

## File shape (2026-05-06)

`tools/synthesis.py` is a single 650-line module organized into nine banner-separated sections:

1. **Configuration** (L32-59) — `MODEL_PRICING`, `load_config`, `load_prompt`
2. **Result types** (L62-75) — `SynthesisResult` dataclass
3. **Tool definition** (L78-109) — `SEARCH_POLICY_TOOL` (multi-source enum)
4. **Result formatting for prompts** (L112-210) — `SOURCE_LABELS`, `format_results_for_prompt`
5. **Cost tracking** (L213-219) — `calculate_cost`
6. **Search clients** (L222-251) — `_search_clients` cache, `get_search_clients`, `do_search`
7. **Standard mode** (L254-327) — `run_standard`
8. **Deep mode** (L330-535) — `run_deep`
9. **Public API** (L538-588) — `run_synthesis` dispatcher
10. **CLI** (L591-649) — `main`

**Public surface**: `run_synthesis`, `run_standard`, `run_deep`, `do_search`, `get_search_clients`, `format_results_for_prompt`, `calculate_cost`, `MODEL_PRICING`, `SEARCH_POLICY_TOOL`, `SOURCE_LABELS`, `SynthesisResult`, `load_config`, `load_prompt`.

**Layer touchpoints** (step 2 — what does synthesis depend on?):

| Stage | Touches |
|---|---|
| Pre-fetch (run_standard L283-296, run_deep L361-374) | `do_search` → `get_search_clients` → `rag.query.create_client`, `rag.query.search_with_client` |
| Tool-use loop (run_deep L401-507) | Anthropic SDK direct (`client.messages.create` with `tools=`), `do_search` for tool execution |
| Synthesis call (run_standard L305-310) | Anthropic SDK direct (no tools) |
| Cost (L217-219) | None (math) |
| Prompt loading (L49-59) | Filesystem (`prompts/{name}.md`, `prompts/domain_preamble.md`) |

Layering is clean: synthesis sits *between* `rag/query.py` (RAG layer) and the apps. It does not reach into UI templates, app-local code, or Claude Code subprocess. The one shared dependency upstream is the Anthropic SDK; downstream is `rag/query.py`.

## Architectural findings — full list

### F1 [outdated] Module docstring shows pre-restructure CLI path

L7-11:

```
Usage:
    python agents/synthesis.py "What are the income limits for SNAP?"
    python agents/synthesis.py "expedited benefits process" --sources olg cmr
    python agents/synthesis.py "shelter deduction" --deep
```

The `agents/` directory was renamed during the 2026-04-06 restructure; current path is `tools/synthesis.py`. New readers will copy-paste the wrong command. Same drift as comparator F2 / search F1 / qc F4 — bundles into **CA-5**.

### F2 [duplication] Pre-fetch-and-format block is duplicated between run_standard and run_deep

`run_standard` L283-296 and `run_deep` L361-374 are nearly identical 14-line blocks:

```python
for source in sources:
    src_programs = (programs_by_source or {}).get(source)
    print(f"  Searching {SOURCE_LABELS.get(source, source)}...", end="", flush=True)
    response = do_search(source, question, top_n=results_per_search,
                         programs=src_programs,
                         program=program, exclude_programs=exclude_programs)
    all_evidence[source] = response["results"]
    search_queries.append(f"{source}: {question}")

    formatted = format_results_for_prompt(response["results"], source)
    context_parts.append(f"=== {SOURCE_LABELS.get(source, source)} Results ===\n{formatted}")
    print(f" {len(response['results'])} results")
```

Only difference: deep mode wraps the context heading in "Initial Search Results" (L388) vs standard's "Search Results" (L300). A `_prefetch_sources()` helper would replace both blocks.

### F3 [inconsistency, MAJOR] `run_standard` has no retry; `run_deep` has one — within the same module

`run_deep` wraps every `messages.create` in a try/except for `RateLimitError` + `APIError` with 60s sleep + one retry (L401-448). `run_standard`'s `messages.create` at L305-310 is bare-handed. **A rate-limit hit on the default `/ask` path is an uncaught exception → 500 from FastAPI.**

This is one of the synthesis-internal inconsistencies feeding **CA-8** ("retry / rate-limit policies diverge wildly"). NS6 in the README. Synthesis is the canonical for the retry pattern *and* has a hole in its own coverage.

### F4 [suspect choice] `max_turns = 15` hardcoded

L350:

```python
max_turns = 15
```

Not config-tunable; not a constant with a comment explaining the choice. Same magic number as comparator L2's hardcoded 15 (CA-10). QC uses `max_searches + 5` formula. The number is unexplained — is it a buffer for trailing reasoning turns? An empirically tuned value? Unknown without git archaeology. Feeds **CA-10**.

### F5 [bug] Deep-mode error path returns a "fake answer" — no success/error signal on `SynthesisResult`

`SynthesisResult` (L66-75) has no `success` or `error` field. When `run_deep` hits an unrecoverable error (L425-436, L437-448), it returns:

```python
return SynthesisResult(
    answer=f"Synthesis failed due to API error: {e}",
    ...
)
```

The error message is in the `answer` field — same shape as a successful synthesis. **Search renders this as a normal answer card and persists it to history** (search NS7, ui/history.py:L80-98 unconditionally writes). Author's research phase would write the error string into `report.md` and the empty/partial `all_evidence` into `evidence.json` with no signal that the run failed.

NS7 in the README. Same anti-pattern as comparator F25.

### F6 [duplication] Identical APIError handler appears twice in `run_deep`

L425-436 (inside the RateLimit-retry block, after the `time.sleep(60)` retry fails) and L437-448 (outer `except anthropic.APIError`) are byte-identical 12-line blocks: same print, same return-with-error-result, same fields. A nested `try/except` would reduce both to a single handler; alternatively, the retry could be lifted into a helper that's the canonical CA-8 retry primitive.

### F7 [suspect choice] Deep-mode evidence accumulation has no dedup-by-id

L489-491:

```python
if source not in all_evidence:
    all_evidence[source] = []
all_evidence[source].extend(search_response["results"])
```

The pre-fetch (L367) already populated `all_evidence[source]`. Subsequent `extend()` calls during the agentic loop append unconditionally. With 8 deep-mode searches × 5 results, the same chunk can appear ~3-5 times in `all_evidence` (with possibly different scores from different queries). Search renders the unfiltered list (`answer.html` L31-83); author persists it (author.py:L169-179). NS5 in the README.

### F8 [drift] `do_search` signature diverges from `ui/search.py:do_search`

| Aspect | `tools/synthesis.py:236-251` | `ui/search.py:94-120` |
|---|---|---|
| Positional order | `do_search(source, query, ...)` | `do_search(query, source=DEFAULT_SOURCE, ...)` |
| `threshold` | hardcoded to `0.0` | exposed as kwarg, default `0.0` |
| `mode` | not accepted | not accepted |
| Cache used | synthesis's lazy `_search_clients` | UI's eager `_clients` |
| Raises if source unknown | no — `create_client` would | yes — explicit `ValueError` |

Same name, same conceptual op, different shapes. **NS2 in the README; promoted to CA-11 in cross-app findings.**

### F9 [suspect choice] Module-level mutable state with lazy init has theoretical race

L226:

```python
_search_clients = {}

def get_search_clients(source: str) -> dict:
    if source not in _search_clients:
        _search_clients[source] = create_client(source=source)
    return _search_clients[source]
```

In FastAPI's threadpool (`asyncio.to_thread(run_synthesis, ...)`), two concurrent `/ask` requests for the same source on a cold cache could both see `source not in _search_clients` and both invoke `create_client`. Last writer wins; no corruption (dict assign is atomic) but `create_client` runs twice and one client is orphaned. Low impact (single-user system today) but the lock-free init is a latent problem for any future multi-user deployment. **NS9 in the README.**

### F10 [drift] Two parallel client caches; UI's is dead-wired for /ask

`ui/search.py:_clients` is populated eagerly at app startup (`init_clients()` in `ui/app.py:L79`). `tools/synthesis._search_clients` is populated lazily inside `get_search_clients`. The canonical `/ask` path goes `app.py:L141-147` → `run_synthesis` → `synthesis.do_search` → `synthesis._search_clients`. **`ui/search.py:_clients` is consulted only by `ui/search.py:do_search`, which is called only by `/search` (the raw-search power-user route, search F2 vestigial)** and not by /ask. **NS3 in the README; CA-11 cross-app.**

### F11 [under-design] No `success` / `error` field on `SynthesisResult` (parent of F5)

Beyond the deep-mode "fake answer" anti-pattern (F5), the dataclass at L66-75 has no signal field at all. Callers cannot distinguish:

- Successful synthesis with empty results (legitimate "no coverage" answer)
- Empty-context synthesis (model hallucinated, search returned nothing useful)
- Max-turns-exhausted synthesis (L526-535: returns whatever `answer_text` happened to be set, or the literal string "Analysis incomplete — maximum turns reached.")
- API error (F5)

All four shapes are returned via the same dataclass, indistinguishable downstream. **NS7 in the README.**

### F12 [suspect choice] `max_turns` exhausted → "Analysis incomplete" message wins only if no prior text

L527: `answer_text or "Analysis incomplete — maximum turns reached."` — uses the last loop iteration's text if any was emitted, otherwise the literal string. So a "max turns reached" outcome can appear to the caller as a complete answer (if the model emitted any text in the final turn) or as the literal "Analysis incomplete" string (if the final turn had only tool_use blocks). Inconsistent presentation; couples to F11.

### F13 [suspect choice] Last text block wins; earlier text blocks discarded

L451-454:

```python
answer_text = ""
for block in resp.content:
    if hasattr(block, "text") and block.text.strip():
        answer_text = block.text.strip()
```

A response with multiple text blocks (e.g., reasoning interleaved with tool_use, then a summary text block) loses everything except the last text block's content. For Sonnet 4.5 responses with thinking + tool calls + final text, this is usually the desired behavior — but it's not documented as the design choice, and there's no `\n\n`-join fallback if a multi-text response actually occurs.

### F14 [suspect choice] Stop-reason handling is binary

L456 / L509:

```python
if resp.stop_reason == "tool_use":
    ...
# Not tool_use — Claude is done
```

`end_turn`, `max_tokens`, and `refusal` (Anthropic API stop reasons) all collapse into the "Claude is done" branch. A `max_tokens` truncation (the response was cut off mid-sentence because `max_tokens` was hit) returns as if complete. No warning to the caller. Same blindness in standard mode (no stop_reason check at all).

### F15 [duplication] Manual three-level dict-copy of `SEARCH_POLICY_TOOL`

L377-384:

```python
tool = dict(SEARCH_POLICY_TOOL)
tool["input_schema"] = dict(tool["input_schema"])
tool["input_schema"]["properties"] = dict(tool["input_schema"]["properties"])
tool["input_schema"]["properties"]["source"] = {
    "type": "string",
    "enum": sources,
    "description": "Which source to search",
}
```

This is a hand-rolled partial deepcopy to avoid mutating the module-level constant. `copy.deepcopy(SEARCH_POLICY_TOOL)` is one line. The current code is correct (each modified level is a fresh dict) but the intent is obscured.

### F16 [under-design] `config_overrides` accepts arbitrary keys; only four are honored

L577-579:

```python
if config_overrides:
    for key, value in config_overrides.items():
        config.set("synthesis", key, str(value))
```

Every key gets written into the `[synthesis]` section regardless of whether synthesis honors it. The keys actually read downstream:

- `model` (L270, L346)
- `max_tokens` (L271, L347)
- `max_searches` (L348 — deep only)
- `results_per_search` (L272, L349)

Any other key (e.g., a typo `max_token`, a wrong-section key like `anthropic_api_key`) writes silently and does nothing. The contract is undocumented in the docstring (L567 says only "synthesis config overrides (e.g. max_tokens)"). Author audit's open question on `config_overrides` accepted-keys lands here. Author currently passes `model`, `max_tokens`, `results_per_search` — all honored.

### F17 [suspect choice / inconsistency] `max_searches` placement asymmetry — top-level kwarg AND config_overrides

`run_synthesis(max_searches=...)` at L549 sets `[synthesis] max_searches` *before* applying `config_overrides` (L574-579). If a caller passes both `max_searches=10` AND `config_overrides={"max_searches": 12}`, config_overrides wins silently. Other tunables (`model`, `max_tokens`, `results_per_search`) only have the config_overrides path. Author exercises this asymmetry today: `max_searches=12` as a top-level kwarg, `results_per_search=8` inside `config_overrides`. Two paths to the same setting; the precedence isn't documented.

### F18 [under-design] `prompt_name` resolves only to project-shared `prompts/`

L49-59 resolves `name` to `PROMPTS_DIR / f"{name}.md"`. There is no fallback to app-local prompts (`programs/{app}/prompts/`), no error message hint, no contract documentation. Today's two callers (search → `synthesis`, author research → `author_research`) both have files in `prompts/` so it works; a future caller passing an app-local prompt name would hit `FileNotFoundError`. Author audit's open question on `prompt_name` resolution lands here. **CA-15** documents the project-shared vs app-local convention.

### F19 [suspect choice] `with_preamble=True` is hardcoded for both modes

L274 and L352 both pass `with_preamble=True` to `load_prompt`. The domain preamble (`prompts/domain_preamble.md`) is unconditionally prepended to whatever prompt the caller named. For author's `author_research` prompt — which may already include domain context — this is a silent double-load. There is no caller-controlled toggle.

### F20 [drift] `program` and `exclude_programs` parameters are dead in practice

`run_synthesis` accepts both (L546-547), `run_standard` and `run_deep` plumb them through (L262-263, L288, L338-339, L366, L484-485). Caller analysis:

- Search /ask (`ui/app.py:L141-147`): does NOT pass `program` or `exclude_programs`
- Author research (`author.py:L126-137`): does NOT pass either
- CLI (`synthesis.py:L626-632`): passes `program` (from `--program`); does NOT support `--exclude-programs`

**`exclude_programs` is dead** — accepted by the public API, plumbed through every layer, but never set by any caller. **`program` is CLI-only** (legacy single-program shorthand). The legacy comment in the docstring (L562-563) acknowledges both are legacy but they remain plumbed. `programs_by_source` is the modern path used by search; author uses the source-list default with no per-source filter (author F2).

### F21 [drift] `format_results_for_prompt` per-source dispatch — four `elif` branches with diverged metadata choices

L124-210 handles `olg` / `fns` / `cmr` / `cfr` in one function via `if/elif`. Cross-checking each branch:

- **OLG** (L136-156): uses `page_title || title`, `section_heading`, `parent_heading`, `breadcrumb`, `url`, `chunk_n/total`. Richest metadata.
- **FNS** (L158-166): uses `chapter`, `chapter_title`, `section_number`, `section_title`. **No chunk_n/total emission** even though FNS chunks have these fields in their metadata.
- **CMR** (L168-183): uses `chapter`, `program`, `section_number`, `section_title`, `hierarchy_path`, `chunk_n/total`.
- **CFR** (L185-200): uses `part`, `program`, `section_number`, `section_title`, `hierarchy_full_path || hierarchy_path`, `chunk_n/total`.

Adding a fifth source requires another `elif` branch. The score format `{score:.2f}` is consistent across branches but differs from the UI's `score_pct = round(r.get("score", 0) * 100)` style (`ui/app.py:L242`) — same score rendered two ways across the codebase (also CA-3 / search F11). **CA-3 canonical.**

### F22 [duplication / inconsistency] FNS branch omits `chunk_n/total` rendering

L158-166 (FNS) does not emit `(part X of Y)` even though FNS chunks have `chunk_n` / `chunk_total` after the FNS cleanup. OLG, CMR, CFR all emit it. Either FNS doesn't need it (single-chunk sections common), or it's an oversight. Worth confirming; bundles into **CA-3**.

### F23 [duplication, internal] `calculate_cost` invocation appears 4 times in run_deep

L433, L445, L511, L532 — every return path computes `calculate_cost(model, total_input, total_output)`. A small helper or moving the cost calc to the caller would reduce repetition. Not high-impact alone; relevant when CA-1 extracts `tools/cost_tracker.py`.

### F24 [suspect choice] Inline `print` statements throughout couple synthesis to caller's stdout

Print sites: L285, L294, L304, L311, L363, L372, L399, L413, L426, L438, L478, L510, L525. All prints are progress-style ("Searching OLG... 5 results", ".", "[rate limited, waiting 60s]", "done"). For the CLI caller, this is the user feedback. For the FastAPI threadpool caller, all of these go to the server log — invisible to the user clicking the Ask button. Author's run_research adds its own `print()` decorations on top (author.py:L114-124, L153, L198-200). No `logging` layer; no caller-controlled verbosity. Same pattern noted for QC (F14) and comparator.

### F25 [suspect choice] `do_search` hardcodes `threshold=0.0` and doesn't accept `mode`

L236-251 hardcodes `threshold=0.0`. `search_with_client` accepts a `mode` parameter ("dense", "sparse", "hybrid"); synthesis doesn't pass it, defaulting to "dense". Per the retrieval quality plan, dense is the chosen production mode — but synthesis silently bakes that decision in instead of reading from `[embedding]` or accepting a kwarg. If a future deployment wanted hybrid synthesis, the only path is a code edit.

### F26 [under-design] `search_queries` provenance is captured but never typed/structured

L70 `search_queries: list = field(default_factory=list)` — the list elements are `f"{source}: {question}"` (L290) for pre-fetches and `f"{source}: {query}"` (L477) for in-loop searches. Both forms collapse the source/query distinction into a single string. Callers that want to display per-source counts or re-run individual queries must parse the colon-separated string back out. A typed shape (`{"source": str, "query": str, "phase": "prefetch"|"loop"}`) would be more useful — author persists this list; search's NS1 fix needs to render it. **CA-14.**

### F27 [under-design] Budget-exhausted tool_result still consumes a turn

L464-474: when `searches_performed >= max_searches`, the model gets a `tool_result` with text "Search budget exhausted ... Please provide your final answer now". The model can still emit another `tool_use` block in the next turn (which will hit the same exhausted-budget message). Each such turn burns a turn from `max_turns` even though no useful work is done. With max_turns=15 and max_searches=8, the model has up to 7 wasted turns to "ignore" the exhaustion message. Functional but wasteful.

### F28 [outdated] CLI lacks `--exclude-programs` flag

L595-617 defines argparse for `--sources`, `--program`, `--deep`, `--max-searches` but no `--exclude-programs`. `rag/query.py`'s CLI has it. `run_synthesis` accepts it. Synthesis CLI users have no way to set it. Either remove the dead `exclude_programs` plumbing (F20) or add the CLI flag. (Minor; the CLI is essentially a developer convenience.)

### F29 [duplication] `with_preamble` and prompt-loading idiom is also in `qc_analyzer.py:L67`

`load_prompt(name, with_preamble=True)` exists in both `tools/synthesis.py:L49-59` and `programs/qc/qc_analyzer.py:L67-77` with the same signature and behavior. Comparator has its own `load_prompt` reading from app-local `programs/comparator/prompts/`. **CA-15** captures this; documentation-only outcome leaning toward "keep the project-shared vs app-local split intentionally."

### F30 [suspect choice] Sonnet pricing is the silent fallback for unknown models

L218: `rates = MODEL_PRICING.get(model, {"input": 3.00, "output": 15.00})` — any model not in `MODEL_PRICING` is priced at Sonnet rates. New models added to config (e.g., a future Opus 5 or Sonnet 5) would be silently mis-priced until the dict is updated. Same pattern in QC (F9). When CA-1 extracts `tools/cost_tracker.py`, the fallback policy should be deliberate (raise? warn? fall through?).

## Bug log

- **B1** (synthesis F5/F11): Deep-mode error path returns a `SynthesisResult` with the error message in `answer`. No `success` / `error` field exists. Search persists this to history; author would write it to `report.md`. Same anti-pattern as comparator F25; mirror of search NS7. **No user-visible regression today** — when this fires, the user sees an "answer" that says "Synthesis failed due to API error: ..." which is at least honest, just not structured.

## Open questions

- **`max_turns = 15`**: pure guess, or empirically tuned? Same number as comparator L2's hardcoded 15 — was one modeled on the other, or did both converge by feel? Worth one comment in code if the answer is known. (CA-10.)
- **FNS formatter chunk_n/total omission (F22)**: oversight or deliberate? FNS chunks do have these fields after the FNS cleanup; the rendering branch just doesn't surface them.
- **`with_preamble=True` hardcoded (F19)**: is `author_research.md` self-contained enough to drop the preamble? Or does the preamble add value even for prompts that rehash the domain?
- **Module-level cache (F9)**: is a multi-user deployment ever in scope? If yes, the lazy init needs a lock; if no, document "single-process assumption."
- **`prompt_name` contract (F18)**: should the resolver fall back to `programs/{caller}/prompts/{name}.md` if not found in project-shared? Or stay strict and force callers to put shared prompts in `prompts/`? **CA-15 leans toward the strict version + documentation.**
- **CLI completeness (F28)**: is the synthesis CLI maintained as a developer tool, or is it vestigial now that all real usage goes through search/author? If vestigial, lean toward stripping it rather than maintaining flag parity with `rag/query.py`.
- **`mode` plumbing (F25)**: should synthesis honor `[embedding] mode` (if added) or its own `[synthesis] mode` key, given the retrieval quality plan landed on dense? Cleanest answer: leave hardcoded until a real need emerges.

---

# Summary

**30 findings**, distributed:

| Category | Count |
|---|---|
| Drift | 4 (F8, F10, F20, F21) |
| Duplication | 6 (F2, F6, F15, F22, F23, F29) |
| Outdated | 2 (F1, F28) |
| Inconsistency | 1 (F3) — partially also F17, F22 |
| Suspect choice | 11 (F4, F7, F9, F12, F13, F14, F17, F19, F24, F25, F30) |
| Under-design | 5 (F11, F16, F18, F26, F27) |
| Bug | 1 (B1, surfaced by F5/F11) |

**MAJOR**: F3 (run_standard has no retry — production reliability hole in the canonical synthesis caller's hot path).

**Top 3-5 implications for the upcoming extractions**:

1. **`tools/cost_tracker.py` (CA-1)**: synthesis's `MODEL_PRICING` and `calculate_cost` are clean and correct; extract as-is. The Sonnet fallback (F30) should be made deliberate during extraction (raise vs warn vs fall through). `calculate_cost` is invoked 4 times in `run_deep` (F23) — extracting won't reduce that call count, but moving cost arithmetic to a `Tracker.record(usage)` shape would.

2. **`tools/result_formatters.py` (CA-3)**: synthesis's `format_results_for_prompt` IS the canonical, but the FNS branch's missing chunk_n/total rendering (F22) should be reconciled before extraction so all four sources share consistent output. Score-format inconsistency with UI templates (F21) is a separate template-layer problem already noted in CA-3.

3. **`tools/retry.py` (CA-8)**: do **not** copy synthesis's `run_deep` retry verbatim — the duplicated APIError handler (F6) and the embed-everything-in-the-loop shape are exactly what the extracted helper should *replace*. The canonical signature (decorator or function) should sit *outside* the agentic loop, and applying it to `run_standard` (F3) is the first integration test.

4. **`tools/policy_tools.py` (CA-9)**: `SEARCH_POLICY_TOOL` is the cleanest of the three tool defs; the manual deepcopy at L377-384 (F15) is a smell that suggests the helper should expose a `make_search_tool(sources)` factory rather than just the constant.

5. **`SynthesisResult` contract (NS7 / F5 / F11)**: any extraction work that touches synthesis's return path should add `success: bool` (or `error: str | None`) to the dataclass. This is the single highest-leverage synthesis-side change because it unblocks search NS7 (history persistence of failures) and author's research-phase error-detection without API changes upstream of synthesis.
