# PRD 0002: CLI contract, search modes, exact search, index date

- **Origin:** handoff `handoffs/2026-11-19-cli-search-modes-and-refresh.md` (from `business`),
  requirements designed with Ben on 2026-11-21.
- **Status:** draft, awaiting Ben's approval.

## 1. Introduction / overview

`rag/query.py` is now infrastructure for another tool. Ben's `business` portfolio is building
an OLG-drafting kit that shells out to it. Today the kit parses the human-readable `--full`
text, and nothing promises that output stays the same. Callers also can't choose a retrieval
mode, can't find exact wording, can't tell how old the index is, and can't reliably tell an
empty result from an error.

This work makes the command line a deliberate, versioned interface:

- a `--mode` flag;
- an `--exact` phrase search;
- a build record that dates every index;
- defined exit codes and error output;
- a written contract, `docs/cli_contract.md`.

All of this has to happen without changing what existing callers get.

## 2. Goals

1. A programmatic caller can run any covered command with `--json` and parse a documented,
   versioned shape (`contract_version: "1.0"`), including on error.
2. A caller can choose `dense`, `sparse` or `hybrid` retrieval. The default stays `dense`,
   and default output for existing queries is unchanged apart from added JSON fields.
3. A caller can find every chunk that contains an exact phrase in any of the four sources,
   with no embedding call, including phrases that cross a chunk boundary.
4. Every `--json` response and the `--list-programs` output state when the index was built,
   stage by stage. If no record exists they say "unknown", and they never fail because of
   it.
5. Exit codes tell these cases apart: success (including zero results), bad arguments,
   index/source unavailable, external API failure, and internal error.
6. The `business` handoff gets a written response.

## 3. User stories

- **Kit author (business):** As the OLG-drafting kit, I want `--json` output with a
  documented shape, so that my parser doesn't break when someone tweaks the text display.
- **Kit author:** As the kit, I want `--exact "form name"` to list every page that uses that
  exact wording, so that a revision can update every occurrence.
- **Kit author:** As the kit, I want each response to carry the index build dates, so that I
  can warn the drafter when results may be stale.
- **Kit author:** As the kit, I want distinct exit codes, so that "nothing found" never looks
  like "the index is missing".
- **Ben / reg-kb agents:** As an existing caller (web UI, synthesis, comparator, QC, author
  research), I want nothing to change for me unless I opt into a new flag.
- **Ben, maintaining two machines:** As the person who copies `index/` by flash drive, I want
  the build dates stored in the index itself, so that file timestamps changing on copy
  don't matter.

## 4. Functional requirements

### 4.1 `--mode dense|sparse|hybrid`

1. `query.py` must accept `--mode {dense,sparse,hybrid}`, default `dense`, and pass it to
   `search_with_client()`.
2. The `search_with_client()` docstring must state the real default (`"dense"`) and explain
   that hybrid tested worse (see 4.6.8).
3. **Broad collections.** The sparse index covers the section tier only. On the CLI,
   `--mode sparse` or `--mode hybrid` combined with a broad collection (`pages`,
   `chapters`, `parts`) must be **rejected** as a usage error (exit 2) with a clear message.
   The Python API keeps its current behavior (it downgrades to dense, and the response's
   `mode` field already reports `"dense"`), and its docstring must say so.
4. **Missing sparse index.** If `--mode sparse` or `--mode hybrid` runs and
   `index/sparse/{source}.pkl` doesn't exist, it must fail with "index unavailable"
   (exit 3). Today it silently returns zero results (sparse) or dense-only results
   (hybrid), so the failure looks like a real answer. The API raises a specific exception
   in this case. No existing caller uses non-dense modes, so this is safe.
5. The JSON `mode` field must report the mode that actually ran.
6. The web UI is **not** changed. Ben decided on 2026-11-21 to leave the mode selector out.

### 4.2 `--exact "phrase"`

1. `--exact "phrase"` must find literal occurrences of the phrase in the chosen source, with
   no Voyage API call. It must not require a Voyage API key to be configured.
2. **Where it searches.** It searches the broad-tier document text: OLG pages, FNS/CMR
   chapters, CFR parts. It reads that text from the ChromaDB broad collection. Measured on
   2026-11-21, the broad text is complete (ChromaDB matches the chunk files, up to 838K
   characters), and a phrase split across a section-chunk boundary is still contiguous
   there.
3. **Chunk attribution.** Each match must be reported against the section chunk that
   contains it. The match is aligned against the parent document's section-chunk bodies,
   concatenated in chunk-suffix order, with each chunk's context-prefix line removed.
   - A match that crosses a chunk boundary is reported once, against the chunk where it
     starts, and lists every chunk it spans in `chunk_ids`.
   - The two tiers format a little text differently: headings live in the chunk prefix
     line, and some tables are laid out differently (about 0.4% of samples). If a match
     can't be aligned, it must still be reported, with `id: null`, `chunk_ids: []` and the
     parent document's fields. It must never be dropped.
4. **Normalization.** The same steps apply to the phrase and to the searched text before
   matching:
   - case-folding;
   - curly and other quote variants → `'` / `"`;
   - dash variants (hyphen, non-breaking hyphen, figure dash, en and em dash, minus,
     full-width hyphen) → `-`;
   - non-breaking and other Unicode spaces → space;
   - zero-width characters and soft hyphens removed;
   - Markdown heading markers (`#`) at line start removed;
   - any whitespace run → one space;
   - leading and trailing space trimmed.

   Matching is a plain substring match: `SNAP` also matches inside `SNAPshot`. The contract
   must say so.
5. **Empty or whitespace-only phrase.** Reject it as a usage error (exit 2).
6. **Result unit.** One result per chunk that contains at least one match, plus one result
   per unaligned match group in a parent document.
7. **Result fields.** Each result has:
   - `rank`;
   - `id` (chunk id, nullable);
   - `chunk_ids` (every chunk the matches span);
   - `parent_id`;
   - `match_count` (matches attributed to this result);
   - `snippets`: up to 3 strings, each about 80 characters of normalized context either
     side of a match;
   - `text` (the full chunk text, as in a normal hit; for an unaligned result, the parent
     document text);
   - `metadata`: the chunk's own metadata dict, the same keys a normal hit carries
     (breadcrumb, page_title, url, last_updated, chunk id fields, program, and so on). For
     an unaligned result it's the parent document's metadata, with OLG's `title` also
     copied to `page_title`;
   - `parent_context`, as with `--context`.
8. **Ordering.**
   - Parent documents sort by total match count, descending, with ties broken by parent id.
   - Within a parent, results follow chunk order, and unaligned results come last.

   The order is deterministic for a given index.
9. **`--top`.** Without `--top`, exact search returns **all** results. With an explicit
   `--top N`, it returns the first N. The response always carries:
   - `result_count` (returned);
   - `total_results` (before the cap);
   - `total_matches` (occurrences across the whole source after filters);
   - `truncated` (bool).
10. **Program filters.**
    - `--programs`, `--program` and `--exclude-programs` apply exactly as in search, to the
      chunk's `program` metadata. An unaligned result uses the parent document's `program`.
    - Sources without program filtering (FNS) ignore them, as search does.
    - The `OLG_PROGRAMS` orchestrator whitelist applies to `--exact` exactly as to search.
11. **Flag compatibility.** `--context` and `--json` are allowed. An explicit `--mode`,
    `--threshold` or `--collection` combined with `--exact` is a usage error (exit 2),
    because they have no meaning for a literal search. Nothing is silently ignored.
12. `--exact` works for `olg`, `fns`, `cmr` and `cfr`.
13. The exact-search logic lives in its own module, `rag/exact_search.py`, which `query.py`
    calls. The module splits into:
    - pure functions (normalization, offset mapping, matching, attribution, ordering) that
      take plain lists of documents;
    - a thin loader that reads ChromaDB.

### 4.3 Index build record

1. A new module, `rag/build_record.py`, reads and writes one record per source at
   `index/{source}/build_record.json`. The record travels with `index/` when it's copied.
2. **Schema.** Each record has:
   - `schema_version: 1`;
   - `source`;
   - `stages`: one entry per stage, keyed `scrape` (OLG) or `parse` (FNS, CMR, CFR), then
     `chunk`, `embed` and `sparse`.

   Each stage holds:
   - `date` (`YYYY-MM-DD`);
   - `completed_at` (ISO-8601 local time with offset);
   - `counts` (stage-specific, such as pages, sections, chunks or documents);
   - optional `details` (such as embedding model names or the chunk variant file);
   - optional `note`.

   `embed` keeps a sub-entry per collection, because `--only` can re-embed one tier alone.
   The stage `date` is the **oldest** collection date, so a result is never shown as
   fresher than its stalest tier.
3. **Writes.** A write updates only its own stage. It reads, merges and writes atomically
   (a temp file, then replace), so a crash can't leave a half-written record. A write that
   fails must print a warning and never fail the pipeline run.
4. **Writers:**

   | Stage | Writer |
   |-------|--------|
   | `scrape` | `rag/olg/scraper.py`, on a completed run |
   | `parse` | `rag/fns/parser.py`, `rag/cmr/parser.py`, `rag/cfr/parser.py` |
   | `chunk` | the four chunkers, each on a successful write of its chunk files |
   | `embed` | `rag/embedder.py`, per collection, after a successful embed |
   | `sparse` | `rag/sparse_index.py`'s `save_index()`, so any builder records the stage, including the local-only `tools/build_sparse_index.py` |

   `rag/embedder.py` must **not** write a record on `--dry-run`, or when a
   `collection_suffix` (side-by-side evaluation) is in use.
5. **Reads.** `read_index_info(source)` returns the response's `index` block. If the record
   is missing or unreadable, it returns the same shape with `record_status: "missing"` (or
   `"unreadable"`) and every stage `date` as `"unknown"`. It never raises.
6. **Two kinds of date.** The record's dates say when *we* fetched or built the index. A
   page's `last_updated` metadata (OLG "Updated") says when *the agency* last changed that
   page. The contract and the `--list-programs` text must describe both and keep them
   separate.
7. **Seed records** for the current index, dates confirmed by Ben on 2026-11-21:

   | Source | Scrape / parse | Chunk | Embed | Sparse |
   |--------|----------------|-------|-------|--------|
   | OLG | scraped 2026-04-30 | 2026-05-01 | 2026-05-04 | 2026-05-04 21:12 |
   | FNS | parsed 2026-05-02 | 2026-05-02 | 2026-05-04 | 2026-05-04 21:12 |
   | CMR | parsed 2026-04-27 | 2026-04-27 | 2026-05-04 | 2026-05-04 21:12 |
   | CFR | parsed 2026-04-29 | 2026-04-29 | 2026-05-04 | 2026-05-04 21:12 |

   - Each seeded stage gets the note
     `"reconstructed 2026-11-21 from scrape_report.txt, file times, git log and sparse built_at"`,
     with `completed_at: null` except for the sparse stage. The sparse time comes from the
     pickle's `built_at`.
   - Counts come from the current chunk files and collections.
   - Seeding is a one-off script, not a pipeline feature.
   - After seeding, the four tiny files must be copied to the other machine with the next
     index copy.
8. `.gitignore` must ignore `index/*/build_record.json`. It lists index files one by one, so
   new files there would otherwise be committed.

### 4.4 JSON responses (contract 1.0)

1. Every `--json` response must include:
   - `contract_version: "1.0"`;
   - `command`: `"search"`, `"exact"`, `"chunk"`, `"url"` or `"list"`;
   - `index`: the 4.3.5 block for the response's source.
2. **Existing fields are unchanged.** Search keeps `query`, `source`, `collection`,
   `filters`, `mode`, `result_count` and `results`. The chunk and URL lookups keep
   `target_chunk_id`, `source`, `chunk_count` and `chunks`. Everything new is added
   alongside.
3. `--list-programs --json` must return JSON:
   - `programs`: `[{program, chunk_count}]`;
   - `structure`: `[{key, title, chunk_count}]` for FNS/CMR chapters or CFR parts, and
     `null` for OLG;
   - `total_chunks`.
4. Error responses with `--json` must print a JSON object to stdout:
   `{contract_version, command, error: {kind, message, exit_code}, index}`. `index` is
   included when the source is known, and is otherwise `null`.

### 4.5 Exit codes and errors

1. **Exit codes.** Decided by Ben on 2026-11-21: zero results is success.

   | Code | Kind | Meaning |
   |------|------|---------|
   | 0 | — | Ran fine. `result_count` may be 0. |
   | 2 | `usage` | Bad or conflicting arguments, unknown program name, empty `--exact` phrase. |
   | 3 | `unavailable` | Missing `config.ini` or API key, missing ChromaDB directory or collection, missing sparse index. |
   | 4 | `api` | The Voyage API call failed (network, auth, rate limit after retries). |
   | 5 | `internal` | Anything unexpected. The message includes the exception type. |

2. **stderr format.** Every error writes exactly one line to stderr:
   `query.py: error [<kind>]: <message>`. No traceback, unless the env var
   `QUERY_DEBUG=1` is set.
3. **stdout stays clean.** Nothing but the response goes to stdout. The current
   `print("Error: ...")` calls on the CLI path (config, collection validation, ChromaDB
   directory, `--url` source) move to the error path.
4. **argparse errors** (exit 2) use the same stderr format. With `--json`, they also print
   the JSON error object.
5. **Lookup commands are mutually exclusive.** A search query, `--exact`, `--chunk-id`,
   `--url` and `--list-programs` can't be combined. Combining them is a usage error. Today
   `--url` silently wins.
6. **The Python API is not restructured.** `create_client()` and `load_config()` still exit
   on missing config or index when called directly. The CLI checks these conditions first,
   so it never reaches those exits. Exception: the 4.1.4 sparse-index exception.

### 4.6 `docs/cli_contract.md`

The contract document must cover:

1. **Scope.** The command is `rag/query.py`, run from the repo root with the repo's
   Python. The Python API is internal and not covered.
2. **Flags.** Every covered flag:
   - search: `--source`, `--collection`, `--programs` (plus legacy `--program` and
     `--exclude-programs`), `--top`, `--threshold`, `--context`, `--mode`;
   - lookups: `--exact`, `--chunk-id` with `--neighbors`, `--url`, `--list-programs`;
   - output: `--json`.

   For each flag: allowed values, defaults, which sources ignore it (FNS ignores program
   filters; `--url` is OLG-only), and which combinations are errors.
3. **JSON shapes.** For each command, field by field: name, type, meaning, nullable or
   not. This includes the `metadata` keys guaranteed per source and the score fields per
   mode:
   - dense: `score` is similarity;
   - sparse: `score: null` plus `bm25_score`;
   - hybrid: `score` is dense similarity or null, plus `rrf_score` and `bm25_score`.
4. **The `index` block and the two kinds of date** (4.3.6).
5. **Exit codes and stderr format** (4.5).
6. **Not promised:**
   - the human-readable text output (including `--full`);
   - exact scores, and result order across rebuilds;
   - chunk-id stability across an index refresh (OLG ids come from breadcrumbs, so a moved
     page gets new ids);
   - fields not listed in the contract.
7. **What each mode is for, with numbers:**
   - Dense is the default and best for natural-language questions.
   - Hybrid tested worse: Rel@1 OLG 62% → 46%, CMR 65% → 57%, Useful@5 unchanged. It
     re-ordered the same chunks into a worse order (retrieval plan, closed 2026-05-05).
   - Sparse is a BM25 keyword ranker, not a phrase finder.
   - `--exact` is for exact wording, form names and section numbers.
8. **Change rules.**
   - Adding a field or flag bumps the minor version (`1.1`) and needs no notice.
   - Renaming or removing one, or changing its meaning or type, bumps the major version and
     needs a handoff to `business` first.

### 4.7 Handoff response

1. Append a `## Response` section to `handoffs/2026-11-19-cli-search-modes-and-refresh.md`,
   following the portfolio standard, section 4. Set the status to `accepted` when the
   build starts, and to `done` when verification passes.
2. It covers:
   - what was built and where the contract lives;
   - why hybrid isn't the default, with the numbers;
   - sparse versus `--exact`;
   - that the kit should move from `--full` text to `--json`;
   - that chunk ids will change at the index refresh, and that `business` gets a handoff
     before it;
   - that `docx_writer` stays a copy;
   - that the OLG refresh (ask 3) is a separate project and that part of the handoff waits
     on it.
3. No agency content. The repo is public.

## 5. Non-goals (out of scope)

- The OLG index refresh (handoff ask 3). No re-scrape, re-chunk or re-embed. Ben is
  getting the corpus as `.docx`; that's a separate project.
- `docx_writer` sharing or a cross-repo import.
- Retrieval changes: fusion weights, ranking, the tokenizer, reranking.
- Web UI changes, including the mode selector.
- Covering the Python API in the contract.
- Whole-word, regex or fuzzy matching for `--exact`.
- Restructuring `create_client()` / `load_config()` error handling for API callers.

## 6. Design considerations

- **Text output.** The human-readable output gets small additions only:
  - a one-line index date summary under `--list-programs`;
  - a readable layout for `--exact` hits (breadcrumb, title, URL, Updated, chunk id,
    match count, snippets).

  Default search text output is unchanged.
- **CLI help.** The `--help` epilog gains `--mode` and `--exact` examples.

## 7. Technical considerations

- **Existing callers must behave the same:** `ui/search.py`, `tools/synthesis.py`,
  `apps/qc/*`, `apps/comparator/comparator.py`, and the Claude Code agents that shell out
  (comparator L2, QC judge, author research). The only API change is the new sparse-index
  exception, on a path no caller uses.
- **Baseline before changing anything.** Before touching `query.py`, capture `--json`
  output for about 5 queries across the 4 sources (dense). After the change, diff it:
  results must be identical apart from the added fields. Queries embed only a few tokens,
  so the cost is negligible.
- **Exact-search cost.** It loads one broad collection's documents (OLG about 6 MB) plus the
  section chunks of the parents that have hits. No embedding, no network.
- **Python environment.** This machine has no `.venv`. The global Python 3.13 (`py`) has
  the pinned `chromadb==1.5.2` and is used for tests and verification.
- **Local-only tools.** `tools/build_sparse_index.py` and `tools/benchmark_retrieval.py`
  are not on this machine. The sparse-stage record works through `save_index()`, so the
  local-only builder needs no change. The optional benchmark re-run happens on the other
  machine, if at all.
- **Tests.** Offline and free, synthetic fixtures only (`tests/conftest.py`). Coverage:
  - argument parsing and conflicts;
  - mode passthrough;
  - normalization;
  - boundary-straddling phrases;
  - unaligned-match fallback;
  - ordering and `--top`;
  - build-record read/write/merge and "unknown";
  - JSON shape, including `contract_version` and `index`;
  - exit codes for each error kind.

  ChromaDB and Voyage are stubbed. Nothing reads the real index.

## 8. Success metrics

- The verification list in the requirements passes on this machine:
  - sparse and hybrid return results;
  - dense output is identical to the baseline;
  - `--exact` finds a known phrase, including a boundary-crossing one, and returns exit 0
    with `result_count: 0` for nonsense;
  - the dates show in `--list-programs` and `--json`;
  - `python -m pytest tests` passes.
- On the real index, for a sample of phrases, measure and record in the build notes how
  often `--exact` matches attribute to a chunk.
- The `business` kit can switch from `--full` text to `--json` using only
  `docs/cli_contract.md`.

## 9. Open questions

None blocking. The four open questions from the requirements are resolved above:

| Question | Resolved in |
|----------|-------------|
| Text source for exact search | 4.2.2, 4.2.3 |
| Today's error behavior | 4.5, Technical considerations |
| Build record location and writers | 4.3 |
| Web UI | 4.1.6: left out |
