# Fund Transfer Quickstart

This guide describes local setup and validation for the fund transfer feature.
The backend uses Python 3.12, uv, FastAPI, and PostgreSQL. The customer app uses
React and Vite and calls the backend only through `/api/v1`.

## Prerequisites

- Python 3.12 and uv
- Node.js and npm
- PostgreSQL, with separate development and test databases
- An authenticated-customer resolver supplied by the hosting bank application

## Configure and start the backend

From the backend directory, install dependencies and set `DATABASE_URL` in the
shell to the development PostgreSQL connection string. Do not store credentials in
tracked files.

```sh
cd backend
uv sync --dev
export DATABASE_URL='postgresql+asyncpg://localhost:5432/simple_bank'
uv run alembic upgrade head
uv run uvicorn simple_bank.main:app --reload
```

The API exposes `POST /api/v1/transfers`. At startup the standalone app has no
bank sign-in provider configured, so it returns `UNAUTHENTICATED` until the host
creates the app with an async `authenticated_customer_resolver` that reads the
existing session and returns its customer ID. The request body must never supply
that identity.

For a fresh or empty database, `alembic upgrade head` applies the account-opening
timestamp revisions directly. For an existing database, first apply
`alembic upgrade 0002_account_opened_at`, backfill every account's `opened_at` from
the authoritative account-opening source, then run `alembic upgrade head`. Revision
`0003_require_account_opened_at` refuses to make the field required while any rows
remain unbackfilled. Do not use migration time as an account's opening time, and do
not start the updated application until the backfill and final revision succeed.

## Start the customer app

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

The Vite development server proxies `/api/v1` requests to the local backend at
`127.0.0.1:8000`. The browser client includes same-origin session credentials and
does not connect directly to a database or internal service.

## Run backend tests

Set `TEST_DATABASE_URL` to a dedicated PostgreSQL test database. Its database name
must contain a `test` component separated by `_` or `-`, for example
`simple_bank_test`. The fixture runs Alembic migrations and truncates only the
feature tables before and after each integration/performance test; it does not
drop the database. Never point it at a development or production database.

```sh
cd backend
uv sync --dev
export TEST_DATABASE_URL='postgresql+asyncpg://localhost:5432/simple_bank_test'
uv run pytest
DATABASE_URL="$TEST_DATABASE_URL" uv run alembic check
```

Without `TEST_DATABASE_URL`, PostgreSQL integration and latency tests are
explicitly skipped. Unit and API contract tests remain runnable:

```sh
uv run pytest tests/unit tests/contract
```

The baseline test suites cover amount precision and boundaries, ownership and
account eligibility, the customer-wide daily limit using the IST calendar day,
atomic debit and credit, error-code mapping, account-number log masking, and
authenticated identity handling. The PostgreSQL concurrency tests use two
independent sessions to prove that parallel transfers cannot overspend a source
account or exceed the customer daily limit. The account-age scenarios below are
pending the follow-up implementation and test tasks.

## Account-age limit validation scenarios

After the account-age follow-up tasks are implemented, validate these cases using
the normal transfer submission path:

1. A source account opened 29 elapsed days earlier has sent Rs 40,000 during the
   current IST day; a valid Rs 10,000 transfer succeeds and brings its total to
   exactly Rs 50,000.
2. A source account opened 29 elapsed days earlier has sent Rs 50,000 that day; a
   valid Rs 1.00 transfer is declined with `DAILY_LIMIT_EXCEEDED`, and neither
   account balance nor either daily total changes.
3. A source account opened exactly 30 elapsed days earlier and its customer-wide
   total each stand at Rs 80,000; a valid Rs 20,000 transfer succeeds and brings
   both totals to Rs 1,00,000.
4. A customer's young source account has reached Rs 50,000, while a different
   mature source account has sent nothing; a Rs 50,000 transfer from the mature
   account succeeds only if the customer-wide total remains at or below
   Rs 1,00,000.
5. Concurrent transfers from a young source account must not make its daily total
   exceed Rs 50,000, and concurrent transfers across a customer's source accounts
   must not make the customer-wide total exceed Rs 1,00,000.

## Response-time acceptance profile

The phrase “normal service conditions” for the 1-second/95% target means this
repeatable test profile:

- Run on a dedicated Linux x86_64 runner with at least 2 vCPU and 4 GiB RAM.
- Run the API and PostgreSQL on the same runner; do not run unrelated
  CPU-intensive tests or benchmarks during the measurement.
- Seed 110 distinct eligible customer/source/recipient account sets with sufficient
  balances and no completed outgoing transfers that day. Use 10 sets for warm-up
  and 100 separate sets for measured requests.
- Start the API and database before timing. Send one unmeasured warm-up request for
  each of 10 clients, then have those 10 clients submit 10 measured valid transfers
  each through the loopback HTTP endpoint.
- Measure complete request-to-response time with a monotonic clock. Exclude service
  startup, database startup, fixture creation, and warm-up requests. At least 95 of
  the 100 measured responses must complete within 1 second.
- Record the runner's CPU and memory, OS, Python and PostgreSQL versions, test
  command, and measured result with the validation outcome.

## Run frontend checks

From the frontend directory:

```sh
npm ci
npm run test:ci
npm run build
npm run lint
```

The UI validates amount syntax without floating-point arithmetic, submits only
through `/api/v1/transfers`, and displays a confirmation only for a completed
transfer.

## Verified implementation results

Validated on 2026-10-07 with an isolated local PostgreSQL test database:

- Backend unit, contract, integration, and performance suites: **44 passed**.
- The prior 100-request PostgreSQL latency test passed its then-current target; it
  has not yet been rerun under the response-time profile defined above.
- Alembic reported no schema changes missing from the migration.
- Frontend tests: **10 passed**; production build and oxlint both passed.
- With no `TEST_DATABASE_URL`, all 7 PostgreSQL-only tests were explicitly skipped.

These baseline results predate the account-age follow-up and do not verify the new
Rs 50,000 source-account limit or the standardized response-time profile. Record
updated results after completing the follow-up tasks.

## Follow-up local validation status

Validated locally on 2026-10-07:

- Backend unit and contract tests: **41 passed**.
- Backend integration and performance tests: **9 skipped** because
  `TEST_DATABASE_URL` is not configured.
- Frontend tests: **10 passed**; production build and lint passed.
- Alembic reports `0003_require_account_opened_at` as the migration head; a
  database-backed migration check was not run.

The account-age PostgreSQL scenarios and the dedicated Linux response-time profile
remain unverified. Tasks T036 and T037 stay pending until those checks can run with
an isolated PostgreSQL test database and the specified benchmark runner.
