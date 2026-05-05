# OLG Retrieval Benchmark — hybrid-dense-weighted

**Run**: 2026-05-04T21:24:05  
**Source**: olg  
**Label**: hybrid-dense-weighted  
**Top-N retrieved + judged**: 5  
**Embedding model**: `voyage-context-3`  
**Judge model**: `claude-haiku-4-5-20251001`  
**Methodology**: LLM-as-judge — Claude Haiku rates each chunk RELEVANT / PARTIAL / IRRELEVANT.  
**Benchmark**: OLG retrieval benchmark v2 — covers SNAP/TAFDC/EAEDC/Cross-Program/BP/Verification Chart, mixed difficulty, includes adversarial cases for hybrid/rerank testing  

## Summary

| Metric | Value | Notes |
|---|---|---|
| Relevance@1 | 11/24 (46%) | Did rank 1 = RELEVANT? |
| Relevant@5 (avg) | 1.75 / 5 | Avg # of RELEVANT chunks in top 5 |
| Useful@5 (avg) | 4.96 / 5 | Avg # of (RELEVANT or PARTIAL) chunks in top 5 |
| Mean rank-weighted score | 1.848 / 2.7 | Sum of (weight × score) over top 5; weights [1.0, 0.7, 0.5, 0.3, 0.2]; score RELEVANT=1.0 / PARTIAL=0.5 / IRRELEVANT=0.0 |

## Quick Summary Table

| # | ID | Topic | Rank-1 Judge | Rank-1 Sim Score | Relevant@5 | Useful@5 | RW |
|---|---|---|---|---|---|---|---|
| 1 | olg_001 | SSN missing for newborn | RELEVANT | 0.602 | 3 | 4 | 2.25 |
| 2 | olg_002 | homeless verification | **PARTIAL** | 0.529 | 0 | 5 | 1.35 |
| 3 | olg_003 | self-employment allowable expenses | **PARTIAL** | 0.475 | 0 | 5 | 1.35 |
| 4 | olg_004 | college student eligibility | **PARTIAL** | 0.499 | 2 | 5 | 1.85 |
| 5 | olg_005 | non-citizen SNAP exclusions | RELEVANT | 0.617 | 3 | 5 | 2.10 |
| 6 | olg_006 | roomer/boarder income | RELEVANT | 0.594 | 3 | 5 | 2.45 |
| 7 | olg_007 | medical deduction thresholds | **PARTIAL** | 0.415 | 0 | 5 | 1.35 |
| 8 | olg_008 | dependent care deduction | RELEVANT | 0.551 | 4 | 5 | 2.45 |
| 9 | olg_009 | lump sum income treatment | RELEVANT | 0.480 | 5 | 5 | 2.70 |
| 10 | olg_010 | TAFDC time limit | RELEVANT | 0.639 | 2 | 5 | 2.20 |
| 11 | olg_011 | ESP participation | **PARTIAL** | 0.333 | 0 | 5 | 1.35 |
| 12 | olg_012 | child support good cause | **PARTIAL** | 0.571 | 0 | 5 | 1.35 |
| 13 | olg_013 | teen parent eligibility | **PARTIAL** | 0.525 | 0 | 5 | 1.35 |
| 14 | olg_014 | EAEDC disability standard | **PARTIAL** | 0.516 | 0 | 5 | 1.35 |
| 15 | olg_015 | EAEDC categorical eligibility | **PARTIAL** | 0.531 | 0 | 5 | 1.35 |
| 16 | olg_016 | application timeliness | RELEVANT | 0.450 | 2 | 5 | 2.00 |
| 17 | olg_017 | residency verification | **PARTIAL** | 0.497 | 2 | 5 | 1.75 |
| 18 | olg_018 | fair hearing rights | **PARTIAL** | 0.424 | 1 | 5 | 1.50 |
| 19 | olg_019 | overpayment classification | **PARTIAL** | 0.395 | 0 | 5 | 1.35 |
| 20 | olg_020 | DV disclosure procedure | RELEVANT | 0.637 | 4 | 5 | 2.45 |
| 21 | olg_021 | ABAWD acronym | RELEVANT | 0.356 | 2 | 5 | 2.00 |
| 22 | olg_022 | VC-1 form lookup | RELEVANT | 0.293 | 4 | 5 | 2.45 |
| 23 | olg_023 | ESP exemptions | **PARTIAL** | 0.380 | 0 | 5 | 1.35 |
| 24 | olg_024 | expedited timing | RELEVANT | 0.363 | 5 | 5 | 2.70 |

---

## Per-Question Detail

Top 5 results per question with judge verdicts and full chunk text. Use this to spot-check whether the judge's rating makes sense.

### olg_001 — SSN missing for newborn (rank-1: RELEVANT)

**Question**: A client applies for SNAP with their two children. They provide an SSN for themselves and the oldest child, but the second, a newborn, does not have an SSN yet. All are US citizens. How do I process the case without the child's SSN?  
**Program filter**: `['SNAP']`  
**Notes**: SSN policy — applicants without SSN, newborn carve-out, BEACON entry. Procedural lookup.  
**Scores**: Relevant@5 = 3, Useful@5 = 4, rank-weighted = 2.25  

#### Rank 1 — RELEVANT (sim 0.602)

- **Chunk ID**: `sec__SNAP__Eligibility__HH_AddNewPersonSNAP__005`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses how to process a SNAP case when a newborn lacks an SSN, including the use of a Systems Generated SSN and the six-month presumptive eligibility period.

```
SNAP > Eligibility Requirements > Household Composition > Add a New Person as a SNAP Household Member > Verifying SSNs for Newborn Children

In many cases, a newborn child will not have an SSN when the household reports that s/he was born or adopted. Alternatively, the household may submit verification that an SSN application has been filed on the newborn’s behalf through SSA.

However, if the household can neither self-declare nor provide proof of application for the newborn’s SSN when the his/her presence in the home is first reported, the newborn shall be eligible to receive SNAP benefits until the household’s next recertification or the sixth month following the month in which s/he was born, whichever is later.

Reminder : Pending the return of the SSN verification, the newborn should be issued a Systems Generated SSN. For more information, see Alternative Social Security Numbers (SSNs) - SNAP .

If, by either of these times, the Department still has not received verification of SSN or SSN application, you must determine if the household has good cause for not complying with the Department’s SSN requirement.

If good cause cannot be established (see Social Security Number for good cause criteria), the newborn must be disqualified and removed from the household.

Note : The six-month period of presumptive eligibility only applies to newborns. If the new household member is not a newborn, then s/he cannot be added to the household until his/her SSN is provided orally or in writing, or we receive verification of his/her SSN application.
```

#### Rank 2 — RELEVANT (sim 0.572)

- **Chunk ID**: `sec__SNAP__Eligibility__HH_AddNewPersonSNAP__006`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses how to process SNAP cases when a newborn child lacks an SSN, explaining the timeline for verification and that benefits can continue during the grace period.

```
SNAP > Eligibility Requirements > Household Composition > Add a New Person as a SNAP Household Member > Verifying SSNs for Newborn Children > Examples of Verifying a Newborn Child’s SSN

Example 1

Carolyn reports on October 10 that she gave birth on October 3, but is unable to provide verification that she filed an SSN application for her child. Carolyn’s certification period does not end until June 30. The sixth month following the child’s birth month is April. Since the certification period ends later than April, Carolyn’s child can continue receiving SNAP benefits until June 30 before Carolyn has to verify her child’s SSN or SSN application.

Example 2

Heather reports on November 20 that she gave birth on November 17, but is unable to provide verification that she filed an SSN application for her child. Heather’s certification period ends on December 31. The sixth month following the child’s birth month is May. Because the sixth month is later than the certification end date, Heather’s child can continue receiving SNAP benefits until May 31 before Heather must verify her child’s SSN or SSN application.

Important : When a newborn is assigned a Systems Generated SSN, SSA may automatically verify his or her SSN through the EVS Batch Process by matching the reported name, date of birth, and gender. For more information, see Facsimile and Systems Generated Social Security Numbers (SSNs) Cleanup .
```

#### Rank 3 — PARTIAL (sim 0.594)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_CubanHatianSNAP__003`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Addresses SSN procedures for clients without SSNs, but specifically for Cuban/Haitian Entrants rather than general SNAP applicants, and doesn't directly address processing cases with missing child SSNs.

```
SNAP > Eligibility Requirements > Noncitizen > Eligible Qualified Noncitizens > Cuban/Haitian Entrant - SNAP > Application Processing for Cuban/Haitian Entrants > Social Security Number for Cuban/Haitian Entrants

New applicants from Cuba or Haiti will likely apply for DTA benefits before they have been issued a Social Security Numbers (SSN). If a client does not provide an SSN at application or reports that they do not have an SSN at application, they must be assigned a Systems Generated 99#.

When you enter a new client in BEACON, an auto populated verification for the SSN or Proof of Application will populate. You must disposition the auto populated verification request as verified, and issue a User Entered, optional VC-1 for Additional Verification entering in the Details field: Social Security Number or Proof of SSN Application. In the Document(s) of evidence field enter:

“Tell us this person’s Social Security Number; you can call and tell us. If this person doesn’t have a Social Security Number, you must provide proof that this person has applied for one.”

Because the SSN verification request is marked Optional, the case will not be denied for failure to provide this verification which many Cuban/Haitian Entrants cannot provide before interacting with an agency such as DTA. More information below in Good Cause for Not Providing a Social Security Number .
```

#### Rank 4 — RELEVANT (sim 0.565)

- **Chunk ID**: `sec__SNAP__Eligibility__SSN_AlternativeNumbersSNAP__003`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses how to process SNAP cases when a household member (including children) has applied for but not yet received an SSN by using systems-generated numbers and documenting the SSN application date.

```
SNAP > Eligibility Requirements > Social Security Number > Alternative Social Security Numbers (SSNs) - SNAP > Systems Generated SSN

Systems generated 990 or 999 numbers are assigned to clients who have applied for, but have not yet received an SSN or are unable to obtain or unwilling to give their SSN due to his or her immigration status. Clients who have applied for an SSN will have their systems generated SSN changed to a Security Administration (SSA) issued SSN through a data exchange with SSA. Clients who do not provide an SSN will not receive a Social Security Administration (SSA) issued SSN through this data exchange.

When adding a client on BEACON who has applied for and is awaiting an SSN, enter the SSN application date on the Assessed Person page. If the client has not applied for an SSN, check Unable to Obtain an SSN.

Before leaving the page, a message will appear asking if a systems generated number should be assigned to the client. Answer Yes.

Use the Assessed Person page to enter or update all additional or alternate SSNs for a household member. Access this page via the RFA workflow or in the AU Composition workflow, as appropriate.

Related Topics Social Security Number Policies and Procedures Last Update: June 10, 2025
```

#### Rank 5 — IRRELEVANT (sim 0.512)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_CubanHatianSNAP__008`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: This chunk addresses SSN requirements for Cuban/Haitian Entrants without work permits, not the general SNAP processing procedure for US citizen children without SSNs.

```
SNAP > Eligibility Requirements > Noncitizen > Eligible Qualified Noncitizens > Cuban/Haitian Entrant - SNAP > Non-Work SSN Letter

Some Cuban Haitian Entrants are not eligible to receive a Social Security Number (SSN) because they do not have a work permit. To get DTA benefits, these individuals must apply for a Non-Work SSN. To apply for a non-work SSN, they must provide a letter from DTA to SSA. SSA is required to provide Non-work SSNs to applicants who are otherwise eligible for government benefits as these programs all have a Social Security Number requirement.

Any Cuban/Haitian Entrant that does not have a work permit (employment authorization card) will require a Non-Work SSN Letter. To determine if a Cuban/Haitian case meets the requirement for a Non-Work SSN, follow the instruction outlined below:

- If the client did not provide a work permit (employment authorization card) as part of their verifications, but they are otherwise eligible as a Cuban/Haitian Entrant, you must forward the case details [e.g., Grantee’s APID, Grantee name, the name(s) of additional household member(s), the documentation used to determine eligibility and the date it was received in the client’s ECF] to your supervisor.
```


### olg_002 — homeless verification (rank-1: PARTIAL)

**Question**: What are the standard requirements to verify that a client is homeless?  
**Program filter**: `['SNAP']`  
**Notes**: Verification list for homeless status. Should pull SNAP eligibility / shelter pages.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.529)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__HH_EnteringHHData__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk describes how to designate a client as homeless in BEACON (the system), but does not explain the standard requirements or verification criteria for determining homelessness status.

```
SNAP > Expenses and Deductions > Household Expenses > Homeless Households > Entering Homeless Households Data > Designate the Client as Homeless

The Address page of BEACON is also used to indicate Homelessness in addition to capturing residential, permanent, and mailing addresses.

1. access the Address page and if the client is homeless, click Homeless checkbox
2. for Current Residence (2a) and Permanent Residence (2b), select None
3. in the Mailing Address section, click the Mailing Address popup icon

  a. Important If the client does not have a Current Residence or Permanent Residence address, you must still enter a mailing address.
4. enter the Address
5. click Next to save and go to the next page in the workflow, or click Finish to save and to exit the page and the workflow

Note : When the Homeless Indicator on the Address page is checked, BEACON will automatically determine whether the household will receive the Shelter Deduction for Homeless Households or the actual Shelter Expenses Deduction , whichever is higher.

Important : To remove the Homeless Indicator, click on the Homeless checkbox to remove the checkmark. The Homeless Indicator must be reviewed whenever a client flagged as “homeless” reports a change in address (mailing, current, and/or permanent), shelter expenses, and/or utility expenses. Shelter Deduction for Homeless Households.
```

#### Rank 2 — PARTIAL (sim 0.504)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__HH_ShelterDeduction__001`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses shelter deductions and expenses for homeless households but does not address the verification requirements or standards for determining whether a client is homeless.

```
SNAP > Expenses and Deductions > Household Expenses > Homeless Households > Shelter Deduction for Homeless Households > Homeless Shelter/Utility Deduction

Households in which all members are homeless and live in a homeless shelter or with someone else who incurs or reasonably expects to incur shelter or utility expenses are eligible for the standard homeless shelter/utility deduction. Certain homeless households temporarily living in the home of someone else are allowed actual shelter expenses and the appropriate SUA, provided the client verifies that the shelter expenses s/he incurs exceed the standard homeless shelter/utility deduction.

Households that receive the standard homeless shelter/utility deduction are neither entitled to the shelter deduction nor the standard utility allowance since the homeless shelter/utility deduction already includes both shelter and utility costs. For homeless households, you must verify and enter shelter expenses only when the actual shelter expenses incurred by the client will yield a shelter deduction that is higher than the Homeless shelter/utility deduction.
```

#### Rank 3 — PARTIAL (sim 0.480)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__SU_AllowanceExpIntro__005`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses benefits for homeless households but does not address the verification requirements or standards for determining homelessness status.

```
SNAP > Expenses and Deductions > Household Expenses > Standard Utility Expenses > Standard Utility Allowance Expense Introduction > Homeless Households Deduction

Households in which all members are homeless and live in a homeless facility who incur or reasonably expect to incur any shelter or utility expenses during a month are eligible for the standard homeless shelter/utility deduction .
```

#### Rank 4 — PARTIAL (sim 0.445)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__HH_ShelterDeduction__006`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses managing the Homeless Indicator in BEACON systems but does not explain the actual verification requirements or procedures for determining homelessness status.

```
SNAP > Expenses and Deductions > Household Expenses > Homeless Households > Shelter Deduction for Homeless Households > SUA is Being Changed

When a change is made to a client’s expenses in the Standard Utility Allowance page and the Homeless Indicator is checked, BEACON will create a hard-edit for you to revisit the Address page and generate a pop-up. This will occur if a case is active or a household known to BEACON has reapplied. The pop-up will read:

In each case, you must review the Address page and check or uncheck the Homeless Indicator as applicable.

Important : Failure to uncheck the Homeless Indicator for clients that are no longer homeless will prevent them from receiving H-EAT benefits for which they may be qualified. For more information, see Heat and Eat. This will also cause large underpayment errors.

Related Topics Entering Homeless Households Data Homeless Households Policy and Procedures Last Update: February 21, 2019
```

#### Rank 5 — PARTIAL (sim 0.457)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__HH_ShelterDeduction__005`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses system procedures for homeless households in SNAP but does not explain the actual verification requirements or standards for determining homelessness status.

```
SNAP > Expenses and Deductions > Household Expenses > Homeless Households > Shelter Deduction for Homeless Households > Shelter Expense is Being Changed

When a change is made to a client’s expenses in the Shelter Expense page and the Homeless Indicator is checked, BEACON will create a hard-edit for you to revisit the Address page and generate a pop-up. This will occur if a case is active or a household known to BEACON has reapplied. The pop-up will read:
```


### olg_003 — self-employment allowable expenses (rank-1: PARTIAL)

**Question**: What kind of expenses are self-employed clients able to claim for their income?  
**Program filter**: `['SNAP']`  
**Notes**: Self-employment cost-of-doing-business deduction. Specific allowable/non-allowable expenses.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.475)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_SNAP__018`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk mentions that self-employed clients may provide business expenses and that some expenses are not allowed as deductions, but it does not specify what kinds of expenses are actually allowed or disallowed.

```
SNAP > Eligibility Requirements > Income > Self Employment > Self-Employment SNAP > Self-Employment Examples > 1099 Income

Chad is a driver for Uber. He receives a 1099 form each year for his gross income. He incurs business expenses and keeps a personal record of them.

Chad is considered self-employed for SNAP purposes. He must supply business records that verify his gross income and may provide optional business expenses. You must review the expenses to determine whether there are any expenses that are not allowed as deductions for SNAP. If there are expenses meeting those criteria, you must not give credit for them.

Note : For Uber and Lyft specifically, drivers may receive a 1099-K and/or a 1099 MISC depending on the amount of income earned. This may also vary if the driver received non-driving income types such as bonuses or referral fees.
```

#### Rank 2 — PARTIAL (sim 0.497)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_SNAP__013`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk explains what expenses are NOT allowed rather than what expenses ARE allowed for self-employed clients to claim.

```
SNAP > Eligibility Requirements > Income > Self Employment > Self-Employment SNAP > Expenses Not Allowed as a Cost of Doing Business

For SNAP only clients, expenses not allowed as a cost of doing business include but are not limited to:

- net losses from previous periods of time
- federal, state and local income taxes, money set aside for retirement purposes and other work-related personal expenses (such as transportation to and from work); these expenses are accounted for by the earned income deduction
- depreciation

Note : When determining expedited eligibility for households with self-employment income, the averaged or prorated monthly self-employment income amount minus the allowable costs of doing business must be used.
```

#### Rank 3 — PARTIAL (sim 0.417)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_SNAP__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk defines self-employment and mentions that self-employed individuals 'incur costs in producing income' but does not specify what types of expenses can actually be claimed.

```
SNAP > Eligibility Requirements > Income > Self Employment > Self-Employment SNAP > Self-Employment Determination

In general, self-employed individuals:

- incur costs in producing income;
- control their work by working either independently of an employer, freelance, or by running the business;
- assume all risks and responsibilities of a business enterprise; and
- are subject to self-employment tax in addition to income tax on net income from self-employment activities; self-employment tax is paid in lieu of Social Security payments.

During the interview, the amount of hours the client worked must be reviewed and entered into BEACON to properly screen for ABAWD Work Program Requirements.

Rental, roomer, and boarder income types are treated as self-employment for SNAP purposes. Rental, Roomer, and Boarder Income

Important : SNAP only clients who are paid in cash but have no business expenses are not considered self-employed. Income received in these situations must be entered as wages in BEACON
```

#### Rank 4 — PARTIAL (sim 0.395)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_SNAP__017`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses self-employment income verification but does not explain what types of business expenses self-employed clients can claim.

```
SNAP > Eligibility Requirements > Income > Self Employment > Self-Employment SNAP > Self-Employment Examples > Cash Income

Kwame babysits for his neighbor Jill for 20 hours a week and makes $12 per an hour. He incurs no business expenses to watch Jill’s child. Kwame is paid in cash and does not receive a W-2 or 1099 form for tax filing purposes.

Based on the case details, Kwame is not considered self-employed. He is paid in cash and does not incur any business expenses. Therefore to verify his income, he must submit a letter from his employer Jill verifying his gross income, the amount of hours he works, and the frequency the income is received.
```

#### Rank 5 — PARTIAL (sim 0.376)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__DC_Examples__004`
- **Section**: `` — 
- **Chunk position**: 5 / 9
- **Program**: SNAP
- **Judge reason**: The chunk discusses dependent care expenses for SNAP recipients but does not address what expenses self-employed clients can claim for their income.

```
SNAP > Expenses and Deductions > Dependent Care Expenses > Dependent Care Expense - Examples

Q8 . Lawrence Tyson is the grantee of a SNAP-only household and is receiving a TSS Transportation Stipend. Lawrence wishes to claim mileage in addition to his previously verified dependent care expenses for his daughter Livia, 8. Is mileage an allowable dependent care expense for Lawrence?

A8 . Yes. Even though Lawrence is receiving a TSS transportation stipend, he is still able to claim mileage as a dependent care expense as the stipend is issued to defray costs associated with travelling to and from a client’s home and place of work, not for dependent care.

Q9 . Amy is the grantee of a three person assistance unit that includes her daughter, Lori age 3, and her boyfriend Jason, age 34. Jason is not Lori’s father. Amy is employed full time. Jason is neither employed nor receiving unemployment, and is not enrolled in an education or training program. Amy wishes to claim dependent care expenses as she states she does not have Jason watch Lori, preferring to have Lori in structured daycare. Is this household eligible for dependent care expenses?
```


### olg_004 — college student eligibility (rank-1: PARTIAL)

**Question**: What eligibility requirements are there for clients who specifically are college students?  
**Program filter**: `['SNAP']`  
**Notes**: SNAP student rules — half-time enrollment threshold, exemption list (work hours, dependent care, work-study, etc.).  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.85  

#### Rank 1 — PARTIAL (sim 0.499)

- **Chunk ID**: `sec__SNAP__Eligibility__Stu_Students__052`
- **Section**: `` — 
- **Chunk position**: 9 / 9
- **Program**: SNAP
- **Judge reason**: The chunk provides specific examples of eligible college students but does not comprehensively list the actual eligibility requirements or criteria for college students in SNAP.

```
SNAP > Eligibility Requirements > Students > Student Examples

A14 : Yes. Since Quincy College offers eligible CTE programs under Perkins IV or programs that would lead to employment, Jodie is considered an eligible college student by being enrolled at Quincy College regardless of the type of degree Jodie is enrolled in.

Q15 : Tabitha (she/her) is appl ying for herself and her 2 college students: Willy (he/him) aged 2 0 , and Rosie (she/her) a ge 21. Willy is an eligible student because he receives a MassGrant. Rosie provided a self-declaration that she has reasonable accommodation through her university’s disability accommodation’s office. Does Rosie qualify as an eligible college student ?

A15 : Yes. Rosie qualifies as an eligible college student under the “mentally/physically unfit for employment” student exemption since Rosie has self-declared they are receiving support from her university’s reasonable accommodation’s office.

Related Topics Earned Income Policy and Procedures Other Income Introduction Students Policy and Procedures Last Update: January 26, 2026
```

#### Rank 2 — RELEVANT (sim 0.512)

- **Chunk ID**: `sec__SNAP__Eligibility__HH_SNAP__003`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses eligibility requirements for college students by specifying that those on meal plans providing more than 50% of meals are ineligible for SNAP.

```
SNAP > Eligibility Requirements > Household Composition > Household Composition - SNAP > Ineligible Clients

- residents of commercial boarding houses
- residents of institutions that provide more than 50% of meals as part of their regular services (see 106 CMR 361.240 for exceptions to this rule)
- college students on meal plans (if the plan provides more than 50% of meals, the student is not eligible)
- strikers

  - Note : In very limited situations, strikers are eligible. (See: 106 CMR 361.240)
- boarders who are not residents of commercial boarding houses.  See 106 CMR 361.240 for specific requirements

Related Topics SNAP Household Composition Job Aid Household Composition Policy and Procedures - SNAP Last Update: April 4, 2019
```

#### Rank 3 — PARTIAL (sim 0.482)

- **Chunk ID**: `sec__SNAP__Eligibility__Stu_Students__022`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk describes a screening procedure for college students but does not actually specify what the eligibility requirements are for them.

```
SNAP > Eligibility Requirements > Students > Conversation With a Household Member About Student Eligibility

When a client indicates that they or a household member is a college student, you must ask them to indicate the name of the college they attend. If this is not a community college, you must continue to screen for student eligibility. You must start with eligibility requirements that are based on household circumstances.
```

#### Rank 4 — RELEVANT (sim 0.494)

- **Chunk ID**: `sec__SNAP__Eligibility__Stu_Students__023`
- **Section**: `` — 
- **Chunk position**: 1 / 5
- **Program**: SNAP
- **Judge reason**: Directly addresses specific eligibility requirements for college students in SNAP, including exceptions for students enrolled in higher education institutions and various household circumstances.

```
SNAP > Eligibility Requirements > Students > Conversation With a Household Member About Student Eligibility > Eligibility Based on Household Circumstances

This is likely to be information we would have in BEACON.

- are they receiving TAFDC and/or enrolled in a TAFDC Pathways to Work program,
- is there a child in the household under 6 years old,
- are they responsible for the care of a dependent household member who is between the ages of 6 and 12 for whom adequate childcare is not available to enable the student to attend school and work a minimum of 20 hours per week,
- are they a single parent enrolled full-time in an institution of higher education and responsible for the care of a dependent child under the age of 12 regardless of the availability of adequate childcare,
- are they working an average of 20 hours per week, or
- are they federally certified as disabled?

If the student does not meet student eligibility criteria based on being enrolled in a community college or for any of the household circumstances mentioned above, you must ask the student if they:

- have received any documentation such as their financial aid award letter, an email/letter from the Department of Education, or Student Aid Report (SAR) stating they have been awarded a MassGrant.
```

#### Rank 5 — PARTIAL (sim 0.483)

- **Chunk ID**: `sec__SNAP__Eligibility__Stu_Students__046`
- **Section**: `` — 
- **Chunk position**: 3 / 9
- **Program**: SNAP
- **Judge reason**: The chunk provides examples of student eligibility scenarios but does not explicitly state the actual eligibility requirements for college students (such as what qualifies them, income limits, or specific criteria).

```
SNAP > Eligibility Requirements > Students > Student Examples

Q5. Drew (he/they) is an ineligible college student as they do not meet any eligibility requirements for a college student. Drew is now off for the summer and plans to continue college in the Fall. Nothing has changed on the case. Can Drew be considered an eligible college student?

A5 . Drew would still be considered an ineligible college student even in the summer as they still do not meet the student status rules.

Q6 . Andrea (she/her) was disqualified from SNAP during the school year because she was receiving a majority of their meals at school. However, Andrea was considered an eligible college student as she received the MassGrant. Andrea is now off for the summer and moved back home with her parents. Can Andrea be considered an eligible college student?

A6 . Since the client is not boarding at this time, Andrea can now be considered an eligible college student as they are receiving the MassGrant. You must not go in at the end of the summer and remove the client or mark the client as Institutionalized based on Simplified Reporting rules. The next reporting period will adjust the client’s eligibility status.
```


### olg_005 — non-citizen SNAP exclusions (rank-1: RELEVANT)

**Question**: What non-citizenship designations are excluded from SNAP?  
**Program filter**: `['SNAP']`  
**Notes**: Multi-section topic — qualified vs non-qualified non-citizens, ineligible statuses, sponsored aliens.  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.10  

#### Rank 1 — RELEVANT (sim 0.617)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_IntroSNAP__005`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk directly lists the specific noncitizen designations that are excluded from SNAP eligibility, which is exactly what the user is asking about.

```
SNAP > Eligibility Requirements > Noncitizen > Noncitizen Introduction - SNAP > Ineligible Legal Noncitizen Status

An individual present in the U.S. under conditions or sections of the INA not described above, notwithstanding a legal noncitizen, is ineligible for SNAP benefits. Their income or assets shall be considered for the remaining household members The following legal noncitizen designations are not eligible for SNAP:

- Asylees
- Refugees
- Noncitizens with an order granting withholding of deportation
- Parolees (with the exception of individuals paroled from Cuba or Haiti)
- Special Humanitarian Parolees (e.g. Ukrainian Humanitarian parolees, Iraqi and Afghan special immigrants, Afghan non-SI Parolees, etc.)
- Victims of Severe Forms of Trafficking
- Members of Hmong, Highland Laotian tribes
- Nonimmigrants
- PRUCOLs

Important: Some of the noncitizen designations outlined above (such as Asylees, Refugees, Parolees, Victims of Trafficking, Members of Hmong, Highland Laotian tribes, Special Humanitarian Parolees, Deportation Withheld , etc.) that no longer meet SNAP eligibility requirements, may have been applied to noncitizens who have already adjusted to LPR status. For this reason, it is important that staff ensure that noncitizens who have adjusted to LPR status from a prior status be coded as Legal Permanent Resident on the Noncitizen Designation page of BEACON.
```

#### Rank 2 — PARTIAL (sim 0.578)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_EnteringNCDataSNAP__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk lists noncitizen designations that ARE eligible for SNAP (like LPR, Refugee, Asylee) and mentions that 'Undetermined' noncitizens are NOT eligible, but does not comprehensively answer which specific designations are excluded from SNAP eligibility.

```
SNAP > Eligibility Requirements > Entering Citizenship and Noncitizen Data in BEACON > Entering Noncitizen Data - Noncitizen Policy - SNAP > Noncitizen Veterans

This page is used to collect immigration history information for a client. The page is for clients who are not US citizens, and it is part of the Assessed Person Nonfinancials section of the workflow.

If the noncitizen status is indicated in the Citizenship page, you must complete this page.

Note : If the client is currently a citizen, but was formerly a noncitizen and there is data on the Noncitizen page, then the Noncitizen page will be available (see below).

The Noncitizen page will be enabled if;

- a person is a noncitizen and US citizenship is changed to Yes on the Citizenship page and there is a pending or active Noncitizen Designation; or
- if the person is a noncitizen and the Noncitizen Designation Statuses are Denied/Closed, for the following Noncitizen Designation Statuses

  - Legal Permanent Resident (LPR)
  - Refugee
  - Asylee
  - Parolee
  - Conditional Entrant
  - Cuban/Haitian Entrant
  - PRUCOL
  - Vietnamese Amerasian
  - Deportation Withheld Noncitizen
  - Noncitizen Veteran
  - Hmong, Highland Laotian
  - Battered Noncitizen
  - Non-immigrant
  - Deportation Order Shown; or
  - Undetermined/Opt-Out

Remember : Noncitizens with an Noncitizen Designation of Undetermined are not eligible for TAFDC, EAEDC or SNAP. If the noncitizen is ineligible for EAEDC benefits you must indicate the noncitizen’s ineligibility in the AU Compositions Results page.

The Noncitizen Veterans page also collects data about noncitizen veterans who lawfully reside in the U.S.
```

#### Rank 3 — PARTIAL (sim 0.515)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_CitOvwSNAP__004`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk addresses ineligible noncitizens in SNAP but does not specify which particular non-citizenship designations are excluded, only that unverifiable citizenship results in ineligibility.

```
SNAP > Eligibility Requirements > Citizenship > Citizenship Overview - SNAP > Participation Pending Verification of U.S. Citizenship

A member whose U.S. citizenship is questionable and cannot be verified will be ineligible and shall be disqualified on the basis of being an ineligible noncitizen, unless another eligible status can be claimed.

Related Topics Entering Citizenship Data - Citizenship - SNAP Citizenship Policy and Procedures - SNAP Last Update: March 10, 2026
```

#### Rank 4 — RELEVANT (sim 0.597)

- **Chunk ID**: `sec__SNAP__Noncitizen__NC_SDXNonCitizenIndCodes__000`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: The table directly lists noncitizen designations and their SNAP eligibility status, clearly identifying which designations are excluded (ineligible) from SNAP.

```
SNAP > Eligibility Requirements > Noncitizen > Eligible Qualified Noncitizens > Legal Permanent Resident (LPR) > Disabled Noncitizens > State Data Exchange (SDX) Noncitizen Indicator Codes - SNAP

| SDX Code | SDX Description | BEACON Description | SNAP Status |
| --- | --- | --- | --- |
| 1 | No status alleged | Undetermined | Ineligible |
| 2 | Valid noncitizen status alleged, but not proven | Undetermined | Ineligible |
| 3 | Amerasian immigrant | Vietnamese Amerasian | Ineligible |
| 4 | North American Indian | Citizen | Eligible |
| A | Proven U.S. born-U.S. citizen | Citizen | Eligible |
| B | Alleged U.S. born- U.S. citizen | Citizen | Eligible |
| C | U.S. citizen born outside of the U.S. Includes naturalized citizens and U.S. citizens born abroad to U.S. parents | Naturalized Citizen | Eligible |
| E | No citizenship or alien status development undertaken; case denied for reason(s) other than citizenship/alien status | Undetermined | Ineligible |
| F | Refugee status- Section 207 or 203 (A)(7) of the I.N.A. | Refugee | Ineligible |
| G | Parole status-Section 212(d)(5) of the I.N.A. | Parolee | Ineligible |
| J | Deportation has been withheld pursuant to section 243 (h) of the I.N.A., or meets one of the following criteria:; Deferred action status noncitizen; Residence of U.S. pursuant to an Order of Supervision; Properly filed an application with the Immigration and Naturalization Service (INS) for adjustment of status | Deportation withheld noncitizen | Ineligible |
| K | Noncitizen lawfully admitted to the U.S. for permanent residence | Legal Permanent Resident | Eligible provided certain conditions are met |
```

#### Rank 5 — RELEVANT (sim 0.588)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_EnteringNonCitizenDesSNAP__003`
- **Section**: `` — 
- **Chunk position**: 1 / 4
- **Program**: SNAP
- **Judge reason**: The table directly lists noncitizen designations and explicitly identifies which ones are excluded (ineligible) from SNAP participation.

```
SNAP > Eligibility Requirements > Noncitizen > Entering Noncitizen Data in BEACON > Entering Noncitizen Designation - SNAP > Legal SNAP Disqualified Indicator > Legal SNAP Disqualified Indicator Coding

| Noncitizen designation | Is this person a legal noncitizen? | Is this person ineligible to participate in the Federal SNAP program? | How to code the Legal SNAP disqualified indicator |
| --- | --- | --- | --- |
| Amerasian | Yes | No | No |
| Citizens from Compacts of Free Associations (COFA) Nations | Yes | No | No |
| Cuban/Haitian Entrant | Yes | No | No |
| Asylee (Active Status), Refugee, Deportation Withheld Noncit., Victim of Trafficking, and Special Humanitarian Parolee | Yes | Yes | Yes |
| Deportation Order Shown | No | Yes | No |
| Nonimmigrant; (Diplomats, Students, Visitors) | No; * as this is a temporary status | Yes | No |
| Undetermined/Opt-Out; *This status is used for individuals who do not have an immigration status as well as those who have opted out of receiving SNAP benefits. | No | Yes | No |
| Legal Permanent Resident (regardless of age) that has had a LPR status equal to or greater than 5 years | Yes | No | No |
| Legal Permanent Resident (18 yrs and over) and has  had LPR status for less than 5 years | Yes | Yes | Yes |
| Legal Permanent Resident (children under 18 yrs), regardless of number of years residing in the US | Yes | No | No |
```


### olg_006 — roomer/boarder income (rank-1: RELEVANT)

**Question**: How is income counted for someone who rents out a room in their house?  
**Program filter**: `['SNAP']`  
**Notes**: Boarder/roomer income treatment — net vs gross, household composition implications.  
**Scores**: Relevant@5 = 3, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.594)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_RentRoomBoardIncSNAP__004`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk directly explains how roomer income from renting out a room is counted as earned income for SNAP eligibility, with clear examples including someone renting a room in their own home.

```
SNAP > Eligibility Requirements > Income > Self Employment > Rental, Roomer, and Boarder Income SNAP > Roomers

Roomers are individuals to whom the household furnishes lodging, but not meals, for compensation. You must explore the possibility that this may be a shared living situation where two or more households split the rent for the apartment. If a household claims roomer income, you must ask the client about the living arrangement.

If all members of the household are listed on a lease and one member pays a portion of the rent to another or to the landlord directly, this is a shared living situation. If the landlord is unaware that another person is living in the apartment, and that person pays rent directly to the primary tenant, it is most likely a roomer situation.

If it is determined that there is roomer income, the total payment is considered earned income.

Example 1 Example 1 Mary owns her home and rents a room to Anna for $40.00 a week, with no meals provided or kitchen privileges. The rent is roomer income as the roomer only is only allowed access to her room.

Example 2 Example 2 Jane lives in a 3 bedroom apartment with a rent of $1000.00, but rents two bedrooms without the landlord’s knowledge at $500.00 a month each. This would be a roomer situation.

Example 3 Example 3 A mother and her 23 year old daughter share an apartment with the rent of $800. The mother pays $500.00 and the daughter pays $300.00. They purchase and prepare food separately. This is a shared housing situation. The mother can claim a shelter expense of $500.00.
```

#### Rank 2 — RELEVANT (sim 0.506)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_RentRoomBoardIncSNAP__006`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses how income from renting out a room (roomer income) is counted as self-employment income for SNAP eligibility purposes.

```
SNAP > Eligibility Requirements > Income > Self Employment > Rental, Roomer, and Boarder Income SNAP > Boarders

The income a household receives from a boarder, other than that received by a household who owns and operates a commercial boarding house, is considered self-employment income. Boarders are different from roomers because they have meals provided to them. All direct payments to the household for room and meals, including contributions to the household’s shelter expenses, must be considered earned income available to the household.

Boarders are ineligible to participate separately from the household providing lodging and meals. Boarders may participate as members of the household providing these services and at the request of the providing household.

Note : A roomer is a person who rents a room or rooms in which to live. A boarder is a person who pays rent and a stipulated sum of money in return for regular meals and lodging.
```

#### Rank 3 — RELEVANT (sim 0.551)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_RentRoomBoardIncSNAP__001`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk directly explains how rental income from renting out rooms/units in a house is counted for SNAP purposes, including the calculation method and deductions allowed.

```
SNAP > Eligibility Requirements > Income > Self Employment > Rental, Roomer, and Boarder Income SNAP > Rental Income

Income from rental property is considered earned income and entitled to the earned income deduction if a household member is actively engaged in the management of the property an average of 20 hours per week or more. For SNAP only clients, if the household member is managing the property less than an average of 20 hours per week, the income must be considered unearned. For TAFDC and EAEDC clients, see Real Estate Income – EAEDC and/or Real Estate Income – TAFDC .

When calculating a household’s income from a rental property, you must:

- determine the monthly rental income received from tenants
- subtract the Cost of Doing Business (CODB)
- prorate the CODB by the number of units
- The result of this calculation is the household’s countable income.

Example : A SNAP client owns a three family house. She occupies the first floor and rents the second and third floor apartments for $1000 a month each. The tenants are responsible for their own utilities. The client’s mortgage expense includes principal of $300, interest of $1500, taxes of $300, and homeowner’s insurance of $400 per month. The water and sewer fee is $300 per month
```

#### Rank 4 — PARTIAL (sim 0.446)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_SE_RentRoomBoardIncSNAP__009`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk addresses boarding house income but focuses on eligibility rules for residents rather than how rental income is counted for the person renting out the room.

```
SNAP > Eligibility Requirements > Income > Self Employment > Rental, Roomer, and Boarder Income SNAP > Commercial Boarding House

Residents of a commercial boarding house are not eligible for SNAP benefits. A commercial boarding house is defined as an establishment that is licensed as a commercial enterprise, and offers meals and lodging for compensation. In cities and towns without licensing requirements, a commercial boarding house is defined as a commercial establishment that offers meals and lodging for compensation with the intent of making a profit. The number of boarders residing in a boarding house shall not be used to determine if a boarding house is a commercial enterprise. The household of the owner of a boarding house may apply for SNAP benefits as a household separate and apart from the residents of the boarding house.
```

#### Rank 5 — PARTIAL (sim 0.452)

- **Chunk ID**: `sec__SNAP__Eligibility__EldDis_AdultFosterCare__009`
- **Section**: `` — 
- **Chunk position**: 4 / 5
- **Program**: SNAP
- **Judge reason**: The chunk discusses room and board income in the context of Adult Foster Care arrangements, which shares the keyword concept of renting out a room, but does not address the general policy for how rental income from renting out a room in one's house is counted for income purposes.

```
SNAP > Eligibility Requirements > Elderly Disabled > Adult Foster Care > Adult Foster Care Payments

Example 2 Example 2 Neiman, age 29, is a SNAP client and chooses to include his mother Rosa in his SNAP case. Rosa is in Adult Foster Care. Per the Adult Foster Care Arrangement, Neiman receives a $1250 Adult Foster Care payment per month. The Adult Foster Care Arrangement also includes a line item that values Rosa’s room and board at $500 per month. Neiman does not charge Rosa this additional fee. The payment verifications supplied by Neiman reflect the $1250 AFC payment. Only the $1250 Adult Foster Care payment is considered countable income for Neiman’s SNAP case, and must be entered as a Foster Care payment. Neiman must supply a written self—declaration attesting to this room and board arrangement.

Example 3 Example 3 Miriam is a SNAP recipient and chooses not to include her father Cliff, who is in Adult Foster Care, in her SNAP case. Per the Adult Foster Care Arrangement, Miriam receives a $500 Adult Foster Care payment per month. The Adult Foster Care Arrangement also values Cliff’s room and board at $350 per month which Miriam collects on the 10th of every month. Since Miriam is choosing not to include Cliff in her SNAP case, the Adult Foster Care payment is not considered countable income for Miriam’s SNAP case. However, the fee collected for Cliff’s room and board must be included as Boarder income.
```


### olg_007 — medical deduction thresholds (rank-1: PARTIAL)

**Question**: What are the minimum and maximum amounts of medical expenses that a client can claim?  
**Program filter**: `['SNAP']`  
**Notes**: Medical expense deduction for elderly/disabled — $35 min, standard medical deduction amount, threshold for itemizing. Numeric lookup.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.415)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__Med_DeductionOvw__004`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk discusses verification thresholds ($190/month) and procedures for medical expenses but does not specify overall minimum or maximum amounts that clients can claim.

```
SNAP > Expenses and Deductions > Health Insurance and Medical Expenses > Medical Expenses > Overview of Medical Expense Deduction > Verifying Medical Expenses Above $190 per Month

If an elderly and/or disabled client declares that they incur less than or equal to $190 per month in medical expenses, they can self-declare these expenses on DTA Connect, telephonically, or a written statement. For more information on the procedures for self-declaring medical expenses, see Standard Medical Deduction Waiver .

Note : A self-declaration is also sufficient for crediting dependent care costs that a client chooses to claim as a medical expense. For more information, see Dependent Care Expense Deduction.

If an elderly and/or disabled client indicates that they incur medical expenses above $190 per month, they must submit verification of all medical expenses to receive credit for expenses above $190 per month. A self-declaration is only acceptable for medical expenses less than or equal to $190 per month to be credited with the SMD.

- Example : Cory (they/them) has a monthly medical expense of $40 for prescriptions and provided a self-declaration through DTA Connect. Cory receives the SMD in the households SNAP calculation.  Cory later reports having to now pay a health insurance premium of $200 per month. To receive an Actual medical expense deduction of $205 ($40 + $200 - $35 = $205) they must provide documentary evidence of both the prescriptions and health insurance premium.
```

#### Rank 2 — PARTIAL (sim 0.410)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__Med_ExpDedRevPeriods__005`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk mentions specific dollar amounts ($35, $190) related to medical expenses but describes procedural verification requirements rather than directly stating the minimum and maximum amounts a client can claim.

```
SNAP > Expenses and Deductions > Health Insurance and Medical Expenses > Medical Expenses > Medical Expense Deduction During Review Periods > Procedures for Verifying Changes in Medical Expenses at IR > $0 into Actuals

At IR, if a client voluntarily indicates a change in medical expenses (verbally or in writing) that brings their monthly total from being less than $35 per month into Actuals, you must:

1. Use the medical items and amounts that the client wrote on the form as a self-declaration that their medical expenses are at least less than or equal to $190 per month. If the information on the form is incomplete or no form was submitted, follow the Telephonic Signature procedures to have the client self-declare a portion those medical expenses that are less than or equal to $190 per month.
2. Enter all the medical expenses into BEACON. You must select the appropriate Expense Type in the Health Insurance and/or Medical Expense pages and enter the self-declared amounts.
3. Send an optional VC-1 for all the medical expenses (including those that client already self-declared). Please note that in order for the household to receive an Actual medical expense deduction, all medical expenses except mileage must be verified through documentary evidence.
```

#### Rank 3 — PARTIAL (sim 0.406)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__Med_ExpDedRevPeriods__008`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: SNAP
- **Judge reason**: The chunk mentions a $190 threshold for medical expenses but does not provide minimum and maximum amounts that clients can claim; it only addresses verification procedures at that threshold.

```
SNAP > Expenses and Deductions > Health Insurance and Medical Expenses > Medical Expenses > Medical Expense Deduction During Review Periods > Procedures for Verifying Medical Expenses at Recertification

Clients with $190 or less in monthly medical costs can self-declare them in writing or by telephonic self-declaration.

At recertification, you do not have to send a VC-1 for medical costs if:

- the total monthly medical costs are $190 or less

AND

- the client clearly lists each medical type and amount on the form (or a separate paper), or
- the client is able to verbally break down each type and amount, and telephonically self-declare.

You must send a VC-1 for medical costs in one or more of the following situations:

- The total monthly medical costs are above $190: You may be able to figure out the total from what the client wrote on the form and/or what they reported verbally. The total includes both regular and one-time medical costs. Any costs that are not monthly must be changed into a monthly amount. (You do not have to send a VC-1 if the client sent all the proof with the recertification.)

  - Reminder : You must continue following the procedure for crediting the household with SMD if they are unable to verify medical costs above $190. See Standard Medical Deduction Waiver .
```

#### Rank 4 — PARTIAL (sim 0.393)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__Med_TransRelCosts__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses eligible medical transportation expenses and provides examples, but does not specify minimum or maximum dollar amounts that clients can claim for medical expenses overall.

```
SNAP > Expenses and Deductions > Health Insurance and Medical Expenses > Medical Expenses > Transportation Related Costs > Overview

Eligible clients may claim travel and lodging costs when seeking health care treatment. This includes roundtrip costs for one time or recurring visits to doctors, clinics, physical therapy sessions and pharmacies.

Transportation costs may include, but are not limited to:

- use of a private car to get to and from appointments. The mileage credit is calculated using the Federal Mileage Rates ;
- parking costs and tolls incurred to attend appointments;
- payments to friends/family for medical related transportation;
- actual cost of bus, subway, shuttle or taxi; or
- monthly public transportation passes. You may credit the client for the percentage used for medical transportation.

Example Example Sally (she/her) is a retired teacher. She has a monthly MBTA Senior Pass that costs $30 per month. She reports that 75% of her trips are for medical related travel. Sally can claim 75% of the cost of her pass as a medical expense, this comes out to $22.50 per month ($30 X .75 = $22.50).

Example Example Jack (he/his) pays a neighbor to take him to his dialysis appointment every Friday. He gives him $5 in cash and the neighbor drops him off and picks him up. Jack provides you with a signed statement from his neighbor verifying this arrangement. You can credit Jack for $21.67 as a monthly transportation cost ($5 x 4.333).
```

#### Rank 5 — PARTIAL (sim 0.382)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__Med_ExpDedRevPeriods__002`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk mentions specific dollar amounts ($35/month and $190/month) related to medical expenses but only in the context of Standard Medical Deduction ranges and verification procedures, not as general minimum/maximum amounts a client can claim.

```
SNAP > Expenses and Deductions > Health Insurance and Medical Expenses > Medical Expenses > Medical Expense Deduction During Review Periods > Procedures for Verifying Changes in Medical Expenses at IR > Client Reports Change in Medical Expenses that Results in Standard Medical Deduction (SMD)

If a client at IR clearly indicated their medical information (including a breakdown of each type and cost) on the IR form, and the change results in the household’s total medical expenses being less than or equal to $190 per month , you must accept the information on the IR form as a written self-declaration.

At IR, clients who report a change in medical expenses resulting in the SMD must provide at least a telephonic self-declaration of medical expenses if they:

- wrote on the IR form that their medical expenses changed, but omitted necessary details (such as the amounts) to complete the written self-declaration; or
- did not report a change in medical expenses in writing, but reported during a call or in-person interaction that their medical expenses changed.

If the client at IR voluntarily indicates a change in medical expenses, but you are unsure whether they are still in the SMD range (>$35/month, <$190/month), you must follow the optional verification procedures detailed in Simplified Reporting Interim Report .

Reminder : Staff must act on verified-upon-receipt information. This means that if a client voluntarily supplies verification of their medical expenses, you must act upon them. The medical expense amount must be updated in BEACON, even if the client was not actually required to provide documentary evidence.
```


### olg_008 — dependent care deduction (rank-1: RELEVANT)

**Question**: Dependent care deduction — what counts?  
**Program filter**: `['SNAP']`  
**Notes**: Allowable dependent care costs — child care, transportation to care, before/after school, etc.  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.551)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__DC_ExpDed__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses what counts as dependent care expenses for the deduction, specifying eligible care types, beneficiaries, and qualifying circumstances.

```
SNAP > Expenses and Deductions > Dependent Care Expenses > Dependent Care Expenses Deduction > Overview

This is an optional verification.

A dependent care deduction is allowable for SNAP households that report dependent care as being necessary to:

- continue employment
- search for a job
- attend training or education program to prepare for employment
- has a disability

Dependent care expenses are allowed for care provided to a child under 18 or for a person with disabilities of any age in need of care.

For information on the dependent care deduction for TAFDC, see Dependent Care Deduction and Entering Dependent Care Expenses Data – TAFDC .

Note :

When a household:

- includes a person who incurs dependent care costs or
- includes a disabled child or adult that incur costs
- that qualify under both the Medical Expense Deduction and the Dependent Care Expense Deduction, the cost may be deducted as either expense, but not both.

In these situations, you must review which deduction will be most beneficial for the household. See examples below.
```

#### Rank 2 — RELEVANT (sim 0.542)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__DC_ExpDed__002`
- **Section**: `` — 
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses what counts as a dependent care deduction by explaining allowable expenses, the requirement that expenses be non-reimbursed, and providing specific examples of what qualifies and what doesn't.

```
SNAP > Expenses and Deductions > Dependent Care Expenses > Dependent Care Expenses Deduction > Overview > Examples

If entered as a Medical Expense, Susan’s household would receive a $165 per month medical expense deduction (Actual Medical Expense $200 - $35 = $165).

In this example, the Dependent Care Expense deduction is more beneficial to the client.

The amount of the dependent care expense must be entered separately for each dependent for whom the expense is incurred. Reimbursed dependent care is not an allowable deduction. Only the non-reimbursed portion of the expense is allowable.

The costs of care provided by a relative may be deducted so long as the relative providing the care is not part of the same SNAP household as the child or dependent adult receiving the care.

Example : Cynthia (she/her) is the grantee of a SNAP household of three that includes her daughters Laura, 20, and Victoria, 12. Cynthia states she pays Laura $20 per week to babysit Victoria after school.

This would not be an allowable Dependent Care Deduction as Laura is a member of the SNAP household.

Example : Cynthia (she/her) is the grantee of a SNAP household of four that includes her husband Stephen (he/his), her daughter Victoria (she/her), age 12, and her son Stephen Jr (he/his), age 5.
```

#### Rank 3 — PARTIAL (sim 0.531)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__DC_ExpDed__007`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk provides an example of dependent care deduction application but doesn't explicitly define what counts as dependent care expenses.

```
SNAP > Expenses and Deductions > Dependent Care Expenses > Dependent Care Expenses Deduction > Dependent Care as a Medical Expense > Example

Carrie (she/her), 35, is the grantee in a SNAP household of 3 that includes her spouse Gary (he/his), 30, and her disabled daughter Shelah (she/her), 6. Carrie receives the SMD deduction of $155 due to verified medication expenses of $40 per month. Due to conflicting work schedules and the necessity of care due to her daughter’s disability, the household elects to put Shelah in medically-supervised daycare two afternoons per week. Carrie supplies receipts from her new childcare provider showing she now pays $100 dollars per month for this care.

When added to the household’s existing medical expenses, the household’s expense deduction would remain at $155 as the addition of the daycare expense is insufficient to meet the threshold for the Actual Medical Expense deduction.

When added as a dependent care expense, the household would receive a $100 per month dependent care deduction in addition to the $155 Standard Medical Deduction, for a total deduction of $255.
```

#### Rank 4 — RELEVANT (sim 0.532)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__DC_ExpDed__003`
- **Section**: `` — 
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses what counts as an allowable dependent care deduction by providing a specific example showing that payments to a non-household relative for childcare qualify.

```
SNAP > Expenses and Deductions > Dependent Care Expenses > Dependent Care Expenses Deduction > Overview > Examples

Cynthia’s other daughter, Laura age 20, lives in the next town over. Cynthia pays Laura to baby sit Stephen Jr. and Victoria four days per week.

While Laura is a relative, since she is not part of the SNAP household, this is an allowable Dependent Care Deduction.
```

#### Rank 5 — RELEVANT (sim 0.539)

- **Chunk ID**: `sec__SNAP__ExpensesDeductions__DC_ExpDed__001`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses what counts as dependent care expenses through detailed examples showing how dependent care costs are categorized and calculated for SNAP benefits.

```
SNAP > Expenses and Deductions > Dependent Care Expenses > Dependent Care Expenses Deduction > Overview > Examples

Example : Susan (she/her) is the grantee in a SNAP household of 2 that includes her 6-year-old son, Matt (he/his). Matt has a disability that occasionally requires care by a medical professional. Due to this, Susan pays a visiting nurse service $50 per month for an attendant to care for Matt afterschool for two hours each day, Monday through Friday, to accommodate her work schedule.

If entered as a Dependent Care Expense, Susan’s household would receive a $50 per month dependent care expense deduction.

If entered as a Medical Expense, Susan’s household would receive a $155 per month medical expense deduction since the $50 paid to the visiting nurse service exceeds the $35.01 threshold required to receive the Standard Medical Deduction.

In this example, the Medical Expense Deduction is more beneficial to the client.

Example : Susan (she/her) is the grantee in a SNAP household of 2 that includes her 6 year old son, Matt (he/his). Matt has a disability that occasionally requires care by a medical professional. Due to this, Susan pays a visiting nurse service $200 per month for an attendant to care for Matt afterschool for two hours each day, Monday through Friday, to accommodate her work schedule.
```


### olg_009 — lump sum income treatment (rank-1: RELEVANT)

**Question**: How are lump sum payments treated when entering income for a client?  
**Program filter**: `['SNAP']`  
**Notes**: Lump sum classification — countable vs excluded, which lump sums count as income vs asset.  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.480)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_EntChgEndOtherUnearnedInc__008`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses how to treat lump sum payments when entering income by instructing users to check the 'Lump Sum' box if income received in a pay period is a lump sum amount.

```
SNAP > Eligibility Requirements > Income > Other Income Unearned > Entering, Changing, and Ending Other (Unearned) Income Data > Income Tab > Adding Other Income Information on the Income Tab

1. open the Other Income Status page; the Income tab will display by default
2. to switch between clients who are part of the same Eligibility Group use the Members list to select the member for whom you will be adding other income information
3. for Garnishment, if the client has his/her income garnished, select Yes; otherwise, select No; BEACON defaults the Period based on the frequency of the income and the pay dates
4. for Gross income, enter the income for one or more pay periods

  a. Important : BEACON adds a decimal point only for whole dollar amounts (if $40 is entered, BEACON adds the decimal point and it will show as $40.00).  You will need to add a decimal point when entering income that is not a whole dollar amount. If a weekly unearned income of $40.50 is entered in BEACON as 4050 BEACON will add a decimal point and make the amount $4050.00. You will need to insert a decimal point manually $40 + Decimal point + 50 to capture the correct amount of $40.50.
5. for lump sum, if the income received in a pay period is actually a lump sum amount, check the Lump Sum box
6. Entered is a display-only date and will be displayed after you enter the gross income and lump sum information
7. click Save
8. click Next, or to exit the page and the workflow, click Finish
```

#### Rank 2 — RELEVANT (sim 0.467)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_EntChgEndEIBEACON__012`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: SNAP
- **Judge reason**: Directly explains how to handle lump sum payments when entering income data in BEACON by checking the Lump Sum checkbox.

```
SNAP > Eligibility Requirements > Income > Earned Income > Entering, Changing, and Ending Earned Income in BEACON > Earnings Tab > Add Earned Income Data to Earnings Tab

6. for Lump Sum, if the income received in a pay period is actually a lump sum payment, check the Lump Sum checkbox
7. entered is a display-only date that is populated after you enter the gross income, hours and lump sum information
8. click Save
9. click Next, or to exit the page and the workflow, click Finish

If income is being garnished, open the Earned Income Garnishment page and capture the garnishment information. For more information, see Earned Income Garnishment.
```

#### Rank 3 — RELEVANT (sim 0.440)

- **Chunk ID**: `sec__SNAP__Eligibility__Assets_SNAPGuide__007`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly explains how lump sum payments are treated as assets when received and the verification requirements for entering them into income calculations.

```
SNAP > Eligibility Requirements > Assets > SNAP Asset Guidelines > Countable Assets > Nonrecurring Lump Sum Income

Nonrecurring lump sum payments include, but are not limited to:

- income tax refunds;
- rebates or credits;
- retroactive lump sum Social Security benefits, public assistance benefits, and railroad retirement benefits;
- lump sum insurance settlements; and
- refunds of security deposits on rental property or utilities.

These payments must be counted as an asset in the month received, unless exempt. When a lump sum payment puts a household’s total assets over the asset limit, you must allow the household to update its entire asset statement. If the household fails to update the asset information, terminate the case.

Verification of Nonrecurring Lump Sum Income

Lump sum payments must be verified by one of the following:

- a copy of the benefit or award letter;
- a copy of the check or payment document; or
- a written statement from the agency or person making the payment.
```

#### Rank 4 — RELEVANT (sim 0.387)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_Noncountable__002`
- **Section**: `` — 
- **Chunk position**: 3 / 6
- **Program**: SNAP
- **Judge reason**: Directly addresses how lump sum payments are treated for income purposes, explaining that nonrecurring lump sum payments are excluded from countable income but may be countable as assets.

```
SNAP > Eligibility Requirements > Income > Noncountable Income

- Infrequent/Irregular: Money received infrequently that does not exceed $30 per quarter. For example, a $25 a birthday gift is not countable.
- In-kind income : Any gain or benefit not in the form of money and provided directly to the household. For example, a client’s neighbor provides produce from his garden.
- Loans : Any amount of money that must be repaid is not countable as income. For example, a friend provides $500 as a loan and requests that the amount be repaid within a year.
- Mass Cultural Council’s Creative Individuals Program Grants: A one-time $5,000 grant to artists, culture bearers, and creative practitioners is non-countable income.
- Nonrecurring Lump Sum Payments: Any lump sum of money received that is not expected to continue occurring is excluded income. For example, the amount of money received from an income tax return.

  - Note : A lump sum payment is a countable asset in the month received unless it is excluded in accordance with 106 CMR 363.140.
- Payments to Certain Volunteers : Payments and reimbursements to volunteer foster grandparents, senior health aides, and those participating in VISTA, or a program established under the Domestic Service Act of 1973.
```

#### Rank 5 — RELEVANT (sim 0.448)

- **Chunk ID**: `sec__SNAP__Eligibility__Inc_EntChildSuptIncSNAP__003`
- **Section**: `` — 
- **Chunk position**: 2 / 3
- **Program**: SNAP
- **Judge reason**: The chunk directly addresses how lump sum payments are treated in income calculations, explaining that infrequent lump sums must not be counted and provides specific guidance on entering income when lump sums are received.

```
SNAP > Eligibility Requirements > Income > Other Income Unearned > Entering Child Support Income - SNAP > Child Support Examples

- March 2018: $300
- April 2018:   $300
- May 2018:   $2,186
- June 2018:   $300

Do I use May’s income to calculate the last three months?

A3 : No. You must not count any payments that are infrequent. It is worth noting that the lump sum received by the client is likely to have been the noncustodial parent’s tax returns that may have been intercepted depending on the time of year. It must not be considered as anticipated income or a recurring lump sum. Therefore, you must update the Support by using March, April and June’s income.

Q4 : Natacha is receiving DOR Child support for their 2 children, Julian and Andrew. One is living in the home, Julian, and the older child, Andrew, is living at college and not in the SNAP case. The client stated that half of the child support is given to the child outside of the home, Andrew, and submitted a letter from Andrew stating this information. The question is would the portion of child support the client gives to Andrew be considered excluded income or countable?
```


### olg_010 — TAFDC time limit (rank-1: RELEVANT)

**Question**: TAFDC 24-month time limit clock — what counts, exemptions  
**Program filter**: `['TAFDC']`  
**Notes**: Multi-section — clock-counting rules, hardship exemptions, extensions, good cause.  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.20  

#### Rank 1 — RELEVANT (sim 0.639)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__TL_State24MonthClock__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: TAFDC
- **Judge reason**: Directly explains what counts toward the 24-month clock and includes information about exemptions (nonexempt requirement and special cases like legally liable but ineligible parents).

```
TAFDC > Program Nonfinancial Requirements > Time Limited Benefits > The State 24 Month Clock

Each TAFDC client subject to the 24-month time-limit has a State TAFDC 24-month clock which tracks the months of time-limited benefits the client has used.

Note : For clock purposes, the months counted are calendar months. You can view the client’s clock on the Time Limits page in the Program Administration workflow.

Clients are notified of their 24-month clock count when the client uses 3 months, 6 months, 9 months, 12 months, 15 months, 18 months and 22 months of time-limited benefits. In a two-parent household, the parent with the higher 24-month clock count will receive the notices indicating how many months were used.

A month is accreted to the 24-month clock for a client who:

- is active or sanctioned for the entire calendar month and

  - Note : For the purposes of counting the 24 months, clients who are legally liable for the children for whom they receive TAFDC, but who are themselves ineligible, are considered active.

- is nonexempt for the entire calendar month and
- receives a TAFDC benefit greater than or equal to $10, or participates in the Full Engagement Program (FEP), or supported work, or would have received more than $10 except for vendor payments or recoupments deductions.
```

#### Rank 2 — RELEVANT (sim 0.670)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__TL_State24MonthClock__001`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: TAFDC
- **Judge reason**: Directly explains what counts toward the 24-month clock, exemptions that stop the clock, and when it resumes.

```
TAFDC > Program Nonfinancial Requirements > Time Limited Benefits > The State 24 Month Clock

Months are accreted to the 24-month clock during the first cyclical payment of the current month. If the client becomes exempt during the month, or does not receive benefits for the entire month, that month is not counted and is removed from the clock in an overnight batch.

The calculation of the client’s cumulative 24-month clock is suspended when:

- the entire case is closed, including when the case becomes ineligible as a result of a sanction
- the client becomes exempt or
- the client voluntarily asks for the TAFDC case to be closed.

The clock resumes accreting months when the situation that caused the suspension no longer exists, or the case is reopened and remains nonexempt, or the case becomes nonexempt for another reason, in the same continuous 60-month period.

Related Topics Time Limited Benefits Policy and Procedures Last Update: September 23, 2014
```

#### Rank 3 — PARTIAL (sim 0.597)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__WPR_TAFDCPg__005`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Describes how to record time limit exemption status in the system but doesn't explain what counts toward the clock or detail the exemption reasons themselves.

```
TAFDC > Program Nonfinancial Requirements > Work Program Rules > Using the Work Requirements TAFDC Page > The Work Requirements TAFDC page is used for five reasons > Reason 5 - AU Time Limit/Reduced Standard Exemption

Records whether a case is subject to the TAFDC 24-month time limit

To record whether a case is subject to the TAFDC 24-month time limit using the Exemption Status drop-down box select:

- If Exempt select the appropriate exemption reason from the Reason drop-down list:

  - Exempt
  - Pending Disability Review
- If Nonexempt, select the appropriate nonexempt reason from the Reason drop-down list:

  - 2 Parent, Child <2
  - Child Age 2 and Older

Related Topics Exemptions from Time Limits and Work Program Rules Using Meets Compliance Last Update: August 9, 2023
```

#### Rank 4 — PARTIAL (sim 0.538)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__TL_24MosClockManAdj__001`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Addresses the 24-month clock and mentions exemptions from time-limited benefits, but does not detail what counts toward the clock or specify the exemptions themselves.

```
TAFDC > Program Nonfinancial Requirements > Time Limited Benefits > 24 Month Clock Manual Adjustments > Client Requests 24-month Clock Adjustment

A TAFDC Time-Limit Information notice is automatically generated to clients who have used their 3rd, 6th, 9th, 12th, 15th and 18th month of time-limited benefits advising them of their time remaining and activities in which to participate to reach self-sufficiency.

For two-parent cases, each parent will receive this notice, which will also advise them how many months the case has used. These notices will also advise clients of reasons why they may be exempt from time-limited benefits and the work program.

If at any time you meet with a client, and after meeting with you and having the 24-month rules and the 24-month clock explained, the client disagrees with the number of months accrued, give him/her the Request for Adjustment of the 24-month Time Limit (TAFDC-8) form (in English or Spanish, as appropriate) to complete. The client must explain the reason for the clock adjustment request on this form.
```

#### Rank 5 — PARTIAL (sim 0.543)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__PNR-TLB-MonitorTimeLimitedBenefits__001`
- **Section**: `` — 
- **Chunk position**: 2 / 3
- **Program**: TAFDC
- **Judge reason**: Describes how to monitor and view the 24-month clock in the system, but does not explain what counts toward the clock or what exemptions exist from it.

```
TAFDC > Program Nonfinancial Requirements > Time Limited Benefits > Monitoring the Time Limited Benefits

1. in the Case Maintenance workflow select the Program Administration workflow
2. in the Program Administration workflow select the Time Limits page
3. select the appropriate client from the Household members list in the upper left corner of the page
4. select the appropriate State TAFDC clock row from the list box and the list box displays the:
5. clock Type
6. Months Used as calculated by the system
7. Start and End dates that span the 60-month period
8. view the clock information on the Clock tab on the Time Limits page.

The following information is displayed on the Clock tab:

- Type: State TAFDC
- Start: system-calculated start date for the clock based on the approval of the application for TAFDC
- Month: displays the specific month and year as determined by the state and federal clock batch jobs
- Countable: indicated Yes or No, displays whether the specific month was used in the 24-month count of time-limited benefits used by the client
- Override reason: displays the reason the TAO director or assistant director is overriding the 24-month clock setting determined by a batch job
```


### olg_011 — ESP participation (rank-1: PARTIAL)

**Question**: What are the ESP participation requirements?  
**Program filter**: `['TAFDC']`  
**Notes**: Employment Services Program — participation hours, activity types, sanction process.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.333)

- **Chunk ID**: `sec__TAFDC__BasicCM__Appt_MissedAssIntvTAFDC__000`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: The chunk discusses missed ESP appointment procedures and sanctions rather than the actual participation requirements for ESP.

```
TAFDC > Basic Case Activities Maintenance > TAFDC Appointments > Missed ESP Assessment Interviews TAFDC

When you schedule Employment Services Program (ESP) assessment and reassessment appointments on the Schedule Appointment page, they are tracked for the ESP Work Program sanction process.

If a client does not keep the appointment or the appointment is not rescheduled before or on the day of the appointment, an overnight batch job changes the appointment status on the Schedule Appointment page to Missed and the client’s name is displayed in the Views menu selection on the Home page, under Daily Priority Actions in Missed ESP Interviews.

The Missed ESP Interviews lists your active TAFDC clients who are Work Program required who have missed a scheduled ESP assessment or reassessment interview. The missed interview results in a Work Program sanction.

The interview is considered missed when the Electronic Case Folder (ECF) for the client is not accessed (no updates or case actions are required) on the day of the appointment, or the appointment is not cancelled or rescheduled on or before the appointment.

Important : Do not schedule exempt clients who volunteer to participate in ESP activities with the assessment or reassessment appointment letter generated from the Schedule Appointment page because the TAFDC case will be closed inappropriately if the client misses the appointment

Related Topics Appointments Policy and Procedures Last Update: October 9, 2014
```

#### Rank 2 — PARTIAL (sim 0.303)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__WPR_MonthEngParWR__003`
- **Section**: `` — 
- **Chunk position**: 4 / 4
- **Program**: TAFDC
- **Judge reason**: The chunk discusses work program participation requirements but does not specifically address ESP (Employment Services Program) participation requirements.

```
TAFDC > Program Nonfinancial Requirements > Work Program Rules > Monthly Engagement and Participation to Meet Work Rules

For any client who must meet the work rules but does not meet the engagement or participation requirements, staff must attempt to connect with the client, explore what challenges exist and strategies to stay engaged. (See FEW and SSS Reengagement Responsibilities ).

Important : Clients who are not subject to work rules but participate as Pathways Volunteers are expected to have regular communication with DTA regarding their progress in their Plan. Those who are exempt may never be sanctioned for work rules.
```

#### Rank 3 — PARTIAL (sim 0.296)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__Cons_SupReengSanctAuth__003`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: The chunk discusses work rule participation and engagement requirements in the context of sanctions, but does not specifically define or explain ESP (Employment Services Program) participation requirements.

```
TAFDC > Program Nonfinancial Requirements > Consequences for Not Meeting the Work Rules > Supervisor Responsibilities for Reengagement and Sanction Authorization > No Engagement or Participation

If the sanction is the result of the client having an active Pathways to Work Plan but their monthly engagement or participation was not authorized, the supervisor must review the following, prior to any work rule sanction being authorized.

The supervisor must:

- review case narratives and Electronic Case File (ECF) for Scanned Documents to determine whether client has provided their Participation form, other verification of engagement or made contact with DTA to request good cause
- determine what contact was made by FEW with a Provider
- ensure that no additional information is known to DTA that would require an exemption or compliance reason to be entered
- review any other engagement attempts to communicate with client, including two required cold calls

Important : Exempt clients who choose to participate in a Pathways to Work activity or work can never be sanctioned for not meeting the work rules.

Related Topics Monthly Engagement and Participation to Meet the Work Rules Removing Work or School Rule Sanctions Authorizing Work or School Rule Sanctions Last Update: August 9, 2023
```

#### Rank 4 — PARTIAL (sim 0.291)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__WPR_MonthEngParWR__004`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: The chunk discusses co-case management expectations and monthly engagement procedures but does not define or explain what ESP (Employment Services Program) participation requirements actually are.

```
TAFDC > Program Nonfinancial Requirements > Work Program Rules > Monthly Engagement and Participation to Meet Work Rules > Co-Case Management Expectations

FEWs and SSSs must have monthly contact with all funded and contracted providers, where they must ensure that any challenges with client enrollment, retention or reengagement are addressed.

Case managers and FEWs must also continue to work collaboratively to share information regarding a client’s participation, including available scanned documents, and changes that may affect a client’s ability to engage.

Staff must ensure that they communicate with clients reporting their own progress in activities, while also working closely with providers to support client engagement and retention in services. If a discrepancy exists between what a client reports as their participation and what is being reported by the provider, additional communication with the client is required. If unable to reach client by phone, a Telephonic Case Maintenance appointment must be scheduled to discuss their activity engagement.

Related Topics Entering Monthly Engagement Entering Participation Hours Last Update: August 9, 2023
```

#### Rank 5 — PARTIAL (sim 0.294)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__WPR_MonthEngParWR__000`
- **Section**: `` — 
- **Chunk position**: 1 / 4
- **Program**: TAFDC
- **Judge reason**: The chunk discusses Pathways to Work participation requirements and monthly engagement procedures, but does not specifically address ESP (Employment Services Program) participation requirements.

```
TAFDC > Program Nonfinancial Requirements > Work Program Rules > Monthly Engagement and Participation to Meet Work Rules

To support progress towards a family’s goals and meeting program rules, DTA staff will have monthly contact with clients participating in Pathways to Work activities.

Participation forms will be generated by BEACON on the Monday before the last Saturday of each month for any client that is enrolled in an activity other than employment and has an active Pathways to Work Plan.

All clients enrolled in Pathways to Work activities are expected to confirm their monthly engagement or participation hours by the 10th day of the month following the month they participated in that activity.

For those subject to work rules, a monthly touchpoint must happen either by DTA recording the return of a participation form, client contact, or other acceptable proof. Community Service Participation forms will be completed by program or site staff.

DTA must enter the engagement or participation proof by the 18th of the reporting month. This information will be recorded in the Pathways Participation workflow.
```


### olg_012 — child support good cause (rank-1: PARTIAL)

**Question**: What is considered to be a good cause reason for non-cooperation with child support requirements?  
**Program filter**: `['TAFDC']`  
**Notes**: Specific list of good cause reasons — DV, rape, fear of harm, adoption pending, child conceived from rape/incest.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.571)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__Child_RevReasonsGC__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: TAFDC
- **Judge reason**: The chunk discusses the process for reviewing and verifying good cause claims but does not specify what reasons actually constitute good cause for non-cooperation with child support.

```
TAFDC > Program Nonfinancial Requirements > Child Support > Child Support Good Cause > Reviewing Reasons for Child Support Good Cause

You must review the reason(s) for a good cause claim at each reevaluation unless the good cause claim is rape or incest The client is not required to re-verify an existing good cause claim.

Important : Relative caregivers may claim good cause when it is not in the best interests of the child to pursue child support. Verification of good cause is never required for these households and must always be approved.

If the reason for claiming good cause no longer exists, the client will be required to cooperate with the Department of Revenue (DOR) and DTA child support requirements.

When the good cause reason no longer exists:

- have the client sign a new Completing the Assignment of Support Rights, Cooperation with Child Support, or Good Cause Claim form (T-A34/36), to indicate their willingness to cooperate. See Completing the Assignment of Support Rights, Cooperation with Child Support, or Good Cause Claim Form . See Child Support Good Cause Not Found if the client refuses to sign
- the Completing the Assignment of Support Rights , Cooperation with Child Support, or Good Cause Claim form must be included in the client’s Electronic Case Folder (ECF) following established procedures.
```

#### Rank 2 — PARTIAL (sim 0.539)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__Child_DenTermFailure2Coop__000`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: The chunk mentions 'good cause' for noncooperation multiple times but does not define or explain what constitutes good cause reasons, only that it exists as an exception to sanctions.

```
TAFDC > Program Nonfinancial Requirements > Child Support > Noncooperation with Child Support Efforts > Denials and Terminations for Failure to Cooperate

During the application and reevaluation processes, tell the client about what happens if they fail to cooperate with the child support requirements without good cause:

TAFDC benefits will be denied for an entire case when the client refuses to assign support rights by not signing the Assignment of Support Rights for TAFDC and MassHealth section of the Assignment of Support Rights, Cooperation with Support, or Good Cause Claim form (TA-34/36) .

TAFDC benefits will also be reduced if the client refuses to cooperate by not signing the Cooperation with Child Support section of the Assignment of Support Rights, Cooperation with Child Support, or Good Cause Claim form or for refusing to provide information about the absent parent, if good cause is not claimed. Uncertain responses, including “unknown” are not considered a refusal to provide information. See Child Support Sanction for Noncooperation .

Enter the information for a sanction when the Department of Revenue (DOR) sends notification of the client’s noncooperation with child support enforcement efforts, unless the client claims good cause for noncooperation. See Child Support Sanction for Noncooperation .

When DOR notifies you that the sanctioned client is cooperating with DOR, make sure that the sanction is removed and TAFDC benefits are properly restored.
```

#### Rank 3 — PARTIAL (sim 0.551)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__Child_AbsentParentDV__001`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: TAFDC
- **Judge reason**: The chunk discusses the process for claiming good cause and mentions domestic violence as a context, but does not actually define or list what constitutes good cause reasons for non-cooperation with child support.

```
TAFDC > Program Nonfinancial Requirements > Child Support > Absent Parent Information at Application > Absent Parent: Domestic Violence

2. enter the date in the Cooperation and Referral date fields
3. click the No radio button in the “Is the client claiming good cause” field in the Safety/Good Cause field
4. ask the client: “Is there a history/threat of DV associated with the absent parent?” Click the Yes or No radio button to record their response and
5. complete the other tabs on the Absence page with the client.

Note : If the client states they cannot cooperate, you must make a referral to a Domestic Violence (DV) Specialist, even if the good cause reasons don’t appear to apply to them.

If the client wishes to claim good cause for not cooperating, on the Absence page Cooperation tab:

1. click the No radio button in the Child support cooperation field and
2. complete the Safety/Good Cause field on the Cooperation tab with the client.

Important : If good cause is claimed, you must update the Cooperation tab immediately. DOR/CSE will not take any steps to establish a child support order unless and until good cause is removed from the Cooperation tab. You must also have the client complete and sign the I do not agree to cooperate and I am claiming good cause option under Cooperation on the Assignment of Support Rights, Cooperation with Child Support, or Good Cause Claim Form (TA-34/36), which is included in the printed application or reevaluation or generated using the Print Assign/Coop/Good Cause checkbox on the Absence tab. See Child Support Good Cause Claimed .
```

#### Rank 4 — PARTIAL (sim 0.550)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__Child_AbsentParentDV__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: TAFDC
- **Judge reason**: The chunk mentions that good cause for non-cooperation exists and should be explored, but does not define or list what specific reasons constitute good cause.

```
TAFDC > Program Nonfinancial Requirements > Child Support > Absent Parent Information at Application > Absent Parent: Domestic Violence

Cooperation with DTA and the Department of Revenue Child Support Enforcement (DOR/CSE) efforts is a requirement for TAFDC. The penalty for noncooperation is a reduction in TAFDC benefits (sanction). Cooperation or non-cooperation must be recorded on the Absence page in the Assessed Person Nonfinancials workflow. DOR/CSE determines if a client is cooperating with child support enforcement efforts or not. If you receive notice from DOR/CSE that the client is not cooperating, you must call the client to explain the child support process and answer any questions they have. You must also explore whether good cause for not cooperating exists or if they feel safe to cooperate. Consider asking a DV Specialist to assist you. This must be documented in a BEACON narrative. If you are not able to reach the client, schedule a case maintenance appointment to discuss this with them.

If a client agrees to cooperate, on the Absence page Cooperation tab you must:

1. click the Yes radio button in the Child support cooperation field
```

#### Rank 5 — PARTIAL (sim 0.548)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__Child_GoodCauseClaim__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: TAFDC
- **Judge reason**: The chunk explains the process for claiming good cause exceptions and client responsibilities, but does not specify what reasons actually qualify as good cause.

```
TAFDC > Program Nonfinancial Requirements > Child Support > Child Support Good Cause > Child Support Good Cause Claimed

Each TAFDC client must have the requirements for cooperating with child support enforcement efforts explained to them. Including, good cause exceptions to cooperation with the child support requirements and exploring whether good cause exists. Every client must also receive the Assignment of Support Rights, Cooperation with Child Support, or Good Cause Claim form (T-A34/36) as well as the Information about Support Assignment, Cooperation and Good Cause notice.

If the client wants to claim a good cause exception for cooperating with child support enforcement efforts, they are responsible for:

- Identifying the appropriate reasons that qualify as good cause, including the name of the child, and the name of the absent parent, if possible
- signing the Good Cause Claim section on the T-A34/36 and
- providing the verifications necessary to substantiate the good cause claim and/or requesting help from you to get verifications

Whenever a client claims a good cause exception to cooperating with the child support requirements, you must:
```


### olg_013 — teen parent eligibility (rank-1: PARTIAL)

**Question**: What eligibility requirements exist for teen / young parents?  
**Program filter**: `['TAFDC']`  
**Notes**: Teen/minor parent — living arrangement requirement, school attendance, adult-supervised housing.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.525)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__PU_DCFYPLPRef__000`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Describes a specific referral requirement for young parents under 22 rather than general eligibility requirements for TAFDC benefits for teen/young parents.

```
TAFDC > Program Nonfinancial Requirements > Parents Under 20 > DCF YPLP Referral

DTA refers pregnant and parenting individuals under 22 who apply for, and are receiving TAFDC benefits to the Department of Children and Families (DCF) for placement in a Young Parent Living Program (YPLP) when:

- the parent under 22 is homeless;
- the parent under 22 asserts that they cannot live in the home of their ownparent(s) because domestic violence, abuse, neglect, substance abuse, or other extraordinary circumstance exist in the home; and
- the parent is under age 18 and there is no adult relative age 20 or older or legal guardian with whom the parent can live.
```

#### Rank 2 — PARTIAL (sim 0.515)

- **Chunk ID**: `sec__TAFDC__TAFDC_What__001`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Mentions teen parent eligibility exists and references school attendance and living arrangement requirements, but does not detail what those specific requirements actually are.

```
TAFDC > What is TAFDC? > Eligibility

TAFDC is for families with children, and certain pregnant people with little or no income. Applicants/clients also must: have dependent children be Massachusetts residents be U.S. citizens or eligible qualified noncitizens have or have applied for a Social Security number for everyone applying for TAFDC be below TAFDC’s income limits

Important : A teen parent is eligible to receive TAFDC for her entire pregnancy if she meets the teen parent school attendance and living arrangement requirements.

People are NOT eligible for TAFDC if they:

- have an outstanding default warrant
- are fleeing prosecution or punishment for a felony
- are an undocumented noncitizen (undocumented noncitizens can get TAFDC for their U.S. citizen children)
- violated probation or parole assigned to them after September 25, 1996
```

#### Rank 3 — PARTIAL (sim 0.498)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__WPR_TAFDCPg__002`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Describes work program exemptions for teen parents rather than eligibility requirements for TAFDC enrollment itself.

```
TAFDC > Program Nonfinancial Requirements > Work Program Rules > Using the Work Requirements TAFDC Page > The Work Requirements TAFDC page is used for five reasons > Reason 2 - Work Program – Required No

Records why the client is not work program required using the Required Status Reason drop-down box.

- If the grantee is not work program required, select one of these reasons using the Required Status Reason drop-down box:

  - Child < 2 Years Old in the AU
  - Disab. Parent in 1 parent AU
  - SSI GR/OP
  - Pregnant / Due within 120 days
  - Both Parents Disabled in AU
  - Caring for a Disabled Person
  - Child < 2 Years Old on SSI
  - Disab. Parent in 2 Parent AU
  - Non Liable Ineligible Grantee
  - Ineligible Noncit Exempt
  - Noncit Child < 2 Years Old on SSI
  - Noncit Both Parents Disabled in AU
  - Noncit Disab. Parent in 2 Parent AU
  - Noncit Caring for a Disabled Person
  - Noncit Pregnant / Due within 120 days
  - Noncit Child < 2 Years Old in the AU
- For parents under age 20, and not work program required, additional exemption reasons are available and must be used:

  - Teen Parent – FT HS Student
  - Teen Parent – Basic Ed & Train./Employ
  - Teen Parent – Struct. Living Prog
  - Teen Parent – Pregnant
  - Noncit Teen Parent – FT HS Student
  - Noncit Teen Parent – Basic Ed & Train./Employ
  - Noncit Teen Parent – Struct. Living Prog
  - Noncit Teen Parent – Pregnant
```

#### Rank 4 — PARTIAL (sim 0.504)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__PU_DCFYPLPRefProc__000`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Discusses a program referral process for young parents rather than the eligibility requirements to qualify for TAFDC as a teen/young parent.

```
TAFDC > Program Nonfinancial Requirements > Parents Under 20 > DCF YPLP Referral Process

The Department of Children and Families (DCF) will place any parent under 22 that the Department of Transitional Assistance (DTA) refers for placement in a Young Parent Living Program (YPLP) when they do not have a safe place to stay or cannot reside with their parents. For parents under 18, placements in a YPLP may be necessary to meet the living arrangement rules.
```

#### Rank 5 — PARTIAL (sim 0.509)

- **Chunk ID**: `sec__TAFDC__ProgramNFReq__PU_Intro__002`
- **Section**: `` — 
- **Program**: TAFDC
- **Judge reason**: Addresses specific rules for parents under 20 (school attendance and living arrangements) but doesn't comprehensively cover all eligibility requirements for teen/young parents in TAFDC.

```
TAFDC > Program Nonfinancial Requirements > Parents Under 20 > Parents Under 20 Introduction > Exceptions to the Parent under 20 School Attendance and Living Arrangement Rules

The following circumstances are exceptions to the school attendance and living arrangement rules:

- A parent under 20 who gives birth is not required to meet the school attendance rules until the child turns three months old
- A TAFDC applicant who applies within 60 days of their 18th birthday meets the living arrangement rules if the school attendance rules are met, and
- A TAFDC applicant who applies within 60 days of  their 20th birthday is not required to meet the school attendance and living arrangement rules.

Note : For parents under 20 who have had a new baby, the compliance reason of Child Under <3 months must be selected in the Pathways Participant section of the Work Requirements TAFDC page to excuse them from school and prevent a sanction for not meeting school rules.

Note : If a person under 20 who is pregnant with no other children has already met their school rules by attaining a high school diploma or high school equivalency certificate, select Teen Parent – Pregnant from the Required status reason drop-down box on the Work Requirement TAFDC page for use in this specific situation.

Related Topics Self-Sufficiency Specialist Last Update: February 1, 2024
```


### olg_014 — EAEDC disability standard (rank-1: PARTIAL)

**Question**: What is the EAEDC disability standard and how do we verify?  
**Program filter**: `['EAEDC']`  
**Notes**: Disability definition + DET process + medical verification requirements.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.516)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Ctkr_FamDisabilityExempt__001`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: Addresses how to verify disability for EAEDC caretaker family exemption, but does not explain what the EAEDC disability standard itself is or the general disability verification process for EAEDC eligibility.

```
EAEDC > Categorical Requirements > Caretaker Family > Caretaker Family Disability Exemption > How is the Disability Exemption Verified?

To verify the disability or health condition you must explore available data sources to determine if a disability determination exists as described in Disability Verification-EAEDC

Where no existing disability determination is found, the client must be sent the EAEDC Medical Provider Statement to verify their disability or health condition.

You must then follow the procedures outlined in Responding to the EAEDC Medical Provider Statement and Entering the Disability-EAEDC to correctly record the disability or lack thereof, in BEACON.
```

#### Rank 2 — PARTIAL (sim 0.537)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_Verification__001`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: EAEDC
- **Judge reason**: The chunk explains how to verify disability for EAEDC but does not define what the EAEDC disability standard actually is (e.g., the specific criteria or definition of disability required).

```
EAEDC > Categorical Requirements > Disability > Disability Verification EAEDC

Case managers are able to verify disability for a client through the following:

- Disability Evaluation Services (DES), a division of forHealth Consulting at UMass Chan Medical School
- the Social Security Administration (SSA)
- MassHealth

Disability status for EAEDC eligibility can also be verified by:

- Massachusetts Rehabilitation Commission (MRC), or
- a competent medical authority.

For information on correctly entering the disability on the Disability and Disability Determination pages see Entering the Disability-EAEDC

An EAEDC client who is actively participating in a Massachusetts Rehabilitation Commission (MRC) training and/or rehabilitation program, including post-secondary education, is considered to be eligible for EAEDC based on a disability. The client must verify this by submitting a letter from MRC indicating that the client is actively participating in an education or training program with MRC.

For information on EAEDC eligibility based on participation in a Massachusetts Rehabilitation Commission (MRC) training and/or rehabilitation program see Participant in a Massachusetts Rehabilitation Commission Program - Overview
```

#### Rank 3 — PARTIAL (sim 0.542)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_Ovw__002`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: Addresses disability verification methods for EAEDC but does not explain what the disability standard itself is or provide the complete verification procedures.

```
EAEDC > Categorical Requirements > Disability > Disability Overview EAEDC > What if There is No Verified Disability Available?

If the client’s disability is not able to be verified by the above options, ask the client if they are participating in an MRC training and/or rehabilitation program including post-secondary education.

If the client is not participating in an MRC program then you must send the client the EAEDC Medical Provider Statement.

A completed and signed EAEDC Medical Provider Statement allows for a client to:

- become eligible for EAEDC,
- remain eligible for EAEDC, or
- be exempt from the EAEDC Caretaker Family DCS registration or TEMP rules.

At each application and each reevaluation, you must assess the client’s case to see whether a current disability verification exists. See Disability Verifications-EAEDC .
```

#### Rank 4 — PARTIAL (sim 0.518)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_Verification__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: EAEDC
- **Judge reason**: The chunk explains disability verification procedures for EAEDC but does not define what the EAEDC disability standard actually is (e.g., the specific criteria or definition of disability used for EAEDC eligibility).

```
EAEDC > Categorical Requirements > Disability > Disability Verification EAEDC

When a client claims a disability or health condition for EAEDC, you must explore whether the client already has a disability decision made by Disability Evaluation Services (DES), a division of forHealth Consulting at UMass Chan Medical School available in their Electronic Case Folder (ECF) or has been determined disabled by another source.

If a prior DES disability decision is found and has not expired, it is to be used to verify the current EAEDC disability until it expires.

- You must create an outlook reminder to review the disability when the DES approval is due to expire and send an EAEDC Medical Provider Statement if no other disability source is found.
- A disability that has been verified by another source is to be reviewed at each reevaluation.

Important : Clients who have previously been approved or recertified for EAEDC based on a self-declaration of their disability or a previously submitted EAEDC Medical Provider Statement must verify their disability during the next reevaluation or next reapplication, whichever is sooner unless there is three months or more remaining on the disability duration on the form or they have become eligible for EAEDC due to age.
```

#### Rank 5 — PARTIAL (sim 0.483)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_RespEAEDCMedProvStmt__000`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: The chunk explains how to verify disability using the Medical Provider Statement form but does not define what the actual EAEDC disability standard is or the specific criteria that must be met.

```
EAEDC > Categorical Requirements > Disability > Responding to the EAEDC Medical Provider Statement EAEDC

The EAEDC Medical Provider Statement is used to verify a disability or health condition:

- to determine eligibility for Emergency Aid to the Elderly Disabled and Children (EAEDC),
- for a disability exemption from the Department of Career Services (DCS) registration at MassHire or Transitional Employment for Massachusetts Parents (TEMP) participation rules in a Caretaker Family EAEDC case, or
- to verify SNAP eligibility for disabled noncitizens who do not meet SNAP eligibility based on their noncitizen status.

For information on sending this form to clients see Disability Verifications-EAEDC .

When the EAEDC Medical Provider Statement form is returned to the Department, you must review the form for completion, as well as the relevant information indicated on the form, to determine if the client is to be considered a person with a disability or health condition for EAEDC purposes.
```


### olg_015 — EAEDC categorical eligibility (rank-1: PARTIAL)

**Question**: What is considered EAEDC categorical eligibility?  
**Program filter**: `['EAEDC']`  
**Notes**: Categorical groups — age 65+, disabled, caretaker of disabled, participating in MRC/MCB, etc.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.531)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Part_MARehabComm__000`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: Describes one specific categorical eligibility pathway (MRC program participation) rather than comprehensively defining what is considered EAEDC categorical eligibility overall.

```
EAEDC > Categorical Requirements > Participant in a Massachusetts Rehabilitation Commission Program - Overview > What Does Participation in a Massachusetts Rehabilitation Commission (MRC) Program Mean for EAEDC?

An EAEDC client who is actively participating in a Massachusetts Rehabilitation Commission (MRC) training and/or rehabilitation program, including post-secondary education, is considered to be a person with a disability. This means they are eligible for EAEDC if they meet all other categorical, financial, and nonfinancial eligibility requirements of the EAEDC program.
```

#### Rank 2 — PARTIAL (sim 0.510)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_Ovw__000`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: The chunk discusses disability as a basis for EAEDC eligibility and exemptions, but does not comprehensively define what constitutes EAEDC categorical eligibility overall (which would include other categories beyond disability).

```
EAEDC > Categorical Requirements > Disability > Disability Overview EAEDC > Purpose of Claiming a Disability for EAEDC

An EAEDC client may claim a disability:

- to gain eligibility for EAEDC based on being a person with a disability or health condition that prevents them from working for 60 days or more, or
- as an exemption from the Department of Career Services (DCS) registration or the Transitional Employment for Massachusetts Families (TEMP) rules for the grantee in an EAEDC Caretaker Family case.

An EAEDC client who is actively participating in a Massachusetts Rehabilitation Commission (MRC) training and/or rehabilitation program, including post-secondary education, is considered eligible for EAEDC based on a disability.

The client must verify this by submitting a letter from MRC indicating that the client is actively participating in an education or training program with MRC.
```

#### Rank 3 — PARTIAL (sim 0.489)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_RespEAEDCMedProvStmt__000`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: The chunk discusses disability verification procedures for EAEDC eligibility but does not explain what categorical eligibility itself is or what categories qualify for EAEDC.

```
EAEDC > Categorical Requirements > Disability > Responding to the EAEDC Medical Provider Statement EAEDC

The EAEDC Medical Provider Statement is used to verify a disability or health condition:

- to determine eligibility for Emergency Aid to the Elderly Disabled and Children (EAEDC),
- for a disability exemption from the Department of Career Services (DCS) registration at MassHire or Transitional Employment for Massachusetts Parents (TEMP) participation rules in a Caretaker Family EAEDC case, or
- to verify SNAP eligibility for disabled noncitizens who do not meet SNAP eligibility based on their noncitizen status.

For information on sending this form to clients see Disability Verifications-EAEDC .

When the EAEDC Medical Provider Statement form is returned to the Department, you must review the form for completion, as well as the relevant information indicated on the form, to determine if the client is to be considered a person with a disability or health condition for EAEDC purposes.
```

#### Rank 4 — PARTIAL (sim 0.491)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Dis_Ovw__002`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: The chunk discusses disability verification procedures for EAEDC eligibility but does not explain what categorical eligibility itself is or what categories qualify for EAEDC.

```
EAEDC > Categorical Requirements > Disability > Disability Overview EAEDC > What if There is No Verified Disability Available?

If the client’s disability is not able to be verified by the above options, ask the client if they are participating in an MRC training and/or rehabilitation program including post-secondary education.

If the client is not participating in an MRC program then you must send the client the EAEDC Medical Provider Statement.

A completed and signed EAEDC Medical Provider Statement allows for a client to:

- become eligible for EAEDC,
- remain eligible for EAEDC, or
- be exempt from the EAEDC Caretaker Family DCS registration or TEMP rules.

At each application and each reevaluation, you must assess the client’s case to see whether a current disability verification exists. See Disability Verifications-EAEDC .
```

#### Rank 5 — PARTIAL (sim 0.496)

- **Chunk ID**: `sec__EAEDC__Categorical_Req__Care_VerfElightm__000`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: The chunk addresses verification requirements for a specific EAEDC category (caring for the disabled) rather than defining what categorical eligibility itself means or listing the categories.

```
EAEDC > Categorical Requirements > Caring for the Disabled > Verifying Eligibility of Person Being Cared For

The EAEDC applicant or client must provide the verifications of the disabled person being cared for. Verification must be provided at application, reevaluation, or at the time of any change.

Verification of a disability for the person being cared for is a written statement from the disabled person’s physician on the physician’s letterhead that verifies the disability, the need for constant care, and the risk of institutionalization without constant care.

Verification of financial eligibility for the person being cared for is in accordance with EAEDC regulations.

Although the disabled person being cared for is not requesting EAEDC, he or she is still an assessed person and must be included in the EAEDC case, with certain modifications.
```


### olg_016 — application timeliness (rank-1: RELEVANT)

**Question**: What are the application processing timeliness standards?  
**Program filter**: (none)  
**Notes**: 30-day standard, 7-day expedited, time clock start. Cross-program — no filter.  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.00  

#### Rank 1 — RELEVANT (sim 0.450)

- **Chunk ID**: `sec__PandP__PP_RFA_PolProcs__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: Policies & Procedures
- **Judge reason**: The chunk is a table of contents that directly lists section 361.700 'Timeliness Standards for Processing' which specifically addresses the user's question about application processing timeliness standards.

```
Cross Programs > Request for Assistance (RFA) > Request for Assistance (RFA) - Policy and Procedures > Regulations

| Chapter. Page | Title |
| --- | --- |
| 703.110 | Good Cause Waivers for Domestic Violence |
| 361.050 | Introduction |
| 361.080 | Prompt Action |
| 361.100 | Filing an Application |
| 361.110 | Where to File |
| 361.120 | Date of Application |
| 361.130 | Household Right to Same Day Filing |
| 361.140 | Mailing Applications to Households |
| 361.150 | Withdrawal of Application |
| 361.160 | Handling Applications for PA Households |
| 361.170 | Handling Applications for NPA Households |
| 361.180 | Handling Applications for Expedited Service Households |
| 361.190 | Handling Applications of Pure SSI Households |
| 361.200 | Household Concept |
| 361.210 | Elderly or Disabled Households |
| 361.220 | Head of Household |
| 361.310 | Authorized Representative to Make Application |
| 361.320 | Authorized representative to Obtain SNAP Benefits |
| 361.330 | Authorized Representative to Purchase Food |
| 361.350 | Drug and Alcohol Treatment Centers and Group Living Arrangements as Authorized Representatives |
| 361.360 | Restrictions on Appointment |
| 361.370 | Documentation and Control of Authorized Representatives |
| 361.400 | Household Refusal to Cooperate |
| 361.500 | Interviewing Households |
| 361.510 | Waiver of the Office Interview |
| 361.530 | Length of Certification When Office Interview is Waived |
| 361.540 | Scheduling Interviews |
| 361.550 | Content of Interviews |
| 361.700 | Timeliness Standards for Processing |
| 361.800 | Expedited processing |
```

#### Rank 2 — PARTIAL (sim 0.471)

- **Chunk ID**: `sec__PandP__PP_RFA_PolProcs__001`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: Policies & Procedures
- **Judge reason**: The chunk is a table of contents listing regulations related to application processing and timeliness (delays, expedited service, processing standards) but does not contain the actual standards themselves, only section references.

```
Cross Programs > Request for Assistance (RFA) > Request for Assistance (RFA) - Policy and Procedures > Regulations

| Chapter. Page | Title |
| --- | --- |
| 361.900 | Delays In Processing |
| 361.910 | Household Caused Delay |
| 361.920 | Department Caused Delay |
| 361.930 | Notification of Pending Status |
| 361.940 | Providing Benefits to Eligible Households |
| 361.950 | Notice of Denial to Ineligible Households |
| 361.960 | Delays Beyond 60 Days |
| 365.800 | Expedited Service |
| 365.810 | Expedited Service Households |
| 365.820 | Expedited Service Processing Standards |
| 365.830 | Expedited Service Verification Requirements |
| 365.840 | Determining Eligibility and Benefit Level for Expedited Service Households |
| 365.850 | Assigning Certification Periods to Expedited Service Households |
| 701.220 | Obtaining Benefits |
| 701.300 | Rights of Applicants and Recipients |
| 701.310 | Right to Nondiscrimination and Equal Treatment |
| 701.320 | Right to Confidentiality |
| 701.330 | Right to Information |
| 701.340 | Right to a Fair Hearing |
| 701.350 | Right to Representation |
| 701.360 | Right to Interpreter Services |
| 701.360 | Right to Interpreter Services |
| 701.390 | Department Obligations Under Title II of the Americans With Disabilities Act (ADA) |
| 701.400 | Responsibilities of Applicants and Recipients |
| 702.110 | The Application Process |
| 702.115 | Filing of Applications |
| 702.120 | The Application Interview |
| 702.125 | Application Activities |
| 705.210 | Obtaining Food Stamps |
```

#### Rank 3 — PARTIAL (sim 0.403)

- **Chunk ID**: `sec__EAEDC__Basic_CA_Maint__Appl_AppIntvWFTabRFA__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: EAEDC
- **Judge reason**: The chunk mentions that application interviews must occur within seven days to meet 'appropriate time standards for application processing' but does not specify what those actual timeliness standards are.

```
EAEDC > Basic Case Activities Maintenance > EAEDC Application Interview > Application Interview: Workflow Tab - RFA

The Request for Assistance (RFA) is the first step in processing an EAEDC application. You complete the RFA on the Home page Workflow tab. As part of the RFA, on the Immediate Needs tab on the Program RFA page you will make a determination of the client’s eligibility for a food voucher or shelter payment (including rent, fuel and utilities) or medical care assistance in advance of completing the application interview, when requested.

When you have completed the Request for Assistance workflow, print the RA-1 Notice. Give or mail a copy of the RA-1 Notice to the client.

A client can apply for EAEDC by initiating an application online, or calling DTA directly. See Telephonic Signature. The application interview may be completed on the same day the RFA is made, or you can schedule a future appointment once any immediate needs are determined. A scheduled application interview must take place as soon as possible (no later than seven days from the date of initial contact by the client) to ensure that appropriate time standards for application processing are met, including Expedited Benefits in a combination cash-SNAP case. If during the interview the client refuses to provide the telephonic signature for the application, you must deny the application as a voluntary withdrawal.
```

#### Rank 4 — RELEVANT (sim 0.461)

- **Chunk ID**: `sec__CrossProg__Verifications__Vers_Basic_Application__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Directly addresses application processing timeliness standards by specifying the timeframes for verification submission across SNAP (30 days), TAFDC (22 days + 8 days), and EAEDC programs.

```
Cross Programs > Verifications > Basic Verification Activities Timelines > Verifications at Application

At application, clients must verify all mandatory financial and nonfinancial eligibility factors prior to the issuance of benefits. To ensure that applications are processed timely and correct documentation is issued, you must enter verifications as soon as they are received from the applicant. For SNAP, applicants have until day 30 day to provide any verifications determining eligibility and grant amount. For TAFDC and EAEDC, client have 22 days with an additional 8 days to provide any verifications determining eligibility and grant amount.

The following are the detailed procedures for verification requirements separated by program (SNAP, TAFDC, and EAEDC).
```

#### Rank 5 — PARTIAL (sim 0.450)

- **Chunk ID**: `sec__CrossProg__Hearings__Hrngs_ApplTimeFrms__003`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: This chunk addresses appeal decision timeframes rather than application processing timeliness standards, though it mentions failure to act on applications timely as an appeal issue.

```
Cross Programs > Hearings > Appeal Time Frames > Division of Hearings Time frames

The DOH referee must render a final decision within 45 days of the date of request for a hearing when the issue under appeal is:

- the denial of the right to apply or reapply for assistance
- the denial of an application for assistance; or
- the failure to act on an application in a timely manner.

Note : The DOH referee must render a final decision within 90 days of the date of request for a hearing for all other appeals.
```


### olg_017 — residency verification (rank-1: PARTIAL)

**Question**: What are some acceptable verifications for residency?  
**Program filter**: (none)  
**Notes**: VERIFICATION CHART TEST — should hit the manually-overridden topical chunks (12, not 32 alphabetical). Regression check on Q35-style retrieval.  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 1.75  

#### Rank 1 — PARTIAL (sim 0.497)

- **Chunk ID**: `sec__CrossProg__Verifications__Vers_Mthds_SelfDeclar__008`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: Cross-Program
- **Judge reason**: The chunk discusses residency verification requirements and circumstances for reverification, but does not provide a list of acceptable verification methods for establishing residency.

```
Cross Programs > Verifications > Verification Methods > Self-Declaration > Telephonic and DTA Connect Self-Declaration > SNAP

- ABAWD Work Rules Exemptions
- Address Change* (if a client who already verified Massachusetts residency reports a new address in Massachusetts)

Reminder : If a client appears on the Out of State EBT Card Usage Match and their EBT usage patterns are not consistent with someone who resides near the Massachusetts border, they must reverify residency because their EBT usage patterns make their residency questionable. (However, Simplified Reporting households who appear on the match do not have to reverify residency during case maintenance—only during application, recertification or IR.) For more information, see Out of State EBT Card Usage Match .
```

#### Rank 2 — PARTIAL (sim 0.481)

- **Chunk ID**: `sec__CrossProg__Matches__ExtAgncyMtchs_OOS-EBTCrdUsgMtch__018`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: The chunk discusses self-declaration as an acceptable verification method when other documentary evidence cannot be obtained, but does not provide a comprehensive list of the primary acceptable verifications for residency (such as utility bills, lease agreements, etc.).

```
Cross Programs > External Agency Matches > The Out of State EBT Card Usage Match > FAW/Case Manager Responsibilities > When a Self-Declaration is Acceptable

If a matched client has made a good faith effort to verify their Massachusetts residency using documentary evidence or collateral contact but was unsuccessful due to mitigating factors, the client may submit a written self-declaration of their intent to continue residing in Massachusetts.

Examples of acceptable mitigating circumstances include ( but are not limited to ):

- The client is homeless or fleeing domestic violence.
- The client is hospitalized (i.e., where they are unable to mail or upload any Massachusetts residency verification).
- The client is unable to obtain verification from a third party (e.g., landlord or landlord’s agent) due to the third party’s noncooperation.

If a household is coded in BEACON as homeless, the Residency Verification Notice will include additional language to accommodate homeless clients who have more difficulty obtaining verification of residency: “If you are a Massachusetts resident and do not have other proofs, you can send us a written statement about your residency.”
```

#### Rank 3 — RELEVANT (sim 0.492)

- **Chunk ID**: `sec__CrossProg__Verifications__Vers_VC1_QandA__001`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: Cross-Program
- **Judge reason**: The chunk directly addresses acceptable verifications for residency, listing data sources, documentary verifications (paystubs, RMV, SSA), collateral contact, and self-declaration as acceptable methods.

```
Cross Programs > Verifications > Verification Checklist (VC-1) > VC-1 Q and A > Homeless

Q1 . Doug Jones (he/him) is a SNAP applicant who states he is homeless. How do I verify residency for this client?

A1 . Residency can be verified in a variety of ways. First, explore whether it can be verified through a data source or via other documentary verifications, such as a paystub or through the RMV or SSA. Before requesting proof of residency you must explore if reasonable proof has already been provided. Remember that collateral contact can also be utilized. In extreme circumstances where the client is unable to provide documentary evidence or DTA is unable to establish collateral contact to verify residency, as is often the case for homeless clients, a signed self-declaration (including the application or recertification form) may be accepted.

Q2 . Lisa Bourne (she/her) is a SNAP applicant, she states that she is homeless and does not have a mailing address she can use. Must she provide a mailing address?

A2. Yes, DTA needs a mailing address to send clients important information. Clients experiencing homelessness may need assistance in identifying an address to use such as that of a friend, relative, authorized representative or shelter. As a last resort, the Document Processing Center (DPC) address may be used. The client must sign the Using DPC for Mailing Address (DPC-MADD) form , which details conditions for use of the DPC address. Clients must be told that they cannot pick up mail from the DPC.
```

#### Rank 4 — RELEVANT (sim 0.536)

- **Chunk ID**: `sec__CrossProg__Matches__ExtAgncyMtchs_OOS-EBTCrdUsgMtch__008`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: The chunk directly lists acceptable verifications for residency (utility bills, lease agreements, rent receipts, property tax bills, and letters from head of household) with specific requirements for each.

```
Cross Programs > External Agency Matches > The Out of State EBT Card Usage Match > Residency Verification Must Be Current

All documentary evidence of residency must be current. “Current” is defined relative to the type of verification that a matched client chooses to submit. Generally, for bills, “current” is based on the billing cycle, which can vary by expense type. For lease agreements, “current” refers to the duration of the agreement. Signed confirmation letters from landlords, shelters, or housing providers must be dated within the last 60 days.

The table below provides some examples:

| Document Type | Considered “Current” If... |
| --- | --- |
| Utility Bill | Dated within the last 60 days |
| Lease Agreement | Shows active term for the client’s current address; e.g., to verify address, a client submits a lease which does not expire for at least another 6 months. |
| Rent Receipt | Dated within the last 60 days |
| Property Tax Bill | Dated for the most recent quarter, half-year, or year; depending on the billing cycle |
| Letter from the Head of Household (if the client is in a shared living situation) | Dated within the last 60 days |
```

#### Rank 5 — PARTIAL (sim 0.467)

- **Chunk ID**: `sec__EAEDC__Gen_NonFinancial_Req__Temp_MA__001`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: EAEDC
- **Judge reason**: The chunk addresses verifications for temporary absence from Massachusetts rather than verifications for residency itself, though it does list some residency-related documents (rent/mortgage receipts, utility bills, telephone bills) as acceptable proof of continued residence.

```
EAEDC > General Nonfinancial Requirements > Temporary Absence from MA > Temporary Absence from MA - EAEDC > Allowable Temporary Absences

Temporary absences from Massachusetts are allowed for the following circumstances:

- health
- business
- school
- family commitments

A client must verify an allowable circumstance and the fact that it is temporary in nature. Once the verification is received, your supervisor must approve the temporary absence.

The following are acceptable verifications for temporary absence:

- Health situation: verified by medical documentation
- Business: verified by a short-term business contract
- School: verified by school documents
- Family commitments: one of the following documents, provided it bears the name and Massachusetts address of the client as proof he or she intends to return:

  - a current rent or mortgage receipt
  - a current utility bill
  - a current telephone bill, or
  - any other form of documentation that the supervisor determines verifies the continued residence or intent to retain residency

When a temporary absence situation is approved, you must record it on the Temporary Absence Page in the AU Composition Details workflow. See the Temporary Absence Page for details on how to record absence information. In addition, you should place a reminder of the end of the temporary absence period on your calendar on the BEACON Home page.
```


### olg_018 — fair hearing rights (rank-1: PARTIAL)

**Question**: What are the fair hearing rights and timeframes?  
**Program filter**: (none)  
**Notes**: BP material — rights to hearing, request timeframe, scheduling, decision timeframe. Cross-program.  
**Scores**: Relevant@5 = 1, Useful@5 = 5, rank-weighted = 1.50  

#### Rank 1 — PARTIAL (sim 0.424)

- **Chunk ID**: `sec__CrossProg__Hearings__Hrngs-RoleHrngOff_TelephFairHrngs__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Describes what fair hearings are and formats available, but does not address the specific timeframes or detailed rights the user is asking about.

```
Cross Programs > Hearings > The Role of a Hearing Officer > Telephonic Fair Hearings

Clients have the right to appeal certain actions or decisions made by DTA. Appeals are heard and decided through the fair hearings process.

A fair hearing is a proceeding where the appropriateness of certain DTA decisions can be reviewed by DTA’s Division of Hearings (DOH). Fair hearings can be completed in person, by telephone, or virtually.
```

#### Rank 2 — PARTIAL (sim 0.427)

- **Chunk ID**: `sec__CrossProg__Hearings__Hrngs_RtFairHrngHowClntFls__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Explains what fair hearing rights are and the process, but does not address specific timeframes for filing or decisions.

```
Cross Programs > Hearings > Right to a Fair Hearing: How a Client Files

If an applicant or client (hereafter called client) disagrees with a Department (DTA) action, s/he has the right to appeal. If a client requests an appeal, s/he will have a fair hearing. A fair hearing is a proceeding where the client can receive a determination of the appropriateness of certain actions or inactions by the DTA from the Division of Hearings (DOH). DOH is an impartial division within the Department that administers hearings and renders decisions for appeals requested by clients.
```

#### Rank 3 — PARTIAL (sim 0.424)

- **Chunk ID**: `sec__CrossProg__Hearings__Hrngs-RoleHrngOff_VrtlFairHrngs__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Describes what fair hearings are and formats available, but does not address specific rights or timeframes that the user is asking about.

```
Cross Programs > Hearings > The Role of a Hearing Officer > Virtual Fair Hearings

Clients have the right to appeal certain actions or decisions made by DTA. Appeals are heard and decided through the fair hearings process.

A fair hearing is a proceeding where the appropriateness of certain DTA decisions can be reviewed by DTA’s Division of Hearings (DOH). Fair hearings can be completed in person, by telephone, or virtually.
```

#### Rank 4 — RELEVANT (sim 0.485)

- **Chunk ID**: `sec__CrossProg__Hearings__Hrngs_ApplTimeFrms__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Directly addresses fair hearing rights and timeframes by explaining when clients can request hearings and the timeframe requirements for submitting requests to the Division of Hearings.

```
Cross Programs > Hearings > Appeal Time Frames > Client Right of Appeal Time frames

The date of request for a fair hearing is the date on which the Division of Hearings (DOH) receives a written statement from the client asking for the opportunity to present his\her disagreement with a Department action or inaction. The DOH must receive the request for a fair hearing from a client within the following time frames:
```

#### Rank 5 — PARTIAL (sim 0.414)

- **Chunk ID**: `sec__CrossProg__Hearings__Hrngs-RoleHrngOff_InPrsnFairHrngs__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Describes what fair hearings are and formats available, but does not address the specific timeframes or detailed rights the user is asking about.

```
Cross Programs > Hearings > The Role of a Hearing Officer > In-Person Fair Hearings

Clients have the right to appeal certain actions or decisions made by DTA. Appeals are heard and decided through the fair hearings process.

A fair hearing is a proceeding where the appropriateness of certain DTA decisions can be reviewed by DTA’s Division of Hearings (DOH). Fair hearings can be completed in-person, by telephone, or virtually.
```


### olg_019 — overpayment classification (rank-1: PARTIAL)

**Question**: What is the difference between IPV, UPV, and AE overpayments?  
**Program filter**: (none)  
**Notes**: Three-way distinction — Intentional Program Violation, Unintentional Program Violation, Agency Error. Should pull BP/Cross-Program overpayment pages.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.395)

- **Chunk ID**: `sec__CrossProg__OverpayRecov__OverpyRec_UnintentPrgmViols__000`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: The chunk defines UPV but does not explain IPV or AE overpayments, so it only partially addresses the comparative question about differences between the three types.

```
Cross Programs > Overpayments and Recovery > Unintentional Program Violations

An Unintentional Program Violation (UPV) is a claim related to an over issuance caused by a misunderstanding or unintended error on the part of the household. UPV causes include, but are not limited to, instances in which the household:

- unintentionally failed to provide correct or complete information,
- unintentionally failed to report a change in circumstances, or
- received more benefits than it was entitled to receive, pending a Fair Hearing decision.

Referrals for potential overpayment screening are sent to the DTA Fraud Overpayment Referral Screening Unit (FORS), which is responsible for reviewing the referral for completeness and accuracy.

Once reviewed, the FORS Unit investigates all UPV referrals. If sufficient evidence is gathered to demonstrate a UPV, the FORS Unit calculates the overpayment and closes the referral. Closing the referral creates the overpayment.

See Appeals for Overpayment Recovery .
```

#### Rank 2 — PARTIAL (sim 0.382)

- **Chunk ID**: `sec__CrossProg__OverpayRecov__OverpyRec_UnintentPrgmViols__003`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: The chunk discusses how to calculate UPV and AE overpayments and briefly mentions they are different categories, but does not explain the substantive differences between IPV, UPV, and AE overpayments themselves.

```
Cross Programs > Overpayments and Recovery > Unintentional Program Violations > Calculating the Amount of an Unintentional Program Violation Claim

The amount of an over issuance claim is determined by calculating the difference between the amount of benefits the household actually received and the amount the household was eligible to receive during the time period in question.

Note: If the household received excess benefits because it unintentionally failed to report a change in circumstances, the first month of over issuance shall be the month the change would have been effective, had it been reported on time.

If the UPV resulted from the client not reporting earned income, when the FORS Unit calculates the amount the household should have received, they do not apply the earned income deduction to the portion of income that the household failed to report.

If a notice of adverse action was required, but not provided by the Department, for the purpose of calculating the claim, the Department shall assume the maximum advance notice period would have expired without the household’s requesting a fair hearing.

Once the overpayment amount has been calculated and the referral submitted, the FORS Unit will review the calculation for accuracy and modify the amount if needed.

Note: Overpayment claims must be properly categorized in the AR Referral Folder. If the overpayment occurred as a result of Department action or inaction, the claim type must be coded as an Agency Error (AE) and not an UPV.
```

#### Rank 3 — PARTIAL (sim 0.392)

- **Chunk ID**: `sec__CrossProg__OverpayRecov__OverpyRec_IntntnlPrgmViols__003`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: The chunk explains how to calculate overpayment amounts but does not distinguish between the three specific overpayment types (IPV, UPV, and AE) that the user is asking about.

```
Cross Programs > Overpayments and Recovery > Intentional Program Violations > Calculating the Amount of an Intentional Program Violation Claim

The amount of an over issuance claim is determined by calculating the difference between the amount of benefits the household actually received and the amount the household was eligible to receive during the time period in question.

Note: If the claim is related to program fraud or trafficking, the amount of the overpayment is based on either the individual’s admission of the amount they trafficked, a court decision, or documentation that informs how much they trafficked, such as EBT transaction data.
```

#### Rank 4 — PARTIAL (sim 0.416)

- **Chunk ID**: `sec__CrossProg__OverpayRecov__OverpyRec_IntntnlPrgmViols__000`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: Cross-Program
- **Judge reason**: The chunk defines IPV but does not explain the differences between IPV, UPV, and AE overpayments as requested.

```
Cross Programs > Overpayments and Recovery > Intentional Program Violations > Calculating the Duration of an Intentional Program Violation Claim

An Intentional Program Violation (IPV) is a claim related to an over issuance caused when household intentionally lies, conceals information, or misrepresents facts to obtain or maintain benefits. This also includes benefit trafficking. This could be due to a household:

- providing inaccurate information to DTA,
- withholding information,
- misusing DTA benefits (trafficking), or
- knowingly receiving duplicate benefits.

Referrals for potential overpayment screening are sent to the DTA Fraud Overpayment Referral Screening Unit (FORS), which is responsible for reviewing the referral for completeness and accuracy.

Once reviewed, if an IPV is suspected, the referral is referred to either DTA’s Administrative Disqualification Unit (ADU) or the State Auditor’s Office Bureau of Special Investigations (BSI).
```

#### Rank 5 — PARTIAL (sim 0.400)

- **Chunk ID**: `sec__SNAP__IPV__IPV_Overview__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk defines IPV and briefly mentions UPV, but does not explain the differences between these categories or address AE overpayments at all.

```
SNAP > Intentional Program Violation > Intentional Program Violation Overview > Definition of an Intentional Program Violation (IPV)

An IPV is any action taken by a client for the purpose of establishing or maintaining SNAP eligibility or for increasing or preventing a reduction in the benefit amount which is committed knowingly, willfully, and/or with deceitful intent, such as:

- making a false statement(s) to the Department, either orally or in writing, to obtain or maintain SNAP benefits to which the household is not entitled
- concealing information to obtain or maintain SNAP benefits to which the household is not entitled
- making a false or misleading statement(s) or misrepresentation(s) to conceal or withhold facts to obtain or maintain SNAP benefits to which the household is not entitled
- altering or transacting SNAP benefits to obtain benefits to which the household is not entitled
- using SNAP benefits to buy nonfood items such as alcohol or tobacco
- using or possessing improperly obtained SNAP benefits
- trading/trafficking (buying or selling) SNAP benefits; or
- intentionally committing any act(s) which violates state regulations of the Supplemental Nutrition Assistance Program.

Note : An unintentional program violation (UPV) is when an overpayment occurs that is the result of a misunderstanding or unintended error on the part of the household or of an error caused by a Department action or failure to act.
```


### olg_020 — DV disclosure procedure (rank-1: RELEVANT)

**Question**: What special actions must be taken when a client discloses that they are victims of domestic violence and want to receive support from a DV specialist?  
**Program filter**: (none)  
**Notes**: DV protections — confidentiality, address suppression, DV specialist referral, waivers from cooperation requirements. Cross-program.  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.637)

- **Chunk ID**: `sec__BP__Procedures__BPp_Resp_Callers_RA__003`
- **Section**: `` — 
- **Program**: BP
- **Judge reason**: The chunk directly addresses the specific actions DTA case managers must take when a client discloses domestic violence, including referral to a DV Specialist, informing about services, and offering the HLS option.

```
Business Process (BP) > Procedures > Phone Procedures > Responding to Callers Requesting Assistance > Domestic Violence

DTA helps victims of domestic violence achieve economic self-sufficiency, safely. Clients who contact the Assistance Line to inform a case manager of domestic violence issues must be referred to a Domestic Violence (DV) Specialist.

Important: While you are obligated to make a referral to the DV Specialist, the client is not obligated to meet with the DV Specialist.

If a client caller informs a case manager of domestic violence issues, you must:

- inform the client of domestic violence services
- review list of statewide Domestic Violence Specialists and select one based on the client’s catchment area (see Policy, Program and External Relations on DTA Online Intranet for DV Specialists list)
- make a referral to the Domestic Violence Specialist
- provide the client with the option of a Heightened Level of Security Indicator (HLS)

Note: The HLS indicator must not be selected if the client has not returned the HLS-1 form.

Client callers who have informed the Department of domestic violence issues may have an HLS indicator that will appear on the client’s Electronic Case Folder (ECF). If an HLS indicator is present and the client contacts the Department, you must:

- inform the client that information regarding his/her case cannot be discussed over the phone, and
- provide the client with TAO information, if requested
```

#### Rank 2 — RELEVANT (sim 0.638)

- **Chunk ID**: `sec__DomViolence__DV_Narratives__000`
- **Section**: `` — 
- **Program**: Domestic Violence
- **Judge reason**: Directly addresses the required actions when clients disclose domestic violence, including mandatory referral to DV Specialists and specific procedures for handling sensitive information.

```
Domestic Violence > Domestic Violence Narratives > Overview

Clients may disclose to staff that they are experiencing domestic violence (DV) at any point in time while interacting with the Department of Transitional Assistance (DTA). Staff are required to refer clients to a Domestic Violence Specialist (DV Specialist) when they disclose a history of DV, express that they have current safety concerns, are struggling to meet certain program requirements including the work program, are in need of resources or are claiming good cause for child support . DV Specialists can work with a client regardless of their eligibility for DTA services.

While detail and documentation are important in most narratives, the sensitive nature of DV situations requires that narratives limit the information included to protect clients’ safety and privacy. It can be retraumatizing for clients to discuss their circumstances several times with multiple staff members and inputting more information than necessary into BEACON can be a safety risk for the client.

Any relevant DV information or details that staff needs to send to the DV Specialist must be relayed via email in the DV Referral (Please see Domestic Violence Referrals page), which is sent to the applicable regional distribution list. Additional documentation in the narrative is not needed.
```

#### Rank 3 — PARTIAL (sim 0.601)

- **Chunk ID**: `sec__DomViolence__DV_Narratives__002`
- **Section**: `` — 
- **Program**: Domestic Violence
- **Judge reason**: The chunk describes DV Specialist documentation and narrative procedures after a referral, but does not address the initial actions or special procedures that must be taken when a client first discloses domestic violence and requests DV specialist support.

```
Domestic Violence > Domestic Violence Narratives > Domestic Violence Specialist Narratives

Whenever a DVS interacts with a client, they must input the following narratives into BEACON, depending on what is applicable:

- “Received referral, spoke/met with client.”
- “HLC assessment completed.”
- “Received referral. Attempted to contact client, left voicemail with my contact information.”
- “Received referral. Client declined to speak/meet to Specialist at this time.”

The DV Specialist must not narrate specifics of conversations that they had with a client. Any information that the DV Specialist needs to record will be contained in the DV Log. The DV Log is only accessible by DV staff and designated managers. The simplified narratives above serve to confirm to staff and supervisors that the referral process was attempted and/or completed. Staff and supervisors will be able to scan for these narratives to confirm that a conversation was had with a DV Specialist.

Note : The DV Specialist will share information that is pertinent to a client’s DTA benefits with staff. Not all information that is shared by a client with a DV Specialist will be available to staff. They will use their discretion as to what information needs to be disclosed. If a case manager has questions about the DV and it is impacting a client’s case, they may reach out to the DV Specialist with the understanding that they may not get a detailed response.
```

#### Rank 4 — RELEVANT (sim 0.608)

- **Chunk ID**: `sec__DomViolence__DV_Specialists__000`
- **Section**: `` — 
- **Program**: Domestic Violence
- **Judge reason**: The chunk directly addresses the special action required when a client discloses domestic violence—referral to a DV Specialist—and explains the specialist's role and services.

```
Domestic Violence > Domestic Violence Specialists

DTA’s Domestic Violence (DV) Specialists help to ensure that safety threats are addressed quickly, and that all appropriate domestic violence services and relevant community resources are made available to survivors of DV.

DV Specialists are qualified to provide many services to survivors of DV, including assisting applicants and clients (hereafter referred to as clients) with documenting and obtaining verifications for good cause due to domestic violence claims in all DTA programs, and/or filing DV Waiver requests for certain TAFDC requirements.

Survivors of DV are to be referred to the office's assigned DV Specialist so that they may receive information about available Domestic Violence Unit and Services.

Important : While you are obligated to make a referral to the DV Specialist, the client is not obligated to meet with the DV Specialist.
```

#### Rank 5 — RELEVANT (sim 0.621)

- **Chunk ID**: `sec__EAEDC__Basic_CA_Maint__Appl_AppIntOVEAEDC__004`
- **Section**: `` — 
- **Program**: EAEDC
- **Judge reason**: The chunk directly addresses the required action when a client discloses domestic violence by stating they must be referred to the DV Specialist and informed about DV services.

```
EAEDC > Basic Case Activities Maintenance > EAEDC Application Interview > EAEDC Application Interview Overview > Domestic Violence Supports

EAEDC applicants must be informed about services and support offered by the Domestic Violence (DV) Unit. Any client indicating a history of or who is currently experiencing domestic violence must be referred to the DV Specialist.

See Domestic Violence Services Available and Domestic Violence Specialists .
```


### olg_021 — ABAWD acronym (rank-1: RELEVANT)

**Question**: ABAWD  
**Program filter**: (none)  
**Notes**: ADVERSARIAL — bare acronym. Tests whether retrieval surfaces the ABAWD work-requirement pages from a single rare token. Expected to be a hybrid-search win.  
**Scores**: Relevant@5 = 2, Useful@5 = 5, rank-weighted = 2.00  

#### Rank 1 — RELEVANT (sim 0.356)

- **Chunk ID**: `sec__SNAP__WorkRules__WR_ABAWDOvw__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk directly defines ABAWD and explains the ABAWD Work Rules, which is exactly what the user is asking about.

```
SNAP > SNAP Work Rules (General and ABAWD) > ABAWD Work Rules > ABAWD Work Rules Overview > Overview

If a SNAP client must meet the General Work Rules , they may also have to meet additional rules. These additional rules are the ABAWD Work Rules.

The ABAWD Work Rules were once called the “ABAWD Work Program Requirement.” “ABAWD” is a federal term that means “Able-Bodied Adult Without Dependents.” You may also hear these rules referred to as the “three-month time limit” or “time-limited benefits.”

All clients who are subject to the ABAWD Work Rules are also subject to the General Work Rules. But some clients who are subject to the General Work Rules are exempt from the ABAWD Work Rules.
```

#### Rank 2 — PARTIAL (sim 0.345)

- **Chunk ID**: `sec__SNAP__WorkRules__WR_ABAWDClock__006`
- **Section**: `` — 
- **Chunk position**: 3 / 3
- **Program**: SNAP
- **Judge reason**: The chunk discusses ABAWD clock tracking and strike documentation but doesn't define what ABAWD is or explain the fundamental policy, which is likely what a user searching for 'ABAWD' would need.

```
SNAP > SNAP Work Rules (General and ABAWD) > ABAWD Work Rules > The ABAWD Clock Page > ABAWD Clock Detail

a. The field will display one of the following descriptions:
    - ABAWD First Strike
    - ABAWD Second Strike
    - ABAWD Third Strike
    - Exception Month 1
    - Exception Month 2
    - Exception Month 3
    - ABAWD Ineligibility Strike
9. Volunteer Checkbox – if the client is meeting the ABAWD Work Rules by volunteering, indicates whether they volunteered for the month.
10. For more information on this checkbox, see Tracking Community Service Participation .
11. Good Cause Checkbox – indicates whether the client has good cause for the not meeting the ABAWD Work Rules during the month. BEACON will check this box automatically if a client is granted good cause in advance of the month (Example: if the client establishes in March that they will have good cause in April).
12. For more information on this checkbox, see Entering Good Cause for Future Months .
```

#### Rank 3 — PARTIAL (sim 0.336)

- **Chunk ID**: `sec__SNAP__WorkRules__WR_ABAWDClock__004`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: The chunk describes technical details about the ABAWD Clock Detail interface and fields, but doesn't explain what ABAWD is, its purpose, or the actual work rules themselves.

```
SNAP > SNAP Work Rules (General and ABAWD) > ABAWD Work Rules > The ABAWD Clock Page > ABAWD Clock Detail

The ABAWD Clock Detail displays information about an individual participation month. You must use the window to add or remove strikes. You can access this page from the ABAWD Clock page by clicking the magnifying glass icon underneath the Detail field:

Clicking the icon for the corresponding month will open that month’s ABAWD Clock Detail. The ABAWD Clock Detail includes the following fields:

1. Period – displays the applicable 36-month ABAWD clock
2. ABAWD Required – displays whether the client was required to meet the WR for the month displayed in the Benefit field
3. Strike – displays whether an active strike applies to the month

  a. The field will be blank if the client did not receive a strike.
  b. The field will say “No” if a strike was removed.
  c. Months with no strike history will be blank.
  d. The field will say “Exception” if the month was the second or third Exception Month.
4. Regain Eligibility – displays whether a client regained eligibility during a particular month after getting three strikes
```

#### Rank 4 — RELEVANT (sim 0.344)

- **Chunk ID**: `sec__SNAP__WorkRules__WR_WaivedAreas__000`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses ABAWD policy by explaining the current status of geographic waivers and how they affect ABAWD work rules and time limits.

```
SNAP > SNAP Work Rules (General and ABAWD) > ABAWD Work Rules > Waived Areas

The ABAWD geographic waiver ended on June 30, 2025. Until further notice no clients are waived from the ABAWD work rules and the time limits due to being a “Resident of a Waived Area.” Staff will continue to see the “Resident of a Waived Area?” exemption question on the ABAWD Work Rules Screening tab, however, the question will remain grayed out and defaulted to “No” for all clients.
```

#### Rank 5 — PARTIAL (sim 0.334)

- **Chunk ID**: `sec__SNAP__WorkRules__WR_GoodCauseABAWD__006`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Addresses ABAWD procedures for recording good cause in BEACON system, but the user's question is just 'ABAWD' with no specific question asked, making it unclear what information they actually need.

```
SNAP > SNAP Work Rules (General and ABAWD) > ABAWD Work Rules > Good Cause Criteria for Not Complying with the ABAWD Work Rules > How Do I Record Good Cause?

To record good cause in BEACON, you must:

1. open the ABAWD Clock page
2. for the strike month, click the icon under the Detail field to open the ABAWD Clock Detail
3. in the Strike dropdown, select No
4. in the Reason dropdown, select the applicable Good Cause reason
5. click Save

See ABAWD Clock Page for more details.
```


### olg_022 — VC-1 form lookup (rank-1: RELEVANT)

**Question**: VC-1  
**Program filter**: (none)  
**Notes**: ADVERSARIAL — form code. VC-1 is the verification request form. Tests rare-token retrieval. Should pull Verification Chart and form-related pages.  
**Scores**: Relevant@5 = 4, Useful@5 = 5, rank-weighted = 2.45  

#### Rank 1 — RELEVANT (sim 0.293)

- **Chunk ID**: `sec__SNAP__Proration__Pro_Recertification__005`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses VC-1 (Verification Checklist) requirements and scenarios where it was not sent or sent late in the context of SNAP recertification.

```
SNAP > Proration > Fault Determination and Proration – Recertification > Department Fault > No VC-1

An interview was conducted, mandatory verifications are needed, but a VC-1 was not sent or was sent late.
```

#### Rank 2 — RELEVANT (sim 0.262)

- **Chunk ID**: `sec__CrossProg__SSPS__SSPS-Pymnts_FnrlFnlDisp_PrintVC-1__000`
- **Section**: `` — 
- **Chunk position**: 1 / 2
- **Program**: Cross-Program
- **Judge reason**: The chunk directly explains what a VC-1 is, its purpose in Funeral and Final Disposition applications, and provides detailed procedural steps for generating and using a VC-1 form.

```
Cross Programs > SSPS Payments > SSPS Benefits Procedures > Funeral and Final Disposition > Funeral and Final Disposition - Print the VC-1

If a Funeral and Final Disposition application requires verification, the Central Burial Unit must send out a VC-1. For instance, a VC-1 may request information about client assets or funeral expenses, or the contents of the bill from the funeral home.

To generate a VC-1, follow these steps in the Invoice page once the Invoice has been created:

1. go to the Invoice page
2. click the Add Event button
3. select Print VC-1 from the drop-down box.  The Event - Print VC-1  page will appear
4. in the Recipient field, select Vendor if the VC-1 will be sent to a funeral home; select Applicant if the VC-1 will go to the person submitting the application
5. enter verification information. The following fields are displayed for data entry:

  a. Other
  b. Value
  c. Verify
  d. Note : The Add Row function can be used to add additional verification requests to the VC-1. The Delete Row function can be used to remove verification requests.
6. it is optional to add additional free-form text in the Additional Text field
```

#### Rank 3 — PARTIAL (sim 0.270)

- **Chunk ID**: `sec__CrossProg__Verifications__Vers_VC1_FormsGenerated__004`
- **Section**: `` — 
- **Chunk position**: 5 / 5
- **Program**: Cross-Program
- **Judge reason**: The chunk mentions VC-1 and related forms but doesn't explain what VC-1 is or its purpose, only listing forms that generate with it.

```
Cross Programs > Verifications > Verification Checklist (VC-1) > Forms Generated with a VC-1

- Veterans Vendor Payments Form (VVPF): form generates with a Verification Element of Veterans Vendor Payments
- Voluntary Consent to Release Information (VARI-OI): form generates with a Verification Element of Release of Information
```

#### Rank 4 — RELEVANT (sim 0.237)

- **Chunk ID**: `sec__CrossProg__Verifications__Vers_VC1_Overview__006`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: The chunk directly addresses VC-1 (Verification Checklist) by explaining the process and requirements for printing a VC-1, including the hard edit that appears when unprocessed scanned documents exist.

```
Cross Programs > Verifications > Verification Checklist (VC-1) > VC-1 Overview > Attempting to Print a VC-1 When Unprocessed Scanned Documents Exist

Prior to sending a VC-1 or INT-2, you must first disposition any scanned or available documents on file. If you attempt to print a VC-1 or INT-2 when there are unprocessed scanned documents of any type (excluding Central Office scanned documents) associated with the case, a hard edit will be displayed which states the following:

“There is an Available/Reviewed scanned document(s) that must be properly dispositioned before you can request verifications. Be sure to review whether this document can satisfy an outstanding verification before sending a request.”

You must review and process according the scanned document(s) attached to the case before this hard edit will be removed. On the VC-1, each verification, such as identity or citizenship, displays a limited number of proofs as examples; however, you may view additional types of proofs by accessing the Verification tab.
```

#### Rank 5 — RELEVANT (sim 0.268)

- **Chunk ID**: `sec__CrossProg__SSPS__SSPS-Pymnts_FnrlFnlDisp_PrintVC-1__001`
- **Section**: `` — 
- **Chunk position**: 2 / 2
- **Program**: Cross-Program
- **Judge reason**: The chunk directly addresses VC-1 by providing detailed procedural instructions on how to print the VC-1 form in the DTA system.

```
Cross Programs > SSPS Payments > SSPS Benefits Procedures > Funeral and Final Disposition > Funeral and Final Disposition - Print the VC-1

7. it is optional to enter text in the Comment field.  Click the popup icon next to the Comment box to do so
8. select Local or Central from the drop-down list in the Location field
9. to preview the VC-1 before a Local print, click the Preview button.  A Centrally printed invoice may not be previewed
10. click the Print button.  A Print Confirmation message will appear “Do you wish to Print VC1?  Click on Yes to proceed with Printing.  Click on No to go back to the Print VC1 event.”
11. click Yes to print the VC-1, or No to go back to page without printing.  If printed either Locally or Centrally, the Invoice page will show the date and time of the printing in a summary section

Note : The Verifications Due Invoices view will display those invoices for which a VC-1 has been generated and sent because verifications are still outstanding. This view is found in the My Office tab by selecting Views, then selecting the Special Services Payment heading, then selecting Verifications Due Invoices.
```


### olg_023 — ESP exemptions (rank-1: PARTIAL)

**Question**: ESP exemptions  
**Program filter**: (none)  
**Notes**: ADVERSARIAL — acronym + topic. Tests retrieval on TAFDC ESP exemption list when query is terse. No filter to test raw retrieval.  
**Scores**: Relevant@5 = 0, Useful@5 = 5, rank-weighted = 1.35  

#### Rank 1 — PARTIAL (sim 0.380)

- **Chunk ID**: `sec__PandP__PNR-EX-ExemptionsPolAndProced__000`
- **Section**: `` — 
- **Program**: Policies & Procedures
- **Judge reason**: The chunk lists exemption-related regulations but doesn't specifically address ESP (Employment Services Program) exemptions or their details.

```
TAFDC > Program Nonfinancial Requirements > Exemptions > Exemptions Policy and Procedures > Regulations

| Chapter. Page | Title |
| --- | --- |
| 703.100 | Exemptions from Time-Limited Benefits and Reduced Need and Payment Standards |
| 703.190 | Disability Exemption Process |
| 703.210 | Dependent Child: Pregnancy |
```

#### Rank 2 — PARTIAL (sim 0.357)

- **Chunk ID**: `sec__PandP__PNR-EX-ExemptionsPolAndProced__002`
- **Section**: `` — 
- **Program**: Policies & Procedures
- **Judge reason**: The chunk lists exemptions-related hotline topics but doesn't provide specific information about ESP (Employment Services Program) exemptions.

```
TAFDC > Program Nonfinancial Requirements > Exemptions > Exemptions Policy and Procedures > Transitions

| Month, Year | Type | Title/Topic |
| --- | --- | --- |
| October 2009 | From the Hotline | Exemptions |
| May 2007 | From the Hotline | Exemptions: Essential to Care |
| December 2006 | From the Hotline | Caring for the Disabled |
| March 2005 | From the Hotline | Exemptions |
```

#### Rank 3 — PARTIAL (sim 0.365)

- **Chunk ID**: `sec__PandP__PNR-EX-ExemptionsPolAndProced__003`
- **Section**: `` — 
- **Program**: Policies & Procedures
- **Judge reason**: The chunk mentions exemptions and related forms but does not provide specific information about ESP (Employment Services Program) exemptions or their criteria.

```
TAFDC > Program Nonfinancial Requirements > Exemptions > Exemptions Policy and Procedures > Forms

| Number | Language | Title |
| --- | --- | --- |
| TAFDC-4 | English/Spanish | Verification of Disability |
| TAFDC-5 | English/Spanish | Exempt/Nonexempt Status Notice |
```

#### Rank 4 — PARTIAL (sim 0.359)

- **Chunk ID**: `sec__PandP__PNR-EX-ExemptionsPolAndProced__004`
- **Section**: `` — 
- **Program**: Policies & Procedures
- **Judge reason**: The chunk is about TAFDC exemptions but contains no actual content about ESP exemptions, only an empty table under 'Other' category.

```
TAFDC > Program Nonfinancial Requirements > Exemptions > Exemptions Policy and Procedures > Other

| Program | Description |
| --- | --- |
| None |  |
```

#### Rank 5 — PARTIAL (sim 0.324)

- **Chunk ID**: `sec__SNAP__WorkRules__WR_SNAPScreeningPg__036`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: The chunk discusses SNAP work rule exemptions but does not specifically address ESP (Employment Services Program) exemptions, which is what the user is asking about.

```
SNAP > SNAP Work Rules (General and ABAWD) > The SNAP Work Rules Screening Page > Exemption Examples

The table below provides examples of each exemption from the General and ABAWD Work Rules. Please note, some exemptions such as Waived Area, Under age 16 or over age 59 are not included on this examples list as these exemptions are based on BEACON data that cannot be changed by the client or worker.
```


### olg_024 — expedited timing (rank-1: RELEVANT)

**Question**: expedited 7 day  
**Program filter**: (none)  
**Notes**: ADVERSARIAL — terse numeric+concept. Should pull SNAP expedited pages despite minimal query. Tests dense retrieval on numeric tokens.  
**Scores**: Relevant@5 = 5, Useful@5 = 5, rank-weighted = 2.70  

#### Rank 1 — RELEVANT (sim 0.363)

- **Chunk ID**: `sec__SNAP__Noncitizen__ElgNC_CubanHatianSNAP__004`
- **Section**: `` — 
- **Chunk position**: 1 / 3
- **Program**: SNAP
- **Judge reason**: Directly addresses expedited 7-day SNAP benefits processing requirements, including the specific 7-day timeline and conditions for issuing expedited benefits.

```
SNAP > Eligibility Requirements > Noncitizen > Eligible Qualified Noncitizens > Cuban/Haitian Entrant - SNAP > Application Processing for Cuban/Haitian Entrants > Providing Expedited Benefits

If the client reports that their INS status is one of the eligible qualified noncitizen statuses, and there are pending outstanding mandatory verifications, but the client otherwise meets eligibility for expedited benefits, expedited benefits must be issued .

Lack of verification of immigration status must not delay expedited service during the 7-day expedited time frame. If the applicant meets the criteria for expedited benefits, appears eligible for SNAP benefits and provides proof of identity for the grantee by Day 7, you must issue expedited benefits by the 7th calendar day following the date of application.

Note : If verification of identity of the grantee has been provided, the case manager must issue an EBT card .

Examples Examples
```

#### Rank 2 — RELEVANT (sim 0.357)

- **Chunk ID**: `sec__SNAP__AppProcessing__AppSNAP_ExpeditedBenefits__010`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses expedited SNAP benefits processing with specific 7-day timeline requirements for scheduling interviews and authorizing benefit payments.

```
SNAP > Application Processing > SNAP Application Processing > Expedited Benefits > Automated Case Actions to Create Expedited SNAP Benefits

If an interview was not conducted/scheduled on a pending expedited SNAP case by day 2 from the application date, the Perform Cold Call Action Creation batch will schedule a phone interview appointment for the client on day 7 from the application date. If day 7 is not a working day, the appointment would be scheduled before day 7. The batch job will automatically enter a narrative for the action taken. However, no appointments will be automatically scheduled for a client who requires an American Sign Language interpreter or a home visit. Appointments for these clients must be made by a case manager or Client Assistance Coordinator (CAC).

A special batch job will automatically authorize an interview wrap-up calculation request for expedited SNAP benefits as soon as identity (SSN) information is verified and an interview is conducted on a pending Expedited SNAP case to release the expedited benefit payment. Once the verification of identity is set up to be verified, the system will automatically request verification of SSN from SVES. When the overnight inquiry of SSN is returned via SVES as verified, the system will automatically mark identity as verified on the verifications tab.
```

#### Rank 3 — RELEVANT (sim 0.346)

- **Chunk ID**: `sec__SNAP__AppProcessing__AppSNAP_ExpeditedBenefits__007`
- **Section**: `` — 
- **Program**: SNAP
- **Judge reason**: Directly addresses expedited 7-day SNAP benefits processing requirements and timelines for issuing expedited benefits within seven days.

```
SNAP > Application Processing > SNAP Application Processing > Expedited Benefits > Subsequent Discovery of Applicant Qualification for Expedited Benefits > Example #1

An applicant is interviewed, screened and determined to meet the criteria for receiving expedited service by Day 7. The applicant, however, does not provide identification by Day 7 (which, at a minimum would be providing their SSN for SVES electronic verification) but provides proof of identity at some later point during the 30-day pending period. You must process expedited benefits using subsequent discovery rules. The expedited benefits must be issued no later than seven days after the date the department discovers the household is entitled to expedited service, provided proof of identity has been verified. If the applicant does not complete the application process by Day 30, you must deny SNAP benefits on Day 30 in accordance with SNAP processing rules.
```

#### Rank 4 — RELEVANT (sim 0.415)

- **Chunk ID**: `sec__CrossProg__EBT__EBT_Overview__027`
- **Section**: `` — 
- **Program**: Cross-Program
- **Judge reason**: Directly explains the 7-day expedited SNAP benefits requirement, including what 'opportunity to participate' means and the specific timeline for EBT card, PIN, and benefit deposit.

```
Cross Programs > EBT > Overview - Electronic Benefit Transfer (EBT) > EBT Cards and Expedited SNAP Benefits

A SNAP applicant eligible for expedited SNAP benefits must be given an opportunity to participate within seven calendar days following the date of application. Opportunity to participate means that the applicant must have: (a) an EBT card, (b) a PIN and (c) SNAP benefits deposited into the EBT account no later than the seventh calendar day after the application filing date.
```

#### Rank 5 — RELEVANT (sim 0.350)

- **Chunk ID**: `sec__EAEDC__Gen_NonFinancial_Req__NonC_CubanHatian__004`
- **Section**: `` — 
- **Chunk position**: 1 / 4
- **Program**: EAEDC
- **Judge reason**: Directly addresses expedited 7-day benefits processing requirements for EAEDC applicants, including specific timelines and conditions for issuing expedited benefits within the 7-day window.

```
EAEDC > General Nonfinancial Requirements > Noncitizen > Eligible Qualified Noncitizens > Cuban/Haitian Entrant > Application Processing for Cuban/Haitian Entrants > Providing Expedited Benefits

If the EAEDC applicant has applied for SNAP and reports that their immigration status is one of the eligible qualified noncitizen statuses, and there are pending outstanding mandatory verifications, but the client otherwise meets eligibility for expedited benefits, expedited benefits must be issued .

Lack of verification of immigration status must not delay expedited service during the 7-day expedited time frame. If the applicant meets the criteria for expedited benefits, appears eligible for SNAP benefits and provides proof of identity for the grantee by Day 7, you must issue expedited benefits by the 7th calendar day following the date of application.

Note : If verification of identity of the grantee has been provided, the case manager must issue an EBT card .

Examples Examples
```

