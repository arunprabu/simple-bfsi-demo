# UC-02 — Fund Transfer between two accounts: write the spec

**Day 1 · Module: Spec-Driven Development (part 1) · Slot: 2 hrs · Demo: 25 min**

## Goal

Turn a short requirement note into a clear spec that both people and AI can follow. This spec is used again on Days 2–4.

## Time plan (120 min)

| Time        | Activity                                                |
| ----------- | ------------------------------------------------------- |
| 0–45 min    | Concepts (why spec-driven, BRD → spec, parts of a spec) |
| 45–70 min   | Demo (25 min)                                           |
| 70–110 min  | Hands-on                                                |
| 110–120 min | Discussion                                              |

## Before the session

```bash
specify init simple-bank --integration copilot     # older versions: --ai copilot
cd simple-bank
code .
```

Create `docs/requirement-fund-transfer.md` with this text:

```markdown
# Requirement: Fund Transfer (Simple Bank)

Customers should be able to transfer money from their savings account to another
Simple Bank account using the bank's web app.

Rules:

1. Amount must be more than Rs 0.
2. The sender must have enough balance.
3. A customer can transfer at most Rs 1,00,000 per day.
4. A customer cannot transfer to the same account.
5. Both accounts must be active.
6. Every transfer gets a unique transaction ID and is saved.
7. The customer should get a quick response.
```

> Rule 7 is vague on purpose — Spec Kit will ask about it.

---

## Demo

### Step 1 — Basic project rules (3 min)

```text
/speckit.constitution Simple Bank project rules:
1. Use Decimal for all money. Round to 2 decimals.
2. Never log full account numbers. Show only the last 4 digits (XXXX1234).
3. Every rule must have a test.
4. APIs start with /api/v1.
5. The customer web app is React (Vite) and calls only the /api/v1 API.
```

Note to Trainees: _"These are the rules every feature must follow."_

### Step 2 — Create the spec (8 min)

```text
/speckit.specify Build the Fund Transfer feature described in #file:docs/requirement-fund-transfer.md .
Write user stories, a numbered list of requirements, and acceptance criteria in Given/When/Then format
for every rule. If something is not clear, mark it [NEEDS CLARIFICATION].
```

Open the new `specs/001-.../spec.md` and show:

- User stories
- Requirements list
- Acceptance criteria (Given/When/Then)
- `[NEEDS CLARIFICATION]` items

### Step 3 — Answer the unclear points (7 min)

```text
/speckit.clarify
```

Answer the questions. Suggested answers:
| Question | Answer |
|---|---|
| What is a "quick" response? | Within 1 second |
| Does the daily limit reset at midnight? | Yes, at 12:00 AM IST |
| What if the transfer fails halfway? | Nothing is debited; show an error |
| Is there a minimum amount? | Rs 1 |

Note to Trainees: _"Now every developer and every AI tool gets the same answer."_

### Step 4 — Add API and data (7 min)

```text
Add two sections to the spec:
1. API: POST /api/v1/transfers — request fields, response fields, and error codes
   (INSUFFICIENT_BALANCE, DAILY_LIMIT_EXCEEDED, SAME_ACCOUNT, ACCOUNT_INACTIVE, INVALID_AMOUNT).
2. Data: Account (account_number, customer_id, balance, status) and Transaction
   (transaction_id, from_account, to_account, amount, status, created_at).
3. Examples table: 5 sample transfers with the expected result.
```

Check one example with the class — does it follow the rules?

---

## Hands-on (40 min)

In pairs, write a spec for one of these:

- **ATM withdrawal**: max Rs 25,000 per day, only in multiples of Rs 100, enough balance needed
- **Add beneficiary**: IFSC must be 11 characters, cannot add the same beneficiary twice
- **FD booking**: minimum Rs 5,000, 6 to 120 months, senior citizens get +0.5% interest

Steps: `/speckit.specify` → `/speckit.clarify` → add examples → swap with another pair and find one unclear requirement.

## Discussion questions

- How many things were unclear in the requirement?
- Which unclear point could have caused a bug?
