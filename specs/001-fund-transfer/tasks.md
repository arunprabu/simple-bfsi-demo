# Tasks: Fund Transfer

**Input**: Design documents from `/specs/001-fund-transfer/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Included because the project constitution requires every application rule
to have an automated test.

**Organization**: Tasks are grouped by the two prioritized user stories in spec.md.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel with other marked tasks in its phase; paths do not overlap.
- **[Story]**: User story served by this task: `[US1]` or `[US2]`.
- Every task names its implementation or test file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the greenfield backend and customer web application projects.

- [X] T001 [P] Initialize the Python 3.12 uv backend and declare FastAPI, Pydantic, SQLAlchemy 2.x, asyncpg, Alembic, pytest, pytest-asyncio, and HTTPX dependencies in `backend/pyproject.toml`.
- [X] T002 [P] Initialize the React/Vite/TypeScript customer web app and frontend test scripts in `frontend/package.json`, `frontend/vite.config.ts`, and `frontend/tsconfig.json`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish persistence, authenticated-customer context, routing, test
infrastructure, and privacy safeguards used by both stories.

**⚠️ CRITICAL**: Complete this phase before starting either user story.

- [X] T003 Configure environment settings and an async SQLAlchemy engine/session factory in `backend/src/simple_bank/config.py` and `backend/src/simple_bank/db/session.py`; read database credentials from environment and never commit credentials.
- [X] T004 Define Customer, Account, and Transaction ORM entities plus the initial Alembic migration in `backend/src/simple_bank/models/customer.py`, `backend/src/simple_bank/models/account.py`, `backend/src/simple_bank/models/transaction.py`, and `backend/migrations/versions/0001_fund_transfer.py`. Preserve these constraints verbatim: Customer `customer_id` is a stable unique identifier; Account `account_number` is unique; `customer_id` is required; `balance` is INR NUMERIC(18, 2) and non-negative; `status` allows ACTIVE or inactive state; source `account_type` is SAVINGS; Transaction `transaction_id` is unique; `from_account` and `to_account` reference Account and must differ; `amount` is INR NUMERIC(18, 2) and at least Rs 1.00; `status` is COMPLETED; `created_at` is timezone-aware.
- [X] T005 Add an injectable authenticated-customer dependency in `backend/src/simple_bank/api/dependencies.py` that obtains identity from the bank's existing session integration, rejects missing identity with HTTP 401 / `UNAUTHENTICATED`, and never trusts a request-body `customer_id`.
- [X] T006 Create the FastAPI application, `/api/v1` router, shared error schemas, and HTTP error mapping scaffolding in `backend/src/simple_bank/main.py`, `backend/src/simple_bank/api/v1/router.py`, `backend/src/simple_bank/schemas/errors.py`, and `backend/src/simple_bank/api/errors.py`.
- [X] T007 Create the React API client in `frontend/src/services/api.ts`; configure its base path as `/api/v1` and ensure customer-facing data access goes only through this client.
- [X] T008 Configure pytest and isolated PostgreSQL test fixtures in `backend/pyproject.toml` and the shared `backend/tests/conftest.py`, including migration-backed setup and cleanup that cannot access a non-test database.
- [X] T009 Add account-number masking and structured transfer logging in `backend/src/simple_bank/logging.py`, with automated privacy assertions in `backend/tests/unit/test_logging.py`; any logged account reference must display only its last four digits as `XXXX1234`, and tests must prove no full account number is emitted.

**Checkpoint**: Backend and frontend projects start, database/test infrastructure is
available, and all future work can obtain authenticated identity without accepting it
from request data.

---

## Phase 3: User Story 1 - Transfer Money to Another Bank Customer (Priority: P1) 🎯 MVP

**Goal**: An authenticated customer can transfer an eligible amount from their active
savings account to a different active Simple Bank account, receive a transaction ID,
and observe the corresponding debit and credit.

**Independent Test**: With seeded active accounts and an authenticated customer,
submit a valid transfer; verify HTTP 201, unique retrievable transaction ID, exact
matching source debit and recipient credit, masked account references, and persisted
completion.

### Tests for User Story 1

- [X] T010 [P] [US1] Add a contract test for a valid `POST /api/v1/transfers` response, including HTTP 201 and all documented success fields, in `backend/tests/contract/test_transfers.py`.
- [X] T011 [P] [US1] Add a TransferService unit test for a valid amount and eligible source/recipient resulting in a completed transfer in `backend/tests/unit/test_transfer_service.py`.
- [X] T012 [P] [US1] Add a PostgreSQL integration test verifying equal source debit and recipient credit, atomic persistence, and a unique retrievable transaction ID in `backend/tests/integration/test_transfers.py`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement account and transaction repository operations in `backend/src/simple_bank/repositories/accounts.py` and `backend/src/simple_bank/repositories/transactions.py`; use exact Decimal values and timezone-aware creation times.
- [X] T014 [US1] Implement `TransferService` in `backend/src/simple_bank/services/transfers.py`; orchestrate a single database transaction that locks the authenticated customer's serialization row, locks source and recipient accounts in deterministic order, revalidates eligibility, debits/credits equally, saves one COMPLETED Transaction, and rolls back all changes on failure.
- [X] T015 [US1] Implement request/response schemas and `POST /api/v1/transfers` in `backend/src/simple_bank/schemas/transfers.py` and `backend/src/simple_bank/api/v1/transfers.py`; accept only `from_account`, `to_account`, and decimal-string `amount`, derive customer identity from T005, and return masked account references with transaction ID, COMPLETED status, amount, and ISO 8601 `created_at`.
- [X] T016 [US1] Implement the customer transfer form and confirmation state in `frontend/src/pages/TransferPage.tsx` and `frontend/src/components/TransferForm.tsx`; submit transfer details only through `frontend/src/services/transfers.ts` and show the result and transaction ID.
- [X] T017 [US1] Add customer web transfer interaction tests in `frontend/src/pages/TransferPage.test.tsx`, verifying successful submission uses the `/api/v1` client and displays the completion result without direct backend access.

**Checkpoint**: User Story 1 delivers an independently testable successful transfer.

---

## Phase 4: User Story 2 - Avoid Invalid or Over-Limit Transfers (Priority: P1)

**Goal**: Invalid transfer attempts, including attempts above the applicable
customer-wide or source-account age-based daily limit, are declined with the
specified error code and customer-safe message, without changing balances or daily
totals.

**Independent Test**: From seeded PostgreSQL state, exercise each invalid amount,
account, balance, customer-wide limit, and source-account age limit; verify the
documented HTTP/code result and that no declined attempt changes either balance or
completed transfer total.

### Tests for User Story 2

- [X] T018 [P] [US2] Add unit tests for TransferService rules in `backend/tests/unit/test_transfer_service.py`: reject amounts below Rs 1.00 or with more than two fractional digits; reject same-account, missing/inactive recipient, inactive source, non-owned/non-savings source, insufficient funds, and totals above Rs 1,00,000 for the IST calendar day; allow exact source-balance and exact daily-limit boundaries; allow transfers between distinct accounts of the same customer.
- [X] T019 [P] [US2] Add API contract tests for `INVALID_AMOUNT`, `INSUFFICIENT_BALANCE`, `DAILY_LIMIT_EXCEEDED`, `SAME_ACCOUNT`, `ACCOUNT_INACTIVE`, `ACCOUNT_NOT_FOUND`, `TRANSFER_FAILED`, and `UNAUTHENTICATED` error status/code/message mapping in `backend/tests/contract/test_transfers.py`.
- [X] T020 [P] [US2] Add PostgreSQL integration tests for declined-transfer rollback, midnight IST limit reset, and concurrent requests that must not overspend a source account or exceed the customer daily limit in `backend/tests/integration/test_transfers.py`.

### Implementation for User Story 2

- [X] T021 [US2] Implement service-level transfer validation and typed domain failures in `backend/src/simple_bank/services/transfers.py`; parse amounts with Decimal, require at least Rs 1.00 and no more than two fractional digits, require different active Simple Bank accounts and an authenticated customer's active savings source, enforce sufficient balance and the completed outgoing limit of Rs 1,00,000 per IST calendar day, and leave failed transfers uncommitted.
- [X] T022 [US2] Map each service/domain failure to the exact HTTP status and error code in `backend/src/simple_bank/api/errors.py` and `backend/src/simple_bank/api/v1/transfers.py`; ensure response messages are customer-safe and never contain full account numbers.
- [X] T023 [US2] Add frontend validation and declined-transfer feedback in `frontend/src/components/TransferForm.tsx` and `frontend/src/pages/TransferPage.tsx`; display the API's customer-safe error result and never treat a declined result as success.
- [X] T024 [US2] Add frontend validation/error-state tests in `frontend/src/pages/TransferPage.test.tsx` for invalid amounts and API declines, asserting no success confirmation appears for a declined transfer.

**Checkpoint**: The baseline User Story 1 and User Story 2 rules have automated
coverage. Complete the age-based US2 follow-up in Phase 6 before considering the
revised daily-limit rule complete.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validate measurable service quality and the complete feature.

- [X] T025 Add a repeatable transfer response-time test in `backend/tests/performance/test_transfer_latency.py` that measures 100 representative submissions under documented normal-service conditions and asserts at least 95 complete within 1 second.
- [X] T026 Add a frontend boundary test in `frontend/src/services/transfers.test.ts` verifying the transfer client uses only `/api/v1/transfers` and contains no direct database or internal-service access.
- [X] T027 Execute and reconcile every validation scenario in `specs/001-fund-transfer/quickstart.md`; update that guide with verified setup/test commands and results in `specs/001-fund-transfer/quickstart.md`.
- [X] T028 Run backend unit, contract, PostgreSQL integration, logging-privacy, and performance tests plus frontend tests; resolve failures and record final commands/outcomes in `specs/001-fund-transfer/quickstart.md`.

---

## Phase 6: User Story 2 Follow-Up — Account-Age Daily Limits (Priority: P1)

**Goal**: Enforce a Rs 50,000 daily outgoing cap per source savings account while
fewer than 30 elapsed days have passed since opening, while retaining the Rs 1,00,000
per-account tier after that boundary and the existing Rs 1,00,000 customer-wide cap.

**Independent Test**: Seed accounts with authoritative opening instants and completed
outgoing transfers, then submit eligible and over-limit requests through the transfer
service and API. Verify the under-30-day and mature tiers, the exact 30-day boundary,
customer-wide aggregation across multiple source accounts, error mapping, and
unchanged state after declines.

### Tests for the Account-Age Limit

- [X] T029 [P] [US2] Add TransferService unit tests in `backend/tests/unit/test_transfer_service.py` for an account under 30 elapsed days, an account exactly 30 elapsed days old, the Rs 50,000 exact and over-limit boundary, the Rs 1,00,000 mature-account tier, separate source accounts, the customer-wide aggregate, and declined transfers not counting toward either total.
- [X] T030 [P] [US2] Add PostgreSQL integration tests in `backend/tests/integration/test_transfers.py` proving concurrent transfers cannot exceed the young source-account Rs 50,000 limit or the customer-wide Rs 1,00,000 limit across multiple source accounts, and that both totals reset at IST midnight.
- [X] T031 [P] [US2] Add API contract tests in `backend/tests/contract/test_transfers.py` for `DAILY_LIMIT_EXCEEDED` when the source-account age-based limit is exceeded, including the customer-safe error response and unchanged balances.

### Implementation for the Account-Age Limit

- [X] T032 [US2] Add a required, immutable, timezone-aware `opened_at` timestamp stored as an instant to the Account ORM model and Alembic revisions `backend/migrations/versions/0002_account_opened_at.py` and `backend/migrations/versions/0003_require_account_opened_at.py`; keep revision 0002 nullable for authoritative backfill, have revision 0003 reject remaining nulls before making the field required, and update account factories in `backend/tests/unit/test_transfer_service.py` and `backend/tests/integration/test_transfers.py` without defaulting to migration time.
- [X] T033 [US2] Update `TransferService` and transaction aggregation in `backend/src/simple_bank/services/transfers.py` and `backend/src/simple_bank/repositories/transactions.py` to use the transfer submission instant and enforce both the customer's Rs 1,00,000 IST-day aggregate and the source account's Rs 50,000 limit before 30 elapsed days or Rs 1,00,000 limit at or after 30 elapsed days.
- [X] T034 [US2] Map breaches of either daily limit to the existing `DAILY_LIMIT_EXCEEDED` response in `backend/src/simple_bank/api/errors.py` and document that the error covers the source-account or customer-wide limit in `specs/001-fund-transfer/contracts/openapi.yaml`.

**Checkpoint**: The age-based limit and the existing customer-wide aggregate pass
unit, API contract, and PostgreSQL concurrency/boundary tests.

---

## Phase 7: Polish — Reproducible Performance Validation

**Purpose**: Make the 1-second/95% response-time criterion reproducible and record
post-follow-up validation results.

- [X] T035 Update `backend/tests/performance/test_transfer_latency.py` to use the documented profile: a dedicated Linux x86_64 runner with at least 2 vCPU and 4 GiB RAM, colocated API and PostgreSQL, no unrelated benchmark load, 10 unmeasured warm-ups, and 10 concurrent clients submitting 100 measured valid loopback HTTP requests from distinct seeded customers and source accounts; use a monotonic clock and assert at least 95 responses complete within 1 second.
- [ ] T036 Execute the account-age scenarios and response-time profile in `specs/001-fund-transfer/quickstart.md`; record the actual runner resources, software versions, commands, and results in that guide.
- [ ] T037 Run the full backend unit, contract, PostgreSQL integration, logging-privacy, and performance suites plus frontend tests and `alembic check`; resolve failures and record final post-follow-up outcomes in `specs/001-fund-transfer/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No prerequisites. T001 and T002 can run in parallel because
  they initialize separate project directories.
- **Foundational (Phase 2)**: Depends on project setup. This phase blocks user stories.
- **User Stories (Phases 3–4)**: Start after Phase 2. US2 extends the same service
  and API error boundary as US1, so execute US1 core integration before US2.
- **Polish (Phase 5)**: Depends on both user stories being complete.
- **Account-age follow-up (Phase 6)**: Depends on the baseline US1/US2 service,
  account model, and PostgreSQL test infrastructure; write the independent test
  suites before implementing the new rule.
- **Reproducible validation (Phase 7)**: Depends on Phase 6; record age-limit and
  performance results before final regression validation.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on another user story.
- **US2 (P1)**: Starts after Phase 2 and depends on the `TransferService` and endpoint
  from US1 for error mapping and rejected-transfer behavior.
- **US2 account-age follow-up (Phase 6)**: Extends the existing US2 limit behavior;
  it depends on the Account model, authenticated-customer aggregation, and transfer
  service from the baseline phases.

### Within Each User Story

- Write and run listed tests so they fail for the missing behavior before
  implementation.
- Complete data/persistence prerequisites before service work, service work before
  route mapping, and API integration before frontend confirmation behavior.
- Preserve exact Decimal semantics and PostgreSQL atomicity at every phase.

### Parallel Opportunities

- T001 and T002 can run concurrently (backend and frontend scaffolds).
- In the Foundational phase, T005, T006, T007, T009 can be developed in parallel
  after the base project setup; T003/T004 and T008 follow their explicit file/
  dependency prerequisites.
- In US1, T010, T011, and T012 are independent test files and can be authored
  concurrently; T013 is a distinct repository file and can proceed alongside them.
- In US2, T018, T019, and T020 can be written concurrently because they target
  distinct test suites, while their implementation tasks follow the service/API
  dependency order.
- In the account-age follow-up, T029, T030, and T031 can be authored in parallel
  because they target separate unit, integration, and contract test files; T032 must
  precede T033, which precedes T034.
- Frontend tasks can proceed independently from backend tasks after T002/T007,
  against the OpenAPI contract and mocked API responses.

## Parallel Example: User Story 1

```text
T010 contract test in backend/tests/contract/test_transfers.py
T011 unit test in backend/tests/unit/test_transfer_service.py
T012 PostgreSQL integration test in backend/tests/integration/test_transfers.py
T013 account/transaction repositories in backend/src/simple_bank/repositories/
```

## Parallel Example: User Story 2

```text
T018 rule tests in backend/tests/unit/test_transfer_service.py
T019 error contract tests in backend/tests/contract/test_transfers.py
T020 rollback/concurrency tests in backend/tests/integration/test_transfers.py
```

## Parallel Example: Account-Age Follow-Up

```text
T029 unit boundary tests in backend/tests/unit/test_transfer_service.py
T030 PostgreSQL concurrency tests in backend/tests/integration/test_transfers.py
T031 API limit-error tests in backend/tests/contract/test_transfers.py
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 project setup.
2. Complete Phase 2 database, authentication boundary, routing, test, and logging
   foundations.
3. Complete Phase 3 successful transfer service, persistence, API, and customer
   interface.
4. Validate US1 independently: HTTP 201, persisted transaction, equal account
   movements, unique ID, and masked response references.

### Incremental Delivery

1. Deliver the valid transfer journey as the MVP.
2. Add all decline rules and error mappings in US2; verify state never changes on
   decline and concurrency cannot bypass balance or daily-limit checks.
3. Complete the latency, frontend boundary, logging privacy, and full quickstart
   validation in Phase 5.
4. Extend US2 with the source-account age tiers and verify both limit scopes in
   Phase 6.
5. Run the defined performance profile and post-follow-up regression checks in
   Phase 7.
