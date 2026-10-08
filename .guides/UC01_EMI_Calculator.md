# UC-01 — Loan EMI Calculator

**Day 1 · Module: Foundations · Slot: 2 hrs · Demo: 20 min**

## Goal
Show that **clear requirements give better AI code**, and where a human must review in an AI-assisted project.

## Time plan (120 min)
| Time | Activity |
|---|---|
| 0–55 min | Concepts (SDLC vs AI-SDLC, assisted vs agentic, human-in-the-loop, vibe coding vs spec-driven) |
| 55–75 min | Demo (20 min) |
| 75–110 min | Hands-on |
| 110–120 min | Discussion |

## Before the session
- Open an empty Python project in VS Code (`uv init emi-calculator`).
- Open Copilot Chat.

---

## Demo

### Part 1 — Vague prompt (5 min)
In Copilot Chat (Agent mode), type:
```text
Write a Python function to calculate loan EMI.
```
Ask the class: *"Would you put this in the bank's web app?"* Look for these problems:
- Uses `float` for money (small rounding errors)
- No rounding to 2 decimals
- Crashes with `ZeroDivisionError` when the interest rate is 0
- No check for negative amount or tenure

### Part 2 — Clear prompt (8 min)
Undo the change. Now type:
```text
Write a Python class EmiCalculator with method calculate_emi(principal, annual_rate_percent, tenure_months).

Rules:
- Use Decimal for money. Round the EMI to 2 decimals (ROUND_HALF_UP).
- Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1), where r = annual rate / 12 / 100.
- If the rate is 0, EMI = principal / months.
- Principal must be between 10,000 and 50,00,000. Tenure between 6 and 84 months.
  Otherwise raise ValueError with a clear message.

Also write pytest tests:
- 5,00,000 at 12% for 36 months = 16607.15
- 1,00,000 at 0% for 12 months = 8333.33
- 5,000 should be rejected
```
Run the tests (`uv run pytest`). Point out: **same AI, same developer — only the instructions changed.**

### Part 3 — Where does a human review? (7 min)
```text
We are adding an EMI calculator to a bank's web app.
List the steps from requirement to production: Requirement, Design, Code, Test, Release, Monitor.
For each step, say what AI can do and where a person must review or approve.
Show it as a simple table.
```
Discuss: Which review would you **never** skip? (e.g., checking the EMI formula, approving the production release.)

---

## Hands-on (35 min)
In pairs, pick one simple bank feature:
- FD interest calculator
- Credit card bill due-date reminder
- ATM withdrawal limit check

1. Try a vague prompt, then a clear prompt with rules. Note the differences.
2. Make a table: Requirement → Design → Code → Test → Release. For each step write what AI does and where a person reviews.

## Discussion questions
- What went wrong with the vague prompt?
- Where did you put human reviews, and why?
