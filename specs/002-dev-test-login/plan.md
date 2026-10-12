# Implementation Plan: Development/Test Fake Sign-In

**Branch**: `002-dev-test-login` | **Date**: 2026-10-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification at `specs/002-dev-test-login/spec.md`. User direction: keep sign-in simple, use PostgreSQL-backed demo users, issue a fake JWT, and restrict the feature to development and automated testing.

## Summary

Add a one-click local sign-in that selects one of a small, seeded set of demo customers and establishes a short-lived, signed JWT session. Store the JWT in an HttpOnly cookie so the existing browser API client can send it to the existing `/api/v1` transfer API. The backend accepts this identity only when the application is explicitly configured for development or testing and fake auth is enabled; otherwise it continues to require its existing authenticated-customer resolver. Seed deterministic demo customers and active accounts in PostgreSQL without resetting existing balances or transaction history. No passwords or fixed login credentials are introduced.

## Technical Context

**Language/Version**: Python 3.12 backend; TypeScript, React 19, and Vite frontend

**Primary Dependencies**: Existing FastAPI, SQLAlchemy 2.x, asyncpg, Alembic, React, and Vite dependencies; add PyJWT for signing and verifying the short-lived test JWT

**Storage**: Existing PostgreSQL `customers` and `accounts` tables; no persisted auth-session table or schema migration is required

**Testing**: pytest unit, API contract, and PostgreSQL integration tests; Vitest frontend tests; PostgreSQL integration tests use the existing isolated `TEST_DATABASE_URL` guard

**Target Platform**: Local development and automated test environments only; browser traffic uses the existing Vite development proxy to the FastAPI app

**Project Type**: Existing React/Vite frontend with a FastAPI backend communicating through `/api/v1`

**Performance Goals**: No additional service latency target; meet SC-001 by reaching the transfer screen within 30 seconds of opening the local app

**Constraints**: Fake auth requires both an allowed `APP_ENV` (`development` or `test`) and explicit `FAKE_AUTH_ENABLED=true`; it defaults off and must not issue a session elsewhere. Demo profiles map only to seeded customer records. The JWT is signed, not encrypted, contains no password or account number, expires after one hour, and is held in an HttpOnly, SameSite=Lax cookie. Its signing key is generated in memory at app startup and is never hard-coded or committed. Transfer identity continues to come from the verified session, not transfer request data. Seed operations are additive/idempotent and never truncate or reset a development database. All frontend data access remains through `/api/v1`.

**Scale/Scope**: A small, deterministic set of demo profiles and accounts for local browser testing; one FastAPI process; no production customer authentication, password management, or external identity provider is added.

### Existing Integration Findings

- `create_app` already accepts an `AuthenticatedCustomerResolver`; the default app has no resolver and correctly rejects transfers as unauthenticated. Fake auth will provide a resolver only in explicitly enabled development/test mode.
- The frontend already uses `credentials: 'include'` and Vite proxies `/api/v1`, so a same-origin session cookie fits the existing API boundary.
- `Customer` currently stores a stable `customer_id`; `Account` stores ownership, opening time, exact balance, status, and account type. The seed operation can use those existing entities.
- Backend `Settings` and `backend/migrations/env.py` currently read `DATABASE_URL`, while `backend/.env.example` provides `POSTGRES_*` connection components. Preserve `DATABASE_URL` as the preferred setting and safely construct a URL from the existing `POSTGRES_*` variables when it is absent, using SQLAlchemy's URL builder rather than string interpolation. Reuse that helper in both application and migration configuration. Do not read or rely on any other environment file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan response | Gate |
|---|---|---|
| Decimal money and two-place rounding | Demo account balances are seeded as exact two-decimal values; transfer arithmetic remains in the existing service and is not changed by fake auth. | PASS |
| Account-number privacy | Demo auth responses and logs do not emit full account numbers; seed and auth tests assert account-number redaction at logging boundaries. | PASS |
| Every rule is tested | Tests cover environment gating, valid/invalid/expired JWTs, demo-profile allowlisting, sign-in/out, resolver identity, seed behavior, and frontend state. | PASS |
| Versioned API boundary | All new session endpoints are mounted under `/api/v1`; contract tests assert their paths and responses. | PASS |
| React/Vite client uses only the API | The login UI uses the `/api/v1` client and same-origin cookie; it never connects to PostgreSQL or internal backend services directly. | PASS |

No constitution deviations are proposed. The fake identity is a local testing aid only; it does not alter the production authentication boundary or any fund-transfer rule.

## Project Structure

### Documentation (this feature)

```text
specs/002-dev-test-login/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md              # Produced by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── src/simple_bank/
│   ├── api/
│   │   ├── dependencies.py          # Select the guarded fake resolver
│   │   └── v1/
│   │       ├── router.py            # Mount the session router
│   │       └── dev_auth.py          # Session status, sign-in, and sign-out
│   ├── schemas/
│   │   └── dev_auth.py              # Typed session/profile request and responses
│   ├── auth/
│   │   ├── __init__.py
│   │   └── dev_jwt.py               # Test-only JWT issue/verify functions
│   ├── config.py                    # APP_ENV, fake-auth gate, database URL
│   ├── dev_seed.py                  # Additive demo Customer/Account seed
│   └── main.py                      # Wire only the permitted resolver
├── migrations/env.py                # Reuse the safe database URL helper
├── .env.example                     # Document local/test mode flags
└── tests/
    ├── unit/
    │   ├── test_dev_auth_config.py
    │   └── test_dev_jwt.py
    ├── contract/
    │   ├── test_dev_auth.py
    │   └── test_dev_auth_gating.py
    └── integration/
        ├── test_dev_seed.py
        └── test_dev_auth_transfer.py

frontend/
└── src/
    ├── App.tsx                      # Gate the local sign-in/transfer views
    ├── components/DevSignIn.tsx     # Select a seeded demo profile
    ├── services/devAuth.ts          # Session status and sign-in/out API calls
    ├── services/devAuth.test.ts
    └── App.test.tsx
```

These are proposed feature files; existing API, model, and frontend files are extended in place. No session table or new customer/account schema is introduced.

**Structure Decision**: Extend the existing separated `backend/` and `frontend/` projects. Keep token validation and fake profile mapping behind the existing FastAPI resolver boundary. The browser selects a demo profile only through the versioned API, and the backend maps that allowed profile to a seeded `Customer`.

## Design and Phase Gates

- **Pre-research**: PASS — the spec has no unresolved clarification markers. The user confirmed local/test-only fake sign-in, PostgreSQL seed data, a fake JWT, and no fixed credentials.
- **Phase 0 research**: Decisions are recorded in [research.md](./research.md), including environment gating, JWT handling, seed behavior, and use of existing database configuration.
- **Phase 1 design**: Entity and token details are in [data-model.md](./data-model.md); endpoint contract is in [contracts/openapi.yaml](./contracts/openapi.yaml); runnable validation scenarios are in [quickstart.md](./quickstart.md).
- **Post-design**: PASS — fake auth is fail-closed outside development/test, all endpoints are versioned, the session identity cannot be overridden in transfer requests, and database seeding does not mutate existing balances.

**Known local configuration constraint**: The sample currently separates PostgreSQL connection components into `POSTGRES_*`, whereas application settings and Alembic read `DATABASE_URL`. The implementation tasks must preserve direct `DATABASE_URL` support and add the safe `POSTGRES_*` fallback to the shared helper before local seeding and migrations are expected to work.

## Complexity Tracking

No constitution violations or additional projects are proposed. PyJWT is the only new runtime dependency; it avoids custom token parsing. A one-time additive seed command and an in-memory signing key keep this test-only feature small and avoid both a session database table and a committed secret.
