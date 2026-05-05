# CMR Retrieval Benchmark — hybrid-dense-weighted

**Run**: 2026-05-04T21:29:43  
**Source**: cmr  
**Label**: hybrid-dense-weighted  
**Top-N retrieved + judged**: 5  
**Embedding model**: `voyage-context-3`  
**Judge model**: `claude-haiku-4-5-20251001`  
**Methodology**: LLM-as-judge — Claude Haiku rates each chunk RELEVANT / PARTIAL / IRRELEVANT.  
**Benchmark**: CMR retrieval benchmark v2 — covers all 18 chapters, mixed difficulty, includes adversarial cases for hybrid/rerank testing  

## Summary

| Metric | Value | Notes |
|---|---|---|
| Relevance@1 | 21/37 (57%) | Did rank 1 = RELEVANT? |
| Relevant@5 (avg) | 1.54 / 5 | Avg # of RELEVANT chunks in top 5 |
| Useful@5 (avg) | 4.62 / 5 | Avg # of (RELEVANT or PARTIAL) chunks in top 5 |
| Mean rank-weighted score | 1.781 / 2.7 | Sum of (weight × score) over top 5; weights [1.0, 0.7, 0.5, 0.3, 0.2]; score RELEVANT=1.0 / PARTIAL=0.5 / IRRELEVANT=0.0 |

## Quick Summary Table

| # | ID | Topic | Rank-1 Judge | Rank-1 Sim Score | Relevant@5 | Useful@5 | RW |
|---|---|---|---|---|---|---|---|
| 1 | cmr_001 | SNAP asset limit | **PARTIAL** | 0.623 | 0 | 5 | 1.35 |
| 2 | cmr_002 | SNAP vehicle exclusion | RELEVANT | 0.571 | 1 | 3 | 1.45 |
| 3 | cmr_003 | SNAP shelter deduction | RELEVANT | 0.569 | 3 | 5 | 2.35 |
| 4 | cmr_004 | SNAP self-employment income | RELEVANT | 0.565 | 4 | 5 | 2.60 |
| 5 | cmr_005 | SNAP excluded income | RELEVANT | 0.599 | 5 | 5 | 2.70 |
| 6 | cmr_006 | SNAP ABAWD exemptions | RELEVANT | 0.599 | 1 | 5 | 1.85 |
| 7 | cmr_007 | SNAP application processing time | **PARTIAL** | 0.516 | 0 | 4 | 1.20 |
| 8 | cmr_008 | SNAP application filing | RELEVANT | 0.647 | 2 | 5 | 1.95 |
| 9 | cmr_009 | SNAP noncitizen eligibility | RELEVANT | 0.562 | 5 | 5 | 2.70 |
| 10 | cmr_010 | SNAP restoration | RELEVANT | 0.548 | 1 | 5 | 1.85 |
| 11 | cmr_011 | SNAP recertification | RELEVANT | 0.547 | 2 | 5 | 1.95 |
| 12 | cmr_012 | SNAP categorical eligibility | **PARTIAL** | 0.542 | 2 | 5 | 1.95 |
| 13 | cmr_013 | SSP eligibility | **PARTIAL** | 0.450 | 2 | 5 | 1.95 |
| 14 | cmr_014 | SSP payment standards | **PARTIAL** | 0.370 | 1 | 4 | 1.55 |
| 15 | cmr_015 | fair hearings general | RELEVANT | 0.488 | 1 | 5 | 1.85 |
| 16 | cmr_016 | hearing time limits | **PARTIAL** | 0.467 | 2 | 5 | 1.85 |
| 17 | cmr_017 | IPV definition | RELEVANT | 0.425 | 2 | 5 | 2.00 |
| 18 | cmr_018 | SNAP IPV penalties | RELEVANT | 0.568 | 2 | 5 | 2.20 |
| 19 | cmr_019 | TAFDC vs EAEDC | **PARTIAL** | 0.434 | 0 | 5 | 1.35 |
| 20 | cmr_020 | TAFDC 24-month limit | **PARTIAL** | 0.521 | 0 | 5 | 1.35 |
| 21 | cmr_021 | TAFDC work program | RELEVANT | 0.602 | 4 | 5 | 2.60 |
| 22 | cmr_022 | TAFDC asset limit | **PARTIAL** | 0.504 | 0 | 4 | 1.25 |
| 23 | cmr_023 | EAEDC disability | **PARTIAL** | 0.543 | 1 | 5 | 1.60 |
| 24 | cmr_024 | ESP overview | **PARTIAL** | 0.438 | 1 | 5 | 1.45 |
| 25 | cmr_025 | FEP overview | RELEVANT | 0.568 | 2 | 5 | 1.95 |
| 26 | cmr_026 | TAFDC MassHealth | **PARTIAL** | 0.547 | 0 | 5 | 1.35 |
| 27 | cmr_027 | TAFDC overpayments | RELEVANT | 0.476 | 1 | 5 | 1.85 |
| 28 | cmr_028 | identity verification | RELEVANT | 0.450 | 2 | 5 | 2.20 |
| 29 | cmr_029 | SNAP household composition | **PARTIAL** | 0.522 | 1 | 5 | 1.45 |
| 30 | cmr_030 | SNAP benefit calculation | RELEVANT | 0.537 | 1 | 5 | 1.85 |
| 31 | cmr_031 | section number lookup | **IRRELEVANT** | 0.187 | 0 | 0 | 0.00 |
| 32 | cmr_032 | ADH acronym | RELEVANT | 0.290 | 4 | 5 | 2.60 |
| 33 | cmr_033 | EPSDT acronym | RELEVANT | 0.503 | 1 | 1 | 1.00 |
| 34 | cmr_034 | PA household defined term | **PARTIAL** | 0.519 | 0 | 5 | 1.35 |
| 35 | cmr_035 | EDP defined term | RELEVANT | 0.418 | 1 | 5 | 1.85 |
| 36 | cmr_036 | SNAP allowed uses | RELEVANT | 0.569 | 1 | 5 | 1.85 |
| 37 | cmr_037 | TCAP application interview | **PARTIAL** | 0.620 | 1 | 5 | 1.70 |

---

## Per-Question Detail

Top 5 results per question with judge verdicts and full chunk text. Use this to spot-check whether the judge's rating makes sense.

### cmr_001 — SNAP asset limit (rank-1: PARTIAL)

**Question**: How much can a SNAP household have in bank accounts  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.110`  
**Notes**: 363.110 Asset Eligibility Limits  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.623)

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

#### Rank 2 — PARTIAL (sim 0.592)

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

#### Rank 3 — PARTIAL (sim 0.537)

- **Chunk ID**: `cmr_sec_363_130__003`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 4 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: This chunk addresses how to verify ownership and access to bank accounts but does not specify the actual dollar limit or threshold for countable assets in SNAP households.

```
106 CMR 363 > FINANCIAL > 363.130 Countable Assets > (B) Bank Accounts.

(3) Verification of Access to and Ownership of Bank Accounts. Claimed lack of access and ownership must be verified. (See Inaccessible Assets). If lack of access is verified, the funds will not be considered available to the household. If the verification submitted does not demonstrate lack of access, the case manager shall then determine ownership.
(a) Verification that a household member lacks access to and ownership of the funds may be demonstrated by the household member's having his or her name removed from the account.
(b) If the verification specified in 106 CMR 363.130(B)(3)(a) is not provided, a household member shall verify lack of ownership of all or a portion of a bank account by providing at least two of the following which demonstrate such lack of ownership:
1. Documents showing the origin of the funds, who opened the account, or whose money was used to open the account;
2. Federal or state tax records showing who declares the tax on the interest income received;
3. Records of who makes deposits and withdrawals and, if appropriate, of how withdrawn funds are spent;
4. Anyreasonable evidence of relevant written or oral agreements made between the parties listed on the account or by someone who established or contributed to the account, with respect to the ownership of the funds in the account;
5. Evidence as to why the household member is listed on the account. If the household member states that he or she does not own the account but is
```

#### Rank 4 — PARTIAL (sim 0.555)

- **Chunk ID**: `cmr_sec_363_130__004`
- **Section**: `363.130` — Countable Assets
- **Chunk position**: 5 / 10
- **Program**: SNAP
- **Hierarchy**: (B) Bank Accounts.
- **Judge reason**: The chunk discusses how to verify ownership of bank accounts for SNAP eligibility but does not specify the actual dollar limit or threshold for countable assets in bank accounts.

```
106 CMR 363 > FINANCIAL > 363.130 Countable Assets > (B) Bank Accounts.

listed as a co-holder solely as a convenience to the other co-holder to conduct bank transactions on his or her behalf, proof of the age, relationship, physical or mental condition, or place of residence of the co-holder shall also be provided;
6. A signed, notarized statement from the household member and from either one of the individuals listed in the joint account, or a person who established or contributed to the account, that the household member had no knowledge of the existence of the account; and
7. If only one of the items listed in 106 CMR 363.130(B)(3)(b)1. through 7. is available and if the other individual(s) listed on the account or who has opened or contributed to the account is unavailable, unable or unwilling to provide a statement, the household member may provide a signed statement attesting under penalties of perjury as to the ownership of funds in the account. A document or piece of evidence submitted to verify a particular fact shall not count as more than one verification under 106 CMR 363.130(B)(3)(b)1. through 7. However, a document, piece of evidence or a statement may address more than one fact needed for verification.
```

#### Rank 5 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_366_110__001`
- **Section**: `366.110` — Household Reporting Responsibilities
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) Change Reporting Requirements
- **Judge reason**: The chunk mentions that households must report when bank accounts reach or exceed the asset limit set by USDA, but does not specify what that actual limit amount is.

```
106 CMR 366 > ADDITIONAL > 366.110 Household Reporting Responsibilities > (A) Change Reporting Requirements

accounts or savings institutions that reaches or exceeds the asset limit authorized by the United States Department of Agriculture and posted on www.mass.gov/dta; and
2. For all other noncategorically eligible households, the value of cash on hand, stocks, bonds and money in bank accounts or savings institutions that reaches or exceeds the asset limit authorized by the United States Department of Agriculture and posted on www.mass.gov/dta; and
(e) Changes in the legal obligation to pay child support, including termination of the obligation when a child reaches the age at which child support is no longer legally obligated.
```


### cmr_002 — SNAP vehicle exclusion (rank-1: RELEVANT)

**Question**: What vehicles are exempt from the SNAP asset test  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.140` — judge picked rank-1 RELEVANT chunk in section `363.140` (section-author intuition agrees)  
**Notes**: 363.140 Noncountable Assets  
**Scores**: Relevant@5 = 1, Useful@5 = 3, rank-weighted = 1.45  

#### Rank 1 — RELEVANT (sim 0.571)

- **Chunk ID**: `cmr_sec_363_140__002`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 3 / 14
- **Program**: SNAP
- **Hierarchy**: (C) Education Savings Accounts.
- **Judge reason**: The chunk directly states that vehicles are noncountable assets under the SNAP asset test, which directly answers the user's question about vehicle exemptions.

```
106 CMR 363 > FINANCIAL > 363.140 Noncountable Assets > (C) Education Savings Accounts.

(C) Education Savings Accounts. Section 529 qualified tuition programs, and Coverdell education savings accounts are noncountable assets.
(D) Vehicles. Vehicles, whether licensed or unlicensed, are noncountable. Vehicles include, but are not limited to, cars, trucks, boats and tractors.
```

#### Rank 2 — PARTIAL (sim 0.477)

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

#### Rank 3 — IRRELEVANT (sim 0.446)

- **Chunk ID**: `cmr_sec_363_140__013`
- **Section**: `363.140` — Noncountable Assets
- **Chunk position**: 14 / 14
- **Program**: SNAP
- **Hierarchy**: (I) Treatment of Exempt Funds.
- **Judge reason**: This chunk addresses treatment of exempt funds in accounts, not vehicle exemptions from the SNAP asset test.

```
106 CMR 363 > FINANCIAL > 363.140 Noncountable Assets > (I) Treatment of Exempt Funds.

(I) Treatment of Exempt Funds.
(1) Exempt funds kept in a separate account shall retain their exemption for an unlimited period of time.
(2) Exempt funds that are commingled in an account with other funds shall retain their exemption for six months from the date they are commingled. After six months from the date of commingling, all funds in the commingled account shall be counted as an asset. An exception is the assets of students and self-employment assistance units exempted by 106 CMR 363.140(H)(2) which retain their exemption for the period of time their income is prorated.
```

#### Rank 4 — IRRELEVANT (sim 0.486)

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

#### Rank 5 — PARTIAL (sim 0.456)

- **Chunk ID**: `cmr_sec_363_110__000`
- **Section**: `363.110` — Asset Eligibility Limits
- **Program**: SNAP
- **Judge reason**: The chunk discusses asset eligibility limits and countable assets for SNAP but does not address vehicle exemptions specifically.

```
106 CMR 363 > FINANCIAL > 363.110 Asset Eligibility Limits

The asset eligibility limits in 106 CMR 363.110 do not apply to categorically eligible households as defined in 106 CMR 365.180: Categorically Eligible Assistance Units. These asset eligibility limits, however, shall be applied to any household with a member disqualified from receiving SNAP benefits due to failing to comply with the SNAP Work Program; or for any of the reasons listed in 106 CMR 367.800: Disqualification Penalties. Non-SSI elder and/or disabled households with income above the Categorical Eligibility Gross Income standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards shall also be subject to asset limits. The total value of countable assets owned by a household subject to asset limits shall not exceed the following:
(A) The amount authorized by the United States Department of Agriculture and posted on www.mass.gov for any household that includes at least one member who is aged 60 or over and/or disabled as described and verified in accordance with 106 CMR 361.210 (A) and (B).
(B) The amount authorized by the United States Department of Agriculture and posted on www.mass.gov for all other households. The household shall report all assets owned or anticipated to be received within the certification period. The equity value of all countable assets will be used to determine if the household is within asset eligibility limits. (Mass. Register #1522, 5/24/2024)
```


### cmr_003 — SNAP shelter deduction (rank-1: RELEVANT)

**Question**: What is the SNAP shelter deduction  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364.400` — judge picked rank-1 RELEVANT chunk in section `364.400` (section-author intuition agrees)  
**Notes**: 364.400 Shelter/Excess Shelter Deduction  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.35  

#### Rank 1 — RELEVANT (sim 0.569)

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

#### Rank 2 — RELEVANT (sim 0.560)

- **Chunk ID**: `cmr_sec_364_500__007`
- **Section**: `364.500` — Determining Net Income
- **Chunk position**: 8 / 8
- **Program**: SNAP
- **Hierarchy**: (K) Shelter Deduction.
- **Judge reason**: The chunk directly defines the SNAP shelter deduction and explains how it is calculated for different household types.

```
106 CMR 364 > DETERMINING > 364.500 Determining Net Income > (K) Shelter Deduction.

(K) Shelter Deduction. Subtract the full amount of the excess shelter expense if the household contains an elderly or disabled member who meets one of the requirements of 106 CMR 361.210: Elderly or Disabled Individuals. For all other households, subtract the excess shelter expense up to the maximum deduction amount. This shelter deduction amount is posted at www.mass.gov/dta.
```

#### Rank 3 — PARTIAL (sim 0.550)

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

#### Rank 4 — RELEVANT (sim 0.528)

- **Chunk ID**: `cmr_sec_364_400__007`
- **Section**: `364.400` — Determining Deductions
- **Chunk position**: 8 / 13
- **Program**: SNAP
- **Hierarchy**: (F) Homeless Shelter/Utility Deduction.
- **Judge reason**: The chunk directly defines and explains the SNAP homeless shelter/utility deduction, including eligibility criteria and how it differs from other shelter deductions.

```
106 CMR 364 > DETERMINING > 364.400 Determining Deductions > (F) Homeless Shelter/Utility Deduction.

(F) Homeless Shelter/Utility Deduction.
(1) Households in which all members are homeless and reside in a homeless facility, as defined by 106 CMR 360.030, that incur or reasonably expect to incur any shelter and/or utility expenses during a month shall be eligible for the homeless shelter/utility deduction. The homeless shelter/utility deduction amount is posted at www.mass.gov/dta. This amount is indexed to inflation and will be adjusted by the United States Department of Agriculture/Food and Nutrition Service (USDA/FNS).
(2) Households in which all members are homeless and reside in the home of another that incur or reasonably expect to incur any shelter and/or utility expenses during a month shall also be eligible for the homeless shelter/utility deduction. Households that receive this deduction are not entitled to either the shelter deduction provided at 106 CMR 364.400(G) or the Standard Utility Allowance provided at 106 CMR 364.400(G)(2) since the homeless shelter/utility deduction already includes both shelter and utility costs.
```

#### Rank 5 — PARTIAL (sim 0.520)

- **Chunk ID**: `cmr_sec_364_500__006`
- **Section**: `364.500` — Determining Net Income
- **Chunk position**: 7 / 8
- **Program**: SNAP
- **Hierarchy**: (J) Excess Shelter Expense.
- **Judge reason**: Explains how excess shelter expense is calculated in SNAP income determination, but doesn't define what the shelter deduction itself is or list allowable shelter expenses.

```
106 CMR 364 > DETERMINING > 364.500 Determining Net Income > (J) Excess Shelter Expense.

(J) Excess Shelter Expense. Total the allowable shelter expenses, unless a homeless shelter deduction was provided. Subtract 50% of the household's preliminary adjusted net income (monthly income after all the above deductions have been subtracted) from the total shelter expenses. The remaining amount, if any, is the excess shelter expense. If there is no excess shelter expense, the household's net monthly income has been determined. If there is excess shelter expense, go to the next step.
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
- **Judge reason**: Directly explains how monthly SNAP income is calculated for self-employed households, including the treatment of net self-employment income and farming losses.

```
106 CMR 365 > SPECIAL > 365.970 Determining Eligibility and Benefit Level for the Self-employed > (C) Determining Monthly SNAP Income. To determine the monthly SNAP income for

(C) Determining Monthly SNAP Income. To determine the monthly SNAP income for households with income from self-employment enterprises, the monthly net self-employment income is added to any other earned income, or in the case of unearned rental income to other unearned income, received by the household. If the cost of producing self-employment income of farmers exceeds the income derived from self-employment, such losses shall be offset against any other countable income in the household, provided that the farmer has received or is anticipating receiving annual gross proceeds of $1000 or more from the farming enterprise; and provided that whatever base is used to determine any net income from self-employment farm operations, such as the previous year's tax return or current income, the same base is used in determining any net loss. Losses shall be prorated over the year in a manner comparable to that used to prorate farm self-employment income. REGULATORY AUTHORITY 106 CMR 364.000: M.G.L. c. 18, § 10. (PAGES 811 THROUGH 814 ARE RESERVED FOR FUTURE USE.)
```

#### Rank 2 — RELEVANT (sim 0.549)

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

#### Rank 3 — RELEVANT (sim 0.555)

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

#### Rank 4 — RELEVANT (sim 0.533)

- **Chunk ID**: `cmr_sec_365_960__000`
- **Section**: `365.960` — Averaging Self-employment Income and Assigning Certification Periods
- **Program**: SNAP
- **Judge reason**: Directly explains how self-employment income is calculated for SNAP by describing the 12-month averaging method and circumstances for using anticipated earnings instead.

```
106 CMR 365 > SPECIAL > 365.960 Averaging Self-employment Income and Assigning Certification Periods

(A) Self-employment income that represents a household's annual support shall be averaged over a 12-month period, even if the income is received in a shorter period of time during that 12 months. For example, self-employment income received by farmers shall be averaged over a 12-month period if the income is intended to support the farmer on an annual basis. This self-employment income shall be annualized even if the household receives income from other sources in addition to self-employment. However, if the averaged annualized amount does not accurately reflect the household's actual circumstances because the household has experienced a substantial increase or decrease in business, the self-employment income shall be calculated on anticipated earnings. The worker shall not calculate self-employment income on the basis of prior income (documented by income tax returns) when the household has experienced a substantial increase or decrease in business.
```

#### Rank 5 — PARTIAL (sim 0.517)

- **Chunk ID**: `cmr_sec_365_900__000`
- **Section**: `365.900` — Households with Income from Self-employment
- **Program**: SNAP
- **Judge reason**: The chunk indicates this section covers self-employment income procedures but doesn't provide the actual calculation methodology or details needed to answer how self-employment income is calculated.

```
106 CMR 365 > SPECIAL > 365.900 Households with Income from Self-employment

The following sections describe the procedures for handling income from self-employment and for determining the eligibility and benefit level of households when all or part of their income is from self-employment.
```


### cmr_005 — SNAP excluded income (rank-1: RELEVANT)

**Question**: What income is excluded from SNAP eligibility determination  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.230` — judge picked rank-1 RELEVANT chunk in section `363.230` (section-author intuition agrees)  
**Notes**: 363.230 Noncountable Income  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.599)

- **Chunk ID**: `cmr_sec_363_230__000`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 1 / 19
- **Program**: SNAP
- **Hierarchy**: (A) In-kind Income and Cash Contributions.
- **Judge reason**: Directly addresses what income is excluded from SNAP eligibility determination by listing specific types of excluded income with examples.

```
106 CMR 363 > FINANCIAL > 363.230 Excluded Income

The following kinds of income will be excluded when determining a household's eligibility and benefit level.
(A) In-kind Income and Cash Contributions. Any gain or benefit not in the form of money and provided directly to the household is excluded from income. For example, meals, clothing, public housing, or produce from a garden would be excluded from income. Any cash contributions from a non-legally responsible person (i.e., someone without a court order or other binding agreement) that are restricted for a specific purpose and provide for a portion of any rent or mortgage, fuel, utilities and/or food or other needs are excluded from income.
```

#### Rank 2 — RELEVANT (sim 0.554)

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

#### Rank 3 — RELEVANT (sim 0.536)

- **Chunk ID**: `cmr_sec_363_230__017`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 18 / 19
- **Program**: SNAP
- **Hierarchy**: (N) Income of SSI Recipients and PASS Funds.
- **Judge reason**: Directly addresses excluded income for SNAP eligibility by explaining that PASS funds are excluded from income determination for SSI recipients.

```
106 CMR 363 > FINANCIAL > 363.230 Excluded Income > (N) Income of SSI Recipients and PASS Funds.

(N) Income of SSI Recipients and PASS Funds. Income of an SSI recipient necessary for the fulfillment of a Plan for Achieving Self Support (PASS) is excluded from income. The PASS program allows persons who receive or who might qualify to receive SSI benefits to develop a plan in which the goal is to become employed. The PASS must be approved by the Social Security Administration (SSA) to permit the individual to set aside a specified amount of money to be used or deposited into a special bank account for future use. These specified funds are to be used to achieve the work goal stated in the approved PASS and shall be excluded from income in determining SNAP eligibility and benefit level. PASS funds may include, but are not limited to, earned income or unearned income, or funds from an insurance settlement. SSI benefits are not used as PASS funds and, therefore, are still considered countable income for SNAP purposes. Exclusion of PASS funds from income for SNAP purposes is verified by a copy of the PASS agreement and the PASS approval letter from the SSA. PASS funds are not counted as assets because the assets of a household member who receives SSI are excluded for SNAP purposes, in accordance with 106 CMR 363.140(H)(7).
```

#### Rank 4 — RELEVANT (sim 0.553)

- **Chunk ID**: `cmr_sec_363_230__001`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 2 / 19
- **Program**: SNAP
- **Hierarchy**: (B) Vendor Payments.
- **Judge reason**: The chunk directly addresses excluded income for SNAP eligibility by providing specific examples of vendor payments that are excluded from income calculations.

```
106 CMR 363 > FINANCIAL > 363.230 Excluded Income > (B) Vendor Payments.

(B) Vendor Payments. A vendor payment is a money payment that is paid to a third party for a household expense. A vendor payment is excluded from income whenever a person or organization outside the household uses its own funds to make a direct payment to a household's creditors or to a person or organization providing a service to the household. The following are examples of excluded vendor payments:
(1) If a relative or friend who is not a household member pays the household's rent from his or her own funds directly to a landlord;
(2) Rent or mortgage payments made to landlords or mortgagees by the Department of Housing and Urban Development (HUD), or by state or local housing authorities on behalf of a household, including utility allowances paid under such programs;
(3) Payments made under the Emergency Assistance (EA) program;
(4) Payments for household expenses made to a third party and not legally owed to the household. The following are examples of such excluded vendor payments:
(a) If an employer pays an employee's rent directly to the landlord in addition to paying the employee his or her regular wages, the rent payment shall be considered an excluded vendor payment. If the employer provides housing to an employee, the value of the housing shall also be an excluded vendor payment:
(b) Payments specified by a court order or other legally binding agreement to go directly to the third party rather than to the household shall be considered excluded vendor payments; and
```

#### Rank 5 — RELEVANT (sim 0.534)

- **Chunk ID**: `cmr_sec_363_220__006`
- **Section**: `363.220` — Countable Income
- **Chunk position**: 7 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Garnishments, Managed Income and Certain Vendor Payments.
- **Judge reason**: The chunk directly addresses income exclusions for SNAP eligibility by listing specific payments that are not considered income and should be disregarded when determining eligibility and benefit levels.

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

#### Rank 1 — RELEVANT (sim 0.599)

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

#### Rank 2 — PARTIAL (sim 0.537)

- **Chunk ID**: `cmr_sec_362_320__003`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 4 / 9
- **Program**: SNAP
- **Hierarchy**: (C) Good Cause Criteria for ABAWD Work Program Requirements.
- **Judge reason**: Addresses good cause criteria for missing work hours rather than exemptions from the ABAWD work requirement itself.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (C) Good Cause Criteria for ABAWD Work Program Requirements.

(C) Good Cause Criteria for ABAWD Work Program Requirements. If an individual would have worked an average of 20 hours per week but missed hours due to good cause, the individual shall be considered to have met the work requirement if the absence from work is temporary and the individual retains his or her job. Good cause shall include circumstances beyond the individual's control, such as, but not limited to, illness, illness of another household member requiring the presence of the member, a household emergency, or the unavailability of transportation.
```

#### Rank 3 — PARTIAL (sim 0.506)

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

#### Rank 4 — PARTIAL (sim 0.529)

- **Chunk ID**: `cmr_sec_362_310__002`
- **Section**: `362.310` — General SNAP Work Requirements
- **Chunk position**: 3 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Exemptions from General SNAP Work Requirements.
- **Judge reason**: Addresses general SNAP work requirement exemptions but not specifically ABAWD (Able-Bodied Adults Without Dependents) exemptions, which are a distinct category with different rules.

```
106 CMR 362 > NONFINANCIAL > 362.310 General SNAP Work Requirements > (C) Exemptions from General SNAP Work Requirements.

(C) Exemptions from General SNAP Work Requirements. The individuals listed in 106 CMR 362.310(C)(1) through (10) are exempt from the general SNAP work requirements found at 106 CMR 362.310(A). If verification is necessary for a particular exemption, it is noted under that exemption.
(1) Age. A person younger than 16 years old or a person 60 years of age or older is exempt. A child who has his or her 16th birthday within a certification period shall fulfill the work registration requirement at the next scheduled recertification, unless the child qualifies for another exemption.
(2) Persons Physically or Mentally Unfit for Employment. Persons who are physically or mentally unfit for employment due to disability or illness, either permanently or temporarily, are exempt. If the disability or illness is not obvious, appropriate verification of physical or mental unfitness must be provided. Verification includes, but is not limited to:
(a) receipt of temporary or permanent disability benefits from a government or private source;
(b) a written, dated and signed statement from a competent medical authority stating that the person is physically or mentally unfit for employment;
(c) participation in a Massachusetts Rehabilitation Commission program or other Massachusetts-approved vocational rehabilitation program; and
(d) proof that the individual is temporarily ill and that the illness is serious enough to temporarily prevent employment.
```

#### Rank 5 — PARTIAL (sim 0.530)

- **Chunk ID**: `cmr_sec_362_310__003`
- **Section**: `362.310` — General SNAP Work Requirements
- **Chunk position**: 4 / 7
- **Program**: SNAP
- **Hierarchy**: (C) Exemptions from General SNAP Work Requirements.
- **Judge reason**: The chunk addresses SNAP work requirement exemptions generally, but ABAWD (Able-Bodied Adults Without Dependents) is a specific SNAP category and this text does not specifically address ABAWD exemptions.

```
106 CMR 362 > NONFINANCIAL > 362.310 General SNAP Work Requirements > (C) Exemptions from General SNAP Work Requirements.

Persons claiming temporary unfitness for employment due to illness will be required to meet work requirements once they become physically or mentally fit.
(3) TAFDC/EAEDC Work Program Participants. A TAFDC or EAEDC client subject to and complying with the relevant program's work requirement is exempt.
(4) Unemployment Compensation Applicants and Recipients. Unemployment Compensation applicants or recipients subject to and participating in a comparable unemployment compensation work program are exempt. If the exemption claimed is questionable, the Department is responsible for verifying the exemption with the office of the State employment services agency.
(5) Caretakers. A parent or other household member responsible for the care of a dependent child under six or an incapacitated person is exempt. If the child has his or her sixth birthday within a certification period, the caregiver of the child shall fulfill the work requirements at the next scheduled recertification, unless the caregiver qualifies for another exemption. If a parent and another member of the household both claim to be responsible for the care of the same dependent child or incapacitated household member, the actual responsibility shall be determined by discussion with the applicant or client.
```


### cmr_007 — SNAP application processing time (rank-1: PARTIAL)

**Question**: How long does DTA have to process a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.080`  
**Notes**: 361.080 Prompt Action; baseline v1 expected 361 broadly, this v2 narrows it  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.20  

#### Rank 1 — PARTIAL (sim 0.516)

- **Chunk ID**: `cmr_sec_361_130__000`
- **Section**: `361.130` — Household Right to Same Day Filing
- **Program**: SNAP
- **Judge reason**: Addresses application filing procedures and same-day filing rights but does not specify the timeframe for DTA to process a completed SNAP application.

```
106 CMR 361 > THE > 361.130 Household Right to Same Day Filing

Households shall be advised of their right to same day filing of the application. Each office shall post signs that explain the application processing standards and the household's right to same day filing. In addition, the household shall be informed that it does not have to be interviewed before filing its application and that it may file an incomplete application as long as the form contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. Department staff shall encourage households to file an application the same day the household or its representative contacts the Department in person or by telephone and expresses an interest in obtaining SNAP benefits.
```

#### Rank 2 — PARTIAL (sim 0.524)

- **Chunk ID**: `cmr_sec_361_120__000`
- **Section**: `361.120` — Date of Application
- **Program**: SNAP
- **Judge reason**: This chunk defines when an application date is established but does not address the processing timeline or how long DTA takes to process the application.

```
106 CMR 361 > THE > 361.120 Date of Application

For households consisting only of SSI applicants or recipients that apply for SNAP benefits at an SSA office, the household's date of application is the date the signed SNAP application is received by the SSA office. The SSA office shall date stamp each application on the date it is received to document the household's date of application. For all other households, the household's date of application is the date an identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office, except that when an application is not received by 5:00 P.M. on a business day or is received on a weekend or holiday, the application date will be the next business day. The Department shall date stamp each application on the date it is received to document the household's date of application.
```

#### Rank 3 — PARTIAL (sim 0.500)

- **Chunk ID**: `cmr_sec_366_920__001`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) Filing an Application.
- **Judge reason**: The chunk defines when an application date is established but does not address the processing timeline or how long DTA has to process the application.

```
106 CMR 366 > ADDITIONAL > 366.920 Regular SSI/SNAP Households > (A) Filing an Application.

(A) Filing an Application. Assistance in completing SNAP applications will be available at SSA or the Department.
(B) Date of Application. If the application is filed at an SSA office, then the date of application shall be the date the identifiable SNAP application is faxed by SSA to the appropriate Transitional Assistance Office (TAO). If an application is filed at a TAO or online, the date of application shall be the date the identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office. (See 106 CMR 361.120: Date of Application.)
```

#### Rank 4 — IRRELEVANT (sim 0.487)

- **Chunk ID**: `cmr_sec_361_140__000`
- **Section**: `361.140` — Mailing Applications to Households
- **Program**: SNAP
- **Judge reason**: This chunk addresses the process of mailing applications to households, not the timeline for DTA to process a submitted SNAP application.

```
106 CMR 361 > THE > 361.140 Mailing Applications to Households

If the household has contacts the Department by telephone but does not wish to come to a local office to file an application that same day and instead prefers receiving an application through the mail rather than applying online, the Department shall mail the application form to the household on the same day as the telephone request. If a household makes a written request for SNAP assistance, the Department shall mail the application form to the household on the same day as the written request for SNAP assistance is received.
```

#### Rank 5 — PARTIAL (sim 0.483)

- **Chunk ID**: `cmr_sec_365_120__003`
- **Section**: `365.120` — Determining Eligibility and Benefit Level
- **Chunk position**: 4 / 6
- **Program**: SNAP
- **Hierarchy**: (A) PA households shall be allowed to apply for SNAP benefits at the same tim...
- **Judge reason**: The chunk references timeliness standards in 106 CMR 361.700-361.960 but does not specify the actual processing timeframe; it only describes procedures for determining eligibility.

```
106 CMR 365 > SPECIAL > 365.120 Determining Eligibility and Benefit Level > (A) PA households shall be allowed to apply for SNAP benefits at the same tim...

(4) Timeliness Standard. The worker must make the SNAP eligibility determination in accordance with all the timeliness standards and procedures specified in 106 CMR 361.700 through 361.960, unless the household has failed to provide verification of an eligibility factor required for both cash assistance and SNAP benefits in accordance with 106 CMR 365.120(A)(3)(b).
(a) As a result of differences in application processing procedures and standards, the worker may have to determine SNAP eligibility prior to determining eligibility for PA payments. Action on the SNAP portion of the application shall not be delayed nor the application denied on grounds that the PA determination has not been made.
(b) Households whose PA applications are denied but who have provided all verifications necessary to determine SNAP eligibility shall not be required to file a new SNAP application. They shall, however, have their SNAP eligibility determined or continued on the basis of their original joint application and any other documented information obtained subsequent to the application that may have been used in the PA determination and that is relevant to SNAP eligibility or level of benefits.
```


### cmr_008 — SNAP application filing (rank-1: RELEVANT)

**Question**: How does someone file a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.100` — judge picked rank-1 RELEVANT chunk in section `361.110` (section-author intuition disagrees with judge)  
**Notes**: 361.100 Filing an Application  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — RELEVANT (sim 0.647)

- **Chunk ID**: `cmr_sec_361_110__000`
- **Section**: `361.110` — Where to File
- **Program**: SNAP
- **Judge reason**: Directly addresses where and how to file a SNAP application, including the various methods available (in person, mail, fax, online).

```
106 CMR 361 > THE > 361.110 Where to File

The application must be filed with the Department and may be submitted in person by the applicant, or by an authorized representative, or by mail, fax or the online application. Households consisting only of SSI applicants or recipients may file a SNAP application at an SSA office in accordance with 106 CMR 361.190.
```

#### Rank 2 — PARTIAL (sim 0.620)

- **Chunk ID**: `cmr_sec_361_130__000`
- **Section**: `361.130` — Household Right to Same Day Filing
- **Program**: SNAP
- **Judge reason**: Addresses same-day filing rights and requirements but doesn't explain the actual process or steps for filing a SNAP application.

```
106 CMR 361 > THE > 361.130 Household Right to Same Day Filing

Households shall be advised of their right to same day filing of the application. Each office shall post signs that explain the application processing standards and the household's right to same day filing. In addition, the household shall be informed that it does not have to be interviewed before filing its application and that it may file an incomplete application as long as the form contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. Department staff shall encourage households to file an application the same day the household or its representative contacts the Department in person or by telephone and expresses an interest in obtaining SNAP benefits.
```

#### Rank 3 — PARTIAL (sim 0.615)

- **Chunk ID**: `cmr_sec_361_140__000`
- **Section**: `361.140` — Mailing Applications to Households
- **Program**: SNAP
- **Judge reason**: Describes one method of obtaining a SNAP application (by mail) but doesn't comprehensively explain all ways to file an application or the actual filing process itself.

```
106 CMR 361 > THE > 361.140 Mailing Applications to Households

If the household has contacts the Department by telephone but does not wish to come to a local office to file an application that same day and instead prefers receiving an application through the mail rather than applying online, the Department shall mail the application form to the household on the same day as the telephone request. If a household makes a written request for SNAP assistance, the Department shall mail the application form to the household on the same day as the written request for SNAP assistance is received.
```

#### Rank 4 — PARTIAL (sim 0.579)

- **Chunk ID**: `cmr_sec_361_190__000`
- **Section**: `361.190` — Handling Applications of SSI Households
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: Describes one specific way SSI households can file SNAP applications (at SSA offices) but doesn't comprehensively explain how someone generally files a SNAP application through DTA.

```
106 CMR 361 > THE > 361.190 Handling Applications of SSI Households

Households of only SSI applicants or recipients may, if they choose, apply for SNAP benefits at a Social Security Administration (SSA) office. SSA shall handle applications of SSI households that have not applied for SNAP benefits in the previous 30 days and that do not have SNAP applications pending. SSA shall inform SSI applicants and recipients of the availability of benefits under the SNAP and the availability of a SNAP application at SSA offices whenever SSI applicants or recipients conduct business at an SSA office. An SSA office is not required to accept SNAP applications or to conduct interviews for SSI applicants or recipients who are not members of households in which all members are SSI applicants or recipients. SSA shall refer non-SSI households to the Department. SSA shall accept and complete SNAP applications filed at the SSA office by SSI households and shall forward them to the Department within one working day after receipt of the signed applications. On a form attached to the application, SSA will indicate required verifications that are on file at the SSA office. Items verified and on file at the SSA office are considered verified for SNAP purposes. An application shall be considered filed for normal processing standards on the date the identifiable application is received by the SSA office. For expedited service, processing time standards begin the date the Department receives the application. SNAP eligibility shall be based solely on SNAP eligibility criteria.
```

#### Rank 5 — RELEVANT (sim 0.563)

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

#### Rank 1 — RELEVANT (sim 0.562)

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

#### Rank 2 — RELEVANT (sim 0.560)

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

#### Rank 3 — RELEVANT (sim 0.560)

- **Chunk ID**: `cmr_sec_362_220__003`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 4 / 12
- **Program**: SNAP
- **Hierarchy**: (B) To receive SNAP benefits the qualified noncitizen must meet the condition...
- **Judge reason**: The chunk directly addresses which noncitizens can receive SNAP benefits by listing specific eligible noncitizen categories and their qualifying conditions.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (B) To receive SNAP benefits the qualified noncitizen must meet the condition...

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

#### Rank 4 — RELEVANT (sim 0.544)

- **Chunk ID**: `cmr_sec_362_220__000`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 1 / 12
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses whether noncitizens can receive SNAP benefits by explaining the eligibility requirements, verification procedures, and conditions under which noncitizens may or may not qualify.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens

A noncitizen applying for SNAP benefits and claiming an eligible noncitizen status must verify that he or she is present in the United States (U.S.) under one of the noncitizen statuses provided in 106 CMR 362.220(A). The status of a noncitizen must be verified at certification, at recertification or whenever the status of the noncitizen changes or is questionable. Verification of an eligible noncitizen status must be presented before the determination of SNAP eligibility. When a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide information about, or acceptable verification of, his or her eligible noncitizen status, that household member shall be ineligible. In such cases the Department shall not continue efforts to obtain documentation. Also, if a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide, or apply for, a Social Security Number due to immigration status he or she is ineligible. The Department shall not continue efforts to obtain documentation. SNAP eligibility will be determined in accordance with 106 CMR 365.520(A) for the household members who do verify an eligible noncitizen status. The Commissioner or designee is required to report to the United States Citizenship and Immigration Services (USCIS) information about noncitizens "known to be in the U.S. unlawfully" as defined in 106 CMR 362.240. SNAP - Eligible Noncitizen Status. A noncitizen's eligibility for SNAP benefits depends on
```

#### Rank 5 — RELEVANT (sim 0.545)

- **Chunk ID**: `cmr_sec_362_220__006`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 7 / 12
- **Program**: SNAP
- **Hierarchy**: (B) To receive SNAP benefits the qualified noncitizen must meet the condition...
- **Judge reason**: The chunk directly addresses which noncitizens can receive SNAP benefits by specifying eligible noncitizen categories and their qualifying conditions.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (B) To receive SNAP benefits the qualified noncitizen must meet the condition...

4. is disabled as defined by 106 CMR 361.210: Elderly or Disabled Individuals; or
5. is a veteran or active duty personnel as defined by 106 CMR 362.240(F).
(9) Parolee. A noncitizen present in the U.S. as a parolee under section 212(d)(5) of the INA for at least one year is an eligible noncitizen when he or she:
(a) has resided as a qualified noncitizen in the U.S. for five years;
(b) was born on or before August 22, 1931 and was lawfully residing in the U.S. on August 22, 1996;
(c) is a child younger than 18 years old;
(d) is disabled as defined by 106 CMR 361.210: Elderly or Disabled Individuals; or
(e) is a veteran or active duty personnel as defined in 106 CMR 361.240(F).
(10) Conditional Entrant. A noncitizen present in the U.S. as a conditional entrant under section 203(a)(7) of the INA is an eligible noncitizen when he or she:
(a) has resided as a qualified noncitizen in the U.S. for five years;
(b) was born on or before August 22, 1931 and was lawfully residing in the U.S. on August 22, 1996;
(c) is a child younger than 18 years old;
(d) is disabled as defined by 106 CMR 361.210: Elderly or Disabled Individuals; or
(e) is a veteran or active duty personnel as defined by 106 CMR 362.240(F).
```


### cmr_010 — SNAP restoration (rank-1: RELEVANT)

**Question**: When are SNAP benefits restored after an agency error  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366` — judge picked rank-1 RELEVANT chunk in section `366.520` (section-author intuition agrees)  
**Notes**: BROAD — chapter 366 covers changes/restoration; specific section may be 366.500  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.548)

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

#### Rank 2 — PARTIAL (sim 0.543)

- **Chunk ID**: `cmr_sec_366_510__000`
- **Section**: `366.510` — Entitlement for Benefits Including Underpayments
- **Program**: SNAP
- **Judge reason**: The chunk explains what types of benefits are restored due to agency error but does not specify the timeline or when (how quickly) those benefits are restored.

```
106 CMR 366 > ADDITIONAL > 366.510 Entitlement for Benefits Including Underpayments

A household is entitled to lost benefits only for those months the household was eligible to participate. In cases where there is no information in the household's case record to document that the household was actually eligible, the Department shall advise the household of what information must be provided to determine eligibility for these months. For each month that the household cannot provide the necessary information to demonstrate its eligibility, the household shall be considered ineligible for restoration of lost benefits. The Department shall restore to the household benefits that were lost because of:
(A) an agency error, such as an incorrect allotment, an incorrect denial or termination of benefits, agency delay in acting on a reported change, or failure to provide benefits for the month following the expiration of the certification period for households properly fulfilling the recertification process;
(B) a fraud disqualification penalty of a household member that is later reversed; and
(C) an error by the Department or by SSA through joint application processing. Such an error shall include, but is not limited to, the loss of an applicant's SNAP application after it has been filed with SSA. Households are also entitled to lost benefits if a Department policy specifically provides for restoration of lost benefits. NON-TEXT PAGE
```

#### Rank 3 — PARTIAL (sim 0.533)

- **Chunk ID**: `cmr_sec_366_520__000`
- **Section**: `366.520` — Computing the Amount to be Restored
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Hierarchy**: (A) Months of Restoration.
- **Judge reason**: Addresses the timeframe for restoration (12 months) but does not specifically explain when restoration occurs after an agency error or the conditions that trigger it.

```
106 CMR 366 > ADDITIONAL > 366.520 Computing the Amount to be Restored

(A) Months of Restoration. Except when benefits are restored as the result of the reversal of a fraud disqualification penalty, benefits shall be restored for not more than 12 months prior to whichever of the following occurred first:
(1) the month the household or another person or agency notified the Department verbally or in writing of the possible loss of benefits;
(2) the month the Department discovered that a loss has occurred; or
(3) the date the household requested a fair hearing to contest the adverse action that resulted in the loss.
```

#### Rank 4 — PARTIAL (sim 0.508)

- **Chunk ID**: `cmr_sec_366_560__000`
- **Section**: `366.560` — Individuals Disqualified for an Intentional Program Violation
- **Program**: SNAP
- **Judge reason**: Addresses benefit restoration but only for intentional program violations, not for agency errors as the question asks

```
106 CMR 366 > ADDITIONAL > 366.560 Individuals Disqualified for an Intentional Program Violation

Individuals disqualified for an intentional program violation are entitled to restoration of any benefits lost during the months they were disqualified only if the decision to disqualify is subsequently reversed. For each month the individual was disqualified, the amount to be restored, if any, shall be determined by comparing the allotment the household received with the allotment the household would have received had the disqualified member been allowed to participate. Benefits shall be restored regardless of the length of time that has elapsed since the household member was disqualified.
```

#### Rank 5 — PARTIAL (sim 0.479)

- **Chunk ID**: `cmr_sec_366_550__000`
- **Section**: `366.550` — Offsetting Claims
- **Program**: SNAP
- **Judge reason**: Addresses restoration of benefits but focuses on offsetting claims rather than the timeline for restoration after agency error.

```
106 CMR 366 > ADDITIONAL > 366.550 Offsetting Claims

If a claim against a household is unpaid, held in suspense or terminated, the amount to be restored shall be offset against the amount due on the claim before the balance is restored to the household. Offsetting shall not occur when a household is certified and receiving an initial allotment, even if the initial allotment is issued retroactively.
```


### cmr_011 — SNAP recertification (rank-1: RELEVANT)

**Question**: What are the SNAP recertification requirements  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366` — judge picked rank-1 RELEVANT chunk in section `366.300` (section-author intuition agrees)  
**Notes**: BROAD — chapter 366 generally; could pull from 365.150 for PA households  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — RELEVANT (sim 0.547)

- **Chunk ID**: `cmr_sec_366_300__000`
- **Section**: `366.300` — Recertification
- **Program**: SNAP
- **Judge reason**: Directly addresses SNAP recertification requirements by outlining the core requirements: submitting a new application, being interviewed, and providing required verification.

```
106 CMR 366 > ADDITIONAL > 366.300 Recertification

A household's SNAP benefits shall not continue beyond the certification period, unless the household has been recertified. To recertify, the household must submit a new application, be interviewed, and provide required verification in accordance with the timeliness standards set forth in 106 CMR 366.320. Those households that timely recertify and are found eligible shall be entitled to uninterrupted benefits. The following sections list the responsibilities of the household and the Department in the recertification process.
```

#### Rank 2 — PARTIAL (sim 0.538)

- **Chunk ID**: `cmr_sec_365_150__000`
- **Section**: `365.150` — Recertification Requirements for PA Households
- **Program**: SNAP
- **Judge reason**: Addresses recertification timing for PA households specifically but doesn't comprehensively cover general SNAP recertification requirements for all household types.

```
106 CMR 365 > SPECIAL > 365.150 Recertification Requirements for PA Households

PA households shall be recertified for SNAP benefits, to the extent possible, at the same time they have their eligibility reviewed for the cash assistance program. If a PA household has not had its PA eligibility reviewed by the end of the 11th month following its initial SNAP certification or last eligibility review, a Notice of SNAP Termination shall be sent to the household.
```

#### Rank 3 — PARTIAL (sim 0.537)

- **Chunk ID**: `cmr_sec_366_310__000`
- **Section**: `366.310` — Notification to Recertify
- **Program**: SNAP
- **Judge reason**: The chunk addresses notification procedures for recertification rather than the actual recertification requirements themselves (eligibility criteria, documentation needed, frequency, etc.).

```
106 CMR 366 > ADDITIONAL > 366.310 Notification to Recertify

Households certified for one or two months shall receive, at the time of certification, a separate notice of recertification responsibilities entitled Notice of Expiration. Those households certified for three months or more (except public assistance households) shall receive a separate Notice of Expiration in the month prior to the last month of their certification period. This notice will be mailed by the Department no earlier than the first day of the next-to-last month of certification or no later than the last day of the next-to-last month of certification. The contents of the notice are set forth in 106 CMR 364.840: Notice of SNAP Termination. Public assistance households shall receive a notice of recertification responsibilities prior to the end of the SNAP certification period. In some instances, these households are recertified for SNAP at the same time as their public assistance redetermination.
```

#### Rank 4 — PARTIAL (sim 0.525)

- **Chunk ID**: `cmr_sec_365_630__002`
- **Section**: `365.630` — Certification of Residents of Group Living Arrangements and Treatment Centers
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (C) Recertification and Changes During the Certification Period.
- **Judge reason**: Mentions recertification requirements but only for a specific subgroup (group living arrangements/treatment centers) and refers to general standards without detailing what those standards actually are.

```
106 CMR 365 > SPECIAL > 365.630 Certification of Residents of Group Living Arrangements and Treatment Centers > (C) Recertification and Changes During the Certification Period.

(C) Recertification and Changes During the Certification Period. The case manager shall recertify these residents and process changes in household circumstances using the same standards that apply to all other SNAP households.
```

#### Rank 5 — RELEVANT (sim 0.531)

- **Chunk ID**: `cmr_sec_366_320__002`
- **Section**: `366.320` — Household Responsibilities
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (C) Providing Verification.
- **Judge reason**: Directly addresses SNAP recertification verification requirements, including income verification procedures and timelines for submitting documentation.

```
106 CMR 366 > ADDITIONAL > 366.320 Household Responsibilities > (C) Providing Verification.

(C) Providing Verification. The following verification requirements shall be met at recertification. (See 106 CMR 365.180: Categorically Eligible Assistance Units for verification factors that are deemed for categorically eligible households.) Additional verification is not required unless the information provided is questionable. Time frames (at least ten calendar days from the date of the Department's initial request) may be established within which the household must submit any required verification requested to ensure its rights to uninterrupted benefits.
(1) Gross Countable Income. The amount of the household's gross countable monthly income, as defined in 106 CMR 363.200: Income, shall be verified prior to recertification. If all attempts to verify the gross countable income are unsuccessful because a third-party has failed to cooperate, the Department shall determine the household's gross countable monthly income based on the best available information. Noncountable income shall be verified only if the information provided by the household is questionable.
```


### cmr_012 — SNAP categorical eligibility (rank-1: PARTIAL)

**Question**: What is SNAP categorical eligibility  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365`  
**Notes**: BROAD — chapter 365 special households; 365.180 in v1  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — PARTIAL (sim 0.542)

- **Chunk ID**: `cmr_sec_364_976__000`
- **Section**: `364.976` — Gross Monthly Categorical Eligibility Income Standards
- **Program**: SNAP
- **Judge reason**: The chunk discusses categorical eligibility income standards and references where to find details, but does not explain what categorical eligibility actually is or its definition.

```
106 CMR 364 > DETERMINING > 364.976 Gross Monthly Categorical Eligibility Income Standards

The Gross Monthly Categorical Eligibility Standards are based on household size and are adjusted annually based on the federal poverty level. These standards are posted at www.mass.gov/dta. For more details on determining categorical eligibility, see 106 CMR 365.180: Categorically Eligible Assistance Units.
```

#### Rank 2 — RELEVANT (sim 0.543)

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

#### Rank 3 — RELEVANT (sim 0.520)

- **Chunk ID**: `cmr_sec_365_180__001`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk directly defines SNAP categorical eligibility by listing specific categories of households that qualify (SNAP-only TANF Service Elder/Disabled Households and SNAP-only TANF Service Adult Households) and their requirements.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (A) The following SNAP households are categorically eligible:

(5) SNAP-only TANF Service Elder/Disabled Households which include SNAP households consisting solely of non-SSI elders (60 years of age or older) and/or disabled individuals in accordance with SNAP disability standards at 106 CMR 361.210: Elderly or Disabled Individuals. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards; and
(6) SNAP-only TANF Service Adult Households include SNAP households consisting solely of adults between 19 and 59 years of age. These households must meet the Gross Monthly Categorically Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards. For purposes of 106 CMR 365.180(A)(1) through (3), authorized to receive means that an individual has been determined eligible for benefits and has been notified of this determination, even if benefits have been authorized but not received, authorized but not accessed, suspended or recouped, or not paid because they are less than a minimum amount. For purposes of 106 CMR 365.180(A)(4) through (6), a TANF Service includes receipt of the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure.
```

#### Rank 4 — PARTIAL (sim 0.503)

- **Chunk ID**: `cmr_sec_364_950__000`
- **Section**: `364.950` — Maximum Gross Monthly Income Standards
- **Program**: SNAP
- **Judge reason**: The chunk mentions categorical eligibility and references where to find details, but does not actually explain what SNAP categorical eligibility is or how it works.

```
106 CMR 364 > DETERMINING > 364.950 Maximum Gross Monthly Income Standards

The Maximum Gross Monthly Income Standards are based on household size and are adjusted annually by USDA/FNS. These standards are posted at www.mass.gov/dta. For more details on determining eligibility based on gross income, see 106 CMR 364.370. Public Assistance categorically eligible households do not have to meet the gross income eligibility standards. SNAP-only TANF Services Households are subject to the Gross Monthly Categorical Eligibility Standards at 106 CMR 364.976.
```

#### Rank 5 — PARTIAL (sim 0.497)

- **Chunk ID**: `cmr_sec_362_270__000`
- **Section**: `362.270` — Deeming of Income and Assets for Sponsored Noncitizens
- **Chunk position**: 1 / 13
- **Program**: SNAP
- **Judge reason**: The chunk references categorical eligibility and mentions a definition at 106 CMR 365.180, but does not actually explain what SNAP categorical eligibility is—it only discusses how deeming rules apply differently to categorically eligible households.

```
106 CMR 362 > NONFINANCIAL > 362.270 Deeming of Income and Assets for Sponsored Noncitizens

The deeming of income and assets rules for sponsored noncitizens do not apply to categorically eligible households as defined in 106 CMR 365.180: Categorically Eligible Assistance Units. The deeming of income and assets rules for sponsored noncitizens will be applied to any household which contains a member disqualified from receiving SNAP benefits due to: a failure to comply with the ABAWD Work Program at 106 CMR 362.320; a failure to comply with TAFDC Income Reporting requirements at 106 CMR 366.110: Household Reporting Responsibilities; or any of the reasons listed in 106 CMR 367.800: Disqualification Penalties. In addition, non-SSI elder and/or disabled households with income, not including the income of the sponsor(s), that exceeds the Categorical Eligibility Gross Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards will be subject to sponsor deeming requirements.
```


### cmr_013 — SSP eligibility (rank-1: PARTIAL)

**Question**: What is the State Supplement Program and who is eligible  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.120`  
**Notes**: 327.120 Eligibility for State Supplement Program  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — PARTIAL (sim 0.450)

- **Chunk ID**: `cmr_sec_327_010__000`
- **Section**: `327.010` — Authority for State Supplement Program
- **Program**: SSP
- **Judge reason**: Explains what SSP is and that Massachusetts offers it, but does not provide eligibility criteria details

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.010 Authority for State Supplement Program

The Supplemental Security Income (SSI) program is administered by the Social Security Administration (SSA) to provide financial assistance to eligible aged, disabled and blind individuals. States have the option to provide additional assistance through the State Supplement Program (SSP). Massachusetts has opted to provide this additional assistance. SSP is authorized under M.G.L. c. 6, § 131 and M.G.L. c. 118A and applicable federal law pertaining to the SSI program and agreements with the Commissioner of Social Security. 106 CMR 327.000 is promulgated and implemented in accordance with M.G.L. c. 30A, and applicable General Laws of Massachusetts.
```

#### Rank 2 — RELEVANT (sim 0.449)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly defines the State Supplement Program and clearly states who is eligible (individuals who receive SSI or don't qualify for SSI due to income), directly answering both parts of the user's question.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.100 Overview of State Supplement Program

SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 3 — RELEVANT (sim 0.439)

- **Chunk ID**: `cmr_sec_327_120__000`
- **Section**: `327.120` — Eligibility for State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly defines the State Supplement Program and specifies the two eligibility categories for SSP, directly answering both parts of the user's question.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.120 Eligibility for State Supplement Program

An application for SSI serves is an application for SSP. There is no separate SSP application. Eligibility for SSP is determined after an eligibility determination for SSI is made by the Social Security Administration (SSA). The Department must accept the SSA determination. Individuals may be eligible for SSP if they are either:
(A) determined eligible for SSI; or
(B) determined not eligible for SSI solely due to income, but their countable income is less than the combined Federal Benefit Rate (FBR) and the appropriate SSP payment.
```

#### Rank 4 — PARTIAL (sim 0.410)

- **Chunk ID**: `cmr_sec_327_110__000`
- **Section**: `327.110` — Definitions
- **Program**: SSP
- **Judge reason**: The chunk provides definitions related to SSP eligibility but does not explain what the State Supplement Program is or clearly state who is eligible for it.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.110 Definitions

The following words and terms, when used in 106 CMR 327.000, have the following meanings, unless the context otherwise requires. (Mass. Register #1390 5/3/19) Child. For SSP purposes, is one who meets the SSI definition of child. Countable Income. As defined in 20 CFR 416.1104. Eligible Individual. An aged, disabled or blind individual who meets all SSI eligibility requirements. See 20 CFR 416.120. Eligible Couple. An eligible individual and his or her eligible spouse who are living in the same household. See 20 CFR 416.1801. Federal Benefit Rate (FBR). As defined in 20 CFR 416.1101. Public Income Maintenance Payment. A payment from any of the following programs: SSI, TAFDC, Refugee Act of 1980, Disaster Relief Act of 1974, Veterans Administration benefits based on need, or any State or local governmental assistance program based on need. Representative Payee. As defined in 20 CFR 416.601. Resources. As defined in 20 CFR 416.1201, et seq. Supplemental Security Income (SSI). As defined in 20 CFR 416.101. SSP-only. A designation for a client who is ineligible for SSI solely based on his or her income but is eligible to receive SSP benefits.
```

#### Rank 5 — PARTIAL (sim 0.375)

- **Chunk ID**: `cmr_sec_327_330__000`
- **Section**: `327.330` — Payment Standards
- **Program**: SSP
- **Judge reason**: Addresses SSP payment standards and amounts but does not explain what the State Supplement Program is or who is eligible for it.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.330 Payment Standards

Payment amounts are based on Eligibility Category, State Living Arrangement, whether the client is eligible as an individual or as a member of an eligible couple and the amount of countable income. If countable income exceeds the Federal Benefit Rate (FBR), the amount exceeding the FBR is deducted from the SSP payment standard. Payment standards are available online at www.mass.gov/dta under the heading Key Resources/Program Eligibility Charts and Tables/SSI Program Payment Charts. Paper copies are available upon request.
```


### cmr_014 — SSP payment standards (rank-1: PARTIAL)

**Question**: What are the SSP payment standards  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.330`  
**Notes**: 327.330 Payment Standards  
**Scores**: Relevant@5 = 1, Useful@5 = 4, rank-weighted = 1.55  

#### Rank 1 — PARTIAL (sim 0.370)

- **Chunk ID**: `cmr_sec_327_350__000`
- **Section**: `327.350` — Timing and Method of SSP Benefit Payments
- **Program**: SSP
- **Judge reason**: Addresses payment timing and minimum amounts but does not provide the actual SSP payment standards/benefit amounts that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.350 Timing and Method of SSP Benefit Payments

SSP benefits are paid once a month. The Department shall determine the method of payment. Minimum Monthly Payment The minimum monthly payment for the SSP is $1.00. If the payment amount is greater than zero but less than $1.00, a payment of $1.00 will be issued.
```

#### Rank 2 — RELEVANT (sim 0.369)

- **Chunk ID**: `cmr_sec_327_330__000`
- **Section**: `327.330` — Payment Standards
- **Program**: SSP
- **Judge reason**: The chunk directly addresses SSP payment standards by explaining how they are determined and where to find the specific payment amounts.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.330 Payment Standards

Payment amounts are based on Eligibility Category, State Living Arrangement, whether the client is eligible as an individual or as a member of an eligible couple and the amount of countable income. If countable income exceeds the Federal Benefit Rate (FBR), the amount exceeding the FBR is deducted from the SSP payment standard. Payment standards are available online at www.mass.gov/dta under the heading Key Resources/Program Eligibility Charts and Tables/SSI Program Payment Charts. Paper copies are available upon request.
```

#### Rank 3 — PARTIAL (sim 0.321)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk explains that SSP payment levels are based on Eligibility Category, State Living Arrangement, and individual/couple status, but does not provide the actual payment standard amounts or rates.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.100 Overview of State Supplement Program

SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 4 — IRRELEVANT (sim 0.337)

- **Chunk ID**: `cmr_sec_327_370__000`
- **Section**: `327.370` — Designated Payees and SSA Representative Payees
- **Program**: SSP
- **Judge reason**: This chunk addresses designated payees and payment recipients for SSP, not the payment standards (benefit amounts) that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.370 Designated Payees and SSA Representative Payees

(A) A Designated Payee is a third-party appointed by the Department to receive the SSP benefit payments when the client is unable to manage or direct the management of benefit payments in his or her own interest.
(B) SSP benefits of a client whose SSI benefits are paid to an SSA Representative Payee will also be paid to the SSA Representative Payee. For SSP purposes, this SSA Representative Payee will be known as a Designated Payee.
(C) SSP benefits for a child younger than 18 years old must be paid to a Designated Payee.
```

#### Rank 5 — PARTIAL (sim 0.310)

- **Chunk ID**: `cmr_sec_327_110__000`
- **Section**: `327.110` — Definitions
- **Program**: SSP
- **Judge reason**: This chunk defines SSP-related terms but does not contain the actual payment standards/amounts that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.110 Definitions

The following words and terms, when used in 106 CMR 327.000, have the following meanings, unless the context otherwise requires. (Mass. Register #1390 5/3/19) Child. For SSP purposes, is one who meets the SSI definition of child. Countable Income. As defined in 20 CFR 416.1104. Eligible Individual. An aged, disabled or blind individual who meets all SSI eligibility requirements. See 20 CFR 416.120. Eligible Couple. An eligible individual and his or her eligible spouse who are living in the same household. See 20 CFR 416.1801. Federal Benefit Rate (FBR). As defined in 20 CFR 416.1101. Public Income Maintenance Payment. A payment from any of the following programs: SSI, TAFDC, Refugee Act of 1980, Disaster Relief Act of 1974, Veterans Administration benefits based on need, or any State or local governmental assistance program based on need. Representative Payee. As defined in 20 CFR 416.601. Resources. As defined in 20 CFR 416.1201, et seq. Supplemental Security Income (SSI). As defined in 20 CFR 416.101. SSP-only. A designation for a client who is ineligible for SSI solely based on his or her income but is eligible to receive SSP benefits.
```


### cmr_015 — fair hearings general (rank-1: RELEVANT)

**Question**: What is the fair hearing process at DTA  
**Program filter**: (none)  
**Expected section (for reference)**: `343.110` — judge picked rank-1 RELEVANT chunk in section `343.110` (section-author intuition agrees)  
**Notes**: 343.110 General Description of the Fair Hearing Process; no program filter (343 is Hearings)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.488)

- **Chunk ID**: `cmr_sec_343_110__000`
- **Section**: `343.110` — General Description of the Fair Hearing Process
- **Program**: Hearings
- **Judge reason**: This chunk directly describes the fair hearing process at DTA, including its purpose, structure, and how it operates, which directly answers the user's question.

```
106 CMR 343 > FAIR HEARING RULES > 343.110 General Description of the Fair Hearing Process

The fair hearing process is an adjudicatory proceeding which allows dissatisfied applicants and clients and certain spouses, as well as certain sponsors of aliens, upon written request, to obtain a determination of the appropriateness of certain actions or inactions on the part of the Department, or of alleged coercive or otherwise improper conduct by a Department employee. The process is designed to secure and protect the interests of both the appellant and appropriate Department personnel and to ensure fair and equitable treatment for all involved. A hearing is conducted by an impartial hearing officer of DOH. The decision of the hearing officer is based only on evidence and testimony presented at the hearing. The hearing officer examines the facts, the law, and the other circumstances of the case presented by the parties to determine the legality and appropriateness of the disputed Department actions or decision of the Department. The hearing decision is binding upon the Department and is not subject to any review within the Department except in the case of a remand of the decision for a new hearing pursuant to 106 CMR 343.710.
```

#### Rank 2 — PARTIAL (sim 0.530)

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

#### Rank 3 — PARTIAL (sim 0.450)

- **Chunk ID**: `cmr_sec_343_225__000`
- **Section**: `343.225` — Notification of the Right to Request a Hearing
- **Program**: Hearings
- **Judge reason**: Addresses notification and request procedures for fair hearings but does not describe the actual hearing process itself (procedures, timeline, decision-making, etc.)

```
106 CMR 343 > FAIR HEARING RULES > 343.225 Notification of the Right to Request a Hearing

(A) At the time of application, and at the time of any Department action affecting his or her assistance, each applicant or client shall be informed in writing of his or her right to a hearing, how to request a hearing and of the right to an authorized representative.
(B) At any time that an applicant or client indicates disagreement with a Department action, he or she shall be told of the right to request a fair hearing. The Department shall help the applicant or client by providing an appeal form and, if asked, help completing the form. The Department must assure the unrestricted freedom to request a fair hearing.
(C) If there is an individual or organization that gives free legal representation, the person asking for a hearing shall be told of the availability of that service.
```

#### Rank 4 — PARTIAL (sim 0.439)

- **Chunk ID**: `cmr_sec_343_610__000`
- **Section**: `343.610` — Basis of Fair Hearing Decisions
- **Chunk position**: 1 / 3
- **Program**: Hearings
- **Hierarchy**: (A) The hearing officer's decision shall be based upon evidence, testimony, m...
- **Judge reason**: Addresses one specific aspect of fair hearings (basis of decisions) but doesn't provide an overview of the overall fair hearing process or procedures.

```
106 CMR 343 > FAIR HEARING RULES > 343.610 Basis of Fair Hearing Decisions

(A) The hearing officer's decision shall be based upon evidence, testimony, materials and legal rules presented at the hearing. Any evidence, testimony, materials, legal rules or arguments presented after the close of the hearing will be excluded unless the hearing is reopened, the parties stipulate procedures for response, or otherwise waive the right to respond.
```

#### Rank 5 — PARTIAL (sim 0.437)

- **Chunk ID**: `cmr_sec_343_030__006`
- **Section**: `343.030` — Definitions
- **Chunk position**: 7 / 8
- **Program**: Hearings
- **Hierarchy**: (K) Party. The appellant or the Department.
- **Judge reason**: Provides definitions of key terms in the fair hearing process but does not describe the actual procedural steps or process itself.

```
106 CMR 343 > FAIR HEARING RULES > 343.030 Definitions > (K) Party. The appellant or the Department.

(K) Party. The appellant or the Department.
(L) Client. A person or family who is or had been receiving assistance under a program administered by the Department of Transitional Assistance.
(M) Hearing Officer. An impartial and independent person designated by the Director of the Division of Hearings to conduct hearings and render decisions under 106 CMR 343.000. No hearing officer who has a direct or indirect interest, personal involvement or bias in a hearing shall conduct such a hearing or participate in the decision-making process of such matters.
```


### cmr_016 — hearing time limits (rank-1: PARTIAL)

**Question**: How long does someone have to request a fair hearing  
**Program filter**: (none)  
**Expected section (for reference)**: `343.140`  
**Notes**: 343.140 Time Limits; could also pull 367.100 (SNAP hearing timing)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — PARTIAL (sim 0.467)

- **Chunk ID**: `cmr_sec_343_240__000`
- **Section**: `343.240` — Request for Fair Hearing
- **Program**: Hearings
- **Judge reason**: The chunk references time limits for requesting a fair hearing but directs to another regulation (106 CMR 343.140) rather than stating the actual timeframe.

```
106 CMR 343 > FAIR HEARING RULES > 343.240 Request for Fair Hearing

(A) A request for a fair hearing is defined as a written statement by the appellant or his or her authorized representative which asks for the opportunity to present the case to a higher authority. The request for a fair hearing must be received by DOH within the time limits provided in 106 CMR 343.140.
(B) Any request for a fair hearing which alleges coercive or otherwise improper conduct on the part of a Department employee must state the name of the employee and the place, date and nature of the incident. If the request lacks the information required by 106 CMR 343.240, DOH shall notify the appellant of the requirement. If the appellant then fails to provide the information within ten days, the appeal shall be dismissed.
```

#### Rank 2 — RELEVANT (sim 0.475)

- **Chunk ID**: `cmr_sec_367_100__000`
- **Section**: `367.100` — Time Period for Requesting Hearing
- **Program**: Program Integrity
- **Judge reason**: Directly specifies the time periods (90 days, one year, and within certification period) for requesting a fair hearing on DTA actions and benefit disputes.

```
106 CMR 367 > VIOLATIONS, > 367.100 Time Period for Requesting Hearing

A household shall be allowed to request a hearing on any action by the Department, or on loss of benefits which occurred in the prior 90 days. Action by the Department includes a denial of a request for restoration of any benefits lost more than 90 days but less than one year prior to the request. In addition, at any time within a certification period a household may request a fair hearing to dispute its current level of benefits.
```

#### Rank 3 — PARTIAL (sim 0.454)

- **Chunk ID**: `cmr_sec_343_225__000`
- **Section**: `343.225` — Notification of the Right to Request a Hearing
- **Program**: Hearings
- **Judge reason**: This chunk explains the right to request a hearing and notification procedures, but does not specify the timeframe or deadline for actually requesting a fair hearing.

```
106 CMR 343 > FAIR HEARING RULES > 343.225 Notification of the Right to Request a Hearing

(A) At the time of application, and at the time of any Department action affecting his or her assistance, each applicant or client shall be informed in writing of his or her right to a hearing, how to request a hearing and of the right to an authorized representative.
(B) At any time that an applicant or client indicates disagreement with a Department action, he or she shall be told of the right to request a fair hearing. The Department shall help the applicant or client by providing an appeal form and, if asked, help completing the form. The Department must assure the unrestricted freedom to request a fair hearing.
(C) If there is an individual or organization that gives free legal representation, the person asking for a hearing shall be told of the availability of that service.
```

#### Rank 4 — RELEVANT (sim 0.516)

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

#### Rank 5 — PARTIAL (sim 0.442)

- **Chunk ID**: `cmr_sec_343_230__000`
- **Section**: `343.230` — Grounds for Appeal
- **Chunk position**: 1 / 6
- **Program**: Hearings
- **Hierarchy**: (A) Denial of an application or request for assistance or the right to apply ...
- **Judge reason**: The chunk explains what grounds exist for requesting a fair hearing but does not address the timeframe or deadline for making such a request.

```
106 CMR 343 > FAIR HEARING RULES > 343.230 Grounds for Appeal

Applicants and clients have a right to request a fair hearing for:
(A) Denial of an application or request for assistance or the right to apply or reapply for assistance (including supplemental payments) programs administered by the Department.
```


### cmr_017 — IPV definition (rank-1: RELEVANT)

**Question**: What is an Intentional Program Violation  
**Program filter**: (none)  
**Expected section (for reference)**: `367.525` — judge picked rank-1 RELEVANT chunk in section `706.300` (section-author intuition disagrees with judge)  
**Notes**: 367.525 Definition of an Intentional Program Violation  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.00  

#### Rank 1 — RELEVANT (sim 0.425)

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

#### Rank 2 — PARTIAL (sim 0.406)

- **Chunk ID**: `cmr_sec_367_500__000`
- **Section**: `367.500` — Intentional Program Violation Claim
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Judge reason**: The chunk explains how intentional program violation claims are pursued but does not define what an intentional program violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.500 Intentional Program Violation Claim

A claim for overissuance shall be pursued as an intentional program violation claim if an Administrative Disqualification Hearing, or a court of appropriate jurisdiction, has found that a household member committed an intentional program violation, or if the individual has filed a signed waiver of his or her right to an Administrative Disqualification Hearing or entered into a consent agreement with the court. All claims established under the Food Stamp Act and future claims shall be collected in accordance with 106 CMR 367.500.
```

#### Rank 3 — PARTIAL (sim 0.393)

- **Chunk ID**: `cmr_sec_367_500__001`
- **Section**: `367.500` — Intentional Program Violation Claim
- **Chunk position**: 2 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Calculating the Amount of an Intentional Program Violation Claim.
- **Judge reason**: The chunk explains how to calculate an Intentional Program Violation claim but does not define what an Intentional Program Violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.500 Intentional Program Violation Claim > (A) Calculating the Amount of an Intentional Program Violation Claim.

(A) Calculating the Amount of an Intentional Program Violation Claim. The amount of an overissuance claim due to an intentional program violation is determined by calculating the difference between the amount actually received and the amount the household should have received during the time period at issue. When determining the amount of benefits the household should have received, the Department shall not apply the 20% earned income deduction to that portion of earned income which the household intentionally failed to report. The Department shall not include any portion of an overissuance that occurred in a month more than six years from the date the overissuance was discovered. If the household member is determined to have committed an intentional program violation by knowingly, willfully, and with deceitful intent failing to report a change in its household circumstances, the first month benefits were overissued shall be the first month the change would have been made effective had it been reported on time.
```

#### Rank 4 — RELEVANT (sim 0.446)

- **Chunk ID**: `cmr_sec_367_525__000`
- **Section**: `367.525` — Definition of an Intentional Program Violation (IPV)
- **Program**: Program Integrity
- **Judge reason**: The chunk directly defines Intentional Program Violation (IPV) and provides specific examples of what constitutes an IPV under Massachusetts DTA policy.

```
106 CMR 367 > VIOLATIONS, > 367.525 Definition of an Intentional Program Violation (IPV)

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

#### Rank 5 — PARTIAL (sim 0.408)

- **Chunk ID**: `cmr_sec_367_520__000`
- **Section**: `367.520` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: Program Integrity
- **Judge reason**: The chunk mentions what an ADH is used for (determining if an IPV was committed) but does not define what an Intentional Program Violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.520 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall conducted in order to determine if an intentional program violation (IPV) has been committed. An ADH shall be initiated by the Department if evidence exists to indicate an IPV was committed.
```


### cmr_018 — SNAP IPV penalties (rank-1: RELEVANT)

**Question**: What are the disqualification penalties for SNAP fraud  
**Program filter**: (none)  
**Expected section (for reference)**: `367.800` — judge picked rank-1 RELEVANT chunk in section `367.800` (section-author intuition agrees)  
**Notes**: 367.800 Disqualification Penalties; 367 is Program Integrity for SNAP  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.568)

- **Chunk ID**: `cmr_sec_367_800__000`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Disqualification for Intentional Program Violations.
- **Judge reason**: Directly specifies SNAP fraud (IPV) disqualification penalties: 1 year for first offense, 2 years for second, and permanent disqualification for third offense.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties

(A) Disqualification for Intentional Program Violations.
(1) Individuals found to have committed a SNAP IPV at an ADH shall be ineligible for SNAP benefits for a period of one year for the first finding, two years for the second finding and permanently for the third finding.
(2) Individuals found to have committed a cash program IPV at an ADH, in the absence of a SNAP IPV under 106 CMR 367.800(A)(1), shall be ineligible for SNAP benefits for the period required under the cash program rules.
```

#### Rank 2 — RELEVANT (sim 0.563)

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

#### Rank 3 — PARTIAL (sim 0.564)

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

#### Rank 4 — PARTIAL (sim 0.516)

- **Chunk ID**: `cmr_sec_367_800__004`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 5 / 6
- **Program**: Program Integrity
- **Hierarchy**: (E) Disqualification for Voluntary Quit.
- **Judge reason**: The chunk addresses SNAP disqualification penalties but only for voluntary job quit violations, not for fraud violations which is what the user specifically asked about.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties > (E) Disqualification for Voluntary Quit.

(E) Disqualification for Voluntary Quit. For applicant households, when a client subject to the SNAP work requirements at 106 CMR 362.310: SNAP Employment and Training Program is unemployed and has voluntarily quit a job without good cause within the 60 days before application, the entire household is ineligible for SNAP benefits for a period of three months for the first finding, six months for the second finding and 12 months for the third finding. For ongoing households, when a client subject to the SNAP work requirements is unemployed and has voluntarily quit a job without good cause, the individual shall be ineligible for SNAP benefits for a period of three months for the first finding, six months for the second finding and 12 months for the third finding. The entire household shall be ineligible for SNAP benefits for a period of six months if the head of household voluntarily quits a job while participating in the program. Persons who have been disqualified for quitting a job without good cause will carry their sanction with them if they join a new household.
```

#### Rank 5 — PARTIAL (sim 0.506)

- **Chunk ID**: `cmr_sec_367_550__000`
- **Section**: `367.550` — Warning to Applicants
- **Program**: Program Integrity
- **Judge reason**: The chunk mentions that disqualification penalties for IPV (Intentional Program Violation) exist and must be communicated to applicants, but does not specify what those actual penalties are.

```
106 CMR 367 > VIOLATIONS, > 367.550 Warning to Applicants

The Department shall inform households in writing of the disqualification penalties for committing an IPV at each application. The penalties shall be written in clear, prominent and boldface lettering on the application form or as a separate notification. The Department shall provide the written penalty warning in English, Spanish, and other languages spoken by a significant minority population.
```


### cmr_019 — TAFDC vs EAEDC (rank-1: PARTIAL)

**Question**: What is the difference between TAFDC and EAEDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `701.200`  
**Notes**: 701.200 The TAFDC and EAEDC Programs  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.434)

- **Chunk ID**: `cmr_sec_701_200__000`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk describes TAFDC but does not provide information about EAEDC or explain the differences between the two programs.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.200 The TAFDC and EAEDC Programs

The Transitional Aid to Families with Dependent Children (TAFDC) program provides financial assistance and employment-related services to families with dependent children. The TAFDC program is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 118 and other relevant statutes and the rules, regulations and policies. TAFDC regulations implement St. 1995, c. 5. TAFDC seeks to integrate clients into the work force and break the cycle of poverty. The major program objectives include:
```

#### Rank 2 — PARTIAL (sim 0.437)

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

#### Rank 3 — PARTIAL (sim 0.424)

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

#### Rank 4 — PARTIAL (sim 0.395)

- **Chunk ID**: `cmr_sec_704_430__000`
- **Section**: `704.430` — EAEDC Living Arrangement and Grant Calculation
- **Chunk position**: 1 / 3
- **Program**: EA
- **Hierarchy**: (A) Defifinition.
- **Judge reason**: The chunk discusses EAEDC living arrangements and mentions TAFDC in comparison contexts, but does not explain the fundamental differences between the two programs themselves.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.430 EAEDC Living Arrangement and Grant Calculation

The EAEDC grant for applicants or clients is based on the living arrangement of the assistance unit. EAEDC Living Arrangement
(A) Defifinition. In order to be eligible for EAEDC, the living arrangement of EAEDC applicants or clients must be one of the following:
(1) Living Arrangement A: an EAEDC individual or EAEDC family who is responsible for a shelter cost, including, but not limited to, rent, mortgage, real estate taxes, insurance, fuel or utility expenses or room or board expenses from a licensed lodging house, and who:
(a) Lives alone; or
(b) Lives with others (including another assistance unit, applying for or receiving TAFDC where there is no legal obligation to support), except as provided in 106 CMR 704.435(A)(2) or (3);
(2) Living Arrangement B: an EAEDC individual or EAEDC family who lives with another assistance unit who is applying for, or receiving TAFDC, including spouses, and a legal obligation to support exists between a member of the TAFDC assistance unit and a member of the EAEDC assistance unit, except as provided in 106 CMR 704.435(A)(3)(b);
```

#### Rank 5 — PARTIAL (sim 0.433)

- **Chunk ID**: `cmr_sec_703_010__000`
- **Section**: `703.010` — Overview of EAEDC Nonfinancial Requirements
- **Program**: EA
- **Judge reason**: The chunk describes EAEDC eligibility requirements but does not explain the differences between TAFDC and EAEDC programs.

```
106 CMR 703 > NONFINANCIAL > 703.010 Overview of EAEDC Nonfinancial Requirements

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


### cmr_020 — TAFDC 24-month limit (rank-1: PARTIAL)

**Question**: How are TAFDC time-limited benefits applied  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.120`  
**Notes**: 703.120 TAFDC Time-limited Benefits  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.521)

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

#### Rank 2 — PARTIAL (sim 0.492)

- **Chunk ID**: `cmr_sec_703_130__000`
- **Section**: `703.130` — TAFDC Extension of Benefits Beyond the 24-month Period
- **Chunk position**: 1 / 5
- **Program**: EA
- **Judge reason**: Addresses extensions beyond the 24-month period but doesn't explain how time-limited benefits are initially applied or calculated.

```
106 CMR 703 > NONFINANCIAL > 703.130 TAFDC Extension of Benefits Beyond the 24-month Period

The Commissioner or designee may extend benefits beyond the 24-month period under certain circumstances. A nonexempt grantee granted an extension must meet all other program requirements. Requests for extensions will be reviewed and determined on a case-by-case basis. Granted extensions may be reviewed and revised as the Commissioner or designee deems appropriate. An individual may request an extension of benefits beyond the 24-month period after a nonexempt grantee has used 22 months of time-limited benefits, or at any time when an individual has already received 24 months of time-limited benefits.
```

#### Rank 3 — PARTIAL (sim 0.463)

- **Chunk ID**: `cmr_sec_703_190__007`
- **Section**: `703.190` — TAFDC Disability Exemption Process
- **Chunk position**: 8 / 10
- **Program**: EA
- **Hierarchy**: (G) When an applicant, who has previously been denied by the Department’s age...
- **Judge reason**: The chunk discusses disability exemptions and references time-limited benefits usage (24 months) but does not explain how time-limited benefits are actually applied or calculated overall.

```
106 CMR 703 > NONFINANCIAL > 703.190 TAFDC Disability Exemption Process > (G) When an applicant, who has previously been denied by the Department’s age...

(G) When an applicant, who has previously been denied by the Department’s agent, makes another claim of disability within a continuous 60-month period; and
(1) the applicant has used 24 months of time-limited benefits (see 106 CMR 703.120), eligibility must be established using the verification described in 106 CMR 701.380(B)(7).
(a) If the applicant is requesting a time-limited benefits extension (see 106 CMR 703.130), the verification described in 106 CMR 701.380(B)(7) may also be used to excuse the applicant from meeting the work activities related to qualifying for a time- limited benefits extension.
(b) If the applicant is not requesting a time-limited benefits extension, the verification described in 106 CMR 701.380(B)(7) may be used to excuse the applicant from meeting the work program requirement (see 106 CMR 703.150), if applicable;
(2) the applicant has not used 24 months of time-limited benefits, the verification at 106 CMR 701.380(B)(7) may be used to excuse the applicant from meeting the work program requirement (see 106 CMR 703.150), if applicable. If the verification described in 106 CMR 701.380(B)(7) is provided, eligibility for TAFDC will be presumed but the applicant will not be considered exempt under 106 CMR 703.100. The final disability determination will be made by the Department’s agent. The length of this good cause period will be determined by the specified verification until the final disability determination is made by the Department’s agent.
```

#### Rank 4 — PARTIAL (sim 0.485)

- **Chunk ID**: `cmr_sec_703_100__000`
- **Section**: `703.100` — TAFDC Exemptions from Time-limited Benefits
- **Chunk position**: 1 / 10
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk describes exemptions FROM time-limited benefits rather than how time-limited benefits are applied, so it's related but doesn't directly answer the question about the application process itself.

```
106 CMR 703 > NONFINANCIAL > 703.100 TAFDC Exemptions from Time-limited Benefits

(A) Requirements.
(1) An assistance unit is exempt from the TAFDC time-limited benefits restrictions found at 106 CMR 703.120, if the grantee:
(a) is disabled as defined in 106 CMR 703.190. A client who requests an exemption under this clause shall, as a condition of continued eligibility, apply for Social Security Disability benefits (RSDI/SSI) and, if requested by the Department, appeal a denial of Social Security Disability benefits at the Social Security Administration as specified in 106 CMR 703.190. Clients who do not comply with the Department’s request to apply for Social Security Disability benefits or appeal a decision shall not be granted a work exemption under this clause;
(b) is essential to the care of one of the following disabled persons living in the home:
1. a child;
2. the grantee's spouse; or
3. the child's other parent. A client who requests this exemption shall either apply for Social Security Disability benefits on behalf of the disabled child or spouse or the disabled spouse or child’s other parent must apply for benefits on his or her own behalf. Verification of such required Social Security Disability benefits applications must be provided.
(c) is in their 33rd week or later of pregnancy or in their third trimester of pregnancy who have submitted documentation signed by a primary care provider or an obstetrician, gynecologist, nurse-midwife or family practitioner that the client has a pregnancy-related
```

#### Rank 5 — PARTIAL (sim 0.441)

- **Chunk ID**: `cmr_sec_703_000__000`
- **Section**: `703.000` — Overview of TAFDC Nonfinancial Requirements
- **Program**: EA
- **Judge reason**: The chunk lists time-limited benefits as a requirement and references the specific regulation (703.120) but does not explain how the benefits are actually applied.

```
106 CMR 703 > NONFINANCIAL > 703.000 Overview of TAFDC Nonfinancial Requirements

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


### cmr_021 — TAFDC work program (rank-1: RELEVANT)

**Question**: What are the TAFDC work program requirements  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.150` — judge picked rank-1 RELEVANT chunk in section `703.150` (section-author intuition agrees)  
**Notes**: 703.150 TAFDC Work Program; was a persistent miss in v1  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.60  

#### Rank 1 — RELEVANT (sim 0.602)

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

#### Rank 2 — RELEVANT (sim 0.590)

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

#### Rank 3 — RELEVANT (sim 0.554)

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

#### Rank 4 — RELEVANT (sim 0.532)

- **Chunk ID**: `cmr_sec_703_150__004`
- **Section**: `703.150` — TAFDC Work Program
- **Chunk position**: 5 / 6
- **Program**: EA
- **Hierarchy**: (A) Requirements.
- **Judge reason**: The chunk directly addresses TAFDC work program requirements by specifying required hours per week based on the age of the youngest child and reapplication rules.

```
106 CMR 703 > NONFINANCIAL > 703.150 TAFDC Work Program > (A) Requirements.

(4) At Reapplication. If a grantee reapplies for assistance any time within a continuous 60- month period, the grantee, unless otherwise exempt, must meet the Work Program requirements to be eligible for assistance. The grantee will not receive another 60-day period to look for work. If the 60-month period has expired when the grantee reapplies for assistance, the grantee, unless otherwise exempt, will receive another 60-day period to look for work before having to meet the Work Program requirement.
(5) For purposes of 106 CMR 703.150(A), the required hours per week are defined as:
(a) 20 hours, if the youngest child in the assistance unit (or who is not in the assistance unit as defined in 106 CMR 704.305(A)(5)(a), (b), or (c)) is between two and six years of age (see 106 CMR 701.600: Definition of Terms); and
(b) 30 hours, if the youngest child in the assistance unit (or who is not in the assistance unit as defined in 106 CMR 704.305(A)(5)(a), (b), or (c)) is six years of age or older. In a two-parent household where both parents are work program required, each parent must meet the required hours per week based on the age of the youngest child in the assistance unit (or who is not in the assistance unit in accordance with 106 CMR 704.305(A)(5)(a), (b), or (c))
```

#### Rank 5 — PARTIAL (sim 0.530)

- **Chunk ID**: `cmr_sec_703_000__000`
- **Section**: `703.000` — Overview of TAFDC Nonfinancial Requirements
- **Program**: EA
- **Judge reason**: The chunk identifies that work program requirements exist under 106 CMR 703.150 but does not provide the actual requirements themselves.

```
106 CMR 703 > NONFINANCIAL > 703.000 Overview of TAFDC Nonfinancial Requirements

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


### cmr_022 — TAFDC asset limit (rank-1: PARTIAL)

**Question**: What is the asset limit for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `704.110`  
**Notes**: 704.110 Asset Limitations  
**Scores**: Relevant@5 = 0, Useful@5 = 4, rank-weighted = 1.25  

#### Rank 1 — PARTIAL (sim 0.504)

- **Chunk ID**: `cmr_sec_704_110__006`
- **Section**: `704.110` — Asset Limitations
- **Chunk position**: 7 / 13
- **Program**: EA
- **Hierarchy**: (B) Bank Balances.
- **Judge reason**: The chunk discusses verification procedures for bank balances under asset limitations but does not state the actual asset limit amount for TAFDC.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.110 Asset Limitations > (B) Bank Balances.

(4) Verification of Account Balances. Verification of the current balance of each account is mandatory at application, at eligibility reviews and when a change is reported. The amount is verified by bank books or bank statements that show the balance within 45 days of the date of application or redetermination. Verification is not required at redetermination when the client states the balance is $25 or less and the balance was $25 or less at the last eligibility determination and the account balance, in combination with other assets, is not over the asset limit. The statement shall be recorded in the case record.
```

#### Rank 2 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_704_110__002`
- **Section**: `704.110` — Asset Limitations
- **Chunk position**: 3 / 13
- **Program**: EA
- **Hierarchy**: (B) Bank Balances.
- **Judge reason**: The chunk discusses what counts toward asset limits and non-countable assets, but does not state the actual numerical asset limit amount for TAFDC.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.110 Asset Limitations > (B) Bank Balances.

(B) Bank Balances. ( 1) Definition. Bank balances may be in the form of savings, checking, trust accounts, term certificates, or other types of accounts held at banks, savings or loan institutions. Balances in a bank account are considered available when a member of the filing unit has both ownership of, and access to, the balance of funds in the account. Any portion of the bank balance or amount held in cash from the following sources is non-countable toward the asset limit:
(a) Highway Relocation assistance payments, Urban Renewal Assistance payments, disaster relief payments used for relocation, and payments from private agencies used for relocation;
(b) Any financial assistance paid to a student such as a financial aid package, grant, loan or scholarship for the purposes of obtaining a degree or certificate from an institution of higher education;
(c) Any portion of a Workers' Compensation, property damage, personal injury, Compensation to Victims of Violent Crimes Act, death settlement or award, except for compensation for lost wages, that is received as a reimbursement for specified items and used to pay for such items; ( d) Earned income credits, whether received as an advance payment or as part or all of an income tax refund;
(e) Any payment made under a Public Law that prohibits the payment from being included as income or a resource in determining eligibility for or the amount of benefifits under any Federal or federally assisted program;
```

#### Rank 3 — PARTIAL (sim 0.472)

- **Chunk ID**: `cmr_sec_704_110__004`
- **Section**: `704.110` — Asset Limitations
- **Chunk position**: 5 / 13
- **Program**: EA
- **Hierarchy**: (B) Bank Balances.
- **Judge reason**: The chunk discusses asset verification procedures for bank balances under asset limitations but does not state the actual asset limit amount for TAFDC.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.110 Asset Limitations > (B) Bank Balances.

have the co-holder's consent. If the account is titled A in trust for B, or A for B, A has full access to the account and B has no access to the account.
(3) Verification of Access to and Ownership of Bank Balances. Claimed lack of access and ownership must be verifified. If lack of access or ownership is verified, the funds will not be considered available to the filing unit. If the verification submitted does not demonstrate lack of access or ownership, the funds will be counted toward the asset limit.
(a) A member of the filing unit may claim lack of access to a joint account when verification has been submitted that the co-holder has a history of physical or emotional abuse, or has threatened to abuse a member of the filing unit. Verification shall be court, law enforcement, medical, psychological, child protective service social service records, or a established good cause for noncooperation with child support. When the applicant or client cannot get the verifification from one of the above sources, sworn statements from the applicant or client and at least one other individual with knowledge of the circumstances is acceptable. Such statements may be made orally and recorded in the case record.
(b) Verification that the member of the filing unit does not have ownership of, or has only partial ownership of, the balance in the account must be shown by at least two of the following:
1. Documents showing the person who opened the account, the person whose
```

#### Rank 4 — PARTIAL (sim 0.468)

- **Chunk ID**: `cmr_sec_704_281__000`
- **Section**: `704.281` — TAFDC Earned Income Disregards For Grant Calculation
- **Chunk position**: 1 / 2
- **Program**: EA
- **Hierarchy**: (A) For purposes of t the grant calculation, a TAFDC client shall have 100% o...
- **Judge reason**: The chunk discusses earned income disregards for TAFDC grant calculation but does not address asset limits, which is what the user is asking about.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.281 TAFDC Earned Income Disregards For Grant Calculation

(A) For purposes of t the grant calculation, a TAFDC client shall have 100% of his or her earned income disregarded for up to six consecutive months immediately following the start of employment, or if already employed the date on which the recipient began receiving TAFDC, whichever is later, provided the total household countable income does not exceed 200% of the Federal Poverty Limit for the client's household size. The household size is determined under the rules of 106 CMR 704.305(B) Composition of the Filing Unit. Except where 704.281l(C)(1l) applies, if a client stops working before receiving the full six months of the 100% disregard, he or she will be eligible to receive the balance of the months when employed again and all other eligibility conditions are met. If, after the client received the 100% disregard, a TAFDC case is closed for at least 30 days and subsequently reopened, the client will be eligible for another six months of the 100% disregard if the client has a different employer from the one for whom the earnings were previously disregarded. All other eligibility conditions must be met.
```

#### Rank 5 — IRRELEVANT (sim 0.460)

- **Chunk ID**: `cmr_sec_704_135__006`
- **Section**: `704.135` — Transfers of lIncome and/or Assets
- **Chunk position**: 7 / 8
- **Program**: EA
- **Hierarchy**: (D) Calculation of Period of lIneligibility.
- **Judge reason**: The chunk discusses penalties for transferred assets rather than the actual asset limit threshold for TAFDC eligibility.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.135 Transfers of lIncome and/or Assets > (D) Calculation of Period of lIneligibility.

(D) Calculation of Period of lIneligibility. Depending upon the value of the transferred income, or asset if the application is for EAEDC as a resident of a licensed rest home, all members will be subject to an uninterrupted ineligibility period. The calculation for the period of ineligibility period is as follows:
(1) Divide the value of the transferred income or asset, as determined in 106 CMR 704.135(C), by the appropriate Payment Standard for the TAFDC assistance unit or the appropriate standard of assistance for the EAEDC assistance unit. The result will be the number of months in the period of ineligibility.
(2) Any remainder from the above calculation shall be considered unearnrned income in the first month following the period of ineligibility and deducted from the appropriate Payment Standard for the TAFDC assistance unit or the appropriate standard of assistance for the EAEDC assistance unit, provided there is a reapplication for assistance during that month.
(3) The period of ineligibility shall begin on the first day of any transfer, in whole or in part, of income or assets within 12 months of application. Any assistance received during the ineligibility period is considered an overpayment in accordance with 106 CMR 706.200, et seq. 5/10/24 106 CMR - 1026
```


### cmr_023 — EAEDC disability (rank-1: PARTIAL)

**Question**: What is EAEDC disability and how is it determined  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.190`  
**Notes**: 703.190 EAEDC Disability  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.60  

#### Rank 1 — PARTIAL (sim 0.543)

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

#### Rank 2 — PARTIAL (sim 0.541)

- **Chunk ID**: `cmr_sec_703_191__004`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 5 / 11
- **Program**: EA
- **Hierarchy**: (E) The Department’s agent shall make the determination of disability for EAE...
- **Judge reason**: The chunk explains the disability determination process for EAEDC but does not define what EAEDC disability is or provide the actual medical standards/criteria used to determine it.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process > (E) The Department’s agent shall make the determination of disability for EAE...

(E) The Department’s agent shall make the determination of disability for EAEDC eligibility except when:
(1) a competent medical authority as defined in 106 CMR 701.600: Definition of Terms verifies that the applicant or client has an impairment or combination of impairments that:
(a) is expected to last at least 60 days but not more than 90 days; and
(b) meets or is equivalent to a medical standard defined in 106 CMR 703.192 or impairment included in the SSI Listing of Impairments.
(2) the applicant’s or client’s medical report is not completed by a competent medical authority, is not completed within 30 days of filing with the Department, or is not based on an examination conducted within 30 days from completion as required by l06 CMR 703.191(D);
(3) a competent medical authority verifies that the EAEDC applicant or client does not have an impairment that affects his or her ability to work and/or that the applicant’s or client’s impairment or combination of impairments is not expected to last for 60 days or more; or
```

#### Rank 3 — RELEVANT (sim 0.520)

- **Chunk ID**: `cmr_sec_703_191__006`
- **Section**: `703.191` — EAEDC Disablity Process
- **Chunk position**: 7 / 11
- **Program**: EA
- **Hierarchy**: (G) When the Department’s agent is required to make a disability determinatio...
- **Judge reason**: Directly explains how EAEDC disability is determined through a four-step process involving MassHealth standards, medical standards, SSI listings, and functional capacity assessment.

```
106 CMR 703 > NONFINANCIAL > 703.191 EAEDC Disablity Process > (G) When the Department’s agent is required to make a disability determinatio...

(G) When the Department’s agent is required to make a disability determination (see 106 CMR 703.191(E)), it shall determine in the order listed whether the applicant or client has an impairment or combination of impairments that:
(1) meets the MassHealth disability standards;
(2) meets or is equivalent to a medical standard specified in 106 CMR 703.192;
(3) does not meet a medical standard specified in 106 CMR 703.192, but meets or is equivalent to an impairment included in the SSI Listing of Impairments; or
(4) neither meets nor is equivalent to a medical standard specified in 106 CMR 703.192 or an impairment included in the SSI Listing of Impairments, but the impairment, or combination of impairments, substantially reduces or eliminates the applicant’s or client’s ability to support himself or herself when consideration is given to the vocational factors specified in 106 CMR 703.193. In making the determination in 106 CMR 703.191(G)(4), the impairment, or combination of impairments, shall not be compared to the medical standards specified in 106 CMR 703.192 or the SSI Listing of Impairments. The determination shall be based on the applicant’s or client’s functional capacity and his or her ability to do work in light of the vocational factors as specified in 106 CMR 703.193.
```

#### Rank 4 — PARTIAL (sim 0.441)

- **Chunk ID**: `cmr_sec_702_710__001`
- **Section**: `702.710` — Supplemental Security Income and State Supplement Program (SSI/SSP) Benefits
- **Chunk position**: 2 / 3
- **Program**: EA
- **Hierarchy**: (B) An EAEDC applicant or client who appears to meet the age or disability st...
- **Judge reason**: The chunk explains disability standards for EAEDC eligibility and references Social Security disability criteria, but does not comprehensively define what EAEDC disability is or provide complete determination procedures.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.710 Supplemental Security Income and State Supplement Program (SSI/SSP) Benefits > (B) An EAEDC applicant or client who appears to meet the age or disability st...

(B) An EAEDC applicant or client who appears to meet the age or disability standards for Social Security Disability benefits (RSDI/SSI) set forth in 20 CFR Part 416, Subpart I, must apply for and cooperate in the Social Security application process as a condition of receipt of cash benefits. A person appears to meet the Social Security Disability (RSDI/SSI) standards for disability if he or she is unable to or has a reduced capacity to work because of a physical or mental impairment that has lasted or is expected to last one year or more. A person who is determined to be eligible for SSI or SSP, including the person subject to recoupment as specified in 106 CMR 703.191(A), is ineligible for EAEDC. The application must be completed within the EAEDC application or eligibility review time standards. An applicant or client who must apply for Social Security Disability (RSDI/SSI) as a condition of EAEDC eligibility must complete a form prescribed by the Department that authorizes reimbursement to the Department of EAEDC assistance received pending SSI approval. The form authorizes:
```

#### Rank 5 — PARTIAL (sim 0.457)

- **Chunk ID**: `cmr_sec_701_600__006`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 7 / 25
- **Program**: EA
- **Hierarchy**: (L) Disabled Adult.
- **Judge reason**: Defines what a disabled adult is in EAEDC but doesn't explain how disability is determined or the specific evaluation process for EAEDC.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (L) Disabled Adult.

(L) Disabled Adult. An individual younger than 66 years old in the TAFDC program or under the age of 65 in the EAEDC program who meets the Department's medical and/or vocational standards as determined by the agency or organization under contract/agreement with the Department to provide disability evaluation services. In addition, an applicant or client shall be considered disabled if he or she is in receipt of Supplemental Security Income for the disabled, or Social Security benefits for the disabled. Manual Reference: 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits, 106 CMR 703.130: TAFDC Extension of Benefits Beyond the 24-month Period, 106 CMR 703.190: TAFDC Disability Exemption Process, 106 CMR 703.610: EAEDC Participant in a Massachusetts Rehabilitation Commission Program, and 106 CMR 703.620: EAEDC Caring for the Disabled.
```


### cmr_024 — ESP overview (rank-1: PARTIAL)

**Question**: What is the Employment Services Program  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `707.100`  
**Notes**: 707.100 Introduction to ESP/Orientation  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.45  

#### Rank 1 — PARTIAL (sim 0.438)

- **Chunk ID**: `cmr_sec_707_185__000`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 1 / 4
- **Program**: EA
- **Judge reason**: Describes a specific component (Post-employment Services) of what may be the Employment Services Program, but does not define or explain what the overall Employment Services Program itself is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.185 Post-employment Services Component

The Post-employment Services component is a voluntary program which provides current and former clients with services that lead to career advancement and employment stability. Participation is subject to the requirements provided in this regulation and depends on available funding and resources. The Department shall determine eligibility for and authorize Post-employment Services. Post-employment Services may only be provided by provider agencies under contract with the Department, and services may vary by provider.
```

#### Rank 2 — PARTIAL (sim 0.407)

- **Chunk ID**: `cmr_sec_707_185__003`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (C) Participation Criteria.
- **Judge reason**: Describes participation criteria for a Post-employment Services component but does not define what the Employment Services Program itself is or its overall purpose and scope.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.185 Post-employment Services Component > (C) Participation Criteria.

(C) Participation Criteria. The following are the criteria for participation in the Post-employment Services component:
(1) The individual is accepted for participation by the Post-employment Services provider;
(2) The individual must attend a program orientation required by the service provider;
(3) The individual must attend case management sessions required by the service provider; and
(4) The individual must participate in Post-employment Services activities scheduled by the service provider. The individual may terminate his or her participation by notifying the Post-employment Services provider.
```

#### Rank 3 — PARTIAL (sim 0.425)

- **Chunk ID**: `cmr_sec_707_185__001`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (A) Eligible Participants.
- **Judge reason**: Describes a specific component (Post-employment Services) of the Employment Services Program but does not define or explain what the overall Employment Services Program is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.185 Post-employment Services Component > (A) Eligible Participants.

(A) Eligible Participants. The following individuals are eligible to participate in the Post-employment Services component:
(1) employed current and former TAFDC clients; and
(2) current and former clients who are in the job search phase of a Department-approved job readiness or employment activity. In order to participate, the individual must first be accepted for participation by an authorized Post-employment Services provider. Eligibility for the Post-employment Services component is limited to up to 12 months from the date the TAFDC case closed.
```

#### Rank 4 — PARTIAL (sim 0.402)

- **Chunk ID**: `cmr_sec_707_160__000`
- **Section**: `707.160` — Supported Work Component
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: Describes a specific component (Supported Work) within the Employment Services Program rather than defining what the overall Employment Services Program is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.160 Supported Work Component

The Supported Work Component provides education, training, employment and support services that an individual needs to obtain and maintain employment. This component consists of Pre-worksite training and Worksite placement. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP) and the criteria in 106 CMR 707.160(A)(2) and (B).
```

#### Rank 5 — RELEVANT (sim 0.383)

- **Chunk ID**: `cmr_sec_707_000__000`
- **Section**: `707.000` — ESP Overview/Participation Requirements
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk directly defines the Employment Services Program (ESP) as a TAFDC program administered by the Department and explains its participation requirements.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.000 ESP Overview/Participation Requirements

106 CMR 707.00 contains the regulations for the TAFDC Employment Services Program (ESP), which is administered by the Department. TAFDC grantees, including a sanctioned or an ineligible grantee who is a parent, excepting an SSI parent, must participate in ESP as follows:
```


### cmr_025 — FEP overview (rank-1: RELEVANT)

**Question**: What is the Full Employment Program for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `708` — judge picked rank-1 RELEVANT chunk in section `708.000` (section-author intuition agrees)  
**Notes**: BROAD — chapter 708 generally (only 7 sections, all about FEP)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — RELEVANT (sim 0.568)

- **Chunk ID**: `cmr_sec_708_000__000`
- **Section**: `708.000` — Overview
- **Program**: EA
- **Judge reason**: Directly defines the Full Employment Program for TAFDC, explaining its purpose, how it works, and key characteristics of client participation.

```
106 CMR 708 > FULL EMPLOYMENT > 708.000 Overview

The Full Employment Program (FEP) component provides clients with paid work experience and on-the-job training needed to obtain an unsubsidized job. Clients participating in the Full Employment Program (FEP) will receive a subsidized wage in lieu of TAFDC cash benefits and are subject to FEP criteria in accordance with 106 CMR 707.180: Full Employment Program.
```

#### Rank 2 — PARTIAL (sim 0.514)

- **Chunk ID**: `cmr_sec_707_180__002`
- **Section**: `707.180` — Full Employment Program
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (C) Benefits of the Full Employment Program. A participant in FEP shall:
- **Judge reason**: The chunk describes benefits of FEP participation but doesn't explain what the Full Employment Program is, its purpose, eligibility requirements, or how it operates overall.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.180 Full Employment Program > (C) Benefits of the Full Employment Program. A participant in FEP shall:

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

#### Rank 3 — PARTIAL (sim 0.508)

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

#### Rank 4 — PARTIAL (sim 0.491)

- **Chunk ID**: `cmr_sec_707_200__004`
- **Section**: `707.200` — Failure to Meet Employment Development Plan (EDP) Obligations or Work Program
- **Chunk position**: 5 / 5
- **Program**: EA
- **Hierarchy**: (C) Consequences for Failure to Obtain a Job through Full Employment Program.
- **Judge reason**: The chunk discusses consequences for failure in the Full Employment Program but does not define or explain what the Full Employment Program itself is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.200 Failure to Meet Employment Development Plan (EDP) Obligations or Work Program > (C) Consequences for Failure to Obtain a Job through Full Employment Program.

(C) Consequences for Failure to Obtain a Job through Full Employment Program.
(1) An individual, who, after three failed attempts to obtain a job through the Full Employment Program (FEP), without good cause as defined by 106 CMR 701.380: Good Cause Criteria, shall be mandated to participate in the TAFDC Community Service component. The EDP will be updated with the mandatory community service requirement and ways the he or she may meet the Work Program requirements.
(2) For the first failure to participate in mandated TAFDC Community Service, the individual is ineligible for TAFDC until he or she meets the Work Program requirements for the required hours per week as provided in 106 CMR 703.150(A)(5) or begins or resumes participation in TAFDC Community Service, participates in other work program activities as provided in 106 CMR 703.150(A)(2) or a combination of these activities for two consecutive weeks.
(3) After the second or subsequent failure by a grantee to participate in mandated TAFDC Community Service, the assistance unit is ineligible for assistance until the individual meets the Work Program requirements for the required hours per week as provided in 106 CMR 703.150(A)(5) or begins or resumes participation in TAFDC Community Service, participates in other work program activities as provided in 106 CMR 703.150(A)(2) or a combination of these activities for two consecutive weeks.
(4) Assistance to the remaining members of the assistance unit shall be in the form of vendor payments, when possible.
```

#### Rank 5 — RELEVANT (sim 0.537)

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


### cmr_026 — TAFDC MassHealth (rank-1: PARTIAL)

**Question**: When is a SNAP household eligible for MassHealth referral  
**Program filter**: (none)  
**Expected section (for reference)**: `705.100`  
**Notes**: 705.100 MassHealth (in TCAP related benefits — though question says SNAP, might cross-pull)  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.547)

- **Chunk ID**: `cmr_sec_705_200__000`
- **Section**: `705.200` — Supplemental Nutrition Assistance Program (SNAP)
- **Program**: EA
- **Judge reason**: The chunk discusses SNAP eligibility and categorical eligibility for SNAP households, but does not address MassHealth referral eligibility criteria.

```
106 CMR 705 > RELATED > 705.200 Supplemental Nutrition Assistance Program (SNAP)

The purpose of SNAP is to ensure adequate nutrition for low income households. The program is administered by the Department. Obtaining SNAP
(A) An applicant or client may also apply for and be eligible for SNAP benefits. The worker must ask whether the applicant wants to apply for SNAP, and if so, must ensure that the application is processed appropriately. When all the members of the SNAP household are receiving TAFDC and/or SSI benefits, the household is categorically eligible for SNAP. See 106 CMR 365.180: Categorically Eligible Households.
```

#### Rank 2 — PARTIAL (sim 0.516)

- **Chunk ID**: `cmr_sec_705_100__000`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 1 / 4
- **Program**: EA
- **Judge reason**: The chunk discusses MassHealth eligibility for TAFDC and EAEDC clients but does not specifically address SNAP household eligibility or referral criteria for MassHealth.

```
106 CMR 705 > RELATED > 705.100 MassHealth

MassHealth provides medical services for individuals who meet specific income and other eligibility requirements. Current TAFDC and EAEDC clients are eligible for MassHealth without filing a separate application. The following are eligible to receive MassHealth benefits: (MA REG. # 1360, Dated 3-9-18)
```

#### Rank 3 — PARTIAL (sim 0.494)

- **Chunk ID**: `cmr_sec_705_100__002`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (B) Extension of MassHealth after the TAFDC Termination for Employment Reasons
- **Judge reason**: Addresses MassHealth eligibility but specifically for TAFDC termination due to employment, not general SNAP household referral eligibility criteria.

```
106 CMR 705 > RELATED > 705.100 MassHealth > (B) Extension of MassHealth after the TAFDC Termination for Employment Reasons

(B) Extension of MassHealth after the TAFDC Termination for Employment Reasons
(1) Members of a TAFDC assistance unit who are ineligible for TAFDC remain eligible for MassHealth for the 12-calendar-month period beginning with the month in which the family becomes ineligible for TAFDC provided that the unit:
(a) continues to include a child who meets the age requirements provided in 106 CMR 703.220: TAFDC Dependent Child: Younger than 18 Years Old and 703.230: TAFDC Dependent Child: 18 years of Age) of a dependent child getting TAFDC;
(b) became ineligible for TAFDC because of an income increase from the grantee's work; and
(c) has a member who continues to work.
```

#### Rank 4 — PARTIAL (sim 0.510)

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

#### Rank 5 — PARTIAL (sim 0.476)

- **Chunk ID**: `cmr_sec_705_100__003`
- **Section**: `705.100` — MassHealth
- **Chunk position**: 4 / 4
- **Program**: EA
- **Hierarchy**: (C) EAEDC Medical Assistance.
- **Judge reason**: Discusses MassHealth eligibility for EAEDC clients but does not address SNAP household eligibility for MassHealth referral.

```
106 CMR 705 > RELATED > 705.100 MassHealth > (C) EAEDC Medical Assistance.

(C) EAEDC Medical Assistance.
(1) The EAEDC program provides EAEDC medical assistance (i.e., limited medical services) to applicants and clients of EAEDC. These services shall be specified in MassHealth regulations of the Division of Medical Assistance.
(2) Certain clients of EAEDC may also be eligible for MassHealth in accordance with the MassHealth regulations of the Division of Medical Assistance. A client is ineligible for EAEDC Medical Assistance if he or she receives benefits under MassHealth.
```


### cmr_027 — TAFDC overpayments (rank-1: RELEVANT)

**Question**: How does DTA correct overpayments and underpayments  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `706.210` — judge picked rank-1 RELEVANT chunk in section `706.210` (section-author intuition agrees)  
**Notes**: 706.210 Correction of Overpayments and Underpayments  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.476)

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

#### Rank 2 — PARTIAL (sim 0.392)

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

#### Rank 3 — PARTIAL (sim 0.402)

- **Chunk ID**: `cmr_sec_706_250__001`
- **Section**: `706.250` — Recovery
- **Chunk position**: 2 / 4
- **Program**: EA
- **Hierarchy**: (B) The Department shall recover all overpayments from current clients regard...
- **Judge reason**: Addresses overpayment recovery procedures but does not explain how DTA corrects underpayments or the full process of how corrections are made.

```
106 CMR 706 > AUXILIARY > 706.250 Recovery > (B) The Department shall recover all overpayments from current clients regard...

(B) The Department shall recover all overpayments from current clients regardless of the amount of the overpayment. The Department shall recover all overpayments from previous clients as provided in 106 CMR 706.280. An overpayment shall be recovered from grantees even if grantees were overpaid in one cash assistance program and is now receiving benefits in another cash assistance program.
```

#### Rank 4 — PARTIAL (sim 0.376)

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

#### Rank 5 — PARTIAL (sim 0.376)

- **Chunk ID**: `cmr_sec_706_260__000`
- **Section**: `706.260` — Recovery of Overpayments Resulting from Department Error and Payments Pending a
- **Program**: EA
- **Judge reason**: The chunk addresses overpayment recovery procedures but does not explain how DTA corrects underpayments or the general correction process for both types of payment errors.

```
106 CMR 706 > AUXILIARY > 706.260 Recovery of Overpayments Resulting from Department Error and Payments Pending a

Fair Hearing Decision and Non-fraudulent Client Error
(A) Overpayments resulting from Department error and non-fraudulent client error shall be recovered.
(B) Overpayments resulting from assistance paid pending implementation of a fair hearing decision as provided in 106 CMR 343.250: Continuation of Benefits Pending Appeal following an appeal of reduction or termination in benefits shall be recovered if the fair hearing decision upholds the reduction or termination. The overpayment in a split fair hearing decision, where the action of the Department is only partly upheld, is the amount found in the fair hearing decision to be incorrectly paid.
(1) The Department shall inform the client that the Department will recover any assistance paid pending implementation of a decision following a fair hearing that is decided in the Department's favor.
(2) The Department shall provide on the notice the option for the appellant to waive the receipt of assistance pending the hearing.
```


### cmr_028 — identity verification (rank-1: RELEVANT)

**Question**: How does DTA verify identity  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361` — judge picked rank-1 RELEVANT chunk in section `361.610` (section-author intuition agrees)  
**Notes**: BROAD — chapter 361 application processing covers verification; many sections in 361 may match  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.450)

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

#### Rank 2 — RELEVANT (sim 0.360)

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

#### Rank 3 — PARTIAL (sim 0.320)

- **Chunk ID**: `cmr_sec_361_610__006`
- **Section**: `361.610` — Verification Requirements at Initial Certification
- **Chunk position**: 7 / 10
- **Program**: SNAP
- **Hierarchy**: (H) Residency.
- **Judge reason**: This chunk addresses verification of residency specifically, not general identity verification procedures, though it mentions identity documents as one tool among others for verification purposes.

```
106 CMR 361 > THE > 361.610 Verification Requirements at Initial Certification > (H) Residency.

(H) Residency. Residency shall be verified before initial certification except in unusual cases (such as homeless households, certain migrant farm-worker households, or households that have just arrived in the state) where verification of residency cannot reasonably be accomplished. To the extent possible, documents used to verify rent or mortgage payments, utilities or identity shall be used to verify residency. If such documentation does not verify residency, the Department shall use any documents, collateral contact, or home visits (see 106 CMR 361.640) that reasonably establish the applicant's residency. No requirement for a specific type of verification may be imposed, and no durational or fixed residency requirement shall be established. An otherwise eligible household shall not be required to reside in a permanent dwelling or have a fixed mailing address as a condition of eligibility. The worker shall not limit verifications to a specific document and must assist the household in obtaining verification, when necessary, as discussed in 106 CMR 361.650.
```

#### Rank 4 — PARTIAL (sim 0.324)

- **Chunk ID**: `cmr_sec_361_650__000`
- **Section**: `361.650` — Responsibility for Obtaining Verification
- **Program**: SNAP
- **Judge reason**: The chunk addresses verification procedures and responsibility for providing documentary evidence, but focuses on income verification rather than identity verification specifically.

```
106 CMR 361 > THE > 361.650 Responsibility for Obtaining Verification

The household has primary responsibility for providing documentary evidence to support its income statements and to resolve any questionable information, provided that nothing in 106 CMR 361.650 shall limit the ability of the Department to verify information from other government agencies or from banks. Households may supply documentary evidence in person, through the mail, or through an authorized representative. The worker shall consider any reasonable documentary evidence provided by the household and shall be primarily concerned with how adequately the verification proves the statements on the application. If it would be difficult or impossible for the household to obtain the documentary evidence in a timely manner, or the household has presented insufficient documentation, the worker shall either offer assistance to the household in obtaining the documentary evidence, except when verification of shelter or utility costs for unoccupied homes would have to be obtained from a source outside the State, or shall use a collateral contact or home visit. The worker shall not require the household to present verification in person at the local office.
```

#### Rank 5 — PARTIAL (sim 0.308)

- **Chunk ID**: `cmr_sec_362_120__000`
- **Section**: `362.120` — Verification of Residency
- **Program**: SNAP
- **Judge reason**: The chunk discusses verification of residency and mentions identity documents as tools to verify residency, but does not directly address how DTA verifies identity itself as a standalone process.

```
106 CMR 362 > NONFINANCIAL > 362.120 Verification of Residency

Residency shall be verified before initial certification except in unusual cases (such as homeless households, certain migrant farmworker households, or households that have just arrived in the state) where verification of residency cannot reasonably be accomplished. As much as possible, documents used to verify rent or mortgage payments, utilities, or identity shall be used to verify residency. If such documentation does not verify residency, the Department shall use any documents, collateral contact, or home visits that reasonably establish the applicant's residency in accordance with 106 CMR 361.640: Sources of Verification. No requirement for a specific type of verification may be imposed. The Department shall not limit verifications to a single document and must assist the household in obtaining verification, when necessary, pursuant to 106 CMR 361.650: Responsibility for Obtaining Verification.
```


### cmr_029 — SNAP household composition (rank-1: PARTIAL)

**Question**: What are SNAP household composition rules  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.2`  
**Notes**: BROAD — 361.200 series; multiple chunks should match  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.45  

#### Rank 1 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_361_220__000`
- **Section**: `361.220` — Head of Household
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: Addresses head of household designation rules but does not comprehensively cover all SNAP household composition rules such as who qualifies as household members, income counting rules, or other composition requirements.

```
106 CMR 361 > THE > 361.220 Head of Household

Primary responsibility for designating the head of household for SNAP purposes rests with the household. The head of household may be any adult member of the household, except that if there is a minor child, the head of household must be an adult who has parental control of the child. The worker may assist in the determination of head of household. If the household does not designate a head of household, DTA may make the designation. Any adult in the household, whether or not that person is the head of the household, may apply for benefits and may conduct business with DTA on behalf of the household. The household may select its head of household at initial certification and at each subsequent recertification. It may not change the designation during a certification period unless there is a change in the household composition, including a change due to death or institutionalization of a household member. For purposes of determining head of household in regard to compliance with the General SNAP Work Requirements at 106 CMR 362.310: SNAP Employment and Training Program or when a voluntary quit is established in accordance with 106 CMR 362.340: Voluntary Quit Provisions, the head of household shall be determined as follows.
```

#### Rank 2 — PARTIAL (sim 0.474)

- **Chunk ID**: `cmr_sec_366_580__000`
- **Section**: `366.580` — Changes in Household Composition
- **Program**: SNAP
- **Judge reason**: Addresses changes to household composition and benefit restoration procedures, but does not explain the foundational rules for what constitutes a SNAP household or how household membership is initially determined.

```
106 CMR 366 > ADDITIONAL > 366.580 Changes in Household Composition

Whenever lost benefits are due because a household and the household's membership has changed, the Department shall restore the lost benefits to the household containing a majority of the individuals who were household members at the time the loss occurred. If the Department cannot locate or determine the household that contains a majority of household members, it shall restore the lost benefits to the household containing the head of the household at the time the loss occurred.
```

#### Rank 3 — PARTIAL (sim 0.466)

- **Chunk ID**: `cmr_sec_365_180__005`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 6 / 9
- **Program**: SNAP
- **Hierarchy**: (F) Verification Requirements.
- **Judge reason**: The chunk discusses household composition verification requirements for categorically eligible households but references the actual household definition in 106 CMR 361.200 rather than providing the composition rules themselves.

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

#### Rank 4 — PARTIAL (sim 0.479)

- **Chunk ID**: `cmr_sec_366_910__001`
- **Section**: `366.910` — Bay State CAP Households
- **Chunk position**: 2 / 12
- **Program**: SNAP
- **Hierarchy**: (A) Bay State CAP Eligibility Criteria.
- **Judge reason**: Addresses household composition for a specific SNAP program (Bay State CAP) rather than general SNAP household composition rules.

```
106 CMR 366 > ADDITIONAL > 366.910 Bay State CAP Households > (A) Bay State CAP Eligibility Criteria.

(A) Bay State CAP Eligibility Criteria. To be eligible for Bay State CAP benefits, the following conditions must be met by the applicant. He or she:
(1) must apply for food assistance benefits at SSA;
(2) must be receiving SSI;
(3) must not be permanently disqualified from receiving SNAP benefits;
(4) must be unmarried (single, divorced or separated);
(5) must have declared he or she purchases and prepares food separately from other individuals living in the same household;
(6) must be 18 years of age or older;
(7) must be a U.S. citizen or an eligible noncitizen in accordance with SNAP rules at 106 CMR 362.220: Noncitizens; and
(8) must not have earnings, in accordance with SSA rules.
```

#### Rank 5 — RELEVANT (sim 0.580)

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


### cmr_030 — SNAP benefit calculation (rank-1: RELEVANT)

**Question**: How are SNAP benefits calculated  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364` — judge picked rank-1 RELEVANT chunk in section `364.600` (section-author intuition agrees)  
**Notes**: BROAD — chapter 364 entirely about determining benefit  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.537)

- **Chunk ID**: `cmr_sec_364_600__002`
- **Section**: `364.600` — Determining the Benefit Level
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (B) Household Size - Over Eight.
- **Judge reason**: This chunk directly explains the step-by-step calculation method for determining SNAP benefit amounts, including how to calculate maximum allotments and apply the 30% net income deduction.

```
106 CMR 364 > DETERMINING > 364.600 Determining the Benefit Level > (B) Household Size - Over Eight.

(B) Household Size - Over Eight.
(1) Determine the maximum allotment for the household size by adding the amount posted at www.mass.gov/dta for each individual in excess of eight to the maximum allotment for an eight-person household.
(2) Determine the household's monthly net income in accordance with 106 CMR 364.500.
(3) Multiply the household's monthly net income (using dollars and cents) by 30%. Drop any digits beyond the second decimal place. If the result is not whole dollars, round the result up to the next whole dollar.
(4) Subtract this 30% amount from the maximum allotment for the household size. The resulting amount is the household's monthly allotment. However, when the calculated amount is zero or less, the household is ineligible for benefits since its net income exceeds the level at which benefits are issued.
```

#### Rank 2 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_364_650__001`
- **Section**: `364.650` — Prorating Initial Month's Benefits
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Count the number of days from the first day of the household's cyclical m...
- **Judge reason**: Addresses a specific calculation method for prorating initial month SNAP benefits rather than explaining the general methodology for how monthly benefit amounts are determined

```
106 CMR 364 > DETERMINING > 364.650 Prorating Initial Month's Benefits > (A) Count the number of days from the first day of the household's cyclical m...

greater than $400, the initial month's allotment is calculated as follows:
(A) Count the number of days from the first day of the household's cyclical month through the date of application, inclusive, to determine the day of the cyclical month. If the day of the cyclical month is 31, use the number 30 instead of 31. Subtract the day of the cyclical month from 31. Multiply the result by the household's monthly allotment. Divide the result of this by 30;
```

#### Rank 3 — PARTIAL (sim 0.490)

- **Chunk ID**: `cmr_sec_364_650__000`
- **Section**: `364.650` — Prorating Initial Month's Benefits
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: The chunk addresses how initial month SNAP benefits are prorated but does not explain the overall calculation methodology for determining standard monthly SNAP benefit amounts.

```
106 CMR 364 > DETERMINING > 364.650 Prorating Initial Month's Benefits

SNAP benefits for a household's initial month shall be prorated. The initial month is the first month for which a household is certified to participate in SNAP following any period of time during which the household did not receive SNAP, except for migrant and seasonal farmworker households. For migrant and seasonal farmworker households, the initial month is the first month for which a household is certified to participate in SNAP following any period of more than one month during which the household did not receive SNAP. A migrant or seasonal farmworker household that has received SNAP within the month before application is entitled to a full month's benefits. Households which apply for initial benefits after the 15th day of the month and are determined eligible for expedited SNAP benefits in accordance with 106 CMR 365.800: Expedited Service, must be issued a combined allotment. A combined allotment includes the initial month's prorated benefits plus the second month's full allotment. Combined allotments must be issued within the seven-day expedited service time frame. Proration is the issuance of that portion of a household's monthly SNAP benefit, as calculated in accordance with 106 CMR 364.600, which corresponds to the period of time from the date of application to the end of the month. For a household with a monthly allotment of $400 or less, the initial month's allotment is determined in accordance with 106 CMR 364.990. For a household with a monthly allotment
```

#### Rank 4 — PARTIAL (sim 0.487)

- **Chunk ID**: `cmr_sec_366_520__001`
- **Section**: `366.520` — Computing the Amount to be Restored
- **Chunk position**: 2 / 2
- **Program**: SNAP
- **Hierarchy**: (B) Computing the Amount to be Restored.
- **Judge reason**: This chunk addresses how to calculate amounts to be restored due to errors, not how SNAP benefits are initially calculated based on income and household size.

```
106 CMR 366 > ADDITIONAL > 366.520 Computing the Amount to be Restored > (B) Computing the Amount to be Restored.

(B) Computing the Amount to be Restored.
(1) If an incorrect allotment caused the loss to an eligible household, the loss of benefits shall be calculated only for those months the household participated. The Department shall calculate the allotment the household was eligible to receive during the months of entitlement. The amount to be restored is the difference between the actual allotment and the allotment the household was eligible to receive.
(2) If an incorrect denial, delay or termination of benefits caused the loss, the months affected by the loss are calculated as follows:
(a) If an eligible household's application was erroneously denied, benefits will be restored back to the month of application. For an eligible household filing a timely reapplication, benefits shall be restored back to the month following the expiration of its certification period;
(b) If an eligible household's application was delayed, the months for which benefits will be restored shall be calculated in accordance with 106 CMR 361.900 through 361.960; and
(c) If a household's benefits were erroneously terminated, benefits will be restored back to the first month in which benefits were not received as a result of the erroneous action. After computing the date the loss initially occurred, the loss shall be calculated for each month subsequent to that date until either the first month the error is corrected or the first month the household is found ineligible.
```

#### Rank 5 — PARTIAL (sim 0.504)

- **Chunk ID**: `cmr_sec_362_270__009`
- **Section**: `362.270` — Deeming of Income and Assets for Sponsored Noncitizens
- **Chunk position**: 10 / 13
- **Program**: SNAP
- **Hierarchy**: (E) Determination of Available Income from a Sponsor.
- **Judge reason**: This chunk addresses income deeming calculations for sponsored noncitizens in SNAP, which is a specific component of SNAP benefit determination, but does not explain the overall SNAP benefit calculation methodology.

```
106 CMR 362 > NONFINANCIAL > 362.270 Deeming of Income and Assets for Sponsored Noncitizens > (E) Determination of Available Income from a Sponsor.

(E) Determination of Available Income from a Sponsor. The total monthly countable income of the sponsor(s) is identified in accordance with 106 CMR 363.220: Countable Income. Excluded income listed in 106 CMR 363.230: Excluded Income is not counted. The portion of the monthly income of the sponsor(s) that shall be deemed as unearned income to the sponsored noncitizen adult(s) shall be calculated as follows:
(1) Subtract 20% from the monthly gross earned income and add that result to the monthly gross unearned income, if any;
(2) Subtract from the result of (1) the Maximum Gross Monthly Income Standards at http://www.mass.gov/eohhs/gov/departments/dta/program-eligibility-charts-and-tables.html for the household equal in size to the sponsor(s) and any other person who is claimed or could be claimed by the sponsor(s) as a dependent for federal income tax purposes;
(3) Divide the result of (2) by the number of sponsored noncitizens; then
(4) Multiply the result of (3) by the number of sponsored noncitizen adults applying for SNAP benefits. This is the sponsors' deemed income amount.
```


### cmr_031 — section number lookup (rank-1: IRRELEVANT)

**Question**: What does 363.140 cover  
**Program filter**: (none)  
**Expected section (for reference)**: `363.140`  
**Notes**: ADVERSARIAL — exact section-number query. Tests whether the embedding picks up the literal '363.140' token. Hybrid search should excel here.  
**Scores**: Relevant@5 = 0, Useful@5 = 0, rank-weighted = 0.00  

#### Rank 1 — IRRELEVANT (sim 0.187)

- **Chunk ID**: `cmr_sec_360_220__000`
- **Section**: `360.220` — Complaint Requirements
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Hierarchy**: (A) Complaints shall contain the following information to facilitate investig...
- **Judge reason**: The chunk covers complaint requirements under 360.220, not the content of regulation 363.140.

```
106 CMR 360 > GENERAL > 360.220 Complaint Requirements

(A) Complaints shall contain the following information to facilitate investigations:
(1) name, address and telephone number or other means of contacting the person alleging discrimination;
(2) location and name of the organization or office accused of discriminatory practices;
(3) the nature of the incident or action or the aspect of program administration that led the person to allege discrimination;
(4) the reason for the alleged discrimination (e.g., age, race, color, sex, disability, religious creed, national origin or political belief);
(5) names, titles and addresses of persons who may have knowledge of the alleged discriminatory acts; and
(6) the date or dates on which the alleged discriminatory actions occurred.
```

#### Rank 2 — IRRELEVANT (sim 0.183)

- **Chunk ID**: `cmr_sec_360_220__003`
- **Section**: `360.220` — Complaint Requirements
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (D) A complaint must be filed no later than 180 days from the date of the all...
- **Judge reason**: The chunk discusses complaint filing deadlines under 360.220, not the coverage of regulation 363.140.

```
106 CMR 360 > GENERAL > 360.220 Complaint Requirements > (D) A complaint must be filed no later than 180 days from the date of the all...

(D) A complaint must be filed no later than 180 days from the date of the alleged discrimination. However, the time for filing may be extended by the Secretary of Agriculture or the Commissioner of the Department or designee.
```

#### Rank 3 — IRRELEVANT (sim 0.181)

- **Chunk ID**: `cmr_sec_360_250__001`
- **Section**: `360.250` — Department Obligations under Title II of the Americans With Disabilities Act (ADA) (42 U.S.C.
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) Definitions.
- **Judge reason**: The chunk covers ADA definitions under 360.250, not the content of regulation 363.140 which the user is asking about.

```
106 CMR 360 > GENERAL > 360.250 Department Obligations under Title II of the Americans With Disabilities Act (ADA) (42 U.S.C. > (A) Definitions.

(3) Physical or Mental Impairment means:
(a) any physiological disorder or condition, cosmetic disfigurement, or anatomical loss affecting one or more the following body systems: Neurological, musculoskeletal, special sense organs, respiratory (including speech organs), cardiovascular, reproductive, digestive, genitourinary, hemic and lymphatic, skin and endocrine; and
(b) Any mental or psychological disorder such as mental retardation, organic brain syndrome, emotional or mental illness, and specific learning disabilities.
(4) Major life activities include functions such as caring for one's self, performing manual tasks, walking, seeing, hearing, speaking, breathing, learning and working.
```

#### Rank 4 — IRRELEVANT (sim 0.176)

- **Chunk ID**: `cmr_sec_363_230__013`
- **Section**: `363.230` — Excluded Income
- **Chunk position**: 14 / 19
- **Program**: SNAP
- **Hierarchy**: (K) Income Excluded by Law.
- **Judge reason**: The retrieved chunk covers 363.230 (Excluded Income), not 363.140, and does not address what section 363.140 covers.

```
106 CMR 363 > FINANCIAL > 363.230 Excluded Income > (K) Income Excluded by Law.

(11) Payments for eligible individuals of Japanese ancestryor their survivors under the Civil Liberties Act of 1988, and payments up to $12,000 per person for eligible Aleuts (who were former residents of the Aleutian and Pribilof Islands) or their survivors under the Aleutian and Pribilof Islands Restitution Act, Public Law 100-383;
(12) Agent Orange Settlement Fund payments made to Vietnam veterans or their survivors, in accordance with Public Law 101-201, effective January 1, 1989;
(13) Payments made to individuals because of their status as victims of Nazi persecution in accordance with Public Law 103-286;
(14) Payments (from $200 through $1200 per month) to the child of a Vietnam veteran disabled in any way by spina bifida;
(15) Payments made under P.L. 101-426, Section 6(h)(2), the Radiation Exposure Compensation Act;
(16) The value of assistance received under the Child Nutrition Act of 1966 and the National School Lunch Act;
(17) Any amount of basic pay that is reduced under the Veterans Benefits Improvement and Health Care Authorization Act shall revert to the Treasury and not be considered to be received by or in control of such individual;
```

#### Rank 5 — IRRELEVANT (sim 0.176)

- **Chunk ID**: `cmr_sec_360_210__000`
- **Section**: `360.210` — Right to File a Complaint
- **Program**: SNAP
- **Judge reason**: The chunk covers complaint procedures under 106 CMR 360.210, not the content of 363.140 which the user is asking about.

```
106 CMR 360 > GENERAL > 360.210 Right to File a Complaint

Individuals who believe they have been subject to discrimination as specified in 106 CMR 360.200 may file a written complaint with the Secretary of Agriculture, the Administrator of FNS, Washington, D.C. 20250, and/or with the Department's Director of Equal Opportunity. The worker shall explain both the FNS and Department's complaint system to each individual who expresses an interest in filing a discrimination complaint and shall advise the individual of the right to file a complaint in either or both systems. Individuals who wish to file a Civil Rights program complaint of discrimination, can complete the USDA Program Discrimination Complaint Form, found online at http://www.ascr.usda.gov/complaint_filing_cust.html, or at any USDA office, or call (866) 632-9992 to request the form. He or she may also write a letter containing all of the information requested in the form. He or she must send the completed complaint form or letter by mail to U.S. Department of Agriculture, Director, Office of Adjudication, 1400 Independence Avenue, S.W., Washington, D.C. 20250-9410, by fax at (202) 690-7442 or email at program.intake@usda.gov. Individuals who are deaf, hard of hearing or have speech disabilities may contact USDA through the Federal Relay Service at (800) 877-8339; or (800) 845-6136 (Spanish). USDA is an equal opportunity provider and employer. Individuals may also file a complaint with Massachusetts Commission Against Discrimination, One Ashburton Place, Sixth Floor, Room 601, Boston, MA 02108; Phone: (617) 994-6000; TTY: (617) 994-6196.
```


### cmr_032 — ADH acronym (rank-1: RELEVANT)

**Question**: What is an ADH  
**Program filter**: (none)  
**Expected section (for reference)**: `367.520` — judge picked rank-1 RELEVANT chunk in section `706.315` (section-author intuition disagrees with judge)  
**Notes**: ADVERSARIAL — Administrative Disqualification Hearing. 367.520 Introduction to ADH.  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.60  

#### Rank 1 — RELEVANT (sim 0.290)

- **Chunk ID**: `cmr_sec_706_315__000`
- **Section**: `706.315` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: EA
- **Judge reason**: Directly defines ADH (Administrative Disqualification Hearing) and explains its purpose in DTA policy.

```
106 CMR 706 > AUXILIARY > 706.315 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall be conducted by the Division of Hearings to determine if an Intentional Program Violation (IPV) has been committed, unless a determination is made by a court of law pursuant to 106 CMR 706.355. An ADH may be initiated by the Department if there is reason to believe an IPV was committed.
```

#### Rank 2 — RELEVANT (sim 0.279)

- **Chunk ID**: `cmr_sec_706_335__000`
- **Section**: `706.335` — The Administrative Disqualification Hearing (ADH)
- **Program**: EA
- **Judge reason**: The chunk directly defines what an ADH (Administrative Disqualification Hearing) is and explains its procedures, directly answering the user's question.

```
106 CMR 706 > AUXILIARY > 706.335 The Administrative Disqualification Hearing (ADH)

If the individual or his or her representative fails to appear at the ADH without good cause, in accordance with 106 CMR 343.320(D), the ADH shall still be conducted. The hearing officer is required to carefully consider the evidence and determine if an Intentional Program Violation (IPV) was committed based on a preponderance of the evidence standard. If the individual is found to have committed an IPV, but the Director of the Division of Hearings later determines that there was good cause for the failure to appear, the previous decision shall be void and the Department shall conduct a new hearing. The individual has ten days from the date of the originally scheduled hearing to present evidence of good cause for failure to appear.
```

#### Rank 3 — RELEVANT (sim 0.280)

- **Chunk ID**: `cmr_sec_706_320__000`
- **Section**: `706.320` — Advance Notice of an Administrative Disqualification Hearing (ADH)
- **Chunk position**: 1 / 6
- **Program**: EA
- **Hierarchy**: (A) The date, time and place of the hearing;
- **Judge reason**: The chunk directly defines ADH as 'Advance Notice of an Administrative Disqualification Hearing' and provides regulatory details about this process.

```
106 CMR 706 > AUXILIARY > 706.320 Advance Notice of an Administrative Disqualification Hearing (ADH)

The Department shall provide a written notice at least 30 days before the ADH as provided in 106 CMR 706.325. The notice shall contain:
(A) The date, time and place of the hearing;
(B) The charge(s) against the individual;
```

#### Rank 4 — RELEVANT (sim 0.266)

- **Chunk ID**: `cmr_sec_367_520__000`
- **Section**: `367.520` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: Program Integrity
- **Judge reason**: Directly defines ADH (Administrative Disqualification Hearing) and explains its purpose in the context of DTA policy.

```
106 CMR 367 > VIOLATIONS, > 367.520 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall conducted in order to determine if an intentional program violation (IPV) has been committed. An ADH shall be initiated by the Department if evidence exists to indicate an IPV was committed.
```

#### Rank 5 — PARTIAL (sim 0.269)

- **Chunk ID**: `cmr_sec_367_800__000`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Disqualification for Intentional Program Violations.
- **Judge reason**: The chunk uses the acronym 'ADH' multiple times but never defines what it stands for or means, so it doesn't actually answer the user's question about what an ADH is.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties

(A) Disqualification for Intentional Program Violations.
(1) Individuals found to have committed a SNAP IPV at an ADH shall be ineligible for SNAP benefits for a period of one year for the first finding, two years for the second finding and permanently for the third finding.
(2) Individuals found to have committed a cash program IPV at an ADH, in the absence of a SNAP IPV under 106 CMR 367.800(A)(1), shall be ineligible for SNAP benefits for the period required under the cash program rules.
```


### cmr_033 — EPSDT acronym (rank-1: RELEVANT)

**Question**: What does EPSDT mean in DTA policy  
**Program filter**: (none)  
**Expected section (for reference)**: `705.130` — judge picked rank-1 RELEVANT chunk in section `705.130` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — Early and Periodic Screening, Diagnosis and Treatment. 705.130. Rare term.  
**Scores**: Relevant@5 = 1, Useful@5 = 1, rank-weighted = 1.00  

#### Rank 1 — RELEVANT (sim 0.503)

- **Chunk ID**: `cmr_sec_705_130__000`
- **Section**: `705.130` — Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)
- **Program**: EA
- **Judge reason**: The chunk directly defines EPSDT and explains its purpose in DTA policy, fully answering the user's question about what the acronym means.

```
106 CMR 705 > RELATED > 705.130 Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)

The purpose of EPSDT is to provide all persons in the assistance unit younger than 21 years old the opportunity for preventive health care, including medical checkups, immunizations, and dental checkups. A full description of the EPSDT program is provided in MassHealth regulations of the Division of Medical Assistance.
```

#### Rank 2 — IRRELEVANT (sim 0.341)

- **Chunk ID**: `cmr_sec_701_395__002`
- **Section**: `701.395` — Learning Disabilities: Screening, Assessment, Sanction Relief and Extensions
- **Chunk position**: 3 / 6
- **Program**: EA
- **Hierarchy**: (B) While waiting for the completion of the assessment, DTA will help clients...
- **Judge reason**: The chunk discusses learning disabilities, ESP activities, and sanctions but does not define or explain what EPSDT means.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.395 Learning Disabilities: Screening, Assessment, Sanction Relief and Extensions > (B) While waiting for the completion of the assessment, DTA will help clients...

(B) While waiting for the completion of the assessment, DTA will help clients participate in their current activity or in starting a new ESP activity. (C)(1) If a client is sanctioned (or is notified of the Department's intention to sanction) for failure to comply with an EDP or the work requirement regarding participation in an ESP activity and the client:
(a) claims that his or her learning disability caused the failure;
(b) participates in the screening and a potential learning disability is indicated; and
(c) agrees to participate in and complete a learning disability assessment, the sanction will not occur while waiting for the assessment outcome. The Department will notify the client of this action in writing. If the individual is determined to have a learning disability that requires a reasonable accommodation to participate in ESP, the pending sanction will be removed.
(2) If any of the conditions of 106 CMR 701.395(C)(1) are not met or:
(a) the individual does not cooperate with the assessment process;
(b) the individual refuses to participate in an ESP program when effective accommodations are possible and have or will be made;
(c) the assessment results find that there is no learning disability or one that requires accommodation in the above ESP program; then the sanction can occur subject to DTA appeal rights as described in 106 CMR 343.000: Fair Hearing Rules.
```

#### Rank 3 — IRRELEVANT (sim 0.333)

- **Chunk ID**: `cmr_sec_701_395__005`
- **Section**: `701.395` — Learning Disabilities: Screening, Assessment, Sanction Relief and Extensions
- **Chunk position**: 6 / 6
- **Program**: EA
- **Hierarchy**: (E) Program participants will be informed orally and in writing that if they ...
- **Judge reason**: The chunk discusses learning disability screening and ADA accommodations but does not define or explain what EPSDT means.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.395 Learning Disabilities: Screening, Assessment, Sanction Relief and Extensions > (E) Program participants will be informed orally and in writing that if they ...

(E) Program participants will be informed orally and in writing that if they provide DTA with documents that show a diagnosis of a learning disability, and that provide adequate information to determine appropriate reasonable accommodations, DTA will accept these documents as a basis for determining whether they are entitled to ADA reasonable accommodations and/or modification to DTA policies, practices and procedures. If the Department determines that the documents do not establish the diagnosis of a learning disability or do not provide information to determine appropriate reasonable accommodations, the Department will offer the client the opportunity to participate in the screening and assessment process.
```

#### Rank 4 — IRRELEVANT (sim 0.389)

- **Chunk ID**: `cmr_sec_705_140__000`
- **Section**: `705.140` — Family Planning Referrals
- **Program**: EA
- **Judge reason**: The chunk discusses family planning referrals but does not define or explain what EPSDT means.

```
106 CMR 705 > RELATED > 705.140 Family Planning Referrals

The purpose of family planning is to help members of the assistance unit obtain counseling and medical services related to having or not having children. Participation in this is voluntary. All TAFDC clients are eligible for family planning referrals and must be informed of the program. MassHealth pays for medical services related to family planning.
```

#### Rank 5 — IRRELEVANT (sim 0.352)

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


### cmr_034 — PA household defined term (rank-1: PARTIAL)

**Question**: What is a Public Assistance household for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365.110`  
**Notes**: ADVERSARIAL — defined term. 365.110 Definition of a Public Assistance (PA) Household  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.519)

- **Chunk ID**: `cmr_sec_361_170__000`
- **Section**: `361.170` — Handling Applications for Non-public Assistance (NPA) Households
- **Program**: SNAP
- **Judge reason**: The chunk defines Non-public Assistance (NPA) households, which is the opposite category of what was asked, but provides related context about SNAP household classifications.

```
106 CMR 361 > THE > 361.170 Handling Applications for Non-public Assistance (NPA) Households

NPA households are defined as follows:
(A) households in which no member is a recipient of cash assistance; and
(B) households in which some members, but not all, are applicants for or recipients of cash assistance.
```

#### Rank 2 — PARTIAL (sim 0.509)

- **Chunk ID**: `cmr_sec_365_170__000`
- **Section**: `365.170` — Department Action on Reported Changes
- **Chunk position**: 1 / 8
- **Program**: SNAP
- **Judge reason**: The chunk discusses how PA households are handled for SNAP purposes but does not define what constitutes a Public Assistance household.

```
106 CMR 365 > SPECIAL > 365.170 Department Action on Reported Changes

Except as provided in 106 CMR 365.170, action shall be taken on reported changes in accordance with the notification and timeliness standards specified in 106 CMR 366.100 through 366.220. Public Assistance (PA) households must be notified whenever their SNAP benefits are altered as a result of changes in their PA benefits. They must also be informed whenever their SNAP certification period is shortened due to changes in household circumstances. 106 CMR 365.170(A) through (C) provide special instructions for handling PA households that, during their certification period, experience:
(1) a reduction in their PA benefits;
(2) termination of their PA benefits; or
(3) a change in household circumstances resulting in a change in their SNAP classification from PA to NPA. 106 CMR 365.170(D) provides special instructions for handling a change from PA to NPA status that is known to the Department at the time of a PA redetermination.
```

#### Rank 3 — PARTIAL (sim 0.500)

- **Chunk ID**: `cmr_sec_365_170__001`
- **Section**: `365.170` — Department Action on Reported Changes
- **Chunk position**: 2 / 8
- **Program**: SNAP
- **Hierarchy**: (A) Reduction in Public Assistance Benefits.
- **Judge reason**: The chunk discusses SNAP benefits and Public Assistance interactions but does not define what constitutes a Public Assistance household for SNAP purposes.

```
106 CMR 365 > SPECIAL > 365.170 Department Action on Reported Changes > (A) Reduction in Public Assistance Benefits.

(A) Reduction in Public Assistance Benefits. When the household circumstance change results in a reduction in the household's PA benefits and a reduction or termination in its SNAP benefits within its SNAP certification period, notice of adverse action shall be issued for both the PA and the SNAP actions. If the household requests a fair hearing within the period provided by the notice of adverse action, the household's SNAP benefits shall be continued on the basis authorized immediately prior to sending the notice. The hearing shall be conducted according to PA procedures and timeliness standards. However, the household must reapply for SNAP benefits if the SNAP certification period expires before the fair hearing process is completed. If the household does not appeal, the change shall be made effective in the month following the expiration of the advance notice period, when possible. When the household circumstance change requires a reduction in the household's PA benefits but an increase in its SNAP benefits, a PA notice of adverse action shall be issued. The notice shall inform the household of the proposed increase but no action shall be taken to increase SNAP benefits until the household decides whether to appeal the proposed action to reduce the cash assistance. If the household decides to appeal and its PA benefits are continued, the household's SNAP benefits shall continue at the previous level. If the household does not
```

#### Rank 4 — PARTIAL (sim 0.500)

- **Chunk ID**: `cmr_sec_365_170__003`
- **Section**: `365.170` — Department Action on Reported Changes
- **Chunk position**: 4 / 8
- **Program**: SNAP
- **Hierarchy**: (B) Termination of Public Assistance Benefits.
- **Judge reason**: The chunk discusses SNAP benefits and Public Assistance in relation to termination and work registration requirements, but does not define what constitutes a Public Assistance household.

```
106 CMR 365 > SPECIAL > 365.170 Department Action on Reported Changes > (B) Termination of Public Assistance Benefits.

(B) Termination of Public Assistance Benefits. When a household circumstance change results in termination of the household's PA benefits, members of the household who lose their SNAP work registration exemption must be advised of the SNAP work registration requirements, if applicable. When there is sufficient information to determine how the change effects the household's SNAP eligibility and benefit level, the following action shall be taken:
(1) If the household's SNAP benefits will be reduced or terminated, notice of adverse action shall be issued for both the PA and the SNAP actions. If the household requests a fair hearing within the period provided by the notice of adverse action, the household's SNAP benefits shall be continued on the basis authorized immediately prior to sending the notice. The hearing shall be conducted according to PA procedures and timeliness standards. However, the household must reapply for SNAP benefits if the SNAP certification period expires before the fair hearing process is completed. If the household does not appeal, the change shall be made effective, when possible, in the month following the expiration of the PA advance notice period;
```

#### Rank 5 — PARTIAL (sim 0.474)

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


### cmr_035 — EDP defined term (rank-1: RELEVANT)

**Question**: What is an Employment Development Plan  
**Program filter**: (none)  
**Expected section (for reference)**: `707.110` — judge picked rank-1 RELEVANT chunk in section `707.110` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — defined term/acronym. 707.110 Completion of an Employment Development Plan (EDP)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.418)

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

#### Rank 2 — PARTIAL (sim 0.413)

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

#### Rank 3 — PARTIAL (sim 0.385)

- **Chunk ID**: `cmr_sec_707_110__004`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 5 / 5
- **Program**: EA
- **Hierarchy**: (C) Reassessment. An individual's EDP will be reassessed by the Department when:
- **Judge reason**: The chunk discusses reassessment of an EDP but does not define what an Employment Development Plan actually is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.110 Completion of an Employment Development Plan (EDP) > (C) Reassessment. An individual's EDP will be reassessed by the Department when:

(C) Reassessment. An individual's EDP will be reassessed by the Department when:
(1) he or she requests a reassessment;
(2) the individual has completed the activities in the current EDP;
(3) an individual participating in the Full Employment Program (FEP) has not found unsubsidized employment; or
(4) the Department determines that a reassessment is needed. The reassessment shall include, but not be limited to, exploring the reasons why the individual is not employed or is not able to complete his or her component activity, and a determination of any additional activities needed to meet the employment goal of the current EDP.
```

#### Rank 4 — PARTIAL (sim 0.369)

- **Chunk ID**: `cmr_sec_707_160__000`
- **Section**: `707.160` — Supported Work Component
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk mentions Employment Development Plan (EDP) by name and indicates it's required for program participation, but does not define what an EDP actually is or explain its contents and purpose.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.160 Supported Work Component

The Supported Work Component provides education, training, employment and support services that an individual needs to obtain and maintain employment. This component consists of Pre-worksite training and Worksite placement. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP) and the criteria in 106 CMR 707.160(A)(2) and (B).
```

#### Rank 5 — PARTIAL (sim 0.387)

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


### cmr_036 — SNAP allowed uses (rank-1: RELEVANT)

**Question**: What can SNAP benefits be used to purchase  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `360.100` — judge picked rank-1 RELEVANT chunk in section `360.100` (section-author intuition agrees)  
**Notes**: 360.100 Uses of SNAP Benefits (covers chapter 360 which is otherwise underrepresented)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.569)

- **Chunk ID**: `cmr_sec_360_100__000`
- **Section**: `360.100` — Uses of SNAP Benefits
- **Program**: SNAP
- **Judge reason**: Directly states what SNAP benefits can be used to purchase (eligible foods, seeds, and plants for home consumption)

```
106 CMR 360 > GENERAL > 360.100 Uses of SNAP Benefits

SNAP benefits are to be used by clients to buy eligible foods, including seeds and plants, for home consumption and use. The household may permit other persons to purchase food for the household. Such persons need not be pictured on the EBT card. Households are not required to have cooking facilities to receive SNAP.
```

#### Rank 2 — PARTIAL (sim 0.533)

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

#### Rank 3 — PARTIAL (sim 0.490)

- **Chunk ID**: `cmr_sec_361_330__000`
- **Section**: `361.330` — Authorized Representative to Purchase Food
- **Program**: SNAP
- **Judge reason**: The chunk addresses who can purchase food with SNAP benefits and procedural requirements, but does not specify what types of food or items are authorized for purchase.

```
106 CMR 361 > THE > 361.330 Authorized Representative to Purchase Food

The authorized representative may use SNAP benefits to purchase food for the household's consumption with the full knowledge and consent of the household. The authorized representative must have a Mass EBT Card in his or her own name when purchasing food with SNAP benefits.
```

#### Rank 4 — PARTIAL (sim 0.474)

- **Chunk ID**: `cmr_sec_364_900__000`
- **Section**: `364.900` — Delivery of Benefits
- **Chunk position**: 1 / 8
- **Program**: SNAP
- **Judge reason**: The chunk mentions that SNAP benefits can be used for 'food purchases' at certain locations but does not specify what particular items or categories of products are eligible for purchase.

```
106 CMR 364 > DETERMINING > 364.900 Delivery of Benefits

Eligible households shall be issued SNAP benefits for each month of eligibility. SNAP benefits can be accessed by using an Electronic Benefit Transfer (EBT) card for food purchases at grocery and other participating stores and farmers markets.
```

#### Rank 5 — PARTIAL (sim 0.418)

- **Chunk ID**: `cmr_sec_366_620__003`
- **Section**: `366.620` — Eligibility and Certification
- **Chunk position**: 4 / 4
- **Program**: SNAP
- **Hierarchy**: (B) Certification Procedures.
- **Judge reason**: The chunk mentions that households are informed where SNAP benefits may be used but does not specify what items can actually be purchased with SNAP benefits.

```
106 CMR 366 > ADDITIONAL > 366.620 Eligibility and Certification > (B) Certification Procedures.

(B) Certification Procedures.
(1) The household must complete and have the head of household, or spouse, or authorized representative sign the disaster benefit application prescribed by the Department. This application form also serves as a request for the maximum SNAP benefit for the household's size.
(2) The Department will review the application to determine if the applicant's statements meet the eligibility requirements of the Commonwealth of Massachusetts Disaster SNAP Plan.
(3) If the household fails to meet the disaster eligibility requirements, it must be given Notice of Denial and be advised that it may apply for SNAP assistance in accordance with ongoing Program requirements.
(4) If the household is determined to be eligible, the Department must provide:
(a) an Electronic Benefit Transfer (EBT) Card;
(b) disaster SNAP benefits for the maximum allotment for the household size for the period authorized by FNS; and
(c) a Notice of Approval which informs the household where SNAP benefits may be used and that the benefit is only for the specified period. Further benefits can be given only as the result of an approval of a new application for a later time period. (If FNS extends the disaster period, the household will have to make a new application for further benefits.)
```


### cmr_037 — TCAP application interview (rank-1: PARTIAL)

**Question**: How do I apply for TAFDC and what happens at the application interview  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `702.120`  
**Notes**: 702.120 The Application Interview (covers chapter 702 which is otherwise unrepresented)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.70  

#### Rank 1 — PARTIAL (sim 0.620)

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

#### Rank 2 — RELEVANT (sim 0.607)

- **Chunk ID**: `cmr_sec_702_115__002`
- **Section**: `702.115` — Filing of Applications
- **Chunk position**: 3 / 3
- **Program**: EA
- **Hierarchy**: (C) Application for Dependent Children.
- **Judge reason**: Directly addresses the application process for TAFDC (Transitional Cash Assistance Program) and describes what happens during the application interview, including the 24-hour activities and interview scheduling requirements.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.115 Filing of Applications > (C) Application for Dependent Children.

(C) Application for Dependent Children. The application for a dependent child must be filed by the grantee or the grantee’s authorized representative.
(D) Activities to be Completed within 24 Hours. If the worker cannot complete all parts of the application within 24 hours of filing, excluding weekends and holidays, he or she, or a Department representative shall, within 24 hours, complete the following activities:
(1) Log the case in to the Department’s system which includes recording the applicant's name, address, telephone number, and the date on which the application was filed;
(2) Ask the applicant about, and make provisions to meet, his or her immediate needs in accordance with 106 CMR 702.125;
(3) Inform the applicant of the steps that he or she must take to complete the application and of general verification requirements and have the applicant sign and date the first part of the application; and
(4) Schedule within seven calendar days any additional interviews that may be necessary to approve or deny the application within 30 calendar days.
(a) If the applicant fails to appear for the scheduled interview, the interview shall be rescheduled for the earliest possible date.
(b) If the applicant fails to appear for a second scheduled interview, the application shall be denied for failure to keep an appointment.
```

#### Rank 3 — PARTIAL (sim 0.589)

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

#### Rank 4 — PARTIAL (sim 0.553)

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

#### Rank 5 — PARTIAL (sim 0.566)

- **Chunk ID**: `cmr_sec_702_120__004`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 5 / 9
- **Program**: EA
- **Hierarchy**: (F) Immediate Needs.
- **Judge reason**: Addresses what happens at the application interview (immediate needs assessment) but does not explain how to apply for TAFDC or the overall application process.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (F) Immediate Needs.

(F) Immediate Needs. At the intake interview, or within 24 hours of the filing of the application if the intake interview cannot be held immediately, the worker must ask the applicant if he or she is in immediate need of food, shelter (including rent, fuel and utilities) or medical care. If so, and the applicant appears to be eligible based on the information available, the worker shall inform the applicant of the option to receive an advance on the cash benefits:
(1) An applicant has the option to receive:
(a) a shelter voucher;
(b) a food voucher, if he or she appears to be ineligible for SNAP benefits;
(c) expedited SNAP benefits through EBT if he or she appears to be eligible for SNAP benefits; and/or
(d) a temporary MassHealth card, if needed.
(2) If any of the above is requested, and the applicant appears to be eligible, the worker shall authorize:
(a) the food and/or shelter vouchers immediately;
(b) expedited SNAP benefits through an EBT transaction immediately; and/or
(c) the Temporary MassHealth card within one working day of the request. The amounts to be authorized for food and shelter vouchers are in the table below: RENT OR MORTGAGE Unheated Facility $102.00 Heated Facility 126.30 FUEL 27.90 UTILITIES 18.60 FOOD (Individual) 41.80
```

