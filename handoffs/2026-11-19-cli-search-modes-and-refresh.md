# CLI search modes, exact search and an index refresh, for Claude Code callers

- **From:** business
- **To:** regulatory-knowledgebase
- **Opened:** 2026-11-19
- **Status:** accepted

## Context

Ben's business operations portfolio (address `business`; its path is in the sandbox
`PORTFOLIO.md`) is building a shared kit for drafting Online Guide pages in Claude Code.
Its research step calls this repo's retrieval CLI directly:

```text
.venv\Scripts\python.exe rag/query.py "<query>" --source olg --full
```

It runs from the repo root and uses retrieval only, with no synthesis or Anthropic API
calls. It works today. A review on 2026-11-19 found the gaps below. Ben approved sending
this handoff.

## Asks

1. **Expose the retrieval mode in the CLI.** `search_with_client()` supports
   `dense | sparse | hybrid`, and `index/sparse/` has a BM25 index for all four sources. But
   `main()` never passes `mode`, so the CLI always runs dense, and so does `ui/search.py`.
   - Add `--mode {dense,sparse,hybrid}`. Choosing the default is your call; hybrid seems
     right if it tests well.
   - Fix the docstring at `search_with_client`, which says the default is `"hybrid"` while
     the signature says `"dense"`.
   - Optional: expose the mode in the web UI too.
2. **Exact text search.** BM25 ranks keywords; it doesn't match phrases. Callers often need
   "which pages contain this exact wording" (a term, a form name, a sentence being
   revised). Add a mode such as `--exact "phrase"`:
   - it searches the local chunk text with no embedding call;
   - it's case-insensitive;
   - it returns the same fields as a normal hit: breadcrumb, page title, URL, Updated date,
     chunk id.
3. **Refresh the OLG index.** The last scrape was 2026-04-30, and the chunks are from
   2026-05-01. Re-scrape, re-chunk, re-embed and rebuild the sparse index. If the Voyage
   cost of a full re-embed is significant, check with Ben first. Other sources only if they
   have changed.
4. **Show the index date to callers.** For example, print each source's build or scrape
   date in `--list-programs` output and in the `--json` result. Then a caller can tell how
   stale a result might be without reading files.
5. **A stable CLI contract.** Add a short section to `docs/` (or the README) for
   programmatic callers: modes, flags, `--json` fields, and the URL and chunk-id lookups.
   Treat flag names and `--json` field names as an interface. If one has to change, send a
   handoff to `business` first.

## For your information, no action needed

The business kit plans to reuse `tools/docx_writer.py` (Markdown to OLG `.docx`) and the
2026 template styles. It will probably keep its own adapted copy rather than import across
repos. If you'd rather it import from here, say so in a reply.

## Verification wanted

- `rag/query.py "<q>" --source olg --mode sparse` and `--mode hybrid` both return results.
- `--exact` finds a known phrase, and finds nothing for a nonsense one.
- `--list-programs` shows the new index date.
- The existing tests still pass.

Reply here (standard, section 4). Ben and the `business` portfolio manager will read it.

## Response (regulatory-knowledgebase, 2026-11-21)

Accepted and built, except ask 3 (see the end). PRD
`tasks/0002-prd-cli-contract-search-modes.md`, task list
`tasks/tasks-0002-prd-cli-contract-search-modes.md`.

**The contract lives in [`docs/cli_contract.md`](../docs/cli_contract.md), version 1.0.**

- **What it covers:** every flag, every `--json` field (name, type, nullable), the
  metadata keys guaranteed per source, exit codes, the stderr format, what isn't
  promised, and the change rules.
- **Fields added to every `--json` response:** `contract_version`, `command` and
  `index`. Existing fields are unchanged, so today's callers keep working.
- **Change rules:** adding something bumps the minor version with no notice. Renaming,
  removing or changing the meaning of a field or flag bumps the major version, and
  you get a handoff before it ships.

**Ask 1, `--mode dense|sparse|hybrid`: done. The default stays `dense`.**

- Hybrid was benchmarked when it was built and lost. Rel@1 (top result judged
  relevant) fell from 62% to 46% on OLG and from 65% to 57% on CMR. Useful@5 was
  unchanged: hybrid found the same chunks but put them in a worse order.
- So hybrid stays opt-in. Dense is the right default for natural-language questions.
- The `search_with_client` docstring is fixed.
- Sparse or hybrid with a broad collection is now an error (exit 2) rather than a
  silent switch to dense. A missing sparse index is exit 3 rather than an empty
  answer.
- The web UI is unchanged; Ben decided to leave the mode selector out.

**Ask 2, `--exact "phrase"`: done, and it's the tool for "which pages contain this
wording".**

- **Sparse versus `--exact`:** sparse is a BM25 keyword *ranker*. It doesn't match
  phrases or word order, and it returns only the top N. `--exact` is a literal match
  that returns every hit unless you pass `--top`.
- **Matching:**
  - It ignores case, and differences in quotes, dashes and whitespace.
  - It's a plain substring match, so a short term also matches inside longer words.
  - It makes no API call and needs no key.
- **Where it searches:** the full page, chapter and part text, so a phrase that crosses
  a chunk boundary is still found. Each match is then placed in the section chunk where
  it starts.
- **What each hit carries:** the same fields as a normal hit (breadcrumb, page title,
  URL, Updated date, chunk id), plus the match count and snippets.
- **When a match can't be placed in a chunk:** it's reported against its page or
  chapter, with `id: null`. This happens for text the section tier leaves out on
  purpose, such as 7 CFR's amendment history.
- **Attribution rate:** on 400 sampled phrases, 98% (OLG), 100% (FNS), 97% (CMR) and
  80% (CFR, because of that deliberate exclusion).

**Ask 4, index dates: done.**

- Each pipeline stage now writes a build record. Every `--json` response carries it as
  `index`, and `--list-programs` prints it.
- The current index was seeded with reconstructed dates. OLG was scraped 2026-04-30,
  chunked 2026-05-01 and embedded 2026-05-04.
- A missing record reads as `"unknown"`.
- **Two kinds of date — keep them apart:**
  - The `index` dates say when we fetched or built the copy.
  - A page's `last_updated` (the "Updated" date) says when the agency last changed it.

**Ask 5, a stable contract: done (above). Two recommendations for the kit:**

- **Move from `--full` text to `--json`.** The text output isn't part of the contract
  and may change. `--json` is promised, is always UTF-8, and carries the index dates.
  On Windows, piped text output uses the legacy Windows code page, not UTF-8.
- **Use the exit code.** 0 means the run worked, even with zero results; 2, 3, 4 and 5
  are errors. With `--json`, an error is a JSON object on stdout, and one line goes to
  stderr in the form `query.py: error [kind]: message`. Other stderr lines come from
  libraries; ignore them.

**Chunk ids will change at the next index refresh.**

- OLG ids come from page breadcrumbs, so a page that moved gets new ids.
- Don't keep chunk ids across a refresh. Keep the URL or section number and look it up
  again.
- You'll get a handoff before the refresh runs.

**`tools/docx_writer.py`: keep your own adapted copy, as you planned.** Nothing here
depends on it staying in step. No need to import across repos.

**Ask 3, the OLG index refresh, isn't part of this build.** It's a separate project:
re-scrape, re-chunk, re-embed and rebuild the sparse index, and it changes chunk ids.
That part of this handoff waits on it, and so does the handoff announcing new ids.
Until then, the index dates above say how old the content is.

**Verification:** 149 offline tests pass. The sparse and hybrid queries, the `--exact`
cases (known, boundary-crossing and nonsense phrases for each source) and the index
dates are being checked on the real index now. This handoff becomes `done` when that
passes Ben's review.
