# RAG Parsing & Chunking Playbook

**Purpose**: A practical guide for adding new sources to Policy Navigator's RAG database. Captures techniques that emerged from cleaning up OLG (HTML), CMR (PDF), CFR (PDF), and FNS (PDF) pipelines. Use this when bringing in a new source so we don't relearn the same lessons.

**Audience**: Future Claude (and Ben) when standing up a new pipeline.

---

## Pipeline shape

Every source follows the same three-stage pipeline:

```
raw → parser → parsed_sections/*.json → chunker → chunks → embedder → ChromaDB
```

- **Parser**: source-specific extraction. Output: one JSON file per logical unit (page for OLG, section for FNS/CMR/CFR). Always one file per unit — easy to inspect, reprocess individually.
- **Chunker**: shared logic with source-specific tuning. Two outputs: broad-tier (chapter / page docs) and granular-tier (section chunks).
- **Embedder**: source-agnostic. Takes chunks, produces vectors via Voyage AI, writes to ChromaDB collection.

Same shape across all four sources. Adding a new source = wiring up these three with source-specific config in `config.ini` and registry entries in `embedder.py` / `query.py` / `ui/search.py`.

---

## Universal chunk size constants

All four chunkers share these:

```python
MIN_CHUNK_SIZE = 200       # below this, fold into a neighbor (when merging is allowed)
MAX_CHUNK_SIZE = 1500      # above this, split
TARGET_CHUNK_SIZE = 1000   # ideal split target
```

These are calibrated for `voyage-3` (1024-dim). Don't change them lightly.

**FNS adds one more** — `PREFIX_BUDGET = 200`. Reserved character budget for the context-prefix line that gets prepended to every chunk. The splitter targets `MAX_CHUNK_SIZE - PREFIX_BUDGET` for the body so final `prefix + body` text stays within `MAX_CHUNK_SIZE`. Adopt this when section titles are long enough that the prefix line can push otherwise-good chunks over MAX. (FNS section titles like "Income Exceeds Certified Household's Required Income Reporting Limit Due to a New Household Member(s) with Income AORD" are ~120 chars on their own.)

---

## Stage 1: Parser

### What every parser does

1. Extract raw text from the source (HTML scrape / pdfplumber / etc.)
2. Strip global noise (page headers, footers, UI artifacts, encoding glitches)
3. Detect section boundaries via source-specific patterns
4. Emit one JSON per section/page with: `text`, `tables`, `cross_references`, `pdf_pages`/`url`, `flags`, level/parent metadata, source-specific fields (`example_text`, `internal_links`, etc.)

### Chapter divider page stripping (PDF sources)

PDFs typically place a divider page between chapters showing:
```
Chapter 12

MAKING THE REVIEW DECISION
```

Without stripping, this content gets attached to the LAST section of the previous chapter (because the parser's section-detection regex doesn't match `Chapter NN` or the all-caps title). Result: the last section's chunks end with "Chapter 12 MAKING THE REVIEW DECISION" garbage.

**Fix in the parser, per-line strip**:
- `^Chapter\s+\d{1,2}\s*$` — bare `Chapter N` line
- `^Chapter\s+\d{1,2}\s+[A-Z][A-Z\s]{3,}$` — combined `Chapter N TITLE` line (catches the post-flattening case)
- Any line that exactly matches an upper-case chapter title from the source's `CHAPTER_TITLES` dict — strips the standalone title line

These belong in `_clean_page_text` alongside header/footer regexes — applied per-line during page cleaning, before section assembly and soft-wrap flattening.

### Soft line-wrap flattening (PDF sources)

PDF text extraction wraps lines at the visual column width. These wraps have no semantic meaning — they're layout artifacts. Without flattening, downstream chunks read like this:

```
PURPOSE.
Each State agency is responsible for conducting QC
reviews as part of its Performance Reporting System.
For QC reviews, a statistical
sample of households...
```

The mid-sentence breaks (`QC\nreviews`, `statistical\nsample`) make embedded text noisy and hurt UI display. Flatten them in the parser.

**Rules** (apply line-by-line; keep the line break only when):

1. Next line is a structural element (bullet, numbered/lettered item, table row, paren-marker)
2. Next line is blank (paragraph separator)
3. Previous line ends with `.!?` AND next line starts with a capital letter (real paragraph break)

Otherwise the break is a soft wrap — replace it with a single space.

Implementation: see `_flatten_soft_wraps()` in `rag/fns/parser.py`. Apply at the section-text level (in `_enrich_section`), so it operates on the assembled section after page-text concatenation. This catches cross-page soft wraps as well as within-page ones.

**HTML sources don't need this** — the scraped HTML already has clean paragraph structure.

### Visual paragraph clarity — insert blank lines at real boundaries

PDF extraction strips the original visual layout. After soft-wrap flattening, the parser keeps semantic line breaks but doesn't add blank-line separators. This leaves chunk text like:

```
• Last bullet of a list.
If an expense qualifies as both a dependent care deduction and a medical deduction, ...
A household may not deduct the following expenses:
• Premium A
• Premium B
```

Without blank lines, a reader can't tell whether the prose paragraph is a continuation of the bullet above or a new paragraph after the list ended. Fix: insert a blank line whenever the parser preserves a real paragraph break (sentence end + capital start) AND specifically when transitioning from a bullet/structural line back to prose.

**Where to insert blanks**:
- After a bullet/list item, before a non-bullet PROSE line → mark list end clearly
- Between two prose paragraphs at a real paragraph break → standard paragraph separator
- Before a bullet/list when prev is non-structural prose AND prev does NOT end with `:` → clear "prose, then new list" transition

**Where NOT to insert**:
- Between sibling bullets (within a list)
- After a list intro ending with `:` and before the first bullet (intro flows directly into list)
- When prev is already blank (avoid stacking)

Side benefit: the chunker's `BLANK → PROSE` break-priority rule fires on these blanks, slightly elevating paragraph-break score from 45 to 60.

### Page header / footer stripping

PDF headers and footers leak into extracted text otherwise. Build regex patterns matching the literal header/footer strings. **Make them case-insensitive** — the same header may appear as `FNS HANDBOOK 310` in body pages and `FNS Handbook 310` in side-by-side example boxes. Caught us once on FNS.

For FNS-style "PDFs with column-aware extraction":
- Apply header/footer cleaning to BOTH columns (left main text AND right example_text)
- We missed this initially; right-column content had `FNS Handbook 310` mid-text

### Side-by-side / multi-column PDF handling

Some pages have two columns (policy text + example box). If the parser uses column-aware extraction, both columns should:
1. Get cleaned (header/footer strip)
2. Be preserved on the section dict (e.g., `text` for left, `example_text` for right)
3. Get incorporated into chunk body before splitting (the chunker reads `example_text` and appends it)

Easy bug: parser captures `example_text` but the chunker ignores it. Result: substantial content gets dropped. Verify each side-by-side flagged section has its example content reaching the chunks.

### Table extraction

Two strategies, both used:
- **Inline placeholder + structured tables list**: parser leaves `[Table]` markers in text, attaches structured table dicts to the section. Used by OLG.
- **Tables-only sidecar**: parser extracts tables separately, chunker appends them to section text after main prose. Used by FNS, CMR, CFR.

Either works. The chunker's responsibility: render structured tables as pipe-delimited markdown (`| h1 | h2 |` / `| --- | --- |` / `| c1 | c2 |`) and append to the body before splitting.

**Manual rewriting**: some PDF tables (multi-column flowing tables, flowcharts labeled "Chart N", hierarchical decision trees) extract as garbled text. CFR had 16 such tables across 273.18 / 275.3 / 275.11 — manually rewritten as flowing prose directly in the parsed section JSONs. Document the rewrites in a `docs/<source>_cleanup/findings.md` so they can be redone if the JSONs are regenerated.

### Section number / boundary detection

Source-specific. Patterns we've seen:

| Source | Pattern | False positives to guard against |
|---|---|---|
| FNS | Numbered sections at line start: `100`, `1021.1`, `820.5` | Inline references like "See Section 622" — require pattern at line start with capitalized title following |
| CMR | `XXX.XXX:` headings filtered by chapter prefix | Cross-references to other chapters |
| CFR | `§ XXX.X` markers | Subpart letter reuse across parts |
| OLG | HTML H2/H3 headings within the page widget | (HTML — not an issue) |

**Always validate**: count detected sections, spot-check against source navigation. CMR's filter-by-chapter-prefix was load-bearing; without it, a phone number `(866) 632-9992` got detected as section header.

### Multi-line title detection (PDF)

PDF section titles often wrap across two visual lines. The parser must look ahead: a heading match captures only the first line; concatenate continuation lines if they're not structural markers and don't match the next heading pattern. CMR's parser does this; it's a common gotcha.

---

## Stage 2: Chunker

### Two-tier output

Every source produces TWO chunk sets:
- **Broad tier** (`pages` / `chapters` / `parts`): one document per top-level container. Used for topic discovery via wider similarity.
- **Granular tier** (`sections`): one chunk per parsed unit (or N chunks if oversized). Used for specific-answer retrieval.

Both go in ChromaDB as separate collections.

### Section merging (cross-section)

**Rule (per Ben's "no two sections in one chunk" call)**: never merge content from two distinct named sections into one chunk. Small sections stay small.

OLG had a bug here pre-cleanup: `merge_small_sections()` was bleeding H2 content into H3 chunks. Fixed by requiring same `parent_section` AND same `level` for merges, OR one side being heading-less intro content.

FNS goes further: cross-section merging is **disabled entirely**. Each FNS section becomes its own chunk(s). Sections like §513 "Evaluating Evidence." that are 99-char heading-only stubs stay as 99-char chunks. They're traceable, citable, and link to children via `parent_section`.

Adopt the FNS rule for any new source unless there's a strong reason to merge.

### Context prefix

Every chunk's text starts with a context-prefix line followed by a blank line and then the body:

```
FNS 310 > Chapter 10: Income > 1045.2 Dividends and Interest

Dividends and Interest. Reviewers must obtain statements...
```

The prefix is part of the embedded text — Voyage AI sees it. This anchors the chunk in its hierarchy without polluting the metadata.

**Format consistency across sources**:
- OLG: `Business Process (BP) > BP Overview > AU Mass Assignment > <Page Title>`
- CMR: `106 CMR 363 > SNAP FINANCIAL > 363.140 Noncountable Assets`
- CFR: `7 CFR 271 > General Information and Definitions > § 271.2 Definitions > Access device`
- FNS: `FNS 310 > Chapter 10: Income > 1045.2 Dividends and Interest`

Pattern: `<source-id> > <chapter/part-title> > <section-number section-title>`. CMR / CFR add a sub-topic level when hierarchy markers are present (`(D) Vehicles`, `Access device`).

**Do NOT include `(part N of M)` in the prefix.** Position info lives in `chunk_n` / `chunk_total` metadata — that's the canonical source. We tried adding `(part N of M)` to the FNS prefix initially; it diverged from the other sources for no benefit. Display layers (CLI, UI, synthesis) read the metadata and render position however they want.

### Position metadata (REQUIRED on every chunk)

Three fields, every chunk:

```python
"hierarchy_path": "1045.2 Dividends and Interest",  # section number + title (or marker like "(D) Vehicles" for CMR)
"chunk_n":        2,        # 1-indexed position within section's split sequence
"chunk_total":    3,        # total chunks for this section
```

A section that fits in one chunk has `chunk_n=1`, `chunk_total=1`. Always populate both, never set to `None`.

### Program tag (filterable category)

Every chunk gets a `program` metadata field. The UI checkbox panel and CLI `--program` flag read this for explicit-include filtering.

**Ben's philosophy**: every program tag must be explicitly included via UI checkbox or CLI flag. No silent default filtering. UI pre-checks the most common values; user widens the net by clicking more checkboxes.

| Source | Program values |
|---|---|
| OLG | `SNAP`, `TAFDC`, `EAEDC`, `Cross-Program`, `BP` |
| CMR | `SSP`, `Hearings`, `SNAP`, `Program Integrity`, `EA` |
| CFR | `SNAP`, `Issuance`, `Administration`, `QC`, `Disaster`, `Summer-EBT` |
| FNS | `SNAP` (Ch 7-11, 13), `QC_Process` (Ch 1-6, 12, 14) |

Map at the broadest natural unit (chapter / part for PDF sources; book / section for OLG). A static dict is sufficient; no per-section override list needed unless really required.

### Break-priority splitter (the splitter algorithm)

When a section exceeds `MAX_CHUNK_SIZE` (or `MAX_CHUNK_SIZE - PREFIX_BUDGET` if you've adopted the prefix budget), split using a break-priority algorithm.

**Algorithm**:
1. Split text into lines on `\n`
2. Pre-process: split long prose lines at internal sentence boundaries (`. [A-Z]` patterns) so the line-boundary algorithm has more candidates inside continuous paragraphs that PDF extraction merged together
3. Classify each line by structural type (bullet, numbered, table row, sub-bullet, prose, blank)
4. Greedily accumulate lines until cumulative size exceeds MAX
5. Walk back to find the highest-priority break candidate within `[MIN..MAX]` window
6. Break before that candidate; restart accumulation with the current line as the new chunk's first line
7. Final pass: any chunk still > MAX gets sentence-split (last resort hard slice)

**Break score table** (FNS-tuned, copy as a starting point):

| Pattern | Score | Why |
|---|---|---|
| Sub-heading detected (cur is short prose ending with `.!?`) | 65 | Topic introducer — group with content |
| Definition entry pattern (`Term – Definition`) | 65 | Clear lexical boundary |
| BLANK → PROSE with prev ends sentence + cur capital | 60 | Real paragraph break |
| Exiting a table (last table row → prose) | 70 | Clean table/prose transition |
| Entering a table (TABLE_HDR after non-table) | 85 (5 if prev ends `:`) | Topic transition |
| Entering a top-level bullet (BULLET_TOP after non-bullet) | 80 (5 if prev ends `:`) | Topic transition |
| Entering a numbered list | 80 (5 if prev ends `:`) | Topic transition |
| Sentence-end + capital start (PROSE → PROSE paragraph break) | 45 | Real paragraph |
| BLANK → PROSE without sentence-end signal | 35 (cur capital) / 10 (cur lowercase) | Stray PDF blank, not a real paragraph |
| Sibling top-level bullets (mid-list) | 25 | Mid-list fallback only — paragraph breaks (45) win |
| Sub-bullet (BULLET_SUB) — never break before | 0 | Forbidden |
| Inside table header / separator | 0 | Forbidden |

**Forbidden** breaks (score 0):
- Before a sub-bullet line (`➢ ▪ ○ -`) — sub-bullets are continuations of their parent top-level bullet
- Before a TABLE_SEP line (would orphan separator from header)
- Right after a TABLE_HDR or TABLE_SEP line (would orphan the table)

### List-intro orphan prevention

When the line just BEFORE a structural element (bullet / numbered / table) ends with `:`, that line is the list intro. Breaking between intro and list orphans context. Penalize structural-entry scores in this case (drop to 5).

Example: `"To establish... must verify all four parts below:" / "1. There is..."` — the colon signals the intro for the numbered list. Break score before "1." drops from 80 to 5.

This was a real bug we hit on §848.1.

### Sub-heading detection

A line is a sub-heading if:
- Length ≤ 100 chars
- Ends with `.!?`
- Starts with a capital letter
- Not a bulleted/numbered/lettered list item

Examples: `"Verification."`, `"Application processing."`, `"Four-part test to establish fleeing felon status."`, `"Alternative test to establish fleeing felon status (also known as the Martinez test)."`

When detected, breaking BEFORE a sub-heading scores 65 (very high — topic introducer). When the PREVIOUS line is a sub-heading, breaking AFTER it scores 15 (penalty — would orphan heading at chunk end).

Apply this rule **regardless of prev's class** (works whether prev is a list item ending the previous topic, a paragraph end, or a blank line). FNS hit a bug where sub-heading detection only fired when prev was PROSE; expand to all "sentence/list-end" prev classes.

### Definitions-section handler

Sections whose title contains "DEFINITION" (or is exactly "Definitions") need a dedicated handler — the break-priority splitter does the wrong thing on lists of defined terms. Use one chunk per defined term, regardless of size. Mirrors CFR's `chunk_definitions()` for 271.2 / 292.2.

**Detection**: section title (case-insensitive) contains "DEFINITION".

**Entry pattern**: a line starting with a capitalized term followed by either:
- A dash separator: ` – ` (en-dash), ` — ` (em-dash), ` - ` (hyphen with surrounding spaces)
- A defining verb: ` means `, ` refers to `, ` is `, ` Is `

**Critical regex constraint**: the term character class must EXCLUDE comma, period, colon, etc. Otherwise the lazy regex matches across mid-sentence "is" verbs in a long sentence (e.g., "The review date should never be the effective date of the action, unless the effective date is the same..." would falsely split at "is").

```python
_FNS_DEFINITION_ENTRY = re.compile(
    r"^([A-Z][A-Za-z0-9()&/' \-]{2,80}?)"
    r"(?:\s+[–—]\s+|\s+-\s+|\s+(?:means|refers to|[Ii]s)\s+)"
    r"\S"
)
```

**Output**: each defined term becomes its own chunk. Lines between definition starts (continuations, sub-bullets, examples) attach to the preceding term's chunk. Oversized single definitions split at sentence boundaries; sub-chunks all carry the term label.

For FNS, this caught §1320 NEGATIVE DEFINITIONS (11 terms) and §130 DEFINITIONS (much larger).

### Hierarchy-aware splitting (CMR / CFR style)

For sources with consistent within-section markers (CMR's `(A)→(1)→(a)→1.` or CFR's `(a)→(1)→(i)→(A)`), define a `<SOURCE>_HIERARCHY` profile: list of `(level, regex)` tuples.

```python
CMR_HIERARCHY = [
    (1, re.compile(r'^\([A-Z]{1,2}\)\s+(.+)')),
    (2, re.compile(r'^\(\d{1,2}\)\s+(.+)')),
    (3, re.compile(r'^\([a-z]\)\s+(.+)')),
    (4, re.compile(r'^\d+\.\s+(.+)')),
]
```

Pre-scan the section to find the lowest-level marker present (top_level). Break preferentially at top_level marker boundaries. The hierarchy_path metadata for split chunks then carries the marker label (e.g., `(D) Vehicles`).

**FNS does NOT have nested paren markers** — it's mostly prose with bullet lists. Use the bullet-priority splitter instead.

Each source picks one or the other based on its actual structure. A quick `grep` / regex profile of the parsed text shows which patterns dominate.

### List integrity — keep lists together

Lists (bulleted or numbered) should stay in one chunk unless the list itself exceeds MAX. When the chunker is forced to break and finds itself between MIN and MAX with mid-list as the in-range option, look back BEFORE the list's intro paragraph for a higher-priority break — even if that earlier break creates a slightly-undersized chunk.

Implementation: in walk-back, track two best candidates:
- `best_in_range` — best break in `[MIN..MAX]` window
- `best_below_min` — best break in `[HARD_MIN..MIN]` window (`HARD_MIN = 100`)

If `best_in_range` is a low-priority break (score < 60, e.g., mid-list) AND `best_below_min` is a high-priority break (score >= 60, e.g., entering a list), prefer the below-MIN candidate. This sacrifices a slightly-small chunk to preserve list integrity.

Example: §1360 ACCEPTABLE DOCUMENTATION has heading (30 chars) + intro paragraph (180 chars) + 3 bullets (~1100 chars). With strict MIN, the chunker would break mid-list. With this rule, chunk 1 = heading + intro (210 chars, just at MIN), chunk 2 = all 3 bullets together.

### Continued-table headers

When a split crosses mid-table, prepend the table's header row (and separator row) to the start of the second chunk so it stands alone:

```
| Header A | Header B |
| --- | --- |
| ... continued rows ...
```

In practice the break-priority algorithm prefers between-table breaks, so this rarely fires — but when it does (large tables), it prevents orphan rows.

### Stable, readable chunk IDs

```
fns_sec_1021_1__000      (FNS section 1021.1, chunk 0)
cmr_sec_362_330__004     (CMR 362.330, chunk 4)
cfr_sec_271_2__012       (CFR § 271.2, chunk 12)
sec__SNAP__AppProcessing__... (OLG slug-based)
```

Per-section indexing — chunks of the same section get consecutive `__NNN` suffixes. Don't use global-per-chapter indexing; per-section is more debuggable and stable.

---

## Stage 3: Embedder

Source-agnostic, no per-source code needed. Wire up:
- `_resolve_source_paths()` in `rag/embedder.py` — one dict entry mapping source name → file paths
- `_resolve_source_config()` — collection name resolution
- `config.ini` — `[<source>]` section, `[chromadb]` collection-name entries

Then `python rag/embedder.py --source <name>` works.

**Critical**: document embeddings are created WITHOUT `input_type="document"`. Queries must NOT use `input_type="query"` — asymmetry would degrade results. This is a global property of the system.

---

## Validation patterns

After regenerating chunks, before re-embedding, run these checks:

### Numerical sanity

```python
# Section count consistency
total_sections_seen = sum(1 for c in chunks if c['metadata']['chunk_n'] == 1)
parsed_count = len(list(Path("index/<source>/parsed_sections").glob("*.json")))
assert total_sections_seen == parsed_count

# Position metadata
assert all('hierarchy_path' in c['metadata'] for c in chunks)
assert all('chunk_n' in c['metadata'] for c in chunks)
assert all('chunk_total' in c['metadata'] for c in chunks)

# Program tagging
assert all('program' in c['metadata'] for c in chunks)
```

### Boundary quality

For each multi-chunk section, classify the transition between consecutive chunks:
- **Clean paragraph**: prev ends with `.!?` AND next starts with capital letter
- **Clean structural**: next starts with bullet / numbered / table / known structural marker
- **Worth inspecting**: anything else

Aim for ~95%+ of boundaries in the first two categories. Worth-inspecting cases are usually:
- Tabular content the parser couldn't extract as a `tables` field (manual rewrite territory)
- Side-by-side parser failures (parser-side fix)
- Real residual mid-sentence breaks (chunker tuning)

### Mid-word check

Concatenate `last_token_of_prev_chunk + first_token_of_next_chunk`. If the result is a single alphabetic token (no whitespace, no punctuation), you've broken mid-word. Should be 0.

### Spot-check sample

Pull one chunk per chapter / section type and eyeball it. Look for:
- Clean text (no `\n` mid-sentence)
- Readable prose
- Tables intact
- Bullet lists intact (not split across chunks unless list itself exceeds MAX)
- Sub-headings travel with their content

---

## Effort tiering for cleanups

When cleaning up an existing source, tier the work:

**Tier 1 — universal mechanical fixes** (apply to all chunks regardless of priority):
- Splitter algorithm
- Soft-wrap flattening
- Position metadata
- Program tagging
- Cross-heading merge protection
- Continued-table headers
- Hierarchy profile / break score table

**Tier 2 — high-priority sections only** (manual touch-ups for the chapters/sections the user actually queries):
- Garbled tables → manual prose rewrites
- Charts / flowcharts → prose decision trees
- Side-by-side parser failures
- Definition-section special handling

**Tier 3 — skipped** for sections the user doesn't prioritize. The Tier 1 mechanical fixes still help these chunks automatically; we just don't audit them before re-embedding.

This tiering came from FNS cleanup: SNAP chapters got full attention, QC_Process chapters got Tier 1 only.

---

## Deferred-list / TODO patterns

When a cleanup touches a source, capture:
- A `docs/<source>_cleanup/plan.md` — the phased plan
- A `docs/<source>_cleanup/findings.md` — numerical findings, manual rewrites done
- A `docs/<source>_cleanup/retrieval_benchmark.md` — before/after benchmark scores (CMR pattern)

These persist beyond the cleanup so future-Claude can check what was done and why.

For ongoing TODOs that affect future work, add memory entries (`~/.claude/projects/<project>/memory/`).

---

## Quick reference — adding a new source

1. **Stand up the parser**: source-specific code, output one JSON per logical unit
2. **Define hierarchy profile** (if applicable) — regex patterns for within-section markers
3. **Define program mapping** — broadest unit → program label dict
4. **Copy a chunker** from a similar source, adapt the splitter / hierarchy / context prefix
5. **Wire up config + registries**:
   - `config.ini` — `[<source>]` section, collection names in `[chromadb]`
   - `rag/embedder.py` — `_resolve_source_paths()`, `_resolve_source_config()`
   - `rag/query.py` — `_resolve_source_paths()`, `_resolve_source_config()`
   - `tools/synthesis.py` — source registration if needed
   - `ui/search.py` — UI source registry
6. **Run parser → chunker → validate** before any embedding
7. **`python rag/embedder.py --source <name> --dry-run`** to confirm cost
8. **Embed** (gated on user go)
9. **Test queries** — `rag/query.py --source <name> "test"` and full-corpus Ask
10. **Document** — `docs/<source>_pipeline.md`

---

## Lessons learned (chronological)

A short log of "we hit this once" gotchas that aren't obvious upfront:

- **OLG**: MadCap Flare scrape captured `View/Hide` button text into chunks. Strip in parser.
- **CMR**: Phone area codes like `(866)` matched the `(\d+)` paragraph marker regex. Restrict to `\d{1,2}`.
- **CMR**: `(AA)`, `(BB)` markers in some chapters needed Level-1 regex expanded to `[A-Z]{1,2}`.
- **CFR**: Definition sections (271.2, 292.2) needed dedicated chunker — each defined term becomes its own chunk regardless of size.
- **CFR**: 16 multi-column tables extracted as scrambled garbage. Manually rewritten as prose.
- **FNS**: Side-by-side example boxes — parser captured `example_text` but chunker dropped it. Always verify both columns reach chunks.
- **FNS**: Page header regex was case-sensitive. Right-column boxes use mixed case (`FNS Handbook 310`). Make case-insensitive.
- **FNS**: PDF column-wrapping → mid-sentence `\n` artifacts. Soft-wrap flattening required.
- **FNS**: List intros ending with `:` getting orphaned from their lists — penalize structural-entry breaks when prev ends with `:`.
- **FNS**: Long sub-heading lines (~95 chars like "Alternative test...") need a permissive (≤100 char) sub-heading threshold.
- **FNS**: `(part N of M)` in chunk text prefix diverged from OLG/CMR/CFR conventions. Removed for consistency — position lives in metadata only.
- **FNS**: Mid-list breaks happened because the walk-back's MIN check stopped before reaching the high-priority "entering list" break. Allow chunks below MIN when the alternative is a low-priority mid-list break.
- **FNS**: §1320 NEGATIVE DEFINITIONS needed the same treatment as CFR's 271.2 — title-based detection ("DEFINITION") triggers the dedicated definitions handler.
- **FNS**: Chapter divider pages ("Chapter 12 / MAKING THE REVIEW DECISION") leaked into the last section of the previous chapter. Strip them in `_clean_page_text` per-line.
- **FNS**: List-end ambiguity (a stranded bullet followed by prose looks like bullet continuation). Fix by inserting blank lines at real paragraph breaks during soft-wrap flattening.
- **All**: Parsed_sections JSONs are the source of truth for everything downstream. Worth keeping clean.
