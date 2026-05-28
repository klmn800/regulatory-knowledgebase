# CMR Cleanup Plan

**Goal**: Raise CMR retrieval accuracy from 55% top-1 to 85%+ top-1.
**Approach**: Fix five root causes in the parser, chunker, and query layer, then re-chunk and re-embed.
**Cost**: ~$0.10 re-embedding. Zero LLM cost (all deterministic code changes).
**Benchmark**: 20-question test suite in `retrieval_benchmark.md`. Re-run after every reprocessing.

---

## Design Principles

These decisions emerged from studying the data and tracing how chunks flow through the system.

### Split smarter, not bigger

Raising MAX_CHUNK_SIZE would reduce splits but make embeddings fuzzier — one 1024-dim vector can't represent 5000 chars of diverse regulatory content well. It also consumes more synthesis token budget. The goal is: **each chunk is a coherent semantic unit at ~1500 chars**, split at natural topic boundaries instead of arbitrary size boundaries.

### Top-level hierarchy labels only

When a chunk falls mid-section, label it with the nearest top-level hierarchy marker — e.g., `(D) Vehicles` — not the full path `(D) Vehicles > (2) Fair Market Value > (a) determination`. Rationale:
- The embedding model already captures deeper detail from the body text itself
- The prefix's job is to add context that ISN'T obvious from the body alone
- Full paths waste prefix characters that could hold actual regulatory content (synthesis.py truncates chunk text to 1000 chars)
- Top-level gives maximum disambiguation per character

### Text prefix and metadata should match

The context prefix (baked into embedded text) and the metadata `section_title` field currently carry redundant information. Whatever label we use should go in both places consistently. No divergence.

### Source-specific hierarchy profiles

Different legal sources have different hierarchy patterns. Rather than hardcoding CMR patterns into the chunker, define hierarchy markers as a configurable profile. The splitting algorithm stays generic; only the patterns change per source. This prepares for CFR (federal regulations) which will have its own hierarchy conventions.

```python
# Hierarchy profiles: list of (level, compiled_regex) — source-specific
CMR_HIERARCHY = [
    (1, re.compile(r'^\([A-Z]{1,2}\)\s+(.+)')),  # (A) Topic  or (AA) Definition
    (2, re.compile(r'^\(\d{1,2}\)\s+(.+)')),      # (1) Sub-topic
    (3, re.compile(r'^\([a-z]\)\s+(.+)')),         # (a) detail
    (4, re.compile(r'^\d+\.\s+(.+)')),             # 1. item
]
```

When CFR arrives, define a `CFR_HIERARCHY` with its own patterns. The splitting function accepts the profile as a parameter.

### Chunk anatomy reference

```
CHUNK TEXT (embedded by Voyage AI, stored in ChromaDB "documents",
           read by Claude in synthesis, shown in UI preview):
┌─ TEXT PREFIX ────────────────────────────────────────────────┐
│ 106 CMR 363 > SNAP FINANCIAL > 363.140 Noncountable Assets  │
│   > (D) Vehicles                                            │
└─────────────────────────────────────────────────────────────-┘

(D) Vehicles.
(1) One licensed vehicle per adult household member is excluded
from countable assets regardless of its value...

METADATA (separate structured fields in ChromaDB, used for
          filtering, display, citations):
  section_number: "363.140"
  section_title:  "Noncountable Assets"        ← always the ORIGINAL title
  program:        "SNAP"
  hierarchy_path: "(D) Vehicles"               ← NEW: sub-topic label
  chunk_n:        4                            ← NEW: position in section
  chunk_total:    7                            ← NEW: total chunks for section
```

### Who consumes what

| Consumer | What it sees | How label changes help |
|----------|-------------|----------------------|
| **Voyage AI** (embedding) | Full chunk text incl. prefix | Hierarchy label in prefix → tighter, more specific vector |
| **Claude** (synthesis) | First 1000 chars of text + metadata citation header | Better citation: `[CMR 363.140 Noncountable Assets > (D) Vehicles]` instead of `(continued)` |
| **Web UI** | First 400 chars of text + metadata in result cards | User sees which sub-topic, plus "Part 4 of 7" |
| **query.py CLI** | Formatted metadata fields | Debuggable output with position info |
| **Program filter** | `metadata.program` field | Unaffected by label changes; cross-program fix is separate |

---

## CMR Legal Text Hierarchy — Analysis Results

Studied across 15+ sections in chapters 327, 343, 362, 363, 364, 366, 367, 703, 704.

### Consistent nesting order (never varies)

```
(A) Top-level category          ← Level 1: uppercase letter in parens
  (1) Numbered item             ← Level 2: number in parens
    (a) Lettered sub-item       ← Level 3: lowercase letter in parens
      1. Numbered detail        ← Level 4: number with period
        a. Lettered detail      ← Level 5: letter with period (rare)
```

### Key facts that make hierarchy-aware splitting feasible

- **Nesting order NEVER varies** — `(A)` always contains `(1)` which contains `(a)`
- **Markers ALWAYS appear at line start** — never mid-sentence → reliable regex detection
- **Every section uses hierarchy** — no pure-prose sections found across all sampled chapters
- **Depth varies (1-5 levels)** but structure is predictable
- **Top-level items are descriptive** — e.g., `(A) Musculoskeletal System`, `(D) Vehicles`, `(B) Exclusions from Lump Sum Income` → natural chunk context labels

### Regex validation results (tested against all 592 sections)

| Level | Pattern | Matches | Sections |
|-------|---------|---------|----------|
| 1 | `^\([A-Z]{1,2}\)\s+` | 1,290+ | 315 |
| 2 | `^\(\d{1,2}\)\s+` | 1,572 | 207 |
| 3 | `^\([a-z]\)\s+` | 1,017 | 103 |
| 4 | `^\d+\.\s+` | 334 | 33 |

**Coverage**: 315 of 592 sections have Level 1 markers. 13 sections use Level 2 only (no Level 1) — the algorithm handles this via `top_level` pre-scan. No sections use Level 3 without also having Level 1 or 2.

**False positive found and fixed**: Phone area codes `(866) 632-9992` and `(617) 994-6000` in section 360.200 matched the original Level 2 pattern `^\(\d+\)\s+`. Fix: restrict to 1-2 digit numbers — `^\(\d{1,2}\)\s+`. Highest legitimate CMR sub-item number found was `(26)`. Area codes are always 3 digits.

**Multi-letter markers**: Sections 701.600 and 704.250 use `(AA)`, `(BB)` through `(MM)` as hierarchy markers. Pattern expanded to `^\([A-Z]{1,2}\)\s+` to capture these. Three-letter abbreviations like `(VSB)`, `(HHS)`, `(DCS)` appear mid-sentence in other sections and are correctly excluded by the 1-2 letter limit.

**No other false positives found** across Levels 1, 3, or 4.

### Critical finding: parsed text uses `\n` only, not `\n\n`

CMR parsed section text uses **single newline** (`\n`) separators throughout. There are zero `\n\n` double-newline boundaries. Verified across 703.192, 363.140, 364.400, and 362.310.

Raw text example:
```
...prevents their use.\n(B) Special Senses and Speech.\n(1) Impairment of...
```

**Consequence for the current splitter**: `split_large_section()` tries `\n\n` first, gets one giant segment, falls back to splitting at `\n`. Every individual line becomes a segment. The greedy packer then groups lines until hitting MAX_CHUNK_SIZE — with no awareness of which lines are hierarchy boundaries.

**Consequence for our fix**: Hierarchy markers ARE reliably at the start of `\n`-split lines. The algorithm works at line granularity, not paragraph granularity. This is actually better — finer control over where to break.

### Example: 703.192 top-level items (53 chunks today)

```
(A) Musculoskeletal System         (B) Special Senses and Speech
(C) Respiratory System             (D) Cardiovascular System
(E) Digestive System               (F) Genitourinary System
(G) Hemic and Lymphatic Systems    (H) Skin
(I) Endocrine System               (J) Multiple Body Systems
(K) Neurological System            (L) Mental Disorders
(M) Immuno-suppressive Disorders   (N) Neoplastic Diseases
(O) Medically Equivalent Impairment(s)
```

Each of these is a natural chunk boundary — a self-contained medical category.

---

## Phase 1: Parser Fix — Multi-line Title Detection

**File**: `rag/cmr/parser.py`, `extract_sections()` function

### Current behavior

Regex `(.+?)$` captures one line. Multi-line PDF titles get truncated or captured as body text fragments.

### Fix

After matching a heading, look ahead to concatenate title continuation lines. A line is part of the title if:
- It's not blank
- It doesn't start with `(A)`, `(1)`, or similar sub-item marker (use hierarchy profile regex)
- It doesn't match the section heading pattern (next section)
- It doesn't start with a lowercase letter suggesting body text

### Sections to validate against

| Section | Current (broken) title | Expected title |
|---------|----------------------|----------------|
| `703.192` | `"or the SSI Listing of Impairments..."` | TBD — verify against PDF |
| `703.720` | `"or has good cause as specified in..."` | TBD — verify against PDF |
| `366.115` | `"and recalculate the household's..."` | TBD — verify against PDF |
| `367.825` | `"are applicable to ADHs..."` | TBD — verify against PDF |

Plus 12 sections with titles >80 chars that likely captured body text.

### Pre-implementation: PDF verification

**Must do before coding.** Extract raw pdfplumber text around each broken section heading from the source PDFs. Confirm:
1. What the actual title text is
2. How the title wraps across lines in the PDF extract
3. Whether the look-ahead heuristic would correctly capture it

---

## Phase 2: Chunker Fixes

**File**: `rag/cmr/chunker.py`

### 2a. Hierarchy-aware splitting — Algorithm

Replace `split_large_section()` with a hierarchy-aware version. The algorithm operates on individual lines (since CMR text has only `\n` separators, not `\n\n`).

#### Hierarchy detection

```python
CMR_HIERARCHY = [
    (1, re.compile(r'^\([A-Z]{1,2}\)\s+(.+)')),  # (A) Topic  or (AA) Definition
    (2, re.compile(r'^\(\d{1,2}\)\s+(.+)')),      # (1) Sub-topic  (1-2 digits only, excludes phone area codes)
    (3, re.compile(r'^\([a-z]\)\s+(.+)')),         # (a) detail
    (4, re.compile(r'^\d+\.\s+(.+)')),             # 1. item
]

def classify_line(line, hierarchy_profile):
    """Return (level, label_text) or (None, None)."""
    for level, pattern in hierarchy_profile:
        m = pattern.match(line)
        if m:
            return level, line   # full line is the label
    return None, None
```

**Validated against all 592 parsed sections.** See "Regex validation results" above for details. Two fixes applied:
- Level 1 expanded to `{1,2}` letters to catch `(AA)`-`(MM)` markers in 701.600 and 704.250
- Level 2 restricted to `{1,2}` digits to exclude phone area codes like `(866)` in 360.200

#### Core algorithm

```
INPUT:  section dict (text field has \n-separated lines)
OUTPUT: list of chunk dicts, each with hierarchy_label, chunk_n, chunk_total

1. SPLIT text into lines at \n, discard blanks
2. CLASSIFY each line → (level, label) using hierarchy profile
3. PRE-SCAN: top_level = lowest level number present in the section
   (if section has (A) markers, top_level=1; if only (1), top_level=2; etc.)
4. ACCUMULATE with hierarchy-aware breaks:

   current_lines = []
   current_size = 0
   current_label = None          # top-level label for this chunk
   hierarchy_state = {}          # tracks active marker at each level
   chunks = []

   for each (line, level, label):
       line_size = len(line) + 1   # +1 for \n join

       # Update hierarchy tracking
       if level is not None:
           hierarchy_state[level] = label
           # Clear all levels below (entering new (B) resets (1), (a), etc.)
           for l in range(level + 1, 6):
               hierarchy_state.pop(l, None)

       # Decide whether to start a new chunk
       must_break = (current_size + line_size > MAX_CHUNK_SIZE) and current_lines
       prefer_break = (level is not None
                       and level <= top_level
                       and current_size >= MIN_CHUNK_SIZE)

       if must_break or prefer_break:
           chunks.append((current_lines, current_label))
           current_lines = []
           current_size = 0
           current_label = hierarchy_state.get(top_level)

       # First top-level marker in this chunk becomes its label
       if current_label is None and level is not None and level <= top_level:
           current_label = label

       current_lines.append(line)
       current_size += line_size

   # Flush remaining
   if current_lines:
       chunks.append((current_lines, current_label))

5. BUILD output: for each (lines, label) in chunks, create section dict
   with text="\n".join(lines), hierarchy_label=label, chunk_n, chunk_total
```

#### Walk-through: 703.192

```
Lines 1-15:  Intro (~600 chars), no hierarchy markers
Line 16:     (A) Musculoskeletal System    → Level 1 detected
             Accumulator has ~600 chars >= MIN_CHUNK_SIZE (200)
             → prefer_break! Flush intro as Chunk 1 (label: None)
             Start new accumulation, current_label = "(A) Musculoskeletal System"

Lines 16-44: (A) content (~1200 chars), sub-items (1), (a), 1. etc.
Line 45:     (B) Special Senses           → Level 1 detected
             Accumulator has ~1200 chars >= MIN_CHUNK_SIZE
             → prefer_break! Flush as Chunk 2 (label: "(A) Musculoskeletal System")
             Start new accumulation, current_label = "(B) Special Senses and Speech"

...continues for each (A)-(O) marker...

(L) Mental Disorders content: ~5000 chars, exceeds MAX_CHUNK_SIZE
  → must_break fires mid-(L). Chunk carries label "(L) Mental Disorders"
  → Next chunk also gets "(L) Mental Disorders" (still the active top-level)
  → Within (L), Level 2 markers (1)-(9) exist. If must_break hasn't fired
    but current_size >= MIN_CHUNK_SIZE and we see a new (1), prefer_break fires.
```

#### Edge cases

| Case | Behavior |
|------|----------|
| Section fits in one chunk | No split, no hierarchy label. Returns original section as-is. |
| Section has no Level 1, only Level 2 | `top_level=2`. Break points are `(1)`, `(2)`, etc. |
| Section has no hierarchy markers at all | Falls back to size-only splitting. Labels are `None` → use `"(part N of M)"` fallback. |
| Single (A) item exceeds MAX_CHUNK_SIZE | `must_break` fires mid-item. Both chunks carry same `(A)` label. |
| Small (A) item (< MIN_CHUNK_SIZE) | Won't trigger `prefer_break` for next `(B)`. Gets folded with (B) content. Label = `(A)` (first marker in chunk). |
| Post-split merge absorbs a chunk | Merged chunk keeps the label of its first constituent. |

### 2b. Context annotation

Annotation is **integrated into splitting** (not a separate pass). The algorithm above tracks `hierarchy_state` and assigns labels during accumulation.

**Context prefix format** (replacing `(continued)`):
```
106 CMR 703 > NONFINANCIAL > 703.192 EAEDC Disability > (D) Cardiovascular System
```

**Rules**:
- First chunk (or no hierarchy marker found): section title only, no suffix
- Subsequent chunks: section title + ` > ` + hierarchy label
- Metadata `section_title` stays as the ORIGINAL title (never modified)
- New metadata field `hierarchy_path` carries the sub-topic label

### 2c. Post-split merge pass

**New flow**:
```
sections → merge_small_sections() → split_with_hierarchy() → merge_small_chunks() → output
```

After splitting, fold any sub-MIN_CHUNK_SIZE fragments into their neighbors. When merging:
- Merged chunk keeps the `hierarchy_label` of its **first** constituent
- `chunk_n` and `chunk_total` are recalculated after merge

### 2d. New metadata fields

| Field | Type | Value | Purpose |
|-------|------|-------|---------|
| `hierarchy_path` | string | e.g., `"(D) Vehicles"` | Sub-topic label for display and citations |
| `chunk_n` | int | 1-indexed position | "Part N of M" display |
| `chunk_total` | int | Total chunks for this section | "Part N of M" display |

These are simple types compatible with ChromaDB metadata (no embedder changes needed).

### 2e. Chunk ID per-section indexing

Change `chunk_index` from global-per-chapter to per-section. `cmr_sec_362_310__000` through `cmr_sec_362_310__010` instead of `__039` through `__049`.

---

## Phase 3: Query Fix — Cross-program Chapters

**File**: `rag/query.py`, `_build_where_filter()` function

### Problem

When `program='SNAP'` is set, chapters tagged `"Cross-Program"` (327 SSP, 343 Fair Hearing Rules) are excluded. These chapters apply to all programs by definition.

### Fix

When building the `where` filter with a specific program, include Cross-Program:
```python
# Instead of: {"program": "SNAP"}
# Use: {"$or": [{"program": "SNAP"}, {"program": "Cross-Program"}]}
```

### Context: How program filtering is used

The `program` metadata is derived from a hardcoded `CHAPTER_PROGRAMS` dict in `rag/cmr/parser.py` that maps chapter numbers to programs. The primary use case is **excluding** TAFDC/EAEDC chapters from SNAP queries, since those are a separate program (Economic Assistance) with different legal requirements and similarly-named pages that muddy results. Cross-Program chapters should never be excluded — they're shared infrastructure.

### Note: applies to CMR source only

OLG also has program metadata and the same filter logic. Check whether OLG has equivalent "cross-program" pages that could be affected. FNS has no program filter.

---

## Phase 4: Special Cases

### 364.990 — SNAP Allotment Proration Table (39 chunks)

This section is a pure numerical table — 401 rows of benefit amounts with no hierarchy markers. All 39 split boundaries cut mid-row. No hierarchy-aware splitting can help here.

Options:
1. **Exclude from section-level chunking** — keep it only in the chapter-level document for broad topic matching
2. **Split by row ranges** with labels like `"364.990 Proration Table (rows 1-50)"`
3. **Leave as-is** — the table rarely causes false positives in the benchmark (only appears as #1 for Q13 "benefit calc" where it's actually relevant)

Decision: TBD during implementation. Option 3 is acceptable if it doesn't hurt the benchmark.

### 366.110 — False positive magnet

"Household Reporting Responsibilities" surfaces as #1 for unrelated queries (asset limits, etc.) because its broad text matches many topics. Not a chunking fix — this is a retrieval-layer issue. Note for future investigation but not blocking this cleanup.

---

## Phase 5: Pre-embedding Checklist

Everything that must be verified before spending money on Voyage AI.

### 5a. Parser output verification

After running the updated parser:
- [ ] 4 broken titles are now correct (703.192, 703.720, 366.115, 367.825)
- [ ] 12 long titles (>80 chars) reviewed — are they genuine long titles or captured body text?
- [ ] No other sections regressed (total section count still 592)
- [ ] Spot-check 5-10 normal sections to confirm no damage

### 5b. Chunker output verification

After running the updated chunker, use `--stats` mode to verify:
- [ ] Zero chunks under MIN_CHUNK_SIZE (orphan fragments eliminated)
- [ ] Zero chunks with "(continued)" in section_title
- [ ] Every multi-chunk section has hierarchy_path on chunks 2+
- [ ] chunk_n and chunk_total are consistent (sum of chunk_n=1 entries equals total section count)
- [ ] Chunk IDs are per-section (e.g., `cmr_sec_362_310__000` through `__NNN`)
- [ ] Total chunk count is reasonable (baseline: 1,275 — expect similar order of magnitude)
- [ ] Spot-check 5 sections: 703.192 (should have ~15 top-level labels A-O), 363.140 (should have A-I labels), a 2-chunk section, a no-split section, one with no Level 1 markers

### 5c. Regression check

- [ ] Sections that don't split (354 of 553) still produce identical single-chunk output
- [ ] Chapter-level documents are unaffected
- [ ] Metadata fields are ChromaDB-compatible (no None values, all strings/ints)

### 5d. Cross-program filter test

- [ ] Query "SNAP fair hearing" with program='SNAP' returns chapter 343 results
- [ ] Query "SNAP eligibility" with program='SNAP' still excludes TAFDC/EAEDC chapters
- [ ] Query with no program filter returns all chapters

---

## Phase 6: Reprocess

1. Re-run parser: `python rag/cmr/parser.py`
2. Re-run chunker: `python rag/cmr/chunker.py`
3. Dry run embedder: `python rag/embedder.py --source cmr --dry-run` (confirm cost)
4. Re-embed: `python rag/embedder.py --source cmr --force`
5. Run retrieval benchmark

---

## Phase 7: Validate

Run the 20-question benchmark from `retrieval_benchmark.md`.

### Metrics to compare

| Metric | Baseline | Target |
|--------|----------|--------|
| Top-1 accuracy | 11/20 (55%) | 17+/20 (85%+) |
| Top-3 accuracy | 16/20 (80%) | 19+/20 (95%+) |
| Complete misses | 3/20 | 0/20 |
| Orphan chunks (<150 chars) | 28 | 0 |
| Chunks with "(continued)" | 722 (56.6%) | 0 |
| Chunks with hierarchy label | 0 | all split chunks |

---

## Phase 8: Consumer Updates (post-embedding, no re-embed needed)

These changes use the new metadata for display and citations. They don't affect embeddings, so they can be done after validation without re-embedding.

### 8a. synthesis.py — citation headers

Update CMR citation format to use `hierarchy_path` and `chunk_n/chunk_total`:
```
[CMR 363.140: Noncountable Assets > (D) Vehicles | Part 4 of 7]
```

### 8b. Web UI — result cards

Update `ui/templates/partials/answer.html` to display:
- `hierarchy_path` as sub-topic indicator
- `chunk_n / chunk_total` as position indicator (e.g., "Part 4 of 7")

### 8c. query.py — CLI output

Update `_format_cmr_result()` to show hierarchy_path and position info.

---

## Implementation Order

Recommended sequence to maximize value per reprocessing cycle:

1. **Phase 1 prep**: Verify broken titles against source PDFs
2. **Phase 1**: Parser title fix
3. **Phase 2a-c**: Hierarchy splitting + annotation + post-split merge (single new function)
4. **Phase 2d-e**: New metadata fields + chunk IDs (integrated with 2a-c)
5. **Phase 3**: Cross-program filter fix (independent, can do anytime)
6. **Phase 5**: Pre-embedding checklist — verify ALL output before spending money
7. **Phase 6**: Reprocess (single re-embedding pass)
8. **Phase 7**: Validate against benchmark
9. **Phase 8**: Consumer updates (no re-embed needed)

One re-embedding pass covers everything. Parser fix and all chunker fixes land together.

---

## Files to Modify

| File | Changes | Phase |
|------|---------|-------|
| `rag/cmr/parser.py` | Multi-line title detection in `extract_sections()` | 1 |
| `rag/cmr/chunker.py` | Replace `split_large_section()` with hierarchy-aware version, post-split merge, new metadata, chunk IDs | 2 |
| `rag/query.py` | Cross-program inclusion in `_build_where_filter()` | 3 |
| `tools/synthesis.py` | CMR citation format using hierarchy_path | 8 |
| `ui/templates/partials/answer.html` | Display hierarchy_path and part N of M | 8 |

## Reference Files

| File | Purpose |
|------|---------|
| `docs/cmr_cleanup/findings.md` | Audit findings with evidence |
| `docs/cmr_cleanup/retrieval_benchmark.md` | 20-question benchmark with baseline scores |

## Architecture Notes

### Three chunkers are independent

`rag/olg/chunker.py`, `rag/fns/chunker.py`, and `rag/cmr/chunker.py` are copy-pasted with identical core logic. No shared base class. Changes to CMR's chunker are fully isolated — zero risk to OLG or FNS.

Shared helper functions (`_combine_text`, `_group_segments`, `render_table`) are duplicated across all three. Future cleanup could extract these to a shared module, but not required for this project.

### Hierarchy profiles are source-specific

CMR's `(A)→(1)→(a)→1.` pattern won't apply to other sources:
- **CFR**: Title→Part→Subpart→Section→paragraph markers (TBD)
- **OLG**: HTML H2/H3 already parsed into separate sections (splitting rarely needed)
- **FNS**: Numbered sections (100, 110, 200) with flat internal structure

The hierarchy profile approach (pattern list passed to the splitting function) means each source defines its own markers without duplicating the splitting logic.
