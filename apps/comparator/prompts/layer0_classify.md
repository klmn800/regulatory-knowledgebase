# Layer 0: FNS Section Classification

You are classifying sections from **FNS Handbook 310**, the federal SNAP Quality Control (QC) manual. This handbook is written for **QC reviewers** — federal/state auditors who check whether SNAP cases were processed correctly. It is NOT a caseworker manual.

We are comparing this handbook against Massachusetts DTA's **Online Guide (OLG)**, which IS the caseworker manual — the guide DTA workers follow day-to-day when processing SNAP cases.

## Your Task

For each FNS section, determine whether it contains **SNAP policy rules that a state caseworker guide should cover**. Not everything in a QC reviewer's manual belongs in a caseworker guide.

## Labels

Classify each section as one of:

### `compare`
The section contains SNAP eligibility rules, benefit calculation methods, income/deduction rules, or requirements that caseworkers must follow when processing cases. **Include sections where policy is embedded in verification/review language** — if the section teaches you what the SNAP rule IS (even while explaining how to verify it), it's `compare`.

**Verification standards are policy.** Sections that specify what documents are acceptable, what verification sources to use, or what evidentiary thresholds apply (e.g., "For standard verification, use the following: ...") are `compare` — these define the verification requirements caseworkers must meet, not just what reviewers check. If the caseworker guide doesn't match these standards, that's a gap.

**Cross-references to other sections are `compare`.** If a section points to another section for verification procedures, rules, or standards (e.g., "See Section 512"), classify it as `compare`. The reference signals that policy or verification requirements exist and need to be checked — even though the details live in the referenced section.

**When in doubt, classify as `compare`.** It is better to compare a borderline section than to skip one that contains real policy.

Examples of `compare` content:
- "Wages and Salaries - 311. This element refers to income earned by a recipient through the receipt of wages, salaries, tips, or commissions." (Section 1021 — defines what counts as earned income)
- "The excess shelter expense is calculated by..." (Section 1150 — shelter deduction formula)
- "Households must report changes which cause their ongoing gross income to exceed 130% of the FPL" (Section 720 — reporting requirements)
- "For standard verification, use the following: Current VBA Award notice; Direct contact with a VBA representative" (Section 1032.1 — acceptable verification sources)
- "In the absence of evidence to the contrary, the reviewer may accept a household's statement." (Section 1032.2 — verification threshold that caseworkers also follow)

### `skip`
The section is about the **QC review process itself** — how to conduct audits, how to document review findings, how to calculate error amounts, or how to report QC results. It may also be a chapter overview or administrative rule. A caseworker guide would never need to cover this content.

Only classify as `skip` when the section is purely about the mechanics of conducting reviews, NOT when it describes what the correct casework standard is.

**Bare section headers with no substantive text** (just a title repeated with no additional content) should be `skip` — there is nothing to compare.

Examples of `skip` content:
- "This chapter outlines procedures for conducting reviews of active cases." (Section 200 — chapter overview)
- "The reviewer must document the basis for..." (Section 1151.1 — documentation instructions for reviewers)
- "Implementation of QC Indexed Policy Memoranda" (Section 151 — administrative rule about policy memo timelines)
- Worked examples showing how to calculate dollar error amounts for QC variances
- A section whose entire text is just its own title (e.g., "Veterans' Benefits – 332.") with no further content

### `reference`
The section is a glossary, definitions list, or terminology section. Not a comparison target, but potentially useful reference material.

Examples of `reference` content:
- "DEFINITIONS. Active Case — A household certified prior to or during the sample month..." (Section 130 — alphabetical glossary of 50+ terms)
- "Common Sources of Bias Include..." (Section 154.1 — defines bias categories)

## Input Format

You will receive:
1. **Full Section (for context)** — the parent section and sibling subsections, shown so you understand the broader topic. Do NOT classify these.
2. **Classify This Section** — the specific section you must classify. Base your label on THIS section only.

Use the context to understand what topic the section falls under, but classify only the designated section.

## Response Format

Respond with ONLY a JSON object (no markdown, no code fences):

{"label": "compare|skip|reference", "reason": "One sentence explaining why. Be specific about what policy rule is present or what makes this non-policy."}
