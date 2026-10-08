# UC-07 — Fund Transfer API: raise a PR and get it reviewed

**Day 4 · Module: GitHub Copilot (part 2) · Slot: 2 hrs · Demo: 25 min**

## Goal

Build the REST API from Spec Kit tasks, use Copilot to understand old code, and take the change through a **pull request with Copilot code review and a teammate's approval**. Also show how to keep sensitive files away from Copilot.

## Time plan (120 min)

| Time        | Activity                                                                              |
| ----------- | ------------------------------------------------------------------------------------- |
| 0–45 min    | Concepts (using Spec Kit with Copilot, understanding old code, PR review, guardrails) |
| 45–70 min   | Demo (25 min)                                                                         |
| 70–110 min  | Hands-on (Stage 3)                                                                    |
| 110–120 min | Discussion                                                                            |

## Before the session

- `simple-bank` with the TransferService from UC-06.
- Add the old interest code below as `legacy/savings_interest.py` (it's also used in UC-09).

```python
class SavingsInterest:
    # calculates monthly interest for savings account
    def calc(self, bal, acc_type):
        r = 0
        if acc_type.upper() == "S":
            r = 3.5
        elif acc_type.upper() == "SC":
            r = 4.0
        elif acc_type.upper() == "STAFF":
            r = 4.5
        i = bal * r / 100 / 12
        if bal < 1000:
            i = 0
        return round(i, 2)
```

---

## Demo

### Step 1 — Build the API from Spec Kit tasks (8 min)

```text
/speckit.implement Implement only the REST API tasks: the POST /api/v1/transfers endpoint,
request validation, and error responses using the existing TransferService.
```

Show `tasks.md` — completed tasks get ticked `[X]`.

> If it runs long, stop after 6 minutes and switch to your `uc07-done` branch.

### Step 2 — Understand old code (5 min)

Open `legacy/savings_interest.py`. In Copilot Chat (Ask mode):

```text
Explain #file:legacy/savings_interest.py in simple words.
List every business rule in it (rates, conditions) and any problems you see.
```

Expected points: rates 3.5% / 4% / 4.5%, no interest below Rs 1,000, uses `float`, unclear names like "S" and "SC", crashes if `acc_type` is None.

Then:

```text
Write pytest tests that capture what this code does today, without changing it.
```

Note to Trainees: _"Before changing old code, we lock in its current behaviour with tests."_

### Step 3 — Pull request with Copilot review (8 min)

```bash
git checkout -b feature/fund-transfer-api
git add -A
git commit -m "Add fund transfer API"
git push -u origin feature/fund-transfer-api
```

On GitHub:

1. Open a pull request.
2. Under **Reviewers**, choose **Copilot**.
3. When comments arrive, decide for each one:
   - **Accept** — apply the suggestion
   - **Later** — create an issue
   - **Reject** — reply with the reason
4. A teammate reviews and approves. Then merge.

Note to Trainees: _"Copilot's review helps, but it does not count as an approval. A person must approve."_

### Step 4 — Keep sensitive files away from Copilot (4 min)

Go to **Repo Settings → Copilot → Content exclusion** and add:

```yaml
- "/config/application-prod.yml"
- "**/*.pem"
```

Open the excluded file — Copilot won't use it.
Also mention:

- **Public code filter** — the organisation can block suggestions that match public code.
- **Organisation policies** — admins decide which Copilot features and models are allowed.

> Note: exclusions may not apply to every Copilot mode — check GitHub's current docs. Never keep real passwords in the repo anyway.

---

## Hands-on (40 min) — Stage 3

On your own feature from UC-06:

1. Push a branch and open a pull request.
2. Add **Copilot** as a reviewer.
3. For each Copilot comment: Accept / Later / Reject (write why).
4. A teammate reviews and approves. Merge.

## Discussion questions

- How many of Copilot's comments were useful?
- What did your teammate catch that Copilot missed?
