# UC-04 — Mini Account Statement with 3 agents

**Day 2 · Module: Agentic AI (part 1) · Slot: 2 hrs · Demo: 25 min**

## Goal

Show the **Planner → Coder → Reviewer** pattern using three simple Copilot custom agents. The Reviewer checks a banking rule: **account numbers must be masked**.

## Time plan (120 min)

| Time        | Activity                                                                                       |
| ----------- | ---------------------------------------------------------------------------------------------- |
| 0–50 min    | Concepts (agent vs assistant, what an agent has: planning, tools, memory, review; agent roles) |
| 50–75 min   | Demo (25 min)                                                                                  |
| 75–110 min  | Hands-on (paper design)                                                                        |
| 110–120 min | Discussion                                                                                     |

## Before the session

Create these three files in the `simple-bank` repo (don't type them live — it takes too long).

> If the tool names don't match your VS Code version, open the agent and use **Configure Tools** to pick similar tools. What matters: Planner and Reviewer can only read; Coder can edit.

**`.github/agents/planner.agent.md`**

```markdown
---
name: planner
description: Makes a step-by-step plan. Does not change code.
tools: ["search", "usages"]
handoffs:
  - label: Send to Coder
    agent: coder
    prompt: Build the plan above. Do not add anything extra.
    send: false
---

You are the Planner for Simple Bank.
Do not edit any files. Read the code and the request, then give:

1. A numbered list of steps (which files to create or change)
2. Test cases in Given/When/Then format
3. Questions for the developer, if any
```

**`.github/agents/coder.agent.md`**

```markdown
---
name: coder
description: Writes code and tests for an approved plan.
tools: ["search", "edit", "runCommands"]
handoffs:
  - label: Send to Reviewer
    agent: reviewer
    prompt: Review the code just written.
    send: false
---

You are the Coder. Follow the plan exactly.
Write tests first, then code. Use Python 3.12 and Decimal for money, with pytest tests.
At the end, list the files you changed.
```

**`.github/agents/reviewer.agent.md`**

```markdown
---
name: reviewer
description: Reviews code. Does not change code.
tools: ["search", "changes"]
handoffs:
  - label: Send fixes to Coder
    agent: coder
    prompt: Fix the problems listed in the review. Do not change anything else.
    send: false
---

You are the Reviewer. Do not edit files. Check the code for:

1. Account numbers must be masked in responses and logs (show only last 4 digits, e.g. XXXX1234).
2. Money must use Decimal.
3. Every rule must have a test.
4. No passwords or secrets in code.
   Give a table: Problem | File | Severity (High/Medium/Low) | Fix.
   End with APPROVED or CHANGES NEEDED.
```

---

## Demo

### Step 1 — Explain the three agents (3 min)

Open the three files. Explain:

- Planner and Reviewer **cannot edit** code.
- `handoffs` add a button to pass work to the next agent.
- `send: false` means **a person must click send** — this is the human check.

### Step 2 — Planner (6 min)

Choose **planner** in the Copilot Chat agent list and type:

```text
Feature: Mini Statement.
GET /api/v1/accounts/{account_number}/mini-statement returns the last 10 transactions
(date, description, debit/credit, amount, balance after), newest first.
The account number in the response must be masked, e.g. XXXX1234.
```

Read the plan with the class. Add one thing before approving, e.g., _"Also test an account with no transactions."_

### Step 3 — Coder (8 min)

Click **Send to Coder**. Add your extra line to the pre-filled message and send.
Point out: tests written first, commands it asks you to approve.

> If it takes too long, stop and switch to your `uc04-done` branch.

### Step 4 — Reviewer (6 min)

Click **Send to Reviewer** and send.
If the code is already perfect, add a mistake yourself so the Reviewer has something to find — for example, return the full account number in the response. Run the Reviewer again.

### Step 5 — Fix loop (2 min)

Click **Send fixes to Coder**. Then review again until you see **APPROVED**.
Note to Trainees: _"The agent says APPROVED, but a person still decides to merge."_

---

## Hands-on (35 min) — on paper

In teams, pick one feature:

- Cheque book request
- Change mobile number (with OTP)
- Download last 3 months' statement as PDF

Fill in this table:

| Agent    | What it gets | What it gives back | Can it edit code? | Who checks its work? |
| -------- | ------------ | ------------------ | ----------------- | -------------------- |
| Planner  |              |                    |                   |                      |
| Coder    |              |                    |                   |                      |
| Tester   |              |                    |                   |                      |
| Reviewer |              |                    |                   |                      |

Then draw arrows showing the flow, including when the Reviewer sends work back.

## Discussion questions

- Why shouldn't the Reviewer be allowed to edit code?
- How many times should the Reviewer and Coder go back and forth before a person steps in?
