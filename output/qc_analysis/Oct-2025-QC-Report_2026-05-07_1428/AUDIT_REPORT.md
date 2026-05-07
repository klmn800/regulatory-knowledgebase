# QC Investigate Audit — Oct-2025-QC-Report_2026-05-07_1428

**Auditor**: Claude Opus 4.7 (1M context)
**Audit date**: 2026-05-07
**Target**: `output/qc_analysis/Oct-2025-QC-Report_2026-05-07_1428/`
**Scope**: 13 rows → 27 findings (26 real + 1 placeholder), all in investigate phase. Cross-checks not in scope.

---

## Top-line verdict

**TRUST LEVEL: HIGH**, with calibrated caveats.

Citations are 100% grounded (115/116 directly in the post-seed trace; 1 verified in the seed via replay). Verdicts are evidence-based: I read the actual chunk text behind every Partial gap claim I checked, and most are structurally accurate (the OLG really does have asymmetric coverage in those areas). Query craft is good — judges sharpen extractor queries with scenario-specific terminology and use full DTA jargon (BEACON, IR, SVES, GWR, ABAWD, EDSAP, SUA, HCSUA, RSDI, SLAM, AORD).

The strongest evidence FOR trust:
- Every Partial verdict I spot-checked (5.1 dependent care vs medical, 5.3 disability maintenance, 4.1/9.1/9.2 income increase effective date, 6.1 partial-paystub) had a **structurally real gap** in OLG when I read the actual chunks.
- Citations for the one apparent corpus-only case (row 3.1 "Contribution Income") were proven IN_SEED via replay.
- The judge differentiates "minor suggestion" gap notes (kept under Adequate) from material gaps (Partial). It does not over-call.

The strongest evidence AGAINST full trust:
- One verdict (row 1.2) asserts an "intersection gap" between the External Databases page and SLAM/IR processing that the very Procedures-for-No-Earnings-on-File page (cited in 1.1's Adequate verdict) already fills explicitly. This is a soft case of gap-invention.
- Three rows (1, 2, 13) have findings with overlapping content — the multi-finding extractor split the same QC issue into different framings, and verdicts diverge across the redundant findings, weakening the row-level signal.
- One row's investigate phase ran 6 searches and produced citations even though extraction returned no findings (row 12, the "Correct" placeholder). Wasted budget; no harm to verdict quality.

Net: a non-technical reader can rely on the verdicts and citations, treating Partial findings as "the OLG could be clearer here, with one of the two sub-findings often being the load-bearing one."

---

## Methodology

I avoided the access trap the prompt warned about: chunk URLs and titles live in `metadata.url` / `metadata.page_title`, **not** at top-level `c.url` / `c.page_title`. I verified my access pattern by printing a known-present chunk before quantifying anything.

Steps taken:
1. Walked all 13 row JSONs, extracted per-finding: extractor queries, judge follow-up queries, verdict, reasoning, gap_description, all `olg_references`, every search result in trace.
2. For each citation, classified as IN_TRACE (matched URL or page_title that appeared in any tool_result) vs IN_CORPUS (URL exists in `index/olg/section_chunks.json` but not in trace).
3. For the only IN_CORPUS-only citation, replayed the seed search via `rag.query.search_with_client(...)` and confirmed the page was retrieved by the seed (which trace storage doesn't preserve).
4. For every Partial verdict I spot-checked, read the actual chunk text from `section_chunks.json` to verify the claimed gap. Did this for: row 1.2 (External Databases + SLAM), 5.1 (Medical Recert + Processing of Unverified Expense Deductions), 5.3 (Information Not Subject to Reverification + SNAP Disability), 4.1/9.1/9.2 (Department Responsibility to Take Timely Action + Change Reporting Overview), 6.1 (Anticipated Income + Income from Steady Employment + Income from Hourly).

Field paths used: `metadata.url`, `metadata.page_title`, `metadata.section_heading`. Tool results within trace: `judge_trace[*].tool_results[*].results[*].url` and `.page_title`.

---

## Statistics

- **Total rows**: 13
- **Total findings**: 27 (extractor multi-finding default produced 1–4 findings per row)
- **Real findings**: 26
- **Placeholder findings**: 1 (row 12 — `policy_issues = "Extraction returned no findings."` because the QC determination was "Correct")

**Coverage distribution**:
- Adequate: 16 (15 real + 1 placeholder)
- Partial: 11
- Gap: 0

**Confidence distribution**:
- HIGH: 26
- MEDIUM: 1 (row 6.1 — appropriately downgraded, see audit notes)
- LOW: 0

**Search budget usage** (of 10 max follow-up turns):
- 4 searches: 1 finding (row 7.1)
- 6 searches: 2 findings (rows 12.1 placeholder, 13.3)
- 7 searches: 4
- 8 searches: 6
- 9 searches: 10 (most common)
- 10 searches: 4 (rows 3.2, 4.1, 9.2, 10.3 — judge fully exhausted)

**Citations**:
- Total: 116 across 27 findings (avg 4.3 per finding)
- IN_TRACE (URL or page_title appears in a stored tool_result): 115
- IN_CORPUS only (URL in corpus but not in stored trace): 1 (row 3.1, "Contribution Income")
- IN_SEED (verified by re-running extractor seed queries): 1 of 1 — 100% recovery
- Unverifiable (not in trace AND not in corpus): **0**

**Net citation grounding: 116/116 = 100%.**

**Run cost**: $9.51 judge + $0.07 extractor = **$9.58 total**. Investigate took 50.6 minutes of wall-clock time. Avg ~$0.36 per finding.

---

## Findings table

Severity rubric:
- **HIGH** — wrong verdict, hallucinated citation, or methodology bug
- **MEDIUM** — inefficient queries, weak reasoning, missed evidence, redundant extraction
- **LOW** — minor wording, cosmetic, edge-case

| ID | Row.Finding | Severity | Axis | Issue | Evidence | Suggested fix point |
|----|-------------|----------|------|-------|----------|---------------------|
| F1 | 1.2 | MEDIUM | E | "Intersection gap" between External Databases (skip if no changes) and SLAM/IR (cold call for new SLAM) is over-stated. The "Procedures for Addressing Cases with No Earnings on File" page (which 1.1 cited as proof of Adequate) already explicitly tells workers to check Work Number when client has no earnings on file at IR. | Read full chunk text — the procedure is unconditional ("If the client checks No: 1. If no Work Number match → no further action. 2. If Work Number match → cold call twice…"). Doesn't depend on whether other pages say "skip data sources for no changes." | Judge prompt: discourage constructing intersection gaps when an explicit scenario-specific procedure already exists |
| F2 | 1.1 + 1.2 | MEDIUM | A | Two findings cover the same QC issue (unreported income at IR with $1,750 rent) split into "client failed to report" vs. "case manager failed to identify." Verdicts diverge (Adequate vs Partial) → row-level picture is confusing. | Same narrative, both findings cite Procedures for No Earnings on File and External Databases pages. Judge reasoning for both heavily overlaps. | Extractor prompt: when the same case has only one recipient-vs-agency error, don't split into recipient/agency halves |
| F3 | 2.1 + 2.2 | MEDIUM | A | Extractor split a single mass-waiver-expiration agency error into "ABAWD Waiver Area Exemption" + "Work Requirement Exemption Management." Both Partial. Both gap claims revolve around the same June 30, 2025 statewide waiver end. | Both reasoning paragraphs name the same gap (no procedural guidance for mass exemption expiration / batch transition). Citations heavily overlap (Waived Areas, ABAWD Work Rules Exemptions appear in both). | Extractor prompt — same as F2 |
| F4 | 13.3 | LOW | A | Extractor labeled finding 3 "Household Composition and Living Arrangement Documentation" but the QC narrative doesn't actually flag a household composition issue — the brother sharing housing is noted in TAO response, not the QC finding. Judge ignored the extractor frame and verified work-rules + homeless coding instead, marking it Adequate. Outcome OK; finding is just a near-duplicate of 13.1 / 13.2. | `policy_issues` says "Household Composition" but reasoning is entirely about WPR coding and homeless indicator — same ground covered by 13.1 + 13.2. | Extractor prompt: discourage speculative "and also this might be relevant" findings |
| F5 | 12.1 | LOW | budget | Investigate ran 6 searches and synthesized a verdict for a placeholder finding (`Extraction returned no findings.`) on a "Correct" determination. Wasted ~$0.40 of judge time per such case. | Trace has 3 follow-up queries on lottery winnings + RSDI countability. Verdict adds nothing — case was already determined Correct by reviewer. | Investigate orchestrator: skip judge invocation when `policy_issues` is the "no findings" sentinel string |
| F6 | 4.1 / 9.1 / 9.2 | LOW | C | Three findings independently identify the **same** "OLG lacks income-INCREASE effective-date guidance" gap. Likely a real systemic finding rather than three separate gaps. | Verified: "Department Responsibility to Take Timely Action" page is structurally only about decreases-to-zero. Change Reporting > Income-Related Changes only states the $125 / 10-day rule. | Output post-processing: detect when Partial gap_descriptions across rows reference identical OLG pages and surface as a "recurring gap" (operationally helpful for policy team triage). Not a judge defect. |
| F7 | 3.1 | LOW | F | One citation "Contribution Income (…/Inc_Contribution.htm)" was not in the post-seed trace. Initial classification: IN_CORPUS only. After replay, verified the page WAS retrieved by all three seed queries (top-3 every time). | `python -c "from rag.query import …"` replay shows Contribution Income > Verifying / Example 1 / Example 2 / Example 3 / BEACON entry all in seed top-5 for at least one of the seed queries. | None — methodology issue with my walker, not a judge defect. **The judge's citation is grounded.** |
| F8 | 9.1 / 9.2 | LOW | A | Same row, same QC issue (recipient failed to report 8/4/2025 new job), split into "change-reporting obligation" vs. "budget-month inclusion." Both Partial with the same gap-claim. | Both gap descriptions reference the income-increase effective-date gap. Both cite same Change Reporting + Timely Action + Anticipated Income pages. | Extractor — same as F2/F3 |
| F9 | 6.1 | LOW | E | MEDIUM-confidence Partial. Judge says no explicit "partial first paystub + employer letter → use letter" guidance. True. But Anticipated Income's "If any amount of income or anticipated date of receipt is uncertain, it must not be counted" + Hourly Employment's "consult with the household to determine the normal amount of income to be expected" together support the right answer. | Read both chunks. Judge's MEDIUM-confidence call appropriately reflects this — gap is real-but-soft. | None — appropriate calibration of confidence. |
| F10 | 4.1 | LOW | A | Extractor query 1 ("change reporting earned income $125 threshold timing") returned a top-1 score of 0.44 — modest. Most other extractor queries top out 0.5–0.6. | search1 top: Enter or Update EBC Results Information (0.44). Doesn't break the run because judge follow-ups land cleaner hits. | Extractor prompt: discourage stuffing multiple concepts into one query (`$125`, `threshold`, `timing` are all in one query). |
| F11 | All Partials | LOW | E | Pattern: judge's threshold for Partial is **"would a worker need to synthesize across multiple OLG pages to find the answer."** This is stricter than "the OLG doesn't cover this." The threshold is consistent and documented in reasoning, but a non-technical reader could read Partial as "policy is missing" when the policy is just non-co-located. | All 11 Partial verdicts I read explain the gap as procedural-integration deficits, not policy absence. | Judge prompt or report rendering: include a 1-line "verdict legend" so consumers know Partial ≠ "OLG silent." Or formalize a sub-classification: "Partial-Synthesis" vs "Partial-Missing." |

No HIGH-severity findings. No hallucinated citations. No wrong-direction verdicts.

---

## Per-axis assessment

### A. Extraction quality

**Working well**: Multi-finding split is genuinely valuable on rows like 5 (4 distinct policy issues from one narrative — dependent care, SSI, disability, newborn) and 7 (3 distinct issues — SMD eligibility, rent, RSDI). The extractor used DTA terminology correctly across queries (BEACON, IR, SVES, GWR, ABAWD, SVES, EDSAP, SUA, RSDI, SLAM, AORD) — no glaring acronym confusions.

**Not working well**: ~5 of the 26 real findings are redundant splits (1.1+1.2, 2.1+2.2, 9.1+9.2, 13.1+13.3 partial overlap). The pattern: the extractor splits the same agency vs. recipient cause, or the same procedural error from "what client did wrong" + "what worker should have caught," producing two findings whose judge verdicts then diverge slightly. This makes row-level interpretation harder.

**Biggest improvement**: tighten the extractor prompt to say "if the same underlying error has both client-facing and worker-facing aspects, return ONE finding." Splits should be reserved for genuinely distinct topics (SSI vs. shelter vs. newborn etc., as in row 5).

### B. Seed search results quality

**Working well**: Top-3 seed scores are typically 0.45–0.60, occasionally 0.60+. The right pages surface for almost every finding I checked. Replay of row 3.1 seed showed Contribution Income page top-5 in all 3 queries.

**Soft notes**: A few extractor queries dilute relevance by stuffing concepts (`change reporting earned income $125 threshold timing` mixes 4 concepts and lands at 0.44 top score). Splitting into more focused queries would improve seed Top-1.

**Best fix point**: extractor prompt — encourage shorter, single-concept queries.

### C. Judge query craft

**Working well**: Real sharpening from generic extractor framing to scenario-specific terms — e.g., row 1.1 went from "interim report income reporting obligations SNAP" to "Simplified Reporting Interim Report Work Number match active wages client said no earned income cold call VC-1." Row 10 added "AC fee public housing", row 11 added "mortgage statement escrow PITI components." Judges incorporate trace findings into next-turn query terms.

**Not working well**: Some rows (9.2 with all 10 searches, 4.1 with all 10) include 3+ near-rephrasings of the same query. Diminishing returns kicked in around turn 5-6 in those rows.

**Biggest improvement**: judge prompt — add a "novel angle check" before each follow-up query: "Does this query introduce a new term/concept the prior queries didn't probe?" This would conserve budget and force broader probing.

### D. RAG behavior

**Working well**: Scores cluster in the 0.4–0.6 range for solid hits, 0.5–0.65 for the best-matched scenarios. ChromaDB metadata filtering (program filter + program-include list) appears to be working. No obvious "ground-truth on this page but didn't surface" cases observed in spot-checks.

**Limitation surfaced**: Section chunks come back standalone (no neighbor pulling). For row 1.1's "Procedures for Addressing Cases with No Earnings on File," the procedure spans 3 separately-returned chunks — the judge had to read each separately to assemble the full procedure (1-3, 4-6, then employer-mismatch handling). Workable, but a chunk-neighbor expand would meaningfully reduce judge cognitive load.

**Best fix point**: RAG retrieval — optional `expand=N` flag on the search tool to pull adjacent chunks from the same section_heading. Gated behind a flag so most queries stay cheap.

### E. Reasoning & conclusion soundness

**Working well**: Reasoning paragraphs almost always reference actual chunk content — e.g., row 5.1 quoted the exact medical-expense recertification rule ("If the client does not provide new proof or new self-declaration of recurring medical expenses on record, you must remove them"); row 8.1 referenced the explicit Group Homes Note box; row 13.2 referenced the BEACON popup at recertification. Judges don't paraphrase the QC issue back at the reader.

**Not working well**: Row 1.2's "intersection gap" is the one reasoning miss I caught — the judge constructs a logical bridge between two pages and calls the absence of the bridge a gap, when an explicit procedure already covered the scenario. The judge had even cited that procedure (in 1.1) one finding earlier.

**Best fix point**: judge prompt — add a "look-aside check": "Before declaring a procedural gap, search the OLG for a scenario-named procedure (e.g., 'Procedures for X')." Catches over-abstract gap construction.

### F. Citation grounding

**Working well**: 100% of cited URLs are real, retrievable chunks. 115/116 came directly from stored trace results. The 1 apparent outlier (row 3.1's Contribution Income) was retrieved by the seed search but the seed isn't preserved in trace — verified via replay. **No hallucinated citations.**

**Methodology gap**: trace storage drops the seed. Auditors who use only trace will mis-classify ~1 in 100 citations as "missing from retrieval." The fix is either (a) include seed results in trace storage, or (b) document this in the audit playbook.

**Best fix point**: judge orchestrator — capture seed results into `judge_trace[0]` as a synthetic "turn 0" entry. Trivial change with material audit-clarity benefit.

---

## Recommended actions (ordered by leverage)

### 1. Tighten multi-finding extractor split rules
- **What**: Update extractor prompt to discourage splitting a single QC error into "client side" + "agency side" findings. Reserve splits for genuinely distinct topics.
- **Where**: `programs/qc/prompts/` (extractor prompt)
- **Impact**: Eliminates ~5/26 (~19%) of the redundant findings I observed. Cleaner row-level signal in QC reports. Modest token savings (5 fewer judge runs ≈ $1.75 / report on a 13-row run).
- **Risk**: Slight under-splitting where a row legitimately has both extraction angles. Mitigate by including 2-3 examples of valid vs invalid splits in the prompt.

### 2. Skip judge for "Extraction returned no findings" placeholder rows
- **What**: When `policy_issues == "Extraction returned no findings."`, skip investigate phase entirely. Write phase=investigated with an empty/no-op finding.
- **Where**: `programs/qc/qc_analyzer.py` (investigate orchestrator)
- **Impact**: Saves ~$0.40 + ~3 minutes per "Correct" determination. On a 13-row report with 1 such row, this is small (~4% cost savings); on a 50-row "lots of correct cases" report it'd compound.
- **Risk**: None. The placeholder by definition has no policy issue to investigate.

### 3. Capture seed search results in trace storage
- **What**: Add a synthetic `turn_0` entry to `judge_trace` containing seed queries + dedup'd top-N seed results.
- **Where**: `programs/qc/qc_analyzer.py` (judge agentic loop)
- **Impact**: Citations become 100% audit-verifiable from trace alone. Removes false-positive "this citation isn't grounded" reports from auditors.
- **Risk**: ~5–10 KB more JSON per finding. Negligible.

### 4. Add a "look-aside" check to judge prompt before declaring procedural gaps
- **What**: Add: "Before concluding a procedural gap exists between OLG pages X and Y, search for a named procedure that covers the specific scenario (e.g., 'Procedures for…' / 'Steps for…' pages). If one is found, evaluate it as a unified procedure rather than an integration gap."
- **Where**: `programs/qc/prompts/qc_judge.md` (or wherever the judge is prompted)
- **Impact**: Would have caught row 1.2's over-stated intersection gap. ~1/11 (~9%) of Partial verdicts in this run had this pattern.
- **Risk**: Slight bias toward Adequate when explicit procedures are imperfect. Mitigate by phrasing as "evaluate," not "default to Adequate."

### 5. Cap follow-up queries at 5–7 with "novel-angle" enforcement
- **What**: Reduce default `judge_search_budget` from 10 → 7. Add to judge prompt: "Each new query must probe a substantively different angle from prior queries — avoid rephrasing." Trace shows queries 6–10 are typically rephrasings.
- **Where**: `[qc_analyzer]` config (`judge_search_budget`) + judge prompt
- **Impact**: ~20% wall-clock + token savings on the high-budget findings. Verdict quality probably unchanged (rows 9.2 and 4.1 with all 10 used didn't find new angles after turn 5).
- **Risk**: Some genuinely thorough investigations may be cut short. Worth A/B testing on a representative sample.

### 6. Surface a "verdict legend" in the QC UI
- **What**: Render a 1-line "Partial = OLG covers the policy but workers must synthesize across pages; not an absence of policy. Gap = OLG silent on this topic" near the verdicts.
- **Where**: QC UI (`ui/templates/qc_*.html`) and CSV export
- **Impact**: Reduces misreading of Partial as "policy gap" when it's "policy non-co-location." Better consumption by non-technical readers.
- **Risk**: None.

### 7. Detect cross-row recurring gaps as a post-process
- **What**: After all rows finish, scan Partial gap_descriptions for shared OLG pages or shared phrasings. Surface a "recurring gap signal" panel in the report.
- **Where**: QC UI (or post-processor in `qc_analyzer.py`)
- **Impact**: This run had rows 4.1 + 9.1 + 9.2 + 11.1 + 11.2 all flagging variants of related shelter/income procedural gaps. A single "this OLG area has 3+ findings" panel would let the policy team triage faster than reading 11 individual Partials.
- **Risk**: Low. Could be heuristic on URL overlap + cosine sim of gap_descriptions.

### Not recommended (considered, but not worth it)

- **Switching judge model from Sonnet 4.5 to a smaller model**: Current judge cost is ~$0.36/finding. The reasoning quality is genuinely dependent on the model. A cost-down attempt would likely surface as more weak-gap reasoning like 1.2. Hold.
- **Adding chunk-neighbor expansion to the search tool**: Useful but costly to retrofit. Currently the judge handles split-procedure chunks fine (rows 1.1 and 8.1 both reasoned correctly across multi-chunk procedures). Defer.
- **Enforcing explicit URL grounding in reasoning text**: Tempting (let auditors grep reasoning for citation URLs). But would push the judge into stilted output and risk regressing reasoning quality. Trace-based grounding suffices.

---

## Bottom line for a non-technical reader

The QC analyzer's investigate phase is producing **trustworthy, well-grounded verdicts** on this October 2025 report. Every citation traces back to a real OLG page. Most Partial findings reflect genuine asymmetries or non-co-located policy in the OLG (which the policy team can act on). The few weak spots are extractor-side redundancy and one over-confident "intersection gap" — neither of which causes wrong final determinations.

You can act on these findings. For the strongest signal, focus on Partials where multiple rows independently identified the same gap (income-increase effective dates; shelter-with-escrow; dependent care recertification re-verification).
