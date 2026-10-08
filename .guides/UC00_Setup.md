# Setup — Read Before Day 1

> **Python edition with a React front-end.** Services use **Python 3.12** with **FastAPI**; the web UI uses **React (Vite)**.

## The demo web app: "Simple Bank"
All use cases use one small, made-up banking web app called **Simple Bank**. Most of the course builds one feature step by step: **Fund Transfer between two accounts**.

| Day | Use case | Runbook |
|---|---|---|
| 1 | Loan EMI Calculator | UC01_EMI_Calculator.md |
| 1 | Fund Transfer — write the spec | UC02_Fund_Transfer_Spec.md |
| 2 | Fund Transfer — Spec Kit step by step | UC03_Fund_Transfer_SpecKit.md |
| 2 | Mini Account Statement with 3 agents | UC04_Mini_Statement_Agents.md |
| 3 | Minimum Balance Check with Copilot coding agent | UC05_Minimum_Balance_Coding_Agent.md |
| 3 | Build the Fund Transfer service with Copilot | UC06_Build_Fund_Transfer.md |
| 4 | Fund Transfer API — PR and review | UC07_Fund_Transfer_PR_Review.md |
| 4 | Fund Transfer web UI with React | UC08_Fund_Transfer_Web_UI_React.md |
| 5 | Old Savings Interest Calculator — assess | UC09_Old_Interest_App_Assessment.md |
| 5 | Deploy Fund Transfer API to AWS | UC10_Deploy_to_AWS.md |
| 6 | Review an AI-written Customer Search API | UC11_Review_AI_Code.md |
| 6 | Case studies: modernize + FD Maturity Calculator | UC12_Case_Studies.md |

## Install once (trainer laptop)
- VS Code + GitHub Copilot and Copilot Chat extensions (signed in with a Copilot Business/Enterprise licence).
- Python 3.12 and `uv` (the runbooks use Python / FastAPI; if your batch uses Java or .NET, ask Copilot for the same thing in that language).
- Node.js 20+ and npm (for the React web UI on Day 4).
- Spec Kit:
  ```bash
  uv tool install specify-cli
  specify --help
  ```
- Docker Desktop, Git, and (for Day 5) AWS CLI and Semgrep (`pip install semgrep`).

## GitHub repo
- Create a repo `simple-bank` in an organisation that has Copilot Business/Enterprise.
- Turn on: Copilot coding agent, Copilot code review, GitHub Actions, code scanning (CodeQL).
- This repository includes [.github/copilot-instructions.md](../.github/copilot-instructions.md), which gives Copilot repository context and coding guidance. Copilot Chat uses it automatically when working in this repository.
- For the React UI (Day 4), create a second repo `simple-bank-web`, or use a `web/` folder inside `simple-bank` — either works.

## About Spec Kit commands
Depending on your Spec Kit version, the commands look like `/speckit.specify` **or** `/speckit-specify`. In Copilot Chat just type `/speckit` and pick from the list.

## Tips for smooth demos
- **Rehearse each demo once** the day before.
- After rehearsing, save the finished code in a branch like `uc06-done`. If a live demo goes wrong, switch to that branch and carry on.
- AI output changes a little each time. That's fine — explain what you see.
