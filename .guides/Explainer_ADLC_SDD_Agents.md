# Explainer — ADLC, SDD, Agents, and Skills

A one-page glossary of the terms used across this course, and how they fit together.

---

## 1. ADLC — AI-Driven Development Life Cycle

**ADLC** is the classic SDLC (plan → design → build → test → review → deploy) where **AI agents do much of the work** and humans set direction, review, and approve.

| SDLC (classic) | ADLC (AI-driven) |
|---|---|
| Humans write specs, code, tests | Humans write specs; agents generate plans, code, tests |
| Code is the main artifact | **Specs and plans** are the main artifacts; code is generated |
| Review the code | Review the spec, then review/verify the code |
| Manual docs | Specs, plans, tasks live in the repo as markdown |

Key idea: **the specification becomes the source of truth**, not the code.

---

## 2. Spec Driven Development (SDD)

SDD is the *method* used inside the ADLC. Instead of "prompt and hope", you write a structured spec first, and the agent works from it.

Typical loop:

1. **Constitution / rules** — project-wide standards (tech stack, testing, security).
2. **Specify** — what to build, in business language (no code). *What & why.*
3. **Plan** — technical approach, data models, API contracts. *How.*
4. **Tasks** — small, ordered, testable work items.
5. **Implement** — the agent writes code task by task.
6. **Change** — update the spec, and the plan/tasks/code are regenerated or amended.

Why it works:
- Specs are small enough for a human to review; code review at scale is not.
- Requirements, decisions, and tests stay traceable ("which task implements rule #7?").
- Re-running the flow after a requirement change is cheap.

---

## 3. AI Agents

An **AI agent** is an LLM that can *take actions*, not just chat. The pattern is:

```
Goal → Reason → Use tools (read files, run commands, call APIs) → Observe → Repeat until done
```

- **Chatbot:** answers a question.
- **Agent:** does the task — edits files, runs tests, opens a PR — and checks its own work.

Agents rely on **context** (the repo, specs, rules) and **tools** (terminal, browser, git, MCP servers).

---

## 4. Coding Agents

Coding agents are AI agents specialised for software work: reading a codebase, writing/editing code, running builds and tests, and using git.

| Agent | Form factor | Notes |
|---|---|---|
| **Claude Code** | Terminal (CLI) | Agentic coding in the terminal; strong at multi-step repo tasks |
| **GitHub Copilot** | GUI (IDE) and TUI | Autocomplete + chat + agent mode; IDE and terminal variants |
| **Cursor** | GUI (IDE) | VS Code-based editor with agent mode |
| **opencode** | Terminal (CLI) | Open-source terminal agent |
| **Cline** | VS Code extension | Open-source agent with plan/act modes |
| **Kiro** | GUI (IDE) | Spec-driven IDE (specs → tasks → code) |
| **Antigravity** | GUI (IDE) | Google's agent-first IDE |
| _…and more_ | | The category moves fast; pick per workflow, not per hype |

How to choose, in practice:
- **CLI agents** fit automation, scripting, and headless/CI use.
- **IDE agents** fit interactive, visual, day-to-day development.
- What matters more than the tool: a good spec, clear rules, and small reviewable changes.

---

## 5. SDD Tools (Spec-Driven Development Skills)

Toolkits that package the SDD workflow (constitution → spec → plan → tasks) as commands an agent can run:

| Tool | What it is |
|---|---|
| **GitHub Spec Kit** | Official GitHub toolkit; `/speckit.*` commands that turn a spec into a plan and tasks |
| **OpenSpec** | Open-source spec management for agent workflows (specs as versioned artifacts) |
| **GStack** | A suite of slash-command skills (plan, review, QA, ship) layered on top of a coding agent |

They all share one idea: **write the spec, generate the plan, generate the tasks, then implement.**

---

## 6. Agent Skills

An **Agent Skill** is a small, portable package of instructions that teaches an agent *how* to do a specific task.

- Structure: a folder with a `SKILL.md` (name, description, instructions) plus optional scripts and reference files.
- Loading: the agent sees the skill's name/description, and pulls in the full instructions **only when the task matches**.
- Purpose: reusable expertise (e.g. "make a PDF", "review a PR", "run the SDD flow") without bloating every prompt.
- Relation to SDD tools: Spec Kit, OpenSpec, and GStack are effectively **collections of skills**.

Think of it as: **specs tell the agent *what* to build; skills tell the agent *how* to work.**

---

## How it all fits together

```
ADLC  (the overall lifecycle: humans direct, agents build)
  └── SDD  (the method: spec → plan → tasks → code)
        ├── Spec Kit / OpenSpec / GStack  (tools that run the SDD flow)
        └── Agent Skills  (reusable how-to instructions agents load)
              └── run on  Coding Agents  (Claude Code, Copilot, Cursor, opencode, Cline, Kiro, Antigravity …)
                    └── which are a type of  AI Agent
```

**One line:** Write the spec (SDD), let a coding agent (Claude Code, Copilot, …) implement it using tools (Spec Kit, skills) — that's the ADLC.
