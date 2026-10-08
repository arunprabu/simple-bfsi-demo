# UC-03 — Fund Transfer: Spec Kit step by step

**Day 2 · Module: Spec-Driven Development (part 2) · Slot: 2 hrs · Demo: 25 min**

## Goal

Run the full Spec Kit flow — **Constitution → Specify → Plan → Tasks** — and show how to update a spec when the requirement changes.

## Time plan (120 min)

| Time        | Activity                                                                         |
| ----------- | -------------------------------------------------------------------------------- |
| 0–40 min    | Concepts (Specify CLI, the Spec Kit flow, team review, new vs existing projects) |
| 40–65 min   | Demo (25 min)                                                                    |
| 65–110 min  | Hands-on                                                                         |
| 110–120 min | Discussion                                                                       |

## Before the session

Use the `simple-bank` project from UC-02 (constitution + Fund Transfer spec are ready).

---

## Demo

### Step 1 — Look at the folders (2 min)

Show:

- `.specify/memory/constitution.md` — project rules
- `specs/001-.../spec.md` — the Fund Transfer spec

Note to Trainees: _"Everything is plain text in the repo, so it can be reviewed like code."_

### Step 2 — Plan: how we will build it (8 min)

```text
/speckit.plan Use Python 3.12 with uv, FastAPI, and SQLite for now.
Keep the transfer rules in a separate service class so they are easy to unit test.
Expose a REST API under /api/v1.
```

Open the files it creates and show:
| File | What it has |
|---|---|
| `plan.md` | Technical approach; check that it follows the constitution |
| `data-model.md` | Account and Transaction |
| `contracts/` | API definition for POST /api/v1/transfers |

### Step 3 — Tasks: small steps to build (5 min)

```text
/speckit.tasks
```

Open `tasks.md`. Point out:

- Tasks are in order
- Tests come before code
- Tasks marked `[P]` can be done in parallel

Quick team review:

```text
Look at #file:specs/001-fund-transfer/tasks.md . Are any tasks too big for one pull request?
Split them. Are any rules from the spec missing a task?
```

(Use the actual folder name Spec Kit created.)

### Step 4 — The requirement changes (8 min)

Read this out: _"New rule from the business: accounts less than 30 days old can transfer only Rs 50,000 per day."_

```text
/speckit.specify Update the Fund Transfer feature (specs/001): accounts opened less than 30 days ago
have a daily transfer limit of Rs 50,000. All other accounts keep the Rs 1,00,000 limit.
Add acceptance criteria and examples for this rule.
```

Then check if everything still matches:

```text
/speckit.analyze
```

Note to Trainees: _"Analyze only reports problems — for example, the data model has no 'account opened date'. A person decides the fix."_

### Step 5 — Save (2 min)

```bash
git add -A
git commit -m "Fund transfer: plan, tasks, new-account limit"
```

---

## Hands-on (45 min)

Use the spec you wrote in UC-02:

1. Run `/speckit.plan` (use your team's language/framework).
2. Run `/speckit.tasks` and review the task list as a team.
3. The trainer gives each team a change (e.g., "senior citizens get +0.25% extra on FD", "ATM limit is Rs 10,000 at night"). Update the spec and run `/speckit.analyze`.

## Discussion questions

- What did `/speckit.analyze` find after the change?
- Which task would you not give to AI without careful review?
