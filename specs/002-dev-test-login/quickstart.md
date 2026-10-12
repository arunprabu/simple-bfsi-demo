# Development/Test Fake Sign-In Quickstart

This guide validates the local demo sign-in and its integration with the existing transfer flow. The fake sign-in is for local development and automated testing only; it is not a production authentication method.

## Prerequisites

- Python 3.12 and `uv`
- Node.js and npm
- A local PostgreSQL instance
- The backend's existing PostgreSQL settings from [backend/.env.example](../../backend/.env.example)
- Demo users and accounts seeded into a disposable development database

The backend prefers `DATABASE_URL`; when it is absent, the planned settings update constructs the connection URL from the existing `POSTGRES_*` environment values. Automated integration tests must use `TEST_DATABASE_URL` pointing to a separate database whose name contains a `test` component. Never point those tests at the development database.

The sample leaves `POSTGRES_PASSWORD` unset. Set it in the local shell only if the PostgreSQL instance requires password authentication; do not put an actual password in the tracked example.

## Start the backend with fake sign-in enabled

From the repository root, load the example PostgreSQL settings into the shell environment. Then:

```sh
cd backend
set -a
. ./.env.example
set +a
uv sync --dev
export APP_ENV=development
export FAKE_AUTH_ENABLED=true
uv run alembic upgrade head
uv run python -m simple_bank.dev_seed
uv run uvicorn simple_bank.main:app --reload
```

The seed command is additive: it creates missing demo customers/accounts and does not truncate tables, reset balances, or delete transactions. The two demo profiles are `demo-user-1` and `demo-user-2`; there are no passwords or fixed login credentials.

## Start and use the frontend

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open the local Vite URL and select one of the labeled demo profiles. The backend creates a short-lived fake JWT session cookie. The frontend does not display or store the token and submits all data through `/api/v1`.

1. Sign in as a demo profile and verify the transfer screen is available.
2. Use the synthetic source and recipient account references from the local seed records to submit an otherwise eligible transfer.
3. Verify the transfer succeeds through the normal service rules and displays the saved transaction confirmation.
4. Sign out, submit another transfer, and verify it is rejected as unauthenticated with no balance changes.
5. Disable fake auth or run outside the permitted development/test mode, restart the backend, and verify the demo sign-in is unavailable and cannot establish a session.

See [the data model](./data-model.md) and [the session API contract](./contracts/openapi.yaml) for the profile and session details.

## Backend validation

Run focused tests:

```sh
cd backend
uv run pytest tests/unit/test_dev_jwt.py tests/contract/test_dev_auth.py
```

For the PostgreSQL seed and resolver integration scenario, set `TEST_DATABASE_URL` to a dedicated test database and run:

```sh
uv run pytest tests/integration/test_dev_seed.py
```

Expected results include:

- Only an explicitly enabled development/test app issues a demo session.
- Unknown profiles, missing seed records, invalid signatures, and expired JWTs do not authenticate.
- The selected seeded profile maps to the expected customer identity; transfer input cannot override it.
- The seed operation is repeatable and does not reset existing balances.
- Signing out clears the browser session; the next transfer is rejected without moving funds.

## Frontend validation

From `frontend/`, run:

```sh
npm run test:ci
npm run build
npm run lint
```

The UI tests should cover the enabled/disabled login state, profile selection, successful sign-in, sign-out, error handling, and that transfer requests continue through the existing `/api/v1` client with same-origin credentials.

## Current Validation Snapshot

Validated on 2026-10-12:

- Backend unit and contract tests: **71 passed**.
- Backend PostgreSQL integration and performance tests: **11 skipped** because `TEST_DATABASE_URL` is not configured; the current process also has no resolved local PostgreSQL URL.
- Frontend tests: **17 passed**.
- Frontend production build/type-check and lint: **passed**.
- The PostgreSQL demo-seed/transfer scenarios, `alembic check`, and the 30-second local sign-in measurement remain pending until a dedicated test database and local development database are configured. See task T021.
