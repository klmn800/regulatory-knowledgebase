# CMR Retrieval Benchmark — judge-baseline

**Run**: 2026-05-04T10:25:26  
**Source**: cmr  
**Label**: judge-baseline  
**Top-N retrieved + judged**: 5  
**Judge model**: `claude-haiku-4-5-20251001`  
**Methodology**: LLM-as-judge — Claude Haiku rates each chunk RELEVANT / PARTIAL / IRRELEVANT.  
**Benchmark**: CMR retrieval benchmark v2 — covers all 18 chapters, mixed difficulty, includes adversarial cases for hybrid/rerank testing  

## Summary

| Metric | Value | Notes |
|---|---|---|
| Relevance@1 | 21/37 (57%) | Did rank 1 = RELEVANT? |
| Relevant@5 (avg) | 1.57 / 5 | Avg # of RELEVANT chunks in top 5 |
| Useful@5 (avg) | 4.54 / 5 | Avg # of (RELEVANT or PARTIAL) chunks in top 5 |
| Mean rank-weighted score | 1.766 / 2.7 | Sum of (weight × score) over top 5; weights [1.0, 0.7, 0.5, 0.3, 0.2]; score RELEVANT=1.0 / PARTIAL=0.5 / IRRELEVANT=0.0 |

## Quick Summary Table

| # | ID | Topic | Rank-1 Judge | Rank-1 Sim Score | Relevant@5 | Useful@5 | RW |
|---|---|---|---|---|---|---|---|
| 1 | cmr_001 | SNAP asset limit | **PARTIAL** | 0.486 | 0 | 3 | 0.85 |
| 2 | cmr_002 | SNAP vehicle exclusion | **PARTIAL** | 0.397 | 1 | 3 | 1.35 |
| 3 | cmr_003 | SNAP shelter deduction | RELEVANT | 0.537 | 3 | 5 | 2.45 |
| 4 | cmr_004 | SNAP self-employment income | RELEVANT | 0.580 | 3 | 5 | 2.30 |
| 5 | cmr_005 | SNAP excluded income | **PARTIAL** | 0.535 | 1 | 5 | 1.45 |
| 6 | cmr_006 | SNAP ABAWD exemptions | RELEVANT | 0.513 | 1 | 5 | 1.85 |
| 7 | cmr_007 | SNAP application processing time | **PARTIAL** | 0.476 | 1 | 5 | 1.60 |
| 8 | cmr_008 | SNAP application filing | RELEVANT | 0.582 | 3 | 5 | 2.35 |
| 9 | cmr_009 | SNAP noncitizen eligibility | RELEVANT | 0.540 | 5 | 5 | 2.70 |
| 10 | cmr_010 | SNAP restoration | **PARTIAL** | 0.505 | 2 | 5 | 1.75 |
| 11 | cmr_011 | SNAP recertification | RELEVANT | 0.622 | 1 | 5 | 1.85 |
| 12 | cmr_012 | SNAP categorical eligibility | RELEVANT | 0.468 | 2 | 5 | 2.20 |
| 13 | cmr_013 | SSP eligibility | **PARTIAL** | 0.446 | 2 | 5 | 1.95 |
| 14 | cmr_014 | SSP payment standards | RELEVANT | 0.492 | 1 | 4 | 1.75 |
| 15 | cmr_015 | fair hearings general | **PARTIAL** | 0.444 | 2 | 5 | 1.85 |
| 16 | cmr_016 | hearing time limits | RELEVANT | 0.444 | 2 | 5 | 2.00 |
| 17 | cmr_017 | IPV definition | RELEVANT | 0.460 | 1 | 5 | 1.85 |
| 18 | cmr_018 | SNAP IPV penalties | RELEVANT | 0.592 | 2 | 5 | 2.10 |
| 19 | cmr_019 | TAFDC vs EAEDC | **PARTIAL** | 0.572 | 0 | 5 | 1.35 |
| 20 | cmr_020 | TAFDC 24-month limit | RELEVANT | 0.509 | 2 | 5 | 2.00 |
| 21 | cmr_021 | TAFDC work program | RELEVANT | 0.600 | 3 | 5 | 2.30 |
| 22 | cmr_022 | TAFDC asset limit | **PARTIAL** | 0.437 | 0 | 2 | 0.75 |
| 23 | cmr_023 | EAEDC disability | **PARTIAL** | 0.646 | 2 | 5 | 1.75 |
| 24 | cmr_024 | ESP overview | **PARTIAL** | 0.473 | 2 | 5 | 1.70 |
| 25 | cmr_025 | FEP overview | RELEVANT | 0.645 | 2 | 5 | 2.20 |
| 26 | cmr_026 | TAFDC MassHealth | **PARTIAL** | 0.508 | 0 | 4 | 1.20 |
| 27 | cmr_027 | TAFDC overpayments | RELEVANT | 0.506 | 1 | 5 | 1.85 |
| 28 | cmr_028 | identity verification | RELEVANT | 0.430 | 3 | 5 | 2.45 |
| 29 | cmr_029 | SNAP household composition | RELEVANT | 0.515 | 3 | 5 | 2.25 |
| 30 | cmr_030 | SNAP benefit calculation | **PARTIAL** | 0.464 | 0 | 5 | 1.35 |
| 31 | cmr_031 | section number lookup | **IRRELEVANT** | 0.243 | 0 | 1 | 0.15 |
| 32 | cmr_032 | ADH acronym | RELEVANT | 0.401 | 3 | 5 | 2.10 |
| 33 | cmr_033 | EPSDT acronym | RELEVANT | 0.405 | 1 | 1 | 1.00 |
| 34 | cmr_034 | PA household defined term | **PARTIAL** | 0.514 | 1 | 5 | 1.70 |
| 35 | cmr_035 | EDP defined term | RELEVANT | 0.499 | 1 | 5 | 1.85 |
| 36 | cmr_036 | SNAP allowed uses | RELEVANT | 0.531 | 1 | 5 | 1.85 |
| 37 | cmr_037 | TCAP application interview | **PARTIAL** | 0.554 | 0 | 5 | 1.35 |

---

## Per-Question Detail

Top 5 results per question with judge verdicts and full chunk text. Use this to spot-check whether the judge's rating makes sense.

### cmr_001 — SNAP asset limit (rank-1: PARTIAL)

**Question**: How much can a SNAP household have in bank accounts  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.110`  
**Notes**: 363.110 Asset Eligibility Limits  
**Scores**: Relevant@5 = 0, Useful@5 = 3, rank-weighted = 0.85  

#### Rank 1 — PARTIAL (sim 0.486)

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

#### Rank 2 — IRRELEVANT (sim 0.464)

- **Chunk ID**: `cmr_sec_363_150__000`
- **Section**: `363.150` — Transfer of Assets
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: This chunk discusses transfer of asset rules and categorical eligibility, not the asset/bank account limits for SNAP households.

```
106 CMR 363 > FINANCIAL > 363.150 Transfer of Assets

The transfer of asset rules do not apply to categorically eligible households as defined in 106 CMR 365.180: Categorically Eligible Assistance Units. The transfer of asset rules will be applied to any household which contains a member disqualified from receiving SNAP benefits. Non-SSI elder and/or disabled households with income above the Categorical Eligibility Gross Income standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards will also be subject to transfer of asset rules.
```

#### Rank 3 — PARTIAL (sim 0.457)

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

#### Rank 4 — IRRELEVANT (sim 0.452)

- **Chunk ID**: `cmr_sec_361_370__001`
- **Section**: `361.370` — Documentation and Control of Authorized Representatives
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (A) The household has freely requested the assistance of the authorized repre...
- **Judge reason**: This chunk discusses authorized representatives and benefit verification, not asset or bank account limits for SNAP households.

```
106 CMR 361 > THE > 361.370 Documentation and Control of Authorized Representatives > (A) The household has freely requested the assistance of the authorized repre...

(A) The household has freely requested the assistance of the authorized representative;
(B) The household's circumstances are correctly represented and the household is receiving the correct amount of SNAP benefits; and
```

#### Rank 5 — PARTIAL (sim 0.446)

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


### cmr_002 — SNAP vehicle exclusion (rank-1: PARTIAL)

**Question**: What vehicles are exempt from the SNAP asset test  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.140`  
**Notes**: 363.140 Noncountable Assets  
**Scores**: Relevant@5 = 1, Useful@5 = 3, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.397)

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

#### Rank 2 — PARTIAL (sim 0.386)

- **Chunk ID**: `cmr_sec_365_120__004`
- **Section**: `365.120` — Determining Eligibility and Benefit Level
- **Chunk position**: 5 / 6
- **Program**: SNAP
- **Hierarchy**: (B) Asset Standards for PA Households.
- **Judge reason**: The chunk discusses asset standards for PA households and references 106 CMR 363.110 for asset eligibility limits, but does not specifically identify which vehicles are exempt from the SNAP asset test.

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

#### Rank 3 — RELEVANT (sim 0.383)

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

#### Rank 4 — IRRELEVANT (sim 0.370)

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

#### Rank 5 — IRRELEVANT (sim 0.366)

- **Chunk ID**: `cmr_sec_365_420__000`
- **Section**: `365.420` — Migrant Farm Laborers
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Definition.
- **Judge reason**: This chunk addresses asset rules for migrant farm laborers specifically, not vehicle exemptions from the SNAP asset test.

```
106 CMR 365 > SPECIAL > 365.420 Migrant Farm Laborers

(A) Definition. Seasonal migrant farm laborers are individuals who move from one region or locale to another to engage in or seek seasonal farm, land, or crop cultivation activities.
(B) Assets. Special care should be taken in dealing with migrants to determine if there are out-of-state assets or income from real property in the migrant's home-base area. For example, a migrant, who claims Texas as a home-base area and who is applying for SNAP in Massachusetts should be asked about the assets in both Texas and Massachusetts. Each applicant household is permitted one home and lot as an exemption from assets. If the applicant has a home and lot in Texas and does not own a residence in Massachusetts, the Texas home will be exempt as an asset. Shelter costs for the home when not occupied by the household because of employment may be allowed under certain circumstances. To be included in the household's shelter costs, the household must intend to return; the home must not be leased or rented; and the current occupants of the home, if any, must not be claiming the shelter costs for SNAP purposes. Verification requirements for expenses of the home not occupeid by the client are discussed in 106 CMR 364.450(B): Other Expenses. The worker should explore the possibility that out-of-state real property is being rented or is producing income in some way. If such property is producing income, such income must be added to all other household income in
```


### cmr_003 — SNAP shelter deduction (rank-1: RELEVANT)

**Question**: What is the SNAP shelter deduction  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364.400` — judge picked rank-1 RELEVANT chunk in section `364.400` (section-author intuition agrees)  
**Notes**: 364.400 Shelter/Excess Shelter Deduction  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.537)

- **Chunk ID**: `cmr_sec_364_400__009`
- **Section**: `364.400` — Determining Deductions
- **Chunk position**: 10 / 13
- **Program**: SNAP
- **Hierarchy**: (G) Shelter Deduction.
- **Judge reason**: The chunk directly defines the SNAP shelter deduction, explaining what it is, how it's calculated, what expenses qualify, and any applicable limits or exceptions.

```
106 CMR 364 > DETERMINING > 364.400 Determining Deductions > (G) Shelter Deduction.

(G) Shelter Deduction. A deduction is allowed for monthly shelter expenses and utility costs in excess of 50% of the household's income after all the above deductions have been allowed. This shelter deduction amount is posted at www.mass.gov/dta. Paper copies are available upon request. This limit on the shelter deduction amount does not apply if the household contains a member who is elderly or disabled in accordance with 106 CMR 361.210: Elderly or Disabled Individuals.
(1) Shelter Expenses.
(a) Continuing charges for the shelter occupied by the household, including rent and mortgage payments, or other continuing charges leading to the ownership of shelter, such as loan repayments for the purchase of a mobile home, including interest on such payments, or condominium fees; NON-TEXT PAGE
(b) Property taxes, state and local assessments, and insurance on the structure itself, but not the separate expense of insuring furniture or personal belongings;
(c) Shelter expenses as described in 106 CMR 364.400(G)(1)(a) and (b) for a home not actually occupied by the household because of employment or training away from home, illness, or abandonment of the home due to natural disaster or casualty loss. Shelter expenses for a vacated home shall be included in the shelter deduction if the household intends to return to the home, the current occupants of the home, if any, are not claiming a shelter deduction for SNAP purposes, and the home is not leased or rented
```

#### Rank 2 — RELEVANT (sim 0.535)

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

#### Rank 3 — RELEVANT (sim 0.505)

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

#### Rank 4 — PARTIAL (sim 0.499)

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

#### Rank 5 — PARTIAL (sim 0.498)

- **Chunk ID**: `cmr_sec_366_910__005`
- **Section**: `366.910` — Bay State CAP Households
- **Chunk position**: 6 / 12
- **Program**: SNAP
- **Hierarchy**: (F) Bay State CAP Benefit Calculation.
- **Judge reason**: The chunk explains how the shelter deduction is calculated for Bay State CAP households specifically, but does not address the general SNAP shelter deduction that the user is asking about.

```
106 CMR 366 > ADDITIONAL > 366.910 Bay State CAP Households > (F) Bay State CAP Benefit Calculation.

(F) Bay State CAP Benefit Calculation. The SSI income of the recipient, as well as any other unearned income, as reported on the SDX, will be used to calculate the monthly Bay State CAP benefit amount.
(1) Bay State CAP households receive the standard deduction for one person.
(2) The shelter deduction for each Bay State CAP household is calculated as follows:
(a) During the SSI interview, households claiming monthly shelter expenses equal to or greater than the high shelter standard will receive the high shelter standard. This amount is determined using a methodology approved by the USDA. The high shelter standard is posted at www.mass.gov/dta. Paper copies are available upon request.
(b) During the SSI interview, households claiming monthly shelter expenses less than the high shelter standard will receive the low shelter standard. This amount is determined using a methodology approved by the USDA. The low shelter standard is posted at www.mass.gov/dta. Paper copies are available upon request.
(c) All Bay State CAP AUs will receive the Bay State CAP Standard Utility Allowance. This amount is determined using a methodology approved by the USDA. The Bay State CAP SUA is posted at www.mass.gov/dta. Paper copies are available upon request.
(d) One half of the household's adjusted gross income will be subtracted from the sum of the appropriate standard shelter expense and the Bay State CAP SUA. The difference is the shelter deduction for the household.
```


### cmr_004 — SNAP self-employment income (rank-1: RELEVANT)

**Question**: How is self-employment income calculated for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.220` — judge picked rank-1 RELEVANT chunk in section `365.970` (section-author intuition disagrees with judge)  
**Notes**: 363.220 Earned Income  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.30  

#### Rank 1 — RELEVANT (sim 0.580)

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

#### Rank 2 — RELEVANT (sim 0.523)

- **Chunk ID**: `cmr_sec_363_220__000`
- **Section**: `363.220` — Countable Income
- **Chunk position**: 1 / 7
- **Program**: SNAP
- **Hierarchy**: (A) Earned Income.
- **Judge reason**: Directly explains how self-employment income is calculated for SNAP, including gross income, capital gains, and exclusions for cost of doing business.

```
106 CMR 363 > FINANCIAL > 363.220 Countable Income

For SNAP purposes, countable income must be categorized as either earned or unearned.
(A) Earned Income.
(1) Wages. All wages and salaries paid to an employee are counted as earned income.
(2) Self-employment. The total gross income from a self-employment enterprise, including the total gain from the sale of any capital goods or equipment related to the business, excluding the cost of doing business, is counted as earned income. Payments from roomers and boarders are classified as earned self-employment income. Income from rental property shall be considered earned self-employment income only if a household member actively engages in the management of the property an average of at least 20 hours per week.
```

#### Rank 3 — PARTIAL (sim 0.517)

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

#### Rank 4 — PARTIAL (sim 0.490)

- **Chunk ID**: `cmr_sec_365_920__000`
- **Section**: `365.920` — Work Requirements
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Hierarchy**: (A) Exemptions.
- **Judge reason**: The chunk addresses work requirements for self-employed individuals but does not explain how self-employment income itself is calculated for SNAP eligibility purposes.

```
106 CMR 365 > SPECIAL > 365.920 Work Requirements

When all or part of a household's income is from self-employment, the household members must comply with SNAP Work Requirements in accordance with 106 CMR 362.300: Work Requirements unless exempt.
(A) Exemptions.
(1) The household member shall be exempt from the SNAP Work Requirements if actively engaged in his or her self-employment enterprise at least 30 hours per week, or if not working 30 hours per week, receiving weekly earnings equal to the hourly federal minimum wage multiplied by 30 hours.
(2) If the household member does not meet the criteria in 106 CMR 365.920(A)(1) and is not otherwise exempt under the provisions of 106 CMR 362.310: SNAP Employment and Training Program or 362.320: SNAP Work Program, the household member must comply with the Work Requirements.
```

#### Rank 5 — RELEVANT (sim 0.463)

- **Chunk ID**: `cmr_sec_365_970__000`
- **Section**: `365.970` — Determining Eligibility and Benefit Level for the Self-employed
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Averaged Income.
- **Judge reason**: The chunk directly explains how self-employment income is calculated for SNAP by describing the averaging method, gross income inclusion, cost exclusion, and division by months.

```
106 CMR 365 > SPECIAL > 365.970 Determining Eligibility and Benefit Level for the Self-employed

(A) Averaged Income. For the period of time over which self-employment is determined, add all gross self-employment income (including capital gains), exclude the cost of producing the self-employment income, and divide the self-employment income by the number of months over which the income will be averaged.
```


### cmr_005 — SNAP excluded income (rank-1: PARTIAL)

**Question**: What income is excluded from SNAP eligibility determination  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `363.230`  
**Notes**: 363.230 Noncountable Income  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.45  

#### Rank 1 — PARTIAL (sim 0.535)

- **Chunk ID**: `cmr_sec_364_500__001`
- **Section**: `364.500` — Determining Net Income
- **Chunk position**: 2 / 8
- **Program**: SNAP
- **Hierarchy**: (A) Total Gross Earned Income.
- **Judge reason**: The chunk mentions income exclusions exist but does not specify what those exclusions are, only that they should be subtracted from gross income.

```
106 CMR 364 > DETERMINING > 364.500 Determining Net Income > (A) Total Gross Earned Income.

(A) Total Gross Earned Income. To determine gross monthly earned income, add the gross monthly income earned by all household members (including self-employment income) less income exclusions. Net losses from a self-employed farmer shall be offset in accordance with 106 CMR 365.970(C): Determining Monthly SNAP Income.
```

#### Rank 2 — PARTIAL (sim 0.495)

- **Chunk ID**: `cmr_sec_361_200__003`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 4 / 5
- **Program**: SNAP
- **Hierarchy**: (B) The following individuals living with others or groups of individuals liv...
- **Judge reason**: The chunk discusses household composition and income limits for special circumstances involving elderly/disabled individuals, but does not address which types of income are excluded from SNAP eligibility determination.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (B) The following individuals living with others or groups of individuals liv...

(4) An individual who is both 60 years of age or older and disabled, as defined in 106 CMR 361.200(B)(4)(a) and (b), may be a separate SNAP household when living with others who purchase food and prepare meals for such individuals, if both the following conditions are true:
(a) The individual is unable to purchase food and prepare meals for himself or herself because he or she suffers from a disability considered permanent under the Social Security Act, or suffers from a non-disease-related, severe, permanent disability. If this disability is not obvious to the Department, verification of the disability is required. The verification shall be a statement from a physician that the individual is unable to purchase food and prepare meals because of the disability. Individuals meeting the disabled definition in 106 CMR 361.210 shall also be considered unable to purchase food and prepare meals for themselves.
(b) The gross income of the others, excluding the individual; and
1. his or her spouse;
2. his or her natural, adopted or stepchildren younger than 22 years old; or
3. a children younger than 18 years old living under his or her parental control, if applicable, in accordance with 106 CMR 363.220: Income, does not exceed 165% of the net income eligibility standard for a household of the appropriate size. See 106 CMR 364.975: Standards for Special Circumstances Involving an Elderly and Disabled Individual for these eligibility standards. Such income must be verified in
```

#### Rank 3 — PARTIAL (sim 0.478)

- **Chunk ID**: `cmr_sec_365_840__000`
- **Section**: `365.840` — Determining Eligibility and Benefit Level for Expedited Service Households
- **Program**: SNAP
- **Judge reason**: The chunk discusses which income must be considered for SNAP eligibility rather than which income is excluded, and focuses specifically on expedited service households rather than general exclusions.

```
106 CMR 365 > SPECIAL > 365.840 Determining Eligibility and Benefit Level for Expedited Service Households

All income received or reasonably expected to be received in the month of application must be considered when determining SNAP eligibility and benefit level. For Destitute (Migrant) Households, income already received during the month of application must be considered when determining eligibility and benefit level. Income anticipated to be received after the application has been made shall be disregarded. If a travel advance has been received during the month of application, it shall be disregarded if it is considered a reimbursement. If it is considered by written contract as an advance on wages to be earned later, the travel advance shall be considered income. The provisions of 106 CMR 364.650: Prorating Initial Month's Benefits concerning the proration of initial month's benefits shall apply to all expedited service households.
```

#### Rank 4 — PARTIAL (sim 0.477)

- **Chunk ID**: `cmr_sec_363_210__000`
- **Section**: `363.210` — Verification of Income
- **Chunk position**: 1 / 8
- **Program**: SNAP
- **Hierarchy**: (A) Initial Application.
- **Judge reason**: Discusses verification of income for SNAP eligibility but does not address which types of income are excluded from the eligibility determination.

```
106 CMR 363 > FINANCIAL > 363.210 Verification of Income

(A) Initial Application. All gross nonexempt income shall be verified prior to certifying a household as eligible to participate in SNAP. However, when all attempts to verify the income have been unsuccessful because the third party providing the income has failed to cooperate, and all other sources of verification are unavailable, the Department shall determine an amount to be used for certification purposes based on the best available information. If the household has no income, a statement from the household that it has no income shall be acceptable verification.
```

#### Rank 5 — RELEVANT (sim 0.474)

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

#### Rank 1 — RELEVANT (sim 0.513)

- **Chunk ID**: `cmr_sec_362_320__002`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Hierarchy**: (B) Exemptions.
- **Judge reason**: The chunk directly lists the specific ABAWD work requirement exemptions including age, pregnancy, living with children, and waived areas.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (B) Exemptions.

(B) Exemptions. Able-bodied Adults without Dependents are exempt from the ABAWD work program requirements if they meet the exemption criteria of 106 CMR 362.310(C). The individuals listed below are also exempt from the ABAWD work program requirements:
(1) Age. Persons younger than 18 years old or 50 years of age or older;
(2) Pregnant Women. A pregnant woman at any stage of pregnancy;
(3) Adults Living with Children Younger than 18 Years Old. Persons residing in a household where a household member is younger than 18 years old, even if the household member who is younger than 18 years old is not eligible for SNAP benefits; and
(4) Resident of a Waived Area. A person who otherwise would be required to participate in the ABAWD work program is exempt if living in an area of the state exempted by the United States Department of Agriculture.
```

#### Rank 2 — PARTIAL (sim 0.413)

- **Chunk ID**: `cmr_sec_362_300__000`
- **Section**: `362.300` — Work Requirements
- **Program**: SNAP
- **Judge reason**: The chunk mentions ABAWD work requirements and references where exemptions are found (106 CMR 362.320) but does not actually list or describe the specific exemptions themselves.

```
106 CMR 362 > NONFINANCIAL > 362.300 Work Requirements

As a condition of eligibility, nonexempt household members between 16 and 59 years of age must comply with the mandatory SNAP work requirements found at 106 CMR 362.310(A). Failure to comply with these requirements without good cause will result in disqualification in accordance with 106 CMR 367.800: Disqualification Penalties. Good cause criteria are found at 106 CMR 362.330. Unless an exemption applies, household members between 18 and 49 years of age must also comply with the ABAWD work program requirements found at 106 CMR 362.320. Failure to comply with these requirements for three months in a three-year period without good cause may result in ineligibility. Good cause criteria are found at 106 CMR 362.320(C).
```

#### Rank 3 — PARTIAL (sim 0.412)

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

#### Rank 4 — PARTIAL (sim 0.383)

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

#### Rank 5 — PARTIAL (sim 0.377)

- **Chunk ID**: `cmr_sec_362_320__001`
- **Section**: `362.320` — Able-bodied Adults Without Dependents (ABAWD) Work Program
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) Mandatory Population and Requirements.
- **Judge reason**: The chunk discusses ABAWD work program requirements and participation options but does not address exemptions from those requirements.

```
106 CMR 362 > NONFINANCIAL > 362.320 Able-bodied Adults Without Dependents (ABAWD) Work Program > (A) Mandatory Population and Requirements.

(3) Provide information to the Department regarding employment status or job availability when requested; and
(4) Any SNAP household member currently meeting his or her ABAWD work program requirement may volunteer to participate in an Employment and Training Program as described in 106 CMR 362.310(B) if a slot is available.
```


### cmr_007 — SNAP application processing time (rank-1: PARTIAL)

**Question**: How long does DTA have to process a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.080`  
**Notes**: 361.080 Prompt Action; baseline v1 expected 361 broadly, this v2 narrows it  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.60  

#### Rank 1 — PARTIAL (sim 0.476)

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

#### Rank 2 — PARTIAL (sim 0.439)

- **Chunk ID**: `cmr_sec_361_120__000`
- **Section**: `361.120` — Date of Application
- **Program**: SNAP
- **Judge reason**: This chunk defines when an application date is established but does not address the processing timeline or how long DTA takes to process the application.

```
106 CMR 361 > THE > 361.120 Date of Application

For households consisting only of SSI applicants or recipients that apply for SNAP benefits at an SSA office, the household's date of application is the date the signed SNAP application is received by the SSA office. The SSA office shall date stamp each application on the date it is received to document the household's date of application. For all other households, the household's date of application is the date an identifiable SNAP application is received by the Department through the online application, the DTA Document Processing Center or at a Department local office, except that when an application is not received by 5:00 P.M. on a business day or is received on a weekend or holiday, the application date will be the next business day. The Department shall date stamp each application on the date it is received to document the household's date of application.
```

#### Rank 3 — RELEVANT (sim 0.433)

- **Chunk ID**: `cmr_sec_361_080__000`
- **Section**: `361.080` — Prompt Action
- **Program**: SNAP
- **Judge reason**: Directly states that DTA must process SNAP applications and issue benefits within 30 calendar days of application, which directly answers the user's question about processing timeframes.

```
106 CMR 361 > THE > 361.080 Prompt Action

Eligible households must be given an opportunity to participate in the Supplemental Nutrition Assistance Program (SNAP) no later than 30 calendar days following their date of application. An opportunity to participate consists of the Department's issuing SNAP benefits through the EBT system before the 30-day processing standard expires. Expedited service shall be provided to households in accordance with 106 CMR 365.800: Expedited Service. Benefits must be provided retroactively to the date of application for households that complete the application process within the required time frame and are eligible to receive benefits in the month of application.
```

#### Rank 4 — PARTIAL (sim 0.403)

- **Chunk ID**: `cmr_sec_366_920__000`
- **Section**: `366.920` — Regular SSI/SNAP Households
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: The chunk mentions SNAP application procedures for SSI households and references a 30-day processing timeframe for disability determinations, but does not directly state the general SNAP application processing timeline that the user is asking about.

```
106 CMR 366 > ADDITIONAL > 366.920 Regular SSI/SNAP Households

In accordance with 7 USC 2020(i) and SSA policy, SSA will take a regular SNAP application for pure SSI households who do not meet the Bay State CAP criteria or who meet Bay State CAP criteria but are subject to a disability determination that will take longer than 30 days to process. The SSA claims representative will also screen for expedited service. SSI applicants/recipients who qualify for expedited service may complete a SNAP application at SSA, the Department or online for regular SNAP benefits. Any obligation attributed to SSA in 106 CMR 366.920 is included for informational purposes only. Appeal rights regarding SSI eligibility or benefit level must be pursued through SSA. The following procedures shall apply for regular SSI/SNAP households served by the Department.
```

#### Rank 5 — PARTIAL (sim 0.397)

- **Chunk ID**: `cmr_sec_366_330__000`
- **Section**: `366.330` — Department Responsibilities
- **Program**: SNAP
- **Judge reason**: Addresses processing timelines for recertification applications but not initial SNAP applications, which is what the user asked about.

```
106 CMR 366 > ADDITIONAL > 366.330 Department Responsibilities

When a household makes a timely application for recertification and fulfills its recertification responsibilities, the Department must certify or deny the application and send the household a notice of the eligibility determination by the end of the current certification period.
(A) Scheduling Interviews. The Department shall schedule a recertification interview in accordance with 106 CMR 366.320(B).
(B) Time Standards for Providing Benefits to Eligible Households. Households that timely reapplied after having been given a Notice of Expiration at the time of certification shall be notified of their eligibility or ineligibility and provided an opportunity to participate (if eligible) no later than 30 days after the household was last issued a SNAP allotment. All other households that timely recertify shall be provided with an opportunity to participate by their normal issuance date in the month following receipt of the application.
```


### cmr_008 — SNAP application filing (rank-1: RELEVANT)

**Question**: How does someone file a SNAP application  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.100` — judge picked rank-1 RELEVANT chunk in section `361.110` (section-author intuition disagrees with judge)  
**Notes**: 361.100 Filing an Application  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.35  

#### Rank 1 — RELEVANT (sim 0.582)

- **Chunk ID**: `cmr_sec_361_110__000`
- **Section**: `361.110` — Where to File
- **Program**: SNAP
- **Judge reason**: Directly addresses where and how to file a SNAP application, including the various methods available (in person, mail, fax, online).

```
106 CMR 361 > THE > 361.110 Where to File

The application must be filed with the Department and may be submitted in person by the applicant, or by an authorized representative, or by mail, fax or the online application. Households consisting only of SSI applicants or recipients may file a SNAP application at an SSA office in accordance with 106 CMR 361.190.
```

#### Rank 2 — RELEVANT (sim 0.540)

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

#### Rank 3 — PARTIAL (sim 0.491)

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

#### Rank 4 — RELEVANT (sim 0.488)

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

#### Rank 5 — PARTIAL (sim 0.470)

- **Chunk ID**: `cmr_sec_361_130__000`
- **Section**: `361.130` — Household Right to Same Day Filing
- **Program**: SNAP
- **Judge reason**: Addresses same-day filing rights and requirements but doesn't explain the actual process or steps for filing a SNAP application.

```
106 CMR 361 > THE > 361.130 Household Right to Same Day Filing

Households shall be advised of their right to same day filing of the application. Each office shall post signs that explain the application processing standards and the household's right to same day filing. In addition, the household shall be informed that it does not have to be interviewed before filing its application and that it may file an incomplete application as long as the form contains the applicant's name and address and is signed by a responsible member of the household or the household's authorized representative. Department staff shall encourage households to file an application the same day the household or its representative contacts the Department in person or by telephone and expresses an interest in obtaining SNAP benefits.
```


### cmr_009 — SNAP noncitizen eligibility (rank-1: RELEVANT)

**Question**: Can a noncitizen receive SNAP benefits  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `362.220` — judge picked rank-1 RELEVANT chunk in section `362.220` (section-author intuition agrees)  
**Notes**: 362.220 Noncitizens (CMR 362.200 series covers citizenship)  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.540)

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

#### Rank 2 — RELEVANT (sim 0.522)

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

#### Rank 3 — RELEVANT (sim 0.520)

- **Chunk ID**: `cmr_sec_362_220__000`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 1 / 12
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses whether noncitizens can receive SNAP benefits by explaining the eligibility requirements, verification procedures, and conditions under which noncitizens may or may not qualify.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens

A noncitizen applying for SNAP benefits and claiming an eligible noncitizen status must verify that he or she is present in the United States (U.S.) under one of the noncitizen statuses provided in 106 CMR 362.220(A). The status of a noncitizen must be verified at certification, at recertification or whenever the status of the noncitizen changes or is questionable. Verification of an eligible noncitizen status must be presented before the determination of SNAP eligibility. When a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide information about, or acceptable verification of, his or her eligible noncitizen status, that household member shall be ineligible. In such cases the Department shall not continue efforts to obtain documentation. Also, if a noncitizen applying for SNAP benefits indicates an inability or unwillingness to provide, or apply for, a Social Security Number due to immigration status he or she is ineligible. The Department shall not continue efforts to obtain documentation. SNAP eligibility will be determined in accordance with 106 CMR 365.520(A) for the household members who do verify an eligible noncitizen status. The Commissioner or designee is required to report to the United States Citizenship and Immigration Services (USCIS) information about noncitizens "known to be in the U.S. unlawfully" as defined in 106 CMR 362.240. SNAP - Eligible Noncitizen Status. A noncitizen's eligibility for SNAP benefits depends on
```

#### Rank 4 — RELEVANT (sim 0.520)

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

#### Rank 5 — RELEVANT (sim 0.504)

- **Chunk ID**: `cmr_sec_362_220__001`
- **Section**: `362.220` — Noncitizens
- **Chunk position**: 2 / 12
- **Program**: SNAP
- **Hierarchy**: (A) A qualified noncitizen is a person who, at the time the person applies fo...
- **Judge reason**: Directly addresses which noncitizens can receive SNAP benefits by listing the specific qualified noncitizen categories eligible for the program.

```
106 CMR 362 > NONFINANCIAL > 362.220 Noncitizens > (A) A qualified noncitizen is a person who, at the time the person applies fo...

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


### cmr_010 — SNAP restoration (rank-1: PARTIAL)

**Question**: When are SNAP benefits restored after an agency error  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366`  
**Notes**: BROAD — chapter 366 covers changes/restoration; specific section may be 366.500  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.75  

#### Rank 1 — PARTIAL (sim 0.505)

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

#### Rank 2 — PARTIAL (sim 0.442)

- **Chunk ID**: `cmr_sec_365_180__007`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 8 / 9
- **Program**: SNAP
- **Hierarchy**: (G) Determination of Eligibility.
- **Judge reason**: The chunk discusses benefit restoration in specific categorical eligibility scenarios (EAEDC/SSI) but does not address the general question of when SNAP benefits are restored after agency error.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (G) Determination of Eligibility.

If a determination of eligibility for EAEDC or SSI benefits is postponed beyond 30 days, or an application for EAEDC or SSI benefits is denied, the SNAP application should be processed immediately as an NPA case. Any changes shall be initialed and the updated application signed by the authorized representative or authorized household member. The Department shall act on reevaluating the original household's EAEDC or SSI eligibility. When applicable, the household shall be advised on the notice of denial to inform the Department if any pending application for EAEDC or SSI benefits is subsequently approved.
(3) Providing Benefits. Any household determined to be categorically eligible within the 30-day SNAP processing timeframe shall be provided benefits back to the date of the SNAP application or, in the case of a joint application, back to the date of the EAEDC or SSI application. Benefits shall be prorated in accordance with 106 CMR 364.650: Prorating Initial Month's Benefits. If a household whose determination of eligibility for EAEDC or SSI benefits has been postponed beyond 30 days and whose SNAP application has been processed as an NPA case subsequently gets approved for EAEDC or SSI benefits, the SNAP benefits must be recalculated based on the excess medical, uncapped shelter, and net income (elderly/disabled) provisions. Any SNAP benefits owed back to the date of the SNAP application or from the
```

#### Rank 3 — RELEVANT (sim 0.407)

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

#### Rank 4 — RELEVANT (sim 0.403)

- **Chunk ID**: `cmr_sec_361_700__001`
- **Section**: `361.700` — Timeliness Standards for Processing
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Hierarchy**: (A) Eligible Assistance Units.
- **Judge reason**: Directly addresses when SNAP benefits are restored after agency error (retroactive to date of application when timeliness standard is missed)

```
106 CMR 361 > THE > 361.700 Timeliness Standards for Processing > (A) Eligible Assistance Units.

(A) Eligible Assistance Units. Households that are found to be eligible must be provided an opportunity to participate within 30 calendar days following the date of application. An opportunity to participate consists of the Department's issuing SNAP benefits via the EBT system before the 30-day processing standard expires. When the Department misses this timeliness standard and the household is eligible for SNAP benefits in the month of application, SNAP benefits must be provided retroactive to the date of application.
```

#### Rank 5 — PARTIAL (sim 0.399)

- **Chunk ID**: `cmr_sec_364_900__003`
- **Section**: `364.900` — Delivery of Benefits
- **Chunk position**: 4 / 8
- **Program**: SNAP
- **Hierarchy**: (C) Replacement of Benefits after Household Misfortune.
- **Judge reason**: This chunk addresses benefit replacement but only for household misfortune situations, not for agency errors as the question asks.

```
106 CMR 364 > DETERMINING > 364.900 Delivery of Benefits > (C) Replacement of Benefits after Household Misfortune.

(C) Replacement of Benefits after Household Misfortune. The Department shall replace SNAP benefits when a household's food purchased with benefits has been destroyed in a household misfortune as defined in 106 CMR 360.030: Definitions when the following conditions are met.
(1) Conditions of Replacement.
(a) The household must report the destruction of food purchased with SNAP benefits to the Department within ten days of the date of the destruction.
(b) The household must sign a statement attesting to the destruction of the food purchased with SNAP benefits and the reason for the replacement. It shall also state that the household is aware of the penalties for intentional misrepresentation of facts, including the penalties for Intentional Program Violations and a charge of perjury for making a false claim. The statement must be received by the Department within ten days of the date of the report. If the tenth day falls on a weekend or holiday, and the statement is received the day after the weekend or holiday, the Department shall consider the statement timely received.
(c) The Department must verify the destruction occurred in a household misfortune through a collateral contact, documentation from a community agency (e.g., fire department, police department, Red Cross), or a home visit.
```


### cmr_011 — SNAP recertification (rank-1: RELEVANT)

**Question**: What are the SNAP recertification requirements  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `366` — judge picked rank-1 RELEVANT chunk in section `366.300` (section-author intuition agrees)  
**Notes**: BROAD — chapter 366 generally; could pull from 365.150 for PA households  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.622)

- **Chunk ID**: `cmr_sec_366_300__000`
- **Section**: `366.300` — Recertification
- **Program**: SNAP
- **Judge reason**: Directly addresses SNAP recertification requirements by outlining the core requirements: submitting a new application, being interviewed, and providing required verification.

```
106 CMR 366 > ADDITIONAL > 366.300 Recertification

A household's SNAP benefits shall not continue beyond the certification period, unless the household has been recertified. To recertify, the household must submit a new application, be interviewed, and provide required verification in accordance with the timeliness standards set forth in 106 CMR 366.320. Those households that timely recertify and are found eligible shall be entitled to uninterrupted benefits. The following sections list the responsibilities of the household and the Department in the recertification process.
```

#### Rank 2 — PARTIAL (sim 0.603)

- **Chunk ID**: `cmr_sec_365_190__004`
- **Section**: `365.190` — Transitional Benefits Alternative
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (E) Recertification Requirements for TBA Households.
- **Judge reason**: Addresses recertification requirements but only for a specific subset (TBA households) rather than general SNAP recertification requirements, and references another regulation for the actual notification details.

```
106 CMR 365 > SPECIAL > 365.190 Transitional Benefits Alternative > (E) Recertification Requirements for TBA Households.

(E) Recertification Requirements for TBA Households. The TBA household must recertify for SNAP at the end of the TBA period and will be notified to recertify in accordance with 106 CMR 366.310: Notification to Recertify.
```

#### Rank 3 — PARTIAL (sim 0.575)

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

#### Rank 4 — PARTIAL (sim 0.561)

- **Chunk ID**: `cmr_sec_366_310__000`
- **Section**: `366.310` — Notification to Recertify
- **Program**: SNAP
- **Judge reason**: The chunk addresses notification procedures for recertification rather than the actual recertification requirements themselves (eligibility criteria, documentation needed, frequency, etc.).

```
106 CMR 366 > ADDITIONAL > 366.310 Notification to Recertify

Households certified for one or two months shall receive, at the time of certification, a separate notice of recertification responsibilities entitled Notice of Expiration. Those households certified for three months or more (except public assistance households) shall receive a separate Notice of Expiration in the month prior to the last month of their certification period. This notice will be mailed by the Department no earlier than the first day of the next-to-last month of certification or no later than the last day of the next-to-last month of certification. The contents of the notice are set forth in 106 CMR 364.840: Notice of SNAP Termination. Public assistance households shall receive a notice of recertification responsibilities prior to the end of the SNAP certification period. In some instances, these households are recertified for SNAP at the same time as their public assistance redetermination.
```

#### Rank 5 — PARTIAL (sim 0.544)

- **Chunk ID**: `cmr_sec_365_150__000`
- **Section**: `365.150` — Recertification Requirements for PA Households
- **Program**: SNAP
- **Judge reason**: Addresses recertification timing for PA households specifically but doesn't comprehensively cover general SNAP recertification requirements for all household types.

```
106 CMR 365 > SPECIAL > 365.150 Recertification Requirements for PA Households

PA households shall be recertified for SNAP benefits, to the extent possible, at the same time they have their eligibility reviewed for the cash assistance program. If a PA household has not had its PA eligibility reviewed by the end of the 11th month following its initial SNAP certification or last eligibility review, a Notice of SNAP Termination shall be sent to the household.
```


### cmr_012 — SNAP categorical eligibility (rank-1: RELEVANT)

**Question**: What is SNAP categorical eligibility  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365` — judge picked rank-1 RELEVANT chunk in section `365.180` (section-author intuition agrees)  
**Notes**: BROAD — chapter 365 special households; 365.180 in v1  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.468)

- **Chunk ID**: `cmr_sec_365_180__000`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 1 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk directly defines SNAP categorical eligibility by listing the specific household types that qualify and the conditions they must meet.

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

#### Rank 2 — RELEVANT (sim 0.468)

- **Chunk ID**: `cmr_sec_365_180__001`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk directly defines SNAP categorical eligibility by listing specific categories of households that qualify (SNAP-only TANF Service Elder/Disabled Households and SNAP-only TANF Service Adult Households) with their eligibility requirements.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (A) The following SNAP households are categorically eligible:

(5) SNAP-only TANF Service Elder/Disabled Households which include SNAP households consisting solely of non-SSI elders (60 years of age or older) and/or disabled individuals in accordance with SNAP disability standards at 106 CMR 361.210: Elderly or Disabled Individuals. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards; and
(6) SNAP-only TANF Service Adult Households include SNAP households consisting solely of adults between 19 and 59 years of age. These households must meet the Gross Monthly Categorically Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards. For purposes of 106 CMR 365.180(A)(1) through (3), authorized to receive means that an individual has been determined eligible for benefits and has been notified of this determination, even if benefits have been authorized but not received, authorized but not accessed, suspended or recouped, or not paid because they are less than a minimum amount. For purposes of 106 CMR 365.180(A)(4) through (6), a TANF Service includes receipt of the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure.
```

#### Rank 3 — PARTIAL (sim 0.452)

- **Chunk ID**: `cmr_sec_365_180__002`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Hierarchy**: (B) SSI, TAFDC and TANF
- **Judge reason**: The chunk discusses specific rules for categorical eligibility (ineligibility conditions and exceptions) but does not define what categorical eligibility itself is or explain the basic concept the user is asking about.

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

#### Rank 4 — PARTIAL (sim 0.450)

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

#### Rank 5 — PARTIAL (sim 0.445)

- **Chunk ID**: `cmr_sec_365_180__007`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 8 / 9
- **Program**: SNAP
- **Hierarchy**: (G) Determination of Eligibility.
- **Judge reason**: The chunk discusses procedures for categorically eligible households in SNAP but does not define what categorical eligibility actually is or explain the concept itself.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (G) Determination of Eligibility.

If a determination of eligibility for EAEDC or SSI benefits is postponed beyond 30 days, or an application for EAEDC or SSI benefits is denied, the SNAP application should be processed immediately as an NPA case. Any changes shall be initialed and the updated application signed by the authorized representative or authorized household member. The Department shall act on reevaluating the original household's EAEDC or SSI eligibility. When applicable, the household shall be advised on the notice of denial to inform the Department if any pending application for EAEDC or SSI benefits is subsequently approved.
(3) Providing Benefits. Any household determined to be categorically eligible within the 30-day SNAP processing timeframe shall be provided benefits back to the date of the SNAP application or, in the case of a joint application, back to the date of the EAEDC or SSI application. Benefits shall be prorated in accordance with 106 CMR 364.650: Prorating Initial Month's Benefits. If a household whose determination of eligibility for EAEDC or SSI benefits has been postponed beyond 30 days and whose SNAP application has been processed as an NPA case subsequently gets approved for EAEDC or SSI benefits, the SNAP benefits must be recalculated based on the excess medical, uncapped shelter, and net income (elderly/disabled) provisions. Any SNAP benefits owed back to the date of the SNAP application or from the
```


### cmr_013 — SSP eligibility (rank-1: PARTIAL)

**Question**: What is the State Supplement Program and who is eligible  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.120`  
**Notes**: 327.120 Eligibility for State Supplement Program  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.95  

#### Rank 1 — PARTIAL (sim 0.446)

- **Chunk ID**: `cmr_sec_327_010__000`
- **Section**: `327.010` — Authority for State Supplement Program
- **Program**: SSP
- **Judge reason**: Explains what SSP is and that Massachusetts offers it, but does not provide eligibility criteria details

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.010 Authority for State Supplement Program

The Supplemental Security Income (SSI) program is administered by the Social Security Administration (SSA) to provide financial assistance to eligible aged, disabled and blind individuals. States have the option to provide additional assistance through the State Supplement Program (SSP). Massachusetts has opted to provide this additional assistance. SSP is authorized under M.G.L. c. 6, § 131 and M.G.L. c. 118A and applicable federal law pertaining to the SSI program and agreements with the Commissioner of Social Security. 106 CMR 327.000 is promulgated and implemented in accordance with M.G.L. c. 30A, and applicable General Laws of Massachusetts.
```

#### Rank 2 — RELEVANT (sim 0.444)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk directly defines the State Supplement Program and clearly states who is eligible (individuals who receive SSI or don't qualify for SSI due to income), directly answering both parts of the user's question.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.100 Overview of State Supplement Program

SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 3 — RELEVANT (sim 0.375)

- **Chunk ID**: `cmr_sec_327_120__000`
- **Section**: `327.120` — Eligibility for State Supplement Program
- **Program**: SSP
- **Judge reason**: Directly explains what the State Supplement Program (SSP) is and specifies the eligibility criteria for who can receive it.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.120 Eligibility for State Supplement Program

An application for SSI serves is an application for SSP. There is no separate SSP application. Eligibility for SSP is determined after an eligibility determination for SSI is made by the Social Security Administration (SSA). The Department must accept the SSA determination. Individuals may be eligible for SSP if they are either:
(A) determined eligible for SSI; or
(B) determined not eligible for SSI solely due to income, but their countable income is less than the combined Federal Benefit Rate (FBR) and the appropriate SSP payment.
```

#### Rank 4 — PARTIAL (sim 0.285)

- **Chunk ID**: `cmr_sec_327_220__003`
- **Section**: `327.220` — State Living Arrangements
- **Chunk position**: 4 / 6
- **Program**: SSP
- **Hierarchy**: (C) State Living Arrangement C: Living in the Household of Another.
- **Judge reason**: The chunk discusses eligibility requirements and living arrangements under SSP but does not explain what the State Supplement Program is or provide comprehensive eligibility criteria.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.220 State Living Arrangements > (C) State Living Arrangement C: Living in the Household of Another.

(C) State Living Arrangement C: Living in the Household of Another. State Living Arrangement C includes an individual or couple living in the household of another and determined by the Social Security Administration to be receiving sufficient support to necessitate a reduction of a in the Federal SSI benefit rate.
```

#### Rank 5 — PARTIAL (sim 0.272)

- **Chunk ID**: `cmr_sec_327_220__000`
- **Section**: `327.220` — State Living Arrangements
- **Chunk position**: 1 / 6
- **Program**: SSP
- **Hierarchy**: (A) State Living Arrangement A: Full Cost of Living.
- **Judge reason**: The chunk discusses SSP benefit amounts based on living arrangements but does not explain what the State Supplement Program is or provide general eligibility criteria for the program.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.220 State Living Arrangements

An individual's SSP benefit amount is determined by their living arrangement.
(A) State Living Arrangement A: Full Cost of Living.
(1) State Living Arrangement A includes an individual who is in Federal Living Arrangement A and is:
(a) Living Alone included in those who live alone, are individuals who rent a room in a commercial rooming house which does not provide board or who live in a hotel. Also, individuals who rent only a room in a private residence are considered living alone if they do not use the residential kitchen facilities for preparation of his or her meals.
(b) Living only with his or her SSI or SSP eligible spouse.
(c) Living only with his or her SSI or SSP eligible spouse and his or her SSI or SSP ineligible children, none of whom receive public income maintenance payments. See 106 CMR 327.110(E).
(d) Living only with his or her SSI or SSP ineligible spouse and/or his or her SSI or SSP ineligible children, none of whom receive public income maintenance payments. For the purposes of 106 CMR 327.220(A)(1)(a) through (d), foster children placed with anyone other than their parents are not considered to be living with the foster parent.
```


### cmr_014 — SSP payment standards (rank-1: RELEVANT)

**Question**: What are the SSP payment standards  
**Program filter**: `['SSP']`  
**Expected section (for reference)**: `327.330` — judge picked rank-1 RELEVANT chunk in section `327.330` (section-author intuition agrees)  
**Notes**: 327.330 Payment Standards  
**Scores**: Relevant@5 = 1, Useful@5 = 4, rank-weighted = 1.75  

#### Rank 1 — RELEVANT (sim 0.492)

- **Chunk ID**: `cmr_sec_327_330__000`
- **Section**: `327.330` — Payment Standards
- **Program**: SSP
- **Judge reason**: The chunk directly addresses SSP payment standards by explaining how they are determined and where to find the specific payment amounts.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.330 Payment Standards

Payment amounts are based on Eligibility Category, State Living Arrangement, whether the client is eligible as an individual or as a member of an eligible couple and the amount of countable income. If countable income exceeds the Federal Benefit Rate (FBR), the amount exceeding the FBR is deducted from the SSP payment standard. Payment standards are available online at www.mass.gov/dta under the heading Key Resources/Program Eligibility Charts and Tables/SSI Program Payment Charts. Paper copies are available upon request.
```

#### Rank 2 — PARTIAL (sim 0.425)

- **Chunk ID**: `cmr_sec_327_100__000`
- **Section**: `327.100` — Overview of State Supplement Program
- **Program**: SSP
- **Judge reason**: The chunk explains that SSP payment levels are based on Eligibility Category, State Living Arrangement, and individual/couple status, but does not provide the actual payment standard amounts or rates.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.100 Overview of State Supplement Program

SSP provides state-funded financial assistance to individuals who receive SSI or who do not qualify for SSI due to income as provided by 106 CMR 327.120. No other individuals are eligible for SSP. SSP provides financial assistance to blind individuals through the authority of the Massachusetts Commission for the Blind and to aged and disabled individuals through the authority of the Department of Transitional Assistance. SSP clients must meet program criteria provided in 106 CMR 327.000. Such criteria are based on and should be interpreted in accordance with applicable Social Security law, regulations and relevant sub-regulatory materials, such as Social Security Rulings (SSRs), Program Operations Manual System (POMS), and Emergency Messages (EMs). In accordance with federal law, payment levels are based on Eligibility Category, State Living Arrangement and whether the client is considered an individual or a member of an eligible couple. See 20 CFR 416, Subpart T.
```

#### Rank 3 — PARTIAL (sim 0.418)

- **Chunk ID**: `cmr_sec_327_350__000`
- **Section**: `327.350` — Timing and Method of SSP Benefit Payments
- **Program**: SSP
- **Judge reason**: Addresses payment timing and minimum amounts but does not provide the actual SSP payment standards/benefit amounts that the user is asking about.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.350 Timing and Method of SSP Benefit Payments

SSP benefits are paid once a month. The Department shall determine the method of payment. Minimum Monthly Payment The minimum monthly payment for the SSP is $1.00. If the payment amount is greater than zero but less than $1.00, a payment of $1.00 will be issued.
```

#### Rank 4 — PARTIAL (sim 0.365)

- **Chunk ID**: `cmr_sec_327_340__000`
- **Section**: `327.340` — Date Benefits Begin
- **Program**: SSP
- **Judge reason**: The chunk discusses when SSP payments begin rather than what the actual payment standards (amounts) are.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.340 Date Benefits Begin

SSP benefit payments will begin as of the date SSI payments begin. For SSP-only eligible clients, SSP benefit payments will begin as of the first day of the month following the date of the SSI application.
```

#### Rank 5 — IRRELEVANT (sim 0.365)

- **Chunk ID**: `cmr_sec_327_400__000`
- **Section**: `327.400` — Overpayments
- **Program**: SSP
- **Judge reason**: The chunk discusses overpayment procedures and definitions rather than SSP payment standards or benefit amounts.

```
106 CMR 327 > ELIGIBILITY REQUIREMENTS FOR SSP > 327.400 Overpayments

An overpayment of SSP benefits exists when an SSP client receives assistance for which he or she is not eligible or the assistance exceeds the amount for which he or she was eligible. An overpayment of SSP benefits may result from Department error, payment of assistance pending implementation of a fair hearing decision upholding the Department's proposed action, client error, or misrepresentation or withholding of information. See 106 CMR 706.220.
```


### cmr_015 — fair hearings general (rank-1: PARTIAL)

**Question**: What is the fair hearing process at DTA  
**Program filter**: (none)  
**Expected section (for reference)**: `343.110`  
**Notes**: 343.110 General Description of the Fair Hearing Process; no program filter (343 is Hearings)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — PARTIAL (sim 0.444)

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

#### Rank 2 — RELEVANT (sim 0.427)

- **Chunk ID**: `cmr_sec_343_110__000`
- **Section**: `343.110` — General Description of the Fair Hearing Process
- **Program**: Hearings
- **Judge reason**: This chunk directly describes the fair hearing process at DTA, including its purpose, structure, and how it operates, which directly answers the user's question.

```
106 CMR 343 > FAIR HEARING RULES > 343.110 General Description of the Fair Hearing Process

The fair hearing process is an adjudicatory proceeding which allows dissatisfied applicants and clients and certain spouses, as well as certain sponsors of aliens, upon written request, to obtain a determination of the appropriateness of certain actions or inactions on the part of the Department, or of alleged coercive or otherwise improper conduct by a Department employee. The process is designed to secure and protect the interests of both the appellant and appropriate Department personnel and to ensure fair and equitable treatment for all involved. A hearing is conducted by an impartial hearing officer of DOH. The decision of the hearing officer is based only on evidence and testimony presented at the hearing. The hearing officer examines the facts, the law, and the other circumstances of the case presented by the parties to determine the legality and appropriateness of the disputed Department actions or decision of the Department. The hearing decision is binding upon the Department and is not subject to any review within the Department except in the case of a remand of the decision for a new hearing pursuant to 106 CMR 343.710.
```

#### Rank 3 — PARTIAL (sim 0.401)

- **Chunk ID**: `cmr_sec_343_010__000`
- **Section**: `343.010` — Purpose
- **Program**: Hearings
- **Judge reason**: Introduces the fair hearing rules and scope but doesn't describe the actual process or procedures involved in the hearing.

```
106 CMR 343 > FAIR HEARING RULES > 343.010 Purpose

106 CMR 343.00 sets forth the rules for hearings and appeals filed by applicants or clients dissatisfied with certain actions or inactions by the Department of Transitional Assistance. Scope 106 CMR 343.000 sets forth the exclusive rules for hearings and appeals filed by applicants, clients and, if applicable, any sponsors of aliens under the programs of Transitional Aid to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC) and State Supplement Program (SSP), and by clients or former clients and/or their spouses under M.G.L. c. 62D. Hearings and appeals arising under Supplemental Nutrition Assistance Program (SNAP) are governed by 106 CMR 367.000: Supplemental Nutrition Assistance Program: Violations, Hearings and Claims, excepting that matters not addressed therein shall be governed by 106 CMR 343.000. The Department may enter into interdepartmental service agreements with other state agencies to conduct hearings in accordance with 106 CMR 343.000.
```

#### Rank 4 — RELEVANT (sim 0.399)

- **Chunk ID**: `cmr_sec_343_310__000`
- **Section**: `343.310` — Scheduling
- **Program**: Hearings
- **Judge reason**: This chunk directly addresses a key procedural component of the DTA fair hearing process by explaining how hearings are scheduled and what accommodations are available.

```
106 CMR 343 > FAIR HEARING RULES > 343.310 Scheduling

Upon receipt of a request for a fair hearing, DOH will register the appeal, set a date for a hearing and so notify the appellant, the appropriate office of the Department, and if applicable, the Department employee against whom allegations of coercive or otherwise improper conduct have been made. DOH shall designate a hearing site accessible to the appellant. If the appellant has a disability which reasonably prevents his or her appearance at the designated site, he or she may request the hearing be held telephonically, at his or her home, or other accessible location.
```

#### Rank 5 — PARTIAL (sim 0.397)

- **Chunk ID**: `cmr_sec_702_600__000`
- **Section**: `702.600` — Appeals
- **Program**: EA
- **Judge reason**: The chunk acknowledges the fair hearing process exists and directs to the relevant regulation (106 CMR 343.000) but does not actually describe what the fair hearing process is.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.600 Appeals

Information regarding the appeal process, the applicant’s or client’s right to request a fair hearing, and the time standards governing appeal procedures are found in 106 CMR 343.000: Fair Hearing Rules.
```


### cmr_016 — hearing time limits (rank-1: RELEVANT)

**Question**: How long does someone have to request a fair hearing  
**Program filter**: (none)  
**Expected section (for reference)**: `343.140` — judge picked rank-1 RELEVANT chunk in section `343.140` (section-author intuition agrees)  
**Notes**: 343.140 Time Limits; could also pull 367.100 (SNAP hearing timing)  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.00  

#### Rank 1 — RELEVANT (sim 0.444)

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

#### Rank 2 — PARTIAL (sim 0.443)

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

#### Rank 3 — PARTIAL (sim 0.443)

- **Chunk ID**: `cmr_sec_702_600__000`
- **Section**: `702.600` — Appeals
- **Program**: EA
- **Judge reason**: The chunk acknowledges that time standards for fair hearing requests exist and directs to 106 CMR 343.000, but does not provide the actual timeframe the user is asking about.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.600 Appeals

Information regarding the appeal process, the applicant’s or client’s right to request a fair hearing, and the time standards governing appeal procedures are found in 106 CMR 343.000: Fair Hearing Rules.
```

#### Rank 4 — RELEVANT (sim 0.420)

- **Chunk ID**: `cmr_sec_367_100__000`
- **Section**: `367.100` — Time Period for Requesting Hearing
- **Program**: Program Integrity
- **Judge reason**: Directly specifies the time periods (90 days, one year, and within certification period) for requesting a fair hearing on DTA actions and benefit disputes.

```
106 CMR 367 > VIOLATIONS, > 367.100 Time Period for Requesting Hearing

A household shall be allowed to request a hearing on any action by the Department, or on loss of benefits which occurred in the prior 90 days. Action by the Department includes a denial of a request for restoration of any benefits lost more than 90 days but less than one year prior to the request. In addition, at any time within a certification period a household may request a fair hearing to dispute its current level of benefits.
```

#### Rank 5 — PARTIAL (sim 0.410)

- **Chunk ID**: `cmr_sec_367_025__000`
- **Section**: `367.025` — Introduction
- **Program**: Program Integrity
- **Judge reason**: The chunk explains the right to request a fair hearing and notification procedures, but does not specify the timeframe or deadline for requesting one.

```
106 CMR 367 > VIOLATIONS, > 367.025 Introduction

The Department shall provide a fair hearing to any household that is dissatisfied with any Department action or inaction that affects participation in the Supplemental Nutrition Assistance Program. Notification of Right to Request Hearing At the time of application, each household shall be informed in writing of its right to a hearing, how to request a hearing, that its case may be presented by a household member or an authorized representative, such as a legal counsel, a relative, a friend or other spokesperson, and that the household may bring an interpreter to the hearing. Each household shall also be informed that in cases in which the head of the household is not fluent in English, the Department will provide an interpreter if the household requests one at least one week before the hearing and that the hearing may be postponed for this purpose. Any time the household expresses to the Department that it disagrees with a Department action, it shall be reminded of the right to request a fair hearing. If there is an individual or organization available that provides free legal representation, the household shall also be informed of the availability of that service. A copy of the hearing procedures shall be made available to any interested party upon request.
```


### cmr_017 — IPV definition (rank-1: RELEVANT)

**Question**: What is an Intentional Program Violation  
**Program filter**: (none)  
**Expected section (for reference)**: `367.525` — judge picked rank-1 RELEVANT chunk in section `706.300` (section-author intuition disagrees with judge)  
**Notes**: 367.525 Definition of an Intentional Program Violation  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.460)

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

#### Rank 2 — PARTIAL (sim 0.449)

- **Chunk ID**: `cmr_sec_706_350__000`
- **Section**: `706.350` — Civil and Criminal Prosecution
- **Program**: EA
- **Judge reason**: The chunk mentions Intentional Program Violation (IPV) and discusses prosecution and disqualification procedures, but does not define what an IPV actually is.

```
106 CMR 706 > AUXILIARY > 706.350 Civil and Criminal Prosecution

A case of an alleged Intentional Program Violation (IPV) may be taken to a court of appropriate jurisdiction for civil or criminal prosecution. Duties and Limitations on the Department with Respect to Court Ordered Disqualification The Department shall disqualify an individual found guilty of an Intentional Program Violation (IPV) by a court, unless otherwise ordered by the court. The Department shall initiate the disqualification period in the first possible month following the date the disqualification was ordered, as provided in 106 CMR 706.305.
```

#### Rank 3 — PARTIAL (sim 0.420)

- **Chunk ID**: `cmr_sec_367_520__000`
- **Section**: `367.520` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: Program Integrity
- **Judge reason**: The chunk mentions what an ADH is used for (determining if an IPV was committed) but does not define what an Intentional Program Violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.520 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall conducted in order to determine if an intentional program violation (IPV) has been committed. An ADH shall be initiated by the Department if evidence exists to indicate an IPV was committed.
```

#### Rank 4 — PARTIAL (sim 0.417)

- **Chunk ID**: `cmr_sec_706_315__000`
- **Section**: `706.315` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: EA
- **Judge reason**: The chunk mentions what an IPV is in context of administrative hearings but does not define or explain what constitutes an Intentional Program Violation.

```
106 CMR 706 > AUXILIARY > 706.315 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall be conducted by the Division of Hearings to determine if an Intentional Program Violation (IPV) has been committed, unless a determination is made by a court of law pursuant to 106 CMR 706.355. An ADH may be initiated by the Department if there is reason to believe an IPV was committed.
```

#### Rank 5 — PARTIAL (sim 0.408)

- **Chunk ID**: `cmr_sec_367_840__000`
- **Section**: `367.840` — Out-of-state Disqualification Referrals
- **Program**: Program Integrity
- **Judge reason**: The chunk mentions IPV and references prosecution procedures but does not define what an Intentional Program Violation actually is.

```
106 CMR 367 > VIOLATIONS, > 367.840 Out-of-state Disqualification Referrals

Any SNAP disqualification from another state due to an IPV will be upheld in Massachusetts as if the decision originated in Massachusetts. Introduction to Civil and Criminal Prosecution A case of an alleged intentional program violation may be taken to a court of appropriate jurisdiction for civil or criminal prosecution.
```


### cmr_018 — SNAP IPV penalties (rank-1: RELEVANT)

**Question**: What are the disqualification penalties for SNAP fraud  
**Program filter**: (none)  
**Expected section (for reference)**: `367.800` — judge picked rank-1 RELEVANT chunk in section `367.800` (section-author intuition agrees)  
**Notes**: 367.800 Disqualification Penalties; 367 is Program Integrity for SNAP  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.592)

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

#### Rank 2 — PARTIAL (sim 0.575)

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

#### Rank 3 — RELEVANT (sim 0.551)

- **Chunk ID**: `cmr_sec_367_800__000`
- **Section**: `367.800` — Disqualification Penalties
- **Chunk position**: 1 / 6
- **Program**: Program Integrity
- **Hierarchy**: (A) Disqualification for Intentional Program Violations.
- **Judge reason**: Directly specifies the disqualification penalties for SNAP fraud (IPV), including duration periods for first, second, and third violations.

```
106 CMR 367 > VIOLATIONS, > 367.800 Disqualification Penalties

(A) Disqualification for Intentional Program Violations.
(1) Individuals found to have committed a SNAP IPV at an ADH shall be ineligible for SNAP benefits for a period of one year for the first finding, two years for the second finding and permanently for the third finding.
(2) Individuals found to have committed a cash program IPV at an ADH, in the absence of a SNAP IPV under 106 CMR 367.800(A)(1), shall be ineligible for SNAP benefits for the period required under the cash program rules.
```

#### Rank 4 — PARTIAL (sim 0.523)

- **Chunk ID**: `cmr_sec_365_660__000`
- **Section**: `365.660` — Facility Penalties and Disqualifications
- **Program**: SNAP
- **Judge reason**: Addresses SNAP fraud penalties but only for organizations/institutions, not individual recipient disqualification penalties which is what the question asks about.

```
106 CMR 365 > SPECIAL > 365.660 Facility Penalties and Disqualifications

USDA may disqualify or penalize an organization or institution if it is determined administratively or judicially that SNAP benefits were misappropriated or used for purchases that did not contribute to a certified household's meals. The worker shall promptly notify SNAP Management, 600 Washington Street, Boston, MA 02111, when there is reason to believe that an organization or institution is misusing SNAP benefits in its possession. However, the Department shall not take any action against the organization or institution before USDA takes action.
```

#### Rank 5 — PARTIAL (sim 0.499)

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


### cmr_019 — TAFDC vs EAEDC (rank-1: PARTIAL)

**Question**: What is the difference between TAFDC and EAEDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `701.200`  
**Notes**: 701.200 The TAFDC and EAEDC Programs  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.572)

- **Chunk ID**: `cmr_sec_701_050__000`
- **Section**: `701.050` — Transitional Cash Assistance Programs Overview
- **Program**: EA
- **Judge reason**: The chunk identifies both programs and indicates they have different eligibility policies, but does not explain the actual differences between TAFDC and EAEDC.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.050 Transitional Cash Assistance Programs Overview

The policies described in this chapter are the basis for the administration and function of both the Transitional Aid to Families with Dependent Children (TAFDC) and Emergency Aid to the Elderly, Disabled and Children (EAEDC) programs; specific eligibility policies for TAFDC and EAEDC are found in 106 CMR 703.000: Nonfinancial Eligibility and 704.000: Financial Eligibility.
```

#### Rank 2 — PARTIAL (sim 0.530)

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

#### Rank 3 — PARTIAL (sim 0.522)

- **Chunk ID**: `cmr_sec_701_200__000`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: The chunk describes TAFDC but does not provide information about EAEDC or explain the differences between the two programs.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.200 The TAFDC and EAEDC Programs

The Transitional Aid to Families with Dependent Children (TAFDC) program provides financial assistance and employment-related services to families with dependent children. The TAFDC program is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 118 and other relevant statutes and the rules, regulations and policies. TAFDC regulations implement St. 1995, c. 5. TAFDC seeks to integrate clients into the work force and break the cycle of poverty. The major program objectives include:
```

#### Rank 4 — PARTIAL (sim 0.518)

- **Chunk ID**: `cmr_sec_701_600__006`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 7 / 25
- **Program**: EA
- **Hierarchy**: (L) Disabled Adult.
- **Judge reason**: The chunk mentions both TAFDC and EAEDC programs but only defines 'Disabled Adult' with different age thresholds for each program, rather than explaining the fundamental differences between the two programs themselves.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (L) Disabled Adult.

(L) Disabled Adult. An individual younger than 66 years old in the TAFDC program or under the age of 65 in the EAEDC program who meets the Department's medical and/or vocational standards as determined by the agency or organization under contract/agreement with the Department to provide disability evaluation services. In addition, an applicant or client shall be considered disabled if he or she is in receipt of Supplemental Security Income for the disabled, or Social Security benefits for the disabled. Manual Reference: 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits, 106 CMR 703.130: TAFDC Extension of Benefits Beyond the 24-month Period, 106 CMR 703.190: TAFDC Disability Exemption Process, 106 CMR 703.610: EAEDC Participant in a Massachusetts Rehabilitation Commission Program, and 106 CMR 703.620: EAEDC Caring for the Disabled.
```

#### Rank 5 — PARTIAL (sim 0.516)

- **Chunk ID**: `cmr_sec_704_000__000`
- **Section**: `704.000` — Overview of Financial Eligibility
- **Program**: EA
- **Judge reason**: The chunk mentions both TAFDC and EAEDC and indicates they have different standards (TAFDC has 'Need and Payment Standards' while EAEDC has 'Living Arrangements and Standards of Assistance'), but does not explain what those differences actually are.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.000 Overview of Financial Eligibility

To receive Transitional Cash Assistance of EAEDC or TAFDC, an applicant or client must meet financial eligibility requirements as well as those requirements provided in 106 CMR 703.000: Transitional Cash Assistance Program: Nonfinancial Requirements. An applicant or client meets the financial eligibility requirements if h e or she has income at or below the Department's limits. The purpose of 1 106 CMR 704.000 is to show how financial eligibility is established. The topics covered are:
(B) Income, 106 CMR 704.200;
(C) Membership in the Assistance Unit and Filing Unit, 106 CMR 704.300;
(D) TAFDC, Need and Payment Standards, 106 CMR 704.410, and 704.420;
(E) EAEDC Living Arrangements and Standards of Assistance, 106 CMR 704.435 and 704.440; and
(F) Calculation of the Grant Amount, 106 CMR 704.500. 5/10/24 106 CMR - 1021 (Mass. Register #1521, 5/10/2024)
```


### cmr_020 — TAFDC 24-month limit (rank-1: RELEVANT)

**Question**: How are TAFDC time-limited benefits applied  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.120` — judge picked rank-1 RELEVANT chunk in section `703.120` (section-author intuition agrees)  
**Notes**: 703.120 TAFDC Time-limited Benefits  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.00  

#### Rank 1 — RELEVANT (sim 0.509)

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

#### Rank 2 — PARTIAL (sim 0.491)

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

#### Rank 3 — PARTIAL (sim 0.476)

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

#### Rank 4 — RELEVANT (sim 0.472)

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

#### Rank 5 — PARTIAL (sim 0.472)

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
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.30  

#### Rank 1 — RELEVANT (sim 0.600)

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

#### Rank 2 — RELEVANT (sim 0.590)

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

#### Rank 3 — PARTIAL (sim 0.541)

- **Chunk ID**: `cmr_sec_702_120__005`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 6 / 9
- **Program**: EA
- **Hierarchy**: (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
- **Judge reason**: Describes PATH program requirements for TAFDC applicants during application intake, but does not comprehensively address the full work program requirements that would apply to ongoing TAFDC recipients (which are referenced in 106 CMR 703.150).

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.

(G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
(1) TAFDC applicants 18 years of age or older shall participate in an intake and employment assessment process which may result in referrals to appropriate employment or education/training opportunities. The Department shall deny applications for either the entire assistance unit or the grantee if the applicant fails to participate in PATH without good cause.
(2) Under PATH, certain TAFDC applicants may also be subject to a Work Ready Job Diversion Program:
(a) Applicants 18 years of age or older who are determined by the Department to have the necessary job skills and experience must participate in a Work Ready Job Diversion Program.
(b) Applicants will be exempted from the Work Ready Job Diversion Program if they will be exempt from the work program (See 106 CMR 703.150: TAFDC Work Program) or have requested a disability exemption (See 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits and Reduced Need and Payment Standards).
(c) Applicants subject to the Work Ready Job Diversion Program must provide evidence of three job search contacts. Applicants must accept referrals to any appropriate Department-identified jobs.
(d) If no evidence of participation in the Work Ready Job Diversion Program is provided prior to day 30 of the application, the TAFDC application for the entire assistance unit will be denied. If the case is approved but there is no further participation
```

#### Rank 4 — PARTIAL (sim 0.539)

- **Chunk ID**: `cmr_sec_701_200__000`
- **Section**: `701.200` — The TAFDC and EAEDC Programs
- **Chunk position**: 1 / 3
- **Program**: EA
- **Judge reason**: Describes TAFDC program objectives including workforce integration but does not detail specific work program requirements.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.200 The TAFDC and EAEDC Programs

The Transitional Aid to Families with Dependent Children (TAFDC) program provides financial assistance and employment-related services to families with dependent children. The TAFDC program is subject to appropriation and is administered by the Department in accordance with M.G.L. c. 118 and other relevant statutes and the rules, regulations and policies. TAFDC regulations implement St. 1995, c. 5. TAFDC seeks to integrate clients into the work force and break the cycle of poverty. The major program objectives include:
```

#### Rank 5 — RELEVANT (sim 0.533)

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


### cmr_022 — TAFDC asset limit (rank-1: PARTIAL)

**Question**: What is the asset limit for TAFDC  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `704.110`  
**Notes**: 704.110 Asset Limitations  
**Scores**: Relevant@5 = 0, Useful@5 = 2, rank-weighted = 0.75  

#### Rank 1 — PARTIAL (sim 0.437)

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

#### Rank 2 — IRRELEVANT (sim 0.436)

- **Chunk ID**: `cmr_sec_701_600__006`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 7 / 25
- **Program**: EA
- **Hierarchy**: (L) Disabled Adult.
- **Judge reason**: The chunk defines 'Disabled Adult' in TAFDC but does not contain any information about asset limits for the program.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (L) Disabled Adult.

(L) Disabled Adult. An individual younger than 66 years old in the TAFDC program or under the age of 65 in the EAEDC program who meets the Department's medical and/or vocational standards as determined by the agency or organization under contract/agreement with the Department to provide disability evaluation services. In addition, an applicant or client shall be considered disabled if he or she is in receipt of Supplemental Security Income for the disabled, or Social Security benefits for the disabled. Manual Reference: 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits, 106 CMR 703.130: TAFDC Extension of Benefits Beyond the 24-month Period, 106 CMR 703.190: TAFDC Disability Exemption Process, 106 CMR 703.610: EAEDC Participant in a Massachusetts Rehabilitation Commission Program, and 106 CMR 703.620: EAEDC Caring for the Disabled.
```

#### Rank 3 — PARTIAL (sim 0.431)

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

#### Rank 4 — IRRELEVANT (sim 0.431)

- **Chunk ID**: `cmr_sec_701_600__016`
- **Section**: `701.600` — Definition of Terms
- **Chunk position**: 17 / 25
- **Program**: EA
- **Hierarchy**: (CC) Nonexempt Assistance Unit - TAFDC.
- **Judge reason**: The chunk defines 'Nonexempt Assistance Unit' but does not contain any information about asset limits for TAFDC.

```
106 CMR 701 > TRANSITIONAL CASH ASSISTANCE PROGRAMS GENERAL POLICIES > 701.600 Definition of Terms > (CC) Nonexempt Assistance Unit - TAFDC.

(CC) Nonexempt Assistance Unit - TAFDC. An assistance unit which does not meet the requirements of 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits and is subject to Time-limited Benefits and the Work Program requirements. Manual Reference: 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits.
```

#### Rank 5 — IRRELEVANT (sim 0.428)

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


### cmr_023 — EAEDC disability (rank-1: PARTIAL)

**Question**: What is EAEDC disability and how is it determined  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `703.190`  
**Notes**: 703.190 EAEDC Disability  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.75  

#### Rank 1 — PARTIAL (sim 0.646)

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

#### Rank 2 — PARTIAL (sim 0.629)

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

#### Rank 3 — RELEVANT (sim 0.622)

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

#### Rank 4 — RELEVANT (sim 0.583)

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

#### Rank 5 — PARTIAL (sim 0.573)

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


### cmr_024 — ESP overview (rank-1: PARTIAL)

**Question**: What is the Employment Services Program  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `707.100`  
**Notes**: 707.100 Introduction to ESP/Orientation  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.70  

#### Rank 1 — PARTIAL (sim 0.473)

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

#### Rank 2 — PARTIAL (sim 0.468)

- **Chunk ID**: `cmr_sec_707_140__000`
- **Section**: `707.140` — Educational Component
- **Chunk position**: 1 / 5
- **Program**: EA
- **Judge reason**: Describes a specific component (Educational Component) of the Employment Services Program rather than defining what the overall Employment Services Program is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.140 Educational Component

The Educational Component provides educational services to individuals to prepare him or her to obtain and maintain employment. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP), and the criteria in 106 CMR 707.140(A) through (D):
```

#### Rank 3 — RELEVANT (sim 0.461)

- **Chunk ID**: `cmr_sec_707_120__000`
- **Section**: `707.120` — Employment Services Program (ESP) Participation Components
- **Program**: EA
- **Judge reason**: The chunk directly defines the Employment Services Program (ESP) and describes its participation components, structure, and requirements, which directly answers the user's question about what the program is.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.120 Employment Services Program (ESP) Participation Components

106 CMR 707.130 through 707.190 describe the ESP component activities. Participation in a component is subject to available program resources and the individual's approved Employment Development Plan (EDP). Each individual who completes an EDP must fulfill the activities on the EDP in accordance with 106 CMR 707.110. ESP participation may include self-initiated educational, vocational, or training programs, not funded by ESP provided the programs are consistent with 106 CMR 707.000 through 106 CMR 707.190 and individual's approved EDP. The individual must meet the Department's participation requirements, including, but not limited to, minimum scheduled hours and attendance requirements established for each ESP component, and the individual must complete the programs in accordance with time frames established by the Department, if any, for a particular component. The individual must be making satisfactory progress in the component, as defined by the service provider. An ESP participant in a self-initiated program who meets the above requirements shall be eligible for ESP Support Services in accordance with 106 CMR 707.210.
```

#### Rank 4 — PARTIAL (sim 0.449)

- **Chunk ID**: `cmr_sec_707_185__002`
- **Section**: `707.185` — Post-employment Services Component
- **Chunk position**: 3 / 4
- **Program**: EA
- **Hierarchy**: (B) Services.
- **Judge reason**: Describes specific services within the Employment Services Program but doesn't define what the program itself is or its overall purpose and scope.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.185 Post-employment Services Component > (B) Services.

(B) Services. Services in the Post-employment Services component may include, but are not limited to:
(1) transition support services;
(2) employee work force retention services;
(3) skills and educational advancement services; and
(4) re-employment and job upgrade services.
```

#### Rank 5 — RELEVANT (sim 0.447)

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
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.645)

- **Chunk ID**: `cmr_sec_708_000__000`
- **Section**: `708.000` — Overview
- **Program**: EA
- **Judge reason**: The chunk directly defines the Full Employment Program for TAFDC, explaining its purpose, how it works, and key characteristics of client participation.

```
106 CMR 708 > FULL EMPLOYMENT > 708.000 Overview

The Full Employment Program (FEP) component provides clients with paid work experience and on-the-job training needed to obtain an unsubsidized job. Clients participating in the Full Employment Program (FEP) will receive a subsidized wage in lieu of TAFDC cash benefits and are subject to FEP criteria in accordance with 106 CMR 707.180: Full Employment Program.
```

#### Rank 2 — RELEVANT (sim 0.608)

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

#### Rank 3 — PARTIAL (sim 0.562)

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

#### Rank 4 — PARTIAL (sim 0.532)

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

#### Rank 5 — PARTIAL (sim 0.513)

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

#### Rank 1 — PARTIAL (sim 0.508)

- **Chunk ID**: `cmr_sec_365_180__005`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 6 / 9
- **Program**: SNAP
- **Hierarchy**: (F) Verification Requirements.
- **Judge reason**: The chunk discusses verification requirements for categorically eligible SNAP households (SSI, EAEDC, TANF) but does not address MassHealth referral eligibility criteria.

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

#### Rank 2 — PARTIAL (sim 0.503)

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

#### Rank 3 — PARTIAL (sim 0.500)

- **Chunk ID**: `cmr_sec_365_180__001`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 2 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk discusses categorical eligibility for SNAP households but does not address MassHealth referral eligibility criteria or conditions.

```
106 CMR 365 > SPECIAL > 365.180 Categorically Eligible Households > (A) The following SNAP households are categorically eligible:

(5) SNAP-only TANF Service Elder/Disabled Households which include SNAP households consisting solely of non-SSI elders (60 years of age or older) and/or disabled individuals in accordance with SNAP disability standards at 106 CMR 361.210: Elderly or Disabled Individuals. These households must meet the Gross Monthly Categorical Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards; and
(6) SNAP-only TANF Service Adult Households include SNAP households consisting solely of adults between 19 and 59 years of age. These households must meet the Gross Monthly Categorically Eligibility Income Standards at 106 CMR 364.976: Gross Monthly Categorical Eligibility Income Standards. For purposes of 106 CMR 365.180(A)(1) through (3), authorized to receive means that an individual has been determined eligible for benefits and has been notified of this determination, even if benefits have been authorized but not received, authorized but not accessed, suspended or recouped, or not paid because they are less than a minimum amount. For purposes of 106 CMR 365.180(A)(4) through (6), a TANF Service includes receipt of the Commonwealth of Massachusetts' Help for Those in Need: A Resource Brochure.
```

#### Rank 4 — IRRELEVANT (sim 0.468)

- **Chunk ID**: `cmr_sec_360_030__002`
- **Section**: `360.030` — Definitions
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (4) A place not designed for or ordinarily used as a regular sleeping accommo...
- **Judge reason**: The chunk contains definitions of terms like 'household' and 'means-tested program' but does not address eligibility criteria or conditions for MassHealth referral of SNAP households.

```
106 CMR 360 > GENERAL > 360.030 Definitions > (4) A place not designed for or ordinarily used as a regular sleeping accommo...

(4) A place not designed for or ordinarily used as a regular sleeping accommodation for people (a hallway, a bus station, a lobby or similar place). Household. Any individual or group whose income and/or assets must be used to calculate SNAP benefits levels. Household Disaster. An emergency situation declared a disaster by the President or the Federal Emergency Management Agency. Disasters are defined as, but are not limited to, floods, hurricanes, earthquakes or fires. Household Misfortune. A loss of food due to, but not limited to, loss of power, fire or flood that is not declared a disaster by the President or the Federal Emergency Management Agency. (Mass. Register #1453 10/1/21) Means-tested Program. The following are federal or state means-tested programs (i.e., income is a factor in determining eligibility): Supplemental Nutrition Assistance Program (SNAP), Transitional Assistance to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC), Emergency Assistance (EA), Supplemental Security Income (SSI), State Supplement Program (SSP) to SSI, Medicaid, State Child Health Insurance (SCHIP), Temporary Assistance for Needy Families (TANF), Food Assistance Programs in Puerto Rico, American Samoa and the Northern Mariana Islands (CNMI) and Veterans' Service benefits. Month. A cyclical month determined by the last digit of the Social Security number of the head of the household, unless otherwise specified.
```

#### Rank 5 — PARTIAL (sim 0.467)

- **Chunk ID**: `cmr_sec_365_180__000`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 1 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: The chunk defines categorical eligibility for SNAP households but does not address MassHealth referral eligibility criteria specifically.

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


### cmr_027 — TAFDC overpayments (rank-1: RELEVANT)

**Question**: How does DTA correct overpayments and underpayments  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `706.210` — judge picked rank-1 RELEVANT chunk in section `706.210` (section-author intuition agrees)  
**Notes**: 706.210 Correction of Overpayments and Underpayments  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.506)

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

#### Rank 2 — PARTIAL (sim 0.388)

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

#### Rank 3 — PARTIAL (sim 0.382)

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

#### Rank 4 — PARTIAL (sim 0.377)

- **Chunk ID**: `cmr_sec_704_250__014`
- **Section**: `704.250` — Noncountable Income
- **Chunk position**: 15 / 21
- **Program**: EA
- **Hierarchy**: (DD) Transitional Cash Assistance benefits resulting from a correction of an ...
- **Judge reason**: Mentions corrections of underpayments and fair hearing decisions but only addresses how such corrections are treated as noncountable income, not the actual process or procedures DTA uses to correct overpayments and underpayments.

```
106 CMR 704 > FINANCIAL ELIGIBILITY > 704.250 Noncountable Income > (DD) Transitional Cash Assistance benefits resulting from a correction of an ...

(DD) Transitional Cash Assistance benefits resulting from a correction of an underpayment or a fair hearing decision, in the month of receipt and the following month;
(EE) Refunds from a utility company, landlord or other vendor that were originally paid for by Transitional Cash Assistance benefits, fuel assistance, or other noncountable income funds;
```

#### Rank 5 — PARTIAL (sim 0.363)

- **Chunk ID**: `cmr_sec_706_220__000`
- **Section**: `706.220` — Causes of Overpayments
- **Program**: EA
- **Judge reason**: This chunk explains the causes of overpayments but does not address how DTA corrects or recovers overpayments and underpayments.

```
106 CMR 706 > AUXILIARY > 706.220 Causes of Overpayments

(A) Department Error. An overpayment may occur as a result of Department error. Department error includes, but is not limited to, failure of the worker to act on information that affects eligibility or the amount of assistance.
(B) Payments Pending a Fair Hearing Decision. An overpayment occurs when the Department's position is upheld on an appeal by a client of a reduction or termination, and aid was paid pending the implementation of the decision.
(C) Client Error, Misrepresentation or Withholding of Information. An overpayment may occur as a result of client error. Client error may occur when the client, because of a misunderstanding of his or her responsibilities, fails to notify the Department of a change in resources or other circumstances within the prescribed ten days of such a change. Certain instances of client error may be fraudulent and should be referred to BSI. An overpayment may also occur because the applicant or client knowingly misrepresents or withholds information from the Department. If there is a reasonable possibility that fraud occurred in an overpayment of benefits, the case should be referred to BSI as provided in 106 CMR 706.240.
```


### cmr_028 — identity verification (rank-1: RELEVANT)

**Question**: How does DTA verify identity  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361` — judge picked rank-1 RELEVANT chunk in section `361.610` (section-author intuition agrees)  
**Notes**: BROAD — chapter 361 application processing covers verification; many sections in 361 may match  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.430)

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

#### Rank 2 — RELEVANT (sim 0.370)

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

#### Rank 3 — RELEVANT (sim 0.342)

- **Chunk ID**: `cmr_sec_365_830__000`
- **Section**: `365.830` — Expedited Service Verification Requirements
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses how DTA verifies identity by listing acceptable documentary evidence and collateral contact methods used for verification.

```
106 CMR 365 > SPECIAL > 365.830 Expedited Service Verification Requirements

The household's identity is the only eligibility factor that must be verified before expedited service is provided. Readily available documentary evidence or collateral contact, in accordance with 106 CMR 361.640(A): Documentary Evidence and (B): Collateral Contact, may be used. Examples of acceptable documentary evidence include, but are not limited to, a driver's license, a work or school identification (I.D.) card, a voter registration card, a birth certificate, wage stubs or an I.D. for health benefits or for another assistance or social services program. Any documents that reasonably establish the applicant's identity must be accepted and no requirement for a specific type of document, such as a birth certificate, may be imposed. The Social Security number requirements of 106 CMR 362.500: Social Security Numbers do not have to be met before expedited service is provided. These requirements must be met prior to the first full month of participation, unless good cause for not meeting these requirements is established in accordance with 106 CMR 362.500(C): Determining Good Cause. The applicant must register for work if subject to SNAP Work Requirements in accordance with 106 CMR 362.300: Work Requirements unless exempt or unless the household has designated an authorized representative to apply on its behalf in accordance with 106 CMR 361.300: Authorized Representatives. Every household member required to meet SNAP Work
```

#### Rank 4 — PARTIAL (sim 0.335)

- **Chunk ID**: `cmr_sec_366_320__004`
- **Section**: `366.320` — Household Responsibilities
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (C) Providing Verification.
- **Judge reason**: The chunk discusses verification of various eligibility factors but does not specifically address how DTA verifies identity itself.

```
106 CMR 366 > ADDITIONAL > 366.320 Household Responsibilities > (C) Providing Verification.

(6) Disability. The disability of a household member, as it pertains to household composition, shall be verified prior to recertification in accordance with 106 CMR 361.210: Elderly or Disabled Individuals.
(7) Legally Obligated Child Support Payments. The household shall be required to verify the amount of legally obligated child support a household member pays to a non-household member prior to recertification.
(8) Additional Verification Requirements.
(a) All other eligibility factors, financial or nonfinancial, shall be verified prior to recertification when the information provided by the applicant is questionable and affects the household's eligibility or benefit level. Other eligibility factors include loans, residency, household composition, citizenship, student eligibility, circumstances related to work registration, and certain deductible expenses.
(b) These factors shall be verified prior to recertification when the Department decides to require verification of additional information. Such verifications must be required statewide and shall not be imposed on a case-by-case basis on particular households.
```

#### Rank 5 — PARTIAL (sim 0.325)

- **Chunk ID**: `cmr_sec_361_210__004`
- **Section**: `361.210` — Elderly or Disabled Individuals
- **Chunk position**: 5 / 5
- **Program**: SNAP
- **Hierarchy**: (B) The requirements in 106 CMR 361.
- **Judge reason**: The chunk addresses verification of disability status rather than general identity verification procedures that DTA uses.

```
106 CMR 361 > THE > 361.210 Elderly or Disabled Individuals > (B) The requirements in 106 CMR 361.

(4) 106 CMR 361.210(A)(5) and (6): proof by the household that the disabled individual is receiving VA disability benefits is sufficient verification of disability.
(5) 106 CMR 361.210(A)(3) and (7): the Department shall use the Social Security Administration's (SSA) most current list of disabilities considered permanent under the Social Security Act. If it is obvious to the worker that the individual has one of the listed disabilities, the household shall be considered to have verified the disability. If the disability is not obvious to the worker, the household shall verify the disability by providing a statement from a physician or a licensed or certified psychologist certifying that the individual has one of the nonobvious disabilities listed.
(6) 106 CMR 361.210(A)(8), the household shall provide proof that the individual receives a Railroad Retirement disability annuity from the Railroad Retirement Board and has been determined to qualify for Medicare.
```


### cmr_029 — SNAP household composition (rank-1: RELEVANT)

**Question**: What are SNAP household composition rules  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `361.2` — judge picked rank-1 RELEVANT chunk in section `361.200` (section-author intuition agrees)  
**Notes**: BROAD — 361.200 series; multiple chunks should match  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.25  

#### Rank 1 — RELEVANT (sim 0.515)

- **Chunk ID**: `cmr_sec_361_200__001`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: Directly addresses SNAP household composition rules by defining which individuals must be considered in the same household, including spouse and parental control rules.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (A) The following individuals living with others or groups of individuals liv...

(A) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals together even if they do not do so unless an exception applies:
(1) Spouse Rule. An individual living with his or her spouse must be in the same SNAP household as the spouse. Spouses shall not be granted separate household status. Spouse is defined as either of two individuals who are legally married to one another, or who are living together and holding themselves out to the community as husband and wife by representing themselves as spouses to relatives, friends, neighbors, or tradespeople;
(2) Parental Control Rule. A child younger than 18 years old, except for a foster care child (as defined in 106 CMR 361.240(F)), who is living with an adult household member (not the child's parent) and under the parental control of the adult household member, must be in the same SNAP household as the adult household member. Parental control means providing financial support or supervision, or both, to an individual younger than 18 years old; and
```

#### Rank 2 — PARTIAL (sim 0.512)

- **Chunk ID**: `cmr_sec_365_180__000`
- **Section**: `365.180` — Categorically Eligible Households
- **Chunk position**: 1 / 9
- **Program**: SNAP
- **Hierarchy**: (A) The following SNAP households are categorically eligible:
- **Judge reason**: Addresses categorical eligibility rules for SNAP households but doesn't comprehensively cover general household composition rules like who counts as a household member, income counting, or other composition requirements.

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

#### Rank 3 — RELEVANT (sim 0.500)

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

#### Rank 4 — RELEVANT (sim 0.490)

- **Chunk ID**: `cmr_sec_361_200__002`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: The chunk directly addresses SNAP household composition rules by defining who must be in the same household and who is considered separate, including the parent/child rule and special living arrangements.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (A) The following individuals living with others or groups of individuals liv...

(3) Parent/Child Rule. A child younger than 22 years old living with his or her natural, adopted or stepparent(s) must be in the same SNAP household as the parent(s).
(B) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals separately even if they do not do so.
(1) An individual, with or without children, residing in a drug or alcohol treatment center shall be one SNAP household separate from the other residents. See 106 CMR 365.600 through 365.690.
(2) A blind or disabled resident of a group living arrangement (106 CMR 365.600 through 365.690) who applies through the use of the facility's authorized representative shall be one SNAP household separate from the other residents. If a blind or disabled resident applies on his or her own behalf, the household size must be determined following the household concept rules defined in 106 CMR 361.200.
(3) An individual, with or without children, residing in a shelter for battered individuals and their children shall be one SNAP household separate from the other residents. See 106 CMR 365.550: Residents of Shelters for Battered Women and Their Children.
```

#### Rank 5 — PARTIAL (sim 0.477)

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


### cmr_030 — SNAP benefit calculation (rank-1: PARTIAL)

**Question**: How are SNAP benefits calculated  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `364`  
**Notes**: BROAD — chapter 364 entirely about determining benefit  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.464)

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

#### Rank 2 — PARTIAL (sim 0.458)

- **Chunk ID**: `cmr_sec_364_980__000`
- **Section**: `364.980` — SNAP Issuance Tables
- **Program**: SNAP
- **Judge reason**: Explains where to find SNAP benefit amounts but doesn't describe the actual calculation methodology or factors used to determine eligibility and benefit levels.

```
106 CMR 364 > DETERMINING > 364.980 SNAP Issuance Tables

A client who is eligible for SNAP benefits will receive 100% of the SNAP benefit allotment listed in the Program Issuance Tables. The standards in the SNAP Issuance Tables are based on household size and are adjusted annually by USDA/FNS. These standards are posted at www.mass.gov/dta. NON-TEXT PAGE
```

#### Rank 3 — PARTIAL (sim 0.451)

- **Chunk ID**: `cmr_sec_364_650__000`
- **Section**: `364.650` — Prorating Initial Month's Benefits
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: The chunk addresses how initial month SNAP benefits are prorated but does not explain the overall calculation methodology for determining standard monthly SNAP benefit amounts.

```
106 CMR 364 > DETERMINING > 364.650 Prorating Initial Month's Benefits

SNAP benefits for a household's initial month shall be prorated. The initial month is the first month for which a household is certified to participate in SNAP following any period of time during which the household did not receive SNAP, except for migrant and seasonal farmworker households. For migrant and seasonal farmworker households, the initial month is the first month for which a household is certified to participate in SNAP following any period of more than one month during which the household did not receive SNAP. A migrant or seasonal farmworker household that has received SNAP within the month before application is entitled to a full month's benefits. Households which apply for initial benefits after the 15th day of the month and are determined eligible for expedited SNAP benefits in accordance with 106 CMR 365.800: Expedited Service, must be issued a combined allotment. A combined allotment includes the initial month's prorated benefits plus the second month's full allotment. Combined allotments must be issued within the seven-day expedited service time frame. Proration is the issuance of that portion of a household's monthly SNAP benefit, as calculated in accordance with 106 CMR 364.600, which corresponds to the period of time from the date of application to the end of the month. For a household with a monthly allotment of $400 or less, the initial month's allotment is determined in accordance with 106 CMR 364.990. For a household with a monthly allotment
```

#### Rank 4 — PARTIAL (sim 0.442)

- **Chunk ID**: `cmr_sec_360_030__002`
- **Section**: `360.030` — Definitions
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (4) A place not designed for or ordinarily used as a regular sleeping accommo...
- **Judge reason**: The chunk defines 'Household' as a group whose income/assets are used to calculate SNAP benefits but does not explain the actual calculation methodology or formula.

```
106 CMR 360 > GENERAL > 360.030 Definitions > (4) A place not designed for or ordinarily used as a regular sleeping accommo...

(4) A place not designed for or ordinarily used as a regular sleeping accommodation for people (a hallway, a bus station, a lobby or similar place). Household. Any individual or group whose income and/or assets must be used to calculate SNAP benefits levels. Household Disaster. An emergency situation declared a disaster by the President or the Federal Emergency Management Agency. Disasters are defined as, but are not limited to, floods, hurricanes, earthquakes or fires. Household Misfortune. A loss of food due to, but not limited to, loss of power, fire or flood that is not declared a disaster by the President or the Federal Emergency Management Agency. (Mass. Register #1453 10/1/21) Means-tested Program. The following are federal or state means-tested programs (i.e., income is a factor in determining eligibility): Supplemental Nutrition Assistance Program (SNAP), Transitional Assistance to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC), Emergency Assistance (EA), Supplemental Security Income (SSI), State Supplement Program (SSP) to SSI, Medicaid, State Child Health Insurance (SCHIP), Temporary Assistance for Needy Families (TANF), Food Assistance Programs in Puerto Rico, American Samoa and the Northern Mariana Islands (CNMI) and Veterans' Service benefits. Month. A cyclical month determined by the last digit of the Social Security number of the head of the household, unless otherwise specified.
```

#### Rank 5 — PARTIAL (sim 0.440)

- **Chunk ID**: `cmr_sec_364_600__000`
- **Section**: `364.600` — Determining the Benefit Level
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Judge reason**: The chunk indicates that benefit levels are determined but does not explain the actual calculation methodology or formula used.

```
106 CMR 364 > DETERMINING > 364.600 Determining the Benefit Level

Once a household has been determined eligible for SNAP considering both nonfinancial and financial eligibility standards, the case manager must determine the household's benefit level or monthly allotment.
```


### cmr_031 — section number lookup (rank-1: IRRELEVANT)

**Question**: What does 363.140 cover  
**Program filter**: (none)  
**Expected section (for reference)**: `363.140`  
**Notes**: ADVERSARIAL — exact section-number query. Tests whether the embedding picks up the literal '363.140' token. Hybrid search should excel here.  
**Scores**: Relevant@5 = 0, Useful@5 = 1, rank-weighted = 0.15  

#### Rank 1 — IRRELEVANT (sim 0.243)

- **Chunk ID**: `cmr_sec_343_010__000`
- **Section**: `343.010` — Purpose
- **Program**: Hearings
- **Judge reason**: The chunk describes 106 CMR 343 (Fair Hearing Rules) but the user is asking about 363.140, which is a different regulation section not addressed in this text.

```
106 CMR 343 > FAIR HEARING RULES > 343.010 Purpose

106 CMR 343.00 sets forth the rules for hearings and appeals filed by applicants or clients dissatisfied with certain actions or inactions by the Department of Transitional Assistance. Scope 106 CMR 343.000 sets forth the exclusive rules for hearings and appeals filed by applicants, clients and, if applicable, any sponsors of aliens under the programs of Transitional Aid to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC) and State Supplement Program (SSP), and by clients or former clients and/or their spouses under M.G.L. c. 62D. Hearings and appeals arising under Supplemental Nutrition Assistance Program (SNAP) are governed by 106 CMR 367.000: Supplemental Nutrition Assistance Program: Violations, Hearings and Claims, excepting that matters not addressed therein shall be governed by 106 CMR 343.000. The Department may enter into interdepartmental service agreements with other state agencies to conduct hearings in accordance with 106 CMR 343.000.
```

#### Rank 2 — IRRELEVANT (sim 0.231)

- **Chunk ID**: `cmr_sec_361_610__002`
- **Section**: `361.610` — Verification Requirements at Initial Certification
- **Chunk position**: 3 / 10
- **Program**: SNAP
- **Hierarchy**: (C) Utility Costs for Certain Homeless Households.
- **Judge reason**: The chunk discusses 361.610 verification requirements for homeless households, not 363.140 which the user is asking about.

```
106 CMR 361 > THE > 361.610 Verification Requirements at Initial Certification > (C) Utility Costs for Certain Homeless Households.

(C) Utility Costs for Certain Homeless Households. Households in which all members are homeless individuals and reside in someone else's home (see 106 CMR 360.020: Definitions) must verify actual shelter and/or utility expenses greater than $143 per month to be eligible for the shelter deduction and the applicable Standard Utility Allowance.
```

#### Rank 3 — IRRELEVANT (sim 0.230)

- **Chunk ID**: `cmr_sec_360_220__002`
- **Section**: `360.220` — Complaint Requirements
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (C) Complaints will be accepted even if the information specified in 106 CMR ...
- **Judge reason**: The chunk discusses 360.220 complaint requirements and does not address what 363.140 covers.

```
106 CMR 360 > GENERAL > 360.220 Complaint Requirements > (C) Complaints will be accepted even if the information specified in 106 CMR ...

(C) Complaints will be accepted even if the information specified in 106 CMR 360.220(A) is not complete. However, investigations will be conducted only if information concerning 106 CMR 360.220(A)(2) through (4) is provided.
```

#### Rank 4 — PARTIAL (sim 0.228)

- **Chunk ID**: `cmr_sec_365_730__000`
- **Section**: `365.730` — Assets
- **Program**: SNAP
- **Judge reason**: The chunk mentions 363.000 through 363.150 but does not specify what 363.140 specifically covers.

```
106 CMR 365 > SPECIAL > 365.730 Assets

Student households are subject to the asset eligibility standards set forth in 106 CMR 363.000 through 363.150. In determining the assets of students, deferred payment loans and other monies that have been averaged as income as specified in 106 CMR 365.740 shall not be counted as an asset.
```

#### Rank 5 — IRRELEVANT (sim 0.227)

- **Chunk ID**: `cmr_sec_367_660__005`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 6 / 6
- **Program**: Program Integrity
- **Hierarchy**: (J) a listing of the household member's rights as described in 106 CMR 367.400;
- **Judge reason**: The chunk discusses ADH (Administrative Disqualification Hearing) waiver procedures under 367.660, not the content or coverage of regulation 363.140.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH > (J) a listing of the household member's rights as described in 106 CMR 367.400;

(J) a listing of the household member's rights as described in 106 CMR 367.400;
(K) a copy of the Department's ADH hearing procedures; and
(L) a statement that failure to return this waiver shall in no way have a negative impact on the result of the ADH.
```


### cmr_032 — ADH acronym (rank-1: RELEVANT)

**Question**: What is an ADH  
**Program filter**: (none)  
**Expected section (for reference)**: `367.520` — judge picked rank-1 RELEVANT chunk in section `706.315` (section-author intuition disagrees with judge)  
**Notes**: ADVERSARIAL — Administrative Disqualification Hearing. 367.520 Introduction to ADH.  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.401)

- **Chunk ID**: `cmr_sec_706_315__000`
- **Section**: `706.315` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: EA
- **Judge reason**: Directly defines ADH (Administrative Disqualification Hearing) and explains its purpose in DTA policy.

```
106 CMR 706 > AUXILIARY > 706.315 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall be conducted by the Division of Hearings to determine if an Intentional Program Violation (IPV) has been committed, unless a determination is made by a court of law pursuant to 106 CMR 706.355. An ADH may be initiated by the Department if there is reason to believe an IPV was committed.
```

#### Rank 2 — PARTIAL (sim 0.399)

- **Chunk ID**: `cmr_sec_706_320__001`
- **Section**: `706.320` — Advance Notice of an Administrative Disqualification Hearing (ADH)
- **Chunk position**: 2 / 6
- **Program**: EA
- **Hierarchy**: (C) A summary of the evidence, and how and where it can be examined;
- **Judge reason**: The chunk mentions ADH as an acronym (Administrative Disqualification Hearing) but only provides procedural details about notice requirements rather than explaining what an ADH actually is or its purpose.

```
106 CMR 706 > AUXILIARY > 706.320 Advance Notice of an Administrative Disqualification Hearing (ADH) > (C) A summary of the evidence, and how and where it can be examined;

(C) A summary of the evidence, and how and where it can be examined;
(D) A warning that failure to appear without good cause, in accordance with 106 CMR 343.320(D), will result in a decision by the hearing officer based solely on the information provided by the Department at the hearing;
```

#### Rank 3 — PARTIAL (sim 0.386)

- **Chunk ID**: `cmr_sec_367_660__004`
- **Section**: `367.660` — Waiver of an ADH
- **Chunk position**: 5 / 6
- **Program**: Program Integrity
- **Hierarchy**: (G) a statement that failure to sign and return this form within the period s...
- **Judge reason**: The chunk mentions ADH multiple times but only in procedural context (waiver forms and charges) without defining what ADH actually stands for or means.

```
106 CMR 367 > VIOLATIONS, > 367.660 Waiver of an ADH > (G) a statement that failure to sign and return this form within the period s...

(G) a statement that failure to sign and return this form within the period specified by the Department will result in the holding of an ADH;
(H) the charge(s) against the household member;
(I) a summary of evidence and how and where it can be examined;
```

#### Rank 4 — RELEVANT (sim 0.381)

- **Chunk ID**: `cmr_sec_367_520__000`
- **Section**: `367.520` — Introduction to Administrative Disqualification Hearings (ADH)
- **Program**: Program Integrity
- **Judge reason**: Directly defines ADH as Administrative Disqualification Hearing and explains its purpose in determining intentional program violations.

```
106 CMR 367 > VIOLATIONS, > 367.520 Introduction to Administrative Disqualification Hearings (ADH)

An ADH shall conducted in order to determine if an intentional program violation (IPV) has been committed. An ADH shall be initiated by the Department if evidence exists to indicate an IPV was committed.
```

#### Rank 5 — RELEVANT (sim 0.379)

- **Chunk ID**: `cmr_sec_706_335__000`
- **Section**: `706.335` — The Administrative Disqualification Hearing (ADH)
- **Program**: EA
- **Judge reason**: The chunk directly defines what an ADH (Administrative Disqualification Hearing) is and explains its procedures, directly answering the user's question.

```
106 CMR 706 > AUXILIARY > 706.335 The Administrative Disqualification Hearing (ADH)

If the individual or his or her representative fails to appear at the ADH without good cause, in accordance with 106 CMR 343.320(D), the ADH shall still be conducted. The hearing officer is required to carefully consider the evidence and determine if an Intentional Program Violation (IPV) was committed based on a preponderance of the evidence standard. If the individual is found to have committed an IPV, but the Director of the Division of Hearings later determines that there was good cause for the failure to appear, the previous decision shall be void and the Department shall conduct a new hearing. The individual has ten days from the date of the originally scheduled hearing to present evidence of good cause for failure to appear.
```


### cmr_033 — EPSDT acronym (rank-1: RELEVANT)

**Question**: What does EPSDT mean in DTA policy  
**Program filter**: (none)  
**Expected section (for reference)**: `705.130` — judge picked rank-1 RELEVANT chunk in section `705.130` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — Early and Periodic Screening, Diagnosis and Treatment. 705.130. Rare term.  
**Scores**: Relevant@5 = 1, Useful@5 = 1, rank-weighted = 1.00  

#### Rank 1 — RELEVANT (sim 0.405)

- **Chunk ID**: `cmr_sec_705_130__000`
- **Section**: `705.130` — Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)
- **Program**: EA
- **Judge reason**: The chunk directly defines EPSDT and explains its purpose in DTA policy, fully answering the user's question about what the acronym means.

```
106 CMR 705 > RELATED > 705.130 Early and Periodic Screening, Diagnosis and Treatment Services (EPSDT)

The purpose of EPSDT is to provide all persons in the assistance unit younger than 21 years old the opportunity for preventive health care, including medical checkups, immunizations, and dental checkups. A full description of the EPSDT program is provided in MassHealth regulations of the Division of Medical Assistance.
```

#### Rank 2 — IRRELEVANT (sim 0.346)

- **Chunk ID**: `cmr_sec_701_395__002`
- **Section**: `701.395` — Learning Disabilities: Screening, Assessment, Sanction Relief and Extensions
- **Chunk position**: 3 / 6
- **Program**: EA
- **Hierarchy**: (B) While waiting for the completion of the assessment, DTA will help clients...
- **Judge reason**: The chunk discusses learning disabilities screening and ESP activities but does not define or explain what EPSDT means.

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

#### Rank 3 — IRRELEVANT (sim 0.320)

- **Chunk ID**: `cmr_sec_707_110__002`
- **Section**: `707.110` — Completion of an Employment Development Plan (EDP)
- **Chunk position**: 3 / 5
- **Program**: EA
- **Hierarchy**: (A) Developing an EDP.
- **Judge reason**: The chunk discusses Employment Development Plans (EDP) in the context of employment services and contains no information about EPSDT or its meaning.

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

#### Rank 4 — IRRELEVANT (sim 0.301)

- **Chunk ID**: `cmr_sec_703_525__003`
- **Section**: `703.525` — TAFDC Result of Sanction for Failure to Cooperate without Good Cause
- **Chunk position**: 4 / 6
- **Program**: EA
- **Hierarchy**: (E) If DOR has not informed DTA of the status of the case within 70 days from...
- **Judge reason**: The chunk discusses TAFDC sanctions and child support enforcement procedures, with no mention of EPSDT or its definition.

```
106 CMR 703 > NONFINANCIAL > 703.525 TAFDC Result of Sanction for Failure to Cooperate without Good Cause > (E) If DOR has not informed DTA of the status of the case within 70 days from...

(E) If DOR has not informed DTA of the status of the case within 70 days from the date the document described in 106 CMR 703.525(D) is sent to DOR, the sanctioned grantee or teen parent shall be deemed to have cooperated with child support enforcement requirements and the sanction will be removed.
```

#### Rank 5 — IRRELEVANT (sim 0.291)

- **Chunk ID**: `cmr_sec_366_110__007`
- **Section**: `366.110` — Household Reporting Responsibilities
- **Chunk position**: 8 / 9
- **Program**: SNAP
- **Hierarchy**: (D) Elderly/Disabled Simplified Application Project (EDSAP)
- **Judge reason**: The chunk discusses EDSAP (Elderly/Disabled Simplified Application Project) but does not define or explain EPSDT, which is a different acronym.

```
106 CMR 366 > ADDITIONAL > 366.110 Household Reporting Responsibilities > (D) Elderly/Disabled Simplified Application Project (EDSAP)

(D) Elderly/Disabled Simplified Application Project (EDSAP) EDSAP reporting households include elderly (age 60 or more) or disabled (regardless of age) household members. Children (less than 18 years old) may also be included in EDSAP households, regardless of disability status. EDSAP households are certified for 36 months and must recertify at the end of their certification period. EDSAP households are not required to complete an Interim Report. During the certification period, EDSAP households must report changes in household composition and whenever any household member begins to receive earned income.
```


### cmr_034 — PA household defined term (rank-1: PARTIAL)

**Question**: What is a Public Assistance household for SNAP  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `365.110`  
**Notes**: ADVERSARIAL — defined term. 365.110 Definition of a Public Assistance (PA) Household  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.70  

#### Rank 1 — PARTIAL (sim 0.514)

- **Chunk ID**: `cmr_sec_361_200__001`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 2 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: The chunk defines SNAP household composition rules but does not specifically define what constitutes a 'Public Assistance household' for SNAP purposes.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (A) The following individuals living with others or groups of individuals liv...

(A) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals together even if they do not do so unless an exception applies:
(1) Spouse Rule. An individual living with his or her spouse must be in the same SNAP household as the spouse. Spouses shall not be granted separate household status. Spouse is defined as either of two individuals who are legally married to one another, or who are living together and holding themselves out to the community as husband and wife by representing themselves as spouses to relatives, friends, neighbors, or tradespeople;
(2) Parental Control Rule. A child younger than 18 years old, except for a foster care child (as defined in 106 CMR 361.240(F)), who is living with an adult household member (not the child's parent) and under the parental control of the adult household member, must be in the same SNAP household as the adult household member. Parental control means providing financial support or supervision, or both, to an individual younger than 18 years old; and
```

#### Rank 2 — RELEVANT (sim 0.510)

- **Chunk ID**: `cmr_sec_365_110__000`
- **Section**: `365.110` — Definition of a Public Assistance (PA) Household
- **Program**: SNAP
- **Judge reason**: Directly defines what constitutes a Public Assistance (PA) household for SNAP purposes under Massachusetts DTA regulations.

```
106 CMR 365 > SPECIAL > 365.110 Definition of a Public Assistance (PA) Household

PA households are those households in which all members receive a cash grant under one of the following programs: Transitional Aid to Families with Dependent Children (TAFDC), or Emergency Aid to the Elderly, Disabled, and Children (EAEDC). Even though a TAFDC Full Employment Program (FEP) household may not receive a cash grant, the household will be considered a PA household. The following households will also be considered PA households:
(1) households including an SSI recipient(s) when all the other members receive cash assistance under TAFDC, or EAEDC; and
(2) households including a child(ren) born after the Family Cap Date who is not included in the TAFDC grant when all other household members receive cash assistance under TAFDC, or EAEDC.
```

#### Rank 3 — PARTIAL (sim 0.481)

- **Chunk ID**: `cmr_sec_360_030__002`
- **Section**: `360.030` — Definitions
- **Chunk position**: 3 / 4
- **Program**: SNAP
- **Hierarchy**: (4) A place not designed for or ordinarily used as a regular sleeping accommo...
- **Judge reason**: The chunk defines 'Household' for SNAP purposes but does not define what constitutes a 'Public Assistance household' specifically.

```
106 CMR 360 > GENERAL > 360.030 Definitions > (4) A place not designed for or ordinarily used as a regular sleeping accommo...

(4) A place not designed for or ordinarily used as a regular sleeping accommodation for people (a hallway, a bus station, a lobby or similar place). Household. Any individual or group whose income and/or assets must be used to calculate SNAP benefits levels. Household Disaster. An emergency situation declared a disaster by the President or the Federal Emergency Management Agency. Disasters are defined as, but are not limited to, floods, hurricanes, earthquakes or fires. Household Misfortune. A loss of food due to, but not limited to, loss of power, fire or flood that is not declared a disaster by the President or the Federal Emergency Management Agency. (Mass. Register #1453 10/1/21) Means-tested Program. The following are federal or state means-tested programs (i.e., income is a factor in determining eligibility): Supplemental Nutrition Assistance Program (SNAP), Transitional Assistance to Families with Dependent Children (TAFDC), Emergency Aid to the Elderly, Disabled and Children (EAEDC), Emergency Assistance (EA), Supplemental Security Income (SSI), State Supplement Program (SSP) to SSI, Medicaid, State Child Health Insurance (SCHIP), Temporary Assistance for Needy Families (TANF), Food Assistance Programs in Puerto Rico, American Samoa and the Northern Mariana Islands (CNMI) and Veterans' Service benefits. Month. A cyclical month determined by the last digit of the Social Security number of the head of the household, unless otherwise specified.
```

#### Rank 4 — PARTIAL (sim 0.478)

- **Chunk ID**: `cmr_sec_361_160__000`
- **Section**: `361.160` — Handling Applications for Public Assistance (PA) Households
- **Program**: SNAP
- **Judge reason**: The chunk discusses procedures for PA households applying for SNAP but does not define what constitutes a Public Assistance household.

```
106 CMR 361 > THE > 361.160 Handling Applications for Public Assistance (PA) Households

To facilitate their participation in SNAP, households in which all members are applying for cash assistance shall be allowed to apply simultaneously for SNAP benefits. However, the household's SNAP eligibility and benefit level shall be based solely on SNAP eligibility criteria. The household shall be certified in accordance with the SNAP notice and processing standards even when these standards are different than those of the cash assistance program. See 106 CMR 365.100 through 365.180 for special procedures for taking and processing SNAP applications for these households.
```

#### Rank 5 — PARTIAL (sim 0.477)

- **Chunk ID**: `cmr_sec_361_200__002`
- **Section**: `361.200` — Household Concept/Definition
- **Chunk position**: 3 / 5
- **Program**: SNAP
- **Hierarchy**: (A) The following individuals living with others or groups of individuals liv...
- **Judge reason**: The chunk defines SNAP household composition rules but does not define what constitutes a 'Public Assistance household' as a distinct concept.

```
106 CMR 361 > THE > 361.200 Household Concept/Definition > (A) The following individuals living with others or groups of individuals liv...

(3) Parent/Child Rule. A child younger than 22 years old living with his or her natural, adopted or stepparent(s) must be in the same SNAP household as the parent(s).
(B) The following individuals living with others or groups of individuals living together shall be considered as purchasing food and preparing meals separately even if they do not do so.
(1) An individual, with or without children, residing in a drug or alcohol treatment center shall be one SNAP household separate from the other residents. See 106 CMR 365.600 through 365.690.
(2) A blind or disabled resident of a group living arrangement (106 CMR 365.600 through 365.690) who applies through the use of the facility's authorized representative shall be one SNAP household separate from the other residents. If a blind or disabled resident applies on his or her own behalf, the household size must be determined following the household concept rules defined in 106 CMR 361.200.
(3) An individual, with or without children, residing in a shelter for battered individuals and their children shall be one SNAP household separate from the other residents. See 106 CMR 365.550: Residents of Shelters for Battered Women and Their Children.
```


### cmr_035 — EDP defined term (rank-1: RELEVANT)

**Question**: What is an Employment Development Plan  
**Program filter**: (none)  
**Expected section (for reference)**: `707.110` — judge picked rank-1 RELEVANT chunk in section `707.110` (section-author intuition agrees)  
**Notes**: ADVERSARIAL — defined term/acronym. 707.110 Completion of an Employment Development Plan (EDP)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.499)

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

#### Rank 2 — PARTIAL (sim 0.496)

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

#### Rank 3 — PARTIAL (sim 0.494)

- **Chunk ID**: `cmr_sec_707_140__000`
- **Section**: `707.140` — Educational Component
- **Chunk position**: 1 / 5
- **Program**: EA
- **Judge reason**: The chunk mentions Employment Development Plan (EDP) by name and indicates it's an approved plan related to employment services, but does not define what an EDP actually is or explain its components and purpose.

```
106 CMR 707 > EMPLOYMENT SERVICES > 707.140 Educational Component

The Educational Component provides educational services to individuals to prepare him or her to obtain and maintain employment. Participation is subject to available program resources, the individual's approved Employment Development Plan (EDP), and the criteria in 106 CMR 707.140(A) through (D):
```

#### Rank 4 — PARTIAL (sim 0.459)

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

#### Rank 5 — PARTIAL (sim 0.459)

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


### cmr_036 — SNAP allowed uses (rank-1: RELEVANT)

**Question**: What can SNAP benefits be used to purchase  
**Program filter**: `['SNAP']`  
**Expected section (for reference)**: `360.100` — judge picked rank-1 RELEVANT chunk in section `360.100` (section-author intuition agrees)  
**Notes**: 360.100 Uses of SNAP Benefits (covers chapter 360 which is otherwise underrepresented)  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — RELEVANT (sim 0.531)

- **Chunk ID**: `cmr_sec_360_100__000`
- **Section**: `360.100` — Uses of SNAP Benefits
- **Program**: SNAP
- **Judge reason**: Directly states what SNAP benefits can be used to purchase (eligible foods, seeds, and plants for home consumption)

```
106 CMR 360 > GENERAL > 360.100 Uses of SNAP Benefits

SNAP benefits are to be used by clients to buy eligible foods, including seeds and plants, for home consumption and use. The household may permit other persons to purchase food for the household. Such persons need not be pictured on the EBT card. Households are not required to have cooking facilities to receive SNAP.
```

#### Rank 2 — PARTIAL (sim 0.485)

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

#### Rank 3 — PARTIAL (sim 0.474)

- **Chunk ID**: `cmr_sec_361_330__000`
- **Section**: `361.330` — Authorized Representative to Purchase Food
- **Program**: SNAP
- **Judge reason**: The chunk addresses who can purchase food with SNAP benefits and procedural requirements, but does not specify what types of food or items are authorized for purchase.

```
106 CMR 361 > THE > 361.330 Authorized Representative to Purchase Food

The authorized representative may use SNAP benefits to purchase food for the household's consumption with the full knowledge and consent of the household. The authorized representative must have a Mass EBT Card in his or her own name when purchasing food with SNAP benefits.
```

#### Rank 4 — PARTIAL (sim 0.456)

- **Chunk ID**: `cmr_sec_364_900__000`
- **Section**: `364.900` — Delivery of Benefits
- **Chunk position**: 1 / 8
- **Program**: SNAP
- **Judge reason**: The chunk mentions that SNAP benefits can be used for 'food purchases' at specific locations but does not provide the detailed list of eligible food items that can be purchased.

```
106 CMR 364 > DETERMINING > 364.900 Delivery of Benefits

Eligible households shall be issued SNAP benefits for each month of eligibility. SNAP benefits can be accessed by using an Electronic Benefit Transfer (EBT) card for food purchases at grocery and other participating stores and farmers markets.
```

#### Rank 5 — PARTIAL (sim 0.443)

- **Chunk ID**: `cmr_sec_360_120__003`
- **Section**: `360.120` — Special Uses of SNAP Benefits
- **Chunk position**: 4 / 6
- **Program**: SNAP
- **Hierarchy**: (D) Meal Purchases for Residents of Group Living Arrangements.
- **Judge reason**: Addresses a specific use case for SNAP benefits (meal purchases in group living arrangements) but doesn't comprehensively answer what SNAP benefits can generally be used to purchase.

```
106 CMR 360 > GENERAL > 360.120 Special Uses of SNAP Benefits > (D) Meal Purchases for Residents of Group Living Arrangements.

(D) Meal Purchases for Residents of Group Living Arrangements. Eligible residents of group living arrangement facilities who are blind or disabled as defined in 106 CMR 361.210: Elderly or Disabled Individuals and acting on their own behalf may use SNAP benefits to buy meals prepared and served at the facility especially for them, if:
(1) the facility is authorized by FNS to transact SNAP benefits through wholesalers;
(2) the facility transacts SNAP benefits at retail food stores as the authorized representative of participating households; or
(3) the organization or institution is authorized by FNS as a retailer. NON-TEXT PAGE
```


### cmr_037 — TCAP application interview (rank-1: PARTIAL)

**Question**: How do I apply for TAFDC and what happens at the application interview  
**Program filter**: `['EA']`  
**Expected section (for reference)**: `702.120`  
**Notes**: 702.120 The Application Interview (covers chapter 702 which is otherwise unrepresented)  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.554)

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

#### Rank 2 — PARTIAL (sim 0.554)

- **Chunk ID**: `cmr_sec_702_110__000`
- **Section**: `702.110` — The Application Process
- **Program**: EA
- **Judge reason**: Defines what the application process is but doesn't explain how to apply or what happens at the interview itself.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.110 The Application Process

The application process consists of all the activities used to determine the eligibility of a TAFDC or EAEDC applicant. These activities start with the filing of an application and concluded with a final disposition of the application.
```

#### Rank 3 — PARTIAL (sim 0.541)

- **Chunk ID**: `cmr_sec_702_120__005`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 6 / 9
- **Program**: EA
- **Hierarchy**: (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
- **Judge reason**: Addresses what happens during the application interview (PATH program requirements) but does not explain how to apply for TAFDC or the initial application process itself.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.

(G) Pathways to Self-sufficiency Program (PATH) for TAFDC Applicants.
(1) TAFDC applicants 18 years of age or older shall participate in an intake and employment assessment process which may result in referrals to appropriate employment or education/training opportunities. The Department shall deny applications for either the entire assistance unit or the grantee if the applicant fails to participate in PATH without good cause.
(2) Under PATH, certain TAFDC applicants may also be subject to a Work Ready Job Diversion Program:
(a) Applicants 18 years of age or older who are determined by the Department to have the necessary job skills and experience must participate in a Work Ready Job Diversion Program.
(b) Applicants will be exempted from the Work Ready Job Diversion Program if they will be exempt from the work program (See 106 CMR 703.150: TAFDC Work Program) or have requested a disability exemption (See 106 CMR 703.100: TAFDC Exemptions from Time-limited Benefits and Reduced Need and Payment Standards).
(c) Applicants subject to the Work Ready Job Diversion Program must provide evidence of three job search contacts. Applicants must accept referrals to any appropriate Department-identified jobs.
(d) If no evidence of participation in the Work Ready Job Diversion Program is provided prior to day 30 of the application, the TAFDC application for the entire assistance unit will be denied. If the case is approved but there is no further participation
```

#### Rank 4 — PARTIAL (sim 0.530)

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

#### Rank 5 — PARTIAL (sim 0.507)

- **Chunk ID**: `cmr_sec_702_120__001`
- **Section**: `702.120` — The Application Interview
- **Chunk position**: 2 / 9
- **Program**: EA
- **Hierarchy**: (B) Identification of the Applicant.
- **Judge reason**: Addresses only one specific aspect of the application interview (identification requirements) but does not cover the overall application process or what happens during the interview more broadly.

```
106 CMR 702 > TRANSITIONAL CASH ASSISTANCE PROGRAM > 702.120 The Application Interview > (B) Identification of the Applicant.

(B) Identification of the Applicant. The worker must establish the identity of the applicant. Proof of identity may be a Social Security number, driver’s license, voter registration card, military service papers, marriage license, employment papers or any of the items provided in 106 CMR 703.220: TAFDC Dependent Child: Younger than 18 Years Old or 106 CMR 703.810: EAEDC Identification of the Applicant used in the verification of age.
```

