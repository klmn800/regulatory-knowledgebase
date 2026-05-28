# CMR Retrieval Benchmark — voyage-context-3-modeB-noprefix

**Run**: 2026-05-04T13:18:25  
**Source**: cmr  
**Label**: voyage-context-3-modeB-noprefix  
**Top-N retrieved + judged**: 5  
**Embedding model**: `voyage-context-3`  
**Collection suffix**: `_vctx3_noprefix`  
**Judge model**: `claude-haiku-4-5-20251001`  
**Methodology**: LLM-as-judge — Claude Haiku rates each chunk RELEVANT / PARTIAL / IRRELEVANT.  
**Benchmark**: CMR retrieval benchmark v2 — covers all 18 chapters, mixed difficulty, includes adversarial cases for hybrid/rerank testing  

## Summary

| Metric | Value | Notes |
|---|---|---|
| Relevance@1 | 22/37 (59%) | Did rank 1 = RELEVANT? |
| Relevant@5 (avg) | 1.62 / 5 | Avg # of RELEVANT chunks in top 5 |
| Useful@5 (avg) | 4.54 / 5 | Avg # of (RELEVANT or PARTIAL) chunks in top 5 |
| Mean rank-weighted score | 1.780 / 2.7 | Sum of (weight × score) over top 5; weights [1.0, 0.7, 0.5, 0.3, 0.2]; score RELEVANT=1.0 / PARTIAL=0.5 / IRRELEVANT=0.0 |

## Quick Summary Table

| # | ID | Topic | Rank-1 Judge | Rank-1 Sim Score | Relevant@5 | Useful@5 | RW |
|---|---|---|---|---|---|---|---|
| 1 | cmr_001 | SNAP asset limit | **PARTIAL** | 0.607 | 0 | 4 | 1.25 |
| 2 | cmr_002 | SNAP vehicle exclusion | RELEVANT | 0.570 | 1 | 3 | 1.40 |
| 3 | cmr_003 | SNAP shelter deduction | **PARTIAL** | 0.522 | 2 | 5 | 1.85 |
| 4 | cmr_004 | SNAP self-employment income | RELEVANT | 0.565 | 4 | 5 | 2.60 |
| 5 | cmr_005 | SNAP excluded income | RELEVANT | 0.595 | 5 | 5 | 2.70 |
| 6 | cmr_006 | SNAP ABAWD exemptions | RELEVANT | 0.597 | 2 | 5 | 1.95 |
| 7 | cmr_007 | SNAP application processing time | RELEVANT | 0.548 | 2 | 5 | 2.10 |
| 8 | cmr_008 | SNAP application filing | RELEVANT | 0.590 | 1 | 5 | 1.85 |
| 9 | cmr_009 | SNAP noncitizen eligibility | RELEVANT | 0.580 | 4 | 5 | 2.60 |
| 10 | cmr_010 | SNAP restoration | RELEVANT | 0.572 | 2 | 5 | 2.10 |
| 11 | cmr_011 | SNAP recertification | RELEVANT | 0.538 | 3 | 5 | 2.10 |
| 12 | cmr_012 | SNAP categorical eligibility | RELEVANT | 0.560 | 1 | 5 | 1.85 |
| 13 | cmr_013 | SSP eligibility | **PARTIAL** | 0.415 | 2 | 5 | 1.95 |
| 14 | cmr_014 | SSP payment standards | **PARTIAL** | 0.368 | 0 | 4 | 1.20 |
| 15 | cmr_015 | fair hearings general | **PARTIAL** | 0.552 | 3 | 5 | 2.05 |
| 16 | cmr_016 | hearing time limits | RELEVANT | 0.512 | 1 | 5 | 1.85 |
| 17 | cmr_017 | IPV definition | RELEVANT | 0.421 | 2 | 5 | 2.20 |
| 18 | cmr_018 | SNAP IPV penalties | **PARTIAL** | 0.529 | 2 | 5 | 1.95 |
| 19 | cmr_019 | TAFDC vs EAEDC | **PARTIAL** | 0.472 | 0 | 5 | 1.35 |
| 20 | cmr_020 | TAFDC 24-month limit | RELEVANT | 0.518 | 2 | 5 | 2.10 |
| 21 | cmr_021 | TAFDC work program | RELEVANT | 0.530 | 3 | 5 | 2.10 |
| 22 | cmr_022 | TAFDC asset limit | **PARTIAL** | 0.528 | 0 | 4 | 1.20 |
| 23 | cmr_023 | EAEDC disability | **PARTIAL** | 0.522 | 1 | 5 | 1.60 |
| 24 | cmr_024 | ESP overview | **PARTIAL** | 0.435 | 0 | 5 | 1.35 |
| 25 | cmr_025 | FEP overview | RELEVANT | 0.581 | 2 | 5 | 2.20 |
| 26 | cmr_026 | TAFDC MassHealth | **PARTIAL** | 0.535 | 0 | 5 | 1.35 |
| 27 | cmr_027 | TAFDC overpayments | RELEVANT | 0.462 | 2 | 5 | 1.95 |
| 28 | cmr_028 | identity verification | RELEVANT | 0.411 | 4 | 5 | 2.55 |
| 29 | cmr_029 | SNAP household composition | RELEVANT | 0.576 | 3 | 5 | 2.30 |
| 30 | cmr_030 | SNAP benefit calculation | RELEVANT | 0.513 | 2 | 5 | 2.20 |
| 31 | cmr_031 | section number lookup | **IRRELEVANT** | 0.182 | 0 | 0 | 0.00 |
| 32 | cmr_032 | ADH acronym | **IRRELEVANT** | 0.313 | 0 | 2 | 0.40 |
| 33 | cmr_033 | EPSDT acronym | **PARTIAL** | 0.514 | 0 | 1 | 0.50 |
| 34 | cmr_034 | PA household defined term | **PARTIAL** | 0.518 | 1 | 5 | 1.60 |
| 35 | cmr_035 | EDP defined term | RELEVANT | 0.382 | 1 | 5 | 1.85 |
| 36 | cmr_036 | SNAP allowed uses | RELEVANT | 0.567 | 1 | 5 | 1.85 |
| 37 | cmr_037 | TCAP application interview | RELEVANT | 0.614 | 1 | 5 | 1.85 |

---

## Per-Question Detail

Top 5 results per question with judge verdicts and full chunk text. Use this to spot-check whether the judge's rating makes sense.

### cmr_001 — SNAP asset limit (rank-1: PARTIAL)

**Question**: How much can a SNAP household have in bank accounts  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.110`  
**Notes**: 363.110 Asset Eligibility Limits  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.25  

#### Rank 1 — PARTIAL (sim 0.607)

- **Chunk ID**: `cmr_sec_363_130__005`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 6 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: The chunk discusses verification procedures for bank accounts but does not specify the actual asset limit amount that SNAP households can have.

```
(4) Verification of Bank Account Balances. Bank account balances must be verified at application, recertification, and at times of reported change. The amount shall be verified by bank books, bank statements or online printouts that show the bank balance within 45 days of the date of the application, recertification, or reported change. If at recertification the household member declares a balance of $25 or less in an account, other than a checking account, verification shall not be required if the balance was $25 or less at the last eligibility determination and the account balance, in combination with other countable assets, is not over the asset limit. The household's declaration shall be recorded in the case record.
```

#### Rank 2 — PARTIAL (sim 0.593)

- **Chunk ID**: `cmr_sec_363_130__002`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 3 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: Defines what bank accounts are and how they're counted as assets, but doesn't specify the actual dollar limit for SNAP household bank account holdings.

```
(B) Bank Accounts.
(1) Definition. Bank accounts may be in the form of savings, checking, trust accounts, term certificates, or other types of accounts held at banks, savings or loan institutions. Funds in a bank account are considered available when a member of the household has both ownership of, and access to, the balance of funds in the account.
(2) Joint Bank Accounts. If a household member is a co-holder of a joint bank account, the entire amount on deposit shall be considered available as an asset unless the household demonstrates otherwise. Crowdfunding accounts (e.g., GoFundMe and Kickstarter) shall also be considered liquid resources if funds are accessible to the household. The actual value of funds accessible to an accountholder shall be counted as a liquid resource. A household member who states that he or she is not the owner, or is only partial owner, of the funds must verify ownership of the funds. A household member who states that he or she has no access, or only partial access to the funds must verify lack of access.
```

#### Rank 3 — PARTIAL (sim 0.558)

- **Chunk ID**: `cmr_sec_363_110__000`
- **Section**: `363.110` — Asset Eligibility Limits
- **Program**: SNAP
- **Judge reason**: The chunk discusses asset limits for SNAP households but does not specify the actual dollar amounts, instead referring users to www.mass.gov for the current limits set by USDA.

```
The asset eligibility limits in 106 CMR 363.110 do not apply to categorically eligible households as defined in 106 CMR 365.180: Categorically Eligible Assistance Units. These asset eligibility limits, however, shall be applied to any household with a member disqualified from receiving SNAP benefits due to failing to comply with the SNAP Work Program; or for any of the reasons listed in 106 CMR 367.800: Disqualification Penalties. Non-SSI elder and/or disabled households with income above the Categorical Eligibility Gross Income standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards shall also be subject to asset limits. The total value of countable assets owned by a household subject to asset limits shall not exceed the following:
(A) The amount authorized by the United States Department of Agriculture and posted on www.mass.gov for any household that includes at least one member who is aged 60 or over and/or disabled as described and verified in accordance with 106 CMR 361.210 (A) and (B).
(B) The amount authorized by the United States Department of Agriculture and posted on www.mass.gov for all other households. The household shall report all assets owned or anticipated to be received within the certification period. The equity value of all countable assets will be used to determine if the household is within asset eligibility limits. (Mass. Register #1522, 5/24/2024)
```

#### Rank 4 — PARTIAL (sim 0.555)

- **Chunk ID**: `cmr_sec_363_130__001`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 2 / 10
- **Program**: SNAP
- **Hierarchy**: (A) Cash.
- **Judge reason**: Defines what cash is and how it's verified, but doesn't specify the actual limit amount a SNAP household can have in bank accounts.

```
(A) Cash.
(1) Definition. Cash is currency, checks, or bank drafts in the possession of, or available to, the household.
(2) Verification. The amount of cash shall be countable at application, recertification, and when a change is reported. The household's declaration of the amount of cash available shall be sufficient verification.
```

#### Rank 5 — IRRELEVANT (sim 0.549)

- **Chunk ID**: `cmr_sec_363_130__004`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 5 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: This chunk discusses verification procedures for joint bank accounts and co-holders, not the actual asset limits for SNAP households.

```
listed as a co-holder solely as a convenience to the other co-holder to conduct bank transactions on his or her behalf, proof of the age, relationship, physical or mental condition, or place of residence of the co-holder shall also be provided;
6. A signed, notarized statement from the household member and from either one of the individuals listed in the joint account, or a person who established or contributed to the account, that the household member had no knowledge of the existence of the account; and
7. If only one of the items listed in 106 CMR 363.130(B)(3)(b)1. through 7. is available and if the other individual(s) listed on the account or who has opened or contributed to the account is unavailable, unable or unwilling to provide a statement, the household member may provide a signed statement attesting under penalties of perjury as to the ownership of funds in the account. A document or piece of evidence submitted to verify a particular fact shall not count as more than one verification under 106 CMR 363.130(B)(3)(b)1. through 7. However, a document, piece of evidence or a statement may address more than one fact needed for verification.
```


### cmr_002 — SNAP vehicle exclusion (rank-1: RELEVANT)

**Question**: What vehicles are exempt from the SNAP asset test  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.140` — judge picked rank-1 RELEVANT chunk in section `363.140` (section-author intuition agrees)  
**Notes**: 363.140 Noncountable Assets  
**Scores**: Relevant@5 = 1, Useful@5 = 3, rank-weighted = 1.40  

#### Rank 1 — RELEVANT (sim 0.570)

- **Chunk ID**: `cmr_sec_363_140__002`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 3 / 14
- **Program**: SNAP
- **Hierarchy**: (C) Education Savings Accounts.
- **Judge reason**: The chunk directly states that vehicles are noncountable assets under the SNAP asset test, providing specific examples of exempt vehicles.

```
(C) Education Savings Accounts. Section 529 qualified tuition programs, and Coverdell education savings accounts are noncountable assets.
(D) Vehicles. Vehicles, whether licensed or unlicensed, are noncountable. Vehicles include, but are not limited to, cars, trucks, boats and tractors.
```

#### Rank 2 — IRRELEVANT (sim 0.487)

- **Chunk ID**: `cmr_sec_363_140__010`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 11 / 14
- **Program**: SNAP
- **Hierarchy**: (H) Other Noncountable Assets. The following assets are noncountable:
- **Judge reason**: The chunk discusses noncountable assets including educational loans, energy assistance, and relocation payments, but does not address vehicle exemptions from the SNAP asset test.

```
(5) Educational Loans, Grants, and Scholarships Any financial assistance paid to a student such as a financial aid package, grant, loan or scholarship for the purposes of obtaining a degree or certificate from an institution of higher education is a noncountable asset. Permissible purposes may include, without limitation, room and board, tuition and fees, and other ancillary costs associated with the costs of obtaining a degree or certificate at an institution of higher education.
(6) Assets Exempt by Law. Certain assets are noncountable for SNAP purposes by a specific provision in federal law, including, but not limited to:
(a) Coupons under a WIC Demonstration Project that can be exchanged for food at farmers' markets;
(b) Highway Relocation assistance payments, Urban Renewal Assistance payments, disaster relief payments used for relocation, and payments from private agencies used for relocation;
(c) State and federal earned income credits (EIC), whether received as an advance payment or as part or all of an income tax refund, in the month of receipt and the following month;
(d) Payments or allowances made to or on behalf of a household for energy assistance under any federal, state, or local law. These payments or allowances must be clearly identified as energy assistance by the legislative body authorizing the program or providing the funds;
(e) Nonliquid assets with a lien in place as a result of taking out a business loan if the
```

#### Rank 3 — PARTIAL (sim 0.486)

- **Chunk ID**: `cmr_sec_363_140__001`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 2 / 14
- **Program**: SNAP
- **Hierarchy**: (B) Household and Personal Goods, Life Insurance and Pension Funds.
- **Judge reason**: The chunk discusses noncountable assets in SNAP but does not specifically address vehicle exemptions from the asset test.

```
(B) Household and Personal Goods, Life Insurance and Pension Funds.
(1) Household goods and personal effects, including one burial lot per household member and the value of a prepaid funeral arrangement, not to exceed $1,500, are noncountable assets. A prepaid funeral arrangement may include a contract with a funeral director or a separately identifiable trust fund. Use of any portion of this asset is countable if used for purposes other than funeral or burial arrangements in accordance with 106 CMR 363.130.
(2) The cash value of life insurance policies is noncountable provided the insurance policies are not cashed.
(3) Pension funds are noncountable assets. These include, but are not limited to, pension or traditional defined-benefits plans, 401(k)s, 501(c)(18)s, 403(b)s, 457s, Federal Employee Thrift Savings plans, Keogh plans, Individual Retirement Accounts (IRAs), Roth IRAs, Simple IRAs, Simplified Employer plans, Profit Sharing plans, and Cash Balance plans.
```

#### Rank 4 — PARTIAL (sim 0.481)

- **Chunk ID**: `cmr_sec_363_140__000`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 1 / 14
- **Program**: SNAP
- **Hierarchy**: (A) Home and Lot.
- **Judge reason**: The chunk discusses noncountable assets for SNAP but does not specifically address vehicle exemptions, which is what the user is asking about.

```
The following assets are not countable when determining the total value of assets available to a household.
(A) Home and Lot. The home and surrounding property that is not separated from the home by intervening property owned by others is noncountable, including:
(1) Property separated from the home by a public right of way, such as a road.
(2) The home and surrounding property when temporarily unoccupied for reasons of employment, training for employment, illness, vacation, or uninhabitability caused by casualty or natural disaster, provided that the household intends to return.
(3) The value of a lot purchased, or in the process of being purchased, to build a home if the household does not already own a home and, if the new home is partially completed, the value of the partially completed home.
(4) Household belongings such as furniture, appliances, household decorations, linens and cookware; personal belongings such as jewelry, books and toys, even if of more than usual value.
(5) Property to which the household has no ready access, such as property that is the subject of legal proceedings (e.g., probate, divorce suits, etc.), and irrevocable trust funds that were placed in trust at least 12 month before application for SNAP benefits.
```

#### Rank 5 — IRRELEVANT (sim 0.479)

- **Chunk ID**: `cmr_sec_363_140__003`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 4 / 14
- **Program**: SNAP
- **Hierarchy**: (E) Income Producing Property.
- **Judge reason**: The chunk discusses income-producing property assets in general, not vehicle exemptions from the SNAP asset test.

```
(E) Income Producing Property. Income producing property is a noncountable asset when it is essential to employment or self-employment, or when it annually produces income consistent with its fair market value. The income derived from such property, however, shall be countable.
(1) Property essential to the employment or self-employment of a household member includes work-related equipment such as the tools of a tradesperson or the machinery of a farmer, and property such as farm land. Property essential to the self-employment of a household member engaged in farming shall continue to be excluded for one year after the household member terminates his or her self-employment from farming. Property that is noncountable because it is essential to employment or self-employment need not produce income consistent with its fair market value.
(2) Property that annually produces income consistent with its fair market value, even if used only on a seasonal basis, is noncountable, including rental and vacation homes. Income shall be considered consistent with fair market value if the income produced is as much as the property could reasonably be expected to produce and is comparable with income produced by similar property in the same area. When it is necessary to determine if property is annually producing income consistent with its fair market value, the worker shall contact local realtors, local tax assessors, the
```


### cmr_003 — SNAP shelter deduction (rank-1: PARTIAL)

**Question**: What is the SNAP shelter deduction  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364.400`  
**Notes**: 364.400 Shelter/Excess Shelter Deduction  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_365_630__001`
- **Section**: `365.630` — Certification of Residents of Group Living Arrangements and Treatment Centers
- **Chunk position**: 2 / 4
- **Program**: SNAP
- **Hierarchy**: (B) Determining Shelter Costs for Residents of Group Living Arrangements, Dru...
- **Judge reason**: Addresses how shelter costs are calculated in specific group living situations but does not explain the general SNAP shelter deduction or standard shelter deduction rules.

```
(B) Determining Shelter Costs for Residents of Group Living Arrangements, Drug or Alcohol Treatment Centers. When residents of group living arrangements or drug and alcohol treatment centers make a combined payment for meals and lodging (shelter), the cost of shelter shall be equal to the difference between the amount of the room and board payment and the maximum SNAP benefit allotment for the appropriate SNAP household size.
```

#### Rank 2 — RELEVANT (sim 0.519)

- **Chunk ID**: `cmr_sec_364_400__009`
- **Section**: `364.400` — Determining Deductions
- **Chunk position**: 10 / 13
- **Program**: SNAP
- **Hierarchy**: (G) Shelter Deduction.
- **Judge reason**: The chunk directly defines and explains the SNAP shelter deduction, including what expenses qualify and how it is calculated.

```
(G) Shelter Deduction. A deduction is allowed for monthly shelter expenses and utility costs in excess of 50% of the household's income after all the above deductions have been allowed. This shelter deduction amount is posted at www.mass.gov/dta. Paper copies are available upon request. This limit on the shelter deduction amount does not apply if the household contains a member who is elderly or disabled in accordance with 106 CMR 361.210: Elderly or Disabled Individuals.
(1) Shelter Expenses.
(a) Continuing charges for the shelter occupied by the household, including rent and mortgage payments, or other continuing charges leading to the ownership of shelter, such as loan repayments for the purchase of a mobile home, including interest on such payments, or condominium fees; NON-TEXT PAGE
(b) Property taxes, state and local assessments, and insurance on the structure itself, but not the separate expense of insuring furniture or personal belongings;
(c) Shelter expenses as described in 106 CMR 364.400(G)(1)(a) and (b) for a home not actually occupied by the household because of employment or training away from home, illness, or abandonment of the home due to natural disaster or casualty loss. Shelter expenses for a vacated home shall be included in the shelter deduction if the household intends to return to the home, the current occupants of the home, if any, are not claiming a shelter deduction for SNAP purposes, and the home is not leased or rented
```

#### Rank 3 — PARTIAL (sim 0.519)

- **Chunk ID**: `cmr_sec_365_520__003`
- **Section**: `365.520` — Disqualified Nonhousehold Members
- **Chunk position**: 4 / 6
- **Program**: SNAP
- **Hierarchy**: (B) Nonhousehold Members Disqualified from Federal Snap Benefits Due to Ineli...
- **Judge reason**: The chunk mentions the shelter expense deduction as one of several deductions but does not explain what the SNAP shelter deduction actually is or how it is calculated.

```
(3) Deductible Expenses.
(a) For purposes of calculating the maximum SNAP benefit the household would be entitled to if all members were SNAP-eligible, all deductions shall be applied to the household in accordance with 106 CMR 364.600(C)(1): Step One.
(b) For purposes of calculating the SNAP benefits of the SNAP-eligible household members:
1. The standard deduction shall be applied to the SNAP-eligible household;
2. The homeless deduction shall be applied to the SNAP-eligible household if the SNAP-eligible household meets the requirements at 106 CMR 364.400(F): Homeless Shelter/Utility Deduction;
3. The shelter expense deduction shall be applied to the SNAP-eligible household if the SNAP-eligible household has income;
4. The earned income deduction shall be applied as follows: a. The earned income deduction of a SNAP-eligible member with earnings shall be applied to the SNAP-eligible household; and b. The earned income deduction of a nonhousehold member with earnings who is a legal noncitizen ineligible for federal SNAP benefits shall not be applied to the SNAP-eligible household;
5. A deduction for child support paid shall be applied as follows: a. A deduction for child support paid by an SNAP-eligible member shall be applied to the SNAP-eligible household.; and b. A deduction for child support paid by a nonhousehold member who is a legal noncitizen ineligible for federal SNAP benefits shall not be applied to the SNAP-eligible household;
```

#### Rank 4 — RELEVANT (sim 0.518)

- **Chunk ID**: `cmr_sec_364_500__007`
- **Section**: `364.500` — Determining Net Income
- **Chunk position**: 8 / 8
- **Program**: SNAP
- **Hierarchy**: (K) Shelter Deduction.
- **Judge reason**: Directly explains what the SNAP shelter deduction is, how it's calculated, and notes that the specific amount is posted on the DTA website.

```
(K) Shelter Deduction. Subtract the full amount of the excess shelter expense if the household contains an elderly or disabled member who meets one of the requirements of 106 CMR 361.210: Elderly or Disabled Individuals. For all other households, subtract the excess shelter expense up to the maximum deduction amount. This shelter deduction amount is posted at www.mass.gov/dta.
```

#### Rank 5 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_365_550__003`
- **Section**: `365.550` — Residents of Shelters for Battered Individuals and Their Children
- **Chunk position**: 4 / 5
- **Program**: SNAP
- **Hierarchy**: (D) Financial Eligibility and Deductible Expenses.
- **Judge reason**: The chunk discusses shelter expenses in the context of financial eligibility for shelter residents but does not explain what the SNAP shelter deduction is or how it is calculated.

```
(D) Financial Eligibility and Deductible Expenses. Shelter residents who apply as separate households shall be certified solely on the basis of their income, assets, and the shelter expenses for which they are liable. The income, assets, and shelter expenses of their former household shall be disregarded. Assets held jointly with members of the former household shall be handled in accordance with 106 CMR 363.120: Jointly-owned Assets. Room payments to the shelter shall be considered shelter expenses.
```


### cmr_004 — SNAP self-employment income (rank-1: RELEVANT)

**Question**: How is self-employment income calculated for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.220` — judge picked rank-1 RELEVANT chunk in section `365.970` (section-author intuition disagrees with judge)  
**Notes**: 363.220 Earned Income  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.60  

#### Rank 1 — RELEVANT (sim 0.565)

- **Chunk ID**: `cmr_sec_365_970__002`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Hierarchy**: (C) Determining Monthly SNAP Income. To determine the monthly SNAP income for
- **Judge reason**: Directly explains how monthly SNAP income from self-employment is calculated by adding net self-employment income to other earned income and addresses loss offset provisions for farmers.

```
(C) Determining Monthly SNAP Income. To determine the monthly SNAP income for households with income from self-employment enterprises, the monthly net self-employment income is added to any other earned income, or in the case of unearned rental income to other unearned income, received by the household. If the cost of producing self-employment income of farmers exceeds the income derived from self-employment, such losses shall be offset against any other countable income in the household, provided that the farmer has received or is anticipating receiving annual gross proceeds of $1000 or more from the farming enterprise; and provided that whatever base is used to determine any net income from self-employment farm operations, such as the previous year's tax return or current income, the same base is used in determining any net loss. Losses shall be prorated over the year in a manner comparable to that used to prorate farm self-employment income. REGULATORY AUTHORITY 106 CMR 364.000: M.G.L. c. 18, § 10. (PAGES 811 THROUGH 814 ARE RESERVED FOR FUTURE USE.)
```

#### Rank 2 — RELEVANT (sim 0.556)

- **Chunk ID**: `cmr_sec_365_970__000`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Averaged Income.
- **Judge reason**: Directly explains the method for calculating self-employment income for SNAP by describing the averaging process and treatment of gross income and expenses.

```
(A) Averaged Income. For the period of time over which self-employment is determined, add all gross self-employment income (including capital gains), exclude the cost of producing the self-employment income, and divide the self-employment income by the number of months over which the income will be averaged.
```

#### Rank 3 — RELEVANT (sim 0.548)

- **Chunk ID**: `cmr_sec_365_960__000`
- **Section**: `365.960` — Averaging Self-employment Income and Assigning Certification Periods
- **Program**: SNAP
- **Judge reason**: Directly explains how self-employment income is calculated for SNAP, including the 12-month averaging method and adjustments for substantial business changes.

```
(A) Self-employment income that represents a household's annual support shall be averaged over a 12-month period, even if the income is received in a shorter period of time during that 12 months. For example, self-employment income received by farmers shall be averaged over a 12-month period if the income is intended to support the farmer on an annual basis. This self-employment income shall be annualized even if the household receives income from other sources in addition to self-employment. However, if the averaged annualized amount does not accurately reflect the household's actual circumstances because the household has experienced a substantial increase or decrease in business, the self-employment income shall be calculated on anticipated earnings. The worker shall not calculate self-employment income on the basis of prior income (documented by income tax returns) when the household has experienced a substantial increase or decrease in business.
```

#### Rank 4 — RELEVANT (sim 0.547)

- **Chunk ID**: `cmr_sec_365_970__001`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (B) Anticipated Income.
- **Judge reason**: Directly explains how self-employment income is calculated for SNAP, specifically addressing the anticipated income method and treatment of capital gains and business expenses.

```
(B) Anticipated Income. For those households whose self-employment income is not averaged but is instead calculated on an anticipated basis, add any capital gains the household anticipates it will receive in the next 12 months, starting with the date the application is filed, and divide this amount by 12. This amount shall be used in successive certification periods during the next 12 months except that a new average monthly amount shall be calculated for this 12 month period if the anticipated amount of capital gains changes. Then add the anticipated monthly amount of capital gains to the anticipated monthly self-employment income, and subtract the cost of producing self-employment income. Except for depreciation, the cost of producing the self-employment income shall be calculated by anticipating the monthly allowable costs of producing the self-employment income. Capital gains is the gain the household makes from the sale of a capital asset, such as real property used to carry out the household's business enterprise, in excess of the value of the property or cost of the property.
```

#### Rank 5 — PARTIAL (sim 0.539)

- **Chunk ID**: `cmr_sec_365_910__000`
- **Section**: `365.910` — Roomer, Boarder, Rental Income
- **Program**: SNAP
- **Judge reason**: The chunk identifies specific types of self-employment income (roomers, rental property, boarders) but doesn't explain the actual calculation method, instead referring to other regulatory sections for the procedures.

```
Income from roomers, rental property, and boarders of a commercial boarding house is considered self-employment income for Program purposes. A household's countable income from these self-employment enterprises should be determined in accordance with the instructions in 106 CMR 365.910. The income a household receives from a boarder, other than that received by a household who owns and operates a commercial boarding house, is also considered self-employment income in accordance with the procedures set forth in 106 CMR 365.200.
```


### cmr_005 — SNAP excluded income (rank-1: RELEVANT)

**Question**: What income is excluded from SNAP eligibility determination  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.230` — judge picked rank-1 RELEVANT chunk in section `363.230` (section-author intuition agrees)  
**Notes**: 363.230 Noncountable Income  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.595)

- **Chunk ID**: `cmr_sec_363_230__000`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 1 / 19
- **Program**: SNAP
- **Hierarchy**: (A) In-kind Income and Cash Contributions.
- **Judge reason**: The chunk directly addresses what income is excluded from SNAP eligibility determination by providing specific examples of excluded income types.

```
The following kinds of income will be excluded when determining a household's eligibility and benefit level.
(A) In-kind Income and Cash Contributions. Any gain or benefit not in the form of money and provided directly to the household is excluded from income. For example, meals, clothing, public housing, or produce from a garden would be excluded from income. Any cash contributions from a non-legally responsible person (i.e., someone without a court order or other binding agreement) that are restricted for a specific purpose and provide for a portion of any rent or mortgage, fuel, utilities and/or food or other needs are excluded from income.
```

#### Rank 2 — RELEVANT (sim 0.566)

- **Chunk ID**: `cmr_sec_363_230__011`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 12 / 19
- **Program**: SNAP
- **Hierarchy**: (J) The Cost of Producing Self-employment Income.
- **Judge reason**: The chunk directly addresses income exclusions for SNAP eligibility by listing specific types of income that are excluded from income determination under federal law and Massachusetts regulations.

```
(J) The Cost of Producing Self-employment Income. The cost of producing self-employment income is excluded from income in accordance with 106 CMR 365.900 through 365.970.
(K) Income Excluded by Law. Certain income is excluded for SNAP purposes by specific provisions in federal law. The following listing of excludable income includes, but is not limited to:
(1) HighwayRelocation assistance payments, Urban Renewal Assistance payments, disaster relief payments used for relocation, and payments from private agencies used for relocation;
(2) The tax-exempt portions of payments made under the Alaska Native Claims Settlement Act;
(3) Funds distributed to or held in trust for members of any Indian tribe pursuant to a judgment of the Indian Claims Settlements or the Secretary of the Interior;
(4) Payments to Native Americans under Public Laws 92-254, 93-134, 94-114, 94-540, 96-420, 97- 458, 98-64 and 102-71, including interest income from these payments;
(5) Payments or reimbursements given to, volunteers serving as foster grandparents, senior health aides, senior companions, or serving in the Service Corps of Retired Executives, in VISTA, or in any other program established under the Domestic Service Act of 1973;
```

#### Rank 3 — RELEVANT (sim 0.554)

- **Chunk ID**: `cmr_sec_363_230__012`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 13 / 19
- **Program**: SNAP
- **Hierarchy**: (K) Income Excluded by Law.
- **Judge reason**: The chunk directly lists specific types of income that are excluded from SNAP eligibility determination, which directly answers the user's question.

```
(6) Youthbuild or Americorps allowances, earnings or payments to individuals participating in those programs;
(7) Payments of state or federal earned income credits (EIC) whether received as advance payments of earned income credits or as part or all of an income tax refund;
(8) Energy assistance payments or allowances as described below:
(a) Any payments or allowances made for the purpose of providing energy assistance under any federal law (other than Part A of Title IV of the Social Security Act (42 USC 601, et seq.)), or
(b) A one-time payment or allowance made under a federal or state law for the costs of weatherization or emergency repair or replacement of an unsafe or inoperative furnace or other heating or cooling device;
(9) Funds received by individuals under the Older American Community Service Employment Program pursuant to the Older Americans Act Amendments of 1987, Public Law 100-175;
(10) Cash donations based on need that are received from one or more private nonprofit charitable organizations, not in excess of $300 aggregate per quarter, pursuant to the Charitable Assistance and Food Bank Act of 1987, Public Law 100-232;
```

#### Rank 4 — RELEVANT (sim 0.552)

- **Chunk ID**: `cmr_sec_363_230__001`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 2 / 19
- **Program**: SNAP
- **Hierarchy**: (B) Vendor Payments.
- **Judge reason**: The chunk directly addresses income exclusions for SNAP eligibility by explaining that vendor payments are excluded from income determination.

```
(B) Vendor Payments. A vendor payment is a money payment that is paid to a third party for a household expense. A vendor payment is excluded from income whenever a person or organization outside the household uses its own funds to make a direct payment to a household's creditors or to a person or organization providing a service to the household. The following are examples of excluded vendor payments:
(1) If a relative or friend who is not a household member pays the household's rent from his or her own funds directly to a landlord;
(2) Rent or mortgage payments made to landlords or mortgagees by the Department of Housing and Urban Development (HUD), or by state or local housing authorities on behalf of a household, including utility allowances paid under such programs;
(3) Payments made under the Emergency Assistance (EA) program;
(4) Payments for household expenses made to a third party and not legally owed to the household. The following are examples of such excluded vendor payments:
(a) If an employer pays an employee's rent directly to the landlord in addition to paying the employee his or her regular wages, the rent payment shall be considered an excluded vendor payment. If the employer provides housing to an employee, the value of the housing shall also be an excluded vendor payment:
(b) Payments specified by a court order or other legally binding agreement to go directly to the third party rather than to the household shall be considered excluded vendor payments; and
```

#### Rank 5 — RELEVANT (sim 0.549)

- **Chunk ID**: `cmr_sec_363_230__017`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 18 / 19
- **Program**: SNAP
- **Hierarchy**: (N) Income of SSI Recipients and PASS Funds.
- **Judge reason**: Directly addresses income exclusions for SNAP eligibility by explaining that PASS funds are excluded from income determination for SSI recipients.

```
(N) Income of SSI Recipients and PASS Funds. Income of an SSI recipient necessary for the fulfillment of a Plan for Achieving Self Support (PASS) is excluded from income. The PASS program allows persons who receive or who might qualify to receive SSI benefits to develop a plan in which the goal is to become employed. The PASS must be approved by the Social Security Administration (SSA) to permit the individual to set aside a specified amount of money to be used or deposited into a special bank account for future use. These specified funds are to be used to achieve the work goal stated in the approved PASS and shall be excluded from income in determining SNAP eligibility and benefit level. PASS funds may include, but are not limited to, earned income or unearned income, or funds from an insurance settlement. SSI benefits are not used as PASS funds and, therefore, are still considered countable income for SNAP purposes. Exclusion of PASS funds from income for SNAP purposes is verified by a copy of the PASS agreement and the PASS approval letter from the SSA. PASS funds are not counted as assets because the assets of a household member who receives SSI are excluded for SNAP purposes, in accordance with 106 CMR 363.140(H)(7).
```


### cmr_006 — SNAP ABAWD exemptions (rank-1: RELEVANT)

**Question**: What are the ABAWD work requirement exemptions  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `362.320` — judge picked rank-1 RELEVANT chunk in section `362.320` (section-author intuition agrees)  
**Notes**: 362.320 ABAWD; or possibly 365.x for SNAP work in PA households  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — RELEVANT (sim 0.597)

- **Chunk ID**: `cmr_sec_362_320__002`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Hierarchy**: (B) Exemptions.
- **Judge reason**: The chunk directly lists the specific ABAWD work requirement exemptions including age, pregnancy, living with children, and waived areas.

```
(B) Exemptions. Able-bodied Adults without Dependents are exempt from the ABAWD work program requirements if they meet the exemption criteria of 106 CMR 362.310(C). The individuals listed below are also exempt from the ABAWD work program requirements:
(1) Age. Persons younger than 18 years old or 50 years of age or older;
(2) Pregnant Women. A pregnant woman at any stage of pregnancy;
(3) Adults Living with Children Younger than 18 Years Old. Persons residing in a household where a household member is younger than 18 years old, even if the household member who is younger than 18 years old is not eligible for SNAP benefits; and
(4) Resident of a Waived Area. A person who otherwise would be required to participate in the ABAWD work program is exempt if living in an area of the state exempted by the United States Department of Agriculture.
```

#### Rank 2 — PARTIAL (sim 0.530)

- **Chunk ID**: `cmr_sec_362_310__002`
- **Section**: `362.310` — General SNAP Work Requirements
- **Chunk position**: 3 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Exemptions from General SNAP Work Requirements.
- **Judge reason**: The chunk addresses general SNAP work requirement exemptions but does not specifically address ABAWD (Able-Bodied Adults Without Dependents) exemptions, which are a distinct category with different rules.

```
(C) Exemptions from General SNAP Work Requirements. The individuals listed in 106 CMR 362.310(C)(1) through (10) are exempt from the general SNAP work requirements found at 106 CMR 362.310(A). If verification is necessary for a particular exemption, it is noted under that exemption.
(1) Age. A person younger than 16 years old or a person 60 years of age or older is exempt. A child who has his or her 16th birthday within a certification period shall fulfill the work registration requirement at the next scheduled recertification, unless the child qualifies for another exemption.
(2) Persons Physically or Mentally Unfit for Employment. Persons who are physically or mentally unfit for employment due to disability or illness, either permanently or temporarily, are exempt. If the disability or illness is not obvious, appropriate verification of physical or mental unfitness must be provided. Verification includes, but is not limited to:
(a) receipt of temporary or permanent disability benefits from a government or private source;
(b) a written, dated and signed statement from a competent medical authority stating that the person is physically or mentally unfit for employment;
(c) participation in a Massachusetts Rehabilitation Commission program or other Massachusetts-approved vocational rehabilitation program; and
(d) proof that the individual is temporarily ill and that the illness is serious enough to temporarily prevent employment.
```

#### Rank 3 — PARTIAL (sim 0.530)

- **Chunk ID**: `cmr_sec_362_320__003`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 4 / 9
- **Program**: SNAP
- **Hierarchy**: (C) Good Cause Criteria for ABAWD Work Program Requirements.
- **Judge reason**: Discusses good cause criteria for meeting ABAWD work requirements rather than exemptions from the requirements themselves.

```
(C) Good Cause Criteria for ABAWD Work Program Requirements. If an individual would have worked an average of 20 hours per week but missed hours due to good cause, the individual shall be considered to have met the work requirement if the absence from work is temporary and the individual retains his or her job. Good cause shall include circumstances beyond the individual's control, such as, but not limited to, illness, illness of another household member requiring the presence of the member, a household emergency, or the unavailability of transportation.
```

#### Rank 4 — PARTIAL (sim 0.523)

- **Chunk ID**: `cmr_sec_362_310__003`
- **Section**: `362.310` — General SNAP Work Requirements
- **Chunk position**: 4 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Exemptions from General SNAP Work Requirements.
- **Judge reason**: The chunk discusses work requirement exemptions but does not specifically identify ABAWD (Able-Bodied Adults Without Dependents) exemptions, instead covering TAFDC/EAEDC, unemployment compensation, and caretaker exemptions.

```
Persons claiming temporary unfitness for employment due to illness will be required to meet work requirements once they become physically or mentally fit.
(3) TAFDC/EAEDC Work Program Participants. A TAFDC or EAEDC client subject to and complying with the relevant program's work requirement is exempt.
(4) Unemployment Compensation Applicants and Recipients. Unemployment Compensation applicants or recipients subject to and participating in a comparable unemployment compensation work program are exempt. If the exemption claimed is questionable, the Department is responsible for verifying the exemption with the office of the State employment services agency.
(5) Caretakers. A parent or other household member responsible for the care of a dependent child under six or an incapacitated person is exempt. If the child has his or her sixth birthday within a certification period, the caregiver of the child shall fulfill the work requirements at the next scheduled recertification, unless the caregiver qualifies for another exemption. If a parent and another member of the household both claim to be responsible for the care of the same dependent child or incapacitated household member, the actual responsibility shall be determined by discussion with the applicant or client.
```

#### Rank 5 — RELEVANT (sim 0.496)

- **Chunk ID**: `cmr_sec_362_310__004`
- **Section**: `362.310` — General SNAP Work Requirements
- **Chunk position**: 5 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Exemptions from General SNAP Work Requirements.
- **Judge reason**: The chunk directly lists specific ABAWD work requirement exemptions including students, addicts/alcoholics, and employed persons with detailed criteria.

```
(6) Students. Persons enrolled at least half-time in any recognized school, including high school, a training program or institution of higher education who have met the conditions provided in 106 CMR 362.400 and 362.410 are exempt. Enrollment must be verified at application and recertification. Persons enrolled less than half-time or who experience a break in their enrollment status due to graduation, expulsion or suspension, or who drop out or otherwise do not intend to return to school do not qualify for this exemption.
(7) Addicts and Alcoholics. A regular participant, either on a resident or nonresident basis, in a drug addiction or alcohol treatment and rehabilitation program is exempt. Participation, if questionable, may be verified through the organization or institution operating the program.
(8) Employed Persons. Persons employed or self-employed are exempt if working a minimum of 30 hours weekly or receiving weekly earnings equal to or greater than the federal minimum wage multiplied by 30 hours. The guidelines for determining a client's eligibility for this exemption are as follows:
(a) Verification of earned income must establish that the amount of income is consistent with a 30-hour work week;
(b) If the income of the employed individual does not meet the preceding test but he or she still claims to be employed, the client shall be required to supply documentary evidence of the existence of an employee-employer relationship and that the number of
```


### cmr_007 — SNAP application processing time (rank-1: RELEVANT)

**Question**: How long does DTA have to process a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.080` — judge picked rank-1 RELEVANT chunk in section `361.080` (section-author intuition agrees)  
**Notes**: 361.080 Prompt Action; baseline v1 expected 361 broadly, this v2 narrows it  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.548)

- **Chunk ID**: `cmr_sec_361_080__000`
- **Section**: `361.080` — Prompt Action
- **Program**: SNAP
- **Judge reason**: Directly states that DTA must process SNAP applications and issue benefits within 30 calendar days of application, which directly answers the user's question about processing timeframes.

```
Eligible households must be given an opportunity to participate in the Supplemental Nutrition Assistance Program (SNAP) no later than 30 calendar days following their date of application. An opportunity to participate consists of the Department's issuing SNAP benefits through the EBT system before the 30-day processing standard expires. Expedited service shall be provided to households in accordance with 106 CMR 365.800: Expedited Service. Benefits must be provided retroactively to the date of application for households that complete the application process within the required time frame and are eligible to receive benefits in the month of application.
```

#### Rank 2 — PARTIAL (sim 0.514)

- **Chunk ID**: `cmr_sec_366_920__001`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) Filing an Application.
- **Judge reason**: The chunk defines when an application date is established but does not address the processing timeline or how long DTA has to process the application.

```
(A) Filing an Application. Assistance in completing SNAP applications will be available at SSA or the Department.
(B) Date of Application. If the application is filed at an SSA office, then the date of application shall be the date the identifiable SNAP application is faxed by SSA to the appropriate Transitional Assistance Office (TAO). If an application is filed at a TAO or online, the date of application shall be the date the identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office. (See 106 CMR 361.120: Date of Application.)
```

#### Rank 3 — RELEVANT (sim 0.514)

- **Chunk ID**: `cmr_sec_361_700__001`
- **Section**: `361.700` — Timeliness Standards for Processing
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Eligible Assistance Units.
- **Judge reason**: Directly states that DTA must process SNAP applications and provide eligible households an opportunity to participate within 30 calendar days of application.

```
(A) Eligible Assistance Units. Households that are found to be eligible must be provided an opportunity to participate within 30 calendar days following the date of application. An opportunity to participate consists of the Department's issuing SNAP benefits via the EBT system before the 30-day processing standard expires. When the Department misses this timeliness standard and the household is eligible for SNAP benefits in the month of application, SNAP benefits must be provided retroactive to the date of application.
```

#### Rank 4 — PARTIAL (sim 0.512)

- **Chunk ID**: `cmr_sec_361_130__000`
- **Section**: `361.130` — Household Right to Same Day Filing
- **Program**: SNAP
- **Judge reason**: The chunk discusses application filing procedures and same-day filing rights but does not specify the actual processing timeline or deadline for DTA to complete SNAP application processing.

```
Households shall be advised of their right to same day filing of the application. Each office shall post signs that explain the application processing standards and the household's right to same day filing. In addition, the household shall be informed that it does not have to be interviewed before filing its application and that it may file an incomplete application as long as the form contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. Department staff shall encourage households to file an application the same day the household or its representative contacts the Department in person or by telephone and expresses an interest in obtaining SNAP benefits.
```

#### Rank 5 — PARTIAL (sim 0.509)

- **Chunk ID**: `cmr_sec_361_120__000`
- **Section**: `361.120` — Date of Application
- **Program**: SNAP
- **Judge reason**: This chunk explains how DTA establishes the application date but does not address the processing timeline or how long DTA has to process the application.

```
For households consisting only of SSI applicants or recipients that apply for SNAP benefits at an SSA office, the household's date of application is the date the signed SNAP application is received by the SSA office. The SSA office shall date stamp each application on the date it is received to document the household's date of application. For all other households, the household's date of application is the date an identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office, except that when an application is not received by 5:00 P.M. on a business day or is received on a weekend or holiday, the application date will be the next business day. The Department shall date stamp each application on the date it is received to document the household's date of application.
```


### cmr_008 — SNAP application filing (rank-1: RELEVANT)

**Question**: How does someone file a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.100` — judge picked rank-1 RELEVANT chunk in section `361.110` (section-author intuition disagrees with judge)  
**Notes**: 361.100 Filing an Application  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.590)

- **Chunk ID**: `cmr_sec_361_110__000`
- **Section**: `361.110` — Where to File
- **Program**: SNAP
- **Judge reason**: Directly explains the multiple methods available for filing a SNAP application (in person, by representative, mail, fax, or online).

```
The application must be filed with the Department and may be submitted in person by the applicant, or by an authorized representative, or by mail, fax or the online application. Households consisting only of SSI applicants or recipients may file a SNAP application at an SSA office in accordance with 106 CMR 361.190.
```

#### Rank 2 — PARTIAL (sim 0.579)

- **Chunk ID**: `cmr_sec_361_130__000`
- **Section**: `361.130` — Household Right to Same Day Filing
- **Program**: SNAP
- **Judge reason**: Addresses same-day filing rights and requirements but doesn't explain the actual steps or methods for submitting a SNAP application.

```
Households shall be advised of their right to same day filing of the application. Each office shall post signs that explain the application processing standards and the household's right to same day filing. In addition, the household shall be informed that it does not have to be interviewed before filing its application and that it may file an incomplete application as long as the form contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. Department staff shall encourage households to file an application the same day the household or its representative contacts the Department in person or by telephone and expresses an interest in obtaining SNAP benefits.
```

#### Rank 3 — PARTIAL (sim 0.574)

- **Chunk ID**: `cmr_sec_361_140__000`
- **Section**: `361.140` — Mailing Applications to Households
- **Program**: SNAP
- **Judge reason**: Describes methods for receiving a SNAP application form (by mail or online) but doesn't explain the actual filing process or steps required to complete an application.

```
If the household has contacts the Department by telephone but does not wish to come to a local office to file an application that same day and instead prefers receiving an application through the mail rather than applying online, the Department shall mail the application form to the household on the same day as the telephone request. If a household makes a written request for SNAP assistance, the Department shall mail the application form to the household on the same day as the written request for SNAP assistance is received.
```

#### Rank 4 — PARTIAL (sim 0.550)

- **Chunk ID**: `cmr_sec_366_920__001`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) Filing an Application.
- **Judge reason**: The chunk explains where and when to file a SNAP application but doesn't describe the actual process or steps for how someone files one.

```
(A) Filing an Application. Assistance in completing SNAP applications will be available at SSA or the Department.
(B) Date of Application. If the application is filed at an SSA office, then the date of application shall be the date the identifiable SNAP application is faxed by SSA to the appropriate Transitional Assistance Office (TAO). If an application is filed at a TAO or online, the date of application shall be the date the identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office. (See 106 CMR 361.120: Date of Application.)
```

#### Rank 5 — PARTIAL (sim 0.547)

- **Chunk ID**: `cmr_sec_361_120__000`
- **Section**: `361.120` — Date of Application
- **Program**: SNAP
- **Judge reason**: The chunk describes how application dates are recorded after filing, but does not explain the actual process or methods for how someone files a SNAP application.

```
For households consisting only of SSI applicants or recipients that apply for SNAP benefits at an SSA office, the household's date of application is the date the signed SNAP application is received by the SSA office. The SSA office shall date stamp each application on the date it is received to document the household's date of application. For all other households, the household's date of application is the date an identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office, except that when an application is not received by 5:00 P.M. on a business day or is received on a weekend or holiday, the application date will be the next business day. The Department shall date stamp each application on the date it is received to document the household's date of application.
```


### cmr_009 — SNAP noncitizen eligibility (rank-1: RELEVANT)

**Question**: Can a noncitizen receive SNAP benefits  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `362.220` — judge picked rank-1 RELEVANT chunk in section `362.220` (section-author intuition agrees)  
**Notes**: 362.220 Noncitizens (CMR 362.200 series covers citizenship)  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.60  

#### Rank 1 — RELEVANT (sim 0.580)

- **Chunk ID**: `cmr_sec_362_220__002`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 3 / 12
- **Program**: SNAP
- **Hierarchy**: (A) A qualified noncitizen is a person who, at the time the person applies fo...
- **Judge reason**: The chunk directly addresses which noncitizens can receive SNAP benefits by listing specific eligible noncitizen categories and their required USCIS statuses.

```
(8) legal permanent residents; and
(9) battered noncitizens.
(B) To receive SNAP benefits the qualified noncitizen must meet the conditions of one of the following USCIS statuses:
(1) Refugee. A noncitizen present in the U.S. as a refugee under section 207 or 207(c) of the INA is an eligible noncitizen.
(2) Asylee. A noncitizen present in the U.S. as a refugee under section 208 of the INA is an eligible noncitizen.
(3) Withholding of Deportation. A noncitizen whose deportation is being withheld under section 243(h) or whose removal is withheld under section 241(b)(3) of the INA is an eligible noncitizen.
(4) Cuban/Haitian Entrant. A noncitizen who is present in the U.S. as a Cuban/Haitian entrant (as defined in section 501(e) of the Refugee Education Assistance Act of 1980) is an eligible noncitizen.
(5) Amerasian. A noncitizen from Vietnam who is present in the U.S. as an Amerasian immigrant (as defined in section 584 of the Foreign Operations, Export Financing and Related Programs Appropriations Act, 1988) is an eligible noncitizen.
```

#### Rank 2 — RELEVANT (sim 0.565)

- **Chunk ID**: `cmr_sec_362_220__001`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 2 / 12
- **Program**: SNAP
- **Hierarchy**: (A) A qualified noncitizen is a person who, at the time the person applies fo...
- **Judge reason**: Directly answers that noncitizens can receive SNAP benefits if they are qualified noncitizens in specified categories, providing the specific eligibility criteria.

```
the noncitizen being a qualified noncitizen and meeting certain conditions related to the qualified noncitizen status.
(A) A qualified noncitizen is a person who, at the time the person applies for or receives SNAP benefits, is in one of the following categories as determined by the USCIS:
(1) refugees admitted to the U.S. under section 207 of the INA, including a victims of severe forms of trafficking;
(2) asylees admitted to the U.S. pursuant to section 208 of the INA;
(3) noncitizens whose deportation is withheld pursuant to section 243(h) or whose removal is withheld pursuant to section 241(b)(3) of the INA;
(4) Cuban/Haitian entrants (defined by section 501(e) of the Refugee Education Assistance Act of 1980);
(5) Amerasians defined by in section 584 of the Foreign Operations, Export Financing and Related Programs Appropriations Act, 1988;
(6) noncitizens paroled as a refugee or asylee pursuant to section 212(d)(5) of the INA for at least one year;
(7) conditional entrants pursuant to section 203(a)(7) of the INA;
```

#### Rank 3 — RELEVANT (sim 0.562)

- **Chunk ID**: `cmr_sec_362_220__003`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 4 / 12
- **Program**: SNAP
- **Hierarchy**: (B) To receive SNAP benefits the qualified noncitizen must meet the condition...
- **Judge reason**: The chunk directly addresses noncitizen eligibility for SNAP benefits by specifying which categories of noncitizens are eligible, including victims of trafficking, legal permanent residents, and those meeting specific criteria.

```
(6) Victims of Severe Forms of Trafficking. A noncitizen who is present in the U.S. and has been issued a letter from the U.S. Department of Health and Human Services (HHS) verifying that the noncitizen is a victim of severe forms of trafficking as defined in 106 CMR 362.240(E) is an eligible noncitizen.
(7) Legal Permanent Resident. A noncitizen present in the U.S. as a legal permanent resident is an eligible noncitizen when he or she:
(a) prior to adjustment to legal permanent resident status, was:
1. a refugee pursuant to section 207 of the INA, including a victim of severe forms of trafficking;
2. an asylee pursuant to section 208 of the INA;
3. a noncitizen whose deportation was being withheld pursuant to section 243(h) or 241(b)(3) of the INA;
4. a Cuban/Haitian entrant (defined by section 501(e) of the Refugee Education Assistance Act of 1980); or
5. an Amerasian immigrant (defined by section 584 of the Foreign Operations, Export Financing and Related Programs Appropriations Act, 1988).
(b) has resided as a qualified noncitizen in the U.S. for five years;
(c) is elderly, born on or before August 22, 1931, and who was lawfully residing in the U.S. on August 22, 1996;
(d) is a child younger than 18 years old;
(e) is disabled as defined in 106 CMR 361.210: Elderly or Disabled Individuals;
(f) has worked a minimum of 40 qualifying quarters pursuant to Title II of the Social Security Act including qualifying quarters of work not covered by Title II;
```

#### Rank 4 — RELEVANT (sim 0.556)

- **Chunk ID**: `cmr_sec_362_220__000`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 1 / 12
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses whether noncitizens can receive SNAP benefits by explaining the verification requirements and eligible noncitizen statuses needed for noncitizen SNAP eligibility.

```
A noncitizen applying for SNAP benefits and claiming an eligible noncitizen status must verify that he or she is present in the United States (U.S.) under one of the noncitizen statuses provided in 106 CMR 362.220(A). The status of a noncitizen must be verified at certification, at recertification or whenever the status of the noncitizen changes or is questionable. Verification of an eligible noncitizen status must be presented before the determination of SNAP eligibility. When a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide information about, or acceptable verification of, his or her eligible noncitizen status, that household member shall be ineligible. In such cases the Department shall not continue efforts to obtain documentation. Also, if a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide, or apply for, a Social Security Number due to immigration status he or she is ineligible. The Department shall not continue efforts to obtain documentation. SNAP eligibility will be determined in accordance with 106 CMR 365.520(A) for the household members who do verify an eligible noncitizen status. The Commissioner or designee is required to report to the United States Citizenship and Immigration Services (USCIS) information about noncitizens "known to be in the U.S. unlawfully" as defined in 106 CMR 362.240. SNAP - Eligible Noncitizen Status. A noncitizen's eligibility for SNAP benefits depends on
```

#### Rank 5 — PARTIAL (sim 0.554)

- **Chunk ID**: `cmr_sec_362_220__004`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 5 / 12
- **Program**: SNAP
- **Hierarchy**: (B) To receive SNAP benefits the qualified noncitizen must meet the condition...
- **Judge reason**: The chunk discusses which noncitizens are eligible for benefits under Massachusetts DTA policy, but does not explicitly state whether noncitizens can receive SNAP benefits or address SNAP-specific eligibility rules.

```
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


### cmr_010 — SNAP restoration (rank-1: RELEVANT)

**Question**: When are SNAP benefits restored after an agency error  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366` — judge picked rank-1 RELEVANT chunk in section `366.520` (section-author intuition agrees)  
**Notes**: BROAD — chapter 366 covers changes/restoration; specific section may be 366.500  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.572)

- **Chunk ID**: `cmr_sec_366_520__001`
- **Section**: `366.520` — Computing the Amount to be Restored
- **Chunk position**: 2 / 2
- **Program**: SNAP
- **Hierarchy**: (B) Computing the Amount to be Restored.
- **Judge reason**: The chunk directly addresses when SNAP benefits are restored after agency errors by specifying restoration timelines for erroneous denials, delays, and terminations.

```
(B) Computing the Amount to be Restored.
(1) If an incorrect allotment caused the loss to an eligible household, the loss of benefits shall be calculated only for those months the household participated. The Department shall calculate the allotment the household was eligible to receive during the months of entitlement. The amount to be restored is the difference between the actual allotment and the allotment the household was eligible to receive.
(2) If an incorrect denial, delay or termination of benefits caused the loss, the months affected by the loss are calculated as follows:
(a) If an eligible household's application was erroneously denied, benefits will be restored back to the month of application. For an eligible household filing a timely reapplication, benefits shall be restored back to the month following the expiration of its certification period;
(b) If an eligible household's application was delayed, the months for which benefits will be restored shall be calculated in accordance with 106 CMR 361.900 through 361.960; and
(c) If a household's benefits were erroneously terminated, benefits will be restored back to the first month in which benefits were not received as a result of the erroneous action. After computing the date the loss initially occurred, the loss shall be calculated for each month subsequent to that date until either the first month the error is corrected or the first month the household is found ineligible.
```

#### Rank 2 — PARTIAL (sim 0.563)

- **Chunk ID**: `cmr_sec_366_530__000`
- **Section**: `366.530` — Notification of Restoration of Lost Benefits
- **Program**: SNAP
- **Judge reason**: Describes the restoration process and notification requirements but does not specify the timeframe or timeline for when benefits are actually restored after agency error.

```
When it is determined that a loss of benefits occurred, the Department shall automatically take action to restore those benefits to the household. No action by the household is necessary. The household shall be notified of its entitlement, the amount of benefits to be restored, any offsetting that was done, the method of restoration and the right to appeal through the fair hearing process if the household disagrees with any aspect of the proposed lost benefit restoration.
```

#### Rank 3 — RELEVANT (sim 0.555)

- **Chunk ID**: `cmr_sec_366_510__000`
- **Section**: `366.510` — Entitlement for Benefits Including Underpayments
- **Program**: SNAP
- **Judge reason**: Directly addresses when SNAP benefits are restored after agency error, including specific examples and conditions for restoration.

```
A household is entitled to lost benefits only for those months the household was eligible to participate. In cases where there is no information in the household's case record to document that the household was actually eligible, the Department shall advise the household of what information must be provided to determine eligibility for these months. For each month that the household cannot provide the necessary information to demonstrate its eligibility, the household shall be considered ineligible for restoration of lost benefits. The Department shall restore to the household benefits that were lost because of:
(A) an agency error, such as an incorrect allotment, an incorrect denial or termination of benefits, agency delay in acting on a reported change, or failure to provide benefits for the month following the expiration of the certification period for households properly fulfilling the recertification process;
(B) a fraud disqualification penalty of a household member that is later reversed; and
(C) an error by the Department or by SSA through joint application processing. Such an error shall include, but is not limited to, the loss of an applicant's SNAP application after it has been filed with SSA. Households are also entitled to lost benefits if a Department policy specifically provides for restoration of lost benefits. NON-TEXT PAGE
```

#### Rank 4 — PARTIAL (sim 0.550)

- **Chunk ID**: `cmr_sec_366_520__000`
- **Section**: `366.520` — Computing the Amount to be Restored
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Hierarchy**: (A) Months of Restoration.
- **Judge reason**: Addresses the duration and lookback period for benefit restoration but does not specify the timeline or process for when restoration actually occurs after an agency error is identified.

```
(A) Months of Restoration. Except when benefits are restored as the result of the reversal of a fraud disqualification penalty, benefits shall be restored for not more than 12 months prior to whichever of the following occurred first:
(1) the month the household or another person or agency notified the Department verbally or in writing of the possible loss of benefits;
(2) the month the Department discovered that a loss has occurred; or
(3) the date the household requested a fair hearing to contest the adverse action that resulted in the loss.
```

#### Rank 5 — PARTIAL (sim 0.525)

- **Chunk ID**: `cmr_sec_366_570__000`
- **Section**: `366.570` — Method of Restoration
- **Program**: SNAP
- **Judge reason**: Explains how benefits are restored but does not specify the timeframe or conditions for when restoration occurs after agency error.

```
Regardless of current eligibility, the Department shall restore lost benefits to a household by issuing an allotment equal to the amount of benefits that were lost. For currently eligible households, the lost benefits shall be issued in a lump sum separate from the household's current monthly allotment. The Department shall honor reasonable requests that the benefits be restored in monthly installments.
```


### cmr_011 — SNAP recertification (rank-1: RELEVANT)

**Question**: What are the SNAP recertification requirements  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366` — judge picked rank-1 RELEVANT chunk in section `366.300` (section-author intuition agrees)  
**Notes**: BROAD — chapter 366 generally; could pull from 365.150 for PA households  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.538)

- **Chunk ID**: `cmr_sec_366_300__000`
- **Section**: `366.300` — Recertification
- **Program**: SNAP
- **Judge reason**: Directly addresses SNAP recertification requirements by outlining the mandatory steps (new application, interview, verification) and timeliness standards households must follow.

```
A household's SNAP benefits shall not continue beyond the certification period, unless the household has been recertified. To recertify, the household must submit a new application, be interviewed, and provide required verification in accordance with the timeliness standards set forth in 106 CMR 366.320. Those households that timely recertify and are found eligible shall be entitled to uninterrupted benefits. The following sections list the responsibilities of the household and the Department in the recertification process.
```

#### Rank 2 — PARTIAL (sim 0.536)

- **Chunk ID**: `cmr_sec_366_320__003`
- **Section**: `366.320` — Household Responsibilities
- **Chunk position**: 4 / 5
- **Program**: SNAP
- **Hierarchy**: (C) Providing Verification.
- **Judge reason**: Addresses specific verification requirements during recertification but doesn't comprehensively cover all SNAP recertification requirements like frequency, timing, or overall process.

```
(2) Noncitizen Status. Noncitizen status shall be verified prior to recertification only when the household reports a change in the noncitizen status of a household member.
(3) Medical Expenses. The amount of allowable medical expenses, including the amount of reimbursement (e.g., by a third-party insurer), shall be verified prior to recertification if their use would result in a larger deduction. Other factors related to the medical expenses, such as the type of service provided or the eligibility of the person incurring the cost, shall be verified only if the information provided by the household is questionable.
(4) Liquid Assets. The current value of the household's countable liquid assets, as defined in 106 CMR 363.100: Assets, shall be verified in accordance with 106 CMR 363.130: Countable Assets prior to recertification.
(5) Social Security Numbers. The Social Security number (SSN) of each household member shall be verified in accordance with 106 CMR 362.500: Social Security Numbers.
```

#### Rank 3 — PARTIAL (sim 0.534)

- **Chunk ID**: `cmr_sec_366_320__004`
- **Section**: `366.320` — Household Responsibilities
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (C) Providing Verification.
- **Judge reason**: The chunk addresses specific verification requirements that occur prior to recertification, but does not comprehensively explain the overall SNAP recertification requirements, timeline, or process.

```
(6) Disability. The disability of a household member, as it pertains to household composition, shall be verified prior to recertification in accordance with 106 CMR 361.210: Elderly or Disabled Individuals.
(7) Legally Obligated Child Support Payments. The household shall be required to verify the amount of legally obligated child support a household member pays to a non-household member prior to recertification.
(8) Additional Verification Requirements.
(a) All other eligibility factors, financial or nonfinancial, shall be verified prior to recertification when the information provided by the applicant is questionable and affects the household's eligibility or benefit level. Other eligibility factors include loans, residency, household composition, citizenship, student eligibility, circumstances related to work registration, and certain deductible expenses.
(b) These factors shall be verified prior to recertification when the Department decides to require verification of additional information. Such verifications must be required statewide and shall not be imposed on a case-by-case basis on particular households.
```

#### Rank 4 — RELEVANT (sim 0.529)

- **Chunk ID**: `cmr_sec_366_320__002`
- **Section**: `366.320` — Household Responsibilities
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (C) Providing Verification.
- **Judge reason**: The chunk directly addresses SNAP recertification requirements by specifying verification requirements that must be met at recertification, including income verification procedures and timelines.

```
(C) Providing Verification. The following verification requirements shall be met at recertification. (See 106 CMR 365.180: Categorically Eligible Assistance Units for verification factors that are deemed for categorically eligible households.) Additional verification is not required unless the information provided is questionable. Time frames (at least ten calendar days from the date of the Department's initial request) may be established within which the household must submit any required verification requested to ensure its rights to uninterrupted benefits.
(1) Gross Countable Income. The amount of the household's gross countable monthly income, as defined in 106 CMR 363.200: Income, shall be verified prior to recertification. If all attempts to verify the gross countable income are unsuccessful because a third-party has failed to cooperate, the Department shall determine the household's gross countable monthly income based on the best available information. Noncountable income shall be verified only if the information provided by the household is questionable.
```

#### Rank 5 — RELEVANT (sim 0.525)

- **Chunk ID**: `cmr_sec_366_310__000`
- **Section**: `366.310` — Notification to Recertify
- **Program**: SNAP
- **Judge reason**: Directly addresses SNAP recertification requirements by specifying notice timing and procedures for different household certification lengths.

```
Households certified for one or two months shall receive, at the time of certification, a separate notice of recertification responsibilities entitled Notice of Expiration. Those households certified for three months or more (except public assistance households) shall receive a separate Notice of Expiration in the month prior to the last month of their certification period. This notice will be mailed by the Department no earlier than the first day of the next-to-last month of certification or no later than the last day of the next-to-last month of certification. The contents of the notice are set forth in 106 CMR 364.840: Notice of SNAP Termination. Public assistance households shall receive a notice of recertification responsibilities prior to the end of the SNAP certification period. In some instances, these households are recertified for SNAP at the same time as their public assistance redetermination.
```


### cmr_012 — SNAP categorical eligibility (rank-1: RELEVANT)

**Question**: What is SNAP categorical eligibility  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365` — judge picked rank-1 RELEVANT chunk in section `365.180` (section-author intuition agrees)  
**Notes**: BROAD — chapter 365 special households; 365.180 in v1  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.560)

- **Chunk ID**: `cmr_sec_365_180__000`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 1 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk directly defines SNAP categorical eligibility by listing the specific household categories that qualify for it under Massachusetts DTA policy.

```
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

#### Rank 2 — PARTIAL (sim 0.547)

- **Chunk ID**: `cmr_sec_365_180__001`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk describes specific SNAP categorical eligibility categories and income standards but does not explain what categorical eligibility itself is or its general purpose and mechanism.

```
(5) SNAP-only TANF Service Elder/Disabled Households which include SNAP households consisting solely of non-SSI elders (60 years of age or older) and/or disabled individuals in accordance with SNAP disability standards at 106 CMR 361.210: Elderly or Disabled Individuals. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards; and
(6) SNAP-only TANF Service Adult Households include SNAP households consisting solely of adults between 19 and 59 years of age. These households must meet the Gross Monthly Categorically Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards. For purposes of 106 CMR 365.180(A)(1) through (3), authorized to receive means that an individual has been determined eligible for benefits and has been notified of this determination, even if benefits have been authorized but not received, authorized but not accessed, suspended or recouped, or not paid because they are less than a minimum amount. For purposes of 106 CMR 365.180(A)(4) through (6), a TANF Service includes receipt of the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure.
```

#### Rank 3 — PARTIAL (sim 0.528)

- **Chunk ID**: `cmr_sec_364_976__000`
- **Section**: `364.976` — Gross Monthly Categorical Eligibility Income Standards
- **Program**: SNAP
- **Judge reason**: The chunk mentions categorical eligibility standards and references where to find details, but does not explain what SNAP categorical eligibility actually is or how it works.

```
The Gross Monthly Categorical Eligibility Standards are based on household size and are adjusted annually based on the federal poverty level. These standards are posted at www.mass.gov/dta. For more details on determining categorical eligibility, see 106 CMR 365.180: Categorically Eligible Assistance Units.
```

#### Rank 4 — PARTIAL (sim 0.520)

- **Chunk ID**: `cmr_sec_365_180__002`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Hierarchy**: (B) SSI, TAFDC and TANF
- **Judge reason**: The chunk discusses categorical eligibility rules and exceptions but does not explain what categorical eligibility actually is or its basic definition and purpose.

```
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

#### Rank 5 — PARTIAL (sim 0.499)

- **Chunk ID**: `cmr_sec_365_180__006`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 7 / 9
- **Program**: SNAP
- **Hierarchy**: (F) Verification Requirements.
- **Judge reason**: The chunk discusses categorical eligibility in the context of SNAP applications but does not define what categorical eligibility actually is or explain the concept itself.

```
106 CMR 361.200: Household Concept.
(G) Determination of Eligibility.
(1) Pending SSI or EAEDC Eligibility. To determine if a household will be eligible due to its status as an EAEDC or SSI household, the SNAP eligibility determination may be temporarily postponed, within the 30-day processing timeframe, if the household is not entitled to expedited service and appears to be categorically eligible. However, denial of a potentially categorically eligible household shall only be postponed until the 30 th. Upon approval of the EAEDC or SSI application, the household is considered categorically eligible if it meets all the criteria in 106 CMR 365.180(A) through (F).
(2) Denials. For a household filing a joint application for SNAP and EAEDC benefits or a household with an EAEDC or SSI application pending that is originally denied SNAP benefits, but is later determined eligible to receive EAEDC or SSI benefits and otherwise categorically eligible, the original application and any other pertinent information occurring after that application shall be used to determine benefits. A second interview is not required. However, the Department shall use any available information to update the application and/or make mail or phone contact with the household or authorized representative to determine any changes in circumstances. Denied applications of a potentially categorically eligible household must be easily retrievable.
```


### cmr_013 — SSP eligibility (rank-1: PARTIAL)

**Question**: What is the State Supplement Program and who is eligible  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.120`  
**Notes**: 327.120 Eligibility for State Supplement Program  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — PARTIAL (sim 0.415)

- **Chunk ID**: `cmr_sec_327_010__000`
- **Section**: `327.010` — Authority for State Supplement Program
- **Program**: SSP
- **Judge reason**: Explains what SSP is and that Massachusetts offers it, but does not provide specific eligibility criteria for the program.

```
The Supplemental Security Income (SSI) program is administered by the Social Security Administration (SSA) to provide financial assistance to eligible aged, disabled and blind individuals. States have the option to provide additional assistance through the State Supplement Program (SSP). Massachusetts has opted to provide this additional assistance. SSP is authorized under M.G.L. c. 6, § 131 and M.G.L. c. 118A and applicable federal law pertaining to the SSI program and agreements with the Commissioner of Social Security. 106 CMR 327.000 is promulgated and implemented in accordance with M.G.L. c. 30A, and applicable General Laws of Massachusetts.
```

#### Rank 2 — RELEVANT (sim 0.404)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly defines the State Supplement Program (SSP) and clearly explains who is eligible, including the specific criteria and categories of individuals who can receive benefits.

```
SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 3 — RELEVANT (sim 0.389)

- **Chunk ID**: `cmr_sec_327_120__000`
- **Section**: `327.120` — Eligibility for State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly explains what the State Supplement Program (SSP) is and provides clear eligibility criteria for who qualifies.

```
An application for SSI serves is an application for SSP. There is no separate SSP application. Eligibility for SSP is determined after an eligibility determination for SSI is made by the Social Security Administration (SSA). The Department must accept the SSA determination. Individuals may be eligible for SSP if they are either:
(A) determined eligible for SSI; or
(B) determined not eligible for SSI solely due to income, but their countable income is less than the combined Federal Benefit Rate (FBR) and the appropriate SSP payment.
```

#### Rank 4 — PARTIAL (sim 0.364)

- **Chunk ID**: `cmr_sec_327_110__000`
- **Section**: `327.110` — Definitions
- **Program**: SSP
- **Judge reason**: The chunk provides definitions related to SSP eligibility criteria but does not explain what the State Supplement Program is or provide a comprehensive overview of who is eligible.

```
The following words and terms, when used in 106 CMR 327.000, have the following meanings, unless the context otherwise requires. (Mass. Register #1390 5/3/19) Child. For SSP purposes, is one who meets the SSI definition of child. Countable Income. As defined in 20 CFR 416.1104. Eligible Individual. An aged, disabled or blind individual who meets all SSI eligibility requirements. See 20 CFR 416.120. Eligible Couple. An eligible individual and his or her eligible spouse who are living in the same household. See 20 CFR 416.1801. Federal Benefit Rate (FBR). As defined in 20 CFR 416.1101. Public Income Maintenance Payment. A payment from any of the following programs: SSI, TAFDC, Refugee Act of 1980, Disaster Relief Act of 1974, Veterans Administration benefits based on need, or any State or local governmental assistance program based on need. Representative Payee. As defined in 20 CFR 416.601. Resources. As defined in 20 CFR 416.1201, et seq. Supplemental Security Income (SSI). As defined in 20 CFR 416.101. SSP-only. A designation for a client who is ineligible for SSI solely based on his or her income but is eligible to receive SSP benefits.
```

#### Rank 5 — PARTIAL (sim 0.340)

- **Chunk ID**: `cmr_sec_327_220__001`
- **Section**: `327.220` — State Living Arrangements
- **Chunk position**: 2 / 6
- **Program**: SSP
- **Hierarchy**: (A) State Living Arrangement A: Full Cost of Living.
- **Judge reason**: The chunk discusses living arrangements and eligibility criteria related to SSP (State Supplement Program) but does not define what the State Supplement Program is or provide comprehensive eligibility information.

```
(2) State Living Arrangement A includes an individual who is in Federal Living Arrangement C, if none of the people with whom he or she is living receives public income maintenance payments.
(3) State Living Arrangement A includes an individual who does not meet the definitions in 106 CMR 327.220(A)(1) or (2), if he or she (or he or she and his or her spouse) are paying at least b of the household's expenses. Public income maintenance payments that are received by the SSP client's spouse who is not eligible for SSI or SSP cannot be used to determine the contribution to the household's expenses.
(4) State Living Arrangement A includes an individual living in a public congregate housing development funded through M.G.L. c. 121B, §§ 38 through 41A, or §§ 42 through 44A (originally known as St. 1954, c. 667 and St. 1966, c. 707) and as provided by Massachusetts in a list to be updated as necessary, of such public congregate housing developments.
```


### cmr_014 — SSP payment standards (rank-1: PARTIAL)

**Question**: What are the SSP payment standards  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.330`  
**Notes**: 327.330 Payment Standards  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.20  

#### Rank 1 — PARTIAL (sim 0.368)

- **Chunk ID**: `cmr_sec_327_350__000`
- **Section**: `327.350` — Timing and Method of SSP Benefit Payments
- **Program**: SSP
- **Judge reason**: Addresses SSP payment mechanics and minimum amounts but does not provide the actual payment standards/benefit amounts that the user is asking about.

```
SSP benefits are paid once a month. The Department shall determine the method of payment. Minimum Monthly Payment The minimum monthly payment for the SSP is $1.00. If the payment amount is greater than zero but less than $1.00, a payment of $1.00 will be issued.
```

#### Rank 2 — PARTIAL (sim 0.361)

- **Chunk ID**: `cmr_sec_327_330__000`
- **Section**: `327.330` — Payment Standards
- **Program**: SSP
- **Judge reason**: The chunk explains how SSP payment standards are calculated and where to find them, but does not provide the actual payment standard amounts themselves.

```
Payment amounts are based on Eligibility Category, State Living Arrangement, whether the client is eligible as an individual or as a member of an eligible couple and the amount of countable income. If countable income exceeds the Federal Benefit Rate (FBR), the amount exceeding the FBR is deducted from the SSP payment standard. Payment standards are available online at www.mass.gov/dta under the heading Key Resources/Program Eligibility Charts and Tables/SSI Program Payment Charts. Paper copies are available upon request.
```

#### Rank 3 — PARTIAL (sim 0.335)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk explains that SSP payment levels are based on Eligibility Category, State Living Arrangement, and individual/couple status, but does not provide the actual payment standard amounts or rates.

```
SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 4 — IRRELEVANT (sim 0.330)

- **Chunk ID**: `cmr_sec_327_370__000`
- **Section**: `327.370` — Designated Payees and SSA Representative Payees
- **Program**: SSP
- **Judge reason**: The chunk discusses designated payees for SSP benefit distribution, not the payment standards (amounts) themselves.

```
(A) A Designated Payee is a third-party appointed by the Department to receive the SSP benefit payments when the client is unable to manage or direct the management of benefit payments in his or her own interest.
(B) SSP benefits of a client whose SSI benefits are paid to an SSA Representative Payee will also be paid to the SSA Representative Payee. For SSP purposes, this SSA Representative Payee will be known as a Designated Payee.
(C) SSP benefits for a child younger than 18 years old must be paid to a Designated Payee.
```

#### Rank 5 — PARTIAL (sim 0.320)

- **Chunk ID**: `cmr_sec_327_340__000`
- **Section**: `327.340` — Date Benefits Begin
- **Program**: SSP
- **Judge reason**: The chunk discusses when SSP payments begin rather than what the actual payment standards (amounts) are.

```
SSP benefit payments will begin as of the date SSI payments begin. For SSP-only eligible clients, SSP benefit payments will begin as of the first day of the month following the date of the SSI application.
```


### cmr_015 — fair hearings general (rank-1: PARTIAL)

**Question**: What is the fair hearing process at DTA  
**Program filter**: (none)  
**Expected section (for reference)**: `343.110`  
**Notes**: 343.110 General Description of the Fair Hearing Process; no program filter (343 is Hearings)  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.05  

#### Rank 1 — PARTIAL (sim 0.552)

- **Chunk ID**: `cmr_sec_701_600__010`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 11 / 25
- **Program**: EA
- **Hierarchy**: (S) Fair Hearing.
- **Judge reason**: Provides a definition of fair hearing but doesn't explain the actual process steps; mainly serves as a reference pointer to the full policy.

```
(S) Fair Hearing. A proceeding conducted by an impartial officer of the Division of Hearings to review an action proposed, taken or not taken by the Department, which has been appealed. Manual Reference: 106 CMR 343.110: General Description of the Fair Hearing Process.
```

#### Rank 2 — RELEVANT (sim 0.473)

- **Chunk ID**: `cmr_sec_343_110__000`
- **Section**: `343.110` — General Description of the Fair Hearing Process
- **Program**: Hearings
- **Judge reason**: The chunk directly explains what the fair hearing process is at DTA, including its purpose, who can request it, and how it is conducted.

```
The fair hearing process is an adjudicatory proceeding which allows dissatisfied applicants and clients and certain spouses, as well as certain sponsors of aliens, upon written request, to obtain a determination of the appropriateness of certain actions or inactions on the part of the Department, or of alleged coercive or otherwise improper conduct by a Department employee. The process is designed to secure and protect the interests of both the appellant and appropriate Department personnel and to ensure fair and equitable treatment for all involved. A hearing is conducted by an impartial hearing officer of DOH. The decision of the hearing officer is based only on evidence and testimony presented at the hearing. The hearing officer examines the facts, the law, and the other circumstances of the case presented by the parties to determine the legality and appropriateness of the disputed Department actions or decision of the Department. The hearing decision is binding upon the Department and is not subject to any review within the Department except in the case of a remand of the decision for a new hearing pursuant to 106 CMR 343.710.
```

#### Rank 3 — RELEVANT (sim 0.462)

- **Chunk ID**: `cmr_sec_343_410__000`
- **Section**: `343.410` — Rights of the Appellant
- **Program**: Hearings
- **Judge reason**: This chunk directly describes appellant rights during the fair hearing process at DTA, which is a core component of how fair hearings operate.

```
The appellant shall have the right to:
(A) be assisted by an authorized representative;
(B) present witnesses;
(C) examine and introduce evidence from his or her case record, and examine and introduce any pertinent Department documents;
(D) present and establish all relevant facts and circumstances by oral testimony and documentary evidence;
(E) make any pertinent arguments without undue interference; and
(F) question or refute any testimony, and confront and cross-examine adverse witnesses.
```

#### Rank 4 — PARTIAL (sim 0.459)

- **Chunk ID**: `cmr_sec_343_030__004`
- **Section**: `343.030` — Definitions
- **Chunk position**: 5 / 8
- **Program**: Hearings
- **Hierarchy**: (H) DOH.
- **Judge reason**: Provides definitions of key terms but does not describe the actual fair hearing process, procedures, or steps involved.

```
(H) DOH. The Division of Hearings within the Department of Transitional Assistance.
(I) Fair Hearing. A proceeding where the legal rights, duties, benefits, or privileges of persons and agencies are determined.
```

#### Rank 5 — RELEVANT (sim 0.457)

- **Chunk ID**: `cmr_sec_343_310__000`
- **Section**: `343.310` — Scheduling
- **Program**: Hearings
- **Judge reason**: Directly describes key procedural steps in the DTA fair hearing process including registration, notification, hearing scheduling, and accessibility accommodations.

```
Upon receipt of a request for a fair hearing, DOH will register the appeal, set a date for a hearing and so notify the appellant, the appropriate office of the Department, and if applicable, the Department employee against whom allegations of coercive or otherwise improper conduct have been made. DOH shall designate a hearing site accessible to the appellant. If the appellant has a disability which reasonably prevents his or her appearance at the designated site, he or she may request the hearing be held telephonically, at his or her home, or other accessible location.
```


### cmr_016 — hearing time limits (rank-1: RELEVANT)

**Question**: How long does someone have to request a fair hearing  
**Program filter**: (none)  
**Expected section (for reference)**: `343.140` — judge picked rank-1 RELEVANT chunk in section `343.140` (section-author intuition agrees)  
**Notes**: 343.140 Time Limits; could also pull 367.100 (SNAP hearing timing)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.512)

- **Chunk ID**: `cmr_sec_343_140__001`
- **Section**: `343.140` — Time Limits
- **Chunk position**: 2 / 4
- **Program**: Hearings
- **Hierarchy**: (B) Time Limitation on the Right of Appeal.
- **Judge reason**: Directly specifies the time limits (90 days or 120 days) within which someone must request a fair hearing from the Division of Hearings.

```
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

#### Rank 2 — PARTIAL (sim 0.499)

- **Chunk ID**: `cmr_sec_701_600__010`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 11 / 25
- **Program**: EA
- **Hierarchy**: (S) Fair Hearing.
- **Judge reason**: Defines what a fair hearing is but does not address the timeframe for requesting one.

```
(S) Fair Hearing. A proceeding conducted by an impartial officer of the Division of Hearings to review an action proposed, taken or not taken by the Department, which has been appealed. Manual Reference: 106 CMR 343.110: General Description of the Fair Hearing Process.
```

#### Rank 3 — PARTIAL (sim 0.469)

- **Chunk ID**: `cmr_sec_343_240__000`
- **Section**: `343.240` — Request for Fair Hearing
- **Program**: Hearings
- **Judge reason**: The chunk defines what a fair hearing request is and references time limits in 106 CMR 343.140, but does not actually state the specific timeframe for requesting a fair hearing.

```
(A) A request for a fair hearing is defined as a written statement by the appellant or his or her authorized representative which asks for the opportunity to present the case to a higher authority. The request for a fair hearing must be received by DOH within the time limits provided in 106 CMR 343.140.
(B) Any request for a fair hearing which alleges coercive or otherwise improper conduct on the part of a Department employee must state the name of the employee and the place, date and nature of the incident. If the request lacks the information required by 106 CMR 343.240, DOH shall notify the appellant of the requirement. If the appellant then fails to provide the information within ten days, the appeal shall be dismissed.
```

#### Rank 4 — PARTIAL (sim 0.467)

- **Chunk ID**: `cmr_sec_701_600__001`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 2 / 25
- **Program**: EA
- **Hierarchy**: (A) Appeal.
- **Judge reason**: The chunk defines what an appeal/fair hearing request is but does not specify the timeframe or deadline for requesting one.

```
(A) Appeal. An appeal is a written request for a fair hearing on an action proposed or taken by the Department or on the Department's failure to act. Manual Reference: 106 CMR 343.000: Fair Hearing Rules, 702.600: Appeals.
```

#### Rank 5 — PARTIAL (sim 0.467)

- **Chunk ID**: `cmr_sec_343_140__003`
- **Section**: `343.140` — Time Limits
- **Chunk position**: 4 / 4
- **Program**: Hearings
- **Hierarchy**: (D) Time Limits for Rendering Decision.
- **Judge reason**: The chunk addresses time limits for issuing hearing decisions after a request is made, but does not address the time limit for requesting a fair hearing in the first place.

```
(D) Time Limits for Rendering Decision.
(1) The hearing officer must issue the hearing decision within 45 days of the date of the request for a hearing when the issue under appeal is:
(a) the denial of the right to apply or reapply for assistance;
(b) the denial of an application for assistance;
(c) the failure to act on an application in a timely manner; or
(d) the failure to issue Disaster Benefits for SSI clients.
(2) The hearing officer must issue the hearing decision within 90 days of the date of request for a hearing for all other appeals.
(3) The above time limits may be extended for good cause as follows:
(a) Where delays are caused by the appellant or his or her representative, the time limits may be extended by the total number of days of the delay, which includes the advance notice period prior to scheduled hearing dates. Such delays include the appellant's delay in the submission of evidence, briefs or other statements, rescheduling or continuances granted at the request or for the benefit of the appellant, and any other delays caused by the actions of the appellant or his or her representative.
(b) Where delays occur due to acts of God or serious illness of the hearing officer which makes him or her unable to render a decision.
```


### cmr_017 — IPV definition (rank-1: RELEVANT)

**Question**: What is an Intentional Program Violation  
**Program filter**: (none)  
**Expected section (for reference)**: `367.525` — judge picked rank-1 RELEVANT chunk in section `367.525` (section-author intuition agrees)  
**Notes**: 367.525 Definition of an Intentional Program Violation  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.421)

- **Chunk ID**: `cmr_sec_367_525__000`
- **Section**: `367.525` — Definition of an Intentional Program Violation (IPV)
- **Program**: Program Integrity
- **Judge reason**: The chunk directly defines what an Intentional Program Violation (IPV) is and provides specific examples of actions that constitute an IPV.

```
For purposes of determining at an ADH whether or not an IPV was committed, an IPV is any action taken by an individual for the purpose of establishing or maintaining SNAP eligibility or for increasing or preventing a reduction in the allotment amount which is committed knowingly, willfully, and/or with deceitful intent. Examples of IPVs include, but are not limited to:
(A) Making a false statement(s) to the Department, either orally or in writing, to obtain or maintain SNAP benefits to which the household is not entitled;
(B) Concealing information to obtain or maintain SNAP benefits to which the household is not entitled;
(C) Making a false or misleading statement(s) or misrepresentation(s) to conceal or withhold facts to obtain or maintain SNAP benefits to which the household is not entitled;
(D) Altering or transacting SNAP benefits to obtain benefits to which the household is not entitled;
(E) Using SNAP benefits to buy nonfood items such as alcohol or tobacco;
(F) Using or possessing improperly obtained SNAP benefits;
(G) Trading or trafficking (buying or selling) SNAP benefits; or
(H) Intentionally committing any act which violates the state regulations.
```

#### Rank 2 — RELEVANT (sim 0.420)

- **Chunk ID**: `cmr_sec_706_300__000`
- **Section**: `706.300` — Definition of an Intentional Program Violation (IPV)
- **Program**: EA
- **Judge reason**: The chunk directly defines what an Intentional Program Violation is, which is exactly what the user is asking about.

```
An Intentional Program Violation (IPV) is any action by an individual for the purpose of establishing or maintaining eligibility or for increasing, or preventing a reduction in, the amount of the grant by intentionally:
(A) making a false or misleading statement or misrepresentation, either orally or in writing, concealing or withholding of facts from the Department; or
(B) taking any other act intended to mislead, misrepresent, conceal or withhold facts or to propound a falsity.
```

#### Rank 3 — PARTIAL (sim 0.404)

- **Chunk ID**: `cmr_sec_367_520__000`
- **Section**: `367.520` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: Program Integrity
- **Judge reason**: The chunk mentions what an ADH is conducted for and when it's initiated, but does not actually define what an Intentional Program Violation is.

```
An ADH shall conducted in order to determine if an intentional program violation (IPV) has been committed. An ADH shall be initiated by the Department if evidence exists to indicate an IPV was committed.
```

#### Rank 4 — PARTIAL (sim 0.402)

- **Chunk ID**: `cmr_sec_367_750__000`
- **Section**: `367.750` — Standard of Proof for Determining an IPV
- **Program**: Program Integrity
- **Judge reason**: Describes the evidentiary standard for determining an IPV but does not define what an IPV actually is.

```
The hearing official shall base the determination of an IPV on clear and convincing evidence which demonstrates that the household member willfully, knowingly, and with deceitful intent committed an IPV.
```

#### Rank 5 — PARTIAL (sim 0.394)

- **Chunk ID**: `cmr_sec_367_800__000`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Disqualification for Intentional Program Violations.
- **Judge reason**: The chunk describes consequences of IPVs rather than defining what an Intentional Program Violation actually is.

```
(A) Disqualification for Intentional Program Violations.
(1) Individuals found to have committed a SNAP IPV at an ADH shall be ineligible for SNAP benefits for a period of one year for the first finding, two years for the second finding and permanently for the third finding.
(2) Individuals found to have committed a cash program IPV at an ADH, in the absence of a SNAP IPV under 106 CMR 367.800(A)(1), shall be ineligible for SNAP benefits for the period required under the cash program rules.
```


### cmr_018 — SNAP IPV penalties (rank-1: PARTIAL)

**Question**: What are the disqualification penalties for SNAP fraud  
**Program filter**: (none)  
**Expected section (for reference)**: `367.800`  
**Notes**: 367.800 Disqualification Penalties; 367 is Program Integrity for SNAP  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — PARTIAL (sim 0.529)

- **Chunk ID**: `cmr_sec_367_800__002`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 3 / 6
- **Program**: Program Integrity
- **Hierarchy**: (C) Disqualification for Trading SNAP Benefits.
- **Judge reason**: Addresses SNAP disqualification penalties but only for trading/trafficking benefits, not general fraud violations

```
(C) Disqualification for Trading SNAP Benefits.
(1) Individuals found guilty by a federal, state or local court of trading (buying or selling) SNAP benefits for a controlled substance shall be ineligible for SNAP benefits for a period of two years for the first finding, and permanently for the second finding.
(2) Individuals found guilty by a federal, state or local court of trading (buying or selling) SNAP benefits for firearms, ammunition or explosives shall be ineligible for SNAP benefits permanently.
(3) Individuals found guilty by a federal, state or local court of trading (buying or selling) SNAP benefits having a value of $500 or more shall be ineligible for SNAP benefits permanently.
```

#### Rank 2 — RELEVANT (sim 0.527)

- **Chunk ID**: `cmr_sec_367_800__000`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Disqualification for Intentional Program Violations.
- **Judge reason**: Directly specifies SNAP fraud (IPV) disqualification penalties: 1 year for first offense, 2 years for second, and permanent disqualification for third offense.

```
(A) Disqualification for Intentional Program Violations.
(1) Individuals found to have committed a SNAP IPV at an ADH shall be ineligible for SNAP benefits for a period of one year for the first finding, two years for the second finding and permanently for the third finding.
(2) Individuals found to have committed a cash program IPV at an ADH, in the absence of a SNAP IPV under 106 CMR 367.800(A)(1), shall be ineligible for SNAP benefits for the period required under the cash program rules.
```

#### Rank 3 — RELEVANT (sim 0.526)

- **Chunk ID**: `cmr_sec_367_800__001`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 2 / 6
- **Program**: Program Integrity
- **Hierarchy**: (B) Disqualification for Receipt of Multiple SNAP Benefits.
- **Judge reason**: Directly addresses SNAP fraud disqualification penalties by specifying a 10-year ineligibility period for fraudulent statements regarding identity or residence to receive multiple benefits.

```
(B) Disqualification for Receipt of Multiple SNAP Benefits. Individuals found by the Department or convicted by a federal, state or local court of having made a fraudulent statement or representation with respect to identity or place of residence to receive multiple benefits simultaneously under SNAP shall be ineligible for SNAP benefits for ten years.
```

#### Rank 4 — PARTIAL (sim 0.517)

- **Chunk ID**: `cmr_sec_363_150__004`
- **Section**: `363.150` — Transfer of Assets
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (D) Period of Disqualification.
- **Judge reason**: The chunk discusses disqualification periods for asset transfers in SNAP, not fraud-specific penalties which are typically different and more severe.

```
(D) Period of Disqualification. The length of the disqualification period is based on the amount by which the countable transferred asset, when added to other countable assets, exceeds the allowable asset limit. The following chart will be used to determine the period of disqualification: Amount in Excess of the Asset Limit Period of Disqualification $ 0 - 249.99 One Month 250 - 999.99 Two Months 1,000 - 2,999.99 Six Months 3,000 - 4,999.99 Nine Months 5,000 - and up 12 Months | Amount in Excess of the Asset Limit | Period of Disqualification | | --- | --- | | $ 0 - 249.99 | One Month | | 250 - 999.99 | Two Months | | 1,000 - 2,999.99 | Six Months | | 3,000 - 4,999.99 | Nine Months | | 5,000 - and up | 12 Months |
```

#### Rank 5 — PARTIAL (sim 0.498)

- **Chunk ID**: `cmr_sec_363_150__001`
- **Section**: `363.150` — Transfer of Assets
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) Transfers Resulting in Disqualification.
- **Judge reason**: Addresses one specific type of SNAP disqualification (asset transfers) but does not comprehensively cover fraud penalties or other fraud-related disqualifications.

```
(A) Transfers Resulting in Disqualification. At the time of application, households shall be asked to provide information regarding any assets that a household member has transferred within the three-month period before the date of application. Households that have transferred assets knowingly for the purpose of qualifying for, attempting to qualifyfor, or to remain eligible for SNAP benefits shall be disqualified from participation in the Program for up to one year from the date of the discovery of the transfer. When action is taken to disqualify a certified household, an advance notice of adverse action and the right to continued benefits pending a hearing decision shall be provided to the household. The notice shall also include the reasons for and length of the disqualification.
```


### cmr_019 — TAFDC vs EAEDC (rank-1: PARTIAL)

**Question**: What is the difference between TAFDC and EAEDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `701.200`  
**Notes**: 701.200 The TAFDC and EAEDC Programs  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.472)

- **Chunk ID**: `cmr_sec_701_200__002`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 3 / 3
- **Program**: EA
- **Hierarchy**: (4) encouraging teenage parents to live with their families or in supportive ...
- **Judge reason**: The chunk describes EAEDC but only briefly mentions TAFDC in passing, without explaining the key differences between the two programs.

```
(4) encouraging teenage parents to live with their families or in supportive living situations and obtain basic educational achievements. The Emergency Aid to the Elderly, Disabled and Children (EAEDC) Program provides financial assistance to qualified elderly and disabled persons, participants in MRC programs, and certain families who meet the program requirements. EAEDC is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 117A and other relevant statutes and the rules, regulations and policies. The authoritative text of the regulations is published by the Secretary of State of the Commonwealth of Massachusetts. Copies of the regulations are available to the public at the Department's area offices.
```

#### Rank 2 — PARTIAL (sim 0.456)

- **Chunk ID**: `cmr_sec_701_050__000`
- **Section**: `701.050` — Transitional Cash Assistance Programs Overview
- **Program**: EA
- **Judge reason**: The chunk identifies both programs and indicates where their specific eligibility policies differ, but does not actually explain what the differences between TAFDC and EAEDC are.

```
The policies described in this chapter are the basis for the administration and function of both the Transitional Aid to Families with Dependent Children (TAFDC) and Emergency Aid to the Elderly, Disabled and Children (EAEDC) programs; specific eligibility policies for TAFDC and EAEDC are found in 106 CMR 703.000: Nonfinancial Eligibility and 704.000: Financial Eligibility.
```

#### Rank 3 — PARTIAL (sim 0.448)

- **Chunk ID**: `cmr_sec_701_110__000`
- **Section**: `701.110` — Limitation on Program Eligibility
- **Program**: EA
- **Judge reason**: The chunk mentions both TAFDC and EAEDC but focuses on eligibility rules and concurrent benefits rather than explaining the fundamental differences between the two programs.

```
(A) TAFDC and EAEDC-family clients may receive MassHealth and SNAP benefits while on TAFDC or EAEDC. Any individual who is a TAFDC client is not concurrently eligible for EAEDC, Supplemental Security Income (SSI), State Supplement Program (SSP) to the Supplemental Security Income or State Veterans Services Benefits (VSB). Any individual who is an EAEDC client is not concurrently eligible for TAFDC, SSI, SSP or SVSB.
(B) An individual is ineligible for TAFDC if he or she:
(1) is fleeing to avoid prosecution, custody or confinement after conviction, under the laws of the place from which the individual flees, for a crime or an attempt to commit a crime, on or after September 26, 1996, which is a felony under the laws of the place from which the individual flees, or which, in the state of New Jersey, is a high misdemeanor under the laws of such state; or
(2) is violating a condition of probation or parole imposed on or after September 26, 1996 under federal or state law.
(C) An individual is ineligible for TAFDC and EAEDC if he or she has an outstanding default or arrest warrant against him or her issued by any court of the Commonwealth of Massachusetts.
```

#### Rank 4 — PARTIAL (sim 0.439)

- **Chunk ID**: `cmr_sec_701_200__000`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk describes TAFDC but does not provide information about EAEDC or any comparison between the two programs.

```
The Transitional Aid to Families with Dependent Children (TAFDC) program provides financial assistance and employment-related services to families with dependent children. The TAFDC program is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 118 and other relevant statutes and the rules, regulations and policies. TAFDC regulations implement St. 1995, c. 5. TAFDC seeks to integrate clients into the work force and break the cycle of poverty. The major program objectives include:
```

#### Rank 5 — PARTIAL (sim 0.439)

- **Chunk ID**: `cmr_sec_701_230__000`
- **Section**: `701.230` — Social Security Numbers (SSN)
- **Chunk position**: 1 / 5
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk mentions both TAFDC and EAEDC but only addresses SSN requirements that apply to both programs, not the substantive differences between them.

```
(A) Requirements.
(1) A Social Security Number (SSN) must be given for each applicant for TAFDC or EAEDC, unless good cause exists in accordance with 106 CMR 701.230(C).
(2) If an SSN cannot be given for each applicant applying for TAFDC or EAEDC, the applicant must provide to the Department written verification from SSA stating that the SSN cannot be provided, but that person:
(a) has applied for an SSN; or
(b) has asked that an already-existing SSN be validated.
(3) TAFDC or EAEDC may not be denied, delayed or decreased while waiting for the issuance or verification of an SSN if the applicant or client has met the requirements specified in 106 CMR 701.230(A) and (B).
(4) Each applicant for TAFDC or EAEDC who does not meet the SSN requirement must be excluded from the assistance unit. An otherwise eligible applicant or client excluded from the assistance unit for not meeting the SSN requirements becomes eligible upon meeting these requirements.
(5) A temporary identification number shall be provided for an applicant or client who is an expectant mother in the 33rd week of pregnancy as a single grantee or a child younger than four months old. This number shall be valid for not more than three months. Failure to provide a valid SSN within three months shall result in the termination of the client's benefits until a valid SSN is provided and verified by the Department. 106 CMR 701.230(A)(5) shall
```


### cmr_020 — TAFDC 24-month limit (rank-1: RELEVANT)

**Question**: How are TAFDC time-limited benefits applied  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.120` — judge picked rank-1 RELEVANT chunk in section `703.120` (section-author intuition agrees)  
**Notes**: 703.120 TAFDC Time-limited Benefits  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.518)

- **Chunk ID**: `cmr_sec_703_120__000`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) A nonexempt grantee, including each grantee in a two-parent family, who i...
- **Judge reason**: This chunk directly explains how TAFDC time-limited benefits are applied, including the 24-month cumulative limit within a 60-month period and the conditions that affect this calculation.

```
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

#### Rank 2 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_703_120__002`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (B) Exception.
- **Judge reason**: The chunk discusses exemptions from time-limited benefits and references where they are defined (106 CMR 703.120(A)), but does not explain how the time-limited benefits themselves are actually applied.

```
(B) Exception.
(1) A teen parent (see 106 CMR 703.180) who received assistance as a member of another TAFDC assistance unit may reapply for TAFDC, if he or she meets the teen parent requirements found at 106 CMR 703.180, and:
(a) he or she is not eligible to be included in another assistance unit; or
(b) the other TAFDC case is closed.
(2) At the time of the reapplication, the worker shall determine if the teen parent meets an exemption specified in 106 CMR 703.100, and:
(a) if the teen parent meets an exemption, the assistance unit will be exempt from the time-limited benefits defined in 106 CMR 703.120(A); or
(b) if the teen parent does not meet an exemption, the teen parent is nonexempt and the time-limited benefits defined in 106 CMR 703.120(A) will apply.
```

#### Rank 3 — RELEVANT (sim 0.497)

- **Chunk ID**: `cmr_sec_703_120__001`
- **Section**: `703.120` — TAFDC Time-limited Benefits
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (A) A nonexempt grantee, including each grantee in a two-parent family, who i...
- **Judge reason**: The chunk directly explains how TAFDC time-limited benefits are applied through the 24-month cumulative period and 60-month continuous period framework, including rules for when these periods stop, restart, and how exemptions affect them.

```
(4) A nonexempt grantee’s cumulative 24-month period is not stopped when there is a sanction period imposed on a member of the assistance unit, except as specified in 106 CMR 703.120(A)(3)(a).
(5) The calculation of the 60-month period cannot be stopped.
(6) If aid to the assistance unit has been terminated because of the end of the cumulative 24- month period, the assistance unit may establish eligibility for TAFDC before the end of the continuous 60-month period if the grantee meets an exemption found at 106 CMR 703.100.
(7) At the end of a continuous 60-month period, a nonexempt grantee may reapply for TAFDC and begin a new cumulative 24-month eligibility period and a new continuous 60- month period.
(8) In a two-parent household, both parents shall have the same 60-month period. If, because of a prior period of assistance, both parents do not share the same start date of their 60-month period, the earliest date shall apply to the household.
```

#### Rank 4 — PARTIAL (sim 0.462)

- **Chunk ID**: `cmr_sec_703_100__000`
- **Section**: `703.100` — TAFDC Exemptions from Time-limited Benefits
- **Chunk position**: 1 / 10
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk describes exemptions FROM time-limited benefits restrictions rather than explaining how the time-limited benefits themselves are applied or calculated.

```
(A) Requirements.
(1) An assistance unit is exempt from the TAFDC time-limited benefits restrictions found at 106 CMR 703.120, if the grantee:
(a) is disabled as defined in 106 CMR 703.190. A client who requests an exemption under this clause shall, as a condition of continued eligibility, apply for Social Security Disability benefits (RSDI/SSI) and, if requested by the Department, appeal a denial of Social Security Disability benefits at the Social Security Administration as specified in 106 CMR 703.190. Clients who do not comply with the Department’s request to apply for Social Security Disability benefits or appeal a decision shall not be granted a work exemption under this clause;
(b) is essential to the care of one of the following disabled persons living in the home:
1. a child;
2. the grantee's spouse; or
3. the child's other parent. A client who requests this exemption shall either apply for Social Security Disability benefits on behalf of the disabled child or spouse or the disabled spouse or child’s other parent must apply for benefits on his or her own behalf. Verification of such required Social Security Disability benefits applications must be provided.
(c) is in their 33rd week or later of pregnancy or in their third trimester of pregnancy who have submitted documentation signed by a primary care provider or an obstetrician, gynecologist, nurse-midwife or family practitioner that the client has a pregnancy-related
```

#### Rank 5 — PARTIAL (sim 0.459)

- **Chunk ID**: `cmr_sec_703_100__003`
- **Section**: `703.100` — TAFDC Exemptions from Time-limited Benefits
- **Chunk position**: 4 / 10
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk discusses time-limited benefits and the 24-month maximum eligibility period for TAFDC, but focuses on exemption status and appeals rather than explaining how time-limited benefits are actually applied or calculated.

```
(4) An exempt grantee remains exempt until the grantee no longer meets the criteria for an exemption. A grantee must inform the Department as soon as his or her circumstances change in a way that may affect his or her exemption status.
(5) A nonexempt grantee may appeal a nonexempt status determination. However, if the grantee’s nonexempt status is upheld at the fair hearing, the period during which the appeal decision was reached is included in the calculation of the 24-month maximum period of eligibility specified in 106 CMR 703.120.
(6) In the event that a grantee claims an exemption but is determined to be nonexempt as a result of the verification process, the period during which the verification process was being completed shall be included in the calculation of the 24-month maximum period of eligibility as specified in 106 CMR 703.200.
(7) If a grantee claims an exemption but is determined to be nonexempt as a result of the verification process, the period during which the verification process was being completed is included in the calculation of the 24-month maximum period of eligibility specified in 106 CMR 703.120.
```


### cmr_021 — TAFDC work program (rank-1: RELEVANT)

**Question**: What are the TAFDC work program requirements  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.150` — judge picked rank-1 RELEVANT chunk in section `703.150` (section-author intuition agrees)  
**Notes**: 703.150 TAFDC Work Program; was a persistent miss in v1  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.530)

- **Chunk ID**: `cmr_sec_703_150__001`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 2 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly outlines the specific work program requirements for TAFDC nonexempt grantees, including employment hours, approved activities, and combinations of work activities.

```
(2) A nonexempt grantee meets the Work Program requirements by:
(a) working in a job for pay for at least the required hours per week as specified in 106 CMR 703.150(A)(5);
(b) working full-time in the Full Employment Program (FEP) (see 106 CMR 707.180: Full Employment Program) or participating in an approved Supported Work Program (see 106 CMR 707.160: Supported Work Component);
(c) participating in community service, job search or another Department approved activity that is expected to result in employment for the required hours per week as specified in 106 CMR 703.150(A)(5). The maximum number of hours a grantee can participate in a community service program is limited by the federal Fair Labor Standards Act (FLSA). A grantee who cannot meet the required hours of participation through community service alone due to the FLSA must participate in an additional allowable work activity so that the required hours are met. If the grantee cannot identify an allowable work activity, the Department shall provide a referral to an activity;
(d) combining the hours of work, other approved work program activities and community service hours to total the required hours per week as specified in 106 CMR 703.150(A)(5). The number of hours of community service and/or other work program activities required each week will be the difference between the required hours per week and the number of hours worked;
(e) participating in a substance abuse treatment program while in a substance abuse
```

#### Rank 2 — PARTIAL (sim 0.528)

- **Chunk ID**: `cmr_sec_703_000__000`
- **Section**: `703.000` — Overview of TAFDC Nonfinancial Requirements
- **Program**: EA
- **Judge reason**: The chunk references the Work Program requirement (106 CMR 703.150) but only lists it as a requirement without explaining what the actual work program requirements are.

```
In order to receive TAFDC, an applicant or client must meet all of the applicable eligibility requirements. These requirements are both nonfinancial and financial. The nonfinancial requirements for TAFDC eligibility are:
(A) 106 CMR 703.100: Exemptions from Time-limited Benefits;
(B) 106 CMR 703.120: Time-limited Benefits;
(D) 106 CMR 703.150: Work Program;
(E) 106 CMR 703.200: Dependent Child;
(F) 106 CMR 703.300: Relationship and Living Arrangement;
(G) 106 CMR 703.340: Residence;
(H) 106 CMR 703.400: Citizens, Noncitizens, and Canadian-born Indians;
(I) 106 CMR 701.230: Social Security Numbers (SSN); and
(J) 106 CMR 703.500: Cooperation with Child Support Enforcement Efforts.
```

#### Rank 3 — PARTIAL (sim 0.510)

- **Chunk ID**: `cmr_sec_701_200__000`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: Mentions TAFDC work program objectives but does not detail specific work requirements or program rules.

```
The Transitional Aid to Families with Dependent Children (TAFDC) program provides financial assistance and employment-related services to families with dependent children. The TAFDC program is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 118 and other relevant statutes and the rules, regulations and policies. TAFDC regulations implement St. 1995, c. 5. TAFDC seeks to integrate clients into the work force and break the cycle of poverty. The major program objectives include:
```

#### Rank 4 — RELEVANT (sim 0.497)

- **Chunk ID**: `cmr_sec_703_150__000`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 1 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: Directly addresses TAFDC work program requirements including required hours, exemptions, and conditions for participation.

```
(A) Requirements.
(1) A grantee who has received assistance for 60 days must work the required hours per week as specified in 106 CMR 703.150(A)(5), unless:
(a) the grantee is exempt (see 106 CMR 703.100);
(b) the grantee is caring for a foster child in the home who is younger than two years old;
(c) a grantee is caring for a foster child in the home whose needs exceed a standard level of care (DCF tiers 2, 3 and 4) as determined by the DCF Commissioner or designee. A waiver of Work Program requirements may be granted by the DTA Commissioner for other foster parent grantees at the request of the DCF Commissioner based on the needs of the foster child; or
(d) the grantee has good cause as specified in 106 CMR 701.380: Good Cause Criteria. In a two-parent household, each parent shall meet the Work Program requirements for the required hours per week as specified in 106 CMR 703.150(A)(5), unless that parent meets the requirements of 106 CMR 703.150(A)(1). If 106 CMR 703.150(A)(1)(b) and (c) apply, however, the work program requirement must still be met by one parent.
```

#### Rank 5 — RELEVANT (sim 0.493)

- **Chunk ID**: `cmr_sec_703_150__002`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 3 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly lists specific work program activities and requirements that satisfy TAFDC work program obligations, including work study, supported work, education/training, and vocational programs.

```
shelter;
(f) participating in an unpaid work study or internship program for the required hours per week;
(g) providing child care to a teen parent’s dependent child (both of whom are living in the grantee’s home) enabling the teen parent to meet the school attendance requirements;
(h) participating in a Department-approved supported work program with a commitment from the employer to hire participants who successfully complete the program;
(i) participating in an education or training activity including a certificate or degree program from a four-year degree-granting higher education institute, community college or a certificate program (up to a bachelor’s degree) for up to the required hours per week as specified in 106 CMR 703.150(A)(5). If the education or training activity is less than the required hours per week, the grantee must participate in other work program activities to meet the required hours. For purposes of meeting the work program requirement, an education or training activity cannot exceed 24 months. The Department may extend this period if the client is making substantial progress towards completion of the certificate or degree program;
(j) participating in a vocational educational program not to exceed 12 months. The Department may extend this period if the client is making substantial progress towards completion of the certificate or degree program in vocational education; or
```


### cmr_022 — TAFDC asset limit (rank-1: PARTIAL)

**Question**: What is the asset limit for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `704.110`  
**Notes**: 704.110 Asset Limitations  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.20  

#### Rank 1 — PARTIAL (sim 0.528)

- **Chunk ID**: `cmr_sec_704_110__000`
- **Section**: `704.110` — Asset Limitations
- **Chunk position**: 1 / 13
- **Program**: EA
- **Judge reason**: Discusses asset limits but for EAEDC (Emergency Aid to Elderly, Disabled and Children) rather than TAFDC (Temporary Assistance for Families with Dependent Children).

```
In order for an EAEDC individual in living arrangement E, as set forth in 106 CMR 704.435(A)(6), to be eligible, the combined countable assets of the filing unit may not exceed $2000. Countable Assets Assets used to determine financial eligibility are:
```

#### Rank 2 — PARTIAL (sim 0.485)

- **Chunk ID**: `cmr_sec_704_000__000`
- **Section**: `704.000` — Overview of Financial Eligibility
- **Program**: EA
- **Judge reason**: The chunk discusses financial eligibility requirements for TAFDC but does not specify the actual asset limit amount; it only references where such information can be found in the regulations.

```
To receive Transitional Cash Assistance of EAEDC or TAFDC, an applicant or client must meet financial eligibility requirements as well as those requirements provided in 106 CMR 703.000: Transitional Cash Assistance Program: Nonfinancial Requirements. An applicant or client meets the financial eligibility requirements if h e or she has income at or below the Department's limits. The purpose of 1 106 CMR 704.000 is to show how financial eligibility is established. The topics covered are:
(B) Income, 106 CMR 704.200;
(C) Membership in the Assistance Unit and Filing Unit, 106 CMR 704.300;
(D) TAFDC, Need and Payment Standards, 106 CMR 704.410, and 704.420;
(E) EAEDC Living Arrangements and Standards of Assistance, 106 CMR 704.435 and 704.440; and
(F) Calculation of the Grant Amount, 106 CMR 704.500. 5/10/24 106 CMR - 1021 (Mass. Register #1521, 5/10/2024)
```

#### Rank 3 — PARTIAL (sim 0.481)

- **Chunk ID**: `cmr_sec_704_010__000`
- **Section**: `704.010` — General Requirements for Financial Eligibility
- **Program**: EA
- **Judge reason**: The chunk discusses income limits for TAFDC eligibility but does not address asset limits, which is the specific question asked.

```
The Department determines financial eligibility for Transitional Cash Assistance based on an assessment of the income of the filing unit. In order for the assistance unit to be eligible, the income of the filing unit may not be above the Department's income limits.
(A) 106 CMR 704.300, 704.305, and 704.310 provide the requirements for determining who is in the filing unit, who is in the assistance unit, and whose assets, income, and needs are considered in determining eligibility.
(C) 106 CMR 704.200 provides the requirements for determining how income is counted in the eligibility test. The remaining sections provide the requirements for calculating and paying the grant once eligibility has been established.
```

#### Rank 4 — IRRELEVANT (sim 0.471)

- **Chunk ID**: `cmr_sec_702_120__008`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 9 / 9
- **Program**: EA
- **Hierarchy**: (H) Verification of Information.
- **Judge reason**: The chunk contains verification requirements and expense allowance tables, but does not address asset limits for TAFDC.

```
(H) Verification of Information. The worker shall require verification of the applicable eligibility factors for which verification is currently required. See 106 CMR 702.300 and 106 CMR 702.310. | RENT OR MORTGAGE | Unheated Facility | $102.00 | | --- | --- | --- | |  | Heated Facility | 126.30 | | FUEL |  | 27.90 | | UTILITIES |  | 18.60 | | FOOD (Individual) |  | 41.80 |
```

#### Rank 5 — PARTIAL (sim 0.469)

- **Chunk ID**: `cmr_sec_704_110__002`
- **Section**: `704.110` — Asset Limitations
- **Chunk position**: 3 / 13
- **Program**: EA
- **Hierarchy**: (B) Bank Balances.
- **Judge reason**: The chunk discusses what counts toward asset limits and non-countable assets, but does not state the actual numerical asset limit for TAFDC.

```
(B) Bank Balances. ( 1) Definition. Bank balances may be in the form of savings, checking, trust accounts, term certificates, or other types of accounts held at banks, savings or loan institutions. Balances in a bank account are considered available when a member of the filing unit has both ownership of, and access to, the balance of funds in the account. Any portion of the bank balance or amount held in cash from the following sources is non-countable toward the asset limit:
(a) Highway Relocation assistance payments, Urban Renewal Assistance payments, disaster relief payments used for relocation, and payments from private agencies used for relocation;
(b) Any financial assistance paid to a student such as a financial aid package, grant, loan or scholarship for the purposes of obtaining a degree or certificate from an institution of higher education;
(c) Any portion of a Workers' Compensation, property damage, personal injury, Compensation to Victims of Violent Crimes Act, death settlement or award, except for compensation for lost wages, that is received as a reimbursement for specified items and used to pay for such items; ( d) Earned income credits, whether received as an advance payment or as part or all of an income tax refund;
(e) Any payment made under a Public Law that prohibits the payment from being included as income or a resource in determining eligibility for or the amount of benefifits under any Federal or federally assisted program;
```


### cmr_023 — EAEDC disability (rank-1: PARTIAL)

**Question**: What is EAEDC disability and how is it determined  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.190`  
**Notes**: 703.190 EAEDC Disability  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.60  

#### Rank 1 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_703_191__005`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 6 / 11
- **Program**: EA
- **Hierarchy**: (E) The Department’s agent shall make the determination of disability for EAE...
- **Judge reason**: The chunk describes how EAEDC disability is determined through medical authority review and SSI/SSDI standards, but doesn't explain what EAEDC disability actually is or provide comprehensive definition of the program itself.

```
(4) the applicant or client verifies that he or she is eligible for SSI or SSDI or considered disabled for purposes of SSI or SSDI (see 106 CMR 703.191(A)(2)).
(F) If a disability determination by the Department’s agent is:
(1) required and the competent medical authority states that the applicant or client meets a medical standard, SSI Listing of Impairments, or has an impairment affecting his or her ability to work, and if otherwise eligible, the applicant or client shall receive EAEDC benefits pending a review by the Department’s agent; or
(2) not required because of 106 CMR 703.191(E), the EAEDC applicant or client shall be considered disabled upon giving the Department the necessary medical report or verifications and shall receive EAEDC benefits if otherwise eligible.
```

#### Rank 2 — PARTIAL (sim 0.511)

- **Chunk ID**: `cmr_sec_703_191__004`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 5 / 11
- **Program**: EA
- **Hierarchy**: (E) The Department’s agent shall make the determination of disability for EAE...
- **Judge reason**: The chunk explains how disability is determined for EAEDC eligibility (by Department's agent or competent medical authority) but does not define what EAEDC disability actually is or provide the substantive criteria/standards for the determination.

```
(E) The Department’s agent shall make the determination of disability for EAEDC eligibility except when:
(1) a competent medical authority as defined in 106 CMR 701.600: Definition of Terms verifies that the applicant or client has an impairment or combination of impairments that:
(a) is expected to last at least 60 days but not more than 90 days; and
(b) meets or is equivalent to a medical standard defined in 106 CMR 703.192 or impairment included in the SSI Listing of Impairments.
(2) the applicant’s or client’s medical report is not completed by a competent medical authority, is not completed within 30 days of filing with the Department, or is not based on an examination conducted within 30 days from completion as required by l06 CMR 703.191(D);
(3) a competent medical authority verifies that the EAEDC applicant or client does not have an impairment that affects his or her ability to work and/or that the applicant’s or client’s impairment or combination of impairments is not expected to last for 60 days or more; or
```

#### Rank 3 — RELEVANT (sim 0.509)

- **Chunk ID**: `cmr_sec_703_191__000`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 1 / 11
- **Program**: EA
- **Hierarchy**: (A) An EAEDC applicant or client younger than 65 years old is disabled if he ...
- **Judge reason**: The chunk directly defines EAEDC disability and explains the three methods used to determine it: medical verification against standards, SSI Listing of Impairments, or vocational assessment.

```
(A) An EAEDC applicant or client younger than 65 years old is disabled if he or she has an impairment or combination of impairments that is expected to last 60 days or more and that substantially reduces or eliminates the applicant’s or client’s ability to support himself or herself. An applicant or client shall be considered as having such an impairment or combination of impairments if he or she:
(1) has an impairment or combination of impairments verified by a competent medical authority as defined in 106 CMR 701.600: Definition of Terms, on a medical report prescribed by the Department, which meets the requirements of 106 CMR 703.191(D). The competent medical authority and the agency or organization under contract/agreement with the Department to provide disability evaluation services (hereafter referred to as the Department’s agent), when required, determines that the impairment:
(a) meets a standard as specified in 106 CMR 703.192;
(b) is included in the SSI Listing of Impairments as specified in 20 CFR, Part 404, Subpart P, Appendix 1; or
(c) substantially reduces or eliminates the applicant’s or client’s ability to support himself or herself when consideration is given to the vocational factors as specified in 106 CMR 703.193; or
```

#### Rank 4 — PARTIAL (sim 0.499)

- **Chunk ID**: `cmr_sec_703_010__000`
- **Section**: `703.010` — Overview of EAEDC Nonfinancial Requirements
- **Program**: EA
- **Judge reason**: The chunk identifies that disability is an EAEDC eligibility requirement and references 106 CMR 703.191 for the definition, but does not actually explain what EAEDC disability is or how it is determined.

```
In order to receive EAEDC, an applicant or client must meet all of the applicable eligibility requirements. These requirements are both nonfinancial or financial. The nonfinancial requirements for EAEDC eligibility are:
(A) 106 CMR 703.600: Elderly - 65 Years of Age or Older;
(B) 106 CMR 703.191: Disabled;
(C) 106 CMR 703.610: Participant in a Massachusetts Rehabilitation Commission Program;
(D) 106 CMR 703.620: Caring for the Disabled;
(E) 106 CMR 703.700: Caretaker Family;
(G) 106 CMR 703.800: Age, Identity, Resident, Place of Residence, Temporary Absence, and Disqualifying Absences;
(H) 106 CMR 703.400: Citizens, Noncitizens and Canadian-born Indians; and
(I) 106 CMR 701.230: Social Security Number (SSN).
```

#### Rank 5 — PARTIAL (sim 0.495)

- **Chunk ID**: `cmr_sec_703_620__000`
- **Section**: `703.620` — EAEDC Caring for the Disabled
- **Program**: EA
- **Judge reason**: The chunk explains EAEDC eligibility for caregivers of disabled persons but does not define what constitutes disability or how disability itself is determined for EAEDC purposes.

```
In order to be eligible for EAEDC as caring for the disabled, the following two conditions must be met:
(1) An applicant or client is required to care for a disabled person in the home in need of constant care; and
(2) if the constant care was not provided, the disabled person would be required to be institutionalized. Both elements must exist for an applicant or client of EAEDC to be categorically eligible. The applicant or client must verify the person’s disability, the need for constant care, and the risk of institutionalization without such care. These must be verified at application, redetermination, or time of any address change, by a written statement from the disabled person’s physician on the physician’s letterhead. The income of the disabled person shall be considered in the determination of eligibility (see 106 CMR 704.340: Eligibility Test for an EAEDC Person Caring for a Disables Person). If the income of the disabled person exceed those limits, the applicant or client is ineligible for EAEDC. The EAEDC applicant or client must meet all other nonfinancial and financial requirements of the EAEDC program as specified in 106 CMR 703.000 and 704.000: Overview of Financial Eligibility.
```


### cmr_024 — ESP overview (rank-1: PARTIAL)

**Question**: What is the Employment Services Program  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `707.100`  
**Notes**: 707.100 Introduction to ESP/Orientation  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.435)

- **Chunk ID**: `cmr_sec_707_185__002`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (B) Services.
- **Judge reason**: Describes services within a post-employment component but does not define what the Employment Services Program itself is or its overall purpose and structure.

```
(B) Services. Services in the Post-employment Services component may include, but are not limited to:
(1) transition support services;
(2) employee work force retention services;
(3) skills and educational advancement services; and
(4) re-employment and job upgrade services.
```

#### Rank 2 — PARTIAL (sim 0.424)

- **Chunk ID**: `cmr_sec_707_185__000`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 1 / 4
- **Program**: EA
- **Judge reason**: Describes Post-employment Services, which is a component related to employment services, but does not define or explain the Employment Services Program itself.

```
The Post-employment Services component is a voluntary program which provides current and former clients with services that lead to career advancement and employment stability. Participation is subject to the requirements provided in this regulation and depends on available funding and resources. The Department shall determine eligibility for and authorize Post-employment Services. Post-employment Services may only be provided by provider agencies under contract with the Department, and services may vary by provider.
```

#### Rank 3 — PARTIAL (sim 0.418)

- **Chunk ID**: `cmr_sec_707_185__001`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (A) Eligible Participants.
- **Judge reason**: Describes eligibility for Post-employment Services component but does not define or explain what the Employment Services Program is overall.

```
(A) Eligible Participants. The following individuals are eligible to participate in the Post-employment Services component:
(1) employed current and former TAFDC clients; and
(2) current and former clients who are in the job search phase of a Department-approved job readiness or employment activity. In order to participate, the individual must first be accepted for participation by an authorized Post-employment Services provider. Eligibility for the Post-employment Services component is limited to up to 12 months from the date the TAFDC case closed.
```

#### Rank 4 — PARTIAL (sim 0.414)

- **Chunk ID**: `cmr_sec_707_185__003`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (C) Participation Criteria.
- **Judge reason**: Describes participation criteria for Post-employment Services component but does not explain what the Employment Services Program itself is or its overall purpose and structure.

```
(C) Participation Criteria. The following are the criteria for participation in the Post-employment Services component:
(1) The individual is accepted for participation by the Post-employment Services provider;
(2) The individual must attend a program orientation required by the service provider;
(3) The individual must attend case management sessions required by the service provider; and
(4) The individual must participate in Post-employment Services activities scheduled by the service provider. The individual may terminate his or her participation by notifying the Post-employment Services provider.
```

#### Rank 5 — PARTIAL (sim 0.408)

- **Chunk ID**: `cmr_sec_707_160__000`
- **Section**: `707.160` — Supported Work Component
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: Describes a component of employment services (Supported Work Component) but does not define or comprehensively explain what the Employment Services Program itself is.

```
The Supported Work Component provides education, training, employment and support services that an individual needs to obtain and maintain employment. This component consists of Pre-worksite training and Worksite placement. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP) and the criteria in 106 CMR 707.160(A)(2) and (B).
```


### cmr_025 — FEP overview (rank-1: RELEVANT)

**Question**: What is the Full Employment Program for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `708` — judge picked rank-1 RELEVANT chunk in section `708.000` (section-author intuition agrees)  
**Notes**: BROAD — chapter 708 generally (only 7 sections, all about FEP)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.581)

- **Chunk ID**: `cmr_sec_708_000__000`
- **Section**: `708.000` — Overview
- **Program**: EA
- **Judge reason**: The chunk directly defines the Full Employment Program for TAFDC, explaining its purpose, how it works, and the benefits clients receive.

```
The Full Employment Program (FEP) component provides clients with paid work experience and on-the-job training needed to obtain an unsubsidized job. Clients participating in the Full Employment Program (FEP) will receive a subsidized wage in lieu of TAFDC cash benefits and are subject to FEP criteria in accordance with 106 CMR 707.180: Full Employment Program.
```

#### Rank 2 — RELEVANT (sim 0.522)

- **Chunk ID**: `cmr_sec_707_180__000`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) Activities. Activities in FEP include:
- **Judge reason**: The chunk directly defines the Full Employment Program for TAFDC, explaining its purpose, how it works, and what activities it includes.

```
The Full Employment Program (FEP) component provides individuals work experience needed to obtain an unsubsidized job. Participants are paid a subsidized wage in lieu of receiving TAFDC.
(A) Activities. Activities in FEP include:
(1) full-time employment of 35 to 40 hours per week consistent with the employer's schedule; and
(2) completion of an Employment Development Plan (EDP) as provided in 106 CMR 707.110.
```

#### Rank 3 — PARTIAL (sim 0.514)

- **Chunk ID**: `cmr_sec_708_100__000`
- **Section**: `708.100` — Participation Requirements for Full Employment Program (FEP) Employers
- **Program**: EA
- **Judge reason**: The chunk describes employer requirements and acceptance criteria for FEP but does not explain what the Full Employment Program itself is or its purpose for TAFDC participants.

```
(A) A Massachusetts employer may request to be a Full Employment Program (FEP) employer. An employer who is accepted for participation must sign an Application Agreement agreeing to the program requirements and responsibilities.
(B) The Department will accept an employer requesting to participate in FEP who offers training and experience for FEP participants to improve the participant's competitive position for finding unsubsidized employment. Acceptance as a FEP employer does not guarantee placement of a FEP participant.
(C) The Department may refuse to accept any employer who:
(1) has been found guilty of violating any laws or regulations governing employment or who has current charges pending for violation of any laws or regulations governing employment;
(2) refuses to sign the Application Agreement or complete any related paperwork; or
(3) has been excluded or terminated from participation in accordance with 106 CMR 708.130. The Department will, at its discretion, determine which employers may participate in the program.
```

#### Rank 4 — PARTIAL (sim 0.512)

- **Chunk ID**: `cmr_sec_707_180__002`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (C) Benefits of the Full Employment Program. A participant in FEP shall:
- **Judge reason**: The chunk describes benefits of the Full Employment Program but does not explain what the program is, its purpose, eligibility requirements, or how it operates overall.

```
(C) Benefits of the Full Employment Program. A participant in FEP shall:
(1) receive a per hour wage from the employer that is at least equal to the current Massachusetts minimum wage;
(2) remain eligible for MassHealth;
(3) have an Individual Asset Account established in which $1 will be credited each hour the participant works. The money from the Individual Asset Account shall be paid to the participant when he or she leaves FEP. This amount shall be in addition to the wage paid by the employer;
(4) receive training experience on the job;
(5) be entitled to sick, holiday and vacation leave, and other benefits provided to other employees;
(6) be considered to be an employee of the FEP employer and shall be entitled to all benefits required by state and federal law;
(7) be eligible for workers' compensation, when appropriate; and
(8) be eligible for a Transitional Child Care (TCC) referral in accordance with 106 CMR 707.210(A)(1)(f)), transitional medical assistance (TMA) through MassHealth and Transitional Support Services stipends when the TAFDC case is terminated due to earnings.
```

#### Rank 5 — PARTIAL (sim 0.498)

- **Chunk ID**: `cmr_sec_708_150__000`
- **Section**: `708.150` — Wage Reimbursements to FEP Employers
- **Program**: EA
- **Judge reason**: The chunk describes specific wage reimbursement details and Individual Asset Account procedures for FEP participants, but does not explain what the Full Employment Program itself is or its overall purpose and structure.

```
(A) Once a FEP participant begins working in a subsidized FEP position, the Department shall pay FEP employers the following amounts as partial reimbursements for wages paid to FEP participants in accordance with 106 CMR 707.180: Full Employment Program:
(1) For the first nine months of employment, the FEP employer will receive a net reimbursement of $2.50 per hour for each FEP participant. This is an initial subsidy of $3.50 per hour, of which $1.00 per hour will be diverted to an Individual Asset Account (IAA) held by the Department on behalf of each FEP participant.
(2) For the next three months of employment, the FEP employer will receive a net reimbursement of $1.50 per hour for each FEP participant. This is an initial subsidy of $2.50 per hour, of which $1.00 per hour will be diverted to an IAA held by the Department on behalf of each FEP participant.
(B) An agency contracted by the Department shall hold and manage the IAA for each FEP participant. The total IAA contributions shall be held and be paid to the FEP participant by the Department upon termination of the participant from the FEP program in accordance with 106 CMR 707.180: Full Employment Program. REGULATORY AUTHORITY 106 CMR 708.000: M.G.L. c. 18, § 10
```


### cmr_026 — TAFDC MassHealth (rank-1: PARTIAL)

**Question**: When is a SNAP household eligible for MassHealth referral  
**Program filter**: (none)  
**Expected section (for reference)**: `705.100`  
**Notes**: 705.100 MassHealth (in TCAP related benefits — though question says SNAP, might cross-pull)  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.535)

- **Chunk ID**: `cmr_sec_705_200__000`
- **Section**: `705.200` — Supplemental Nutrition Assistance Program (SNAP)
- **Program**: EA
- **Judge reason**: The chunk discusses SNAP eligibility and categorical eligibility but does not address MassHealth referral eligibility criteria or when such referrals occur.

```
The purpose of SNAP is to ensure adequate nutrition for low income households. The program is administered by the Department. Obtaining SNAP
(A) An applicant or client may also apply for and be eligible for SNAP benefits. The worker must ask whether the applicant wants to apply for SNAP, and if so, must ensure that the application is processed appropriately. When all the members of the SNAP household are receiving TAFDC and/or SSI benefits, the household is categorically eligible for SNAP. See 106 CMR 365.180: Categorically Eligible Households.
```

#### Rank 2 — PARTIAL (sim 0.531)

- **Chunk ID**: `cmr_sec_702_120__003`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 4 / 9
- **Program**: EA
- **Hierarchy**: (E) Related Benefits and Services.
- **Judge reason**: The chunk mentions SNAP and MassHealth referral together but addresses TAFDC/EAEDC eligibility for MassHealth rather than specifically when SNAP households are eligible for MassHealth referral.

```
(E) Related Benefits and Services. The worker must inform the applicant that eligibility for TAFDC or EAEDC benefits will confer eligibility for MassHealth as specified in the regulations of the Division of Medical Assistance; that he or she may choose to apply for SNAP benefits as part of the application and that SNAP eligibility will be determined according to SNAP eligibility criteria; and that if he or she is found ineligible for TAFDC or EAEDC he or she may make a separate application for MassHealth, and/or SNAP benefits. The worker must make any necessary referrals for other benefits or services, such as child care. See 106 CMR 705: Related Benefits.
```

#### Rank 3 — PARTIAL (sim 0.496)

- **Chunk ID**: `cmr_sec_705_100__000`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 1 / 4
- **Program**: EA
- **Judge reason**: The chunk discusses MassHealth eligibility for TAFDC and EAEDC clients but does not specifically address when a SNAP household is eligible for MassHealth referral.

```
MassHealth provides medical services for individuals who meet specific income and other eligibility requirements. Current TAFDC and EAEDC clients are eligible for MassHealth without filing a separate application. The following are eligible to receive MassHealth benefits: (MA REG. # 1360, Dated 3-9-18)
```

#### Rank 4 — PARTIAL (sim 0.493)

- **Chunk ID**: `cmr_sec_705_100__002`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (B) Extension of MassHealth after the TAFDC Termination for Employment Reasons
- **Judge reason**: Addresses MassHealth referral eligibility but only for the specific case of TAFDC termination due to employment, not general SNAP household eligibility criteria.

```
(B) Extension of MassHealth after the TAFDC Termination for Employment Reasons
(1) Members of a TAFDC assistance unit who are ineligible for TAFDC remain eligible for MassHealth for the 12-calendar-month period beginning with the month in which the family becomes ineligible for TAFDC provided that the unit:
(a) continues to include a child who meets the age requirements provided in 106 CMR 703.220: TAFDC Dependent Child: Younger than 18 Years Old and 703.230: TAFDC Dependent Child: 18 years of Age) of a dependent child getting TAFDC;
(b) became ineligible for TAFDC because of an income increase from the grantee's work; and
(c) has a member who continues to work.
```

#### Rank 5 — PARTIAL (sim 0.486)

- **Chunk ID**: `cmr_sec_705_250__000`
- **Section**: `705.250` — Supplemental Nutrition Assistance
- **Chunk position**: 1 / 2
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk discusses SNA/SNAP eligibility requirements but does not address MassHealth referral eligibility criteria specifically.

```
(A) Requirements. The Department provides Supplemental Nutrition Assistance (SNA) benefits to certain households receiving Non-public Assistance (NPA) SNAP benefits. These households must meet the criteria 106 CMR 705.250(A)(1) through (4) to be eligible:
(1) receive NPA SNAP benefits, this is met once the household has received its first cyclical month's issuance;
(2) be categorically eligible for TANF assistance (see 106 CMR 365.180(A)(4)(a) through (c));
(3) contain no household member who is an active TAFDC client; and
(4) contain at least one parent or caretaker relative who is working and who is a citizen or meets the noncitizen requirements provided in 106 CMR 703.430 as follows:
(a) for a single-parent or caretaker-relative household, the parent or caretaker relative must be working:
(i) at least 30 hours per week, if the household does not contain a child younger than six years old; or (ii) at least 20 hours per week, if the household contains a child younger than six years old;
(b) for a household that contains two parents or two caretaker relatives:
(i) if one of the parents or caretaker relatives is not a citizen and does not meet the noncitizen requirements provided in 106 CMR 703.430: TAFDC Noncitizen Status, the parent or caretaker relative, who is a citizen or meets the noncitizen requirements provided in 106 CMR 703.430: TAFDC Noncitizen Status, must be working at least 30 hours per week; or
```


### cmr_027 — TAFDC overpayments (rank-1: RELEVANT)

**Question**: How does DTA correct overpayments and underpayments  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `706.210` — judge picked rank-1 RELEVANT chunk in section `706.210` (section-author intuition agrees)  
**Notes**: 706.210 Correction of Overpayments and Underpayments  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — RELEVANT (sim 0.462)

- **Chunk ID**: `cmr_sec_706_210__000`
- **Section**: `706.210` — Correction of Overpayments and Underpayments
- **Program**: EA
- **Judge reason**: The chunk directly explains DTA's procedures for identifying, correcting, and recovering both overpayments and underpayments, including notification requirements and offset procedures.

```
The Department has the responsibility to identify and correct overpayments and underpayments. The Department must promptly correct underpayments to current clients and to those who would have been clients if the mistake causing the underpayment had not occurred. When an underpayment is established, the Department shall send written notice to the client that:
(1) includes the amount; and
(2) informs the client of the right to request a fair hearing. Before an action to recoup an overpayment as provided in 106 CMR 706.290, the Department shall notify the client in accordance with 106 CMR 702.500: Notification of Proposed Action. If both an underpayment and an overpayment exist, the Department may offset one against the other if the existence and amount of both the underpayment and the overpayment can be promptly determined. Otherwise, the Department shall proceed to correct the underpayment and overpayment independently. Retroactive corrective underpayments shall not be considered as income or as an asset for purposes of determining continued eligibility and amount of assistance either in the month paid or in the following month. All overpayments are subject to recovery by the Department. Overpayments involving possible fraud shall be referred to the Bureau of Special Investigations (BSI).
```

#### Rank 2 — PARTIAL (sim 0.395)

- **Chunk ID**: `cmr_sec_706_250__001`
- **Section**: `706.250` — Recovery
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (B) The Department shall recover all overpayments from current clients regard...
- **Judge reason**: The chunk addresses overpayment recovery procedures but does not explain how DTA corrects underpayments, which is half of the user's question.

```
(B) The Department shall recover all overpayments from current clients regardless of the amount of the overpayment. The Department shall recover all overpayments from previous clients as provided in 106 CMR 706.280. An overpayment shall be recovered from grantees even if grantees were overpaid in one cash assistance program and is now receiving benefits in another cash assistance program.
```

#### Rank 3 — PARTIAL (sim 0.382)

- **Chunk ID**: `cmr_sec_706_220__000`
- **Section**: `706.220` — Causes of Overpayments
- **Program**: EA
- **Judge reason**: The chunk explains causes of overpayments but does not address how DTA corrects or recovers overpayments and underpayments.

```
(A) Department Error. An overpayment may occur as a result of Department error. Department error includes, but is not limited to, failure of the worker to act on information that affects eligibility or the amount of assistance.
(B) Payments Pending a Fair Hearing Decision. An overpayment occurs when the Department's position is upheld on an appeal by a client of a reduction or termination, and aid was paid pending the implementation of the decision.
(C) Client Error, Misrepresentation or Withholding of Information. An overpayment may occur as a result of client error. Client error may occur when the client, because of a misunderstanding of his or her responsibilities, fails to notify the Department of a change in resources or other circumstances within the prescribed ten days of such a change. Certain instances of client error may be fraudulent and should be referred to BSI. An overpayment may also occur because the applicant or client knowingly misrepresents or withholds information from the Department. If there is a reasonable possibility that fraud occurred in an overpayment of benefits, the case should be referred to BSI as provided in 106 CMR 706.240.
```

#### Rank 4 — PARTIAL (sim 0.376)

- **Chunk ID**: `cmr_sec_706_250__000`
- **Section**: `706.250` — Recovery
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) The Department shall act promptly to recover all overpayments from curren...
- **Judge reason**: Addresses overpayment recovery procedures but does not explain how underpayments are corrected or provide a complete picture of both correction mechanisms.

```
(A) The Department shall act promptly to recover all overpayments from current clients and from previous clients who reapply for and are determined eligible for TAFDC or EAEDC. The Department shall refer overpayments to BSI whenever there is a reasonable possibility of fraud. In such cases, no recovery may take place until BSI notifies the Department that it has decided not to investigate or its investigation is complete, or unless recovery is being made through the Administrative Disqualification process as provided in 106 CMR 706.345.
```

#### Rank 5 — RELEVANT (sim 0.375)

- **Chunk ID**: `cmr_sec_706_290__000`
- **Section**: `706.290` — Recovery from Current Clients
- **Program**: EA
- **Judge reason**: The chunk directly addresses how DTA recovers overpayments through specific methods (recoupment, lump sum, installments, wage assignment) and recovery amounts, which is a core part of how DTA corrects overpayments.

```
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


### cmr_028 — identity verification (rank-1: RELEVANT)

**Question**: How does DTA verify identity  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361` — judge picked rank-1 RELEVANT chunk in section `361.610` (section-author intuition agrees)  
**Notes**: BROAD — chapter 361 application processing covers verification; many sections in 361 may match  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.55  

#### Rank 1 — RELEVANT (sim 0.411)

- **Chunk ID**: `cmr_sec_361_610__005`
- **Section**: `361.610` — Verification Requirements at Initial Certification
- **Chunk position**: 6 / 10
- **Program**: SNAP
- **Hierarchy**: (G) Identity.
- **Judge reason**: Directly explains DTA's identity verification procedures, including acceptable documentary evidence and collateral contact methods.

```
(G) Identity. The identity of the applicant and any authorized representative applying on behalf of the household shall be verified prior to initial certification. Identity may be verified through documentary evidence that is readily available to the applicant or representative. Examples of acceptable documentary evidence which the applicant may provide include, but are not limited to, a driver's license; a work or school ID; an ID for health benefits or for another assistance or social service program; a voter registration card; wage stubs or a birth certificate. Any documents which reasonably establish identity must be accepted, and no requirement for a specific type of document may be imposed. In the absence of documentary evidence, identity shall be verified by collateral contact in accordance with 106 CMR 361.640.
```

#### Rank 2 — RELEVANT (sim 0.375)

- **Chunk ID**: `cmr_sec_365_830__000`
- **Section**: `365.830` — Expedited Service Verification Requirements
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses DTA identity verification methods, listing acceptable documentary evidence and collateral contact procedures used to verify applicant identity.

```
The household's identity is the only eligibility factor that must be verified before expedited service is provided. Readily available documentary evidence or collateral contact, in accordance with 106 CMR 361.640(A): Documentary Evidence and (B): Collateral Contact, may be used. Examples of acceptable documentary evidence include, but are not limited to, a driver's license, a work or school identification (I.D.) card, a voter registration card, a birth certificate, wage stubs or an I.D. for health benefits or for another assistance or social services program. Any documents that reasonably establish the applicant's identity must be accepted and no requirement for a specific type of document, such as a birth certificate, may be imposed. The Social Security number requirements of 106 CMR 362.500: Social Security Numbers do not have to be met before expedited service is provided. These requirements must be met prior to the first full month of participation, unless good cause for not meeting these requirements is established in accordance with 106 CMR 362.500(C): Determining Good Cause. The applicant must register for work if subject to SNAP Work Requirements in accordance with 106 CMR 362.300: Work Requirements unless exempt or unless the household has designated an authorized representative to apply on its behalf in accordance with 106 CMR 361.300: Authorized Representatives. Every household member required to meet SNAP Work
```

#### Rank 3 — RELEVANT (sim 0.364)

- **Chunk ID**: `cmr_sec_366_920__003`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 4 / 5
- **Program**: SNAP
- **Hierarchy**: (D) Verification at Initial Certification.
- **Judge reason**: The chunk directly addresses how DTA verifies identity at initial certification, including use of SDX data and specific procedures for identity verification.

```
(D) Verification at Initial Certification.
(1) If the application is filed at an SSA office, SSA will indicate what required verifications are on file at the SSA office. Unless the application is incomplete, mandatory verification is missing, or certain information on the application is questionable, no other verification shall be requested.
(2) If an application is filed at a TAO, available SDX data will be used to verify the assets, identity, residency, social security number and unearned income of the SSI recipient. Additional verification of these eligibility factors will be required only if the information supplied by the SSI recipient contradicts SDX data.
(3) Deductible expenses claimed by the applicant shall be verified in accordance with Department requirements.
(4) Noncitizen Status. Noncitizen Status will be verified through SDX. The applicant must meet an eligible noncitizen status in accordance with 106 CMR 362.220(B). The applicant will be denied if the noncitizen status on SDX is an ineligible status. Additional verification of noncitizen status will be required if the SDX information is questionable.
```

#### Rank 4 — PARTIAL (sim 0.340)

- **Chunk ID**: `cmr_sec_365_830__001`
- **Section**: `365.830` — Expedited Service Verification Requirements
- **Chunk position**: 2 / 2
- **Program**: SNAP
- **Judge reason**: The chunk states that identity must be verified before expedited service but does not explain the actual methods or procedures DTA uses to verify identity.

```
Requirements must register for work before expedited service is provided (this requirement shall be waived for disaster SNAP benefits as defined in 106 CMR 366.600: Disaster Certification). The worker should attempt to obtain as much required verification as possible during the interview, but should not delay the certification for expedited service until the sixth day if the worker has determined it is unlikely that other verification can be obtained within the expedited service processing time frame. Identity must always be verified before expedited service is provided.
```

#### Rank 5 — RELEVANT (sim 0.322)

- **Chunk ID**: `cmr_sec_361_640__000`
- **Section**: `361.640` — Sources of Verification
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Documentary Evidence.
- **Judge reason**: Directly explains DTA's methods for verifying identity and household circumstances, including documentary evidence, collateral contacts, and home visits.

```
Sources of verification include documentary evidence, collateral contacts or home visits. In all cases the source of the verification must be documented in the case record.
(A) Documentary Evidence. Workers shall use documentary evidence as the primary source of verification for all items except household size which may be verified by collateral contact. Documentary evidence consists of a written confirmation of a household's circumstances. Examples of documentary evidence shall include: wage stubs, SDX data, and utility bills. Although documentary evidence shall be the primary source of verification, acceptable verification shall not be limited to any specific type of document and may be obtained through the household or other source. Workers shall use an alternate source of verification such as collateral contact or home visit, when documentary evidence cannot be obtained or is insufficient to make a firm determination of eligibility or benefit level. When the verification is an original document, a photocopy of the document must be made, if possible. If circumstances prevent the photocopying of a document and a copy is not available, the worker must record the source and date of the document. The household must be permitted to keep the original document.
```


### cmr_029 — SNAP household composition (rank-1: RELEVANT)

**Question**: What are SNAP household composition rules  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.2` — judge picked rank-1 RELEVANT chunk in section `361.200` (section-author intuition agrees)  
**Notes**: BROAD — 361.200 series; multiple chunks should match  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.30  

#### Rank 1 — RELEVANT (sim 0.576)

- **Chunk ID**: `cmr_sec_361_200__001`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: The chunk directly addresses SNAP household composition rules by explaining specific rules (Spouse Rule and Parental Control Rule) that determine which individuals must be in the same household.

```
(A) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals together even if they do not do so unless an exception applies:
(1) Spouse Rule. An individual living with his or her spouse must be in the same SNAP household as the spouse. Spouses shall not be granted separate household status. Spouse is defined as either of two individuals who are legally married to one another, or who are living together and holding themselves out to the community as husband and wife by representing themselves as spouses to relatives, friends, neighbors, or tradespeople;
(2) Parental Control Rule. A child younger than 18 years old, except for a foster care child (as defined in 106 CMR 361.240(F)), who is living with an adult household member (not the child's parent) and under the parental control of the adult household member, must be in the same SNAP household as the adult household member. Parental control means providing financial support or supervision, or both, to an individual younger than 18 years old; and
```

#### Rank 2 — RELEVANT (sim 0.552)

- **Chunk ID**: `cmr_sec_361_200__002`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: The chunk directly addresses SNAP household composition rules by explaining which individuals must be in the same household, which individuals are considered separate households, and specific rules for different living situations.

```
(3) Parent/Child Rule. A child younger than 22 years old living with his or her natural, adopted or stepparent(s) must be in the same SNAP household as the parent(s).
(B) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals separately even if they do not do so.
(1) An individual, with or without children, residing in a drug or alcohol treatment center shall be one SNAP household separate from the other residents. See 106 CMR 365.600 through 365.690.
(2) A blind or disabled resident of a group living arrangement (106 CMR 365.600 through 365.690) who applies through the use of the facility's authorized representative shall be one SNAP household separate from the other residents. If a blind or disabled resident applies on his or her own behalf, the household size must be determined following the household concept rules defined in 106 CMR 361.200.
(3) An individual, with or without children, residing in a shelter for battered individuals and their children shall be one SNAP household separate from the other residents. See 106 CMR 365.550: Residents of Shelters for Battered Women and Their Children.
```

#### Rank 3 — PARTIAL (sim 0.540)

- **Chunk ID**: `cmr_sec_361_200__004`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (B) The following individuals living with others or groups of individuals liv...
- **Judge reason**: Addresses specific household composition rules for elderly/disabled individuals with family members, but is narrowly focused on one scenario rather than comprehensively covering SNAP household composition rules.

```
accordance with 106 CMR 363.210: Verification of Income. An elderly and disabled individual who meets the two conditions in 106 CMR 361.200(B)(4) and lives with his or her spouse, natural, adopted or stepchildren younger than 22 years old, or children younger than 18 years old living under his or her parental control must be in the same household as the spouse, natural, adopted or stepchildren, or children living under his or her parental control in accordance with 106 CMR 361.200(A).
```

#### Rank 4 — PARTIAL (sim 0.531)

- **Chunk ID**: `cmr_sec_361_230__003`
- **Section**: `361.230` — Nonhousehold Members
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (E) Others.
- **Judge reason**: Addresses one specific exception to household composition rules but doesn't provide comprehensive rules about who is included in or excluded from SNAP households.

```
(E) Others. Other individuals, with the exception of spouses, parents and their children younger than 22 years old, and children younger than 18 years old living under parental control of an adult household member in accordance with 106 CMR 361.200, who share living quarters with the household but do not purchase food and prepare meals with the household.
```

#### Rank 5 — RELEVANT (sim 0.531)

- **Chunk ID**: `cmr_sec_361_200__000`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: Directly defines SNAP household composition by outlining the three categories that determine who is considered a household for SNAP purposes.

```
A SNAP household is defined as:
(1) an individual who lives alone;
(2) an individual living with others who purchases food and prepares meals separately; or
(3) a group of individuals living together who purchase food and prepare meals together.
```


### cmr_030 — SNAP benefit calculation (rank-1: RELEVANT)

**Question**: How are SNAP benefits calculated  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364` — judge picked rank-1 RELEVANT chunk in section `364.600` (section-author intuition agrees)  
**Notes**: BROAD — chapter 364 entirely about determining benefit  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.513)

- **Chunk ID**: `cmr_sec_364_600__002`
- **Section**: `364.600` — Determining the Benefit Level
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (B) Household Size - Over Eight.
- **Judge reason**: This chunk directly explains the calculation method for SNAP benefits by detailing the formula used to determine monthly allotments based on household size and net income.

```
(B) Household Size - Over Eight.
(1) Determine the maximum allotment for the household size by adding the amount posted at www.mass.gov/dta for each individual in excess of eight to the maximum allotment for an eight-person household.
(2) Determine the household's monthly net income in accordance with 106 CMR 364.500.
(3) Multiply the household's monthly net income (using dollars and cents) by 30%. Drop any digits beyond the second decimal place. If the result is not whole dollars, round the result up to the next whole dollar.
(4) Subtract this 30% amount from the maximum allotment for the household size. The resulting amount is the household's monthly allotment. However, when the calculated amount is zero or less, the household is ineligible for benefits since its net income exceeds the level at which benefits are issued.
```

#### Rank 2 — RELEVANT (sim 0.494)

- **Chunk ID**: `cmr_sec_364_650__001`
- **Section**: `364.650` — Prorating Initial Month's Benefits
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Count the number of days from the first day of the household's cyclical m...
- **Judge reason**: This chunk directly explains the calculation method for SNAP benefit allotments in the initial month, which is a core component of how SNAP benefits are calculated.

```
greater than $400, the initial month's allotment is calculated as follows:
(A) Count the number of days from the first day of the household's cyclical month through the date of application, inclusive, to determine the day of the cyclical month. If the day of the cyclical month is 31, use the number 30 instead of 31. Subtract the day of the cyclical month from 31. Multiply the result by the household's monthly allotment. Divide the result of this by 30;
```

#### Rank 3 — PARTIAL (sim 0.491)

- **Chunk ID**: `cmr_sec_364_650__002`
- **Section**: `364.650` — Prorating Initial Month's Benefits
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Hierarchy**: (B) If the result of 106 CMR 364.
- **Judge reason**: Describes rounding and minimum benefit rules but doesn't explain the actual calculation methodology for determining SNAP benefit amounts.

```
(B) If the result of 106 CMR 364.650(A) is not a whole dollar, round the result down to the next whole dollar by dropping cents; then
(C) If the result of 106 CMR 364.650(B), is less than $10, no benefits shall be issued for the initial month.
```

#### Rank 4 — PARTIAL (sim 0.484)

- **Chunk ID**: `cmr_sec_366_910__006`
- **Section**: `366.910` — Bay State CAP Households
- **Chunk position**: 7 / 12
- **Program**: SNAP
- **Hierarchy**: (F) Bay State CAP Benefit Calculation.
- **Judge reason**: Discusses income calculation steps but focuses on Bay State CAP (cash assistance) rather than SNAP benefit calculation specifically.

```
(3) The shelter deduction will be subtracted from the household's adjusted gross income to determine the monthly net income.
(4) The net monthly income will be used to determine the Bay State CAP benefit amount in accordance with 106 CMR 364.600: Determining the Benefit Level.
```

#### Rank 5 — PARTIAL (sim 0.479)

- **Chunk ID**: `cmr_sec_364_980__000`
- **Section**: `364.980` — SNAP Issuance Tables
- **Program**: SNAP
- **Judge reason**: Explains what eligible clients receive but doesn't describe the actual calculation methodology or factors used to determine benefit amounts.

```
A client who is eligible for SNAP benefits will receive 100% of the SNAP benefit allotment listed in the Program Issuance Tables. The standards in the SNAP Issuance Tables are based on household size and are adjusted annually by USDA/FNS. These standards are posted at www.mass.gov/dta. NON-TEXT PAGE
```


### cmr_031 — section number lookup (rank-1: IRRELEVANT)

**Question**: What does 363.140 cover  
**Program filter**: (none)  
**Expected section (for reference)**: `363.140`  
**Notes**: ADVERSARIAL — exact section-number query. Tests whether the embedding picks up the literal '363.140' token. Hybrid search should excel here.  
**Scores**: Relevant@5 = 0, Useful@5 = 0, rank-weighted = 0.00  

#### Rank 1 — IRRELEVANT (sim 0.182)

- **Chunk ID**: `cmr_sec_702_800__002`
- **Section**: `702.800` — Assignments for Third Party Recoveries
- **Chunk position**: 3 / 3
- **Program**: EA
- **Hierarchy**: (B) It is the responsibility of the applicant or client to provide the detail...
- **Judge reason**: The chunk discusses settlement reporting and lien procedures but does not address what regulation 363.140 specifically covers.

```
(10) a copy of the police report (if applicable). Upon any partial or final settlement of the case, the applicant or client who signed the original assignment or his or her attorney or authorized representative (if the applicant or client has one) is required to provide the Department with information on the amount of the settlement and the details surrounding it. Failure to comply with any of these provisions is grounds for denial, closing, and/or referral to the Bureau of Special Investigations. Workers may not compute the amount of a lien, but must make a referral to the Department’s authorized agent for computing the amount of a lien. REGULATORY AUTHORITY 106 CMR 702.000: M.G.L. c. 18.
```

#### Rank 2 — IRRELEVANT (sim 0.180)

- **Chunk ID**: `cmr_sec_360_220__000`
- **Section**: `360.220` — Complaint Requirements
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Hierarchy**: (A) Complaints shall contain the following information to facilitate investig...
- **Judge reason**: The chunk describes complaint procedures for discrimination investigations but does not explain what regulation 363.140 covers or its scope.

```
(A) Complaints shall contain the following information to facilitate investigations:
(1) name, address and telephone number or other means of contacting the person alleging discrimination;
(2) location and name of the organization or office accused of discriminatory practices;
(3) the nature of the incident or action or the aspect of program administration that led the person to allege discrimination;
(4) the reason for the alleged discrimination (e.g., age, race, color, sex, disability, religious creed, national origin or political belief);
(5) names, titles and addresses of persons who may have knowledge of the alleged discriminatory acts; and
(6) the date or dates on which the alleged discriminatory actions occurred.
```

#### Rank 3 — IRRELEVANT (sim 0.179)

- **Chunk ID**: `cmr_sec_360_220__002`
- **Section**: `360.220` — Complaint Requirements
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (C) Complaints will be accepted even if the information specified in 106 CMR ...
- **Judge reason**: The chunk discusses complaint procedures and investigation requirements under 106 CMR 360.220, not the content or coverage of 363.140.

```
(C) Complaints will be accepted even if the information specified in 106 CMR 360.220(A) is not complete. However, investigations will be conducted only if information concerning 106 CMR 360.220(A)(2) through (4) is provided.
```

#### Rank 4 — IRRELEVANT (sim 0.175)

- **Chunk ID**: `cmr_sec_701_310__000`
- **Section**: `701.310` — Right to Nondiscrimination and Equal Treatment
- **Program**: EA
- **Judge reason**: The chunk discusses anti-discrimination policies and equal treatment requirements but does not address what regulation 363.140 specifically covers.

```
All activities conducted by the Department must be carried out in accordance with Title VI of the Civil Rights Act of 1964 (42 U.S.C. § 2000d, et seq.), Section 504 of the Rehabilitation Act of 1973, as amended (29 U.S.C. § 794), the Americans with Disabilities Act of 1990, as amended, the Age Discrimination Act of 1975, as amended (42 U.S.C. § 6101, et seq.), and the Massachusetts Constitution. The Department of Transitional Assistance does not discriminate on the basis of race, color, sex, national origin, disability, sexual orientation, genetic information, military status or age in admission or access to, or treatment or employment in, its programs or activities. The Director of Equal Opportunity has been designated to help coordinate the Department's effort to comply with anti-discrimination laws. For further information about the regulations and the Department's grievance procedures for resolution of discrimination complaints, contact the Director of Equal Opportunity, Department of Transitional Assistance, 600 Washington Street, Boston, MA 02111. Benefits under the TAFDC and EAEDC Programs must be given to all applicants and clients on an equal basis. All applicants and clients must be treated in the same manner in determining whether they meet eligibility requirements, in calculating the amount of the grant, and in providing related benefits and referrals for services.
```

#### Rank 5 — IRRELEVANT (sim 0.175)

- **Chunk ID**: `cmr_sec_360_220__003`
- **Section**: `360.220` — Complaint Requirements
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (D) A complaint must be filed no later than 180 days from the date of the all...
- **Judge reason**: The chunk discusses complaint filing deadlines for discrimination cases and does not address what regulation 363.140 covers.

```
(D) A complaint must be filed no later than 180 days from the date of the alleged discrimination. However, the time for filing may be extended by the Secretary of Agriculture or the Commissioner of the Department or designee.
```


### cmr_032 — ADH acronym (rank-1: IRRELEVANT)

**Question**: What is an ADH  
**Program filter**: (none)  
**Expected section (for reference)**: `367.520`  
**Notes**: ADVERSARIAL — Administrative Disqualification Hearing. 367.520 Introduction to ADH.  
**Scores**: Relevant@5 = 0, Useful@5 = 2, rank-weighted = 0.40  

#### Rank 1 — IRRELEVANT (sim 0.313)

- **Chunk ID**: `cmr_sec_701_390__000`
- **Section**: `701.390` — Department Obligations under Title II of the Americans with Disabilities Act (ADA)
- **Chunk position**: 1 / 5
- **Program**: EA
- **Hierarchy**: (A) Definitions.
- **Judge reason**: The chunk defines disability under the ADA and qualified individuals with disabilities, but does not define or explain what an ADH is in the context of Massachusetts DTA policy.

```
(A) Definitions.
(1) Disability under the ADA is defined as:
(a) a physical or mental impairment which substantially limits one or more major life activities of an individual;
(b) a record of having such impairment; or
(c) being regarded as having such impairment. Disability does not include psychoactive substance abuse disorder resulting from current illegal use of drugs.
(2) A qualified individual with a disability is an individual who meets the essential eligibility requirements for the receipt of services or participation in programs or activities provided by the Department with or without:
(a) reasonable modifications to rules, policies, or practices;
(b) the removal of architectural, communication, or transportation barriers; and/or
(c) the provision of auxiliary aids and services. An individual who poses a direct threat to the health and safety of others is not a qualified individual. An individual who is currently engaging in the illegal use of drugs when the Department acts on the a basis of such use is not a qualified individual.
```

#### Rank 2 — IRRELEVANT (sim 0.290)

- **Chunk ID**: `cmr_sec_701_390__001`
- **Section**: `701.390` — Department Obligations under Title II of the Americans with Disabilities Act (ADA)
- **Chunk position**: 2 / 5
- **Program**: EA
- **Hierarchy**: (A) Definitions.
- **Judge reason**: The chunk defines physical/mental impairment and major life activities but does not address what an ADH is or explain the acronym.

```
(3) Physical or Mental Impairment means:
(a) any physiological disorder or condition, cosmetic disfigurement, or anatomical loss affecting one or more of the following body systems: Neurological, musculoskeletal, special sense organs, respiratory (including speech organs), cardiovascular, reproductive, digestive, genitourinary, hemic and lymphatic, skin and endocrine; and
(b) Any mental or psychological disorder such as mental retardation, organic brain syndrome, emotional, or mental illness and specific learning disabilities.
(4) Major life activities include functions such as caring for one's self, performing manual tasks, walking, seeing, hearing, speaking, breathing, learning and working.
```

#### Rank 3 — PARTIAL (sim 0.282)

- **Chunk ID**: `cmr_sec_706_335__000`
- **Section**: `706.335` — The Administrative Disqualification Hearing (ADH)
- **Program**: EA
- **Judge reason**: The chunk discusses ADH procedures and consequences but does not define what an ADH is or explain its acronym/meaning.

```
If the individual or his or her representative fails to appear at the ADH without good cause, in accordance with 106 CMR 343.320(D), the ADH shall still be conducted. The hearing officer is required to carefully consider the evidence and determine if an Intentional Program Violation (IPV) was committed based on a preponderance of the evidence standard. If the individual is found to have committed an IPV, but the Director of the Division of Hearings later determines that there was good cause for the failure to appear, the previous decision shall be void and the Department shall conduct a new hearing. The individual has ten days from the date of the originally scheduled hearing to present evidence of good cause for failure to appear.
```

#### Rank 4 — PARTIAL (sim 0.279)

- **Chunk ID**: `cmr_sec_706_315__000`
- **Section**: `706.315` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: EA
- **Judge reason**: The chunk explains what an ADH does and when it's conducted, but doesn't define what the acronym ADH stands for or what it means.

```
An ADH shall be conducted by the Division of Hearings to determine if an Intentional Program Violation (IPV) has been committed, unless a determination is made by a court of law pursuant to 106 CMR 706.355. An ADH may be initiated by the Department if there is reason to believe an IPV was committed.
```

#### Rank 5 — IRRELEVANT (sim 0.278)

- **Chunk ID**: `cmr_sec_701_390__003`
- **Section**: `701.390` — Department Obligations under Title II of the Americans with Disabilities Act (ADA)
- **Chunk position**: 4 / 5
- **Program**: EA
- **Hierarchy**: (C) The Department, in providing any aid, benefit, or service, may not, direc...
- **Judge reason**: The chunk discusses disability non-discrimination requirements for DTA aid and services, but does not define or explain what an ADH is.

```
(C) The Department, in providing any aid, benefit, or service, may not, directly or through contractual, licensing, or other arrangements on the basis of disability:
(1) Deny a qualified individual with a disability the opportunity to participate in or benefit from the aid, benefit, or service;
(2) Afford a qualified individual with a disability an opportunity to participate in or benefit from the aid, benefit, or service that is not equal to that afforded others;
(3) Provide a qualified individual with a disability with an aid, benefit, or service that is not as effective in affording equal opportunity to obtain the same result, to gain the same benefit, or to reach the same level of achievement as that provided to others;
(4) Provide different or separate aids, benefits, or services to individuals with disabilities than is provided to others unless such action is necessary to provide qualified individuals with disabilities with aids, benefits, or services that are as effective as those provided to others; and
```


### cmr_033 — EPSDT acronym (rank-1: PARTIAL)

**Question**: What does EPSDT mean in DTA policy  
**Program filter**: (none)  
**Expected section (for reference)**: `705.130`  
**Notes**: ADVERSARIAL — Early and Periodic Screening, Diagnosis and Treatment. 705.130. Rare term.  
**Scores**: Relevant@5 = 0, Useful@5 = 1, rank-weighted = 0.50  

#### Rank 1 — PARTIAL (sim 0.514)

- **Chunk ID**: `cmr_sec_705_130__000`
- **Section**: `705.130` — Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)
- **Program**: EA
- **Judge reason**: The chunk describes EPSDT's purpose and what it provides, but does not explicitly state what the acronym EPSDT stands for or means.

```
The purpose of EPSDT is to provide all persons in the assistance unit younger than 21 years old the opportunity for preventive health care, including medical checkups, immunizations, and dental checkups. A full description of the EPSDT program is provided in MassHealth regulations of the Division of Medical Assistance.
```

#### Rank 2 — IRRELEVANT (sim 0.359)

- **Chunk ID**: `cmr_sec_705_140__000`
- **Section**: `705.140` — Family Planning Referrals
- **Program**: EA
- **Judge reason**: The chunk discusses family planning services but does not define or explain what EPSDT means.

```
The purpose of family planning is to help members of the assistance unit obtain counseling and medical services related to having or not having children. Participation in this is voluntary. All TAFDC clients are eligible for family planning referrals and must be informed of the program. MassHealth pays for medical services related to family planning.
```

#### Rank 3 — IRRELEVANT (sim 0.355)

- **Chunk ID**: `cmr_sec_705_100__003`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (C) EAEDC Medical Assistance.
- **Judge reason**: The chunk discusses EAEDC medical assistance and MassHealth but does not mention or define EPSDT at all.

```
(C) EAEDC Medical Assistance.
(1) The EAEDC program provides EAEDC medical assistance (i.e., limited medical services) to applicants and clients of EAEDC. These services shall be specified in MassHealth regulations of the Division of Medical Assistance.
(2) Certain clients of EAEDC may also be eligible for MassHealth in accordance with the MassHealth regulations of the Division of Medical Assistance. A client is ineligible for EAEDC Medical Assistance if he or she receives benefits under MassHealth.
```

#### Rank 4 — IRRELEVANT (sim 0.346)

- **Chunk ID**: `cmr_sec_701_600__006`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 7 / 25
- **Program**: EA
- **Hierarchy**: (L) Disabled Adult.
- **Judge reason**: The chunk defines 'Disabled Adult' but does not mention or explain what EPSDT means.

```
(L) Disabled Adult. An individual younger than 66 years old in the TAFDC program or under the age of 65 in the EAEDC program who meets the Department's medical and/or vocational standards as determined by the agency or organization under contract/agreement with the Department to provide disability evaluation services. In addition, an applicant or client shall be considered disabled if he or she is in receipt of Supplemental Security Income for the disabled, or Social Security benefits for the disabled. Manual Reference: 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits, 106 CMR 703.130: TAFDC Extension of Benefits Beyond the 24-month Period, 106 CMR 703.190: TAFDC Disability Exemption Process, 106 CMR 703.610: EAEDC Participant in a Massachusetts Rehabilitation Commission Program, and 106 CMR 703.620: EAEDC Caring for the Disabled.
```

#### Rank 5 — IRRELEVANT (sim 0.339)

- **Chunk ID**: `cmr_sec_701_395__002`
- **Section**: `701.395` — Learning Disabilities: Screening, Assessment, Sanction Relief and Extensions
- **Chunk position**: 3 / 6
- **Program**: EA
- **Hierarchy**: (B) While waiting for the completion of the assessment, DTA will help clients...
- **Judge reason**: The chunk discusses ESP (Employment Support Program) activities and learning disability assessments but does not define or explain what EPSDT means.

```
(B) While waiting for the completion of the assessment, DTA will help clients participate in their current activity or in starting a new ESP activity. (C)(1) If a client is sanctioned (or is notified of the Department's intention to sanction) for failure to comply with an EDP or the work requirement regarding participation in an ESP activity and the client:
(a) claims that his or her learning disability caused the failure;
(b) participates in the screening and a potential learning disability is indicated; and
(c) agrees to participate in and complete a learning disability assessment, the sanction will not occur while waiting for the assessment outcome. The Department will notify the client of this action in writing. If the individual is determined to have a learning disability that requires a reasonable accommodation to participate in ESP, the pending sanction will be removed.
(2) If any of the conditions of 106 CMR 701.395(C)(1) are not met or:
(a) the individual does not cooperate with the assessment process;
(b) the individual refuses to participate in an ESP program when effective accommodations are possible and have or will be made;
(c) the assessment results find that there is no learning disability or one that requires accommodation in the above ESP program; then the sanction can occur subject to DTA appeal rights as described in 106 CMR 343.000: Fair Hearing Rules.
```


### cmr_034 — PA household defined term (rank-1: PARTIAL)

**Question**: What is a Public Assistance household for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365.110`  
**Notes**: ADVERSARIAL — defined term. 365.110 Definition of a Public Assistance (PA) Household  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.60  

#### Rank 1 — PARTIAL (sim 0.518)

- **Chunk ID**: `cmr_sec_365_120__005`
- **Section**: `365.120` — Determining Eligibility and Benefit Level
- **Chunk position**: 6 / 6
- **Program**: SNAP
- **Hierarchy**: (C) Income Standards For PA Households.
- **Judge reason**: The chunk discusses how PA household payments are treated as income for SNAP purposes, but does not define what constitutes a Public Assistance household itself.

```
considered a lump sum payment. For example, if a household applies in November and is eligible in November but receives its first check in December to cover both months, only the December benefit amount is considered as income.
(c) Protective Payments. Protective payments are any portion of the cash grant that is legally obligated and otherwise payable to the PA household, but diverted by the Department to a third party for a household expense (e.g., vendor rent). Protective payments are countable as income when determining SNAP eligibility and benefit level.
```

#### Rank 2 — PARTIAL (sim 0.517)

- **Chunk ID**: `cmr_sec_365_170__000`
- **Section**: `365.170` — Department Action on Reported Changes
- **Chunk position**: 1 / 8
- **Program**: SNAP
- **Judge reason**: The chunk discusses how PA households are handled for SNAP purposes but does not define what constitutes a Public Assistance household.

```
Except as provided in 106 CMR 365.170, action shall be taken on reported changes in accordance with the notification and timeliness standards specified in 106 CMR 366.100 through 366.220. Public Assistance (PA) households must be notified whenever their SNAP benefits are altered as a result of changes in their PA benefits. They must also be informed whenever their SNAP certification period is shortened due to changes in household circumstances. 106 CMR 365.170(A) through (C) provide special instructions for handling PA households that, during their certification period, experience:
(1) a reduction in their PA benefits;
(2) termination of their PA benefits; or
(3) a change in household circumstances resulting in a change in their SNAP classification from PA to NPA. 106 CMR 365.170(D) provides special instructions for handling a change from PA to NPA status that is known to the Department at the time of a PA redetermination.
```

#### Rank 3 — RELEVANT (sim 0.516)

- **Chunk ID**: `cmr_sec_365_110__000`
- **Section**: `365.110` — Definition of a Public Assistance (PA) Household
- **Program**: SNAP
- **Judge reason**: The chunk directly defines what constitutes a Public Assistance (PA) household for SNAP purposes, listing the specific programs and conditions that qualify.

```
PA households are those households in which all members receive a cash grant under one of the following programs: Transitional Aid to Families with Dependent Children (TAFDC), or Emergency Aid to the Elderly, Disabled, and Children (EAEDC). Even though a TAFDC Full Employment Program (FEP) household may not receive a cash grant, the household will be considered a PA household. The following households will also be considered PA households:
(1) households including an SSI recipient(s) when all the other members receive cash assistance under TAFDC, or EAEDC; and
(2) households including a child(ren) born after the Family Cap Date who is not included in the TAFDC grant when all other household members receive cash assistance under TAFDC, or EAEDC.
```

#### Rank 4 — PARTIAL (sim 0.514)

- **Chunk ID**: `cmr_sec_360_030__002`
- **Section**: `360.030` — Definitions
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (4) A place not designed for or ordinarily used as a regular sleeping accommo...
- **Judge reason**: The chunk defines 'Household' for SNAP purposes but does not define what constitutes a 'Public Assistance household' specifically.

```
(4) A place not designed for or ordinarily used as a regular sleeping accommodation for people (a hallway, a bus station, a lobby or similar place). Household. Any individual or group whose income and/or assets must be used to calculate SNAP benefits levels. Household Disaster. An emergency situation declared a disaster by the President or the Federal Emergency Management Agency. Disasters are defined as, but are not limited to, floods, hurricanes, earthquakes or fires. Household Misfortune. A loss of food due to, but not limited to, loss of power, fire or flood that is not declared a disaster by the President or the Federal Emergency Management Agency. (Mass. Register #1453 10/1/21) Means-tested Program. The following are federal or state means-tested programs (i.e., income is a factor in determining eligibility): Supplemental Nutrition Assistance Program (SNAP), Transitional Assistance to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC), Emergency Assistance (EA), Supplemental Security Income (SSI), State Supplement Program (SSP) to SSI, Medicaid, State Child Health Insurance (SCHIP), Temporary Assistance for Needy Families (TANF), Food Assistance Programs in Puerto Rico, American Samoa and the Northern Mariana Islands (CNMI) and Veterans' Service benefits. Month. A cyclical month determined by the last digit of the Social Security number of the head of the household, unless otherwise specified.
```

#### Rank 5 — PARTIAL (sim 0.510)

- **Chunk ID**: `cmr_sec_365_120__004`
- **Section**: `365.120` — Determining Eligibility and Benefit Level
- **Chunk position**: 5 / 6
- **Program**: SNAP
- **Hierarchy**: (B) Asset Standards for PA Households.
- **Judge reason**: The chunk discusses income and asset standards for PA households in the context of SNAP eligibility, but does not define what a Public Assistance household actually is.

```
(B) Asset Standards for PA Households. Asset standards for PA households shall be determined as specified in 106 CMR 363.110: Asset Eligibility Limits.
(C) Income Standards For PA Households.
(1) Countable Income. All income received by the PA household, including the cash grant, special allowances and all other income (unless excluded in accordance with 106 CMR 363.230: Excluded Income) shall be counted in determining the household's eligibility for SNAP benefits.
(2) Income Exclusions and Deductions. PA households will receive only the income exclusions and deductions provided in SNAP policy. The income exclusions and deductions allowed under cash assistance programs for the purposes of grant calculation shall not be allowed in determining income for SNAP purposes.
(3) Special Allowances, Retroactive Lump Sum Payments and Protective Payments.
(a) Special Allowances. Special allowances, except for one-time payments (e.g., the clothing allowance for TAFDC children) or vendor payments, are treated as countable income. This income may be averaged over the certification period or on a variable basis of issuance to cover the period when the allowance is received.
(b) Retroactive Lump Sum PA Payments. Retroactive lump sum payments are excluded as income and counted as an asset in the month received. If a PA client's first payment is delayed beyond the first month of eligibility, the retroactive portion of that check is
```


### cmr_035 — EDP defined term (rank-1: RELEVANT)

**Question**: What is an Employment Development Plan  
**Program filter**: (none)  
**Expected section (for reference)**: `707.110` — judge picked rank-1 RELEVANT chunk in section `707.110` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — defined term/acronym. 707.110 Completion of an Employment Development Plan (EDP)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.382)

- **Chunk ID**: `cmr_sec_707_110__002`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 3 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk directly describes what an Employment Development Plan (EDP) contains and the requirements for its approval, which comprehensively answers the user's question about what an EDP is.

```
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

#### Rank 2 — PARTIAL (sim 0.361)

- **Chunk ID**: `cmr_sec_707_160__000`
- **Section**: `707.160` — Supported Work Component
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk mentions Employment Development Plan (EDP) by name and indicates it's an approved document related to work participation, but does not define what an EDP actually is or explain its contents and purpose.

```
The Supported Work Component provides education, training, employment and support services that an individual needs to obtain and maintain employment. This component consists of Pre-worksite training and Worksite placement. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP) and the criteria in 106 CMR 707.160(A)(2) and (B).
```

#### Rank 3 — PARTIAL (sim 0.359)

- **Chunk ID**: `cmr_sec_707_110__000`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 1 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk describes who must have an EDP and when it's completed, but does not define what an Employment Development Plan actually is or what it contains.

```
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

#### Rank 4 — PARTIAL (sim 0.356)

- **Chunk ID**: `cmr_sec_707_180__000`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 1 / 4
- **Program**: EA
- **Hierarchy**: (A) Activities. Activities in FEP include:
- **Judge reason**: The chunk mentions Employment Development Plan (EDP) and references where it's defined (106 CMR 707.110) but does not actually explain what an EDP is.

```
The Full Employment Program (FEP) component provides individuals work experience needed to obtain an unsubsidized job. Participants are paid a subsidized wage in lieu of receiving TAFDC.
(A) Activities. Activities in FEP include:
(1) full-time employment of 35 to 40 hours per week consistent with the employer's schedule; and
(2) completion of an Employment Development Plan (EDP) as provided in 106 CMR 707.110.
```

#### Rank 5 — PARTIAL (sim 0.349)

- **Chunk ID**: `cmr_sec_707_140__000`
- **Section**: `707.140` — Educational Component
- **Chunk position**: 1 / 5
- **Program**: EA
- **Judge reason**: The chunk mentions Employment Development Plan (EDP) by name but only describes it as something that must be 'approved' without explaining what it actually is or its purpose.

```
The Educational Component provides educational services to individuals to prepare him or her to obtain and maintain employment. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP), and the criteria in 106 CMR 707.140(A) through (D):
```


### cmr_036 — SNAP allowed uses (rank-1: RELEVANT)

**Question**: What can SNAP benefits be used to purchase  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `360.100` — judge picked rank-1 RELEVANT chunk in section `360.100` (section-author intuition agrees)  
**Notes**: 360.100 Uses of SNAP Benefits (covers chapter 360 which is otherwise underrepresented)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.567)

- **Chunk ID**: `cmr_sec_360_100__000`
- **Section**: `360.100` — Uses of SNAP Benefits
- **Program**: SNAP
- **Judge reason**: Directly states what SNAP benefits can be used to purchase (eligible foods, seeds, and plants for home consumption)

```
SNAP benefits are to be used by clients to buy eligible foods, including seeds and plants, for home consumption and use. The household may permit other persons to purchase food for the household. Such persons need not be pictured on the EBT card. Households are not required to have cooking facilities to receive SNAP.
```

#### Rank 2 — PARTIAL (sim 0.542)

- **Chunk ID**: `cmr_sec_360_030__003`
- **Section**: `360.030` — Definitions
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (4) A place not designed for or ordinarily used as a regular sleeping accommo...
- **Judge reason**: The chunk defines what SNAP benefits are but does not specify what items or categories of food can be purchased with them.

```
SNAP Benefits. Any coupon, stamp, certificate, voucher, authorization card, access device including an electronic benefit card and personal identification number, or SNAP payment in the form of cash or a check for the purchase of eligible food.
```

#### Rank 3 — PARTIAL (sim 0.533)

- **Chunk ID**: `cmr_sec_360_120__000`
- **Section**: `360.120` — Special Uses of SNAP Benefits
- **Chunk position**: 1 / 6
- **Program**: SNAP
- **Hierarchy**: (A) Communal Dining.
- **Judge reason**: Addresses only special/limited uses of SNAP benefits (communal dining) rather than the general categories of items that can be purchased with SNAP benefits.

```
Certain households have been authorized to use their SNAP benefits to buy prepared meals or to make it less difficult to obtain food. These authorized special uses of SNAP benefits are:
(A) Communal Dining.
(1) Eligible Household Members. Eligible household members 60 years of age or older or Supplemental Security Income (SSI) recipients and their spouses may use SNAP benefits to buy meals prepared especially for them at communal dining facilities authorized by the Food and Nutrition Service (FNS) for that purpose.
(2) Communal Dining Facilities. A communal dining facility is a public or nonprofit private establishment, approved by FNS, that prepares and serves meals for elderly persons, or for SSI recipients and their spouses. These facilities include senior citizen centers, apartment buildings occupied primarily by elderly persons and SSI recipients and their spouses, and federally subsidized housing for the elderly at which meals are prepared for and served to the residents.
```

#### Rank 4 — PARTIAL (sim 0.532)

- **Chunk ID**: `cmr_sec_360_120__002`
- **Section**: `360.120` — Special Uses of SNAP Benefits
- **Chunk position**: 3 / 6
- **Program**: SNAP
- **Hierarchy**: (C) Food Purchases for Residents of Drug or Alcohol Treatment and Rehabilitat...
- **Judge reason**: Addresses a specific use case for SNAP benefits (food in treatment centers) but doesn't provide the comprehensive list of what SNAP benefits can generally be used to purchase.

```
(C) Food Purchases for Residents of Drug or Alcohol Treatment and Rehabilitation Centers. Members of eligible households who are narcotic addicts or alcoholics and who regularly participate in a drug or alcoholic treatment and rehabilitation program may use SNAP benefits to purchase food provided for them during the course of such programs by an organization or institution meeting the requirements of 106 CMR 365.610: Drug and Alcohol Treatment Centers, if one of the following is true:
(1) the organization or institution is authorized by FNS to redeem SNAP benefits through wholesalers;
(2) the organization or institution redeems SNAP benefits at retail food stores as the authorized representative of participating households; or
(3) the organization or institution is authorized by FNS as a retailer.
```

#### Rank 5 — PARTIAL (sim 0.526)

- **Chunk ID**: `cmr_sec_360_120__005`
- **Section**: `360.120` — Special Uses of SNAP Benefits
- **Chunk position**: 6 / 6
- **Program**: SNAP
- **Hierarchy**: (F) Meals for Homeless Households.
- **Judge reason**: Addresses one specific use case for SNAP benefits (meals for homeless households) but doesn't provide a comprehensive answer about what SNAP benefits can generally be used to purchase.

```
(F) Meals for Homeless Households. Eligible households not living in permanent dwellings or having no fixed mailing addresses may use all or part of the SNAP benefits for meals prepared and served by a public or private nonprofit establishment (e.g., homeless meal provider, soup kitchen, temporary shelter) approved by an appropriate state or local agency to feed homeless individuals and authorized by FNS as a retail food outlet.
```


### cmr_037 — TCAP application interview (rank-1: RELEVANT)

**Question**: How do I apply for TAFDC and what happens at the application interview  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `702.120` — judge picked rank-1 RELEVANT chunk in section `702.115` (section-author intuition disagrees with judge)  
**Notes**: 702.120 The Application Interview (covers chapter 702 which is otherwise unrepresented)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.614)

- **Chunk ID**: `cmr_sec_702_115__002`
- **Section**: `702.115` — Filing of Applications
- **Chunk position**: 3 / 3
- **Program**: EA
- **Hierarchy**: (C) Application for Dependent Children.
- **Judge reason**: The chunk directly addresses the application interview process for TAFDC, including what happens within 24 hours of filing, interview scheduling, and consequences for missing interviews.

```
(C) Application for Dependent Children. The application for a dependent child must be filed by the grantee or the grantee’s authorized representative.
(D) Activities to be Completed within 24 Hours. If the worker cannot complete all parts of the application within 24 hours of filing, excluding weekends and holidays, he or she, or a Department representative shall, within 24 hours, complete the following activities:
(1) Log the case in to the Department’s system which includes recording the applicant's name, address, telephone number, and the date on which the application was filed;
(2) Ask the applicant about, and make provisions to meet, his or her immediate needs in accordance with 106 CMR 702.125;
(3) Inform the applicant of the steps that he or she must take to complete the application and of general verification requirements and have the applicant sign and date the first part of the application; and
(4) Schedule within seven calendar days any additional interviews that may be necessary to approve or deny the application within 30 calendar days.
(a) If the applicant fails to appear for the scheduled interview, the interview shall be rescheduled for the earliest possible date.
(b) If the applicant fails to appear for a second scheduled interview, the application shall be denied for failure to keep an appointment.
```

#### Rank 2 — PARTIAL (sim 0.605)

- **Chunk ID**: `cmr_sec_702_120__000`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 1 / 9
- **Program**: EA
- **Hierarchy**: (A) Completion of Interviews.
- **Judge reason**: Describes what happens during the application interview but does not explain how to apply for TAFDC or the overall application process.

```
Each determination of eligibility may include a face-to-face interview with the applicant. Application Activities
(A) Completion of Interviews. The worker is responsible for the completion of the application interview form, which is then signed by the applicant. The worker is responsible for assuring that the information recorded accurately represents what the applicant states about his or her circumstances.
```

#### Rank 3 — PARTIAL (sim 0.582)

- **Chunk ID**: `cmr_sec_702_120__006`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 7 / 9
- **Program**: EA
- **Hierarchy**: (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
- **Judge reason**: Addresses what happens during the application process (job search requirements) but does not explain how to apply or describe the application interview itself.

```
or insufficient participation in the Program by the 60th day after application, the entire case will be terminated.
(3) Under PATH, certain TAFDC applicants may also be subject to the Initial Job Search Program:
(a) Applicants who are 18 years of age or older and not provided with a Work Ready Job Diversion referral under 106 CMR 702.125(G)(3), and who will not be exempt from the Work Program (See 106 CMR 703.150: TAFDC Work Program) or have a pending request for an exemption must provide evidence of job search in the 60-day period from the date of application.
(b) Applicants subject to the Initial Job Search Program must provide evidence of three job search contacts. The frequency of reporting of such contacts will be determined by the Department.
(c) If no evidence of Initial Job Search contacts are provided prior to day 30 of the application, the TAFDC application will be denied for the grantee and any other adult subject to the requirement. If otherwise eligible, the remainder of the assistance unit will be approved. If contacts are made by day 30, and the assistance unit is otherwise found eligible for TAFDC, the entire case will be approved. If the entire case is approved but there are no further contacts or insufficient contacts made by the 60th day after application, the grantee and any other adult subject to the requirement will be terminated.
(d) Any job search under PATH done on-line must be done on a website approved by the Department.
```

#### Rank 4 — PARTIAL (sim 0.581)

- **Chunk ID**: `cmr_sec_702_115__001`
- **Section**: `702.115` — Filing of Applications
- **Chunk position**: 2 / 3
- **Program**: EA
- **Hierarchy**: (B) Definition.
- **Judge reason**: Defines what an application is and mentions an intake interview, but doesn't explain the actual application process steps or what happens during the interview itself.

```
(B) Definition. An application is a signed and dated request for assistance. The application is filed when the applicant signs and dates the prescribed forms. The application is completed by the worker during an intake interview. An application is different from an inquiry, which is simply a request for information about the TAFDC program or its eligibility requirements. An inquiry may result in an application, referral to another agency, or no further action.
```

#### Rank 5 — PARTIAL (sim 0.577)

- **Chunk ID**: `cmr_sec_702_120__005`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 6 / 9
- **Program**: EA
- **Hierarchy**: (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
- **Judge reason**: Addresses what happens during the application process (PATH participation requirements) but does not explain how to apply or describe the general application interview process.

```
(G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
(1) TAFDC applicants 18 years of age or older shall participate in an intake and employment assessment process which may result in referrals to appropriate employment or education/training opportunities. The Department shall deny applications for either the entire assistance unit or the grantee if the applicant fails to participate in PATH without good cause.
(2) Under PATH, certain TAFDC applicants may also be subject to a Work Ready Job Diversion Program:
(a) Applicants 18 years of age or older who are determined by the Department to have the necessary job skills and experience must participate in a Work Ready Job Diversion Program.
(b) Applicants will be exempted from the Work Ready Job Diversion Program if they will be exempt from the work program (See 106 CMR 703.150: TAFDC Work Program) or have requested a disability exemption (See 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits and Reduced Need and Payment Standards).
(c) Applicants subject to the Work Ready Job Diversion Program must provide evidence of three job search contacts. Applicants must accept referrals to any appropriate Department-identified jobs.
(d) If no evidence of participation in the Work Ready Job Diversion Program is provided prior to day 30 of the application, the TAFDC application for the entire assistance unit will be denied. If the case is approved but there is no further participation
```

