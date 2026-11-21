# CLI search modes, exact search and an index refresh, for Claude Code callers

- **From:** business
- **To:** regulatory-knowledgebase
- **Opened:** 2026-11-19
- **Status:** proposed

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
