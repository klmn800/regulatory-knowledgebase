## Relevant Files

- `rag/build_record.py`: new. Reads and writes the per-source index build record.
- `rag/exact_search.py`: new. Literal phrase search (normalization, matching, chunk attribution, ordering) plus a thin ChromaDB loader.
- `rag/cli_errors.py`: new. Error kinds, exit codes, the stderr line and the JSON error object.
- `rag/query.py`: CLI changes (`--mode`, `--exact`, the JSON envelope, errors, exclusive commands, `--list-programs --json`) and the docstring fix.
- `rag/sparse_index.py`: `save_index()` writes the sparse stage.
- `rag/embedder.py`, `rag/olg/scraper.py`, `rag/{fns,cmr,cfr}/parser.py`, `rag/{olg,fns,cmr,cfr}/chunker.py`: write their stage.
- `.gitignore`: ignore `index/*/build_record.json`.
- `docs/cli_contract.md`: new. The versioned CLI contract.
- `handoffs/2026-11-19-cli-search-modes-and-refresh.md`: the `## Response` section and status.
- `CLAUDE.md`, `README.md`: commands and module tables.
- `tests/test_build_record.py`, `tests/test_pipeline_records.py`, `tests/test_exact_search.py`, `tests/test_query_cli.py`: new.
- Seed records written to `index/{olg,fns,cmr,cfr}/build_record.json` (gitignored; copy to the other machine with the next index copy).
- Known: `tests/test_reference_docs.py::test_path_traversal_and_reserved_names` hangs on Windows 10, where `CON.txt` resolves to the console device (pre-existing bug in `apps/author/reference_docs.py`, outside this PRD). Run the suite with `--deselect` until it's fixed.

### Notes

- Run the tests with `py -m pytest tests`. They are offline and free, with synthetic fixtures only and ChromaDB and Voyage stubbed.
- This machine has no `.venv`, so use the global Python 3.13 (`py`).

## Tasks

- [x] 1.0 Capture a dense baseline, then build the build-record module and seed the current index
  - [x] 1.1 Before any code change, save `--json` output for 5 dense queries (2 OLG, 1 each FNS, CMR, CFR) and for 1 chunk-id lookup, to the scratchpad as the baseline.
  - [x] 1.2 Write `rag/build_record.py`:
    - stage names per source (`scrape` for OLG, `parse` for the others, then `chunk`, `embed`, `sparse`);
    - `record_stage(source, stage, counts, details=None, note=None, index_root=None, when=None)`: atomic read, merge, then temp-file-and-replace; never raises, warns on failure;
    - `record_embed_collection(source, tier, collection, model, count, ...)`: the stage date is the oldest collection date;
    - `read_index_info(source, index_root=None)`: returns the PRD 4.3.5 block, with `record_status` of `present`, `missing` or `unreadable`, and missing dates as `"unknown"`;
    - `format_index_info_text(info)`: the one-line summary for the text output.
  - [x] 1.3 Add `index/*/build_record.json` to `.gitignore`.
  - [x] 1.4 Write `tests/test_build_record.py`: write/read round trip, merging two stages, the embed per-collection oldest-date rule, missing record â†’ `"unknown"`, unreadable JSON â†’ `"unreadable"` with no exception, and a write failure that doesn't raise.
  - [x] 1.5 Seed the four records with a one-off scratch script: the dates confirmed in PRD 4.3.7, the reconstruction note, counts from the current chunk files and collections, and the sparse `completed_at` from the pickle's `built_at`. Print each record to check it.
- [x] 2.0 Make each pipeline stage write its build record
  - [x] 2.1 `rag/olg/scraper.py`: on a completed run, write the `scrape` stage with counts of pages scraped, 404s and failures.
  - [x] 2.2 `rag/fns/parser.py`, `rag/cmr/parser.py`, `rag/cfr/parser.py`: after parsed JSONs are written, write the `parse` stage with section and source-PDF counts.
  - [x] 2.3 The four chunkers: after the chunk files are written, write the `chunk` stage with broad and section chunk counts. For CFR, record which variant file the embedder uses.
  - [x] 2.4 `rag/embedder.py`: after each collection embeds successfully, write its `embed` entry with model, collection and count. Skip on `--dry-run` and whenever a `collection_suffix` is set.
  - [x] 2.5 `rag/sparse_index.py` `save_index()`: write the `sparse` stage with the chunk count, using `index.built_at` as the time. The index root is derived from the pickle path.
  - [x] 2.6 Tests: `save_index()` into a temp index root writes the sparse stage, and the embedder's skip rule (a pure helper) is covered.
- [ ] 3.0 Turn the CLI into the contract layer: error kinds and exit codes, the JSON envelope, `--mode`, `--list-programs --json`, exclusive commands
  - [ ] 3.1 Write `rag/cli_errors.py`:
    - `CliError(kind, message)` and the kind â†’ exit code map (`usage` 2, `unavailable` 3, `api` 4, `internal` 5);
    - `emit_error(err, command, source, as_json)`, which writes the stderr line and, with `--json`, the JSON object on stdout;
    - a `QUERY_DEBUG` traceback switch.
  - [ ] 3.2 `query.py` argument parsing:
    - an ArgumentParser subclass whose `error()` raises `CliError("usage")`;
    - `--mode` and `--top`, `--threshold`, `--collection` default to `None`, so an explicit flag can be detected (search falls back to the old defaults);
    - the lookup commands are mutually exclusive.
  - [ ] 3.3 CLI checks before any client is created:
    - config file and Voyage key (not needed for `--exact`);
    - ChromaDB directory and collection exist;
    - collection valid for the source;
    - `--mode` sparse/hybrid not used with a broad collection;
    - sparse index exists for sparse/hybrid;
    - `--url` only with OLG.

    All of these raise `CliError` with nothing on stdout.
  - [ ] 3.4 Map failures to kinds: unknown program (`ValueError` from `_resolve_program_name`) â†’ `usage`; Voyage exceptions â†’ `api`; a ChromaDB missing collection â†’ `unavailable`; anything else â†’ `internal`. `main()` wraps the run and exits with the code.
  - [ ] 3.5 API: `search_with_client()` raises `SparseIndexMissingError` (a subclass of `FileNotFoundError`) when the mode isn't dense and no sparse index exists. Fix the docstring default and document the broad-tier downgrade.
  - [ ] 3.6 Add `contract_version`, `command` and `index` to the search, chunk and URL JSON, plus the OLG_PROGRAMS guardrail's empty response. The `--mode` value passes through to `search_with_client()`.
  - [ ] 3.7 `--list-programs`: one index-date line in the text output. With `--json`, the PRD 4.4.3 shape. Refactor `_print_info` into a data function and a text formatter so the text output stays the same.
  - [ ] 3.8 Write `tests/test_query_cli.py`, with ChromaDB and Voyage stubbed:
    - argument parsing and conflicts;
    - mode passthrough, and broad + sparse rejected;
    - each exit code;
    - the stderr format;
    - the JSON error object;
    - search, chunk and list JSON carrying `contract_version`, `command` and `index`;
    - default search JSON unchanged apart from the added fields.
- [ ] 4.0 Add `--exact` phrase search (`rag/exact_search.py`) and wire it into the CLI
  - [ ] 4.1 `normalize_with_map(text)`: applies the PRD 4.2.4 rules and returns the normalized string plus a map from each normalized index to its original index. `normalize(text)` is the plain form.
  - [ ] 4.2 `find_matches(phrase, docs)`: non-overlapping matches in each broad document, as normalized offsets.
  - [ ] 4.3 `attribute(parent_text_match, chunks)`: builds the concatenated stream of chunk bodies (prefix line removed) with per-chunk spans. Each matched phrase occurrence is aligned to a stream occurrence in order. The result is the start chunk plus every chunk spanned, or the match is unaligned.
  - [ ] 4.4 `exact_search(phrase, broad_docs, chunk_loader, filter_fn, top)`: groups results per chunk plus unaligned groups, adds snippets, sets `parent_id`, applies the program filter, orders per PRD 4.2.8 and computes the totals and `truncated`.
  - [ ] 4.5 The ChromaDB loader: reads the broad collection's documents and metadata, and loads a parent's section chunks lazily by parent-id metadata. It needs no Voyage client.
  - [ ] 4.6 Wire it into `query.py`:
    - `--exact` with the flag checks from PRD 4.2.11;
    - program filters and the OLG_PROGRAMS whitelist;
    - `--context`;
    - JSON (`command: "exact"`);
    - a text formatter.
  - [ ] 4.7 Write `tests/test_exact_search.py`: each normalization rule, a phrase straddling a chunk boundary, a heading-crossing phrase, an unaligned fallback, ordering, the `--top` cap and totals, the program filter, an empty phrase â†’ usage error, and no match â†’ `result_count: 0` with exit 0.
  - [ ] 4.8 On the real index, measure the attribution rate on a sample of about 200 phrases taken from the broad text across the four sources, and record it in this task list.
  - [ ] 4.9 **GATE (plan-changing test):** stop only if the attribution rate is under 95% for any source. In that case show Ben the failing patterns and propose either better alignment or searching the chunk text instead. At 95% or above, carry on without stopping.
- [ ] 5.0 Write `docs/cli_contract.md`, update CLAUDE.md and README, and write the handoff response
  - [ ] 5.1 Write `docs/cli_contract.md` covering every item in PRD 4.6.
  - [ ] 5.2 Update the `query.py` module docstring and `--help` epilog, the CLAUDE.md query commands and module table (`exact_search`, `build_record`, `cli_errors`), and the README.
  - [ ] 5.3 Read the portfolio standard, section 4. Set the handoff status to `accepted` and write the `## Response`, covering PRD 4.7 with no agency content.
- [ ] 6.0 Verify on the real index
  - [ ] 6.1 Run sparse and hybrid OLG queries and confirm both return results.
  - [ ] 6.2 Run the dense baseline queries again and diff against 1.1: results must be identical apart from the added fields.
  - [ ] 6.3 Run `--exact` on a known phrase, on a phrase that crosses a chunk boundary, and on a nonsense phrase (exit 0, `result_count: 0`), for each source.
  - [ ] 6.4 Check that `--list-programs` (text and JSON) and `--json` show the index dates, and that a temporarily renamed record gives `"unknown"`.
  - [ ] 6.5 Check that each error kind gives the right exit code and the stderr line: a bad program, broad + sparse, a missing collection via a bad config path, and a bad Voyage key via an env override if possible.
  - [ ] 6.6 Run `py -m pytest tests`.
  - [ ] 6.7 **GATE (see):** Ben reviews the verification results. If he approves, set the handoff status to `done` and commit.
