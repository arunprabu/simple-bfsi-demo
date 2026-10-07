# Agent instructions

# Simple Bank Copilot instructions

Follow the root `AGENTS.md` restrictions: NEVER access the `guide/` or `guides/` or `.guide/` directories, and access only `.env.example` among environment files.

Use python in your commands, not python3

## Repository context

- This repository contains Simple Bank training guides, requirements, and Spec Kit skills. App source code may be created as part of a use case; do not assume it already exists.
- Treat the active use case's specification and acceptance criteria as the source of truth. Ask for clarification when they conflict or leave an important behavior undefined.
- Follow the stack and scope named by the active use case. Unless it says otherwise, backend examples use Python 3.12 and FastAPI, and the web UI uses React with Vite.
- Keep training guides consistent with the repository's existing terminology, use-case numbering, and learner-focused style.

## Banking and code quality

- Represent monetary amounts with `Decimal` in Python or an equivalent exact decimal type; do not use binary floating point for money.
- Preserve all specified transfer rules, including positive amounts, sufficient balance, daily limits, distinct active accounts, and unique persisted transaction IDs. Do not invent additional business rules.
- Never hard-code credentials or expose them in examples. Do not log full account numbers or other sensitive customer data; mask account numbers when they must be shown.
- Validate inputs and return clear, stable error codes for expected business-rule failures. Do not expose internal exception details to users.
- Add or update automated tests for each relevant acceptance criterion. Run the narrowest relevant tests or checks when available, and report anything that could not be run.

## Working in this repository

- Prefer small, focused changes that preserve the educational intent of the material.
- Keep documentation examples consistent with the code and requirements they describe.
- Do not modify generated Spec Kit integration files or skill definitions unless the task specifically calls for it.

## Restricted paths

- NEVER EVER access the `guide/` or `guides/` or `.guide/`directories and the files inside. NEVER TRY listing, searching, reading, creating, editing, or deleting files in them.
- Do not access any environment file other than `.env.example`.
- In particular, NEVER access `.env.local`, `.env.dev`, `.env.stage`, `.env.test`, or `.env.prod`.
- Treat any other `.env` file as restricted too. Never read, search, modify, or reveal its contents.
- Use python in your commands, not python3
