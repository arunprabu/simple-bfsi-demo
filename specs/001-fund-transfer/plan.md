# Implementation Plan: Fund Transfer

**Branch**: `001-fund-transfer` | **Date**: 2026-10-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification at `specs/001-fund-transfer/spec.md` and user plan
constraints: Python 3.12 managed with uv, FastAPI, PostgreSQL, transfer rules in a
separate service class, and a REST API under `/api/v1`.

## Summary

Deliver authenticated customer-to-customer transfers from a savings account to an
active Simple Bank account. A FastAPI REST endpoint delegates all eligibility and
transfer orchestration to a separately unit-testable `TransferService`. Persist
accounts and completed transactions in PostgreSQL, using exact decimal amounts and a
single database transaction to enforce atomic debit/credit, balance validation, the
per-customer Rs 1,00,000 IST-calendar-day aggregate, and a per-source-account daily
limit of Rs 50,000 until 30 elapsed days have passed since account opening (then
Rs 1,00,000). The existing React/Vite customer web app, when implemented, calls only
this versioned API.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy 2.x, asyncpg, Alembic; uv for
environment and dependency management

**Storage**: PostgreSQL; `NUMERIC(18, 2)` for persisted INR amounts; timezone-aware
timestamps

**Testing**: pytest; unit tests for transfer rules, PostgreSQL-backed integration
tests for transaction/concurrency guarantees, and API contract tests. Rule tests cover
the under-30-day source-account cap, its exact boundary, the mature-account cap, and
the separate customer-wide aggregate.

**Target Platform**: Python 3.12 server runtime with a reachable PostgreSQL instance;
deployment environment is not specified by the project documentation. The response-
time acceptance profile uses a dedicated Linux x86_64 runner with at least 2 vCPU and
4 GiB RAM, with the API and PostgreSQL on that runner and no unrelated benchmark load.

**Project Type**: Web application with a FastAPI backend and a constitution-mandated
React/Vite customer web client communicating only through `/api/v1`

**Performance Goals**: Return a clear success or decline result within 1 second for
at least 95 of 100 measured submissions under the defined profile: 10 concurrent
clients, 100 valid loopback HTTP submissions from distinct seeded customers and
source accounts, and 10 unmeasured warm-up requests. Exclude startup and fixture
setup from timing and use a monotonic clock.

**Constraints**: All monetary arithmetic uses `Decimal` and PostgreSQL `NUMERIC`;
reject amounts below Rs 1.00 or with more than two fractional digits; no full account
numbers in logs; complete debit, credit, and transaction persistence atomically;
require an authoritative, timezone-aware Account `opened_at`; enforce both the
Rs 1,00,000 customer-wide daily aggregate and the source-account limit (Rs 50,000
before 30 elapsed days, otherwise Rs 1,00,000) in the same transaction; serialize
same-customer transfer decisions to prevent either limit from being exceeded

**Scale/Scope**: Initial feature scope is a single bank and its customer accounts.
Expected production customer count and throughput are not specified; the 10-client,
100-submission profile is a reproducible acceptance-test condition, not a production
capacity claim.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan response | Gate |
|---|---|---|
| Decimal money and two-place rounding | Python `Decimal` and PostgreSQL `NUMERIC(18, 2)`; request precision validated without float conversion. | PASS |
| Account-number privacy | Mask account references at log boundaries; tests assert that full numbers never appear. | PASS |
| Every rule is tested | Unit, API, and PostgreSQL integration tests cover service rules, including both account-age tiers, exact limits, customer aggregation, persistence, atomicity, and concurrency. | PASS |
| API prefix | Mount the transfer router only under `/api/v1`; contract tests assert the route. | PASS |
| React/Vite client uses only the API | Keep the customer web client as a separate consumer of the versioned API; no direct database or backend access. | PASS |

No constitution deviations are proposed. Authentication is an integration boundary:
the transfer request uses the existing authenticated customer identity and never
accepts a caller-selected `customer_id`; implementation must connect the existing
sign-in/session provider when available.

## Project Structure

### Documentation (this feature)

```text
specs/001-fund-transfer/
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
├── pyproject.toml
├── alembic.ini
├── migrations/
├── src/simple_bank/
│   ├── api/v1/transfers.py
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/transfers.py
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── package.json
└── src/
    └── services/transfers.ts
```

The repository currently has no source-code directories or dependency manifests.
These are proposed implementation locations, not existing files. `TransferService`
owns transfer decisions and orchestration; the API layer performs HTTP validation,
authentication-context extraction, service invocation, and response/error mapping.
Repositories/data-access code handle persistence and transaction boundaries. The
frontend location is included to honor the constitution but its existing app setup
must be confirmed during task implementation.

**Structure Decision**: Use a separated backend/frontend web application layout.
Keep the feature's rule-bearing service in `backend/src/simple_bank/services`, with
FastAPI route adapters under `api/v1`, and test its rules independently of HTTP and
PostgreSQL.

## Phase Gates

- **Pre-research**: PASS — feature requirements are clarified, user technology
  choices are explicit, and constitutional constraints are known.
- **Post-design**: PASS — data and API design preserve exact decimal amounts,
  account-number privacy, `/api/v1`, the account-age and customer-wide limits, and
  service-level testability. See
  [research.md](./research.md), [data-model.md](./data-model.md), and
  [contracts/openapi.yaml](./contracts/openapi.yaml).
- **Known integration assumption**: The authenticated customer identity is supplied
  by the bank's existing sign-in/session integration. The repository has no
  application/auth implementation to inspect; integration wiring must be confirmed
  when implementation begins. Existing account opening instants must come from the
  authoritative account source; a migration timestamp is not a valid substitute.

## Complexity Tracking

No constitution violations or additional projects are proposed. Separate
repository/data-access components are warranted to keep rule decisions unit-testable
while preserving a single atomic PostgreSQL transaction for fund movement.
