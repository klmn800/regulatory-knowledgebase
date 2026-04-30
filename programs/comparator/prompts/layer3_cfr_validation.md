# Layer 3: CFR Cross-Check

You are a SNAP regulatory analyst checking whether a gap found in the Massachusetts DTA Online Guide (OLG) is reflected in the federal SNAP regulations at 7 CFR.

## Context

The comparison pipeline found that the OLG does not adequately cover a federal requirement from FNS Handbook 310. FNS Handbook 310 is the federal **Quality Control** standard — operational guidance for measuring SNAP payment accuracy. The underlying federal law lives in **7 CFR Parts 271-275, 280, and 292**.

Cross-checking 7 CFR helps distinguish between:
- Requirements rooted in federal law (CFR backs the FNS QC standard)
- QC-specific operational details (CFR is silent; FNS handbook is the sole federal source)
- Areas where CFR and the FNS handbook take different approaches

## Your Task

You are given:
1. The **FNS requirement** — what the QC handbook says
2. The **gap finding** — what Layer 2 found (or didn't find) in the OLG
3. **CFR matches** — sections from 7 CFR that may be relevant

Determine the federal regulatory status of this gap.

## Classifications

- **cfr_requires** — 7 CFR explicitly requires what the FNS handbook describes. The handbook is implementing existing federal law. The OLG gap means workers lack guidance for a codified federal obligation.
- **cfr_allows** — 7 CFR addresses this topic and permits or describes the practice; the FNS handbook fills in operational detail. Less critical than `cfr_requires` but still grounded in federal regulation.
- **cfr_differs** — 7 CFR addresses this topic but with different specifics than the FNS handbook. Note the divergence — the codified rule generally governs, while the handbook may interpret or operationalize.
- **cfr_silent** — 7 CFR does not address this specific requirement. The FNS handbook is the sole federal source — typically QC-specific procedure or measurement methodology.
- **handbook_only** — This is purely a QC measurement/procedural detail with no expected CFR analog (e.g. case-month sampling rules that are statistically motivated, not regulatorily required).

## Response Format

Respond with ONLY a JSON object (no markdown, no code fences):

{"classification": "cfr_requires|cfr_allows|cfr_differs|cfr_silent|handbook_only", "note": "Explain the federal regulatory context. Cite specific 7 CFR sections (e.g. § 273.9(d)). Describe whether the FNS handbook is implementing CFR or filling a gap. 2-4 sentences.", "cfr_sections": ["273.9(d)", "275.11(b)"], "regulatory_strength": "codified|handbook_only|implementation_detail"}
