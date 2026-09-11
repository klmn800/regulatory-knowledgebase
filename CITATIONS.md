# Claude Citations — Working Reference

**Owner:** Solutions Laboratory
**Last verified:** 2026-08-03 (Opus 5, `anthropic` SDK 0.120.2, hands-on spike + official docs)
**Applies to:** any tool that summarizes, reviews, or answers questions over supplied documents.

A durable reference so a future session does not have to re-derive this. Everything below is
either quoted from official docs or observed directly in
`finance-doc-summarizer/spikes/spike_citations_vs_structure.py`.

---

## 1. What it is

`citations: {enabled: true}` set on a `document` content block in the **Messages API**. Not a
Claude Code feature, not a prompting technique. All active models support it.

## 2. Why it is not "just prompting the model to cite"

This is the whole point, and it is the part people get wrong.

**Prompted citation:** the model *writes* the quote. Those are sampled tokens like any others.
It can misquote by a word, paraphrase and present it as verbatim, or emit a plausible-looking
page number that is wrong. Nothing checks it against the source.

**Native citation:** the API chunks the document server-side and indexes the chunks. The model
emits a compact *reference to a location*. The API then substitutes `cited_text` **from the source
document**. The quote is retrieved, not written.

Two independent confirmations that this is real and not marketing:

- **Economic.** `cited_text` does not count toward output tokens, and does not count toward input
  tokens when passed back in later turns. You are not billed for the quote because the model never
  generated it.
- **Observed.** In our spike, the anchor returned for a revenue sentence began at char 0 and
  included the company letterhead. No model asked to quote a revenue figure would choose to
  include "ACME INDUSTRIES, INC. / Management's Discussion and Analysis (excerpt)" in its
  quotation. That is a machine-selected span, not a curated one.

Simon Willison's term for this is the useful one: **deterministic quoting** — text "guaranteed to
be copied across and not lossily transformed."

## 3. What it guarantees, and what it does not

> **Citations guarantee that the cited passage exists in the source at that location.
> They do not guarantee that the passage supports the claim attached to it.**

Two distinct failure modes, and only the first is closed:

| Failure mode | Closed by native citations? |
|---|---|
| Fabricated / misquoted source text | **Yes**, by construction |
| Real quote, wrong interpretation | **No** |
| Fabricated *external* reference (paper, URL, case law) | Not applicable — different problem |

Most public "don't trust AI citations" commentary is about the third row. Do not let a stakeholder
conflate them; the honest, bounded claim is stronger than an oversold one:

> *It cannot misquote. It can still misread.*

That sentence is the one to put in front of a skeptical reviewer. People trust systems whose
limits they can state.

---

## 4. Our design stance: citations are **navigation**, not proof

The industry frames citations as *verification* — evidence the model did not lie. We frame them
as **pre-screening and wayfinding**: the model has read 200 pages and is telling a human *where to
look*. The human opens the anchor, reads the paragraph around it, reads up a bit, and builds their
own understanding. That is the work product — not the summary.

> *"People want to do the right thing, you just need to make it easy for them."*

The design rule that falls out: **the cost of checking a claim must be lower than the cost of not
checking it.** One click, not "open the PDF, Ctrl-F, hope." Time-to-verify is a real metric and
worth measuring.

Four consequences that change engineering decisions:

1. **It changes what "good" means.** Verification framing optimizes *precision* — every citation
   must be exactly right. Navigation framing weights *recall* — did we point at everything worth
   looking at? An anchor that is slightly wide but lands the reader in the right paragraph is a
   **success** under navigation and a **failure** under verification. Build evals accordingly.
2. **It de-risks the product against the strongest published critique.** Published factual-accuracy
   rates for cited AI output are poor (see §8). But a *navigation aid* does not need to be right to
   be useful — it needs to be approximately right and cheap to dismiss. A wrong pointer costs the
   reader five seconds. A wrong claim asserted as fact costs credibility. Framing citations as
   pointers moves the product out of the blast radius.
3. **Precision still matters absolutely for figures.** A number is *checked*, not read around. So
   grounding is two-tier by design, not by compromise:
   - **Figures →** exact verbatim string match, offsets computed in code. Anchor must be tight.
   - **Narrative claims →** generous anchors are fine, even preferable. Context is the feature.
4. **Export is now the primary risk, not a footnote.** Verification is a one-time act; navigation
   is continuous. If the artifact lands in Word as flat text, the entire value proposition
   evaporates at the final step. Anchors must survive export — as hyperlinks back into a source
   viewer, or as Word comments carrying the locator. Design the export around this from day one.

**Push back on "excessively cited."** Cite densely, yes — but if *everything* is cited, nothing is
prioritized, and citation density degrades into highlighting the whole document. The value is
selective pre-screening. The answer is not fewer citations; it is **more structure on them** —
type and rank each anchor (figure / obligation / risk / hedge / change-vs-prior) so the reader
chooses their own depth. Density plus structure is navigable. Density alone is a highlighter that
has run out of ideas.

---

## 5. Configuration reference

| Document type | Chunking | Citation locator |
|---|---|---|
| Plain text | Sentences (minimum granularity) | Character indices, 0-indexed, exclusive end |
| PDF | Sentences, from extracted text | Page numbers, 1-indexed, exclusive end |
| **Custom content** | **None — your blocks used as-is** | **Block indices, 0-indexed** |

- Sentence is the **minimum** granularity. Claude may chain consecutive sentences to cite a
  paragraph or longer. Wide anchors are a model choice, not an API limit.
- **Custom content documents are the control surface.** Pre-segment the document yourself, supply
  one block per unit you want citable, and a citation resolves to exactly that unit. For any tool
  where anchor precision matters, this should be the default ingestion shape — not an optimization.
- Citations must be enabled on **all or none** of the documents in a request.
- `title` and `context` are passed to the model but are **not citable**. `title` is length-limited;
  use `context` for metadata (text or stringified JSON).
- Text only. **Image citations are not supported.**

## 6. Gotchas — all verified, all silent failures

1. **Forcing a tool call yields zero citations.** Citations attach to *text* blocks. With
   `tool_choice: {type: "tool", ...}` the response contains only a `tool_use` block and there is
   nothing for anchors to land on — **200 OK, zero citations**. Use `tool_choice: auto` and prompt
   for narrative first, then the structured call. Both arrive in one turn.
   → **Assert on this:** citations enabled + zero citations returned = bug, not an empty result.
2. **`output_config.format` is a hard 400.** *"Citations cannot be enabled when output format is
   set."* Structured outputs require strict JSON; citations require interleaved text blocks.
   **Tool calling is unaffected** — strict and non-strict tools both coexist with citations fine.
   That is the supported route to structure + provenance in one call.
3. **Scanned PDFs are not citable at all.** No extractable text, no citations, no image citations.
   For document-heavy domains this makes OCR a *provenance* requirement, not a quality nicety.
4. **Response shape changes.** One text block becomes many, some carrying a `citations` array. Any
   consumer parsing `content[0].text` breaks. This is the single most reported integration pain.
5. **Rendering anchors is fiddlier than it looks.** Apply highlight markup **back-to-front** so
   earlier insertions don't shift later offsets, and keep markup off markdown syntax characters.

## 7. Cost model

- Enabling citations adds input tokens from **system prompt additions + document chunking**.
- Measured: **1,862 vs 1,060 input tokens (~+75%)** on a ~1k-token document. Most of that is
  *fixed* overhead, so the ratio collapses on large documents. **Do not quote ~75% as the number.**
- `cited_text` is free on output, and free on input when passed back.
- Net vs. prompted quoting: usually **cheaper**, because prompted quoting bills every quoted
  character as output.
- **Caching:** source documents can be cached (`cache_control` on the top-level document block);
  response citation blocks cannot. Because `citations.enabled` lives *inside* the document block,
  toggling it changes the cached prefix — a citations run and a non-citations run **cannot share a
  cache entry**. Pick one mode per cached document.
- Compatible with prompt caching, token counting, and the Batches API.

## 8. Evidence base

**Vendor (Anthropic):** up to **+15% recall accuracy** vs. custom prompt-based implementations.
Endex reported source hallucination and formatting errors **10% → 0%** and **+20% references per
response**. The Endex figure is the more meaningful one — a whole class of error eliminated rather
than a metric nudged, which is what "copied, not typed" predicts.

**Independent practitioners:** neither Simon Willison nor Daniel Corin reports a citation *quality*
problem. Both report *integration* problems — response shape and highlight rendering respectively.
That is a meaningful pattern: the hard part is plumbing, not accuracy.

**Literature (important context, different target):** *Cited but Not Verified* (PwC, arXiv
2605.06635, May 2026) benchmarks 14 models on deep-research citation quality: **link validity
>94%, topical relevance >80%, factual accuracy only 39–77%.** Fact-check accuracy **drops ~42% as
tool calls scale from 2 to 150** — more retrieval produced *less* accurate citation. Related work
documents citation hallucination rates of **11–57%** across deployed models.

⚠️ **These numbers measure deep-research agents citing the live web — not the Citations API over a
supplied document.** The paper explicitly sets Anthropic's Citations API aside as addressing
citation *generation* rather than *evaluation*. Cite these to explain the problem the feature
sidesteps; never present them as measurements of it.

## 9. Build checklist

- [ ] Custom content documents, pre-segmented — one block per citable unit
- [ ] `tool_choice: auto`, narrative before the structured call
- [ ] Assertion: citations enabled + zero citations = raise, don't return
- [ ] Figures verified by verbatim string match in code; never trust the model to re-type a number
- [ ] OCR upstream, or accept zero provenance on scanned input
- [ ] Anchors typed and ranked, not just counted
- [ ] Export carries locators (hyperlink or comment) — verified end-to-end
- [ ] Consumer handles multi-block responses

## Sources

- [Citations — Claude docs](https://platform.claude.com/docs/en/build-with-claude/citations)
- [Introducing Citations on the Anthropic API](https://claude.com/blog/introducing-citations-api)
- [Simon Willison — Anthropic's new Citations API](https://simonwillison.net/2025/Jan/24/anthropics-new-citations-api/)
- [Daniel Corin — Document Citations](https://www.danielcorin.com/posts/2025/document-citations/)
- [Cited but Not Verified (arXiv 2605.06635)](https://arxiv.org/pdf/2605.06635)
- [GhostCite (arXiv 2602.06718)](https://arxiv.org/pdf/2602.06718)
- [Citations API on Amazon Bedrock](https://aws.amazon.com/about-aws/whats-new/2025/06/citations-api-pdf-claude-models-amazon-bedrock/)
