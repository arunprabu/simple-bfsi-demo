# Tasks: Development/Test Fake Sign-In

**Input**: Design documents from `specs/002-dev-test-login/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `contracts/openapi.yaml`

**Tests**: Included because the project constitution requires every normative application rule to have automated coverage.

**Organization**: Tasks are grouped by the two user stories in `spec.md`. No passwords or fixed login credentials are introduced.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks in the same phase because their files do not overlap.
- **[Story]**: User story served by the task: `[US1]` or `[US2]`.
- Every task includes its implementation or test file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the small JWT dependency and document explicit local/test configuration.

- [X] T001 [P] Add `PyJWT` to `backend/pyproject.toml` and regenerate `backend/uv.lock` with `uv lock`.
- [X] T002 [P] Document `APP_ENV=development` and `FAKE_AUTH_ENABLED=false` in `backend/.env.example`, leave database passwords to local environment configuration, and add no demo password or JWT signing secret.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish safe environment parsing and one reusable PostgreSQL URL source for the API, seed command, and migrations.

**⚠️ CRITICAL**: Complete this phase before either user story.

- [X] T003 [P] Add unit tests in `backend/tests/unit/test_dev_auth_config.py` for `DATABASE_URL` precedence, safe URL construction from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and `POSTGRES_DB`, disabled-by-default fake auth, allowed `APP_ENV` values (`development` and `test`), and rejection of fake auth in other environments.
- [X] T004 Implement the shared settings and database URL helper in `backend/src/simple_bank/config.py`; preserve `DATABASE_URL` as the override, use SQLAlchemy's URL builder for the `POSTGRES_*` fallback, and update `backend/migrations/env.py` to use the same helper without logging connection credentials.

**Checkpoint**: Configuration tests pass; app and Alembic can use the existing PostgreSQL settings; fake auth remains disabled unless explicitly allowed.

---

## Phase 3: User Story 1 - Sign In to the Local Test App (Priority: P1) 🎯 MVP

**Goal**: A developer/tester selects a seeded demo profile, receives a fake JWT session, and can exercise the existing transfer flow without a password.

**Independent Test**: With `APP_ENV=development` and fake auth explicitly enabled, prepare the demo records, sign in through the frontend, submit an otherwise eligible transfer, and verify the normal transfer rules and saved confirmation apply to the selected seeded customer.

### Tests for User Story 1

- [X] T005 [P] [US1] Add JWT unit tests in `backend/tests/unit/test_dev_jwt.py` for valid signing/verification and rejection of an unexpected algorithm, invalid signature, wrong issuer/audience, missing demo marker, malformed token, and expired `exp`.
- [X] T006 [P] [US1] Add API contract tests in `backend/tests/contract/test_dev_auth.py` for `GET` and `POST /api/v1/dev-auth/session`; verify allowlisted profiles, profile-not-found and demo-data-unavailable errors, the `dev_session` cookie attributes, no password field, no JWT in the JSON body, and the `/api/v1` prefix.
- [X] T007 [P] [US1] Add PostgreSQL integration tests in `backend/tests/integration/test_dev_seed.py` for the additive seed operation, including repeat runs that preserve existing balances and transactions and assertions that account numbers do not appear in logs; use only the isolated `TEST_DATABASE_URL`.
- [X] T008 [P] [US1] Add an integration test in `backend/tests/integration/test_dev_auth_transfer.py` that signs in as a seeded profile, submits a transfer with the `dev_session` cookie, verifies the authenticated customer owns the source account, and confirms a request-supplied customer identifier cannot change that identity.
- [X] T009 [P] [US1] Add Vitest tests in `frontend/src/services/devAuth.test.ts` and `frontend/src/App.test.tsx` for session-status/profile loading, password-free demo selection, same-origin cookie credentials, and transition to the transfer screen after sign-in.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement the additive demo seed command in `backend/src/simple_bank/dev_seed.py` for `demo-user-1` → `demo-customer-1` and `demo-user-2` → `demo-customer-2`; preserve the Data Model constraints verbatim: `customer_id` is stable and required as a reference to an existing Customer; `account_number` is unique and synthetic, and its full value is never logged; `opened_at` is required and timezone-aware; `balance` is exact two-decimal INR and non-negative; `status` is `ACTIVE`; a source account has `account_type=SAVINGS`; and the recipient is a different account. Insert missing rows only; never truncate tables, reset balances, or delete transactions.
- [X] T011 [P] [US1] Add `backend/src/simple_bank/auth/__init__.py` and implement the PyJWT codec in `backend/src/simple_bank/auth/dev_jwt.py` using fixed `HS256` verification, a process-local generated signing key, and only `sub` (an existing allowlisted demo `customer_id`), `demo=true`, fixed `iss`/`aud`, `iat`, and one-hour `exp` claims; do not add passwords, fixed credentials, or a committed key.
- [X] T012 [US1] Add typed request/response models in `backend/src/simple_bank/schemas/dev_auth.py` and implement session status and sign-in in `backend/src/simple_bank/api/v1/dev_auth.py`; map `FAKE_AUTH_DISABLED` to 403, `DEMO_PROFILE_NOT_FOUND` to 404, and `DEMO_DATA_UNAVAILABLE` to 503 in `backend/src/simple_bank/api/errors.py`. Define `profile_id` as a stable allowlisted string (`demo-user-1` or `demo-user-2`), `label` as non-sensitive display text, and `customer_id` as a required reference to an existing Customer (`demo-customer-1` or `demo-customer-2`). Set an HttpOnly, SameSite=Lax `dev_session` cookie scoped to `/api/v1` (Secure when served over HTTPS) without returning the JWT in the response body.
- [X] T013 [US1] Mount the dev-auth router under `/api/v1` and wire the fake resolver in `backend/src/simple_bank/api/v1/router.py`, `backend/src/simple_bank/main.py`, and `backend/src/simple_bank/api/dependencies.py`; use fake identity only when configuration permits it, prefer an explicitly supplied bank resolver, and continue deriving transfer identity from the verified session rather than transfer request data.
- [X] T014 [P] [US1] Implement the typed session-status and sign-in client in `frontend/src/services/devAuth.ts` using the existing `/api/v1` client and same-origin credentials.
- [X] T015 [US1] Add the demo-profile selection UI in `frontend/src/components/DevSignIn.tsx` and connect it through `frontend/src/App.tsx`; show the demo option only in a Vite development build when the backend reports fake auth enabled, collect no password, and show the existing transfer screen after sign-in.

**Checkpoint**: A tester can use a seeded profile to reach the existing transfer screen and complete an eligible transfer through the normal API/session identity.

---

## Phase 4: User Story 2 - Preserve Authentication Outside Local Testing (Priority: P1)

**Goal**: Fake sign-in cannot establish a session outside explicitly permitted development/test modes; existing bank authentication remains authoritative, and signing out ends the browser demo session.

**Independent Test**: Verify the demo option is unavailable when fake auth is disabled or the app is outside development/test, that a supplied bank resolver still determines identity, and that signing out clears the cookie so the next transfer is rejected as unauthenticated without moving funds.

### Tests for User Story 2

- [X] T016 [P] [US2] Add contract tests in `backend/tests/contract/test_dev_auth_gating.py` proving fake sign-in is off by default, production/unknown modes cannot issue a cookie, configuration cannot enable fake auth outside development/test, a supplied bank resolver takes precedence, and a transfer without a valid session returns `UNAUTHENTICATED` without changing balances.
- [X] T017 [P] [US2] Extend `frontend/src/App.test.tsx` to verify the demo option is hidden when Vite is not in development mode or backend status is disabled, and verify the signed-out state after logout.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `DELETE /api/v1/dev-auth/session` in `backend/src/simple_bank/api/v1/dev_auth.py` to clear the `dev_session` cookie; verify session status becomes anonymous and subsequent transfers receive the existing `UNAUTHENTICATED` result.
- [X] T019 [P] [US2] Add sign-out handling in `frontend/src/services/devAuth.ts`, `frontend/src/components/DevSignIn.tsx`, and `frontend/src/App.tsx`; clear the browser session, return to the demo sign-in state, and leave the existing bank-authenticated transfer path unchanged.

**Checkpoint**: Fake auth is unavailable outside the permitted local/test configuration; normal resolver behavior is preserved; sign-out removes the browser's demo session.

---

## Phase 5: Polish & Cross-Cutting Validation

**Purpose**: Verify the complete local workflow and keep the contract/quickstart aligned with implementation.

- [X] T020 Run the backend unit/contract tests and frontend Vitest/build/lint checks; record the commands and actual results in `specs/002-dev-test-login/quickstart.md`.
- [ ] T021 With a dedicated PostgreSQL `TEST_DATABASE_URL` and a local development `DATABASE_URL`, run the demo-seed and authenticated-transfer integration tests, validate `uv run alembic check`, time the local sign-in against SC-001, and record actual results in `specs/002-dev-test-login/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 and T002 can run in parallel.
- **Foundational (Phase 2)**: Depends on Setup. T003 establishes configuration expectations; T004 implements them and blocks both stories.
- **User Story 1 (Phase 3)**: Starts after Phase 2. Author T005-T009 in parallel; then implement the seed and JWT modules (T010-T011), session API (T012), backend wiring (T013), and frontend client/UI (T014-T015).
- **User Story 2 (Phase 4)**: Builds on the session API and UI from US1. T016 and T017 can be authored in parallel; T018 and T019 can be implemented in parallel after their respective tests.
- **Polish (Phase 5)**: Depends on both stories being complete. T020 can run without PostgreSQL; T021 requires a dedicated test database and a local development database connection.

### User Story Dependencies

- **US1 (P1)**: Depends on Setup and Foundational; no dependency on another user story.
- **US2 (P1)**: Depends on the US1 session endpoint and UI for logout, but independently verifies that fake auth is disabled outside the allowed local/test mode and that an injected bank resolver remains authoritative.

### Parallel Opportunities

- T001 and T002 touch separate files.
- T005-T009 cover separate backend unit, contract, PostgreSQL integration, and frontend test files.
- T010 and T011 implement separate seed and JWT modules.
- T014 can proceed alongside backend implementation after the API contract is stable.
- T016 and T017 use separate test files; T018 and T019 work on separate backend/frontend files.

## Parallel Example: User Story 1

```text
T005 JWT unit tests in backend/tests/unit/test_dev_jwt.py
T006 session API contract tests in backend/tests/contract/test_dev_auth.py
T007 seed integration tests in backend/tests/integration/test_dev_seed.py
T008 transfer/session integration tests in backend/tests/integration/test_dev_auth_transfer.py
T009 frontend sign-in tests in frontend/src/App.test.tsx and frontend/src/services/devAuth.test.ts
```

## Parallel Example: User Story 2

```text
T016 backend disabled-mode and resolver-precedence tests in backend/tests/contract/test_dev_auth_gating.py
T017 frontend disabled-mode and logout tests in frontend/src/components/DevSignIn.test.tsx
T018 backend session-cookie deletion in backend/src/simple_bank/api/v1/dev_auth.py
T019 frontend logout flow in frontend/src/components/DevSignIn.tsx and frontend/src/App.tsx
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational configuration.
2. Complete US1 to sign in as a seeded demo profile and exercise the existing transfer flow locally.
3. Do not treat the feature as complete until US2 proves the fake path is disabled outside development/test and sign-out works.

### Incremental Delivery

1. Add the JWT dependency, environment configuration, and shared PostgreSQL URL resolution.
2. Add seed data, fake session endpoints, and the local sign-in UI; validate US1 independently.
3. Add logout and disabled-mode/real-resolver regressions; validate US2 independently.
4. Run the available tests and frontend checks in T020. Complete PostgreSQL/Alembic validation and the timed end-to-end scenario in T021 once the local database URLs are configured.
