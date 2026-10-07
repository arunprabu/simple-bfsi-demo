# Fund Transfer Plan Research

## Technology and design decisions

### Backend runtime and package management

- **Decision**: Use Python 3.12 and uv to create/manage the backend environment and
  lock dependencies.
- **Rationale**: This directly follows the project owner's selected runtime and
  package manager. Pin resolved dependencies in the project lockfile so local,
  CI, and production installations are repeatable.
- **Alternatives considered**: Poetry, pip/requirements files, and newer Python
  runtimes. These are not selected because the project explicitly requested Python
  3.12 with uv.

### HTTP service and request validation

- **Decision**: Use FastAPI with Pydantic request/response schemas. Mount the
  transfer router under `/api/v1`; keep HTTP concerns outside `TransferService`.
- **Rationale**: FastAPI provides a clear REST boundary and schema-driven validation
  and OpenAPI generation. The service class can be unit-tested without constructing
  an HTTP request.
- **Alternatives considered**: A different Python web framework or putting
  eligibility logic in route handlers. Neither aligns as well with the selected
  stack and explicit service-class requirement.

### Persistence and transaction boundaries

- **Decision**: Use PostgreSQL through SQLAlchemy 2.x and asyncpg, with Alembic
  migrations. Persist currency as `NUMERIC(18, 2)`. Execute transfer validation,
  debit, credit, and transaction insertion inside one database transaction.
- **Rationale**: PostgreSQL exact numerics avoid binary floating-point money
  errors. A single transaction ensures either all balance and history changes
  commit or none do. Row locks and a per-customer serialization lock make balance
  and daily-limit checks safe under concurrent requests.
- **Alternatives considered**: SQLite or floating-point columns were rejected for
  production correctness and concurrency behavior. Direct SQL without migration
  management was rejected in favor of explicit schema evolution.

### Transfer-rule service boundary

- **Decision**: Implement an application `TransferService` that accepts an
  authenticated customer ID, source/destination account identifiers, amount, and
  persistence unit-of-work/repository collaborators. It owns rule evaluation and
  orchestration; the route maps service outcomes to HTTP.
- **Rationale**: Pure rule decisions can be unit-tested with fakes, while
  PostgreSQL integration tests prove locking, atomicity, and persistence behavior.
  This satisfies the request to keep transfer rules in a separate service class.
- **Alternatives considered**: Embedding business decisions in FastAPI routes or
  database model hooks. Both make isolated rule testing and behavior review harder.

### Daily-limit concurrency and IST boundary

- **Decision**: Calculate a customer's completed outgoing total using the IST
  calendar-day interval converted to UTC instants. Serialize transfers for that
  customer by locking a stable customer/account-owner row, then lock both account
  rows in deterministic identifier order before checking status/balance and applying
  changes. Keep all locks until commit/rollback.
- **Rationale**: Locking only a source account does not prevent two requests from
  different source accounts from both passing the same daily-limit check. A stable
  per-customer lock serializes that check; deterministic account lock order reduces
  deadlock risk. The database transaction provides rollback if any write fails.
- **Alternatives considered**: An unlocked aggregate query can race. PostgreSQL
  serializable isolation could detect conflicting work but would require retry
  handling and still benefits from an explicit customer-level serialization strategy.
  Advisory locks are possible but couple application correctness to lock-key design.

### API contract and customer app

- **Decision**: Treat `POST /api/v1/transfers` and the documented error codes as the
  backend contract. The customer web app uses the API only. Derive the actor from
  the existing authenticated session; do not accept `customer_id` in the transfer
  body.
- **Rationale**: This meets both the specification and constitution. Keeping the
  authentication mechanism behind the existing bank session boundary avoids
  inventing an auth protocol in this feature.
- **Alternatives considered**: A new authentication scheme or direct frontend
  access to storage/services would exceed scope and violate the project's API
  boundary.

### Testing strategy

- **Decision**: Use pytest for service unit tests, API/contract tests, and
  PostgreSQL-backed integration tests. Run concurrency tests against PostgreSQL,
  not an in-memory substitute.
- **Rationale**: Every business rule must be tested. Unit tests give focused,
  fast coverage; database integration tests are necessary to prove transaction and
  lock semantics; contract tests protect `/api/v1` response shapes and error mapping.
- **Alternatives considered**: Mock-only database testing was rejected for
  concurrency/atomicity guarantees; a separate test framework is unnecessary for
  the selected Python stack.

## Explicit assumptions and deferred decisions

- The authenticated customer identity is available to the API from the bank's
  existing session integration; this repository currently contains no application
  or authentication source code.
- The specification does not define retry deduplication/idempotency. For this plan,
  each accepted HTTP submission is treated as a distinct transfer request. Whether
  the API needs an idempotency key should be decided before launch if clients can
  automatically retry transfer submissions.
- Operational deployment, expected account/customer volume, and availability SLOs
  are not specified. The plan preserves the measurable 1-second response goal and
  leaves infrastructure sizing to deployment planning.
- Database transactions record only completed transfers as specified. Failed
  attempts are returned to the caller but are not represented as completed
  transaction rows.
