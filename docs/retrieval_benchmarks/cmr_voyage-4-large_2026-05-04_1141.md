# CMR Retrieval Benchmark — voyage-4-large

**Run**: 2026-05-04T11:41:03  
**Source**: cmr  
**Label**: voyage-4-large  
**Top-N retrieved + judged**: 5  
**Embedding model**: `voyage-4-large`  
**Collection suffix**: `_voyage4large`  
**Judge model**: `claude-haiku-4-5-20251001`  
**Methodology**: LLM-as-judge — Claude Haiku rates each chunk RELEVANT / PARTIAL / IRRELEVANT.  
**Benchmark**: CMR retrieval benchmark v2 — covers all 18 chapters, mixed difficulty, includes adversarial cases for hybrid/rerank testing  

## Summary

| Metric | Value | Notes |
|---|---|---|
| Relevance@1 | 22/37 (59%) | Did rank 1 = RELEVANT? |
| Relevant@5 (avg) | 1.51 / 5 | Avg # of RELEVANT chunks in top 5 |
| Useful@5 (avg) | 4.68 / 5 | Avg # of (RELEVANT or PARTIAL) chunks in top 5 |
| Mean rank-weighted score | 1.799 / 2.7 | Sum of (weight × score) over top 5; weights [1.0, 0.7, 0.5, 0.3, 0.2]; score RELEVANT=1.0 / PARTIAL=0.5 / IRRELEVANT=0.0 |

## Quick Summary Table

| # | ID | Topic | Rank-1 Judge | Rank-1 Sim Score | Relevant@5 | Useful@5 | RW |
|---|---|---|---|---|---|---|---|
| 1 | cmr_001 | SNAP asset limit | **PARTIAL** | 0.587 | 0 | 5 | 1.35 |
| 2 | cmr_002 | SNAP vehicle exclusion | RELEVANT | 0.513 | 1 | 2 | 1.35 |
| 3 | cmr_003 | SNAP shelter deduction | **PARTIAL** | 0.568 | 2 | 5 | 1.80 |
| 4 | cmr_004 | SNAP self-employment income | RELEVANT | 0.620 | 4 | 5 | 2.45 |
| 5 | cmr_005 | SNAP excluded income | RELEVANT | 0.543 | 3 | 5 | 2.20 |
| 6 | cmr_006 | SNAP ABAWD exemptions | RELEVANT | 0.604 | 1 | 5 | 1.85 |
| 7 | cmr_007 | SNAP application processing time | **PARTIAL** | 0.500 | 1 | 5 | 1.70 |
| 8 | cmr_008 | SNAP application filing | RELEVANT | 0.602 | 3 | 5 | 2.30 |
| 9 | cmr_009 | SNAP noncitizen eligibility | RELEVANT | 0.564 | 5 | 5 | 2.70 |
| 10 | cmr_010 | SNAP restoration | **PARTIAL** | 0.519 | 1 | 5 | 1.60 |
| 11 | cmr_011 | SNAP recertification | RELEVANT | 0.594 | 1 | 5 | 1.85 |
| 12 | cmr_012 | SNAP categorical eligibility | RELEVANT | 0.528 | 2 | 5 | 1.95 |
| 13 | cmr_013 | SSP eligibility | RELEVANT | 0.542 | 2 | 5 | 2.10 |
| 14 | cmr_014 | SSP payment standards | RELEVANT | 0.511 | 1 | 5 | 1.85 |
| 15 | cmr_015 | fair hearings general | **PARTIAL** | 0.469 | 1 | 5 | 1.70 |
| 16 | cmr_016 | hearing time limits | **PARTIAL** | 0.523 | 2 | 5 | 1.95 |
| 17 | cmr_017 | IPV definition | RELEVANT | 0.508 | 1 | 5 | 1.85 |
| 18 | cmr_018 | SNAP IPV penalties | RELEVANT | 0.582 | 2 | 5 | 2.20 |
| 19 | cmr_019 | TAFDC vs EAEDC | **PARTIAL** | 0.502 | 0 | 5 | 1.35 |
| 20 | cmr_020 | TAFDC 24-month limit | RELEVANT | 0.502 | 2 | 5 | 2.10 |
| 21 | cmr_021 | TAFDC work program | RELEVANT | 0.556 | 5 | 5 | 2.70 |
| 22 | cmr_022 | TAFDC asset limit | **PARTIAL** | 0.503 | 0 | 4 | 1.20 |
| 23 | cmr_023 | EAEDC disability | **PARTIAL** | 0.489 | 1 | 5 | 1.45 |
| 24 | cmr_024 | ESP overview | RELEVANT | 0.478 | 1 | 5 | 1.85 |
| 25 | cmr_025 | FEP overview | RELEVANT | 0.567 | 2 | 5 | 2.20 |
| 26 | cmr_026 | TAFDC MassHealth | **PARTIAL** | 0.552 | 0 | 4 | 1.20 |
| 27 | cmr_027 | TAFDC overpayments | RELEVANT | 0.471 | 1 | 5 | 1.85 |
| 28 | cmr_028 | identity verification | RELEVANT | 0.473 | 2 | 5 | 2.20 |
| 29 | cmr_029 | SNAP household composition | RELEVANT | 0.569 | 4 | 5 | 2.55 |
| 30 | cmr_030 | SNAP benefit calculation | **PARTIAL** | 0.561 | 0 | 5 | 1.35 |
| 31 | cmr_031 | section number lookup | **PARTIAL** | 0.357 | 1 | 2 | 0.70 |
| 32 | cmr_032 | ADH acronym | **PARTIAL** | 0.376 | 0 | 5 | 1.35 |
| 33 | cmr_033 | EPSDT acronym | RELEVANT | 0.504 | 1 | 1 | 1.00 |
| 34 | cmr_034 | PA household defined term | **PARTIAL** | 0.556 | 1 | 5 | 1.70 |
| 35 | cmr_035 | EDP defined term | RELEVANT | 0.616 | 1 | 5 | 1.85 |
| 36 | cmr_036 | SNAP allowed uses | RELEVANT | 0.580 | 1 | 5 | 1.85 |
| 37 | cmr_037 | TCAP application interview | **PARTIAL** | 0.492 | 0 | 5 | 1.35 |

---

## Per-Question Detail

Top 5 results per question with judge verdicts and full chunk text. Use this to spot-check whether the judge's rating makes sense.

### cmr_001 — SNAP asset limit (rank-1: PARTIAL)

**Question**: How much can a SNAP household have in bank accounts  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.110`  
**Notes**: 363.110 Asset Eligibility Limits  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.587)

- **Chunk ID**: `cmr_sec_363_130__005`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 6 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: The chunk discusses verification procedures for bank accounts but does not specify the actual asset limit amount that SNAP households can have.

```
106 CMR 363 > FINANCIAL > 363.130 Countable Assets > (B) Bank Accounts.

(4) Verification of Bank Account Balances. Bank account balances must be verified at application, recertification, and at times of reported change. The amount shall be verified by bank books, bank statements or online printouts that show the bank balance within 45 days of the date of the application, recertification, or reported change. If at recertification the household member declares a balance of $25 or less in an account, other than a checking account, verification shall not be required if the balance was $25 or less at the last eligibility determination and the account balance, in combination with other countable assets, is not over the asset limit. The household's declaration shall be recorded in the case record.
```

#### Rank 2 — PARTIAL (sim 0.556)

- **Chunk ID**: `cmr_sec_363_110__000`
- **Section**: `363.110` — Asset Eligibility Limits
- **Program**: SNAP
- **Judge reason**: The chunk addresses asset limits for SNAP households but does not specify the actual dollar amounts, instead referring users to www.mass.gov for the specific limits set by USDA.

```
106 CMR 363 > FINANCIAL > 363.110 Asset Eligibility Limits

The asset eligibility limits in 106 CMR 363.110 do not apply to categorically eligible households as defined in 106 CMR 365.180: Categorically Eligible Assistance Units. These asset eligibility limits, however, shall be applied to any household with a member disqualified from receiving SNAP benefits due to failing to comply with the SNAP Work Program; or for any of the reasons listed in 106 CMR 367.800: Disqualification Penalties. Non-SSI elder and/or disabled households with income above the Categorical Eligibility Gross Income standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards shall also be subject to asset limits. The total value of countable assets owned by a household subject to asset limits shall not exceed the following:
(A) The amount authorized by the United States Department of Agriculture and posted on www.mass.gov for any household that includes at least one member who is aged 60 or over and/or disabled as described and verified in accordance with 106 CMR 361.210 (A) and (B).
(B) The amount authorized by the United States Department of Agriculture and posted on www.mass.gov for all other households. The household shall report all assets owned or anticipated to be received within the certification period. The equity value of all countable assets will be used to determine if the household is within asset eligibility limits. (Mass. Register #1522, 5/24/2024)
```

#### Rank 3 — PARTIAL (sim 0.554)

- **Chunk ID**: `cmr_sec_363_130__002`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 3 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: Defines what bank accounts are and how they're counted as assets, but does not specify the actual dollar limit for SNAP household bank account holdings.

```
106 CMR 363 > FINANCIAL > 363.130 Countable Assets > (B) Bank Accounts.

(B) Bank Accounts.
(1) Definition. Bank accounts may be in the form of savings, checking, trust accounts, term certificates, or other types of accounts held at banks, savings or loan institutions. Funds in a bank account are considered available when a member of the household has both ownership of, and access to, the balance of funds in the account.
(2) Joint Bank Accounts. If a household member is a co-holder of a joint bank account, the entire amount on deposit shall be considered available as an asset unless the household demonstrates otherwise. Crowdfunding accounts (e.g., GoFundMe and Kickstarter) shall also be considered liquid resources if funds are accessible to the household. The actual value of funds accessible to an accountholder shall be counted as a liquid resource. A household member who states that he or she is not the owner, or is only partial owner, of the funds must verify ownership of the funds. A household member who states that he or she has no access, or only partial access to the funds must verify lack of access.
```

#### Rank 4 — PARTIAL (sim 0.526)

- **Chunk ID**: `cmr_sec_363_150__002`
- **Section**: `363.150` — Transfer of Assets
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (B) Transfers Not Resulting in Disqualification.
- **Judge reason**: The chunk discusses asset transfers and disqualification but does not specify the actual allowable limit amount for countable household assets in SNAP.

```
106 CMR 363 > FINANCIAL > 363.150 Transfer of Assets > (B) Transfers Not Resulting in Disqualification.

(B) Transfers Not Resulting in Disqualification. Eligibility for SNAP shall not be affected by a transfer of assets in the following cases:
(1) the asset would not otherwise affect eligibility because the total countable household assets was less than the allowable limits at the time of the transfer;
(2) the assets are sold or traded at or near fair market value;
(3) the assets are transferred between members of the same household; and
(4) the assets are transferred for reasons other than qualifying or attempting to qualify for SNAP benefits, for example, a parent placing funds in an educational trust fund.
```

#### Rank 5 — PARTIAL (sim 0.523)

- **Chunk ID**: `cmr_sec_365_810__000`
- **Section**: `365.810` — Expedited Service Households
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Hierarchy**: (A) $150 Gross Income Household.
- **Judge reason**: Mentions liquid asset limits ($100) for a specific household category but doesn't provide the general SNAP asset limit for all households.

```
106 CMR 365 > SPECIAL > 365.810 Expedited Service Households

To qualify for expedited service, an applicant household need only meet one of the following circumstances.
(A) $150 Gross Income Household. A $150 gross income household is a household whose gross income for the month of application does not exceed $150 and whose liquid assets, as described in 106 CMR 363.100: Assets, do not exceed $100.
```


### cmr_002 — SNAP vehicle exclusion (rank-1: RELEVANT)

**Question**: What vehicles are exempt from the SNAP asset test  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.140` — judge picked rank-1 RELEVANT chunk in section `363.140` (section-author intuition agrees)  
**Notes**: 363.140 Noncountable Assets  
**Scores**: Relevant@5 = 1, Useful@5 = 2, rank-weighted = 1.35  

#### Rank 1 — RELEVANT (sim 0.513)

- **Chunk ID**: `cmr_sec_363_140__002`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 3 / 14
- **Program**: SNAP
- **Hierarchy**: (C) Education Savings Accounts.
- **Judge reason**: The chunk directly states that vehicles are noncountable assets under the SNAP asset test, explicitly answering the user's question about vehicle exemptions.

```
106 CMR 363 > FINANCIAL > 363.140 Noncountable Assets > (C) Education Savings Accounts.

(C) Education Savings Accounts. Section 529 qualified tuition programs, and Coverdell education savings accounts are noncountable assets.
(D) Vehicles. Vehicles, whether licensed or unlicensed, are noncountable. Vehicles include, but are not limited to, cars, trucks, boats and tractors.
```

#### Rank 2 — PARTIAL (sim 0.462)

- **Chunk ID**: `cmr_sec_363_140__012`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 13 / 14
- **Program**: SNAP
- **Hierarchy**: (H) Other Noncountable Assets. The following assets are noncountable:
- **Judge reason**: The chunk addresses noncountable assets for SNAP but focuses on household member assets and specific account types rather than vehicle exemptions specifically.

```
106 CMR 363 > FINANCIAL > 363.140 Noncountable Assets > (H) Other Noncountable Assets. The following assets are noncountable:

(7) Assets of Certain Household Members. Assets of certain household members are noncountable as follows:
(a) The assets of SSI and/or TAFDC household members shall be considered exempt for SNAP purposes if the household members receive benefits under one or more of the following titles of the Social Security Act: Title XVI (SSI); Titles I, X, or XIV for the aged, blind, or disabled; or Title IV-A (TANF); and
(b) The assets of individuals for whom state and/or federal foster care maintenance payments are made, including assets of the child of the foster child when the foster care maintenance payment includes the child of the foster child;
(8) TAFDC/FEP - Individual Asset Account. Funds maintained in an Individual Asset Account (IAA) as part of the TAFDC Full Employment Program (FEP) shall be excluded until receipt of such funds upon termination of FEP employment. Funds received from the IAA upon termination of FEP employment shall be countable; and
(9) Reimbursements. Any portion of a Workers' Compensation, property damage, personal injury, Compensation to Victims of Violent Crimes Act, death settlement or award, except for compensation for lost wages, that is received as a reimbursement for specified items and used to pay for such items.
```

#### Rank 3 — IRRELEVANT (sim 0.447)

- **Chunk ID**: `cmr_sec_363_150__000`
- **Section**: `363.150` — Transfer of Assets
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: This chunk discusses transfer of asset rules and categorical eligibility, not vehicle exemptions from the SNAP asset test.

```
106 CMR 363 > FINANCIAL > 363.150 Transfer of Assets

The transfer of asset rules do not apply to categorically eligible households as defined in 106 CMR 365.180: Categorically Eligible Assistance Units. The transfer of asset rules will be applied to any household which contains a member disqualified from receiving SNAP benefits. Non-SSI elder and/or disabled households with income above the Categorical Eligibility Gross Income standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards will also be subject to transfer of asset rules.
```

#### Rank 4 — IRRELEVANT (sim 0.446)

- **Chunk ID**: `cmr_sec_363_140__010`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 11 / 14
- **Program**: SNAP
- **Hierarchy**: (H) Other Noncountable Assets. The following assets are noncountable:
- **Judge reason**: The chunk discusses noncountable assets including educational loans and various exempt assets, but does not address vehicle exemptions from the SNAP asset test.

```
106 CMR 363 > FINANCIAL > 363.140 Noncountable Assets > (H) Other Noncountable Assets. The following assets are noncountable:

(5) Educational Loans, Grants, and Scholarships Any financial assistance paid to a student such as a financial aid package, grant, loan or scholarship for the purposes of obtaining a degree or certificate from an institution of higher education is a noncountable asset. Permissible purposes may include, without limitation, room and board, tuition and fees, and other ancillary costs associated with the costs of obtaining a degree or certificate at an institution of higher education.
(6) Assets Exempt by Law. Certain assets are noncountable for SNAP purposes by a specific provision in federal law, including, but not limited to:
(a) Coupons under a WIC Demonstration Project that can be exchanged for food at farmers' markets;
(b) Highway Relocation assistance payments, Urban Renewal Assistance payments, disaster relief payments used for relocation, and payments from private agencies used for relocation;
(c) State and federal earned income credits (EIC), whether received as an advance payment or as part or all of an income tax refund, in the month of receipt and the following month;
(d) Payments or allowances made to or on behalf of a household for energy assistance under any federal, state, or local law. These payments or allowances must be clearly identified as energy assistance by the legislative body authorizing the program or providing the funds;
(e) Nonliquid assets with a lien in place as a result of taking out a business loan if the
```

#### Rank 5 — IRRELEVANT (sim 0.437)

- **Chunk ID**: `cmr_sec_363_150__002`
- **Section**: `363.150` — Transfer of Assets
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (B) Transfers Not Resulting in Disqualification.
- **Judge reason**: This chunk addresses asset transfers and disqualification rules, not vehicle exemptions from the SNAP asset test.

```
106 CMR 363 > FINANCIAL > 363.150 Transfer of Assets > (B) Transfers Not Resulting in Disqualification.

(B) Transfers Not Resulting in Disqualification. Eligibility for SNAP shall not be affected by a transfer of assets in the following cases:
(1) the asset would not otherwise affect eligibility because the total countable household assets was less than the allowable limits at the time of the transfer;
(2) the assets are sold or traded at or near fair market value;
(3) the assets are transferred between members of the same household; and
(4) the assets are transferred for reasons other than qualifying or attempting to qualify for SNAP benefits, for example, a parent placing funds in an educational trust fund.
```


### cmr_003 — SNAP shelter deduction (rank-1: PARTIAL)

**Question**: What is the SNAP shelter deduction  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364.400`  
**Notes**: 364.400 Shelter/Excess Shelter Deduction  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.80  

#### Rank 1 — PARTIAL (sim 0.568)

- **Chunk ID**: `cmr_sec_365_520__003`
- **Section**: `365.520` — Disqualified Nonhousehold Members
- **Chunk position**: 4 / 6
- **Program**: SNAP
- **Hierarchy**: (B) Nonhousehold Members Disqualified from Federal Snap Benefits Due to Ineli...
- **Judge reason**: The chunk mentions the shelter expense deduction as one of several deductions but does not explain what the SNAP shelter deduction actually is or how it is calculated.

```
106 CMR 365 > SPECIAL > 365.520 Disqualified Nonhousehold Members > (B) Nonhousehold Members Disqualified from Federal Snap Benefits Due to Ineli...

(3) Deductible Expenses.
(a) For purposes of calculating the maximum SNAP benefit the household would be entitled to if all members were SNAP-eligible, all deductions shall be applied to the household in accordance with 106 CMR 364.600(C)(1): Step One.
(b) For purposes of calculating the SNAP benefits of the SNAP-eligible household members:
1. The standard deduction shall be applied to the SNAP-eligible household;
2. The homeless deduction shall be applied to the SNAP-eligible household if the SNAP-eligible household meets the requirements at 106 CMR 364.400(F): Homeless Shelter/Utility Deduction;
3. The shelter expense deduction shall be applied to the SNAP-eligible household if the SNAP-eligible household has income;
4. The earned income deduction shall be applied as follows: a. The earned income deduction of a SNAP-eligible member with earnings shall be applied to the SNAP-eligible household; and b. The earned income deduction of a nonhousehold member with earnings who is a legal noncitizen ineligible for federal SNAP benefits shall not be applied to the SNAP-eligible household;
5. A deduction for child support paid shall be applied as follows: a. A deduction for child support paid by an SNAP-eligible member shall be applied to the SNAP-eligible household.; and b. A deduction for child support paid by a nonhousehold member who is a legal noncitizen ineligible for federal SNAP benefits shall not be applied to the SNAP-eligible household;
```

#### Rank 2 — RELEVANT (sim 0.562)

- **Chunk ID**: `cmr_sec_364_400__009`
- **Section**: `364.400` — Determining Deductions
- **Chunk position**: 10 / 13
- **Program**: SNAP
- **Hierarchy**: (G) Shelter Deduction.
- **Judge reason**: The chunk directly defines the SNAP shelter deduction, explaining what it covers, how it's calculated, and what expenses qualify as shelter deductions under Massachusetts DTA policy.

```
106 CMR 364 > DETERMINING > 364.400 Determining Deductions > (G) Shelter Deduction.

(G) Shelter Deduction. A deduction is allowed for monthly shelter expenses and utility costs in excess of 50% of the household's income after all the above deductions have been allowed. This shelter deduction amount is posted at www.mass.gov/dta. Paper copies are available upon request. This limit on the shelter deduction amount does not apply if the household contains a member who is elderly or disabled in accordance with 106 CMR 361.210: Elderly or Disabled Individuals.
(1) Shelter Expenses.
(a) Continuing charges for the shelter occupied by the household, including rent and mortgage payments, or other continuing charges leading to the ownership of shelter, such as loan repayments for the purchase of a mobile home, including interest on such payments, or condominium fees; NON-TEXT PAGE
(b) Property taxes, state and local assessments, and insurance on the structure itself, but not the separate expense of insuring furniture or personal belongings;
(c) Shelter expenses as described in 106 CMR 364.400(G)(1)(a) and (b) for a home not actually occupied by the household because of employment or training away from home, illness, or abandonment of the home due to natural disaster or casualty loss. Shelter expenses for a vacated home shall be included in the shelter deduction if the household intends to return to the home, the current occupants of the home, if any, are not claiming a shelter deduction for SNAP purposes, and the home is not leased or rented
```

#### Rank 3 — PARTIAL (sim 0.558)

- **Chunk ID**: `cmr_sec_365_630__001`
- **Section**: `365.630` — Certification of Residents of Group Living Arrangements and Treatment Centers
- **Chunk position**: 2 / 4
- **Program**: SNAP
- **Hierarchy**: (B) Determining Shelter Costs for Residents of Group Living Arrangements, Dru...
- **Judge reason**: Addresses how shelter costs are calculated for a specific group (residents of group living arrangements), but does not explain the general SNAP shelter deduction or how it applies to typical SNAP households.

```
106 CMR 365 > SPECIAL > 365.630 Certification of Residents of Group Living Arrangements and Treatment Centers > (B) Determining Shelter Costs for Residents of Group Living Arrangements, Dru...

(B) Determining Shelter Costs for Residents of Group Living Arrangements, Drug or Alcohol Treatment Centers. When residents of group living arrangements or drug and alcohol treatment centers make a combined payment for meals and lodging (shelter), the cost of shelter shall be equal to the difference between the amount of the room and board payment and the maximum SNAP benefit allotment for the appropriate SNAP household size.
```

#### Rank 4 — PARTIAL (sim 0.554)

- **Chunk ID**: `cmr_sec_364_400__012`
- **Section**: `364.400` — Determining Deductions
- **Chunk position**: 13 / 13
- **Program**: SNAP
- **Hierarchy**: (G) Shelter Deduction.
- **Judge reason**: The chunk discusses utility allowances and standard utility allowances which are components of shelter deductions, but does not explain what the shelter deduction itself is or how it is calculated overall.

```
106 CMR 364 > DETERMINING > 364.400 Determining Deductions > (G) Shelter Deduction.

sewerage; garbage and trash collection; the basic fee for one telephone and tax; and the initial utility installation fee, if applicable; or
(c) Telephone Standard Utility Allowance. The Telephone Standard Utility Allowance applies to a household that incurs a telephone cost but none of the following costs separate from its rent or mortgage: heating or cooling; cooking fuel; electricity; water; sewerage; and garbage and trash collection. The telephone SUA includes the basic fee for one telephone and tax, and the initial utility installation fee, if applicable.
(3) Treatment of the Standard Utility Allowance in Shared Living Situations. If a household lives with another SNAP household or households, each household that contributes to utility costs shall be entitled to the full applicable SUA.
(4) Standard Utility Allowance for Unoccupied Homes. Households that also incur utility expenses for a home that is unoccupied because of employment or training away from home, illness or abandonment caused by a natural disaster or casualty loss, will only be allowed one standard utility allowance, whichever is highest.
```

#### Rank 5 — RELEVANT (sim 0.544)

- **Chunk ID**: `cmr_sec_364_500__007`
- **Section**: `364.500` — Determining Net Income
- **Chunk position**: 8 / 8
- **Program**: SNAP
- **Hierarchy**: (K) Shelter Deduction.
- **Judge reason**: The chunk directly defines and explains the SNAP shelter deduction, including how it's calculated for different household types and where to find the specific deduction amounts.

```
106 CMR 364 > DETERMINING > 364.500 Determining Net Income > (K) Shelter Deduction.

(K) Shelter Deduction. Subtract the full amount of the excess shelter expense if the household contains an elderly or disabled member who meets one of the requirements of 106 CMR 361.210: Elderly or Disabled Individuals. For all other households, subtract the excess shelter expense up to the maximum deduction amount. This shelter deduction amount is posted at www.mass.gov/dta.
```


### cmr_004 — SNAP self-employment income (rank-1: RELEVANT)

**Question**: How is self-employment income calculated for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.220` — judge picked rank-1 RELEVANT chunk in section `365.970` (section-author intuition disagrees with judge)  
**Notes**: 363.220 Earned Income  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.620)

- **Chunk ID**: `cmr_sec_365_970__002`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Hierarchy**: (C) Determining Monthly SNAP Income. To determine the monthly SNAP income for
- **Judge reason**: Directly explains how monthly SNAP income is calculated for self-employed households, including the treatment of net self-employment income and farm losses.

```
106 CMR 365 > SPECIAL > 365.970 Determining Eligibility and Benefit Level for the Self-employed > (C) Determining Monthly SNAP Income. To determine the monthly SNAP income for

(C) Determining Monthly SNAP Income. To determine the monthly SNAP income for households with income from self-employment enterprises, the monthly net self-employment income is added to any other earned income, or in the case of unearned rental income to other unearned income, received by the household. If the cost of producing self-employment income of farmers exceeds the income derived from self-employment, such losses shall be offset against any other countable income in the household, provided that the farmer has received or is anticipating receiving annual gross proceeds of $1000 or more from the farming enterprise; and provided that whatever base is used to determine any net income from self-employment farm operations, such as the previous year's tax return or current income, the same base is used in determining any net loss. Losses shall be prorated over the year in a manner comparable to that used to prorate farm self-employment income. REGULATORY AUTHORITY 106 CMR 364.000: M.G.L. c. 18, § 10. (PAGES 811 THROUGH 814 ARE RESERVED FOR FUTURE USE.)
```

#### Rank 2 — RELEVANT (sim 0.573)

- **Chunk ID**: `cmr_sec_363_220__000`
- **Section**: `363.220` — Countable Income
- **Chunk position**: 1 / 7
- **Program**: SNAP
- **Hierarchy**: (A) Earned Income.
- **Judge reason**: Directly explains how self-employment income is calculated for SNAP, including gross income, capital goods, and business expenses.

```
106 CMR 363 > FINANCIAL > 363.220 Countable Income

For SNAP purposes, countable income must be categorized as either earned or unearned.
(A) Earned Income.
(1) Wages. All wages and salaries paid to an employee are counted as earned income.
(2) Self-employment. The total gross income from a self-employment enterprise, including the total gain from the sale of any capital goods or equipment related to the business, excluding the cost of doing business, is counted as earned income. Payments from roomers and boarders are classified as earned self-employment income. Income from rental property shall be considered earned self-employment income only if a household member actively engages in the management of the property an average of at least 20 hours per week.
```

#### Rank 3 — PARTIAL (sim 0.551)

- **Chunk ID**: `cmr_sec_364_500__001`
- **Section**: `364.500` — Determining Net Income
- **Chunk position**: 2 / 8
- **Program**: SNAP
- **Hierarchy**: (A) Total Gross Earned Income.
- **Judge reason**: Mentions self-employment income in the context of gross earned income calculation but doesn't explain the specific methodology for calculating self-employment income itself.

```
106 CMR 364 > DETERMINING > 364.500 Determining Net Income > (A) Total Gross Earned Income.

(A) Total Gross Earned Income. To determine gross monthly earned income, add the gross monthly income earned by all household members (including self-employment income) less income exclusions. Net losses from a self-employed farmer shall be offset in accordance with 106 CMR 365.970(C): Determining Monthly SNAP Income.
```

#### Rank 4 — RELEVANT (sim 0.536)

- **Chunk ID**: `cmr_sec_365_970__000`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Averaged Income.
- **Judge reason**: The chunk directly explains the method for calculating self-employment income for SNAP by describing the averaging process and what to include/exclude.

```
106 CMR 365 > SPECIAL > 365.970 Determining Eligibility and Benefit Level for the Self-employed

(A) Averaged Income. For the period of time over which self-employment is determined, add all gross self-employment income (including capital gains), exclude the cost of producing the self-employment income, and divide the self-employment income by the number of months over which the income will be averaged.
```

#### Rank 5 — RELEVANT (sim 0.535)

- **Chunk ID**: `cmr_sec_365_970__001`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (B) Anticipated Income.
- **Judge reason**: Directly explains how self-employment income is calculated for SNAP by detailing the anticipated income method, including capital gains, monthly allowable costs, and depreciation treatment.

```
106 CMR 365 > SPECIAL > 365.970 Determining Eligibility and Benefit Level for the Self-employed > (B) Anticipated Income.

(B) Anticipated Income. For those households whose self-employment income is not averaged but is instead calculated on an anticipated basis, add any capital gains the household anticipates it will receive in the next 12 months, starting with the date the application is filed, and divide this amount by 12. This amount shall be used in successive certification periods during the next 12 months except that a new average monthly amount shall be calculated for this 12 month period if the anticipated amount of capital gains changes. Then add the anticipated monthly amount of capital gains to the anticipated monthly self-employment income, and subtract the cost of producing self-employment income. Except for depreciation, the cost of producing the self-employment income shall be calculated by anticipating the monthly allowable costs of producing the self-employment income. Capital gains is the gain the household makes from the sale of a capital asset, such as real property used to carry out the household's business enterprise, in excess of the value of the property or cost of the property.
```


### cmr_005 — SNAP excluded income (rank-1: RELEVANT)

**Question**: What income is excluded from SNAP eligibility determination  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.230` — judge picked rank-1 RELEVANT chunk in section `363.230` (section-author intuition agrees)  
**Notes**: 363.230 Noncountable Income  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.543)

- **Chunk ID**: `cmr_sec_363_230__011`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 12 / 19
- **Program**: SNAP
- **Hierarchy**: (J) The Cost of Producing Self-employment Income.
- **Judge reason**: The chunk directly addresses excluded income for SNAP eligibility by listing specific types of income that are excluded from income determination, including self-employment costs and federally-excluded income categories.

```
106 CMR 363 > FINANCIAL > 363.230 Excluded Income > (J) The Cost of Producing Self-employment Income.

(J) The Cost of Producing Self-employment Income. The cost of producing self-employment income is excluded from income in accordance with 106 CMR 365.900 through 365.970.
(K) Income Excluded by Law. Certain income is excluded for SNAP purposes by specific provisions in federal law. The following listing of excludable income includes, but is not limited to:
(1) HighwayRelocation assistance payments, Urban Renewal Assistance payments, disaster relief payments used for relocation, and payments from private agencies used for relocation;
(2) The tax-exempt portions of payments made under the Alaska Native Claims Settlement Act;
(3) Funds distributed to or held in trust for members of any Indian tribe pursuant to a judgment of the Indian Claims Settlements or the Secretary of the Interior;
(4) Payments to Native Americans under Public Laws 92-254, 93-134, 94-114, 94-540, 96-420, 97- 458, 98-64 and 102-71, including interest income from these payments;
(5) Payments or reimbursements given to, volunteers serving as foster grandparents, senior health aides, senior companions, or serving in the Service Corps of Retired Executives, in VISTA, or in any other program established under the Domestic Service Act of 1973;
```

#### Rank 2 — PARTIAL (sim 0.526)

- **Chunk ID**: `cmr_sec_363_200__000`
- **Section**: `363.200` — Income
- **Program**: SNAP
- **Judge reason**: The chunk states that all income is counted except when specifically excluded, but does not list the actual exclusions that answer the user's question.

```
106 CMR 363 > FINANCIAL > 363.200 Income

All income to the household, from whatever source, that is anticipated to be received during the period of certification shall be counted when determining a household's eligibility and benefit level except when specificallyexcluded below. Categoricallyeligible households, in accordance with 106 CMR 365.180: Categorically Eligible Assistance Units, do not need to meet gross or net income eligibility standards.
```

#### Rank 3 — RELEVANT (sim 0.526)

- **Chunk ID**: `cmr_sec_363_230__000`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 1 / 19
- **Program**: SNAP
- **Hierarchy**: (A) In-kind Income and Cash Contributions.
- **Judge reason**: The chunk directly addresses what income is excluded from SNAP eligibility determination by listing specific types of excluded income with examples.

```
106 CMR 363 > FINANCIAL > 363.230 Excluded Income

The following kinds of income will be excluded when determining a household's eligibility and benefit level.
(A) In-kind Income and Cash Contributions. Any gain or benefit not in the form of money and provided directly to the household is excluded from income. For example, meals, clothing, public housing, or produce from a garden would be excluded from income. Any cash contributions from a non-legally responsible person (i.e., someone without a court order or other binding agreement) that are restricted for a specific purpose and provide for a portion of any rent or mortgage, fuel, utilities and/or food or other needs are excluded from income.
```

#### Rank 4 — PARTIAL (sim 0.521)

- **Chunk ID**: `cmr_sec_365_120__004`
- **Section**: `365.120` — Determining Eligibility and Benefit Level
- **Chunk position**: 5 / 6
- **Program**: SNAP
- **Hierarchy**: (B) Asset Standards for PA Households.
- **Judge reason**: The chunk discusses income exclusions for SNAP but references another regulation (106 CMR 363.230) where the actual excluded income list is located, rather than providing the specific exclusions themselves.

```
106 CMR 365 > SPECIAL > 365.120 Determining Eligibility and Benefit Level > (B) Asset Standards for PA Households.

(B) Asset Standards for PA Households. Asset standards for PA households shall be determined as specified in 106 CMR 363.110: Asset Eligibility Limits.
(C) Income Standards For PA Households.
(1) Countable Income. All income received by the PA household, including the cash grant, special allowances and all other income (unless excluded in accordance with 106 CMR 363.230: Excluded Income) shall be counted in determining the household's eligibility for SNAP benefits.
(2) Income Exclusions and Deductions. PA households will receive only the income exclusions and deductions provided in SNAP policy. The income exclusions and deductions allowed under cash assistance programs for the purposes of grant calculation shall not be allowed in determining income for SNAP purposes.
(3) Special Allowances, Retroactive Lump Sum Payments and Protective Payments.
(a) Special Allowances. Special allowances, except for one-time payments (e.g., the clothing allowance for TAFDC children) or vendor payments, are treated as countable income. This income may be averaged over the certification period or on a variable basis of issuance to cover the period when the allowance is received.
(b) Retroactive Lump Sum PA Payments. Retroactive lump sum payments are excluded as income and counted as an asset in the month received. If a PA client's first payment is delayed beyond the first month of eligibility, the retroactive portion of that check is
```

#### Rank 5 — RELEVANT (sim 0.519)

- **Chunk ID**: `cmr_sec_363_220__006`
- **Section**: `363.220` — Countable Income
- **Chunk position**: 7 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Garnishments, Managed Income and Certain Vendor Payments.
- **Judge reason**: The chunk directly addresses income exclusions for SNAP eligibility by listing specific payments that are not considered income when determining household eligibility and benefit levels.

```
106 CMR 363 > FINANCIAL > 363.220 Countable Income > (C) Garnishments, Managed Income and Certain Vendor Payments.

(c) The Department must adjust SNAP benefits as a result of changes in household circumstances not related to the penalty imposed by another applicable public assistance program.
(6) Payments That Are Not Considered Income. The following payments are not income for SNAP purposes and should be disregarded when determining a household's eligibility and benefit level:
(a) Child support payments made to TAFDC recipients that must be assigned to the Department by the recipient under Title IV-D of the Social Security Act (Child Support Enforcement) to maintain TAFDC eligibility; and
(b) Monies withheld from a public assistance grant or repaid by the recipient to any income source or monies received from any income source if the following conditions apply:
1. the monies are voluntarily or involuntarily withheld from or returned to the income source to repay a prior overpayment that was caused by any reason other than the household intentionallyfailing to complywith the requirements of another federal or state needs-based welfare program, such as TAFDC, EAEDC or SSI; and
2. the overpayment is not considered excluded income as provided in 106 CMR 363.230.
```


### cmr_006 — SNAP ABAWD exemptions (rank-1: RELEVANT)

**Question**: What are the ABAWD work requirement exemptions  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `362.320` — judge picked rank-1 RELEVANT chunk in section `362.320` (section-author intuition agrees)  
**Notes**: 362.320 ABAWD; or possibly 365.x for SNAP work in PA households  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.604)

- **Chunk ID**: `cmr_sec_362_320__002`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Hierarchy**: (B) Exemptions.
- **Judge reason**: The chunk directly lists the ABAWD work requirement exemptions including age, pregnancy, living with children, and waived areas.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (B) Exemptions.

(B) Exemptions. Able-bodied Adults without Dependents are exempt from the ABAWD work program requirements if they meet the exemption criteria of 106 CMR 362.310(C). The individuals listed below are also exempt from the ABAWD work program requirements:
(1) Age. Persons younger than 18 years old or 50 years of age or older;
(2) Pregnant Women. A pregnant woman at any stage of pregnancy;
(3) Adults Living with Children Younger than 18 Years Old. Persons residing in a household where a household member is younger than 18 years old, even if the household member who is younger than 18 years old is not eligible for SNAP benefits; and
(4) Resident of a Waived Area. A person who otherwise would be required to participate in the ABAWD work program is exempt if living in an area of the state exempted by the United States Department of Agriculture.
```

#### Rank 2 — PARTIAL (sim 0.528)

- **Chunk ID**: `cmr_sec_362_320__008`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 9 / 9
- **Program**: SNAP
- **Hierarchy**: (H) Additional Three Month Eligibility.
- **Judge reason**: Describes one specific exemption/exception to ABAWD work requirements but doesn't comprehensively address all exemptions available.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (H) Additional Three Month Eligibility.

(H) Additional Three Month Eligibility. A client who has regained eligibility under 106 CMR 362.320(F) and is no longer fufilling the ABAWD work program requirement may continue to receive SNAP benefits for an additional three months without complying with 106 CMR 362.320(A). This exception is limited to a single period of three consecutive months during the balance of the three-year period.
```

#### Rank 3 — PARTIAL (sim 0.518)

- **Chunk ID**: `cmr_sec_362_320__007`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 8 / 9
- **Program**: SNAP
- **Hierarchy**: (G) Maintaining Eligibility.
- **Judge reason**: The chunk mentions exemptions in subsection (B) but does not provide the actual list of exemptions themselves, only referencing where they can be found.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (G) Maintaining Eligibility.

(G) Maintaining Eligibility. Clients who regain eligibility under 106 CMR 362.320(F) shall remain eligible for the balance of the three-year period as long as they continue to comply with the ABAWD work program requirements by:
(1) Working at a job 20 hours per week averaged monthly;
(2) Working at a community service site for a specified number of hours per month determined by dividing the monthly SNAP allotment by the (higher of the State or Federal) minimum wage;
(3) Participating and complying with the requirements of a qualifying SNAP E&T program for at least 20 hours per week in accordance with 106 CMR 362.320(A)(2);
(4) Working at a job less than 20 hours per week and participating in a qualifying SNAP E&T program for a combined total of 20 hours per week averaged monthly; or
(5) Being exempt from ABAWD work program requirements in accordance with 106 CMR 362.320(B).
```

#### Rank 4 — PARTIAL (sim 0.499)

- **Chunk ID**: `cmr_sec_362_320__000`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 1 / 9
- **Program**: SNAP
- **Hierarchy**: (A) Mandatory Population and Requirements.
- **Judge reason**: The chunk describes ABAWD work requirements and mentions 'nonexempt' members but does not list the actual exemptions from these requirements.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program

(A) Mandatory Population and Requirements. All nonexempt household members between 18 and 49 years of age must:
(1) Register for work at application and every 12 months after initial registration; and
(2) Do one of the following:
(a) Work at a job, or combination of jobs, for 20 hours per week averaged monthly. The work performed may be done in exchange for money, in exchange for goods or services (in-kind work) or may be unpaid work;
(b) Work at a community service site for a specified number of hours per month determined by dividing the monthly SNAP allotment by the (higher of the State or Federal) minimum wage;
(c) Participate in a qualifying SNAP Employment and Training (E&T) program, including basic education, vocational or technical training, or on-the-job training for 20 hours per week. Job search activies associated with E&T components must make up less than half of the required participation hours; or
(d) Work at a job less than 20 hours per week and participate in a qualifying SNAP E&T program component or a WIOA activity for a combined total of 20 hours per week averaged monthly; and
```

#### Rank 5 — PARTIAL (sim 0.496)

- **Chunk ID**: `cmr_sec_362_320__006`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 7 / 9
- **Program**: SNAP
- **Hierarchy**: (F) Regaining Eligibility.
- **Judge reason**: The chunk discusses regaining eligibility after ABAWD non-compliance and mentions becoming exempt, but does not actually list or describe the specific exemptions from ABAWD work requirements.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (F) Regaining Eligibility.

(F) Regaining Eligibility. Clients who are determined ineligible for failure to comply with the ABAWD work program requirements for three months during a three-year period may regain eligibility, if otherwise eligible, after the client:
(1) Works at a job for 80 hours during a 30-day period;
(2) Works at a community service site for a specified number of hours per month determined by dividing the monthly SNAP allotment by the (higher of the State or Federal) minimum wage;
(3) Participates and complies with the requirements of a qualifying SNAP Employment and Training (E&T) program component in accordance with 106 CMR 362.320(A)(2) for 80 hours during a 30-day period;
(4) Works and participates in a qualifying SNAP E&T Program component for a combined total of 80 hours per month during a 30-day period;
(5) Provides proof that he or she will meet the work requirement during a 30 consecutive day period; or
(6) Becomes exempt from ABAWD work program requirements. There is no limit on how many times an individual may regain eligibility by meeting the work requirement.
```


### cmr_007 — SNAP application processing time (rank-1: PARTIAL)

**Question**: How long does DTA have to process a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.080`  
**Notes**: 361.080 Prompt Action; baseline v1 expected 361 broadly, this v2 narrows it  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.70  

#### Rank 1 — PARTIAL (sim 0.500)

- **Chunk ID**: `cmr_sec_365_820__002`
- **Section**: `365.820` — Expedited Service Processing Standards
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Hierarchy**: (C) Unsigned or Incomplete Application.
- **Judge reason**: Addresses processing timelines for incomplete/unsigned applications under expedited service (6 days), but doesn't provide the general standard processing timeframe for regular SNAP applications.

```
106 CMR 365 > SPECIAL > 365.820 Expedited Service Processing Standards > (C) Unsigned or Incomplete Application.

(C) Unsigned or Incomplete Application. If a household submits an application that is either unsigned or incomplete and is subsequently interviewed by telephone, the case manager shall complete the application during the interview. The completed application will be mailed to the household on the same day for signature. For these households, the expedited service processing standard begins on the date a completed and signed application is received rather than the date the application was filed. Households unable to appoint an authorized representative and not required to come into the office as part of the certification process shall have their SNAP benefits issued no later than six days after the receipt of the returned signed application. In some cases the case manager may discover a household is entitled to expedited service that the screening process failed to identify. For these households the expedited service processing standard begins on the date the case manager discovers the household is entitled to expedited service.
```

#### Rank 2 — RELEVANT (sim 0.498)

- **Chunk ID**: `cmr_sec_361_080__000`
- **Section**: `361.080` — Prompt Action
- **Program**: SNAP
- **Judge reason**: Directly states that DTA must process SNAP applications and issue benefits within 30 calendar days of application, which directly answers the user's question about processing timeframes.

```
106 CMR 361 > THE > 361.080 Prompt Action

Eligible households must be given an opportunity to participate in the Supplemental Nutrition Assistance Program (SNAP) no later than 30 calendar days following their date of application. An opportunity to participate consists of the Department's issuing SNAP benefits through the EBT system before the 30-day processing standard expires. Expedited service shall be provided to households in accordance with 106 CMR 365.800: Expedited Service. Benefits must be provided retroactively to the date of application for households that complete the application process within the required time frame and are eligible to receive benefits in the month of application.
```

#### Rank 3 — PARTIAL (sim 0.495)

- **Chunk ID**: `cmr_sec_361_120__000`
- **Section**: `361.120` — Date of Application
- **Program**: SNAP
- **Judge reason**: This chunk defines when an application date is established but does not address the processing timeline or how long DTA takes to process the application.

```
106 CMR 361 > THE > 361.120 Date of Application

For households consisting only of SSI applicants or recipients that apply for SNAP benefits at an SSA office, the household's date of application is the date the signed SNAP application is received by the SSA office. The SSA office shall date stamp each application on the date it is received to document the household's date of application. For all other households, the household's date of application is the date an identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office, except that when an application is not received by 5:00 P.M. on a business day or is received on a weekend or holiday, the application date will be the next business day. The Department shall date stamp each application on the date it is received to document the household's date of application.
```

#### Rank 4 — PARTIAL (sim 0.495)

- **Chunk ID**: `cmr_sec_364_820__001`
- **Section**: `364.820` — Notice of Pending/Denial
- **Chunk position**: 2 / 4
- **Program**: SNAP
- **Hierarchy**: (A) If some action by the worker is needed to complete the application, the n...
- **Judge reason**: Discusses application processing and notice requirements but does not specify the actual timeframe DTA has to process a SNAP application.

```
106 CMR 364 > DETERMINING > 364.820 Notice of Pending/Denial > (A) If some action by the worker is needed to complete the application, the n...

(A) If some action by the worker is needed to complete the application, the notice must inform the household that its application has not been completed and is being processed.
(B) If some action by the household is needed to complete the application, the notice must inform the household that its application has not been completed and is being processed, and what action the household must take to complete the application and that if the action is not taken within 60 days of the date the application was filed, SNAP benefits will be denied with no further notice to the household.
```

#### Rank 5 — PARTIAL (sim 0.494)

- **Chunk ID**: `cmr_sec_366_920__000`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: The chunk discusses SNAP application procedures for SSI households but does not specify the processing timeline that the user is asking about.

```
106 CMR 366 > ADDITIONAL > 366.920 Regular SSI/SNAP Households

In accordance with 7 USC 2020(i) and SSA policy, SSA will take a regular SNAP application for pure SSI households who do not meet the Bay State CAP criteria or who meet Bay State CAP criteria but are subject to a disability determination that will take longer than 30 days to process. The SSA claims representative will also screen for expedited service. SSI applicants/recipients who qualify for expedited service may complete a SNAP application at SSA, the Department or online for regular SNAP benefits. Any obligation attributed to SSA in 106 CMR 366.920 is included for informational purposes only. Appeal rights regarding SSI eligibility or benefit level must be pursued through SSA. The following procedures shall apply for regular SSI/SNAP households served by the Department.
```


### cmr_008 — SNAP application filing (rank-1: RELEVANT)

**Question**: How does someone file a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.100` — judge picked rank-1 RELEVANT chunk in section `361.110` (section-author intuition disagrees with judge)  
**Notes**: 361.100 Filing an Application  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.30  

#### Rank 1 — RELEVANT (sim 0.602)

- **Chunk ID**: `cmr_sec_361_110__000`
- **Section**: `361.110` — Where to File
- **Program**: SNAP
- **Judge reason**: Directly addresses where and how to file a SNAP application, including multiple filing methods (in person, mail, fax, online).

```
106 CMR 361 > THE > 361.110 Where to File

The application must be filed with the Department and may be submitted in person by the applicant, or by an authorized representative, or by mail, fax or the online application. Households consisting only of SSI applicants or recipients may file a SNAP application at an SSA office in accordance with 106 CMR 361.190.
```

#### Rank 2 — RELEVANT (sim 0.586)

- **Chunk ID**: `cmr_sec_361_100__000`
- **Section**: `361.100` — Filing an Application
- **Program**: SNAP
- **Judge reason**: The chunk directly explains how to file a SNAP application, including submission methods (in person, mail, fax, online) and required application components.

```
106 CMR 361 > THE > 361.100 Filing an Application

Households who want to participate in SNAP must submit an identifiable SNAP application. An identifiable SNAP application contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. The application may be submitted in person by the applicant or an authorized representative or by mail, fax or the online application. The application form used by the Department must contain or be accompanied by the following information:
(A) A statement that the information provided by the applicant on the application will be subject to verification by federal, state, and local officials to determine whether such information is factual and that if any material part of that information is incorrect, SNAP benefits may be denied and the applicant may be subject to criminal prosecution for knowingly providing incorrect information;
(B) A description of the civil and criminal provisions and penalties for violations of the Food Stamp Act and its amendments; and
(C) A statement to be signed by one adult household member that certifies, under penalty of perjury, the truth of the information contained in the application, including the information concerning citizenship and noncitizen status of all household members.
```

#### Rank 3 — PARTIAL (sim 0.586)

- **Chunk ID**: `cmr_sec_364_840__004`
- **Section**: `364.840` — Notice of SNAP Termination
- **Chunk position**: 5 / 7
- **Program**: SNAP
- **Hierarchy**: (G) The right to request an application and have it accepted by the Departmen...
- **Judge reason**: Mentions where to file an application and that applications must be signed with legible name/address, but doesn't explain the actual filing process or steps needed to complete a SNAP application.

```
106 CMR 364 > DETERMINING > 364.840 Notice of SNAP Termination > (G) The right to request an application and have it accepted by the Departmen...

(G) The right to request an application and have it accepted by the Department as long as it is signed and contains a legible name and address;
(H) The address of the Department where the application must be filed;
```

#### Rank 4 — PARTIAL (sim 0.585)

- **Chunk ID**: `cmr_sec_361_130__000`
- **Section**: `361.130` — Household Right to Same Day Filing
- **Program**: SNAP
- **Judge reason**: Addresses same-day filing rights and requirements but doesn't explain the actual process or steps for filing a SNAP application.

```
106 CMR 361 > THE > 361.130 Household Right to Same Day Filing

Households shall be advised of their right to same day filing of the application. Each office shall post signs that explain the application processing standards and the household's right to same day filing. In addition, the household shall be informed that it does not have to be interviewed before filing its application and that it may file an incomplete application as long as the form contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. Department staff shall encourage households to file an application the same day the household or its representative contacts the Department in person or by telephone and expresses an interest in obtaining SNAP benefits.
```

#### Rank 5 — RELEVANT (sim 0.574)

- **Chunk ID**: `cmr_sec_366_920__001`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) Filing an Application.
- **Judge reason**: Directly addresses how to file a SNAP application by specifying that assistance is available at SSA or the Department, and explains the application filing process and date determination.

```
106 CMR 366 > ADDITIONAL > 366.920 Regular SSI/SNAP Households > (A) Filing an Application.

(A) Filing an Application. Assistance in completing SNAP applications will be available at SSA or the Department.
(B) Date of Application. If the application is filed at an SSA office, then the date of application shall be the date the identifiable SNAP application is faxed by SSA to the appropriate Transitional Assistance Office (TAO). If an application is filed at a TAO or online, the date of application shall be the date the identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office. (See 106 CMR 361.120: Date of Application.)
```


### cmr_009 — SNAP noncitizen eligibility (rank-1: RELEVANT)

**Question**: Can a noncitizen receive SNAP benefits  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `362.220` — judge picked rank-1 RELEVANT chunk in section `362.220` (section-author intuition agrees)  
**Notes**: 362.220 Noncitizens (CMR 362.200 series covers citizenship)  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.564)

- **Chunk ID**: `cmr_sec_362_220__009`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 10 / 12
- **Program**: SNAP
- **Hierarchy**: (E) Nonimmigrant Noncitizen Status.
- **Judge reason**: Directly addresses noncitizen SNAP eligibility by specifying that nonimmigrant noncitizens in non-qualified statuses are ineligible for SNAP benefits.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (E) Nonimmigrant Noncitizen Status.

(E) Nonimmigrant Noncitizen Status. An individual lawfully residing in the U.S. in a non- qualified status (such as a student or H1-B Visa worker) is ineligible for SNAP benefits. The nonimmigrant shall be ineligible in accordance with 106 CMR 361.230(D) and his or her income and assets are considered available to any remaining household members in accordance with 106 CMR 365.520(A).
```

#### Rank 2 — RELEVANT (sim 0.564)

- **Chunk ID**: `cmr_sec_362_220__004`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 5 / 12
- **Program**: SNAP
- **Hierarchy**: (B) To receive SNAP benefits the qualified noncitizen must meet the condition...
- **Judge reason**: The chunk directly addresses which noncitizens can receive SNAP benefits by specifying eligibility conditions for qualified noncitizens, including those with qualifying work quarters and battered noncitizens.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (B) To receive SNAP benefits the qualified noncitizen must meet the condition...

(g) can be credited with a total of 40 qualifying quarters pursuant to Title II of the Social Security Act as worked by a combination of:
1. the noncitizen;
2. parent(s) of the noncitizen while the noncitizen was younger than 18 years old, including quarters worked before the noncitizen was born or adopted; and/or
3. the spouse of the noncitizen during their marriage if the noncitizen is still married to the spouse or is widowed; or No quarter may be claimed after December 31, 1996 if benefits from a federal means-tested program, defined by 106 CMR 362.240, were received from any state during that same quarter.
(h) is a veteran or active duty personnel as defined in 106 CMR 362.240(F).
(8) Battered Noncitizen. A noncitizen who is battered is an eligible noncitizen when he or she has proof of the battering and meets the following conditions:
(a) The noncitizen must have one of the following:
1. a Form I-130 petition filed by his or her spouse or parent;
2. a Form I-130 petition filed as a widow(er) of a U.S. Citizen;
3. an approved self-petition under the Violence Against Women Act or a pending self-petition under the Act with a notice of prima facie determination (including those filed by a parent); or
4. an application for cancellation of removal or suspension of deportation filed as a victim of domestic violence;
(b) The noncitizen, the noncitizen's child or the noncitizen child's parent has been
```

#### Rank 3 — RELEVANT (sim 0.555)

- **Chunk ID**: `cmr_sec_362_220__000`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 1 / 12
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses whether noncitizens can receive SNAP benefits by explaining the eligibility requirements, verification procedures, and conditions under which noncitizens may or may not qualify.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens

A noncitizen applying for SNAP benefits and claiming an eligible noncitizen status must verify that he or she is present in the United States (U.S.) under one of the noncitizen statuses provided in 106 CMR 362.220(A). The status of a noncitizen must be verified at certification, at recertification or whenever the status of the noncitizen changes or is questionable. Verification of an eligible noncitizen status must be presented before the determination of SNAP eligibility. When a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide information about, or acceptable verification of, his or her eligible noncitizen status, that household member shall be ineligible. In such cases the Department shall not continue efforts to obtain documentation. Also, if a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide, or apply for, a Social Security Number due to immigration status he or she is ineligible. The Department shall not continue efforts to obtain documentation. SNAP eligibility will be determined in accordance with 106 CMR 365.520(A) for the household members who do verify an eligible noncitizen status. The Commissioner or designee is required to report to the United States Citizenship and Immigration Services (USCIS) information about noncitizens "known to be in the U.S. unlawfully" as defined in 106 CMR 362.240. SNAP - Eligible Noncitizen Status. A noncitizen's eligibility for SNAP benefits depends on
```

#### Rank 4 — RELEVANT (sim 0.548)

- **Chunk ID**: `cmr_sec_362_220__005`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 6 / 12
- **Program**: SNAP
- **Hierarchy**: (B) To receive SNAP benefits the qualified noncitizen must meet the condition...
- **Judge reason**: The chunk directly addresses noncitizen eligibility for SNAP benefits by specifying conditions under which qualified noncitizens can receive benefits, including provisions for battered noncitizens and residency requirements.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (B) To receive SNAP benefits the qualified noncitizen must meet the condition...

abused in the U.S. under any of the circumstances in 106 CMR 362.220(B)(8)(b)1. through 3.:
1. The noncitizen has been battered or subjected to extreme cruelty in the U.S. by a spouse or parent of the noncitizen, or by a member of the spouse's or parent's family residing in the same household, if the spouse or parent consents to or acquiesces in the battery and cruelty;
2. The noncitizen's child has been battered or subjected to extreme cruelty in the U.S. by a spouse or parent of the noncitizen, or by a member of the spouse's or parent's family residing in the same household if the spouse or parent consents to or acquiesces in the battery or cruelty, and the noncitizen did not actively participate in the battery or cruelty; or
3. The parent of a noncitizen child has been battered or subjected to extreme cruelty in the U.S. by the parent's spouse, or by a member of the spouse's family residing in the same household as the parent, if the spouse consents to or acquiesces in such battery or cruelty;
(c) There is a substantial connection between the battery or extreme cruelty and the need for SNAP benefits;
(d) The battered noncitizen, child, or parent no longer resides in the same household as the abuser; and
(e) The noncitizen meets one of the following conditions:
1. has resided as a qualified noncitizen in the U.S. for five years;
2. was born on or before August 22, 1931 and was lawfully residing in the U.S. on August 22, 1996;
3. is a child younger than 18 years old;
```

#### Rank 5 — RELEVANT (sim 0.545)

- **Chunk ID**: `cmr_sec_362_220__002`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 3 / 12
- **Program**: SNAP
- **Hierarchy**: (A) A qualified noncitizen is a person who, at the time the person applies fo...
- **Judge reason**: The chunk directly addresses which noncitizens can receive SNAP benefits by listing qualified noncitizen statuses and USCIS categories that make them eligible.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (A) A qualified noncitizen is a person who, at the time the person applies fo...

(8) legal permanent residents; and
(9) battered noncitizens.
(B) To receive SNAP benefits the qualified noncitizen must meet the conditions of one of the following USCIS statuses:
(1) Refugee. A noncitizen present in the U.S. as a refugee under section 207 or 207(c) of the INA is an eligible noncitizen.
(2) Asylee. A noncitizen present in the U.S. as a refugee under section 208 of the INA is an eligible noncitizen.
(3) Withholding of Deportation. A noncitizen whose deportation is being withheld under section 243(h) or whose removal is withheld under section 241(b)(3) of the INA is an eligible noncitizen.
(4) Cuban/Haitian Entrant. A noncitizen who is present in the U.S. as a Cuban/Haitian entrant (as defined in section 501(e) of the Refugee Education Assistance Act of 1980) is an eligible noncitizen.
(5) Amerasian. A noncitizen from Vietnam who is present in the U.S. as an Amerasian immigrant (as defined in section 584 of the Foreign Operations, Export Financing and Related Programs Appropriations Act, 1988) is an eligible noncitizen.
```


### cmr_010 — SNAP restoration (rank-1: PARTIAL)

**Question**: When are SNAP benefits restored after an agency error  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366`  
**Notes**: BROAD — chapter 366 covers changes/restoration; specific section may be 366.500  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.60  

#### Rank 1 — PARTIAL (sim 0.519)

- **Chunk ID**: `cmr_sec_366_510__000`
- **Section**: `366.510` — Entitlement for Benefits Including Underpayments
- **Program**: SNAP
- **Judge reason**: The chunk explains what types of agency errors qualify for benefit restoration but does not specify the timeline or when (how quickly) benefits are actually restored after an error is identified.

```
106 CMR 366 > ADDITIONAL > 366.510 Entitlement for Benefits Including Underpayments

A household is entitled to lost benefits only for those months the household was eligible to participate. In cases where there is no information in the household's case record to document that the household was actually eligible, the Department shall advise the household of what information must be provided to determine eligibility for these months. For each month that the household cannot provide the necessary information to demonstrate its eligibility, the household shall be considered ineligible for restoration of lost benefits. The Department shall restore to the household benefits that were lost because of:
(A) an agency error, such as an incorrect allotment, an incorrect denial or termination of benefits, agency delay in acting on a reported change, or failure to provide benefits for the month following the expiration of the certification period for households properly fulfilling the recertification process;
(B) a fraud disqualification penalty of a household member that is later reversed; and
(C) an error by the Department or by SSA through joint application processing. Such an error shall include, but is not limited to, the loss of an applicant's SNAP application after it has been filed with SSA. Households are also entitled to lost benefits if a Department policy specifically provides for restoration of lost benefits. NON-TEXT PAGE
```

#### Rank 2 — PARTIAL (sim 0.444)

- **Chunk ID**: `cmr_sec_366_570__000`
- **Section**: `366.570` — Method of Restoration
- **Program**: SNAP
- **Judge reason**: Explains how benefits are restored but does not specify the timeline or conditions for when restoration occurs after agency error.

```
106 CMR 366 > ADDITIONAL > 366.570 Method of Restoration

Regardless of current eligibility, the Department shall restore lost benefits to a household by issuing an allotment equal to the amount of benefits that were lost. For currently eligible households, the lost benefits shall be issued in a lump sum separate from the household's current monthly allotment. The Department shall honor reasonable requests that the benefits be restored in monthly installments.
```

#### Rank 3 — RELEVANT (sim 0.442)

- **Chunk ID**: `cmr_sec_366_520__001`
- **Section**: `366.520` — Computing the Amount to be Restored
- **Chunk position**: 2 / 2
- **Program**: SNAP
- **Hierarchy**: (B) Computing the Amount to be Restored.
- **Judge reason**: The chunk directly addresses when and how SNAP benefits are restored after agency errors (incorrect allotment, denial, delay, or termination), specifying the exact months benefits will be restored back to.

```
106 CMR 366 > ADDITIONAL > 366.520 Computing the Amount to be Restored > (B) Computing the Amount to be Restored.

(B) Computing the Amount to be Restored.
(1) If an incorrect allotment caused the loss to an eligible household, the loss of benefits shall be calculated only for those months the household participated. The Department shall calculate the allotment the household was eligible to receive during the months of entitlement. The amount to be restored is the difference between the actual allotment and the allotment the household was eligible to receive.
(2) If an incorrect denial, delay or termination of benefits caused the loss, the months affected by the loss are calculated as follows:
(a) If an eligible household's application was erroneously denied, benefits will be restored back to the month of application. For an eligible household filing a timely reapplication, benefits shall be restored back to the month following the expiration of its certification period;
(b) If an eligible household's application was delayed, the months for which benefits will be restored shall be calculated in accordance with 106 CMR 361.900 through 361.960; and
(c) If a household's benefits were erroneously terminated, benefits will be restored back to the first month in which benefits were not received as a result of the erroneous action. After computing the date the loss initially occurred, the loss shall be calculated for each month subsequent to that date until either the first month the error is corrected or the first month the household is found ineligible.
```

#### Rank 4 — PARTIAL (sim 0.439)

- **Chunk ID**: `cmr_sec_366_530__000`
- **Section**: `366.530` — Notification of Restoration of Lost Benefits
- **Program**: SNAP
- **Judge reason**: The chunk explains the process and notification requirements for benefit restoration but does not specify the timeframe or timeline for when benefits are actually restored after an agency error.

```
106 CMR 366 > ADDITIONAL > 366.530 Notification of Restoration of Lost Benefits

When it is determined that a loss of benefits occurred, the Department shall automatically take action to restore those benefits to the household. No action by the household is necessary. The household shall be notified of its entitlement, the amount of benefits to be restored, any offsetting that was done, the method of restoration and the right to appeal through the fair hearing process if the household disagrees with any aspect of the proposed lost benefit restoration.
```

#### Rank 5 — PARTIAL (sim 0.427)

- **Chunk ID**: `cmr_sec_366_520__000`
- **Section**: `366.520` — Computing the Amount to be Restored
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Hierarchy**: (A) Months of Restoration.
- **Judge reason**: Addresses the timeframe for restoration (12 months) but doesn't specifically explain when restoration occurs after agency error or the conditions that trigger it.

```
106 CMR 366 > ADDITIONAL > 366.520 Computing the Amount to be Restored

(A) Months of Restoration. Except when benefits are restored as the result of the reversal of a fraud disqualification penalty, benefits shall be restored for not more than 12 months prior to whichever of the following occurred first:
(1) the month the household or another person or agency notified the Department verbally or in writing of the possible loss of benefits;
(2) the month the Department discovered that a loss has occurred; or
(3) the date the household requested a fair hearing to contest the adverse action that resulted in the loss.
```


### cmr_011 — SNAP recertification (rank-1: RELEVANT)

**Question**: What are the SNAP recertification requirements  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366` — judge picked rank-1 RELEVANT chunk in section `366.300` (section-author intuition agrees)  
**Notes**: BROAD — chapter 366 generally; could pull from 365.150 for PA households  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.594)

- **Chunk ID**: `cmr_sec_366_300__000`
- **Section**: `366.300` — Recertification
- **Program**: SNAP
- **Judge reason**: Directly addresses SNAP recertification requirements by outlining the core requirements: submitting a new application, being interviewed, and providing required verification.

```
106 CMR 366 > ADDITIONAL > 366.300 Recertification

A household's SNAP benefits shall not continue beyond the certification period, unless the household has been recertified. To recertify, the household must submit a new application, be interviewed, and provide required verification in accordance with the timeliness standards set forth in 106 CMR 366.320. Those households that timely recertify and are found eligible shall be entitled to uninterrupted benefits. The following sections list the responsibilities of the household and the Department in the recertification process.
```

#### Rank 2 — PARTIAL (sim 0.590)

- **Chunk ID**: `cmr_sec_365_150__000`
- **Section**: `365.150` — Recertification Requirements for PA Households
- **Program**: SNAP
- **Judge reason**: Addresses recertification timing for PA households specifically but doesn't comprehensively cover general SNAP recertification requirements for all household types.

```
106 CMR 365 > SPECIAL > 365.150 Recertification Requirements for PA Households

PA households shall be recertified for SNAP benefits, to the extent possible, at the same time they have their eligibility reviewed for the cash assistance program. If a PA household has not had its PA eligibility reviewed by the end of the 11th month following its initial SNAP certification or last eligibility review, a Notice of SNAP Termination shall be sent to the household.
```

#### Rank 3 — PARTIAL (sim 0.589)

- **Chunk ID**: `cmr_sec_366_310__000`
- **Section**: `366.310` — Notification to Recertify
- **Program**: SNAP
- **Judge reason**: The chunk addresses notification procedures for recertification rather than the actual recertification requirements themselves (eligibility criteria, documentation needed, frequency, etc.).

```
106 CMR 366 > ADDITIONAL > 366.310 Notification to Recertify

Households certified for one or two months shall receive, at the time of certification, a separate notice of recertification responsibilities entitled Notice of Expiration. Those households certified for three months or more (except public assistance households) shall receive a separate Notice of Expiration in the month prior to the last month of their certification period. This notice will be mailed by the Department no earlier than the first day of the next-to-last month of certification or no later than the last day of the next-to-last month of certification. The contents of the notice are set forth in 106 CMR 364.840: Notice of SNAP Termination. Public assistance households shall receive a notice of recertification responsibilities prior to the end of the SNAP certification period. In some instances, these households are recertified for SNAP at the same time as their public assistance redetermination.
```

#### Rank 4 — PARTIAL (sim 0.563)

- **Chunk ID**: `cmr_sec_364_840__006`
- **Section**: `364.840` — Notice of SNAP Termination
- **Chunk position**: 7 / 7
- **Program**: SNAP
- **Hierarchy**: (L) The right to apply for SNAP recertification at an office of the Social Se...
- **Judge reason**: Mentions SNAP recertification but only addresses a specific scenario (SSI recipients) rather than general recertification requirements.

```
106 CMR 364 > DETERMINING > 364.840 Notice of SNAP Termination > (L) The right to apply for SNAP recertification at an office of the Social Se...

(L) The right to apply for SNAP recertification at an office of the Social Security Administration (SSA) if all members of the household are applicants or recipients of Supplemental Security Income (SSI).
```

#### Rank 5 — PARTIAL (sim 0.558)

- **Chunk ID**: `cmr_sec_365_190__004`
- **Section**: `365.190` — Transitional Benefits Alternative
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (E) Recertification Requirements for TBA Households.
- **Judge reason**: Addresses recertification requirements but only for a specific subset (TBA households) rather than general SNAP recertification requirements, and references another regulation for the actual notification procedures.

```
106 CMR 365 > SPECIAL > 365.190 Transitional Benefits Alternative > (E) Recertification Requirements for TBA Households.

(E) Recertification Requirements for TBA Households. The TBA household must recertify for SNAP at the end of the TBA period and will be notified to recertify in accordance with 106 CMR 366.310: Notification to Recertify.
```


### cmr_012 — SNAP categorical eligibility (rank-1: RELEVANT)

**Question**: What is SNAP categorical eligibility  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365` — judge picked rank-1 RELEVANT chunk in section `365.180` (section-author intuition agrees)  
**Notes**: BROAD — chapter 365 special households; 365.180 in v1  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — RELEVANT (sim 0.528)

- **Chunk ID**: `cmr_sec_365_180__000`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 1 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk directly defines SNAP categorical eligibility by listing the specific household types that qualify for categorical eligibility under Massachusetts DTA policy.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households

(A) The following SNAP households are categorically eligible:
(1) Any SNAP household in which all members receive or are authorized to receive SSI and/or Emergency Aid to the Elderly, Disabled and Children (EAEDC) benefits;
(2) Any SNAP household in which all members receive or are authorized to receive TAFDC benefits;
(3) Any SNAP household in which all members receive or are authorized to receive a combination of benefits listed in 106 CMR 365.180(A)(1) or (2);
(4) SNAP-only Temporary Assistance for Needy Families (TANF) Service Family Households which include SNAP households:
(a) consisting solely of a pregnant woman;
(b) with a child younger than 19 years old living with a parent;
(c) with a child younger than 19 years old living with a caretaker relative; and
(d) with a child younger than 19 years old living with an adult caretaker exercising SNAP parental control pursuant to 106 CMR 361.200(A)(2): Parental Control Rule. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards;
```

#### Rank 2 — PARTIAL (sim 0.502)

- **Chunk ID**: `cmr_sec_365_180__006`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 7 / 9
- **Program**: SNAP
- **Hierarchy**: (F) Verification Requirements.
- **Judge reason**: The chunk discusses categorical eligibility procedures and verification requirements but does not define what SNAP categorical eligibility actually is or explain the concept itself.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (F) Verification Requirements.

106 CMR 361.200: Household Concept.
(G) Determination of Eligibility.
(1) Pending SSI or EAEDC Eligibility. To determine if a household will be eligible due to its status as an EAEDC or SSI household, the SNAP eligibility determination may be temporarily postponed, within the 30-day processing timeframe, if the household is not entitled to expedited service and appears to be categorically eligible. However, denial of a potentially categorically eligible household shall only be postponed until the 30 th. Upon approval of the EAEDC or SSI application, the household is considered categorically eligible if it meets all the criteria in 106 CMR 365.180(A) through (F).
(2) Denials. For a household filing a joint application for SNAP and EAEDC benefits or a household with an EAEDC or SSI application pending that is originally denied SNAP benefits, but is later determined eligible to receive EAEDC or SSI benefits and otherwise categorically eligible, the original application and any other pertinent information occurring after that application shall be used to determine benefits. A second interview is not required. However, the Department shall use any available information to update the application and/or make mail or phone contact with the household or authorized representative to determine any changes in circumstances. Denied applications of a potentially categorically eligible household must be easily retrievable.
```

#### Rank 3 — PARTIAL (sim 0.495)

- **Chunk ID**: `cmr_sec_365_180__007`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 8 / 9
- **Program**: SNAP
- **Hierarchy**: (G) Determination of Eligibility.
- **Judge reason**: The chunk discusses procedures for categorically eligible households and SNAP processing but does not define what categorical eligibility actually is or explain the concept itself.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (G) Determination of Eligibility.

If a determination of eligibility for EAEDC or SSI benefits is postponed beyond 30 days, or an application for EAEDC or SSI benefits is denied, the SNAP application should be processed immediately as an NPA case. Any changes shall be initialed and the updated application signed by the authorized representative or authorized household member. The Department shall act on reevaluating the original household's EAEDC or SSI eligibility. When applicable, the household shall be advised on the notice of denial to inform the Department if any pending application for EAEDC or SSI benefits is subsequently approved.
(3) Providing Benefits. Any household determined to be categorically eligible within the 30-day SNAP processing timeframe shall be provided benefits back to the date of the SNAP application or, in the case of a joint application, back to the date of the EAEDC or SSI application. Benefits shall be prorated in accordance with 106 CMR 364.650: Prorating Initial Month's Benefits. If a household whose determination of eligibility for EAEDC or SSI benefits has been postponed beyond 30 days and whose SNAP application has been processed as an NPA case subsequently gets approved for EAEDC or SSI benefits, the SNAP benefits must be recalculated based on the excess medical, uncapped shelter, and net income (elderly/disabled) provisions. Any SNAP benefits owed back to the date of the SNAP application or from the
```

#### Rank 4 — PARTIAL (sim 0.493)

- **Chunk ID**: `cmr_sec_365_180__002`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Hierarchy**: (B) SSI, TAFDC and TANF
- **Judge reason**: The chunk discusses specific rules for categorical eligibility (ineligibility conditions and excluded household members) but does not explain what categorical eligibility itself is or its basic definition and purpose.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (B) SSI, TAFDC and TANF

(B) SSI, TAFDC and TANF
(1) Ineligible Households. An SSI, TAFDC and/or TANF household shall not be considered categorically eligible if:
(a) the entire household is institutionalized as defined in 106 CMR 361.200: Household Concept;
(b) any member of that household is disqualified from receiving SNAP benefits for the reasons listed in 106 CMR 367.800: Disqualification Penalties or for failing to comply with SNAP Work Program requirements at 106 CMR 362.320: SNAP Work Program; or
(c) a household that is a TANF-service Household identified at 106 CMR 365.180(A)(4), (5) or (6) will not be considered categorically-eligible if the household's income exceeds the income standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards.
(2) Ineligible Household Members. No person shall be included as a member of an otherwise categorically eligible household if that person is:
(a) an ineligible noncitizen, in accordance with 106 CMR 362.220: Noncitizens;
(b) an ineligible student, in accordance with 106 CMR 362.400 through 362.410;
(c) institutionalized in a nonexempt facility, as defined in 106 CMR 361.240(B): Residents of Institutions; or
(d) ineligible because of failure to comply with the work requirements of the SNAP Program at 106 CMR 362.320: SNAP Work Program or 367.800: Disqualification Penalties.
```

#### Rank 5 — RELEVANT (sim 0.492)

- **Chunk ID**: `cmr_sec_365_180__001`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk directly defines SNAP categorical eligibility by listing specific categories of households that qualify and their income requirements under Massachusetts DTA policy.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (A) The following SNAP households are categorically eligible:

(5) SNAP-only TANF Service Elder/Disabled Households which include SNAP households consisting solely of non-SSI elders (60 years of age or older) and/or disabled individuals in accordance with SNAP disability standards at 106 CMR 361.210: Elderly or Disabled Individuals. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards; and
(6) SNAP-only TANF Service Adult Households include SNAP households consisting solely of adults between 19 and 59 years of age. These households must meet the Gross Monthly Categorically Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards. For purposes of 106 CMR 365.180(A)(1) through (3), authorized to receive means that an individual has been determined eligible for benefits and has been notified of this determination, even if benefits have been authorized but not received, authorized but not accessed, suspended or recouped, or not paid because they are less than a minimum amount. For purposes of 106 CMR 365.180(A)(4) through (6), a TANF Service includes receipt of the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure.
```


### cmr_013 — SSP eligibility (rank-1: RELEVANT)

**Question**: What is the State Supplement Program and who is eligible  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.120` — judge picked rank-1 RELEVANT chunk in section `327.100` (section-author intuition disagrees with judge)  
**Notes**: 327.120 Eligibility for State Supplement Program  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.542)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly defines the State Supplement Program and clearly states who is eligible (individuals who receive SSI or don't qualify for SSI due to income), directly answering both parts of the user's question.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.100 Overview of State Supplement Program

SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 2 — PARTIAL (sim 0.531)

- **Chunk ID**: `cmr_sec_327_010__000`
- **Section**: `327.010` — Authority for State Supplement Program
- **Program**: SSP
- **Judge reason**: Explains what SSP is and that Massachusetts offers it, but does not provide eligibility criteria details

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.010 Authority for State Supplement Program

The Supplemental Security Income (SSI) program is administered by the Social Security Administration (SSA) to provide financial assistance to eligible aged, disabled and blind individuals. States have the option to provide additional assistance through the State Supplement Program (SSP). Massachusetts has opted to provide this additional assistance. SSP is authorized under M.G.L. c. 6, § 131 and M.G.L. c. 118A and applicable federal law pertaining to the SSI program and agreements with the Commissioner of Social Security. 106 CMR 327.000 is promulgated and implemented in accordance with M.G.L. c. 30A, and applicable General Laws of Massachusetts.
```

#### Rank 3 — RELEVANT (sim 0.513)

- **Chunk ID**: `cmr_sec_327_120__000`
- **Section**: `327.120` — Eligibility for State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly defines the State Supplement Program (SSP) and clearly specifies the two categories of individuals eligible for it.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.120 Eligibility for State Supplement Program

An application for SSI serves is an application for SSP. There is no separate SSP application. Eligibility for SSP is determined after an eligibility determination for SSI is made by the Social Security Administration (SSA). The Department must accept the SSA determination. Individuals may be eligible for SSP if they are either:
(A) determined eligible for SSI; or
(B) determined not eligible for SSI solely due to income, but their countable income is less than the combined Federal Benefit Rate (FBR) and the appropriate SSP payment.
```

#### Rank 4 — PARTIAL (sim 0.450)

- **Chunk ID**: `cmr_sec_327_220__004`
- **Section**: `327.220` — State Living Arrangements
- **Chunk position**: 5 / 6
- **Program**: SSP
- **Hierarchy**: (D) State living Arrangement E: Domiciliary Care.
- **Judge reason**: The chunk discusses a specific living arrangement category within SSP eligibility but does not define what the State Supplement Program is or provide general eligibility criteria.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.220 State Living Arrangements > (D) State living Arrangement E: Domiciliary Care.

(D) State living Arrangement E: Domiciliary Care. State Living Arrangement E includes an individual living in a licensed rest home where he or she pays a fixed rate as established by the Massachusetts Executive Office of Health and Human Services. The total payment, combined SSI and SSP, includes an allowance for personal needs. Specifically excluded from this category are persons institutionalized in Title XIX facilities or in a public institution when the individual is not being charged for his or her care.
```

#### Rank 5 — PARTIAL (sim 0.431)

- **Chunk ID**: `cmr_sec_327_110__000`
- **Section**: `327.110` — Definitions
- **Program**: SSP
- **Judge reason**: The chunk provides definitions related to SSP eligibility but does not explain what the State Supplement Program is or clearly state who is eligible for it.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.110 Definitions

The following words and terms, when used in 106 CMR 327.000, have the following meanings, unless the context otherwise requires. (Mass. Register #1390 5/3/19) Child. For SSP purposes, is one who meets the SSI definition of child. Countable Income. As defined in 20 CFR 416.1104. Eligible Individual. An aged, disabled or blind individual who meets all SSI eligibility requirements. See 20 CFR 416.120. Eligible Couple. An eligible individual and his or her eligible spouse who are living in the same household. See 20 CFR 416.1801. Federal Benefit Rate (FBR). As defined in 20 CFR 416.1101. Public Income Maintenance Payment. A payment from any of the following programs: SSI, TAFDC, Refugee Act of 1980, Disaster Relief Act of 1974, Veterans Administration benefits based on need, or any State or local governmental assistance program based on need. Representative Payee. As defined in 20 CFR 416.601. Resources. As defined in 20 CFR 416.1201, et seq. Supplemental Security Income (SSI). As defined in 20 CFR 416.101. SSP-only. A designation for a client who is ineligible for SSI solely based on his or her income but is eligible to receive SSP benefits.
```


### cmr_014 — SSP payment standards (rank-1: RELEVANT)

**Question**: What are the SSP payment standards  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.330` — judge picked rank-1 RELEVANT chunk in section `327.330` (section-author intuition agrees)  
**Notes**: 327.330 Payment Standards  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.511)

- **Chunk ID**: `cmr_sec_327_330__000`
- **Section**: `327.330` — Payment Standards
- **Program**: SSP
- **Judge reason**: The chunk directly addresses SSP payment standards by explaining how they are determined and where to find them.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.330 Payment Standards

Payment amounts are based on Eligibility Category, State Living Arrangement, whether the client is eligible as an individual or as a member of an eligible couple and the amount of countable income. If countable income exceeds the Federal Benefit Rate (FBR), the amount exceeding the FBR is deducted from the SSP payment standard. Payment standards are available online at www.mass.gov/dta under the heading Key Resources/Program Eligibility Charts and Tables/SSI Program Payment Charts. Paper copies are available upon request.
```

#### Rank 2 — PARTIAL (sim 0.454)

- **Chunk ID**: `cmr_sec_327_350__000`
- **Section**: `327.350` — Timing and Method of SSP Benefit Payments
- **Program**: SSP
- **Judge reason**: The chunk addresses payment timing and minimum amounts but does not provide the actual SSP payment standards/benefit amounts that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.350 Timing and Method of SSP Benefit Payments

SSP benefits are paid once a month. The Department shall determine the method of payment. Minimum Monthly Payment The minimum monthly payment for the SSP is $1.00. If the payment amount is greater than zero but less than $1.00, a payment of $1.00 will be issued.
```

#### Rank 3 — PARTIAL (sim 0.376)

- **Chunk ID**: `cmr_sec_327_340__000`
- **Section**: `327.340` — Date Benefits Begin
- **Program**: SSP
- **Judge reason**: The chunk discusses when SSP payments begin rather than what the actual payment standards (amounts) are.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.340 Date Benefits Begin

SSP benefit payments will begin as of the date SSI payments begin. For SSP-only eligible clients, SSP benefit payments will begin as of the first day of the month following the date of the SSI application.
```

#### Rank 4 — PARTIAL (sim 0.372)

- **Chunk ID**: `cmr_sec_327_110__000`
- **Section**: `327.110` — Definitions
- **Program**: SSP
- **Judge reason**: This chunk defines SSP-related terms but does not contain the actual payment standards/amounts that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.110 Definitions

The following words and terms, when used in 106 CMR 327.000, have the following meanings, unless the context otherwise requires. (Mass. Register #1390 5/3/19) Child. For SSP purposes, is one who meets the SSI definition of child. Countable Income. As defined in 20 CFR 416.1104. Eligible Individual. An aged, disabled or blind individual who meets all SSI eligibility requirements. See 20 CFR 416.120. Eligible Couple. An eligible individual and his or her eligible spouse who are living in the same household. See 20 CFR 416.1801. Federal Benefit Rate (FBR). As defined in 20 CFR 416.1101. Public Income Maintenance Payment. A payment from any of the following programs: SSI, TAFDC, Refugee Act of 1980, Disaster Relief Act of 1974, Veterans Administration benefits based on need, or any State or local governmental assistance program based on need. Representative Payee. As defined in 20 CFR 416.601. Resources. As defined in 20 CFR 416.1201, et seq. Supplemental Security Income (SSI). As defined in 20 CFR 416.101. SSP-only. A designation for a client who is ineligible for SSI solely based on his or her income but is eligible to receive SSP benefits.
```

#### Rank 5 — PARTIAL (sim 0.366)

- **Chunk ID**: `cmr_sec_327_210__000`
- **Section**: `327.210` — Eligibility Categories
- **Program**: SSP
- **Judge reason**: This chunk describes SSP eligibility categories rather than the actual payment standards/amounts that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.210 Eligibility Categories

An individual must be in one of the following SSI categories to be eligible for SSP. If an individual is eligible under more than one category, the category which provides the highest payment level shall be used:
(A) Aged. 65 years of age or older;
(B) Disabled. Disabled in accordance with 20 CFR Part 416, Subpart I. If disability has not been determined by SSA, disability will be determined by the agency or organization under agreement with the Department to provide disability evaluation services; or
(C) Blind. Determined to be blind in accordance with 20 CFR Part 416, Subpart I. If blindness has not been determined by SSA, blindness will be determined by the agency or organization under agreement with the Department to provide disability evaluation services.
```


### cmr_015 — fair hearings general (rank-1: PARTIAL)

**Question**: What is the fair hearing process at DTA  
**Program filter**: (none)  
**Expected section (for reference)**: `343.110`  
**Notes**: 343.110 General Description of the Fair Hearing Process; no program filter (343 is Hearings)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.70  

#### Rank 1 — PARTIAL (sim 0.469)

- **Chunk ID**: `cmr_sec_701_600__010`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 11 / 25
- **Program**: EA
- **Hierarchy**: (S) Fair Hearing.
- **Judge reason**: Provides a definition of fair hearing but does not describe the actual process steps; directs to another manual reference (106 CMR 343.110) that would contain the detailed process information.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (S) Fair Hearing.

(S) Fair Hearing. A proceeding conducted by an impartial officer of the Division of Hearings to review an action proposed, taken or not taken by the Department, which has been appealed. Manual Reference: 106 CMR 343.110: General Description of the Fair Hearing Process.
```

#### Rank 2 — RELEVANT (sim 0.446)

- **Chunk ID**: `cmr_sec_343_110__000`
- **Section**: `343.110` — General Description of the Fair Hearing Process
- **Program**: Hearings
- **Judge reason**: This chunk directly describes the fair hearing process at DTA, including its purpose, structure, and how it operates, which directly answers the user's question.

```
106 CMR 343 > FAIR HEARING RULES > 343.110 General Description of the Fair Hearing Process

The fair hearing process is an adjudicatory proceeding which allows dissatisfied applicants and clients and certain spouses, as well as certain sponsors of aliens, upon written request, to obtain a determination of the appropriateness of certain actions or inactions on the part of the Department, or of alleged coercive or otherwise improper conduct by a Department employee. The process is designed to secure and protect the interests of both the appellant and appropriate Department personnel and to ensure fair and equitable treatment for all involved. A hearing is conducted by an impartial hearing officer of DOH. The decision of the hearing officer is based only on evidence and testimony presented at the hearing. The hearing officer examines the facts, the law, and the other circumstances of the case presented by the parties to determine the legality and appropriateness of the disputed Department actions or decision of the Department. The hearing decision is binding upon the Department and is not subject to any review within the Department except in the case of a remand of the decision for a new hearing pursuant to 106 CMR 343.710.
```

#### Rank 3 — PARTIAL (sim 0.437)

- **Chunk ID**: `cmr_sec_343_030__004`
- **Section**: `343.030` — Definitions
- **Chunk position**: 5 / 8
- **Program**: Hearings
- **Hierarchy**: (H) DOH.
- **Judge reason**: Provides definitions related to fair hearings but does not describe the actual fair hearing process or procedures.

```
106 CMR 343 > FAIR HEARING RULES > 343.030 Definitions > (H) DOH.

(H) DOH. The Division of Hearings within the Department of Transitional Assistance.
(I) Fair Hearing. A proceeding where the legal rights, duties, benefits, or privileges of persons and agencies are determined.
```

#### Rank 4 — PARTIAL (sim 0.419)

- **Chunk ID**: `cmr_sec_343_010__000`
- **Section**: `343.010` — Purpose
- **Program**: Hearings
- **Judge reason**: Introduces the fair hearing rules and scope but doesn't describe the actual process steps or procedures for conducting a fair hearing.

```
106 CMR 343 > FAIR HEARING RULES > 343.010 Purpose

106 CMR 343.00 sets forth the rules for hearings and appeals filed by applicants or clients dissatisfied with certain actions or inactions by the Department of Transitional Assistance. Scope 106 CMR 343.000 sets forth the exclusive rules for hearings and appeals filed by applicants, clients and, if applicable, any sponsors of aliens under the programs of Transitional Aid to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC) and State Supplement Program (SSP), and by clients or former clients and/or their spouses under M.G.L. c. 62D. Hearings and appeals arising under Supplemental Nutrition Assistance Program (SNAP) are governed by 106 CMR 367.000: Supplemental Nutrition Assistance Program: Violations, Hearings and Claims, excepting that matters not addressed therein shall be governed by 106 CMR 343.000. The Department may enter into interdepartmental service agreements with other state agencies to conduct hearings in accordance with 106 CMR 343.000.
```

#### Rank 5 — PARTIAL (sim 0.413)

- **Chunk ID**: `cmr_sec_364_710__003`
- **Section**: `364.710` — Household Certification Periods
- **Chunk position**: 4 / 6
- **Program**: SNAP
- **Hierarchy**: (D) The notice shall also advise the household of its rights to a fair hearin...
- **Judge reason**: Mentions fair hearing rights but only in context of notice requirements; does not explain the actual fair hearing process itself.

```
106 CMR 364 > DETERMINING > 364.710 Household Certification Periods > (D) The notice shall also advise the household of its rights to a fair hearin...

(D) The notice shall also advise the household of its rights to a fair hearing, the telephone number of the Department, and, if possible, the name of the individual to contact for additional information.
```


### cmr_016 — hearing time limits (rank-1: PARTIAL)

**Question**: How long does someone have to request a fair hearing  
**Program filter**: (none)  
**Expected section (for reference)**: `343.140`  
**Notes**: 343.140 Time Limits; could also pull 367.100 (SNAP hearing timing)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — PARTIAL (sim 0.523)

- **Chunk ID**: `cmr_sec_343_240__000`
- **Section**: `343.240` — Request for Fair Hearing
- **Program**: Hearings
- **Judge reason**: The chunk references time limits for requesting a fair hearing but directs to 106 CMR 343.140 for the actual deadline rather than stating it directly.

```
106 CMR 343 > FAIR HEARING RULES > 343.240 Request for Fair Hearing

(A) A request for a fair hearing is defined as a written statement by the appellant or his or her authorized representative which asks for the opportunity to present the case to a higher authority. The request for a fair hearing must be received by DOH within the time limits provided in 106 CMR 343.140.
(B) Any request for a fair hearing which alleges coercive or otherwise improper conduct on the part of a Department employee must state the name of the employee and the place, date and nature of the incident. If the request lacks the information required by 106 CMR 343.240, DOH shall notify the appellant of the requirement. If the appellant then fails to provide the information within ten days, the appeal shall be dismissed.
```

#### Rank 2 — RELEVANT (sim 0.483)

- **Chunk ID**: `cmr_sec_343_140__001`
- **Section**: `343.140` — Time Limits
- **Chunk position**: 2 / 4
- **Program**: Hearings
- **Hierarchy**: (B) Time Limitation on the Right of Appeal.
- **Judge reason**: Directly specifies the time limits (90 days or 120 days depending on circumstances) within which someone must request a fair hearing from the DTA.

```
106 CMR 343 > FAIR HEARING RULES > 343.140 Time Limits > (B) Time Limitation on the Right of Appeal.

(B) Time Limitation on the Right of Appeal. The date of request for a fair hearing is the date on which the Division of Hearings receives a written statement from the appellant asking for the opportunity for a fair hearing will be treated as a request for an appeal. The Division of Hearings must receive the request within the following time limits:
(1) 90 days from the date of official written notice of action by the Department.
(2) Unless waived by the Division of Hearing Director or his or her designee, 120 days from:
(a) the date of application when the Department fails to act on an application;
(b) the date of request for service when the Department fails to act on the request;
(c) the date of Department action when the Department fails to send official written notice of the action;
(d) the date of the alleged coercive or otherwise improper conduct. This time limit can be extended up to one year from the date of the conduct provided that the appellant files an affidavit with the Director of the Division of Hearings stating that, and can establish at a hearing that:
1. he or she did not know of the right to appeal;
2. he or she reasonably believed that the problem was being resolved administratively; or
3. he or she was justifiably unaware of the conduct in question; and
4. the appeal is made in good faith. Failure to substantiate allegations of coercive or improper conduct either prior to or at the hearing shall be grounds for dismissal.
```

#### Rank 3 — RELEVANT (sim 0.476)

- **Chunk ID**: `cmr_sec_367_100__000`
- **Section**: `367.100` — Time Period for Requesting Hearing
- **Program**: Program Integrity
- **Judge reason**: Directly specifies the time periods (90 days, one year, and within certification period) for requesting a fair hearing on DTA actions and benefit disputes.

```
106 CMR 367 > VIOLATIONS, > 367.100 Time Period for Requesting Hearing

A household shall be allowed to request a hearing on any action by the Department, or on loss of benefits which occurred in the prior 90 days. Action by the Department includes a denial of a request for restoration of any benefits lost more than 90 days but less than one year prior to the request. In addition, at any time within a certification period a household may request a fair hearing to dispute its current level of benefits.
```

#### Rank 4 — PARTIAL (sim 0.459)

- **Chunk ID**: `cmr_sec_343_245__000`
- **Section**: `343.245` — Dismissal of Request for a Hearing
- **Program**: Hearings
- **Judge reason**: References the time frame requirement in 106 CMR 343.140 but doesn't state the actual deadline; user would need to look up that regulation to get the specific answer.

```
106 CMR 343 > FAIR HEARING RULES > 343.245 Dismissal of Request for a Hearing

(A) DOH shall dismiss a request for a hearing when:
(1) The request is not received within the appropriate time frame provided in 106 CMR 343.140;
(2) The request is withdrawn either orally or in writing by the appellant or his or her authorized representative;
(3) The sole issue is one of state or federal law requiring automatic adjustments for classes of clients and the correctness of the grant computation is not at issue;
(4) The stated reason for the request is not grounds for appeal as defined in 106 CMR 343.230;
(5) The stated reason for the hearing request is outside the scope of 106 CMR 343.000; or
(6) The party requesting the hearing has no standing.
(B) The Director may schedule a hearing to allow the appellant the opportunity to contest the dismissal.
```

#### Rank 5 — PARTIAL (sim 0.454)

- **Chunk ID**: `cmr_sec_343_030__007`
- **Section**: `343.030` — Definitions
- **Chunk position**: 8 / 8
- **Program**: Hearings
- **Hierarchy**: (N) Timely Notice.
- **Judge reason**: Defines the timely notice period (10 days) and timely request window, but doesn't specify the overall deadline for requesting a fair hearing after an action occurs.

```
106 CMR 343 > FAIR HEARING RULES > 343.030 Definitions > (N) Timely Notice.

(N) Timely Notice. A timely notice shall be adequate notice which meets the requirements found in 106 CMR 343.140. Prior to an intended action to reduce, suspend or terminate assistance, the Department must send a timely notice to the client except as provided in 106 CMR 343.210 and 702.950: Inadequate or Incomplete Monthly Report. A timely notice is a notice mailed at least ten calendar days prior to the action. This is called the timely notice period.
(O) Timely Request. A timely request for a hearing is one received by DOH within the timely notice period.
```


### cmr_017 — IPV definition (rank-1: RELEVANT)

**Question**: What is an Intentional Program Violation  
**Program filter**: (none)  
**Expected section (for reference)**: `367.525` — judge picked rank-1 RELEVANT chunk in section `706.300` (section-author intuition disagrees with judge)  
**Notes**: 367.525 Definition of an Intentional Program Violation  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.508)

- **Chunk ID**: `cmr_sec_706_300__000`
- **Section**: `706.300` — Definition of an Intentional Program Violation (IPV)
- **Program**: EA
- **Judge reason**: The chunk directly defines Intentional Program Violation (IPV) with specific criteria, which directly answers the user's question.

```
106 CMR 706 > AUXILIARY > 706.300 Definition of an Intentional Program Violation (IPV)

An Intentional Program Violation (IPV) is any action by an individual for the purpose of establishing or maintaining eligibility or for increasing, or preventing a reduction in, the amount of the grant by intentionally:
(A) making a false or misleading statement or misrepresentation, either orally or in writing, concealing or withholding of facts from the Department; or
(B) taking any other act intended to mislead, misrepresent, conceal or withhold facts or to propound a falsity.
```

#### Rank 2 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_367_500__000`
- **Section**: `367.500` — Intentional Program Violation Claim
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Judge reason**: The chunk explains how intentional program violation claims are pursued but does not define what an intentional program violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.500 Intentional Program Violation Claim

A claim for overissuance shall be pursued as an intentional program violation claim if an Administrative Disqualification Hearing, or a court of appropriate jurisdiction, has found that a household member committed an intentional program violation, or if the individual has filed a signed waiver of his or her right to an Administrative Disqualification Hearing or entered into a consent agreement with the court. All claims established under the Food Stamp Act and future claims shall be collected in accordance with 106 CMR 367.500.
```

#### Rank 3 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_367_520__000`
- **Section**: `367.520` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: Program Integrity
- **Judge reason**: The chunk mentions what an ADH is used for (determining if an IPV was committed) but does not define what an Intentional Program Violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.520 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall conducted in order to determine if an intentional program violation (IPV) has been committed. An ADH shall be initiated by the Department if evidence exists to indicate an IPV was committed.
```

#### Rank 4 — PARTIAL (sim 0.497)

- **Chunk ID**: `cmr_sec_367_500__002`
- **Section**: `367.500` — Intentional Program Violation Claim
- **Chunk position**: 3 / 6
- **Program**: Program Integrity
- **Hierarchy**: (B) Collection of Intentional Program Violation Claim.
- **Judge reason**: The chunk describes collection procedures for intentional program violations but does not define what an intentional program violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.500 Intentional Program Violation Claim > (B) Collection of Intentional Program Violation Claim.

(B) Collection of Intentional Program Violation Claim.
(1) If the household member is found to have committed an intentional program violation at either an Administrative Disqualification Hearing or by a court of appropriate jurisdiction, or if the individual has entered into a consent agreement with the court or filed a signed waiver in accordance with 106 CMR 367.660, the Department shall send an IPV claim demand letter and a repayment agreement letter in accordance with 106 CMR 367.825 unless:
(a) the household has already repaid the claim;
(b) the Department has documentation which shows that no member of the household can be located; or
(c) the legal representative prosecuting a member of the household for intentional program violation advises in writing that collection action will prejudice the case.
(2) If the intentional program violation claim has not been repaid and a completed and acceptable signed repayment agreement letter has not been received by the Department within ten days of the date it was mailed, collection action shall be initiated by automatically reducing the household's benefit allotment each month. Any time benefits are automatically reduced due to an IPV, the allotment shall be reduced by 20% of the household's entitlement before sanctions, or $20, whichever is greater. Automatic benefit reduction shall continue until the claim is repaid. The acceptance of a completed and signed repayment agreement
```

#### Rank 5 — PARTIAL (sim 0.491)

- **Chunk ID**: `cmr_sec_706_310__000`
- **Section**: `706.310` — Warning to Applicants and Clients
- **Program**: EA
- **Judge reason**: The chunk mentions Intentional Program Violation and references penalties but does not define what an IPV actually is.

```
106 CMR 706 > AUXILIARY > 706.310 Warning to Applicants and Clients

At the time of application, the Department shall inform all applicants, in writing, of the disqualification penalties, in accordance with 106 CMR 706.305, for committing an Intentional Program Violation (IPV). The Department shall notify all current clients, in writing, of the IPV disqualification penalties, provided in 106 CMR 706.305.
```


### cmr_018 — SNAP IPV penalties (rank-1: RELEVANT)

**Question**: What are the disqualification penalties for SNAP fraud  
**Program filter**: (none)  
**Expected section (for reference)**: `367.800` — judge picked rank-1 RELEVANT chunk in section `367.800` (section-author intuition agrees)  
**Notes**: 367.800 Disqualification Penalties; 367 is Program Integrity for SNAP  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.582)

- **Chunk ID**: `cmr_sec_367_800__001`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 2 / 6
- **Program**: Program Integrity
- **Hierarchy**: (B) Disqualification for Receipt of Multiple SNAP Benefits.
- **Judge reason**: Directly addresses SNAP fraud disqualification penalties by specifying a 10-year ineligibility period for fraudulent statements regarding identity or residence to obtain multiple benefits.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties > (B) Disqualification for Receipt of Multiple SNAP Benefits.

(B) Disqualification for Receipt of Multiple SNAP Benefits. Individuals found by the Department or convicted by a federal, state or local court of having made a fraudulent statement or representation with respect to identity or place of residence to receive multiple benefits simultaneously under SNAP shall be ineligible for SNAP benefits for ten years.
```

#### Rank 2 — RELEVANT (sim 0.544)

- **Chunk ID**: `cmr_sec_367_800__000`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Disqualification for Intentional Program Violations.
- **Judge reason**: Directly specifies the disqualification penalties for SNAP fraud (IPV), including duration of ineligibility for first, second, and third violations.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties

(A) Disqualification for Intentional Program Violations.
(1) Individuals found to have committed a SNAP IPV at an ADH shall be ineligible for SNAP benefits for a period of one year for the first finding, two years for the second finding and permanently for the third finding.
(2) Individuals found to have committed a cash program IPV at an ADH, in the absence of a SNAP IPV under 106 CMR 367.800(A)(1), shall be ineligible for SNAP benefits for the period required under the cash program rules.
```

#### Rank 3 — PARTIAL (sim 0.537)

- **Chunk ID**: `cmr_sec_367_800__002`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 3 / 6
- **Program**: Program Integrity
- **Hierarchy**: (C) Disqualification for Trading SNAP Benefits.
- **Judge reason**: Addresses disqualification penalties for specific SNAP fraud violations (trading benefits) but does not comprehensively cover all types of SNAP fraud penalties that the user is asking about.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties > (C) Disqualification for Trading SNAP Benefits.

(C) Disqualification for Trading SNAP Benefits.
(1) Individuals found guilty by a federal, state or local court of trading (buying or selling) SNAP benefits for a controlled substance shall be ineligible for SNAP benefits for a period of two years for the first finding, and permanently for the second finding.
(2) Individuals found guilty by a federal, state or local court of trading (buying or selling) SNAP benefits for firearms, ammunition or explosives shall be ineligible for SNAP benefits permanently.
(3) Individuals found guilty by a federal, state or local court of trading (buying or selling) SNAP benefits having a value of $500 or more shall be ineligible for SNAP benefits permanently.
```

#### Rank 4 — PARTIAL (sim 0.486)

- **Chunk ID**: `cmr_sec_365_660__000`
- **Section**: `365.660` — Facility Penalties and Disqualifications
- **Program**: SNAP
- **Judge reason**: Addresses SNAP fraud penalties but only for organizations/institutions, not individual recipient disqualification penalties which is what the question asks about.

```
106 CMR 365 > SPECIAL > 365.660 Facility Penalties and Disqualifications

USDA may disqualify or penalize an organization or institution if it is determined administratively or judicially that SNAP benefits were misappropriated or used for purchases that did not contribute to a certified household's meals. The worker shall promptly notify SNAP Management, 600 Washington Street, Boston, MA 02111, when there is reason to believe that an organization or institution is misusing SNAP benefits in its possession. However, the Department shall not take any action against the organization or institution before USDA takes action.
```

#### Rank 5 — PARTIAL (sim 0.469)

- **Chunk ID**: `cmr_sec_361_370__002`
- **Section**: `361.370` — Documentation and Control of Authorized Representatives
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Hierarchy**: (C) The authorized representative is properly using the SNAP benefits.
- **Judge reason**: Addresses disqualification for authorized representatives who commit fraud, but does not cover disqualification penalties for individual SNAP recipients committing fraud.

```
106 CMR 361 > THE > 361.370 Documentation and Control of Authorized Representatives > (C) The authorized representative is properly using the SNAP benefits.

(C) The authorized representative is properly using the SNAP benefits. Except in cases of drug and alcohol treatment centers and group homes, the Department may disqualify the authorized representative from participating as an authorized representative for up to one year if the Department has obtained evidence that the authorized representative has misrepresented a household's circumstances and has knowingly provided false information about the household, or has made improper use of SNAP benefits. The Department shall notify the household and the authorized representative in writing 30 days before disqualification. The notice shall include the proposed action; the reason for the proposed action; the household's right to request a fair hearing; and the appropriate Department telephone number; and the name of the person to contact for additional information.
```


### cmr_019 — TAFDC vs EAEDC (rank-1: PARTIAL)

**Question**: What is the difference between TAFDC and EAEDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `701.200`  
**Notes**: 701.200 The TAFDC and EAEDC Programs  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.502)

- **Chunk ID**: `cmr_sec_701_200__002`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 3 / 3
- **Program**: EA
- **Hierarchy**: (4) encouraging teenage parents to live with their families or in supportive ...
- **Judge reason**: The chunk describes what EAEDC is but does not explain the differences between TAFDC and EAEDC programs.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.200 The TAFDC and EAEDC Programs > (4) encouraging teenage parents to live with their families or in supportive ...

(4) encouraging teenage parents to live with their families or in supportive living situations and obtain basic educational achievements. The Emergency Aid to the Elderly, Disabled and Children (EAEDC) Program provides financial assistance to qualified elderly and disabled persons, participants in MRC programs, and certain families who meet the program requirements. EAEDC is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 117A and other relevant statutes and the rules, regulations and policies. The authoritative text of the regulations is published by the Secretary of State of the Commonwealth of Massachusetts. Copies of the regulations are available to the public at the Department's area offices.
```

#### Rank 2 — PARTIAL (sim 0.490)

- **Chunk ID**: `cmr_sec_701_050__000`
- **Section**: `701.050` — Transitional Cash Assistance Programs Overview
- **Program**: EA
- **Judge reason**: The chunk identifies both programs and indicates they have different eligibility policies, but does not explain the actual differences between TAFDC and EAEDC.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.050 Transitional Cash Assistance Programs Overview

The policies described in this chapter are the basis for the administration and function of both the Transitional Aid to Families with Dependent Children (TAFDC) and Emergency Aid to the Elderly, Disabled and Children (EAEDC) programs; specific eligibility policies for TAFDC and EAEDC are found in 106 CMR 703.000: Nonfinancial Eligibility and 704.000: Financial Eligibility.
```

#### Rank 3 — PARTIAL (sim 0.488)

- **Chunk ID**: `cmr_sec_701_200__000`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk describes TAFDC but does not provide information about EAEDC or explain the differences between the two programs.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.200 The TAFDC and EAEDC Programs

The Transitional Aid to Families with Dependent Children (TAFDC) program provides financial assistance and employment-related services to families with dependent children. The TAFDC program is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 118 and other relevant statutes and the rules, regulations and policies. TAFDC regulations implement St. 1995, c. 5. TAFDC seeks to integrate clients into the work force and break the cycle of poverty. The major program objectives include:
```

#### Rank 4 — PARTIAL (sim 0.483)

- **Chunk ID**: `cmr_sec_706_400__003`
- **Section**: `706.400` — Delivery of Benefits
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (D) Minimum Monthly Payment.
- **Judge reason**: The chunk mentions both TAFDC and EAEDC but only addresses one specific difference (minimum monthly payment amounts) rather than explaining the fundamental differences between the two programs.

```
106 CMR 706 > AUXILIARY > 706.400 Delivery of Benefits > (D) Minimum Monthly Payment.

(D) Minimum Monthly Payment. The smallest monthly grant paid for TAFDC is $10. The smallest monthly grant paid for EAEDC is $2. If the grant amount is greater than zero, but less than the smallest monthly grant paid for the cash program, the grantee is considered to be receiving assistance, but will not receive a monthly payment.
```

#### Rank 5 — PARTIAL (sim 0.479)

- **Chunk ID**: `cmr_sec_701_110__000`
- **Section**: `701.110` — Limitation on Program Eligibility
- **Program**: EA
- **Judge reason**: The chunk mentions both TAFDC and EAEDC and notes they are mutually exclusive programs, but does not explain the substantive differences between them (e.g., eligibility criteria, who each serves, benefit amounts).

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.110 Limitation on Program Eligibility

(A) TAFDC and EAEDC-family clients may receive MassHealth and SNAP benefits while on TAFDC or EAEDC. Any individual who is a TAFDC client is not concurrently eligible for EAEDC, Supplemental Security Income (SSI), State Supplement Program (SSP) to the Supplemental Security Income or State Veterans Services Benefits (VSB). Any individual who is an EAEDC client is not concurrently eligible for TAFDC, SSI, SSP or SVSB.
(B) An individual is ineligible for TAFDC if he or she:
(1) is fleeing to avoid prosecution, custody or confinement after conviction, under the laws of the place from which the individual flees, for a crime or an attempt to commit a crime, on or after September 26, 1996, which is a felony under the laws of the place from which the individual flees, or which, in the state of New Jersey, is a high misdemeanor under the laws of such state; or
(2) is violating a condition of probation or parole imposed on or after September 26, 1996 under federal or state law.
(C) An individual is ineligible for TAFDC and EAEDC if he or she has an outstanding default or arrest warrant against him or her issued by any court of the Commonwealth of Massachusetts.
```


### cmr_020 — TAFDC 24-month limit (rank-1: RELEVANT)

**Question**: How are TAFDC time-limited benefits applied  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.120` — judge picked rank-1 RELEVANT chunk in section `703.120` (section-author intuition agrees)  
**Notes**: 703.120 TAFDC Time-limited Benefits  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.502)

- **Chunk ID**: `cmr_sec_703_120__000`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) A nonexempt grantee, including each grantee in a two-parent family, who i...
- **Judge reason**: The chunk directly explains how TAFDC time-limited benefits are applied, including the 24-month cumulative limit in a 60-month period and the conditions that affect this calculation.

```
106 CMR 703 > NONFINANCIAL > 703.120 TAFDC Time-limited Benefits

(A) A nonexempt grantee, including each grantee in a two-parent family, who is receiving TAFDC or who would be receiving TAFDC but for a TAFDC sanction, may only receive TAFDC for a maximum of a cumulative 24 months in a continuous 60-month period. The ineligibility shall apply to all members of the assistance unit.
(1) The initial continuous 60-month period begins on the date an assistance unit first becomes eligible for TAFDC. The maximum cumulative 24-month period in a continuous 60-month period begins on the date that an exempt grantee becomes nonexempt, or the date a nonexempt grantee first becomes eligible for TAFDC, whichever is later.
(2) An assistance unit shall be considered to be receiving TAFDC if it:
(a) receives a TAFDC grant;
(b) has a grantee participating in the Full Employment Program or supported work; or
(c) receives TAFDC benefits through vendor payments.
(3) The calculation of a nonexempt grantee’s cumulative 24-month period shall stop when:
(a) the entire assistance unit is ineligible, including ineligibility as the result of a sanction;
(b) the grantee becomes exempt as specified in 106 CMR 703.100; or
(c) the assistance unit voluntarily withdraws from TAFDC. The calculation of the cumulative 24-month period resumes when the grantee becomes nonexempt in the same continuous 60-month period.
```

#### Rank 2 — PARTIAL (sim 0.496)

- **Chunk ID**: `cmr_sec_703_120__002`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (B) Exception.
- **Judge reason**: The chunk discusses exceptions to time-limited benefits for teen parents but does not explain how time-limited benefits are actually applied in general.

```
106 CMR 703 > NONFINANCIAL > 703.120 TAFDC Time-limited Benefits > (B) Exception.

(B) Exception.
(1) A teen parent (see 106 CMR 703.180) who received assistance as a member of another TAFDC assistance unit may reapply for TAFDC, if he or she meets the teen parent requirements found at 106 CMR 703.180, and:
(a) he or she is not eligible to be included in another assistance unit; or
(b) the other TAFDC case is closed.
(2) At the time of the reapplication, the worker shall determine if the teen parent meets an exemption specified in 106 CMR 703.100, and:
(a) if the teen parent meets an exemption, the assistance unit will be exempt from the time-limited benefits defined in 106 CMR 703.120(A); or
(b) if the teen parent does not meet an exemption, the teen parent is nonexempt and the time-limited benefits defined in 106 CMR 703.120(A) will apply.
```

#### Rank 3 — RELEVANT (sim 0.484)

- **Chunk ID**: `cmr_sec_703_120__001`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (A) A nonexempt grantee, including each grantee in a two-parent family, who i...
- **Judge reason**: The chunk directly explains how TAFDC time-limited benefits are applied through cumulative 24-month periods, continuous 60-month periods, and specific rules for calculating and stopping these periods.

```
106 CMR 703 > NONFINANCIAL > 703.120 TAFDC Time-limited Benefits > (A) A nonexempt grantee, including each grantee in a two-parent family, who i...

(4) A nonexempt grantee’s cumulative 24-month period is not stopped when there is a sanction period imposed on a member of the assistance unit, except as specified in 106 CMR 703.120(A)(3)(a).
(5) The calculation of the 60-month period cannot be stopped.
(6) If aid to the assistance unit has been terminated because of the end of the cumulative 24- month period, the assistance unit may establish eligibility for TAFDC before the end of the continuous 60-month period if the grantee meets an exemption found at 106 CMR 703.100.
(7) At the end of a continuous 60-month period, a nonexempt grantee may reapply for TAFDC and begin a new cumulative 24-month eligibility period and a new continuous 60- month period.
(8) In a two-parent household, both parents shall have the same 60-month period. If, because of a prior period of assistance, both parents do not share the same start date of their 60-month period, the earliest date shall apply to the household.
```

#### Rank 4 — PARTIAL (sim 0.480)

- **Chunk ID**: `cmr_sec_701_600__016`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 17 / 25
- **Program**: EA
- **Hierarchy**: (CC) Nonexempt Assistance Unit - TAFDC.
- **Judge reason**: Defines what a nonexempt assistance unit is and references time-limited benefits, but doesn't explain how time-limited benefits are actually applied.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (CC) Nonexempt Assistance Unit - TAFDC.

(CC) Nonexempt Assistance Unit - TAFDC. An assistance unit which does not meet the requirements of 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits and is subject to Time-limited Benefits and the Work Program requirements. Manual Reference: 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits.
```

#### Rank 5 — PARTIAL (sim 0.470)

- **Chunk ID**: `cmr_sec_703_130__000`
- **Section**: `703.130` — TAFDC Extension of Benefits Beyond the 24-month Period
- **Chunk position**: 1 / 5
- **Program**: EA
- **Judge reason**: Addresses extensions beyond the 24-month period but doesn't explain how time-limited benefits are initially applied or calculated.

```
106 CMR 703 > NONFINANCIAL > 703.130 TAFDC Extension of Benefits Beyond the 24-month Period

The Commissioner or designee may extend benefits beyond the 24-month period under certain circumstances. A nonexempt grantee granted an extension must meet all other program requirements. Requests for extensions will be reviewed and determined on a case-by-case basis. Granted extensions may be reviewed and revised as the Commissioner or designee deems appropriate. An individual may request an extension of benefits beyond the 24-month period after a nonexempt grantee has used 22 months of time-limited benefits, or at any time when an individual has already received 24 months of time-limited benefits.
```


### cmr_021 — TAFDC work program (rank-1: RELEVANT)

**Question**: What are the TAFDC work program requirements  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.150` — judge picked rank-1 RELEVANT chunk in section `703.150` (section-author intuition agrees)  
**Notes**: 703.150 TAFDC Work Program; was a persistent miss in v1  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.556)

- **Chunk ID**: `cmr_sec_703_150__001`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 2 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly outlines the specific work program requirements for TAFDC nonexempt grantees, including employment hours, approved activities, and participation options.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program > (A) Requirements.

(2) A nonexempt grantee meets the Work Program requirements by:
(a) working in a job for pay for at least the required hours per week as specified in 106 CMR 703.150(A)(5);
(b) working full-time in the Full Employment Program (FEP) (see 106 CMR 707.180: Full Employment Program) or participating in an approved Supported Work Program (see 106 CMR 707.160: Supported Work Component);
(c) participating in community service, job search or another Department approved activity that is expected to result in employment for the required hours per week as specified in 106 CMR 703.150(A)(5). The maximum number of hours a grantee can participate in a community service program is limited by the federal Fair Labor Standards Act (FLSA). A grantee who cannot meet the required hours of participation through community service alone due to the FLSA must participate in an additional allowable work activity so that the required hours are met. If the grantee cannot identify an allowable work activity, the Department shall provide a referral to an activity;
(d) combining the hours of work, other approved work program activities and community service hours to total the required hours per week as specified in 106 CMR 703.150(A)(5). The number of hours of community service and/or other work program activities required each week will be the difference between the required hours per week and the number of hours worked;
(e) participating in a substance abuse treatment program while in a substance abuse
```

#### Rank 2 — RELEVANT (sim 0.541)

- **Chunk ID**: `cmr_sec_703_150__002`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 3 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly lists specific work program requirements and activities that TAFDC participants must engage in to meet their work obligations.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program > (A) Requirements.

shelter;
(f) participating in an unpaid work study or internship program for the required hours per week;
(g) providing child care to a teen parent’s dependent child (both of whom are living in the grantee’s home) enabling the teen parent to meet the school attendance requirements;
(h) participating in a Department-approved supported work program with a commitment from the employer to hire participants who successfully complete the program;
(i) participating in an education or training activity including a certificate or degree program from a four-year degree-granting higher education institute, community college or a certificate program (up to a bachelor’s degree) for up to the required hours per week as specified in 106 CMR 703.150(A)(5). If the education or training activity is less than the required hours per week, the grantee must participate in other work program activities to meet the required hours. For purposes of meeting the work program requirement, an education or training activity cannot exceed 24 months. The Department may extend this period if the client is making substantial progress towards completion of the certificate or degree program;
(j) participating in a vocational educational program not to exceed 12 months. The Department may extend this period if the client is making substantial progress towards completion of the certificate or degree program in vocational education; or
```

#### Rank 3 — RELEVANT (sim 0.522)

- **Chunk ID**: `cmr_sec_703_150__000`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 1 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: This chunk directly outlines the core TAFDC work program requirements, including the 60-day threshold, required weekly hours, exemptions, and special circumstances for foster care situations.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program

(A) Requirements.
(1) A grantee who has received assistance for 60 days must work the required hours per week as specified in 106 CMR 703.150(A)(5), unless:
(a) the grantee is exempt (see 106 CMR 703.100);
(b) the grantee is caring for a foster child in the home who is younger than two years old;
(c) a grantee is caring for a foster child in the home whose needs exceed a standard level of care (DCF tiers 2, 3 and 4) as determined by the DCF Commissioner or designee. A waiver of Work Program requirements may be granted by the DTA Commissioner for other foster parent grantees at the request of the DCF Commissioner based on the needs of the foster child; or
(d) the grantee has good cause as specified in 106 CMR 701.380: Good Cause Criteria. In a two-parent household, each parent shall meet the Work Program requirements for the required hours per week as specified in 106 CMR 703.150(A)(5), unless that parent meets the requirements of 106 CMR 703.150(A)(1). If 106 CMR 703.150(A)(1)(b) and (c) apply, however, the work program requirement must still be met by one parent.
```

#### Rank 4 — RELEVANT (sim 0.520)

- **Chunk ID**: `cmr_sec_703_150__003`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 4 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly outlines TAFDC Work Program requirements including the 60-day initial period, employment/FEP participation, Community Service Program participation, and exemptions for categorically ineligible noncitizens.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program > (A) Requirements.

(k) if residing in an emergency shelter, meeting his or her housing search requirements. A grantee is given an initial period of up to 60 days to meet the Work Program requirement. During this period, the grantee must seek employment or find employment through FEP. A grantee who does not meet the Work Program requirements as defined in 106 CMR 703.150(A)(2) within the 60 days must participate in the Community Service Program, unless participating in FEP.
(3) A categorically ineligible noncitizen who is unable to work in a paying job because of his or her noncitizen status, must participate in the Community Service program for the required hours per week, unless the grantee:
(a) meets another exemption (see 106 CMR 703.100);
(b) is caring for a foster child in the home who is younger than two years old;
(c) is caring for a foster child in the home whose needs exceed a standard level of care (DCF tiers 2, 3 and 4) as determined by the DCF Commissioner or his or her designee. A waiver of work requirements may be given for other foster parent grantees at the request of the DCF Commissioner based on the needs of the foster child; or
(d) has good cause (see 106 CMR 701.380: Good Cause Criteria). The individual shall be given an initial period of up to 60 days to find a Community Service placement. If the individual does not begin a Community Service placement within the 60 days, he or she shall be mandated to participate in Community Service.
```

#### Rank 5 — RELEVANT (sim 0.513)

- **Chunk ID**: `cmr_sec_703_150__004`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 5 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly addresses TAFDC work program requirements by specifying required work hours per week based on the age of the youngest child in the assistance unit and reapplication rules.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program > (A) Requirements.

(4) At Reapplication. If a grantee reapplies for assistance any time within a continuous 60- month period, the grantee, unless otherwise exempt, must meet the Work Program requirements to be eligible for assistance. The grantee will not receive another 60-day period to look for work. If the 60-month period has expired when the grantee reapplies for assistance, the grantee, unless otherwise exempt, will receive another 60-day period to look for work before having to meet the Work Program requirement.
(5) For purposes of 106 CMR 703.150(A), the required hours per week are defined as:
(a) 20 hours, if the youngest child in the assistance unit (or who is not in the assistance unit as defined in 106 CMR 704.305(A)(5)(a), (b), or (c)) is between two and six years of age (see 106 CMR 701.600: Definition of Terms); and
(b) 30 hours, if the youngest child in the assistance unit (or who is not in the assistance unit as defined in 106 CMR 704.305(A)(5)(a), (b), or (c)) is six years of age or older. In a two-parent household where both parents are work program required, each parent must meet the required hours per week based on the age of the youngest child in the assistance unit (or who is not in the assistance unit in accordance with 106 CMR 704.305(A)(5)(a), (b), or (c))
```


### cmr_022 — TAFDC asset limit (rank-1: PARTIAL)

**Question**: What is the asset limit for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `704.110`  
**Notes**: 704.110 Asset Limitations  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.20  

#### Rank 1 — PARTIAL (sim 0.503)

- **Chunk ID**: `cmr_sec_707_180__003`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (D) Impact on TAFDC Benefits.
- **Judge reason**: The chunk mentions asset-related rules for TAFDC but addresses only Individual Asset Accounts in FEP employment, not the general asset limit for TAFDC eligibility.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.180 Full Employment Program > (D) Impact on TAFDC Benefits.

(D) Impact on TAFDC Benefits.
(1) The assistance unit shall receive a supplemental payment when the FEP gross income less 20% and less the allowable dependent care deduction as provided in 106 CMR 704.275: Dependent Care Deduction, is less than the TAFDC benefit that the assistance unit would have received, based on the size of the assistance unit and any other income. The amount of the supplemental payment is the result of the above calculation.
(2) The Individual Asset Account established for the participant is a noncountable asset for TAFDC until the participant receives the funds from the account after leaving FEP employment.
```

#### Rank 2 — PARTIAL (sim 0.480)

- **Chunk ID**: `cmr_sec_704_135__007`
- **Section**: `704.135` — Transfers of lIncome and/or Assets
- **Chunk position**: 8 / 8
- **Program**: EA
- **Hierarchy**: (E) Ineligibility for Transitional Cash Assistance.
- **Judge reason**: The chunk discusses TAFDC ineligibility due to asset transfers but does not specify the actual asset limit amount for TAFDC eligibility.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.135 Transfers of lIncome and/or Assets > (E) Ineligibility for Transitional Cash Assistance.

(E) Ineligibility for Transitional Cash Assistance. Any member of the filing unit who is determined to be ineligible for EAEDC due to the transfer of income or assets is concurrently ineligible for TAFDC. Conversely, any member of the filing unit who is determined to be ineligible for TAFDC due to the transfer of income or assets is concurrently ineligible for EAEDC. | RREENNTT OORR MMOORRTTGGAAGGEE | UUnnhheeaatteedd FFaacciilliittyy | $$110022..0000 | | --- | --- | --- | |  | HHeeaatteedd FFaacciilliittyy | 112266..3300 | | FFUUEELL |  | 2277..9900 | | UUTTIILLIITTIIEESS |  | 1188..6600 | | FFOOOODD ((IInnddiivviidduuaall)) |  | 4411..8800 |
```

#### Rank 3 — PARTIAL (sim 0.462)

- **Chunk ID**: `cmr_sec_704_260__000`
- **Section**: `704.260` — TAFDC Income Test of Eligibility
- **Program**: EA
- **Judge reason**: This chunk addresses TAFDC income eligibility but does not contain information about asset limits, which is what the user specifically asked about.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.260 TAFDC Income Test of Eligibility

(A) Financial eligibility for TAFDC is determined at application, eligibility reviews and when a change in income is reported. Filing units whose total countable income as defined in 106 CMR 704.210 does not exceed the applicable Need Standard for the exempt or nonexempt assistance unit found at 106 CMR 704.400 and 106 CMR 704.405, respectively, are eligible.
(B) Test of Financial Eligibility.
(1) The total income of the filing unit, excluding:
(a) the types of noncountable income as provided in 106 CMR 704.250;
(b) the wages received from the Full Employment Program; and
(c) the disregarded income as provided in 106 CMR 704.270, 106 CMR 704.275, 106 CMR 704.280 and 106 CMR 704.281 lmay not exceed the applicable Need Standard in any month.
(2) If the filing unit's income is over the appropriate Need Standard, the assistance unit is ineligible. If the filing unit's income is equal to or is less than the appropriate Need Standard, the assistance unit is eligible.
```

#### Rank 4 — IRRELEVANT (sim 0.455)

- **Chunk ID**: `cmr_sec_702_105__000`
- **Section**: `702.105` — Case Management Requirements for the TAFDC Program
- **Program**: EA
- **Judge reason**: The chunk describes case management requirements and summary information that must be provided to clients, but does not contain any information about asset limits for TAFDC.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.105 Case Management Requirements for the TAFDC Program

The Department shall provide a written or verbal summary of the regulations and requirements for the TAFDC program. This summary shall include, but is not limited to, information about:
(1) time limits for assistance;
(2) fraud penalties;
(3) school attendance requirements;
(4) immunization requirements; and
(5) protective payments for rent or utilities.
```

#### Rank 5 — PARTIAL (sim 0.454)

- **Chunk ID**: `cmr_sec_703_120__000`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) A nonexempt grantee, including each grantee in a two-parent family, who i...
- **Judge reason**: The chunk discusses TAFDC time limits and eligibility rules but does not address asset limits, which is what the user is asking about.

```
106 CMR 703 > NONFINANCIAL > 703.120 TAFDC Time-limited Benefits

(A) A nonexempt grantee, including each grantee in a two-parent family, who is receiving TAFDC or who would be receiving TAFDC but for a TAFDC sanction, may only receive TAFDC for a maximum of a cumulative 24 months in a continuous 60-month period. The ineligibility shall apply to all members of the assistance unit.
(1) The initial continuous 60-month period begins on the date an assistance unit first becomes eligible for TAFDC. The maximum cumulative 24-month period in a continuous 60-month period begins on the date that an exempt grantee becomes nonexempt, or the date a nonexempt grantee first becomes eligible for TAFDC, whichever is later.
(2) An assistance unit shall be considered to be receiving TAFDC if it:
(a) receives a TAFDC grant;
(b) has a grantee participating in the Full Employment Program or supported work; or
(c) receives TAFDC benefits through vendor payments.
(3) The calculation of a nonexempt grantee’s cumulative 24-month period shall stop when:
(a) the entire assistance unit is ineligible, including ineligibility as the result of a sanction;
(b) the grantee becomes exempt as specified in 106 CMR 703.100; or
(c) the assistance unit voluntarily withdraws from TAFDC. The calculation of the cumulative 24-month period resumes when the grantee becomes nonexempt in the same continuous 60-month period.
```


### cmr_023 — EAEDC disability (rank-1: PARTIAL)

**Question**: What is EAEDC disability and how is it determined  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.190`  
**Notes**: 703.190 EAEDC Disability  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.45  

#### Rank 1 — PARTIAL (sim 0.489)

- **Chunk ID**: `cmr_sec_703_191__005`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 6 / 11
- **Program**: EA
- **Hierarchy**: (E) The Department’s agent shall make the determination of disability for EAE...
- **Judge reason**: The chunk describes the disability determination process and procedures for EAEDC but does not explain what EAEDC disability is or the specific criteria/standards used to determine it.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process > (E) The Department’s agent shall make the determination of disability for EAE...

(4) the applicant or client verifies that he or she is eligible for SSI or SSDI or considered disabled for purposes of SSI or SSDI (see 106 CMR 703.191(A)(2)).
(F) If a disability determination by the Department’s agent is:
(1) required and the competent medical authority states that the applicant or client meets a medical standard, SSI Listing of Impairments, or has an impairment affecting his or her ability to work, and if otherwise eligible, the applicant or client shall receive EAEDC benefits pending a review by the Department’s agent; or
(2) not required because of 106 CMR 703.191(E), the EAEDC applicant or client shall be considered disabled upon giving the Department the necessary medical report or verifications and shall receive EAEDC benefits if otherwise eligible.
```

#### Rank 2 — PARTIAL (sim 0.467)

- **Chunk ID**: `cmr_sec_703_191__002`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 3 / 11
- **Program**: EA
- **Hierarchy**: (B) An EAEDC applicant or client must apply for SSI and cooperate in the SSI ...
- **Judge reason**: The chunk addresses EAEDC disability verification requirements and references the definition in 703.191(A)(1), but does not actually provide the definition or explain how disability is determined.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process > (B) An EAEDC applicant or client must apply for SSI and cooperate in the SSI ...

(B) An EAEDC applicant or client must apply for SSI and cooperate in the SSI application and/or appeal process when required by the Department or the Department’s agent.
(C) An EAEDC client must submit verifications at times determined by the Department and/or the Department’s agent of his or her:
(1) disability as defined in 106 CMR 703.191(A)(1) from a competent medical authority as defined in 106 CMR 701.600: Definition of Terms; or
(2) being determined disabled for purposes of SSI or SSDI as specified in 106 CMR 703.191(A)(2).
```

#### Rank 3 — PARTIAL (sim 0.461)

- **Chunk ID**: `cmr_sec_703_191__001`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 2 / 11
- **Program**: EA
- **Hierarchy**: (A) An EAEDC applicant or client younger than 65 years old is disabled if he ...
- **Judge reason**: The chunk shows one criterion for EAEDC disability determination (SSA/administrative law judge notification) but is incomplete and doesn't explain the full definition or all methods for determining disability.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process > (A) An EAEDC applicant or client younger than 65 years old is disabled if he ...

(2) has written notification from SSA or an administrative law judge that he or she is considered disabled for purposes of SSI or SSDI and/or that he or she is eligible for SSI or SSDI. However, this provision does not apply to those who are not currently receiving SSI or SSDI payments due to the recoupment of an overpayment by SSA. Such person is not eligible for EAEDC.
```

#### Rank 4 — PARTIAL (sim 0.461)

- **Chunk ID**: `cmr_sec_703_191__004`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 5 / 11
- **Program**: EA
- **Hierarchy**: (E) The Department’s agent shall make the determination of disability for EAE...
- **Judge reason**: The chunk describes the disability determination process and who makes the determination, but does not explain what EAEDC disability is or provide the actual medical standards/criteria used to determine it.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process > (E) The Department’s agent shall make the determination of disability for EAE...

(E) The Department’s agent shall make the determination of disability for EAEDC eligibility except when:
(1) a competent medical authority as defined in 106 CMR 701.600: Definition of Terms verifies that the applicant or client has an impairment or combination of impairments that:
(a) is expected to last at least 60 days but not more than 90 days; and
(b) meets or is equivalent to a medical standard defined in 106 CMR 703.192 or impairment included in the SSI Listing of Impairments.
(2) the applicant’s or client’s medical report is not completed by a competent medical authority, is not completed within 30 days of filing with the Department, or is not based on an examination conducted within 30 days from completion as required by l06 CMR 703.191(D);
(3) a competent medical authority verifies that the EAEDC applicant or client does not have an impairment that affects his or her ability to work and/or that the applicant’s or client’s impairment or combination of impairments is not expected to last for 60 days or more; or
```

#### Rank 5 — RELEVANT (sim 0.440)

- **Chunk ID**: `cmr_sec_703_191__000`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 1 / 11
- **Program**: EA
- **Hierarchy**: (A) An EAEDC applicant or client younger than 65 years old is disabled if he ...
- **Judge reason**: The chunk directly defines EAEDC disability and explains the three main criteria used to determine it: meeting Department standards, matching SSI Listing of Impairments, or substantially reducing ability to support oneself based on vocational factors.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process

(A) An EAEDC applicant or client younger than 65 years old is disabled if he or she has an impairment or combination of impairments that is expected to last 60 days or more and that substantially reduces or eliminates the applicant’s or client’s ability to support himself or herself. An applicant or client shall be considered as having such an impairment or combination of impairments if he or she:
(1) has an impairment or combination of impairments verified by a competent medical authority as defined in 106 CMR 701.600: Definition of Terms, on a medical report prescribed by the Department, which meets the requirements of 106 CMR 703.191(D). The competent medical authority and the agency or organization under contract/agreement with the Department to provide disability evaluation services (hereafter referred to as the Department’s agent), when required, determines that the impairment:
(a) meets a standard as specified in 106 CMR 703.192;
(b) is included in the SSI Listing of Impairments as specified in 20 CFR, Part 404, Subpart P, Appendix 1; or
(c) substantially reduces or eliminates the applicant’s or client’s ability to support himself or herself when consideration is given to the vocational factors as specified in 106 CMR 703.193; or
```


### cmr_024 — ESP overview (rank-1: RELEVANT)

**Question**: What is the Employment Services Program  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `707.100` — judge picked rank-1 RELEVANT chunk in section `707.120` (section-author intuition disagrees with judge)  
**Notes**: 707.100 Introduction to ESP/Orientation  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.478)

- **Chunk ID**: `cmr_sec_707_120__000`
- **Section**: `707.120` — Employment Services Program (ESP) Participation Components
- **Program**: EA
- **Judge reason**: The chunk directly defines the Employment Services Program (ESP) and describes its participation components, structure, and requirements, which directly answers the user's question about what the ESP is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.120 Employment Services Program (ESP) Participation Components

106 CMR 707.130 through 707.190 describe the ESP component activities. Participation in a component is subject to available program resources and the individual's approved Employment Development Plan (EDP). Each individual who completes an EDP must fulfill the activities on the EDP in accordance with 106 CMR 707.110. ESP participation may include self-initiated educational, vocational, or training programs, not funded by ESP provided the programs are consistent with 106 CMR 707.000 through 106 CMR 707.190 and individual's approved EDP. The individual must meet the Department's participation requirements, including, but not limited to, minimum scheduled hours and attendance requirements established for each ESP component, and the individual must complete the programs in accordance with time frames established by the Department, if any, for a particular component. The individual must be making satisfactory progress in the component, as defined by the service provider. An ESP participant in a self-initiated program who meets the above requirements shall be eligible for ESP Support Services in accordance with 106 CMR 707.210.
```

#### Rank 2 — PARTIAL (sim 0.472)

- **Chunk ID**: `cmr_sec_707_115__000`
- **Section**: `707.115` — Program Participation
- **Program**: EA
- **Judge reason**: The chunk describes program participation requirements for ESP but does not define what the Employment Services Program actually is or its purpose.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.115 Program Participation

Except as described in 106 CMR 707.170, 707.180 and 707.185, participation in the Employment Services Program (ESP) shall be subject to the requirements in 106 CMR 707.115 and available program resources.
(A) An individual who participates in ESP must:
(1) attend a program orientation;
(2) attend an initial assessment interview;
(3) assist in the developmentof his or her Employment Development Plan (EDP);
(4) attend reassessment interviews, when required;
(5) schedule the minimum hours of participation required for each ESP component activity;
(6) attend the scheduled hours of his or her ESP component activity, unless good cause exists as defined by 106 CMR 701.380: Good Cause Criteria; and
(7) unless otherwise specified, provide verification of participation at time periods determined by the Department on a form prescribed by the Department. These forms must be signed under the penalties of perjury by providers of the ESP component activity(ies).
```

#### Rank 3 — PARTIAL (sim 0.472)

- **Chunk ID**: `cmr_sec_707_140__000`
- **Section**: `707.140` — Educational Component
- **Chunk position**: 1 / 5
- **Program**: EA
- **Judge reason**: Describes a specific component (Educational Component) of the Employment Services Program rather than defining what the overall Employment Services Program is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.140 Educational Component

The Educational Component provides educational services to individuals to prepare him or her to obtain and maintain employment. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP), and the criteria in 106 CMR 707.140(A) through (D):
```

#### Rank 4 — PARTIAL (sim 0.471)

- **Chunk ID**: `cmr_sec_707_185__000`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 1 / 4
- **Program**: EA
- **Judge reason**: Describes a specific component (Post-employment Services) of the Employment Services Program rather than defining what the overall Employment Services Program is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.185 Post-employment Services Component

The Post-employment Services component is a voluntary program which provides current and former clients with services that lead to career advancement and employment stability. Participation is subject to the requirements provided in this regulation and depends on available funding and resources. The Department shall determine eligibility for and authorize Post-employment Services. Post-employment Services may only be provided by provider agencies under contract with the Department, and services may vary by provider.
```

#### Rank 5 — PARTIAL (sim 0.465)

- **Chunk ID**: `cmr_sec_707_110__000`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 1 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk describes procedures for completing an Employment Development Plan within the ESP program but does not define what the Employment Services Program itself is or its overall purpose and structure.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.110 Completion of an Employment Development Plan (EDP)

(A) Developing an EDP.
(1) An EDP will be completed every year for:
(a) a grantee who the Department determines must participate in an Employment Services Program (ESP) component because there are available component slots;
(b) a grantee who volunteers to participate in ESP;
(c) all teen parents who have not graduated from high school or do not have a HiSET certificate;
(d) a grantee needing support services to work or to participate in ESP or in a self- initiated program not funded by ESP as provided in 106 CMR 707.120;
(e) a dependent child 16 or 17 years of age who is not in school and must participate in the ESP Educational Component;
(f) a grantee or an ineligible grantee specified in 106 CMR 703.150(A)(2) referred to community service who:
1. volunteers to participate in community service;
2. is mandated to participate in community service because he or she did not meet the participation requirements of another ESP component; or
3. needs support services to participate in community service;
(g) a grantee participating in the Full Employment Program; and
(h) any other grantee who the Department determines needs an EDP.
```


### cmr_025 — FEP overview (rank-1: RELEVANT)

**Question**: What is the Full Employment Program for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `708` — judge picked rank-1 RELEVANT chunk in section `707.180` (section-author intuition disagrees with judge)  
**Notes**: BROAD — chapter 708 generally (only 7 sections, all about FEP)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.567)

- **Chunk ID**: `cmr_sec_707_180__000`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) Activities. Activities in FEP include:
- **Judge reason**: Directly defines the Full Employment Program for TAFDC, explaining its purpose, how participants are compensated, and the activities involved.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.180 Full Employment Program

The Full Employment Program (FEP) component provides individuals work experience needed to obtain an unsubsidized job. Participants are paid a subsidized wage in lieu of receiving TAFDC.
(A) Activities. Activities in FEP include:
(1) full-time employment of 35 to 40 hours per week consistent with the employer's schedule; and
(2) completion of an Employment Development Plan (EDP) as provided in 106 CMR 707.110.
```

#### Rank 2 — RELEVANT (sim 0.542)

- **Chunk ID**: `cmr_sec_708_000__000`
- **Section**: `708.000` — Overview
- **Program**: EA
- **Judge reason**: Directly defines the Full Employment Program for TAFDC, explaining its purpose, how clients participate, and the benefits/wages they receive.

```
106 CMR 708 > FULL EMPLOYMENT > 708.000 Overview

The Full Employment Program (FEP) component provides clients with paid work experience and on-the-job training needed to obtain an unsubsidized job. Clients participating in the Full Employment Program (FEP) will receive a subsidized wage in lieu of TAFDC cash benefits and are subject to FEP criteria in accordance with 106 CMR 707.180: Full Employment Program.
```

#### Rank 3 — PARTIAL (sim 0.523)

- **Chunk ID**: `cmr_sec_703_150__001`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 2 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk mentions the Full Employment Program (FEP) as an option for meeting TAFDC work requirements but only references it and directs to 106 CMR 707.180 for actual details, rather than explaining what the FEP is.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program > (A) Requirements.

(2) A nonexempt grantee meets the Work Program requirements by:
(a) working in a job for pay for at least the required hours per week as specified in 106 CMR 703.150(A)(5);
(b) working full-time in the Full Employment Program (FEP) (see 106 CMR 707.180: Full Employment Program) or participating in an approved Supported Work Program (see 106 CMR 707.160: Supported Work Component);
(c) participating in community service, job search or another Department approved activity that is expected to result in employment for the required hours per week as specified in 106 CMR 703.150(A)(5). The maximum number of hours a grantee can participate in a community service program is limited by the federal Fair Labor Standards Act (FLSA). A grantee who cannot meet the required hours of participation through community service alone due to the FLSA must participate in an additional allowable work activity so that the required hours are met. If the grantee cannot identify an allowable work activity, the Department shall provide a referral to an activity;
(d) combining the hours of work, other approved work program activities and community service hours to total the required hours per week as specified in 106 CMR 703.150(A)(5). The number of hours of community service and/or other work program activities required each week will be the difference between the required hours per week and the number of hours worked;
(e) participating in a substance abuse treatment program while in a substance abuse
```

#### Rank 4 — PARTIAL (sim 0.523)

- **Chunk ID**: `cmr_sec_707_180__003`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (D) Impact on TAFDC Benefits.
- **Judge reason**: The chunk addresses how FEP impacts TAFDC benefits but does not explain what the Full Employment Program itself is or its core purpose and requirements.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.180 Full Employment Program > (D) Impact on TAFDC Benefits.

(D) Impact on TAFDC Benefits.
(1) The assistance unit shall receive a supplemental payment when the FEP gross income less 20% and less the allowable dependent care deduction as provided in 106 CMR 704.275: Dependent Care Deduction, is less than the TAFDC benefit that the assistance unit would have received, based on the size of the assistance unit and any other income. The amount of the supplemental payment is the result of the above calculation.
(2) The Individual Asset Account established for the participant is a noncountable asset for TAFDC until the participant receives the funds from the account after leaving FEP employment.
```

#### Rank 5 — PARTIAL (sim 0.518)

- **Chunk ID**: `cmr_sec_701_600__012`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 13 / 25
- **Program**: EA
- **Hierarchy**: (V) Full Employment Program Wages-TAFDC.
- **Judge reason**: The chunk defines Full Employment Program Wages but only provides a brief definition and references without explaining what the Full Employment Program itself is or how it operates.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (V) Full Employment Program Wages-TAFDC.

(V) Full Employment Program Wages-TAFDC. The gross wages a participant gets directly from his or her Full Employment Program employer. Manual Reference: 106 CMR 707.180: Full Employment Program.
(W) Grant. The total amount of assistance that an assistance unit is eligible to receive. Manual Reference: 106 CMR 704.500: Calculation of the Grant Amount.
```


### cmr_026 — TAFDC MassHealth (rank-1: PARTIAL)

**Question**: When is a SNAP household eligible for MassHealth referral  
**Program filter**: (none)  
**Expected section (for reference)**: `705.100`  
**Notes**: 705.100 MassHealth (in TCAP related benefits — though question says SNAP, might cross-pull)  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.20  

#### Rank 1 — PARTIAL (sim 0.552)

- **Chunk ID**: `cmr_sec_702_120__003`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 4 / 9
- **Program**: EA
- **Hierarchy**: (E) Related Benefits and Services.
- **Judge reason**: The chunk discusses MassHealth referral in the context of TAFDC/EAEDC eligibility and mentions SNAP, but does not specifically address when a SNAP household becomes eligible for MassHealth referral.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (E) Related Benefits and Services.

(E) Related Benefits and Services. The worker must inform the applicant that eligibility for TAFDC or EAEDC benefits will confer eligibility for MassHealth as specified in the regulations of the Division of Medical Assistance; that he or she may choose to apply for SNAP benefits as part of the application and that SNAP eligibility will be determined according to SNAP eligibility criteria; and that if he or she is found ineligible for TAFDC or EAEDC he or she may make a separate application for MassHealth, and/or SNAP benefits. The worker must make any necessary referrals for other benefits or services, such as child care. See 106 CMR 705: Related Benefits.
```

#### Rank 2 — PARTIAL (sim 0.515)

- **Chunk ID**: `cmr_sec_365_180__001`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk discusses categorical eligibility for SNAP households but does not address MassHealth referral eligibility criteria or procedures.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (A) The following SNAP households are categorically eligible:

(5) SNAP-only TANF Service Elder/Disabled Households which include SNAP households consisting solely of non-SSI elders (60 years of age or older) and/or disabled individuals in accordance with SNAP disability standards at 106 CMR 361.210: Elderly or Disabled Individuals. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards; and
(6) SNAP-only TANF Service Adult Households include SNAP households consisting solely of adults between 19 and 59 years of age. These households must meet the Gross Monthly Categorically Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards. For purposes of 106 CMR 365.180(A)(1) through (3), authorized to receive means that an individual has been determined eligible for benefits and has been notified of this determination, even if benefits have been authorized but not received, authorized but not accessed, suspended or recouped, or not paid because they are less than a minimum amount. For purposes of 106 CMR 365.180(A)(4) through (6), a TANF Service includes receipt of the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure.
```

#### Rank 3 — PARTIAL (sim 0.504)

- **Chunk ID**: `cmr_sec_705_200__000`
- **Section**: `705.200` — Supplemental Nutrition Assistance Program (SNAP)
- **Program**: EA
- **Judge reason**: The chunk discusses SNAP eligibility and categorical eligibility for SNAP households, but does not address MassHealth referral eligibility criteria.

```
106 CMR 705 > RELATED > 705.200 Supplemental Nutrition Assistance Program (SNAP)

The purpose of SNAP is to ensure adequate nutrition for low income households. The program is administered by the Department. Obtaining SNAP
(A) An applicant or client may also apply for and be eligible for SNAP benefits. The worker must ask whether the applicant wants to apply for SNAP, and if so, must ensure that the application is processed appropriately. When all the members of the SNAP household are receiving TAFDC and/or SSI benefits, the household is categorically eligible for SNAP. See 106 CMR 365.180: Categorically Eligible Households.
```

#### Rank 4 — IRRELEVANT (sim 0.498)

- **Chunk ID**: `cmr_sec_361_160__000`
- **Section**: `361.160` — Handling Applications for Public Assistance (PA) Households
- **Program**: SNAP
- **Judge reason**: The chunk addresses SNAP application procedures for PA households but does not discuss MassHealth referral eligibility criteria.

```
106 CMR 361 > THE > 361.160 Handling Applications for Public Assistance (PA) Households

To facilitate their participation in SNAP, households in which all members are applying for cash assistance shall be allowed to apply simultaneously for SNAP benefits. However, the household's SNAP eligibility and benefit level shall be based solely on SNAP eligibility criteria. The household shall be certified in accordance with the SNAP notice and processing standards even when these standards are different than those of the cash assistance program. See 106 CMR 365.100 through 365.180 for special procedures for taking and processing SNAP applications for these households.
```

#### Rank 5 — PARTIAL (sim 0.496)

- **Chunk ID**: `cmr_sec_364_050__000`
- **Section**: `364.050` — Introduction
- **Program**: SNAP
- **Judge reason**: The chunk discusses SNAP eligibility determination but does not address the specific question about when a SNAP household is eligible for MassHealth referral.

```
106 CMR 364 > DETERMINING > 364.050 Introduction

When the Department receives a complete application, including all required verification and documentation, the case manager must determine if the household is eligible to participate in SNAP. For eligible households, the benefit level is the monthly allotment or amount of SNAP benefits the household is eligible to receive.
```


### cmr_027 — TAFDC overpayments (rank-1: RELEVANT)

**Question**: How does DTA correct overpayments and underpayments  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `706.210` — judge picked rank-1 RELEVANT chunk in section `706.210` (section-author intuition agrees)  
**Notes**: 706.210 Correction of Overpayments and Underpayments  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.471)

- **Chunk ID**: `cmr_sec_706_210__000`
- **Section**: `706.210` — Correction of Overpayments and Underpayments
- **Program**: EA
- **Judge reason**: This chunk directly addresses how DTA corrects both overpayments and underpayments, including notification procedures, offset options, and recovery processes.

```
106 CMR 706 > AUXILIARY > 706.210 Correction of Overpayments and Underpayments

The Department has the responsibility to identify and correct overpayments and underpayments. The Department must promptly correct underpayments to current clients and to those who would have been clients if the mistake causing the underpayment had not occurred. When an underpayment is established, the Department shall send written notice to the client that:
(1) includes the amount; and
(2) informs the client of the right to request a fair hearing. Before an action to recoup an overpayment as provided in 106 CMR 706.290, the Department shall notify the client in accordance with 106 CMR 702.500: Notification of Proposed Action. If both an underpayment and an overpayment exist, the Department may offset one against the other if the existence and amount of both the underpayment and the overpayment can be promptly determined. Otherwise, the Department shall proceed to correct the underpayment and overpayment independently. Retroactive corrective underpayments shall not be considered as income or as an asset for purposes of determining continued eligibility and amount of assistance either in the month paid or in the following month. All overpayments are subject to recovery by the Department. Overpayments involving possible fraud shall be referred to the Bureau of Special Investigations (BSI).
```

#### Rank 2 — PARTIAL (sim 0.362)

- **Chunk ID**: `cmr_sec_706_200__000`
- **Section**: `706.200` — Overpayments and Underpayments
- **Program**: EA
- **Judge reason**: The chunk defines what overpayments and underpayments are but does not explain how DTA corrects them, which is what the user is asking about.

```
106 CMR 706 > AUXILIARY > 706.200 Overpayments and Underpayments

An overpayment exists when an assistance unit receives assistance for which it is not eligible or the assistance exceeds the amount for which it was eligible. However, an unaccessed EBT cash benefit shall not be considered an overpayment. An overpayment may result from Department error, client error, misrepresentation or withholding of information, or assistance paid pending an appeal as provided in 106 CMR 343.250: Continuation of Benefits Pending Appeal. An underpayment exists when:
(A) a financial assistance payment received by or for an assistance unit for the month is less than the amount for which the assistance unit was eligible; or
(B) the Department fails to issue a financial assistance payment for the month to an eligible assistance unit, if such payment should have been issued.
```

#### Rank 3 — PARTIAL (sim 0.346)

- **Chunk ID**: `cmr_sec_706_000__000`
- **Section**: `706.000` — Overview of Auxiliary Activities
- **Program**: EA
- **Judge reason**: This is an overview/table of contents that identifies overpayments and underpayments as a topic (106 CMR 706.200) but does not provide the actual procedures or methods for how DTA corrects them.

```
106 CMR 706 > AUXILIARY > 706.000 Overview of Auxiliary Activities

106 CMR 706.000 describes activities that affect the delivery of benefits and are required to ensure the proper and accurate direction of funds. Unless otherwise specified, 106 CMR 706.000 applies to TAFDC and EAEDC applicants and clients. Auxiliary activities and the circumstances in which they are required are described in 106 CMR 706.000(A) through (G):
(A) Inquiries, Requests and Complaints, 106 CMR 706.100;
(B) Overpayments and Underpayments, 106 CMR 706.200;
(C) Referral to the Bureau of Special Investigations, 106 CMR 706.240;
(D) Delivery of Benefits, 106 CMR 706.400;
(E) Lost and Stolen Checks, 106 CMR 706.500;
(F) Vendor Payments, 106 CMR 706.600; and
(G) Quality Control, 106 CMR 706.700.
```

#### Rank 4 — PARTIAL (sim 0.338)

- **Chunk ID**: `cmr_sec_706_290__000`
- **Section**: `706.290` — Recovery from Current Clients
- **Program**: EA
- **Judge reason**: The chunk addresses overpayment recovery methods but does not address how DTA corrects underpayments, which is half of the user's question.

```
106 CMR 706 > AUXILIARY > 706.290 Recovery from Current Clients

(A) Method of Recovery.
(1) Recovery of an overpayment shall be sought from current clients and previous clients who reapply for and are determined eligible for TAFDC or EAEDC.
(2) The methods of recovery shall be by:
(a) recoupment, which is the recovery of an overpayment by means of a reduction in the client's grant;
(b) a lump sum payment;
(c) installment payments;
(d) wage assignment as provided in 106 CMR 706.295;
(e) any combination of the above four methods; or
(f) any other recovery method permitted by law.
(3) If a client refuses or fails to pay or who has been repaying his or her overpayment to the Department through a lump sum payment and/or installment payments or a combination of methods provided in 106 CMR 706.290(A)(2) misses a payment or is otherwise in arrears, he or she shall be required to repay the remaining overpayment:
(a) by recoupment; or
(b) by wage assignment.
(B) Amount of Recovery.
(1) The Department shall recover overpayments on a monthly basis, in an amount equal to:
(a) 10% of the appropriate TAFDC Payment Standard or EAEDC Standards of Assistance;
(b) an amount that exceeds 10% of the appropriate TAFDC Payment Standard or EAEDC Standards of Assistance, if the client agrees, through an arrangement with BSI or the Department;
(c) a judgment or order of the court; or
(d) a repayment agreement established by a fair hearing or an administrative disqualification hearing.
```

#### Rank 5 — PARTIAL (sim 0.335)

- **Chunk ID**: `cmr_sec_706_250__000`
- **Section**: `706.250` — Recovery
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) The Department shall act promptly to recover all overpayments from curren...
- **Judge reason**: Addresses overpayment recovery procedures but does not explain how underpayments are corrected or the full process for both types of payment adjustments.

```
106 CMR 706 > AUXILIARY > 706.250 Recovery

(A) The Department shall act promptly to recover all overpayments from current clients and from previous clients who reapply for and are determined eligible for TAFDC or EAEDC. The Department shall refer overpayments to BSI whenever there is a reasonable possibility of fraud. In such cases, no recovery may take place until BSI notifies the Department that it has decided not to investigate or its investigation is complete, or unless recovery is being made through the Administrative Disqualification process as provided in 106 CMR 706.345.
```


### cmr_028 — identity verification (rank-1: RELEVANT)

**Question**: How does DTA verify identity  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361` — judge picked rank-1 RELEVANT chunk in section `361.610` (section-author intuition agrees)  
**Notes**: BROAD — chapter 361 application processing covers verification; many sections in 361 may match  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.473)

- **Chunk ID**: `cmr_sec_361_610__005`
- **Section**: `361.610` — Verification Requirements at Initial Certification
- **Chunk position**: 6 / 10
- **Program**: SNAP
- **Hierarchy**: (G) Identity.
- **Judge reason**: Directly explains DTA's identity verification methods including acceptable documentary evidence and collateral contact procedures.

```
106 CMR 361 > THE > 361.610 Verification Requirements at Initial Certification > (G) Identity.

(G) Identity. The identity of the applicant and any authorized representative applying on behalf of the household shall be verified prior to initial certification. Identity may be verified through documentary evidence that is readily available to the applicant or representative. Examples of acceptable documentary evidence which the applicant may provide include, but are not limited to, a driver's license; a work or school ID; an ID for health benefits or for another assistance or social service program; a voter registration card; wage stubs or a birth certificate. Any documents which reasonably establish identity must be accepted, and no requirement for a specific type of document may be imposed. In the absence of documentary evidence, identity shall be verified by collateral contact in accordance with 106 CMR 361.640.
```

#### Rank 2 — RELEVANT (sim 0.427)

- **Chunk ID**: `cmr_sec_366_920__003`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 4 / 5
- **Program**: SNAP
- **Hierarchy**: (D) Verification at Initial Certification.
- **Judge reason**: The chunk directly addresses how DTA verifies identity through SDX data and other verification methods at initial certification for SSI/SNAP households.

```
106 CMR 366 > ADDITIONAL > 366.920 Regular SSI/SNAP Households > (D) Verification at Initial Certification.

(D) Verification at Initial Certification.
(1) If the application is filed at an SSA office, SSA will indicate what required verifications are on file at the SSA office. Unless the application is incomplete, mandatory verification is missing, or certain information on the application is questionable, no other verification shall be requested.
(2) If an application is filed at a TAO, available SDX data will be used to verify the assets, identity, residency, social security number and unearned income of the SSI recipient. Additional verification of these eligibility factors will be required only if the information supplied by the SSI recipient contradicts SDX data.
(3) Deductible expenses claimed by the applicant shall be verified in accordance with Department requirements.
(4) Noncitizen Status. Noncitizen Status will be verified through SDX. The applicant must meet an eligible noncitizen status in accordance with 106 CMR 362.220(B). The applicant will be denied if the noncitizen status on SDX is an ineligible status. Additional verification of noncitizen status will be required if the SDX information is questionable.
```

#### Rank 3 — PARTIAL (sim 0.400)

- **Chunk ID**: `cmr_sec_361_600__000`
- **Section**: `361.600` — Verification
- **Program**: SNAP
- **Judge reason**: Defines verification generally and references sections 361.600-361.660 but doesn't explain the specific methods DTA uses to verify identity.

```
106 CMR 361 > THE > 361.600 Verification

Verification is the use of third-party information or documentation to establish the accuracy of the information provided by the applicant. 106 CMR 361.600 through 361.660 describe the requirements for verification. Application of these requirements to each eligibility factor is discussed in the sections dealing with the particular eligibility factor. (See 106 CMR 365.180: Categorically Eligible Assistance Units for verification of factors that are deemed for categorically eligible households.)
```

#### Rank 4 — PARTIAL (sim 0.371)

- **Chunk ID**: `cmr_sec_361_650__000`
- **Section**: `361.650` — Responsibility for Obtaining Verification
- **Program**: SNAP
- **Judge reason**: The chunk addresses verification procedures and responsibility for providing documentary evidence, but focuses on income verification rather than identity verification specifically.

```
106 CMR 361 > THE > 361.650 Responsibility for Obtaining Verification

The household has primary responsibility for providing documentary evidence to support its income statements and to resolve any questionable information, provided that nothing in 106 CMR 361.650 shall limit the ability of the Department to verify information from other government agencies or from banks. Households may supply documentary evidence in person, through the mail, or through an authorized representative. The worker shall consider any reasonable documentary evidence provided by the household and shall be primarily concerned with how adequately the verification proves the statements on the application. If it would be difficult or impossible for the household to obtain the documentary evidence in a timely manner, or the household has presented insufficient documentation, the worker shall either offer assistance to the household in obtaining the documentary evidence, except when verification of shelter or utility costs for unoccupied homes would have to be obtained from a source outside the State, or shall use a collateral contact or home visit. The worker shall not require the household to present verification in person at the local office.
```

#### Rank 5 — PARTIAL (sim 0.368)

- **Chunk ID**: `cmr_sec_365_180__005`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 6 / 9
- **Program**: SNAP
- **Hierarchy**: (F) Verification Requirements.
- **Judge reason**: The chunk discusses verification of household factors and program eligibility for SSI, EAEDC, and TANF, but does not address identity verification methods or procedures.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (F) Verification Requirements.

(F) Verification Requirements.
(1) The Department shall verify the following factors for SSI:
(a) each member receives SSI benefits or is authorized to receive, as specified in 106 CMR 365.180(A)(1);
(b) the household includes no individuals who have been disqualified in accordance with 106 CMR 365.180(B)(2);
(c) the SNAP household includes all persons who purchase and prepare food together regardless of whether or not they are separate units for SSI; and
(d) the household composition meets the definition of a household, as specified in 106 CMR 361.200: Household Concept.
(2) The Department shall verify the following factors for EAEDC:
(a) each member receives EAEDC benefits;
(b) the household includes no individuals who have been disqualified for EAEDC, in accordance with 106 CMR 365.180(C)(2)(d) and (e); and
(c) the household composition meets the definition of a household, as specified in 106 CMR 361.200: Household Concept.
(3) The Department shall verify the following factors, for TANF Services Households:
(a) the household is eligible for the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure; and
(b) the income of the household does not exceed the appropriate standards for the SNAP Only TANF Services Household as outlined at 106 CMR 365.180(A)(5).
(c) the household includes no individuals disqualified in accordance with 106 CMR 365.180(B)(2); and
(d) the household composition meets the definition of a household, in accordance with
```


### cmr_029 — SNAP household composition (rank-1: RELEVANT)

**Question**: What are SNAP household composition rules  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.2` — judge picked rank-1 RELEVANT chunk in section `361.200` (section-author intuition agrees)  
**Notes**: BROAD — 361.200 series; multiple chunks should match  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.55  

#### Rank 1 — RELEVANT (sim 0.569)

- **Chunk ID**: `cmr_sec_361_200__002`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: Directly addresses SNAP household composition rules including parent/child requirements and special living arrangements that determine household membership.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (A) The following individuals living with others or groups of individuals liv...

(3) Parent/Child Rule. A child younger than 22 years old living with his or her natural, adopted or stepparent(s) must be in the same SNAP household as the parent(s).
(B) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals separately even if they do not do so.
(1) An individual, with or without children, residing in a drug or alcohol treatment center shall be one SNAP household separate from the other residents. See 106 CMR 365.600 through 365.690.
(2) A blind or disabled resident of a group living arrangement (106 CMR 365.600 through 365.690) who applies through the use of the facility's authorized representative shall be one SNAP household separate from the other residents. If a blind or disabled resident applies on his or her own behalf, the household size must be determined following the household concept rules defined in 106 CMR 361.200.
(3) An individual, with or without children, residing in a shelter for battered individuals and their children shall be one SNAP household separate from the other residents. See 106 CMR 365.550: Residents of Shelters for Battered Women and Their Children.
```

#### Rank 2 — RELEVANT (sim 0.566)

- **Chunk ID**: `cmr_sec_361_200__001`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: Directly addresses SNAP household composition rules by defining which individuals must be in the same household, including spouse and parental control rules.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (A) The following individuals living with others or groups of individuals liv...

(A) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals together even if they do not do so unless an exception applies:
(1) Spouse Rule. An individual living with his or her spouse must be in the same SNAP household as the spouse. Spouses shall not be granted separate household status. Spouse is defined as either of two individuals who are legally married to one another, or who are living together and holding themselves out to the community as husband and wife by representing themselves as spouses to relatives, friends, neighbors, or tradespeople;
(2) Parental Control Rule. A child younger than 18 years old, except for a foster care child (as defined in 106 CMR 361.240(F)), who is living with an adult household member (not the child's parent) and under the parental control of the adult household member, must be in the same SNAP household as the adult household member. Parental control means providing financial support or supervision, or both, to an individual younger than 18 years old; and
```

#### Rank 3 — RELEVANT (sim 0.554)

- **Chunk ID**: `cmr_sec_361_200__000`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: Directly defines SNAP household composition by outlining the three types of household units recognized under Massachusetts DTA policy.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition

A SNAP household is defined as:
(1) an individual who lives alone;
(2) an individual living with others who purchases food and prepares meals separately; or
(3) a group of individuals living together who purchase food and prepare meals together.
```

#### Rank 4 — PARTIAL (sim 0.538)

- **Chunk ID**: `cmr_sec_365_510__000`
- **Section**: `365.510` — Nondisqualified Nonhousehold Members
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: Addresses a specific aspect of SNAP household composition (nondisqualified nonhousehold members) but doesn't provide comprehensive household composition rules.

```
106 CMR 365 > SPECIAL > 365.510 Nondisqualified Nonhousehold Members

Nondisqualified nonhousehold members shall be treated in accordance with the provisions of 106 CMR 365.510(A) through (C). If otherwise eligible, nondisqualified nonhousehold members may be eligible as separate SNAP households.
```

#### Rank 5 — RELEVANT (sim 0.530)

- **Chunk ID**: `cmr_sec_361_230__000`
- **Section**: `361.230` — Nonhousehold Members
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Judge reason**: Directly addresses SNAP household composition by defining who can and cannot be considered household members and how their income/resources are treated.

```
106 CMR 361 > THE > 361.230 Nonhousehold Members

In some cases individuals residing within a household cannot be considered SNAP household members. Such persons are termed nonhousehold members. Except for disqualified individuals described in 106 CMR 361.230(D), the nonhousehold member's income and resources shall not be considered in determining the household's eligibility and benefit level. Nonhousehold members who are otherwise eligible may participate in the program as separate households. Nonhousehold members include:
```


### cmr_030 — SNAP benefit calculation (rank-1: PARTIAL)

**Question**: How are SNAP benefits calculated  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364`  
**Notes**: BROAD — chapter 364 entirely about determining benefit  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.561)

- **Chunk ID**: `cmr_sec_364_980__000`
- **Section**: `364.980` — SNAP Issuance Tables
- **Program**: SNAP
- **Judge reason**: Explains what eligible clients receive (100% of allotment from tables) but doesn't explain how the benefit amount itself is calculated based on income, household size, expenses, or other factors.

```
106 CMR 364 > DETERMINING > 364.980 SNAP Issuance Tables

A client who is eligible for SNAP benefits will receive 100% of the SNAP benefit allotment listed in the Program Issuance Tables. The standards in the SNAP Issuance Tables are based on household size and are adjusted annually by USDA/FNS. These standards are posted at www.mass.gov/dta. NON-TEXT PAGE
```

#### Rank 2 — PARTIAL (sim 0.543)

- **Chunk ID**: `cmr_sec_364_600__003`
- **Section**: `364.600` — Determining the Benefit Level
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (C) For households containing both SNAP members and legal noncitizens ineligi...
- **Judge reason**: Describes a specific calculation scenario for mixed-eligibility households rather than the general SNAP benefit calculation methodology.

```
106 CMR 364 > DETERMINING > 364.600 Determining the Benefit Level > (C) For households containing both SNAP members and legal noncitizens ineligi...

(C) For households containing both SNAP members and legal noncitizens ineligible for SNAP benefits, the Department will:
(1) Step One: Calculate SNAP benefits using all household members, all household members' income and full deductions to determine the maximum SNAP benefits the household would be entitled to if all members were SNAP eligible.
(2) Step Two: Calculate the SNAP benefits for SNAP members excluding the income and deductions of legal noncitizens ineligible for SNAP benefits.
(3) Step Three: Compare the results from Step One and Step Two.
(a) If the Step Two amount exceeds or is equal to the Step One amount, the Department will pay the Step One amount as the SNAP benefit.
(b) If the Step Two amount is less than the Step One amount, the Department will pay the Step Two amount as the SNAP benefit.
```

#### Rank 3 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_364_050__000`
- **Section**: `364.050` — Introduction
- **Program**: SNAP
- **Judge reason**: The chunk mentions that benefit level is determined for eligible households but does not explain the actual calculation methodology or formula used to determine SNAP benefits.

```
106 CMR 364 > DETERMINING > 364.050 Introduction

When the Department receives a complete application, including all required verification and documentation, the case manager must determine if the household is eligible to participate in SNAP. For eligible households, the benefit level is the monthly allotment or amount of SNAP benefits the household is eligible to receive.
```

#### Rank 4 — PARTIAL (sim 0.519)

- **Chunk ID**: `cmr_sec_364_600__000`
- **Section**: `364.600` — Determining the Benefit Level
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Judge reason**: The chunk indicates that benefit levels are determined but does not explain the actual calculation methodology or formula used.

```
106 CMR 364 > DETERMINING > 364.600 Determining the Benefit Level

Once a household has been determined eligible for SNAP considering both nonfinancial and financial eligibility standards, the case manager must determine the household's benefit level or monthly allotment.
```

#### Rank 5 — PARTIAL (sim 0.485)

- **Chunk ID**: `cmr_sec_366_110__006`
- **Section**: `366.110` — Household Reporting Responsibilities
- **Chunk position**: 7 / 9
- **Program**: SNAP
- **Hierarchy**: (C) Simplified Reporting Requirements
- **Judge reason**: The chunk discusses when and how SNAP benefits are recalculated during certification periods, but does not explain the actual methodology or formula used to calculate SNAP benefit amounts.

```
106 CMR 366 > ADDITIONAL > 366.110 Household Reporting Responsibilities > (C) Simplified Reporting Requirements

(5) If, during the certification period prior to the submission of the Interim Report or following the submission of the Interim Report, the Department receives notice of a TAFDC or EAEDC income change for the Simplified Reporting household, the Department will recalculate the SNAP benefits and pay the increased, decreased, or unchanged recalculated SNAP benefit amount.
(6) The Department may clarify unclear information received in accordance with 106 CMR 366.115 and recalculate the household's SNAP benefit amount during the certification period. The Department will recalculate the SNAP benefits and pay the increased, decreased, or unchanged recalculated SNAP benefit amount.
(7) In (4), (5), and (6) above, the Department will pay the SNAP benefit amount for the remainder of the certification period unless the Department subsequently recalculates the SNAP benefit amount in accordance with (4) through (6) above.
```


### cmr_031 — section number lookup (rank-1: PARTIAL)

**Question**: What does 363.140 cover  
**Program filter**: (none)  
**Expected section (for reference)**: `363.140`  
**Notes**: ADVERSARIAL — exact section-number query. Tests whether the embedding picks up the literal '363.140' token. Hybrid search should excel here.  
**Scores**: Relevant@5 = 1, Useful@5 = 2, rank-weighted = 0.70  

#### Rank 1 — PARTIAL (sim 0.357)

- **Chunk ID**: `cmr_sec_363_130__000`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 1 / 10
- **Program**: SNAP
- **Judge reason**: The chunk discusses 363.130 (Countable Assets) but the user is asking about 363.140, which is a different section not covered in this retrieved text.

```
106 CMR 363 > FINANCIAL > 363.130 Countable Assets

Countable assets are all those that must be included in determining the total value of the household's assets. If an asset is jointly owned, the value available to the household shall be determined in accordance with 106 CMR 363.120. Assets shall be distinguished from income as defined in 106 CMR 363.200. Assets counted in determining financial eligibility include, but are not limited to:
```

#### Rank 2 — IRRELEVANT (sim 0.351)

- **Chunk ID**: `cmr_sec_360_020__000`
- **Section**: `360.020` — Authority
- **Program**: SNAP
- **Judge reason**: The chunk discusses 360.020 Authority and Food Stamp Act regulations, but does not address what 363.140 covers.

```
106 CMR 360 > GENERAL > 360.020 Authority

The authority for the regulations is the Food Stamp Act and its amendments and the resulting regulations issued by the United States Department of Agriculture (USDA) in 7 CFR Parts 270 through 282, to implement the law.
```

#### Rank 3 — IRRELEVANT (sim 0.345)

- **Chunk ID**: `cmr_sec_360_030__001`
- **Section**: `360.030` — Definitions
- **Chunk position**: 2 / 4
- **Program**: SNAP
- **Hierarchy**: (1) A supervised shelter designed to provide temporary accommodations;
- **Judge reason**: The chunk is from 360.030 (Definitions) and does not address what 363.140 covers.

```
106 CMR 360 > GENERAL > 360.030 Definitions > (1) A supervised shelter designed to provide temporary accommodations;

(1) A supervised shelter designed to provide temporary accommodations;
(2) A halfway house or similar institution that provides temporary residence for individuals intended to be institutionalized;
(3) A temporary accommodation in the residence of another individual for no more than 90 days; or
```

#### Rank 4 — IRRELEVANT (sim 0.344)

- **Chunk ID**: `cmr_sec_367_660__003`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 4 / 6
- **Program**: Program Integrity
- **Hierarchy**: (E) the name and telephone number of someone who can be of assistance if the ...
- **Judge reason**: The chunk discusses 106 CMR 367.660 regarding waivers of ADH, not 363.140, and does not address what section 363.140 covers.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH > (E) the name and telephone number of someone who can be of assistance if the ...

(E) the name and telephone number of someone who can be of assistance if the accused should wish to discuss the charges, or the implications of the waiver;
(F) a place for the individual and the head of household or authorized representative to sign the form;
```

#### Rank 5 — RELEVANT (sim 0.343)

- **Chunk ID**: `cmr_sec_363_140__008`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 9 / 14
- **Program**: SNAP
- **Hierarchy**: (G) Assets of Nonhousehold Members. The assets of a nonhousehold member shall be
- **Judge reason**: The chunk directly addresses what 363.140 covers by explaining that it contains noncountable assets, specifically addressing assets of nonhousehold members and their treatment in eligibility determinations.

```
106 CMR 363 > FINANCIAL > 363.140 Noncountable Assets > (G) Assets of Nonhousehold Members. The assets of a nonhousehold member shall be

(G) Assets of Nonhousehold Members. The assets of a nonhousehold member shall be disregarded when determining the eligibility of the remaining household members except when the nonhousehold member is a disqualified nonhousehold member in accordance with 106 CMR 361.230(D): Disqualified Individuals. The assets of disqualified nonhousehold members must be considered in accordance with 106 CMR 365.500: Households Living with Non-household Members. The noncountable assets listed in 106 CMR 363.140 are also exempt for disqualified nonhousehold members.
```


### cmr_032 — ADH acronym (rank-1: PARTIAL)

**Question**: What is an ADH  
**Program filter**: (none)  
**Expected section (for reference)**: `367.520`  
**Notes**: ADVERSARIAL — Administrative Disqualification Hearing. 367.520 Introduction to ADH.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.376)

- **Chunk ID**: `cmr_sec_367_660__004`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 5 / 6
- **Program**: Program Integrity
- **Hierarchy**: (G) a statement that failure to sign and return this form within the period s...
- **Judge reason**: The chunk uses the term 'ADH' multiple times but does not define what ADH stands for or means, only describing procedures related to it.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH > (G) a statement that failure to sign and return this form within the period s...

(G) a statement that failure to sign and return this form within the period specified by the Department will result in the holding of an ADH;
(H) the charge(s) against the household member;
(I) a summary of evidence and how and where it can be examined;
```

#### Rank 2 — PARTIAL (sim 0.346)

- **Chunk ID**: `cmr_sec_367_660__003`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 4 / 6
- **Program**: Program Integrity
- **Hierarchy**: (E) the name and telephone number of someone who can be of assistance if the ...
- **Judge reason**: The chunk mentions 'ADH' in the title but only shows procedural details about waiving an ADH without defining what an ADH actually is.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH > (E) the name and telephone number of someone who can be of assistance if the ...

(E) the name and telephone number of someone who can be of assistance if the accused should wish to discuss the charges, or the implications of the waiver;
(F) a place for the individual and the head of household or authorized representative to sign the form;
```

#### Rank 3 — PARTIAL (sim 0.322)

- **Chunk ID**: `cmr_sec_367_675__000`
- **Section**: `367.675` — Advance Notice of an ADH
- **Program**: Program Integrity
- **Judge reason**: The chunk discusses procedures for an ADH (Advance Disciplinary Hearing) but does not define what an ADH is or explain its purpose.

```
106 CMR 367 > VIOLATIONS, > 367.675 Advance Notice of an ADH

The Department shall provide advance notice of an ADH in accordance with 106 CMR 367.625. No notice shall be sent and no ADH shall be held unless it is determined that the client received the penalty warning in the appropriate language prior to the date of the suspected IPV. This notice shall be sent by First Class Mail and shall contain:
(A) the date, time, and place of the hearing;
(B) the charge(s) against the household member;
(C) a summary of the evidence, and how and where it can be examined;
(D) a warning that the decision will be based solely on information provided by the Department if the household member fails to appear at the hearing;
(E) a warning that a finding that an IPV was committed will result in a 12-month period of disqualification for the first finding; a 24-month period of disqualification for the second finding; and permanent disqualification for the third finding;
(F) a listing of the household member's rights provided in 106 CMR 367.400;
(G) a copy of the Department's hearing procedures;
(H) a statement that the household member may call the local office to obtain the name and telephone number of someone who can provide free legal advice; and
(I) a statement that the household member or authorized representative has ten days from the date of the scheduled hearing to present good cause for failure to appear, in order to receive a new hearing.
```

#### Rank 4 — PARTIAL (sim 0.322)

- **Chunk ID**: `cmr_sec_367_660__005`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 6 / 6
- **Program**: Program Integrity
- **Hierarchy**: (J) a listing of the household member's rights as described in 106 CMR 367.400;
- **Judge reason**: The chunk mentions ADH multiple times but assumes the reader already knows what ADH is; it discusses waiver procedures and rights rather than defining what ADH stands for or means.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH > (J) a listing of the household member's rights as described in 106 CMR 367.400;

(J) a listing of the household member's rights as described in 106 CMR 367.400;
(K) a copy of the Department's ADH hearing procedures; and
(L) a statement that failure to return this waiver shall in no way have a negative impact on the result of the ADH.
```

#### Rank 5 — PARTIAL (sim 0.315)

- **Chunk ID**: `cmr_sec_367_660__000`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Judge reason**: The chunk discusses waiving an ADH and its consequences but does not define what an ADH actually is.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH

The individual may waive the ADH by signing a waiver form. The individual suspected of an IPV, and the head of the SNAP household, if different, may complete, sign and return the waiver form to the Department. By completing, signing and returning the waiver form, the individual and the household agree to all penalties and requirements, including repayment, incumbent upon a household containing a member who is found guilty of an IPV at an ADH. The waiver form shall include:
```


### cmr_033 — EPSDT acronym (rank-1: RELEVANT)

**Question**: What does EPSDT mean in DTA policy  
**Program filter**: (none)  
**Expected section (for reference)**: `705.130` — judge picked rank-1 RELEVANT chunk in section `705.130` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — Early and Periodic Screening, Diagnosis and Treatment. 705.130. Rare term.  
**Scores**: Relevant@5 = 1, Useful@5 = 1, rank-weighted = 1.00  

#### Rank 1 — RELEVANT (sim 0.504)

- **Chunk ID**: `cmr_sec_705_130__000`
- **Section**: `705.130` — Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)
- **Program**: EA
- **Judge reason**: The chunk directly defines EPSDT as Early and Periodic Screening, Diagnosis and Treatment Services and explains its purpose in DTA policy.

```
106 CMR 705 > RELATED > 705.130 Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)

The purpose of EPSDT is to provide all persons in the assistance unit younger than 21 years old the opportunity for preventive health care, including medical checkups, immunizations, and dental checkups. A full description of the EPSDT program is provided in MassHealth regulations of the Division of Medical Assistance.
```

#### Rank 2 — IRRELEVANT (sim 0.364)

- **Chunk ID**: `cmr_sec_705_100__000`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 1 / 4
- **Program**: EA
- **Judge reason**: The chunk discusses MassHealth eligibility and TAFDC/EAEDC programs but does not define or explain what EPSDT means.

```
106 CMR 705 > RELATED > 705.100 MassHealth

MassHealth provides medical services for individuals who meet specific income and other eligibility requirements. Current TAFDC and EAEDC clients are eligible for MassHealth without filing a separate application. The following are eligible to receive MassHealth benefits: (MA REG. # 1360, Dated 3-9-18)
```

#### Rank 3 — IRRELEVANT (sim 0.355)

- **Chunk ID**: `cmr_sec_705_100__003`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (C) EAEDC Medical Assistance.
- **Judge reason**: The chunk discusses EAEDC medical assistance and MassHealth but does not mention or define EPSDT at all.

```
106 CMR 705 > RELATED > 705.100 MassHealth > (C) EAEDC Medical Assistance.

(C) EAEDC Medical Assistance.
(1) The EAEDC program provides EAEDC medical assistance (i.e., limited medical services) to applicants and clients of EAEDC. These services shall be specified in MassHealth regulations of the Division of Medical Assistance.
(2) Certain clients of EAEDC may also be eligible for MassHealth in accordance with the MassHealth regulations of the Division of Medical Assistance. A client is ineligible for EAEDC Medical Assistance if he or she receives benefits under MassHealth.
```

#### Rank 4 — IRRELEVANT (sim 0.349)

- **Chunk ID**: `cmr_sec_705_100__001`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (A) Extended MassHealth Eligibility Subsequent to Termination of TAFDC or EAEDC.
- **Judge reason**: The chunk discusses TAFDC and EAEDC termination and MassHealth eligibility but does not define or explain what EPSDT means.

```
106 CMR 705 > RELATED > 705.100 MassHealth > (A) Extended MassHealth Eligibility Subsequent to Termination of TAFDC or EAEDC.

(A) Extended MassHealth Eligibility Subsequent to Termination of TAFDC or EAEDC. Members of a TAFDC or EAEDC assistance unit whose TAFDC or EAEDC assistance has been terminated shall receive MassHealth until a determination of ineligibility is made by MassHealth.
```

#### Rank 5 — IRRELEVANT (sim 0.339)

- **Chunk ID**: `cmr_sec_707_210__000`
- **Section**: `707.210` — Employment Services Program Support Services
- **Chunk position**: 1 / 9
- **Program**: EA
- **Judge reason**: The chunk discusses child care referral eligibility and employment services but does not mention or define EPSDT (Early and Periodic Screening, Diagnosis, and Treatment).

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.210 Employment Services Program Support Services

(A)(1) Child Care Referral Eligibility. The Department of Transitional Assistance determines eligibility referrals for child care services for individuals who have an approved Employment Development Plan (EDP) or an Extension Agreement and who meet the participation requirements of 106 CMR 707.115, or who are former clients in accordance with 106 CMR 707.210(A)(1)(f). The following individuals shall be eligible for child care referral services:
(a) an employed TAFDC grantee or a teen parent who is not the grantee who:
1. is included in the assistance unit; or
2. would be included in the assistance unit, but for a sanction due to noncooperation with the TAFDC child support requirements in accordance with 106 CMR 703.500: TAFDC Cooperation with Child Support Requirements or immunization requirements in accordance with 106 CMR 703.160: TAFDC Immunizations and who is required to meet the Work Program requirements in accordance with 106 CMR 703.150: TAFDC Work Program. Referral for such child care services may be authorized as long as the individual is employed and receives TAFDC;
(b) a TAFDC grantee, or a teen parent who is not the grantee who is required to participate in an ESP component activity or has volunteered to participate in an ESP component activity, including self-initiated educational activities included on the individual's EDP who:
1. is included in the assistance unit; or
2. would be included in the assistance unit, but for a sanction due to noncooperation
```


### cmr_034 — PA household defined term (rank-1: PARTIAL)

**Question**: What is a Public Assistance household for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365.110`  
**Notes**: ADVERSARIAL — defined term. 365.110 Definition of a Public Assistance (PA) Household  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.70  

#### Rank 1 — PARTIAL (sim 0.556)

- **Chunk ID**: `cmr_sec_361_160__000`
- **Section**: `361.160` — Handling Applications for Public Assistance (PA) Households
- **Program**: SNAP
- **Judge reason**: The chunk discusses procedures for PA households applying for SNAP but does not define what constitutes a Public Assistance household.

```
106 CMR 361 > THE > 361.160 Handling Applications for Public Assistance (PA) Households

To facilitate their participation in SNAP, households in which all members are applying for cash assistance shall be allowed to apply simultaneously for SNAP benefits. However, the household's SNAP eligibility and benefit level shall be based solely on SNAP eligibility criteria. The household shall be certified in accordance with the SNAP notice and processing standards even when these standards are different than those of the cash assistance program. See 106 CMR 365.100 through 365.180 for special procedures for taking and processing SNAP applications for these households.
```

#### Rank 2 — RELEVANT (sim 0.520)

- **Chunk ID**: `cmr_sec_365_110__000`
- **Section**: `365.110` — Definition of a Public Assistance (PA) Household
- **Program**: SNAP
- **Judge reason**: This chunk directly defines what constitutes a Public Assistance (PA) household, which is exactly what the user is asking about.

```
106 CMR 365 > SPECIAL > 365.110 Definition of a Public Assistance (PA) Household

PA households are those households in which all members receive a cash grant under one of the following programs: Transitional Aid to Families with Dependent Children (TAFDC), or Emergency Aid to the Elderly, Disabled, and Children (EAEDC). Even though a TAFDC Full Employment Program (FEP) household may not receive a cash grant, the household will be considered a PA household. The following households will also be considered PA households:
(1) households including an SSI recipient(s) when all the other members receive cash assistance under TAFDC, or EAEDC; and
(2) households including a child(ren) born after the Family Cap Date who is not included in the TAFDC grant when all other household members receive cash assistance under TAFDC, or EAEDC.
```

#### Rank 3 — PARTIAL (sim 0.518)

- **Chunk ID**: `cmr_sec_364_710__002`
- **Section**: `364.710` — Household Certification Periods
- **Chunk position**: 3 / 6
- **Program**: SNAP
- **Hierarchy**: (B) The notice shall advise Public Assistance (PA) households receiving SNAP ...
- **Judge reason**: The chunk mentions PA households receiving SNAP but describes certification period procedures rather than defining what constitutes a Public Assistance household.

```
106 CMR 364 > DETERMINING > 364.710 Household Certification Periods > (B) The notice shall advise Public Assistance (PA) households receiving SNAP ...

(B) The notice shall advise Public Assistance (PA) households receiving SNAP benefits pending the approval of the PA grant that SNAP benefits will be decreased upon receipt of that PA grant.
(C) The beginning and ending months of the certification period must be in the notice. For households certified one or two months, the Notice of Eligibility shall be combined with the Notice of Recertification. For households certified three months or longer, the notice shall include a reminder of the need to reapply for continued certification at the end of the certification period. For PA households, the notice shall state that the household's certification period will expire the month after the next PA redetermination or in one year, which ever occurs first.
```

#### Rank 4 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_365_170__007`
- **Section**: `365.170` — Department Action on Reported Changes
- **Chunk position**: 8 / 8
- **Program**: SNAP
- **Hierarchy**: (C) Change in Classification from a PA to an NPA SNAP Household.
- **Judge reason**: The chunk discusses PA (Public Assistance) and NPA (Non-Public Assistance) SNAP households and their classification changes, but does not define what a Public Assistance household actually is.

```
106 CMR 365 > SPECIAL > 365.170 Department Action on Reported Changes > (C) Change in Classification from a PA to an NPA SNAP Household.

application by the 15 th day of the last month of its certification period and completes its recertification responsibilities.
(D) Change from PA to NPA Status is Known to the Department at the Time of the Public Assistance Redetermination. When a change from PA to NPA status is known to the Department at the time of a public assistance redetermination, the household shall nevertheless be recertified for SNAP benefits, to the extent possible, at the same time it is redetermined for the public assistance program.
```

#### Rank 5 — PARTIAL (sim 0.503)

- **Chunk ID**: `cmr_sec_361_170__000`
- **Section**: `361.170` — Handling Applications for Non-public Assistance (NPA) Households
- **Program**: SNAP
- **Judge reason**: The chunk defines Non-public Assistance (NPA) households, which is the opposite category of what was asked, but provides context about household classifications under SNAP policy.

```
106 CMR 361 > THE > 361.170 Handling Applications for Non-public Assistance (NPA) Households

NPA households are defined as follows:
(A) households in which no member is a recipient of cash assistance; and
(B) households in which some members, but not all, are applicants for or recipients of cash assistance.
```


### cmr_035 — EDP defined term (rank-1: RELEVANT)

**Question**: What is an Employment Development Plan  
**Program filter**: (none)  
**Expected section (for reference)**: `707.110` — judge picked rank-1 RELEVANT chunk in section `707.110` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — defined term/acronym. 707.110 Completion of an Employment Development Plan (EDP)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.616)

- **Chunk ID**: `cmr_sec_707_110__002`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 3 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk directly defines what an Employment Development Plan (EDP) is by explaining its required components, approval criteria, and key characteristics.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.110 Completion of an Employment Development Plan (EDP) > (A) Developing an EDP.

(4) The EDP shall contain:
(a) the individual's employment goal and the activities needed to meet the employment goal;
(b) ESP component activities in which the individual will participate;
(c) necessary support services; and
(d) the anticipated start and end dates for the activities.
(5) An EDP shall be approved when:
(a) the EDP is consistent with the regulations found in 703.150: TAFDC Work Program and 707.000 through 707.180;
(b) the activities in the EDP are consistent with the goal of the individual obtaining a job;
(c) the EDP is consistent with the assessment or reassessment of the individual's education, skills and work experience; and
(d) the component activities and support services, subject to appropriations, are available. When an EDP is not approved, the Department shall document the reasons.
(6) Except for individuals who failed to meet their Work Program requirements, the written EDP must be mutually agreed to and signed by the individual and a Department worker. The individual shall be provided a copy of the EDP. An EDP is not a contract. An EDP is valid for the period stated in the plan, but not for more than 12 months unless, in accordance with 106 CMR 707.110(C), there is a need to reassess the EDP.
```

#### Rank 2 — PARTIAL (sim 0.576)

- **Chunk ID**: `cmr_sec_707_110__001`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 2 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk describes the process and criteria for developing an EDP but does not provide a direct definition of what an Employment Development Plan actually is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.110 Completion of an Employment Development Plan (EDP) > (A) Developing an EDP.

(2) An initial assessment interview shall be conducted by a Department worker at application or the eligibility review and shall include, but not be limited to, the following:
(a) the collection of information about the individual's education, skills and employment background;
(b) a discussion of the available services to help the individual obtain and maintain a job;
(c) a review of the individual's ESP requirement as specified in 106 CMR 707.000; and
(d) a discussion of the available ESP components that will best help the individual obtain and maintain a job.
(3) The following criteria are used to develop an EDP:
(a) the initial assessment of the individual's education, skills and work experience;
(b) available program resources to support the individual in the ESP activity and his or her employment goal;
(c) the individual's need for and the availability of support services as provided in 106 CMR 707.210;
(d) the individual's vocational and employment interests;
(e) employment opportunities in the northeast regional labor market as found in the Dictionary of Occupational Titles, Occupational Outlook Handbook and Labor Market Surveys; and
(f) the component requirements as provided in 106 CMR 707.120 through 707.180.
```

#### Rank 3 — PARTIAL (sim 0.573)

- **Chunk ID**: `cmr_sec_707_180__000`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) Activities. Activities in FEP include:
- **Judge reason**: The chunk mentions Employment Development Plan (EDP) and references where it's defined (106 CMR 707.110), but does not actually explain what an EDP is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.180 Full Employment Program

The Full Employment Program (FEP) component provides individuals work experience needed to obtain an unsubsidized job. Participants are paid a subsidized wage in lieu of receiving TAFDC.
(A) Activities. Activities in FEP include:
(1) full-time employment of 35 to 40 hours per week consistent with the employer's schedule; and
(2) completion of an Employment Development Plan (EDP) as provided in 106 CMR 707.110.
```

#### Rank 4 — PARTIAL (sim 0.571)

- **Chunk ID**: `cmr_sec_707_110__000`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 1 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk explains who must complete an EDP and when, but does not define what an Employment Development Plan actually is or what it contains.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.110 Completion of an Employment Development Plan (EDP)

(A) Developing an EDP.
(1) An EDP will be completed every year for:
(a) a grantee who the Department determines must participate in an Employment Services Program (ESP) component because there are available component slots;
(b) a grantee who volunteers to participate in ESP;
(c) all teen parents who have not graduated from high school or do not have a HiSET certificate;
(d) a grantee needing support services to work or to participate in ESP or in a self- initiated program not funded by ESP as provided in 106 CMR 707.120;
(e) a dependent child 16 or 17 years of age who is not in school and must participate in the ESP Educational Component;
(f) a grantee or an ineligible grantee specified in 106 CMR 703.150(A)(2) referred to community service who:
1. volunteers to participate in community service;
2. is mandated to participate in community service because he or she did not meet the participation requirements of another ESP component; or
3. needs support services to participate in community service;
(g) a grantee participating in the Full Employment Program; and
(h) any other grantee who the Department determines needs an EDP.
```

#### Rank 5 — PARTIAL (sim 0.568)

- **Chunk ID**: `cmr_sec_707_110__003`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 4 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk discusses procedures for completing and placing individuals in an EDP but does not define what an Employment Development Plan actually is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.110 Completion of an Employment Development Plan (EDP) > (A) Developing an EDP.

(7) An individual unable to agree with the contents of the EDP may have the EDP reviewed by a Department supervisor to help resolve the matter.
(B) Component Placement and Availability.
(1) The Department refers individuals for placement in an available component activity. These referrals shall include, but not be limited to, ESP-funded and non-ESP funded component activities.
(2) If there is no opening in an ESP component chosen by the individual, the EDP will not be approved and the individual will be required to select another component activity.
(3) An individual may find his or her own community service site which must be approved by the Department.
```


### cmr_036 — SNAP allowed uses (rank-1: RELEVANT)

**Question**: What can SNAP benefits be used to purchase  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `360.100` — judge picked rank-1 RELEVANT chunk in section `360.100` (section-author intuition agrees)  
**Notes**: 360.100 Uses of SNAP Benefits (covers chapter 360 which is otherwise underrepresented)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.580)

- **Chunk ID**: `cmr_sec_360_100__000`
- **Section**: `360.100` — Uses of SNAP Benefits
- **Program**: SNAP
- **Judge reason**: Directly states what SNAP benefits can be used to purchase (eligible foods, seeds, and plants for home consumption)

```
106 CMR 360 > GENERAL > 360.100 Uses of SNAP Benefits

SNAP benefits are to be used by clients to buy eligible foods, including seeds and plants, for home consumption and use. The household may permit other persons to purchase food for the household. Such persons need not be pictured on the EBT card. Households are not required to have cooking facilities to receive SNAP.
```

#### Rank 2 — PARTIAL (sim 0.574)

- **Chunk ID**: `cmr_sec_360_030__003`
- **Section**: `360.030` — Definitions
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (4) A place not designed for or ordinarily used as a regular sleeping accommo...
- **Judge reason**: The chunk defines what SNAP benefits are but doesn't specify what items can be purchased with them; it only mentions 'eligible food' without listing what qualifies.

```
106 CMR 360 > GENERAL > 360.030 Definitions > (4) A place not designed for or ordinarily used as a regular sleeping accommo...

SNAP Benefits. Any coupon, stamp, certificate, voucher, authorization card, access device including an electronic benefit card and personal identification number, or SNAP payment in the form of cash or a check for the purchase of eligible food.
```

#### Rank 3 — PARTIAL (sim 0.555)

- **Chunk ID**: `cmr_sec_360_120__002`
- **Section**: `360.120` — Special Uses of SNAP Benefits
- **Chunk position**: 3 / 6
- **Program**: SNAP
- **Hierarchy**: (C) Food Purchases for Residents of Drug or Alcohol Treatment and Rehabilitat...
- **Judge reason**: Addresses a specific use case for SNAP benefits (food purchases in treatment centers) but doesn't comprehensively answer what SNAP benefits can generally be used to purchase.

```
106 CMR 360 > GENERAL > 360.120 Special Uses of SNAP Benefits > (C) Food Purchases for Residents of Drug or Alcohol Treatment and Rehabilitat...

(C) Food Purchases for Residents of Drug or Alcohol Treatment and Rehabilitation Centers. Members of eligible households who are narcotic addicts or alcoholics and who regularly participate in a drug or alcoholic treatment and rehabilitation program may use SNAP benefits to purchase food provided for them during the course of such programs by an organization or institution meeting the requirements of 106 CMR 365.610: Drug and Alcohol Treatment Centers, if one of the following is true:
(1) the organization or institution is authorized by FNS to redeem SNAP benefits through wholesalers;
(2) the organization or institution redeems SNAP benefits at retail food stores as the authorized representative of participating households; or
(3) the organization or institution is authorized by FNS as a retailer.
```

#### Rank 4 — PARTIAL (sim 0.517)

- **Chunk ID**: `cmr_sec_364_900__000`
- **Section**: `364.900` — Delivery of Benefits
- **Chunk position**: 1 / 8
- **Program**: SNAP
- **Judge reason**: The chunk mentions that SNAP benefits can be used for 'food purchases' at specific locations but does not detail what specific items or categories of products are eligible for purchase.

```
106 CMR 364 > DETERMINING > 364.900 Delivery of Benefits

Eligible households shall be issued SNAP benefits for each month of eligibility. SNAP benefits can be accessed by using an Electronic Benefit Transfer (EBT) card for food purchases at grocery and other participating stores and farmers markets.
```

#### Rank 5 — PARTIAL (sim 0.512)

- **Chunk ID**: `cmr_sec_360_120__000`
- **Section**: `360.120` — Special Uses of SNAP Benefits
- **Chunk position**: 1 / 6
- **Program**: SNAP
- **Hierarchy**: (A) Communal Dining.
- **Judge reason**: Addresses specific authorized uses of SNAP benefits (prepared meals at communal dining) but doesn't comprehensively answer what SNAP benefits can generally be used to purchase

```
106 CMR 360 > GENERAL > 360.120 Special Uses of SNAP Benefits

Certain households have been authorized to use their SNAP benefits to buy prepared meals or to make it less difficult to obtain food. These authorized special uses of SNAP benefits are:
(A) Communal Dining.
(1) Eligible Household Members. Eligible household members 60 years of age or older or Supplemental Security Income (SSI) recipients and their spouses may use SNAP benefits to buy meals prepared especially for them at communal dining facilities authorized by the Food and Nutrition Service (FNS) for that purpose.
(2) Communal Dining Facilities. A communal dining facility is a public or nonprofit private establishment, approved by FNS, that prepares and serves meals for elderly persons, or for SSI recipients and their spouses. These facilities include senior citizen centers, apartment buildings occupied primarily by elderly persons and SSI recipients and their spouses, and federally subsidized housing for the elderly at which meals are prepared for and served to the residents.
```


### cmr_037 — TCAP application interview (rank-1: PARTIAL)

**Question**: How do I apply for TAFDC and what happens at the application interview  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `702.120`  
**Notes**: 702.120 The Application Interview (covers chapter 702 which is otherwise unrepresented)  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.492)

- **Chunk ID**: `cmr_sec_702_115__001`
- **Section**: `702.115` — Filing of Applications
- **Chunk position**: 2 / 3
- **Program**: EA
- **Hierarchy**: (B) Definition.
- **Judge reason**: Defines what an application is and mentions an intake interview, but doesn't explain how to apply or what actually happens during the interview process.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.115 Filing of Applications > (B) Definition.

(B) Definition. An application is a signed and dated request for assistance. The application is filed when the applicant signs and dates the prescribed forms. The application is completed by the worker during an intake interview. An application is different from an inquiry, which is simply a request for information about the TAFDC program or its eligibility requirements. An inquiry may result in an application, referral to another agency, or no further action.
```

#### Rank 2 — PARTIAL (sim 0.472)

- **Chunk ID**: `cmr_sec_702_120__003`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 4 / 9
- **Program**: EA
- **Hierarchy**: (E) Related Benefits and Services.
- **Judge reason**: Addresses what happens during the application interview regarding related benefits, but does not explain how to apply for TAFDC or cover the full scope of the interview process.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (E) Related Benefits and Services.

(E) Related Benefits and Services. The worker must inform the applicant that eligibility for TAFDC or EAEDC benefits will confer eligibility for MassHealth as specified in the regulations of the Division of Medical Assistance; that he or she may choose to apply for SNAP benefits as part of the application and that SNAP eligibility will be determined according to SNAP eligibility criteria; and that if he or she is found ineligible for TAFDC or EAEDC he or she may make a separate application for MassHealth, and/or SNAP benefits. The worker must make any necessary referrals for other benefits or services, such as child care. See 106 CMR 705: Related Benefits.
```

#### Rank 3 — PARTIAL (sim 0.453)

- **Chunk ID**: `cmr_sec_702_110__000`
- **Section**: `702.110` — The Application Process
- **Program**: EA
- **Judge reason**: Defines what the application process is but doesn't explain how to apply or what happens at the interview itself.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.110 The Application Process

The application process consists of all the activities used to determine the eligibility of a TAFDC or EAEDC applicant. These activities start with the filing of an application and concluded with a final disposition of the application.
```

#### Rank 4 — PARTIAL (sim 0.439)

- **Chunk ID**: `cmr_sec_702_120__000`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 1 / 9
- **Program**: EA
- **Hierarchy**: (A) Completion of Interviews.
- **Judge reason**: Addresses what happens at the application interview but does not explain how to apply for TAFDC or the initial application process.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview

Each determination of eligibility may include a face-to-face interview with the applicant. Application Activities
(A) Completion of Interviews. The worker is responsible for the completion of the application interview form, which is then signed by the applicant. The worker is responsible for assuring that the information recorded accurately represents what the applicant states about his or her circumstances.
```

#### Rank 5 — PARTIAL (sim 0.436)

- **Chunk ID**: `cmr_sec_702_120__006`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 7 / 9
- **Program**: EA
- **Hierarchy**: (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
- **Judge reason**: Addresses what happens during the application interview (PATH and Initial Job Search requirements) but does not explain how to apply for TAFDC or the general application process.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.

or insufficient participation in the Program by the 60th day after application, the entire case will be terminated.
(3) Under PATH, certain TAFDC applicants may also be subject to the Initial Job Search Program:
(a) Applicants who are 18 years of age or older and not provided with a Work Ready Job Diversion referral under 106 CMR 702.125(G)(3), and who will not be exempt from the Work Program (See 106 CMR 703.150: TAFDC Work Program) or have a pending request for an exemption must provide evidence of job search in the 60-day period from the date of application.
(b) Applicants subject to the Initial Job Search Program must provide evidence of three job search contacts. The frequency of reporting of such contacts will be determined by the Department.
(c) If no evidence of Initial Job Search contacts are provided prior to day 30 of the application, the TAFDC application will be denied for the grantee and any other adult subject to the requirement. If otherwise eligible, the remainder of the assistance unit will be approved. If contacts are made by day 30, and the assistance unit is otherwise found eligible for TAFDC, the entire case will be approved. If the entire case is approved but there are no further contacts or insufficient contacts made by the 60th day after application, the grantee and any other adult subject to the requirement will be terminated.
(d) Any job search under PATH done on-line must be done on a website approved by the Department.
```

