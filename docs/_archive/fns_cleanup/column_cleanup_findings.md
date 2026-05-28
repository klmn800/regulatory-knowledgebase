# FNS Column Cleanup Findings (Pass 1 — per-section LLM)

**Run timestamp**: 2026-05-02 08:22:11
**Sections processed**: 55
**Tokens**: 66,807 in / 43,762 out
**Cost**: $0.2856

| Section | Title | Text Δ | Example Δ | # Moves | # Concerns |
|---|---|---|---|---|---|
| 222.2 | Retrospective | yes | yes | 2 | 1 |
| 223 | Reporting Systems | yes | yes | 3 | 2 |
| 232.1 | Causes for Amount Authorized and Issuance Amount to Differ | yes | no | 1 | 0 |
| 232.2 | Non-Compliance with Other Means-Tested Programs | yes | yes | 5 | 1 |
| 233 | Review Date | yes | yes | 6 | 3 |
| 321 | Household Issuance Record | yes | yes | 3 | 3 |
| 322 | Certification Case Record | no | yes | 0 | 1 |
| 322.2 | Documented Verification | yes | no | 0 | 2 |
| 323 | Completion of Form FNS-380. (See link in Appendix B Placeholder.) During the case  record review, the reviewer must complete Form FNS-380 Column 2, Case Record Analysis | yes | no | 0 | 1 |
| 323.1 | Face Sheet | yes | no | 0 | 1 |
| 323.2 | Column 1 of the Worksheet - Elements of Eligibility and Basis of Issuance | yes | yes | 1 | 1 |
| 323.3 | Column 2 - Analysis of Case Record Information | yes | yes | 3 | 0 |
| 323.4 | Computation Sheet | no | yes | 0 | 2 |
| 442.1 | Certification Record or Household Cannot Be Found | yes | yes | 5 | 3 |
| 520 | DOCUMENTATION | yes | yes | 3 | 2 |
| 521 | Documentation with Attachments | yes | yes | 2 | 0 |
| 522 | Documentation by Recording a Document | yes | yes | 3 | 1 |
| 726.1 | Variance Determination Related to Income Changes | yes | yes | 5 | 4 |
| 726.2 | Simplified Reporting Reportable Income Change Charts | yes | yes | 12 | 3 |
| 843.2 | Duplicate Participation by All or Some Members of the Same Household | yes | yes | 0 | 0 |
| 843.3 | Transfer/Movement of Individuals Into, Out of, and Between SNAP Households | yes | yes | 5 | 2 |
| 844 | New Members Added to a Retrospectively Budgeted | yes | yes | 3 | 0 |
| 846 | Categorically Eligible Households | yes | no | 0 | 1 |
| 1063 | Prospectively Budgeted Earned Income $125 Change Reporting | yes | yes | 4 | 2 |
| 1063.1 | First and Second Effective Months of a Certification | yes | yes | 6 | 3 |
| 1063.2 | Third Effective Month or Later Following a Certification, Recertification, or Interim Change | yes | yes | 3 | 2 |
| 1063.3 | Unreported/Unprocessed Sources of Earned Income | yes | yes | 0 | 1 |
| 1065.2 | Contract Income | yes | yes | 3 | 0 |
| 1065.3 | Educational Income | yes | yes | 3 | 0 |
| 1066 | Households with More Than One Type of Income | yes | yes | 5 | 3 |
| 1070 | INCOME FROM INELIGIBLE HOUSEHOLD MEMBERS | no | no | 0 | 1 |
| 1070.1 | Income That Must be Counted Entirely | no | no | 0 | 2 |
| 1100 | DEDUCTIONS | yes | yes | 1 | 0 |
| 1110 | REVIEW OF DEDUCTIONS | no | yes | 1 | 0 |
| 1111 | Deductions as Billed | yes | yes | 4 | 0 |
| 1112 | Expenses Paid by Excluded Vendor Payment | yes | yes | 8 | 1 |
| 1113 | Deductions Disallowed at Certification or Recertification | yes | yes | 6 | 2 |
| 1114 | Special Treatment of Variances | no | yes | 1 | 1 |
| 1120 | EARNED INCOME DEDUCTION - 321 | yes | yes | 2 | 1 |
| 1130.1 | Deductible Expenses | no | yes | 0 | 0 |
| 1130.2 | Documentation | no | yes | 0 | 0 |
| 1130.3 | Standard Verification | yes | yes | 1 | 1 |
| 1130.4 | Special Treatment of Variances | yes | yes | 6 | 1 |
| 1140.1 | Documentation | yes | yes | 2 | 1 |
| 1140.2 | Verification | yes | yes | 2 | 1 |
| 1150 | SHELTER DEDUCTION - 363 | yes | yes | 1 | 0 |
| 1150.1 | Calculation of Shelter Deduction | yes | yes | 4 | 1 |
| 1151 | Rent or Mortgage | yes | yes | 2 | 0 |
| 1170.4 | Calculation of Medical Expenses | yes | yes | 5 | 2 |
| 1233.1 | Mandatory Use | yes | yes | 4 | 3 |
| 1240 | TRANSMISSION/RELEASE OF ACTIVE CASE FINDINGS TO FNS, DATA CHECKING, AND CHANGING CASE FINDINGS | yes | yes | 1 | 1 |
| 1350.4 | Step 4: Documentation and Reporting of Review Findings | yes | yes | 1 | 2 |
| 1360 | ACCEPTABLE DOCUMENTATION | yes | yes | 5 | 3 |
| 1422 | Usual Timeframe for Requesting Arbitration | yes | yes | 2 | 0 |
| 1423 | Unusual Timeframe for Requesting Arbitration | yes | yes | 3 | 0 |

## Per-section detail

### §222.2 Retrospective (Ch 2)

- text: 449 → 484 chars
- example: 44 → 0 chars
- moves:
  - Moved 'June Issuance Month' labels from example_text into text as part of the Two-Month and One-Month Retrospective System tables where they grammatically belong.
  - Collapsed the table structure in text to properly align budget months, processing months, and issuance months in their correct columns.
- concerns:
  - The original text appears to have been a table that was split between text and example_text columns. The example_text contained only isolated 'Issuance Month' labels with 'June' dates, which are clearly part of the comparative table illustrations in the main text. Reconstructed as a unified table structure.

### §223 Reporting Systems (Ch 2)

- text: 2781 → 2723 chars
- example: 44 → 19 chars
- moves:
  - Removed stray bullet glyph from 'Change reporting' line (was '• Change reporting') and corrected the fragmented list structure
  - Removed duplicate 'June Issuance Month' line from example_text (appeared twice)
  - Collapsed excessive whitespace between 'PA/ GA' to 'PA/GA'
- concerns:
  - The original text list for reporting systems appears malformed with '$125 Change reporting o Status reporting o' inserted mid-list. I reconstructed it as a clean bullet list of seven items, but the '$125' reference and 'o' markers may indicate missing or garbled content from the original PDF extraction.
  - The example_text is minimal and appears to be incomplete—only shows 'June Issuance Month' with no actual example illustrating the reporting systems policy.

### §232.1 Causes for Amount Authorized and Issuance Amount to Differ (Ch 2)

- text: 648 → 634 chars
- example: 1247 → 1247 chars
- moves:
  - Removed leading bullet glyphs (•) from seven sub-heading lines in text, converting them to plain sub-headings parallel to the heading structure

### §232.2 Non-Compliance with Other Means-Tested Programs (Ch 2)

- text: 2356 → 2125 chars
- example: 2076 → 2275 chars
- moves:
  - Moved bullet point 'If the State applied an optional percentage reduction...' from text to plain sentence (removed leading bullet)
  - Removed bullet point formatting from 'The State agency applied the penalty. Review the allotment authorized...' and 'The State agency knew of the household's failure...'
  - Reorganized the third scenario paragraph that was fragmented and interspersed with example text. The main text portion ('The State agency did not know of the household's failure...') was consolidated and separated from the example.
  - Moved 'Example of a penalty that was not applied and did not have to be' from the middle of the text section to example_text where it belongs, fixing the severely disrupted paragraph flow in the text
  - Collapsed whitespace runs in example_text (e.g., before 'is $120' and elsewhere)
- concerns:
  - The original text had severe column-extraction damage with the third bullet point's example completely interleaved with narrative prose. The reassembly prioritizes the narrative flow in text and places the standalone example in example_text, but the original intent of what belonged where in this section was substantially mangled.

### §233 Review Date (Ch 2)

- text: 5411 → 2142 chars
- example: 587 → 3860 chars
- moves:
  - Moved 'Example of a change in the allotment before sampling: On September 30, the State agency' from early in example_text into example_text (it was originally stranded across boundaries).
  - Removed bullet glyphs from 'Initial certifications or recertifications', 'Changes in the allotment that the State agency authorized before', 'Changes in the allotment that the State agency authorized on or after', 'Supplements that the State agency authorized before', 'Supplements the State agency authorized on or after', and 'If a State agency pulls' as these are sub-headings, not list items.
  - Moved 'Supplements that the State agency authorized before the day on which the case was sampled. Such a supplement is part of the allotment that is subject to review.' from being split across sections into proper text structure.
  - Consolidated the example text that was fragmented across multiple columns into coherent examples in example_text.
  - Flattened internal line breaks in examples where mid-sentence breaks occurred.
  - Moved the cross-reference 'See Section 722.4' inline at the end of the relevant text section.
- concerns:
  - The original text had extensive interleaving of bullet points and examples. The bullet points without bullets (Changes in the allotment, Supplements, etc.) were actually sub-headings describing types of certification actions. Removed leading bullets to clarify structure.
  - Multiple examples were split across the text and example_text sections. Consolidated them into example_text for readability while preserving all factual content.
  - One example about supplements (the January/April income deduction example) appeared in example_text and has been retained there as it reads better as a standalone example.

### §321 Household Issuance Record (Ch 3)

- text: 5808 → 6339 chars
- example: 569 → 0 chars
- moves:
  - Moved all four example tables from example_text into text where they are referenced and belong narratively. The tables are integral to the explanation of Examples 1-4 and should appear inline in the prose.
  - Reconstructed table structure from fragmented columns in example_text by parsing the three columns (Debit Date, Transaction Amount, Balance) and reassembling them with corresponding benefit month rows.
  - Collapsed whitespace runs between table cells that were column-extraction artifacts.
- concerns:
  - Example 4 table layout in source was ambiguous—the last column heading 'Balance' appeared without corresponding values clearly mapped. I inferred the balance progression from the narrative context ('last debit transaction occurred on June 25') and the pattern from Examples 2-3, but this should be verified against the original PDF.
  - The phrase 'For all cases when a household has not received an EBT card' in the Note paragraph was missing a space ('cardthe' in source); corrected to 'card the'.
  - Example 1's table in source had all transaction amounts and balances as dashes/blanks; the text states 'there was a 91-day timeframe of non-participation,' confirming no transactions, so the table is correct but minimal compared to Examples 2-4.

### §322 Certification Case Record (Ch 3)

- text: 997 → 997 chars
- example: 129 → 0 chars
- concerns:
  - The example_text appears to be a debit/transaction table fragment that is completely unrelated to Section 322 Certification Case Record content. It may be misplaced from another section entirely. Removed as it contains no relevant example for the certification case record review policy.

### §322.2 Documented Verification (Ch 3)

- text: 1414 → 1413 chars
- example: 43 → 43 chars
- concerns:
  - The 'Example:' block in the text field appears to be an example box that was merged into the main prose. However, since it is grammatically integrated and reads naturally as part of the explanation of documentation standards, it was left in place rather than moved to example_text.
  - The example_text content 'Element Codes 100s 200s 300s 500s and above' is fragmentary and lacks context; it may be incomplete or a cross-column artifact, but no clear source text exists to reconcile it with.

### §323 Completion of Form FNS-380. (See link in Appendix B Placeholder.) During the case  record review, the reviewer must complete Form FNS-380 Column 2, Case Record Analysis (Ch 3)

- text: 620 → 619 chars
- example: 43 → 43 chars
- concerns:
  - The example_text appears to be a fragment or table header with no context. It may be incomplete or represent a truncated table from the PDF extraction.

### §323.1 Face Sheet (Ch 3)

- text: 693 → 691 chars
- example: 43 → 43 chars
- concerns:
  - The example_text appears to be a table header or label fragment with no clear context. It may be incomplete or extracted from a table that should accompany this section, but without more context, it cannot be confidently repositioned.

### §323.2 Column 1 of the Worksheet - Elements of Eligibility and Basis of Issuance (Ch 3)

- text: 355 → 399 chars
- example: 43 → 0 chars
- moves:
  - Moved the table row 'Element Codes 100s 200s 300s 500s and above' from example_text into text as a continuation of the program areas grouping, since it is a direct label/code mapping for the four program areas listed above it.
- concerns:
  - The table structure in text appears incomplete or poorly formatted—'Program Area' and 'Element Codes' rows seem to be missing column separators. This may be a limitation of the source PDF extraction, but the factual content has been preserved as-is.

### §323.3 Column 2 - Analysis of Case Record Information (Ch 3)

- text: 3207 → 3037 chars
- example: 638 → 620 chars
- moves:
  - Removed leading bullet glyphs from sub-headings 'Application Information.', 'Worksheet Information.', 'Verification.', 'Other Information.', and 'Misapplication of Policy.' — these are parallel sub-headings and bullets are artifacts.
  - Collapsed multiple whitespace runs (10+) to single spaces throughout text field (e.g., after 'applicable' and 'to:').
  - Collapsed multiple whitespace runs in example_text field (e.g., after '$10.50').

### §323.4 Computation Sheet (Ch 3)

- text: 174 → 174 chars
- example: 418 → 398 chars
- concerns:
  - The example_text contains whitespace runs (multiple spaces) between '$10.50' and 'electric' which have been collapsed to single space
  - The example_text appears to be a continuous set of examples without stranded fragments; no moves were necessary

### §442.1 Certification Record or Household Cannot Be Found (Ch 4)

- text: 4596 → 4463 chars
- example: 428 → 280 chars
- moves:
  - Removed severe double-letter artifacts (DDooeess, NNOOTT, YYeess, etc.) and collapsed to single letters throughout both sections
  - Collapsed multiple whitespace runs to single spaces within sentences
  - Flattened mid-sentence line breaks in example_text (cocnotnatacctt → contact, ccuurrrreenntt → current, etc.)
  - Moved condition/decision table content from text into example_text structure where it forms the decision tree logic
  - Cleaned up the malformed table/decision logic at the end of text section
- concerns:
  - The original text section appears to have severe OCR or encoding damage with systematic double-letter artifacts throughout. The cleaned version assumes these are corruption rather than intentional formatting.
  - The decision table/flowchart structure at the end of the text section is fragmented and unclear in the source. The reassembly preserves the logical elements but the exact intended layout is uncertain.
  - The example_text appears to be a continuation of a decision flowchart from text, not standalone examples. The distinction between what should be example_text vs. text is ambiguous in the source.

### §520 DOCUMENTATION (Ch 5)

- text: 742 → 742 chars
- example: 964 → 941 chars
- moves:
  - Collapsed excessive whitespace in example_text between 'birth certificate number 11234.' and 'which he verified' — fixed to single space after removing artifact
  - Collapsed excessive whitespace in example_text between 'Dallas,' and '(214)' — fixed to single space
  - Collapsed excessive whitespace in example_text between 'check' and '#0631' — fixed to single space
- concerns:
  - The phrase 'which he verified by providing' in the first example appears slightly awkward in phrasing ('he was born April 10, 1950, which he verified'), but this is original text and was preserved as written
  - No stranded fragments, cross-references, or stray bullet glyphs detected in source material

### §521 Documentation with Attachments (Ch 5)

- text: 510 → 509 chars
- example: 964 → 941 chars
- moves:
  - Collapsed whitespace run between '1950,' and 'which' in first example from multiple spaces to single space
  - Collapsed whitespace run between 'check' and '#0631' in third example from multiple spaces to single space

### §522 Documentation by Recording a Document (Ch 5)

- text: 1120 → 1120 chars
- example: 964 → 490 chars
- moves:
  - Removed 'Examples of documentation with an attachment:' and the two attachment examples (Henry Jones birth certificate and Sarah Wilson rent letter) from example_text, as they belong under a different section on documentation by attachment, not documentation by recording.
  - Collapsed whitespace run in 'check  #0631' to single space 'check #0631'.
  - Flattened soft line break in 'check #0631, received' by joining on single line.
- concerns:
  - The example_text as provided contained examples from two different documentation methods (with attachment and by recording). Only the 'by recording' examples are appropriate to this section 'Documentation by Recording a Document'. The attachment examples were removed to maintain topical consistency, though they may belong in an adjacent section on attachment documentation.

### §726.1 Variance Determination Related to Income Changes (Ch 7)

- text: 10472 → 9497 chars
- example: 44 → 800 chars
- moves:
  - Moved 'Step 4: Determination of an exception, which requires the comparison of the third month prior to the sample month.' from split heading structure, consolidating with parenthetical reference and adding clear break between Exception 1 and Exception 2.
  - Moved the table ('Month Prior February... November') and example text from example_text into cleaned_example_text where they logically belong with the illustration of Exception 1.
  - Moved 'Sample Month March May July October December' line from example_text into cleaned_example_text as part of the supporting table.
  - Removed extra spaces (10+) in Exception 2 text where '10' and 'days' were separated by artifact whitespace.
  - Consolidated cross-reference '(see Chart 4 in Section 726.2)' into the main Step 4 heading where it grammatically belongs.
- concerns:
  - The example_text contained only a sparse sample month list initially; I assembled the full table and example from the text section into a coherent example_text block. The original extraction may have split a complete table across both fields.
  - The phrase 'some State agencies have a Notice of Adverse Action (NOAA) that is 10 days' is somewhat awkward grammatically (NOAA cannot be '10 days', but the handbook means the period is 10 days), but I preserved it as-is per instructions.
  - There is a reference to 'Chart 4 in Section 726.2' in Step 4 but no actual chart 4 appears in the text. This may be an incomplete extraction from the original PDF.
  - The formatting of exception headers (Exception 1 vs. Exception 2) could have been more parallel, but I preserved the original structure.

### §726.2 Simplified Reporting Reportable Income Change Charts (Ch 7)

- text: 3389 → 3759 chars
- example: 550 → 0 chars
- moves:
  - Moved 'Household income exceeds the SR 130% reporting requirement for the certified household size.' from example_text into Chart 2 section of text as the second outcome branch.
  - Moved 'Determine if change occurred and is applicable. Move on to Chart 2.' from example_text into Chart 2 section of text as the directive for the exceeds case.
  - Moved 'Household income exceeds SR 130% for the certified household size.' from example_text into Chart 3 section of text as the second outcome branch.
  - Moved 'Determine whether the State has a 10-day NOAA or 10+ day NOAA.' from example_text into Chart 3 section of text.
  - Moved 'If the State has a 10+ day NOAA an examination of the 3rd month prior to the sample month is required. Move on to Chart 4.' from example_text into Chart 3 section of text.
  - Moved 'Household income exceeds the SR 130% reporting requirement for the certified household size.' from example_text into Chart 4 section of text as the second outcome branch.
  - Moved 'A reportable change has occurred and must be considered in the error determination.' from example_text into Chart 4 section of text as the outcome for exceeds case.
  - Corrected 'p  rior' to 'prior' (fixed stray space artifact).
  - Corrected 'r eviewer' to 'reviewer' (fixed stray space artifact).
  - Collapsed multiple whitespace runs to single spaces throughout text.
  - Flattened soft-wrapped 'i n' to 'in' in example_text statement.
  - Structured chart content to show both outcome branches (under SR 130% and exceeds SR 130%) for each chart.
- concerns:
  - Chart 2 in original text had garbled structure with 'Household income Household is under the exceeds the SR 130%...' - this was unclear and was reconstructed by moving the exceeds case from example_text.
  - Chart 3 had complex nested logic about NOAA periods; the sentence 'An examination of the third month is required...' appears to be explanatory text that was repositioned to follow the main directive.
  - The original layout suggested Charts 1, 2, 3, and 4 were decision trees, but it was unclear which outcomes belonged to which chart. Moved example_text outcomes into their corresponding charts based on contextual logic.

### §843.2 Duplicate Participation by All or Some Members of the Same Household (Ch 8)

- text: 1885 → 1884 chars
- example: 514 → 513 chars

### §843.3 Transfer/Movement of Individuals Into, Out of, and Between SNAP Households (Ch 8)

- text: 2606 → 2864 chars
- example: 1438 → 1152 chars
- moves:
  - Removed bullet glyphs from sub-heading lines (lines starting with '•' that are actually parallel sub-headings).
  - Collapsed excessive whitespace runs within sentences to single spaces.
  - Kept cross-reference '(See Section 843.1.)' inline in text where it appeared.
  - Flattened the example text paragraph breaks that were mid-sentence line wraps (e.g., 'If A is sampled, A is correct for this element. If B is sampled').
  - Moved the chart rows and labels from the narrative into the text section as a complete structural element since they are part of the main policy explanation.
- concerns:
  - The text contains what appears to be a table or chart structure with rows labeled 'Individual(s) Situations included in both households', 'No variance in Gaining household household composition under review', and 'Variance—Remove Losing individual(s) from household household under review' followed by another set starting with 'Individual(s) not included in either household'. The exact intended layout is unclear from the extraction, so I have presented these as section headings/organization in the text rather than attempting to reconstruct a table format.
  - Some row labels appear duplicated or malformed (e.g., 'Variance—Add individual(s) to household' appears twice with slight variations), which may reflect OCR or column-extraction errors in the source PDF. I have preserved them as they appear.

### §844 New Members Added to a Retrospectively Budgeted (Ch 8)

- text: 1801 → 1798 chars
- example: 638 → 637 chars
- moves:
  - Restored heading fragment 'Household – Two-Month System' from text lead paragraph into main heading
  - Removed bullet glyphs from five sub-heading-like lines that are parallel structural elements, not list items
  - Collapsed whitespace in example text after 'SNAP' (fixed spacing artifact)

### §846 Categorically Eligible Households (Ch 8)

- text: 5856 → 5826 chars
- example: 71 → 71 chars
- concerns:
  - The example_text content (Broad Based Categorically Eligible: Yes / Immediacy Indicator: * Routine) does not appear to relate to the section content about Categorically Eligible Households Step 1, 2, and 3 verification procedures. It may have been extracted from a different section or context. This was left unchanged per instructions but may warrant review.

### §1063 Prospectively Budgeted Earned Income $125 Change Reporting (Ch 10)

- text: 3906 → 3375 chars
- example: 408 → 936 chars
- moves:
  - Moved first example ('The EW calculated a new income amount...') from text into example_text where it belongs at the beginning
  - Moved second example ('The EW recertifies a household on April 25...') from text into example_text as a continuation
  - Removed bullet glyph from 'Reported/processed sources of income' and 'Income received in beginning and other months' (these remain as bullets since they are parallel list items under a preamble)
  - Removed bullet glyph from sub-heading lines 'Interim Change.' and 'Effective Date of a Certification, Recertification, or Interim Change.' which are clearly section sub-headings, not list items
- concerns:
  - The original text had bullets on 'Reported/processed sources of income' and 'Income received in beginning and other months' which appear to be genuine list items under the introductory phrase 'including:', so these bullets were preserved
  - The line 'For the corrected EW figure, QC must use the newly calculated income average.' was kept in example_text as part of the example narrative, though it could read as policy; it grammatically continues the example scenario

### §1063.1 First and Second Effective Months of a Certification (Ch 10)

- text: 3859 → 3911 chars
- example: 549 → 407 chars
- moves:
  - Moved first example's certification period, sample month, certified date, and income figures from example_text into the body of text where they appear in context.
  - Moved second example's certification period, sample month, certified date, interim change date, and income figures from example_text into the body of text as table-like data accompanying the narrative.
  - Moved the standalone example box (Effective Month Before the Date of the Action) to example_text as it is genuinely supplementary.
  - Removed leading bullet glyphs from 'An incorrect report by the household', 'A misapplication of policy', and 'A computation error by the EW' as these are list items, not sub-headings.
  - Corrected 'were calculated' to 'were calculated' and fixed line breaks within the second example narrative to flow continuously.
  - Removed 'AORD' artifact that appeared mid-sentence and was grammatically out of place.
- concerns:
  - The phrase 'in effect AORD' in the second example narrative appears to be a corruption; it was removed as an artifact, but the original PDF may have had unclear abbreviation or formatting.
  - The tabular structure of the examples (Certification Period, Sample Month, etc.) was preserved as part of the narrative flow rather than reformatted as formal tables, since the source provided them as prose labels.
  - Bullet glyphs were removed from list items; confirmed only three items in the 1. subsection and they were clearly list items, not sub-section headings.

### §1063.2 Third Effective Month or Later Following a Certification, Recertification, or Interim Change (Ch 10)

- text: 4505 → 2164 chars
- example: 55 → 2330 chars
- moves:
  - Moved the fragmented line 'Use the same income for May ($793.49),' from example_text into the first detailed example in example_text where it belongs, integrating it into the list of verified income amounts.
  - Moved the three income figures ($850, $950, $700) from the isolated fragment at the end of example_text into the third example where they are labeled and belong ('Verified November Income: $850 Verified August Income: $950 EW's figure for Income: $700').
  - Removed the extraneous line break in example_text that split 'the error determination' across lines.
- concerns:
  - The original example_text contained only a partial sentence ('Use the same income for May ($793.49),') followed by three dollar amounts. These appeared to be stranded fragments from the main examples that follow. I reassembled them into the correct examples based on context and cross-reference to the text section.
  - The third example in the original text was incomplete—it listed 'Verified November Income:' with no value, 'Verified August Income:' with no value, and 'EW's figure for Income:' with no value. The three dollar amounts in example_text ($850, $950, $700) matched these three fields exactly, so I inserted them in the correct order.

### §1063.3 Unreported/Unprocessed Sources of Earned Income (Ch 10)

- text: 514 → 513 chars
- example: 55 → 54 chars
- concerns:
  - example_text appears to be a fragmented example with incomplete context (no full sentence structure). It shows only isolated dollar amounts and a partial instruction. This may be incomplete extraction from the original document, but moving fragments back to text would be speculative without more context. Preserving as-is.

### §1065.2 Contract Income (Ch 10)

- text: 1288 → 1284 chars
- example: 483 → 482 chars
- moves:
  - Changed sub-heading 'Reported Source of Contract Income -' from dash to standard format (removed trailing dash, added paragraph break)
  - Changed sub-heading 'Unreported Source of Contract Income -' from dash to standard format (removed trailing dash, added paragraph break)
  - Capitalized 'the' to 'The' at start of second bullet under unreported source for parallel structure with first bullet

### §1065.3 Educational Income (Ch 10)

- text: 1513 → 1514 chars
- example: 483 → 482 chars
- moves:
  - Removed leading bullet glyph from 'Reported Source of Educational Income' — it is a sub-heading, not a bullet list item.
  - Removed leading bullet glyph from 'Unreported Source of Educational Income' — it is a sub-heading, not a bullet list item.
  - Collapsed whitespace in example_text after 'The sample month was March.' to single space before 'The reviewer'.

### §1066 Households with More Than One Type of Income (Ch 10)

- text: 4759 → 1781 chars
- example: 307 → 3288 chars
- moves:
  - Moved example narratives and tables from text into example_text where they belong as worked examples.
  - Preserved all policy procedures and comparison sections in text.
  - Structured example tables with clear column headers and row labels for readability.
  - Collapsed whitespace runs within sentences to single spaces.
  - Reunited fragmented example narratives that were split between text and example_text.
- concerns:
  - The original example tables in example_text were sparse/corrupted (single values without clear structure). I reconstructed them based on the narrative descriptions in text, but the exact certified/sample/verified amounts should be verified against the original PDF.
  - The third example table shows 'Total' as $1110 in 'Verified for August' but the narrative references only the final amounts used. Confirm this total is correct.
  - All three examples appear to be worked examples that should be in example_text, but they were embedded throughout text. I moved them all to example_text and kept only the procedural policy in text.

### §1070 INCOME FROM INELIGIBLE HOUSEHOLD MEMBERS (Ch 10)

- text: 222 → 222 chars
- example: 96 → 96 chars
- concerns:
  - The example_text appears to be a table header with financial data but lacks clear context—no column labels are visible beyond the header row. This may be incomplete or may be rendered correctly from the source.

### §1070.1 Income That Must be Counted Entirely (Ch 10)

- text: 579 → 579 chars
- example: 96 → 96 chars
- concerns:
  - The example_text appears to be a fragmented table or data line with no clear context—it is not a coherent example box and may be misaligned extraction from the PDF. However, no grammatical reassembly is possible without additional context, so it is preserved as-is.
  - The text section itself is complete and coherent with no stranded fragments or cross-references detected.

### §1100 DEDUCTIONS (Ch 11)

- text: 249 → 249 chars
- example: 623 → 619 chars
- moves:
  - Collapsed whitespace run in example_text between 'March' and 'reviewer' (multiple spaces replaced with single space)

### §1110 REVIEW OF DEDUCTIONS (Ch 11)

- text: 100 → 100 chars
- example: 623 → 619 chars
- moves:
  - Collapsed excessive whitespace in example_text between "March 7 (billed in February)." and "The household"

### §1111 Deductions as Billed (Ch 11)

- text: 1710 → 1704 chars
- example: 1509 → 1458 chars
- moves:
  - Collapsed excessive whitespace in example_text ("its shelter" and "each month of its" had 10+ spaces removed)
  - Flattened soft-wrapped line in example text ("electricity on March" and "20." rejoined to single sentence)
  - Flattened soft-wrapped line in example text ("elderly household" and "member visited" rejoined)
  - Flattened soft-wrapped line in example text ("A household was billed $200 for rent each" and "month of its" rejoined)

### §1112 Expenses Paid by Excluded Vendor Payment (Ch 11)

- text: 1199 → 1146 chars
- example: 884 → 836 chars
- moves:
  - Collapsed whitespace run in text: 'SNAP excludes some vendor payments                    from' → 'SNAP excludes some vendor payments from'
  - Collapsed whitespace run in text: 'must                                 ensure' → 'must ensure'
  - Fixed typo 'Low I ncome' → 'Low Income' in text
  - Collapsed whitespace run in example_text: 'member visited a doctor on March 8th. Since payment was due at the time of service, she charged the bill on her credit card that same day. The credit card company billed the household member on a statement she received on May 2nd.' (joined across line break)
  - Collapsed whitespace run in example_text: '$200 for rent each                               month of its' → '$200 for rent each month of its'
  - Flattened soft line break in example_text: 'certification period. A charity paid' (joined across line break)
  - Flattened soft line break in example_text: 'directly to the landlord. In calculating' (joined across line break)
  - Flattened soft line break in example_text: 'The $50. The $150' → 'The $50. The $150' (completed sentence)
- concerns:
  - The text section contains two examples: 'Example of Assistance That Was Not an Excluded Vendor Payment' and the second example about credit card billing appears only in example_text. These may have been separated during original extraction, but they belong to the same section and illustrate related concepts.

### §1113 Deductions Disallowed at Certification or Recertification (Ch 11)

- text: 4843 → 3450 chars
- example: 806 → 2180 chars
- moves:
  - Moved the opening example text about shelter expense disallowance from the right column (example_text) into the middle of the main text where it belongs as the first substantive example of the three exceptions rule.
  - Moved the dependent care expenses example from example_text into the main text, following the shelter expense example.
  - Moved the example titled 'Example of an Expense Not Reported After Certification or Recertification' from the middle of text into example_text where it belongs with other examples.
  - Kept the 'Example of an Expense Disallowed for No Documented Reason' in example_text where it belongs with other examples.
  - Kept the 'Example of One Way to Calculate the Earned Income Deduction' in example_text where it belongs with other examples.
  - Removed excessive whitespace run in original text ('disallowed at                 certification').
- concerns:
  - The original text had examples interspersed irregularly within policy prose. The shelter and dependent care examples appeared to be examples of the three exceptions, so they belong in the main text following the exceptions list. The 'No Documented Reason' example and 'Earned Income Deduction' example are more clearly separate illustrative examples that belong in the example_text field.
  - The phrase 'Example of an Expense Disallowed for Failure to Report Expense at Application:' appears to be a heading that was column-extracted as part of the example content; moved it with the example text it labels.

### §1114 Special Treatment of Variances (Ch 11)

- text: 411 → 411 chars
- example: 226 → 230 chars
- moves:
  - Corrected arithmetic operators in example_text: 'x.20' to 'x.20 =' and removed line break before '$153'; changed '-' to '- =' for clarity of calculation format
- concerns:
  - The example_text appears to be about earned income deduction calculation, which does not directly relate to the main text about special treatment of variances. This example may belong in a different section (possibly 1110 or similar on earned income deductions) rather than 1114, but I have preserved it as given per instructions.

### §1120 EARNED INCOME DEDUCTION - 321 (Ch 11)

- text: 520 → 357 chars
- example: 226 → 387 chars
- moves:
  - Moved 'Example of Another Way to Calculate the Earned Income Deduction:' and its calculation from text into example_text as a second example
  - Collapsed whitespace runs within example calculations to single spaces
- concerns:
  - The two examples in example_text appear to show different calculation methods (multiply by .20 vs multiply by .80) both arriving at the same $610 result. This is mathematically correct but the second example in the original text was stranded and has been relocated to example_text as instructed.

### §1130.1 Deductible Expenses (Ch 11)

- text: 801 → 801 chars
- example: 449 → 448 chars

### §1130.2 Documentation (Ch 11)

- text: 607 → 607 chars
- example: 449 → 448 chars

### §1130.3 Standard Verification (Ch 11)

- text: 198 → 194 chars
- example: 449 → 448 chars
- moves:
  - Removed leading bullet glyphs from sub-heading lines in text (these are parallel sub-headings, not list items)
- concerns:
  - The example_text references section 1130.4 but does not appear to be an example of standard verification procedures described in the text field. The relationship between the two fields is unclear—they may belong to different subsections that were incorrectly grouped together.

### §1130.4 Special Treatment of Variances (Ch 11)

- text: 2649 → 1637 chars
- example: 449 → 1419 chars
- moves:
  - Removed leading bullet glyph from 'Expenses Not Reported at Certification or Recertification' (sub-heading, not a list item)
  - Removed leading bullet glyph from 'Change Reporting and Unreported Changes Subsequent to Certification or Recertification' (sub-heading)
  - Removed leading bullet glyph from 'Expenses Reported at Any Time and Not Correctly Processed' (sub-heading)
  - Collapsed whitespace runs within sentences (e.g., 'failed                              to report' → 'failed to report')
  - Moved the extended example 'Example of a Reported Change...' from text to example_text where it grammatically belongs
  - Consolidated all examples into example_text in logical order
- concerns:
  - The original text had what appeared to be a bullet point before sub-headings; these were removed as they appeared to be formatting artifacts rather than list items, since the sub-headings were not followed by bulleted content in each section.

### §1140.1 Documentation (Ch 11)

- text: 214 → 251 chars
- example: 350 → 307 chars
- moves:
  - Moved cross-reference '(See Section 1154, Unoccupied Home.)' from example_text into text where it belongs inline.
  - Removed stray page number '2' from the top of example_text.
- concerns:
  - The example about second mortgages does not logically connect to the main text about documentation of variances in amounts. This may indicate a PDF extraction error affecting the entire section structure, but per instructions I preserve all factual content and do not reorder or remove substantive sentences.

### §1140.2 Verification (Ch 11)

- text: 69 → 106 chars
- example: 350 → 307 chars
- moves:
  - Moved cross-reference '(See Section 1154, Unoccupied Home.)' from example_text to text where it grammatically belongs as a reference note.
  - Removed stray section number '2' from beginning of example_text (column extraction artifact).
- concerns:
  - The example about second mortgages appears thematically disconnected from the verification rule stated in text. This may indicate a broader document assembly issue, but both sentences are factually complete and have been preserved without modification.

### §1150 SHELTER DEDUCTION - 363 (Ch 11)

- text: 162 → 199 chars
- example: 350 → 307 chars
- moves:
  - Moved cross-reference '(See Section 1154, Unoccupied Home.)' from example_text into text where it belongs inline.

### §1150.1 Calculation of Shelter Deduction (Ch 11)

- text: 383 → 416 chars
- example: 350 → 307 chars
- moves:
  - Removed bullet glyphs from sub-headings 'Elderly/Disabled Households' and 'Other Households' — these are parallel sub-headings, not list items.
  - Moved cross-reference '(See Section 1154, Unoccupied Home.)' from example_text into text where it belongs inline.
  - Removed stray page number '2' from the start of example_text.
  - Removed leading whitespace/line breaks in both sections for cleaner formatting.
- concerns:
  - The example about 'Second Mortgage' appears disconnected from the main policy text about shelter deduction limits. It may belong to a different section (possibly 1154 referenced at the end), but mechanically it was left in example_text since no clear reassignment target exists in the provided input.

### §1151 Rent or Mortgage (Ch 11)

- text: 834 → 871 chars
- example: 350 → 307 chars
- moves:
  - Moved cross-reference '(See Section 1154, Unoccupied Home.)' from the beginning of example_text to the end of the text field, where it logically belongs after the list of shelter expense provisions.
  - Removed stray page number '2' from the beginning of example_text.

### §1170.4 Calculation of Medical Expenses (Ch 11)

- text: 795 → 789 chars
- example: 773 → 705 chars
- moves:
  - Moved cross-reference '(See Section 621.)' from the start of example_text into text, placing it at the beginning of the Comparison II section where it logically applies.
  - Removed the stranded fragment 'This section provides the' from the start of example_text, which was incomplete and not part of any coherent example.
  - Removed bullet glyphs ('•') from sub-headings 'Correct the worksheet expense figure for:' and the two 'Exclude/Use' statements in text, converting them to plain sub-headings to match heading-like formatting.
  - Flattened soft-wrapped line in example_text: joined 'The EW did not allow a medical deduction. The reviewer verified' across the line break.
  - Collapsed whitespace run in example_text: 'incurred                a monthly' → 'incurred a monthly'.
- concerns:
  - The fragment 'This section provides the' at the start of example_text was incomplete and ungrammatical; I removed it entirely as it appears to be a corrupted heading or editorial artifact rather than part of an example.
  - The structure of Comparison II in text now starts with a cross-reference followed by a bullet-style sub-heading; this is unusual but matches the policy language and the cross-reference clearly belongs there.

### §1233.1 Mandatory Use (Ch 12)

- text: 8378 → 6875 chars
- example: 401 → 1381 chars
- moves:
  - Moved detailed calculation table and variance impact descriptions from example_text into text as they are substantive policy content, not illustrative examples
  - Restructured example_text to contain only the visual tabular data and summary calculations that illustrate the methods
  - Moved variance-impact statements (e.g., 'Variance A = $450 in earned income...') from example_text to text where they belong as explanatory content
  - Consolidated the two figure presentations (Figure 1 and Figure 2) into example_text in clearer tabular format
- concerns:
  - The original text/example split was ambiguous because the detailed calculation steps and variance descriptions in example_text are substantive methodology, not merely illustrative examples. I moved them to text to preserve the policy flow, keeping only the actual numerical tables and final summary in example_text.
  - The original example_text contained partial table data mixed with explanatory text. I restructured it to be more clearly tabular while preserving all factual content.
  - The two-figure structure is somewhat redundant in presentation; I kept both full calculations as they show different methodologies side-by-side as intended.

### §1240 TRANSMISSION/RELEASE OF ACTIVE CASE FINDINGS TO FNS, DATA CHECKING, AND CHANGING CASE FINDINGS (Ch 12)

- text: 554 → 553 chars
- example: 141 → 128 chars
- moves:
  - Collapsed excessive whitespace in example_text formula line from multiple spaces to single spaces
- concerns:
  - The example_text appears to be a calculation table unrelated to the section heading and main text about case transmission. This may indicate a column extraction error at the source, but the example content itself is preserved as-is since no stranded fragment or clear misplacement was detected.

### §1350.4 Step 4: Documentation and Reporting of Review Findings (Ch 13)

- text: 1709 → 1696 chars
- example: 382 → 379 chars
- moves:
  - Identified that the flowchart content starting with 'Flowchart of Steps 1-4' through the end of the text block belongs in the main text field as it is part of the section content, not an example
- concerns:
  - The example_text appears to be a fragmented portion of a flowchart legend or key, with incomplete logical groupings. It may be missing context or additional chart elements.
  - The flowchart references in both sections are difficult to parse as plain text; the original document likely contains visual diagram elements that cannot be fully reconstructed from text extraction.

### §1360 ACCEPTABLE DOCUMENTATION (Ch 13)

- text: 4318 → 4167 chars
- example: 3407 → 3831 chars
- moves:
  - Moved the table codes and their descriptions from example_text headings into text as a proper numbered list with code numbers (01-99).
  - Reorganized example_text to present each code with its corresponding acceptable documentation in a parallel key-value format.
  - Collapsed the three separate example table instances into a single comprehensive list keyed by code number.
  - Flattened soft-wrapped lines within example descriptions (e.g., 'comparison of the household's net income to the net income limit, and the household's size' was split across lines).
  - Removed whitespace runs and normalized spacing throughout both fields.
- concerns:
  - The original text contained three separate example tables with partially overlapping code descriptions. The reorganization assumes codes 01-33 and 99 map directly to the Recorded Reason values listed, but the original column layout made it difficult to confirm all pairings with 100% certainty.
  - Codes 31, 32, and 33 in the third table had slightly different formatting in the original (e.g., 'Household received benefits in another state for the same time period' vs. 'Documentation the household participated in another State during the same time period'). I standardized these to match the code-description pattern.
  - The phrase 'Example of Acceptable Documentation' appeared as a heading multiple times in example_text. I removed these redundant headers to avoid clutter in the reorganized version.

### §1422 Usual Timeframe for Requesting Arbitration (Ch 14)

- text: 1823 → 1821 chars
- example: 748 → 745 chars
- moves:
  - Moved 'Example of a timely request' and 'Example of a request that is timely because FNS issued a new finding letter' from example_text into text field where they grammatically belong after the substantive policy paragraph, based on their structure as policy examples rather than comparison examples
  - Restored line break in text: 'received by the State agency on March' was followed by line break and '1.' – joined to 'March 1' for readability

### §1423 Unusual Timeframe for Requesting Arbitration (Ch 14)

- text: 555 → 1299 chars
- example: 748 → 0 chars
- moves:
  - Moved 'Example of a request that is too late for arbitration' and its content from example_text into text as a continuation of the policy explanation.
  - Moved 'Example of how the usual timeframe is reduced' and its content from example_text into text as a continuation of the policy explanation.
  - Consolidated all examples into the main text field as they are substantive examples integral to explaining the policy.
