# `query.py` CLI contract

**Contract version: 1.0** (2026-11-21). Every `--json` response carries it as
`contract_version`.

This is the interface for programs and agents that call the retrieval CLI, such as
Claude Code research steps and the `business` drafting kit. Flag names, JSON field
names and exit codes listed here are promised. Anything not listed here isn't promised
(see [Not promised](#not-promised)). How the contract may change is under
[Change rules](#change-rules).

## Scope

- **The command** is `rag/query.py`, run from the repo root with the repo's Python
  (for example `.venv\Scripts\python.exe rag/query.py ...`).
- **The Python API** (`search()`, `create_client()`, `search_with_client()` and the rest)
  is internal and not covered.
- **Read-only.** The CLI never changes the index. Retrieval only: no synthesis, and no
  Anthropic API calls. Search calls Voyage AI to embed the query; `--exact`,
  `--chunk-id`, `--url` and `--list-programs` make no API call.

## Commands

Each run does exactly one command. Combining them is a usage error (exit 2).

| Command | How to ask for it | `command` in JSON |
|---------|-------------------|-------------------|
| Search | a positional query: `query.py "income deduction"` | `"search"` |
| Exact phrase | `--exact "phrase"` | `"exact"` |
| Chunk lookup | `--chunk-id ID` (optionally `--neighbors N`) | `"chunk"` |
| Page lookup | `--url URL` (OLG only) | `"url"` |
| Source summary | `--list-programs` | `"list"` |

## Flags

| Flag | Values | Default | Applies to | Notes and errors |
|------|--------|---------|------------|------------------|
| `--source`, `-s` | `olg`, `fns`, `cmr`, `cfr` | `olg` | all commands | |
| `--json` | (switch) | off | all commands | The JSON shapes below. Always UTF-8. |
| `--collection`, `-c` | `sections`, or the source's broad tier: `pages` (OLG), `chapters` (FNS, CMR), `parts` (CFR) | `sections` | search | A tier the source doesn't have → exit 2. With `--exact` → exit 2. |
| `--mode` | `dense`, `sparse`, `hybrid` | `dense` | search | `sparse` or `hybrid` with a broad collection → exit 2 (the sparse index covers sections only). Missing sparse index → exit 3. With `--exact` → exit 2. See [Choosing a mode](#choosing-a-mode). |
| `--top`, `-n` | integer | search: `5`; exact: all results | search, exact | |
| `--threshold`, `-t` | 0 to 1 | `0` (no cut-off) | search, dense mode | Drops results below this similarity. Has no effect in sparse or hybrid mode. With `--exact` → exit 2. |
| `--programs` | comma-separated program names | none | search, exact | Keep only these programs. Preferred over the two legacy flags below, and wins if they're combined. |
| `--program`, `-p` | one program name | none | search, exact | Legacy single-program form. |
| `--exclude-programs` | comma-separated program names | none | search, exact | Legacy. Drop these programs. |
| `--context` | (switch) | off | search, exact | Adds the parent page, chapter or part as `parent_context`. Section results only; broad-tier results get `null`. |
| `--full` | (switch) | off | search, exact | Text output only: don't truncate. No effect on JSON, which always has the full text. |
| `--chunk-id` | a chunk id | | chunk lookup | An id that doesn't exist gives `chunk_count: 0` and exit 0. |
| `--neighbors` | integer | `0` | chunk lookup | Also return N chunks before and after, within the same parent section or page. Ignored by other commands. |
| `--url` | an OLG page URL | | page lookup | Every section chunk of that page. With `--source` other than `olg` → exit 2. |
| `--exact` | a phrase | | exact | An empty or whitespace-only phrase → exit 2. See [Exact phrase search](#exact-phrase-search). |
| `--list-programs` | (switch) | | source summary | |

**Program names** match case-insensitively against the names stored in the index
(`--list-programs` shows them). An unknown name is a usage error (exit 2) whose message
lists the valid names. **FNS ignores all three program flags**, as its sections carry no
program filter. The names `--list-programs` shows for FNS are labels only.

**The `OLG_PROGRAMS` environment variable** is set by an orchestrator, not by the
caller. When it's set, OLG searches and exact searches are limited to that
comma-separated list of programs. Program flags can narrow within the list but never
widen it. A filter entirely outside the list returns zero results with
`filters: {"olg_programs_guardrail": "no_match"}` and exit 0.

## JSON responses

All responses are a single JSON object on stdout, encoded as UTF-8. Every response has:

| Field | Type | Meaning |
|-------|------|---------|
| `contract_version` | string | `"1.0"` |
| `command` | string | `search`, `exact`, `chunk`, `url` or `list` |
| `index` | object | The source's build dates. See [The `index` block](#the-index-block-and-the-two-kinds-of-date). |

### Search (`command: "search"`)

| Field | Type | Meaning |
|-------|------|---------|
| `query` | string | The query as given. |
| `source` | string | `olg`, `fns`, `cmr` or `cfr` |
| `collection` | string | The tier searched: `sections`, `pages`, `chapters` or `parts`. |
| `filters` | object | The program filter applied, with names as stored: `programs` (list), `program` (string) or `exclude_programs` (list). Empty when there's no filter. |
| `mode` | string | The mode that actually ran. |
| `result_count` | integer | Number of results. 0 is a normal, successful answer. |
| `results` | list | Best first. |

Each result:

| Field | Type | Null? | Meaning |
|-------|------|-------|---------|
| `rank` | integer | no | 1, 2, 3, ... |
| `id` | string | no | The chunk id (section tier) or document id (broad tier). |
| `text` | string | no | The full chunk text, including its context-prefix line. |
| `metadata` | object | no | See [Metadata](#metadata). |
| `score` | number | yes | Similarity from 0 to 1. See the table below. |
| `bm25_score` | number | yes | Sparse and hybrid only. |
| `rrf_score` | number | no | Hybrid only. |
| `parent_context` | object | yes | With `--context` on the section tier: `{text, metadata}` of the parent page, chapter or part. Otherwise `null`. |

Score fields by mode:

| Mode | `score` | `bm25_score` | `rrf_score` |
|------|---------|--------------|-------------|
| dense | dense similarity | (absent) | (absent) |
| sparse | `null` | BM25 score | (absent) |
| hybrid | dense similarity, or `null` for a result only BM25 found | BM25 score, or `null` for a result only dense found | fused score; results are ordered by it |

Scores compare results within one response. They aren't comparable across modes,
sources or index rebuilds.

### Exact phrase (`command: "exact"`)

| Field | Type | Meaning |
|-------|------|---------|
| `phrase` | string | The phrase as given. |
| `normalized_phrase` | string | The phrase after normalization; this is what was matched. |
| `source` | string | |
| `filters` | object | As in search. |
| `result_count` | integer | Results returned. |
| `total_results` | integer | Results before the `--top` cap. |
| `total_matches` | integer | Occurrences of the phrase across the source, after program filters. |
| `truncated` | boolean | `true` when `--top` cut results off. |
| `results` | list | Ordered as described under [Exact phrase search](#exact-phrase-search). |

Each result:

| Field | Type | Null? | Meaning |
|-------|------|-------|---------|
| `rank` | integer | no | |
| `id` | string | yes | The section chunk where the match starts. `null` when the match couldn't be placed in a chunk (see below). |
| `chunk_ids` | list of strings | no | Every chunk this result's matches span: more than one when a match crosses a chunk boundary. Empty when `id` is `null`. |
| `parent_id` | string | no | The page, chapter or part the match is in. |
| `match_count` | integer | no | Matches attributed to this result. |
| `snippets` | list of strings | no | Up to 3, each about 80 characters of normalized text either side of a match. |
| `text` | string | no | The chunk's full text, or the parent document's when `id` is `null`. |
| `metadata` | object | no | The chunk's metadata, the same keys a section search hit has. When `id` is `null`, the parent document's metadata (the broad-tier keys under [Metadata](#metadata)), with OLG's `title` also copied to `page_title`. |
| `parent_context` | object | yes | With `--context`: `{text, metadata}` of the parent. Otherwise `null`. |

### Chunk and page lookups (`command: "chunk"` / `"url"`)

| Field | Type | Meaning |
|-------|------|---------|
| `target_chunk_id` | string | The id asked for, or the URL for `--url`. |
| `source` | string | |
| `chunk_count` | integer | 0 when nothing was found (still exit 0). |
| `chunks` | list | `{id, text, metadata}`, in reading order. Neighbors outside the section or page are skipped, not padded. |

### Source summary (`command: "list"`)

| Field | Type | Meaning |
|-------|------|---------|
| `source` | string | |
| `programs` | list | `{program, chunk_count}` per program label, most chunks first. |
| `structure` | list or null | `{key, title, chunk_count}` per FNS or CMR chapter or CFR part, in order. `key` is the chapter or part number (integer). CMR entries also carry `program`. `null` for OLG. |
| `total_chunks` | integer | Section chunks in the source. |

### Errors

With `--json`, a failed run still prints one JSON object on stdout:

```json
{
  "contract_version": "1.0",
  "command": "search",
  "error": {"kind": "usage", "message": "...", "exit_code": 2},
  "index": { ... }
}
```

`index` is `null` when the source itself is invalid. `command` is the command that was
asked for. When the arguments can't be parsed, it's a best guess from them.

### Metadata

These `metadata` keys are guaranteed on every result from the named tier. Other keys
are present today but not promised.

| Source | Tier | Guaranteed keys |
|--------|------|-----------------|
| OLG | sections | `breadcrumb`, `page_title`, `parent_heading`, `section_heading`, `url`, `last_updated`, `program`, `parent_page_id`, `chunk_n`, `chunk_total` |
| OLG | pages | `breadcrumb`, `title`, `url`, `last_updated`, `program` |
| FNS | sections | `chapter` (integer), `chapter_title`, `section_number` (string), `section_title`, `handbook_pages`, `pdf_pages`, `parent_chapter_id`, `chunk_n`, `chunk_total` |
| FNS | chapters | `chapter` (integer), `chapter_title`, `handbook_pages`, `pdf_pages` |
| CMR | sections | `chapter` (integer), `chapter_title`, `section_number` (string), `section_title`, `program`, `pdf_file`, `parent_chapter_id`, `chunk_n`, `chunk_total` |
| CMR | chapters | `chapter` (integer), `chapter_title`, `program` |
| CFR | sections | `part` (integer), `part_title`, `subpart_title`, `section_number` (string), `section_title`, `program`, `pdf_file`, `parent_part_id`, `chunk_n`, `chunk_total` |
| CFR | parts | `part` (integer), `part_title`, `program` |

All values are strings unless marked. An empty string means the field doesn't apply.
For example, `section_heading` is empty for an OLG section with no heading.
`chunk_n` / `chunk_total` give the chunk's position in its section (OLG: page section),
counting from 1.

## The `index` block and the two kinds of date

Every JSON response says when the source's index was built:

```json
"index": {
  "source": "cmr",
  "record_status": "present",
  "stages": {
    "parse":  {"date": "2026-04-27", "completed_at": null, "counts": {"sections": 592, "pdfs": 18}},
    "chunk":  {"date": "2026-04-27", "completed_at": null, "counts": {...}},
    "embed":  {"date": "2026-05-04", "completed_at": null, "counts": {...}},
    "sparse": {"date": "2026-05-04", "completed_at": "2026-05-04T21:12:33-04:00", "counts": {"chunks": 1415}}
  }
}
```

- **Stages.** OLG has `scrape`, `chunk`, `embed` and `sparse`. FNS, CMR and CFR have
  `parse` in place of `scrape`. Every stage is always present.
- **`date`** is `YYYY-MM-DD`, or the string `"unknown"`.
  - The `embed` date is the date of the *oldest* embedded collection, so a result never
    looks fresher than its stalest tier.
  - The **scrape date** says how old the OLG content is: it's when the pages were
    fetched.
- **`completed_at`** is an ISO-8601 time with offset, or `null` when only the day is
  known. Dates reconstructed for the index built before build records existed have
  `null`.
- **`counts`** is an object whose keys vary by stage. **`details`** and **`note`** are
  optional and not promised.
- **`record_status`** is `present`, `missing` or `unreadable`. When it isn't `present`,
  every `date` is `"unknown"`. A missing record never fails a command.

**Two kinds of date — don't mix them up:**

- The `index` dates say when *this system* fetched or built its copy of a source.
- An OLG page's `last_updated` metadata (the "Updated" date) says when *the agency*
  last changed that page.

A page can show an "Updated" date years older than the scrape. Content changed after
the scrape date isn't in the index yet.

The text output of `--list-programs` ends with the same dates on one line, plus a
reminder of this distinction.

## Exact phrase search

`--exact "phrase"` finds literal occurrences of the phrase. It makes no Voyage call and
needs no API key.

- **What it searches.** The full text of every broad-tier document (OLG pages, FNS and
  CMR chapters, CFR parts), so it also finds a phrase that runs across two section
  chunks.
- **Normalization.** The phrase and the text are normalized the same way before
  matching:
  - case-folded;
  - quote variants become `'` or `"`;
  - dash variants (hyphen, non-breaking hyphen, en and em dash, minus, and others)
    become `-`;
  - Unicode spaces become a space;
  - zero-width characters and soft hyphens are removed;
  - Markdown heading markers (`#`) at line start are removed;
  - whitespace runs become one space, and the ends are trimmed.
- **Matching is a plain substring match.** `SNAP` also matches inside `SNAPshot`, and
  `10` matches inside `106`. Add surrounding words for precision.
- **Chunk attribution.** Each match is placed in the section chunk where it starts.
  - A match on a heading, or across a heading into its first sentence, lands on the
    chunk under that heading.
  - A match that can't be placed is still reported, against its parent document, with
    `id: null`. It is never dropped. This happens for text the section tier
    deliberately leaves out, such as 7 CFR § 272.1(g), the amendment history, and
    § 271.8, and for some tables laid out differently in the two tiers.
  - Measured on 400 sampled phrases (2026-11-21), matches attributed to a chunk: OLG
    98%, FNS 100%, CMR 97%, CFR 80% (the CFR gap is the deliberate exclusion).
- **Results.** One result per chunk containing at least one match, plus one per parent
  for matches that couldn't be placed.
- **Order.**
  - Parent documents with the most matches come first, ties broken by parent id.
  - Within a parent, results follow reading order, and the unplaced result comes last.
  - The order is deterministic for a given index.
- **No `--top` means every result.** With `--top N`, the first N are returned, and
  `total_results`, `total_matches` and `truncated` describe the rest.
- **Program filters** and `OLG_PROGRAMS` apply to each result's chunk metadata. An
  unplaced result uses the parent's program.
- **Not allowed with `--exact`:** `--mode`, `--threshold` and `--collection` (exit 2).
  They have no meaning for a literal search.

## Choosing a mode

| Use | For | Why |
|-----|-----|-----|
| `dense` (default) | Natural-language questions: "what counts as earned income for a student" | Ranks by meaning. Best on the retrieval benchmark. |
| `sparse` | Rare keywords and identifiers, when dense misses them | BM25 keyword ranking. It ranks documents by shared words; it does **not** match phrases or word order. |
| `hybrid` | A query that mixes a rare token with a question, as a second try | Dense and BM25 fused. Tested worse than dense on natural-language questions (below). |
| `--exact` | Exact wording, form names, section numbers, a sentence being revised: "which pages say X?" | Literal match over all text, every hit, nothing ranked away. |

**Why dense is the default.** On the retrieval benchmark (retrieval quality plan,
closed 2026-05-05), hybrid against dense:

| Source | Rel@1, dense | Rel@1, hybrid | Useful@5 |
|--------|--------------|---------------|----------|
| OLG | 62% | 46% | unchanged |
| CMR | 65% | 57% | unchanged |

Hybrid found the same chunks but put them in a worse order.
- Rel@1 is the share of benchmark queries whose top result a judge rated relevant.
- Useful@5 is the average number of useful results in the top 5 (dense scored about
  5 out of 5).

On section-number and acronym queries, sparse alone did retrieve the right chunks,
but fusing it with dense didn't carry them to the top. Hence: try `--mode sparse`
(or `--exact`) when a query hinges on an identifier.

## Exit codes and stderr

| Code | Kind | Meaning |
|------|------|---------|
| 0 | | Ran fine. `result_count` (or `chunk_count`) may be 0, which is a real answer. |
| 2 | `usage` | Bad or conflicting arguments, an unknown program name, an empty `--exact` phrase. |
| 3 | `unavailable` | Missing `config.ini` or Voyage API key, missing ChromaDB directory or collection, missing sparse index. (`--exact` needs neither config nor key; `--list-programs` doesn't need the key.) |
| 4 | `api` | The Voyage API call failed (network, authentication, rate limit after retries). |
| 5 | `internal` | Anything unexpected. The message names the exception type. |

- **stdout carries only the response.** That's the JSON object with `--json`, or the
  text output otherwise. Nothing else.
- **stderr carries one line per error,** in this format:

  ```text
  query.py: error [<kind>]: <message>
  ```

  Only lines starting with `query.py:` are part of the contract. Libraries the CLI
  loads can print their own warnings to stderr, such as a torch "Redirects are
  currently not supported" note on Windows. Ignore those lines.
- **Tracebacks** are printed to stderr only when the environment variable
  `QUERY_DEBUG=1` is set.
- **A rate-limit wait** ("Rate limited — waiting…") is reported on stderr, and the run
  continues.

## Not promised

These may change without a version bump or notice:

- **The text output** (without `--json`), including `--full` and `--list-programs`
  text. Parse JSON instead.
- **Exact scores, and result order across index rebuilds.**
- **Chunk ids across an index refresh.**
  - OLG chunk ids come from the page's breadcrumb and position, so a page that moves
    or gains a section gets new ids.
  - Don't store chunk ids beyond the current index; store the URL or section number
    and look them up again.
  - Within one index, ids are stable.
- **Fields not listed in this document,** including extra `metadata` keys and the
  `index` block's `details` and `note`.
- **Speed.** A run takes several seconds to start (library imports). Search adds a
  Voyage call. `--exact` reads the whole source.

## Change rules

- **Adding** a field, flag, command or enum value bumps the minor version (`1.1`). No
  notice is needed. Callers must ignore fields they don't know.
- **Renaming or removing** a field, flag or command, or **changing** its meaning or
  type, bumps the major version (`2.0`). It needs a handoff to `business` before the
  change ships.
- **A planned index refresh** that will change chunk ids is announced to `business`
  with a handoff before it runs.
- The version is the `contract_version` string in every response and the heading of
  this document. Both change together.
