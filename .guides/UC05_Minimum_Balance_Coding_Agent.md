# UC-05 — Minimum Balance Check with the Copilot coding agent

**Day 3 · Module: Agentic AI (part 2) · Slot: 2 hrs · Demo: 25 min**

## Goal

Give a GitHub issue to the **Copilot coding agent**, let it open a pull request, and show the **human approval steps** before anything is merged. Also discuss which bank tasks are OK for an agent.

## Time plan (120 min)

| Time        | Activity                                                                                      |
| ----------- | --------------------------------------------------------------------------------------------- |
| 0–3 min     | **Start the coding agent first** (Step 1) — it works in the background                        |
| 3–45 min    | Concepts (what agents pass to each other, human approvals, when to use agents, AWS Transform) |
| 45–70 min   | Demo (25 min)                                                                                 |
| 70–110 min  | Hands-on                                                                                      |
| 110–120 min | Discussion                                                                                    |

## Before the session

- Copilot coding agent is turned on for `simple-bank`.
- Branch protection on `main`: at least 1 approval needed before merge.
- A simple GitHub Actions workflow that runs `uv run pytest`.
- Rehearse once — the agent usually takes 10–20 minutes.

---

## Demo

### Step 1 — Create the issue and assign it (at the start, 3 min)

Create a GitHub issue:

**Title:** `Block withdrawal if balance goes below Rs 1,000`

**Description:**

```markdown
Savings accounts must keep a minimum balance of Rs 1,000.

Rules:

- A withdrawal or transfer is rejected if the balance after it would be less than Rs 1,000.
- Error code: MIN_BALANCE_REQUIRED.
- The minimum balance amount must come from configuration, not hard-coded.

Tests needed:

- Balance 5,000, withdraw 4,000 -> allowed (balance 1,000)
- Balance 5,000, withdraw 4,001 -> rejected
- Balance 1,000, withdraw 1 -> rejected

Use Decimal. Do not change files in .github/.
```

Assign the issue to **Copilot**. Show that it reacts and opens a draft pull request.

### Step 2 — Check the pull request (10 min)

After the concepts part, open the pull request:

1. **Session log** — click "View session" to see what the agent did step by step.
2. **Run checks** — the tests don't run until a person clicks **Approve and run workflows**. Click it.
   Note to Trainees: _"The agent can't even run the pipeline without a human."_
3. **Review the code** — check the three test cases from the issue. If something is missing, comment:
   ```text
   @copilot Please add a test where the balance is exactly Rs 1,000 and the withdrawal is Rs 0.01. It should be rejected.
   ```
   Show that the agent reads the comment and pushes a new commit.
4. **Merge** — only a person can approve and merge.

> If the agent hasn't finished, show the pull request from your rehearsal.

### Step 3 — Agent or not? (7 min)

In Copilot Chat (Ask mode):

```text
For each bank task below, say if it is good for an AI agent to do on its own,
if a developer should do it with AI help, or if a person should do it.
Give a one-line reason. Show a table.
1. Add unit tests for the EMI calculator
2. Change the interest rate used for all fixed deposits
3. Upgrade a library version in 5 services
4. Add a new fraud rule for large UPI payments
5. Fix spelling mistakes in API error messages
6. Delete old customer records
7. Add the minimum balance check
```

Discuss the answers. Point out that the minimum balance **rule** was written by a person — the agent only wrote the code.

### Step 4 — AWS Transform (5 min, slides or screenshots)

Explain in simple words: AWS Transform uses AI agents to help move old applications (like mainframe COBOL) to modern code. It:

1. Reads the old code
2. Writes documentation
3. Suggests how to split the app
4. Converts the code
   Each step still needs a person to check the result.

---

## Hands-on (40 min)

Use the paper design from UC-04:

1. For each agent step, write **what it receives** and **what it gives back**.
2. Mark every place a person must approve, and how (click a button, review a PR, sign off).
3. Mark each step as: agent can do alone / developer with AI / person only.

## Discussion questions

- Which approval steps did GitHub enforce automatically?
- What would you never let an agent merge on its own?
