# CMR Integration Brainstorm

**Date**: 2026-03-17
**Context**: Discussion about expanding the policy knowledgebase beyond OLG and FNS to include the actual Massachusetts regulations.

---

## The Idea

Integrate **106 CMR (Code of Massachusetts Regulations)** into the policy knowledgebase as a third source alongside the OLG and FNS Handbook 310. These are the actual state regulations that govern DTA's programs — the legal authority that the Online Guide implements.

## Source Material

- **What**: Code of Massachusetts Regulations, Title 106 (Department of Transitional Assistance)
- **Format**: 18 PDFs, averaging ~20 pages each (~360 pages total)
- **Content**: Formal regulatory language with deep nested structure
- **Example citation format**: `106 CMR 362.330(A)(1)(a)`

## Sample Content

The language reads like formal legal regulation with deeply nested hierarchical structure:

```
362.330: Good Cause Criteria for the General SNAP Work Requirements
  (A) Good Cause Reasons.
    (1) Suitable state-standard child care is totally unavailable...
    (2) The individual suffers a family crisis or emergency...
      (a) demands the individual's immediate attention;
      (b) can only be attended to by the individual; and
      (c) can only be attended to during hours of employment...
    (3) The employment or offer of paid employment is at a wage level below...
      (a) the applicable federal minimum wage;
      (b) the applicable state minimum wage; or
      (c) 80% of the federal minimum wage...
    ...
  (B) Verifications.
    (1) The unavailability of childcare shall be verified by...
```

## Pipeline Assessment

### What's similar to FNS/OLG
- Same pipeline shape: PDF parsing --> structured JSON --> chunking --> embedding --> ChromaDB (in `index/chroma_db/`)
- Same embedding model (Voyage voyage-3) works well -- legal text is information-dense but still natural language
- Same query interface pattern
- Would get its own collections in the shared ChromaDB (e.g., `cmr_chapters`, `cmr_sections`)
- Cross-references are frequent and use formal citation format (`106 CMR 362.310`) -- actually easier to parse with regex than FNS references

### What's different from FNS
- **18 separate PDFs** instead of one large document -- minor, just loop over files
- **Deep nested hierarchy within sections**: The `(A)(1)(a)(b)(c)` structure is the legal logic itself. FNS sections are flatter and more self-contained.
- **Context dependency is heavier**: Sub-items like `(3)(a)` are meaningless without the parent section's framing. Chunking must preserve the full nested structure within each CMR section.
- **Section numbering scheme**: CMR uses `XXX.XXX` format (e.g., `362.330`) rather than FNS's `XXXX.X` format

### Chunking strategy (key difference)
- **Chunk at the CMR section number level** (e.g., `362.330` as one chunk), NOT at sub-items
- **Preserve full nested structure within each chunk** -- don't break `(A)(1)(a)(b)(c)` apart
- **Longer chunks are OK**: A section like `362.330` is maybe 2,000-3,000 chars, within healthy embedding range
- **Context prefix**: `"106 CMR 362 > 362.330: Good Cause Criteria for General SNAP Work Requirements"`
- This differs from OLG (splits at H2/H3) and FNS (shorter, more self-contained sections)

### Models
- **Embeddings**: Voyage voyage-3 remains the right choice. Legal-specific embedding models exist but a strong general-purpose model is better here because queries won't be in legalese.
- **LLM (Claude)**: Structured legal language is Claude's sweet spot. No change needed.

## The Bigger Vision

This isn't just "add a third data source." With three indexed sources, the project becomes a **comprehensive policy evaluator**:

### Three-source priority model
1. **OLG** (first) -- what workers actually follow day-to-day
2. **CMR** (second) -- the state regulations the OLG is supposed to implement
3. **FNS Handbook** (third) -- the federal rules the CMR is supposed to implement

When sources disagree, the disagreement IS the finding.

### Use cases
- **Answer policy questions** (simple and complex) by pulling from all three sources as needed
- **Evaluate the OLG itself** -- systematically check whether OLG correctly implements CMR requirements
- **Find gaps**: CMR requirements with no OLG coverage
- **Find conflicts**: OLG guidance that contradicts CMR or FNS
- **Trace authority**: For any OLG policy, show the CMR regulation and FNS rule behind it

### What's genuinely new work (beyond repeating the pipeline pattern)
- **Orchestration layer**: Decides which sources to query and in what order based on the question
- **Synthesis agent**: Reasons across results from multiple collections, identifies agreement/gaps/conflicts
- **User interface**: Beyond CLI -- likely web-based, since the audience is policy staff

### Development path
1. Finish FNS Phase 2 + 3 (chunking, embedding, query, comparator)
2. Build CMR pipeline (parser, chunker, embedder)
3. Build orchestration/synthesis agent
4. Build better UI

Each step delivers standalone value.

## Project Restructuring

Decision made to consolidate into a single project directory (moving out of `solutions_laboratory/` root) so everything lives in one workspace with one CLAUDE.md. The project is now organized under `policy_navigator/` with `rag/` (source pipelines + shared query/embedder), `tools/` (shared utilities), `programs/` (comparator, author, qc), `index/` (data), `output/` (results), and `raw/` (source files).
