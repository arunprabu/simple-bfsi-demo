# UC-12 — Case Studies: modernize the Interest Calculator + build an FD Maturity Calculator

**Day 6 · Module: Connected Case Studies · Slot: 4 hrs · Trainer demo: 15 min per case study**

## Goal

Teams use everything from the course on two small projects in the same bank:

- **Case Study 1 (modernize):** turn the old Savings Interest Calculator into a new REST service that gives the **same results**.
- **Case Study 2 (new build):** build a new **FD Maturity Calculator** service.

## Time plan (240 min)

| Time        | Activity                                     |
| ----------- | -------------------------------------------- |
| 0–10 min    | Briefing: teams, deliverables, review points |
| 10–25 min   | Demo: Case Study 1 start (15 min)            |
| 25–110 min  | Teams work on Case Study 1                   |
| 110–120 min | Break                                        |
| 120–135 min | Demo: Case Study 2 start (15 min)            |
| 135–215 min | Teams work on Case Study 2                   |
| 215–240 min | Team presentations (3 min each) + wrap-up    |

## Team roles

- **Spec owner** — writes and clarifies the spec
- **Driver** — uses Copilot
- **Reviewer** — checks code and tests
- **Note-taker** — keeps the review record

## Review points (from the UC-11 checklist)

| Point                     | When                      | Who approves |
| ------------------------- | ------------------------- | ------------ |
| RP1 Spec approved         | After the spec is written | Trainer      |
| RP2 Pull request approved | Before merge              | Another team |
| RP3 Results checked       | Before presenting         | Trainer      |

---

# Case Study 1 — Modernize the Savings Interest Calculator

**Starting point:** the old app and modernization spec from UC-09.

### Rules (from the old code)

| Account type        | Interest rate (per year) |
| ------------------- | ------------------------ |
| S (regular)         | 3.5%                     |
| SC (senior citizen) | 4.0%                     |
| STAFF               | 4.5%                     |

- Monthly interest = balance × rate / 100 / 12, rounded to 2 decimals.
- No interest if balance is below Rs 1,000.
- New: unknown or empty account type returns an error (the old code crashed).

### Trainer demo (15 min)

**Step 1 — Plan and tasks (4 min)**

```text
/speckit.plan Python 3.12, FastAPI. One REST endpoint POST /api/v1/interest/calculate.
Keep the calculation in a separate InterestCalculator class using Decimal.
```

```text
/speckit.tasks
```

**Step 2 — Compare old and new results (6 min)**

```text
Create a pytest test that checks the new InterestCalculator gives the same result as the old
SavingsInterest.calc for these inputs:
(50000, S), (50000, SC), (50000, STAFF), (999, S), (1000, S), (123456.78, SC), (0, S).
Print a table: input | old result | new result | match?
```

Expected results to check:
| Balance | Type | Monthly interest |
|---|---|---|
| 50,000 | S | 145.83 |
| 50,000 | SC | 166.67 |
| 50,000 | STAFF | 187.50 |
| 999 | S | 0.00 |
| 1,000 | S | 2.92 |

**Step 3 — Build it (5 min)**

```text
/speckit.implement Implement the InterestCalculator and the REST endpoint. Run the comparison test.
```

### Team steps (85 min)

1. Review and improve the spec from UC-09 → **RP1**
2. Run `/speckit.plan` and `/speckit.tasks`
3. Write the old-vs-new comparison test **first**
4. Build the calculator and the REST endpoint with `/speckit.implement`
5. Run Semgrep; open a PR; get Copilot review → another team approves → **RP2**
6. Write a short report (half a page): what you changed, what stayed the same, any problems left → **RP3**

Report prompt:

```text
Write a short report (half a page) on modernizing the savings interest calculator:
what we built, how we checked the results match the old code, what we changed on purpose,
and any open issues.
```

---

# Case Study 2 — New FD Maturity Calculator service

### Requirement card (give to teams)

> Customers want to see how much they will get when their Fixed Deposit matures.
>
> - Amount: Rs 5,000 to Rs 1,00,00,000
> - Tenure: 6 to 120 months
> - Interest rate: 7.0% per year. Senior citizens (60+) get 7.5%.
> - Interest is compounded every 3 months (quarterly).
> - Maturity amount = P × (1 + r/4)^(4 × years), rounded to 2 decimals.
> - Return: principal, rate used, interest earned, maturity amount.

### Trainer demo (15 min)

**Step 1 — Spec (5 min)**

```text
/speckit.specify FD Maturity Calculator service for Simple Bank. <paste the requirement card>
Include error codes INVALID_AMOUNT and INVALID_TENURE, and an examples table.
```

Check the examples with the class:
| Amount | Tenure | Senior? | Rate | Maturity amount |
|---|---|---|---|---|
| 1,00,000 | 12 months | No | 7.0% | 1,07,185.90 |
| 1,00,000 | 12 months | Yes | 7.5% | 1,07,713.59 |
| 1,000 | 12 months | No | — | Error: INVALID_AMOUNT |

Note to Trainees: _"Always check AI-calculated numbers by hand — they become our test data."_

**Step 2 — API and first test (10 min)**

```text
/speckit.plan Python 3.12, FastAPI. Endpoint POST /api/v1/fd/maturity. Use Decimal.
```

```text
Write a failing pytest test: Rs 1,00,000 for 12 months, not senior citizen, expects maturity amount 107185.90.
Do not write the service yet.
```

Note to Trainees: _"The test is red now. Your job is to make it green."_

### Team steps (80 min)

1. Write the spec, run `/speckit.clarify`, check the examples by hand → **RP1**
2. Run `/speckit.plan` and `/speckit.tasks`
3. Build the service with `/speckit.implement`; get 1–2 tests passing
4. Open a PR, get Copilot review, another team approves → **RP2**
5. Fill the review record below → **RP3**
6. (Optional) Add a small React page for the calculator, reusing the UC-08 pattern, and include it in the PR.

### Review record (copy into `review-record.md`)

```markdown
# Review Record — FD Maturity Calculator (Team \_\_\_)

| Check                                     | Done? | Who checked | Notes |
| ----------------------------------------- | ----- | ----------- | ----- |
| Spec approved by trainer                  |       |             |       |
| Examples checked by hand                  |       |             |       |
| Tests pass                                |       |             |       |
| Copilot review comments handled           |       |             |       |
| Semgrep scan clean                        |       |             |       |
| No sensitive data in logs                 |       |             |       |
| Approved by another team (not the author) |       |             |       |
```

---

## Team presentations (3 min each)

Each team answers:

1. Did the new interest service match the old one?
2. What did Copilot get wrong, and how did you catch it?
3. Which review point was most useful?

**Trainer wrap-up:** go back to the Day 1 EMI demo — _"Same AI all week. What made the code better was a clear spec, good context, and people reviewing at the right points."_
