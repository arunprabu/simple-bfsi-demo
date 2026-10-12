# Development/Test Fake Sign-In Research

## Decisions

### Environment gate

- **Decision**: Enable fake sign-in only when `APP_ENV` is explicitly `development` or `test` and `FAKE_AUTH_ENABLED` is explicitly true. Treat missing or unrecognized settings as disabled; reject configuration that enables fake auth in other environments.
- **Rationale**: A backend-side gate is authoritative and cannot be bypassed by changing frontend visibility. The frontend also checks the backend session-status response before showing the demo sign-in.
- **Alternatives considered**: A frontend-only Vite flag would not protect the API. A single ambiguous default mode could accidentally enable fake sign-in. Both were rejected.

### Demo identities and seed data

- **Decision**: Seed two deterministic demo customers and eligible accounts in the existing PostgreSQL database. Expose only fixed demo-profile aliases; the backend maps an allowed alias to an existing seeded customer. The seed operation inserts missing rows only and never truncates tables or resets balances.
- **Rationale**: This lets the tester use the real transfer service and ownership checks with realistic persisted accounts, without registering real customers or adding password storage.
- **Alternatives considered**: Listing arbitrary rows from `customers` would allow a tester to impersonate any record in a misconfigured local database. A new demo-user database table or a separate identity service adds scope without helping the local workflow.

### Fake JWT and browser session

- **Decision**: Use PyJWT with a fixed allowed algorithm (`HS256`) and a random process-local signing key generated at startup when fake auth is enabled. Include only the demo customer subject, a demo marker, fixed issuer and audience, issued-at, and one-hour expiry claims. Send the token as an HttpOnly, SameSite=Lax `dev_session` cookie scoped to `/api/v1`; set `Secure` only when served over HTTPS and clear the cookie on sign-out. Do not return the token in JSON, request a password, or store a password.
- **Rationale**: The existing API client already includes same-origin credentials. A process-local key requires no committed secret and invalidates tokens on restart, which is acceptable for an explicitly local/test-only feature. JWTs are signed, not encrypted, so the token contains no secret or unrelated customer data.
- **Alternatives considered**: A hard-coded or sample signing key would create a reusable credential. An unsigned token would be forgeable. A plaintext or hashed password flow is unnecessary because users select a seeded demo profile without a password. Storing the JWT in browser local storage exposes it to JavaScript and is unnecessary for this local flow.

### Resolver and API integration

- **Decision**: Keep the current `AuthenticatedCustomerResolver` boundary. In enabled local/test mode, a new resolver validates the JWT cookie and returns its allowed demo customer. Outside that mode, keep using the supplied bank resolver or the existing unauthenticated result. Add session status, sign-in, and sign-out operations under `/api/v1/dev-auth/session`.
- **Rationale**: This reuses the existing server-side identity seam and leaves `POST /api/v1/transfers` unchanged. The frontend learns whether the demo option is available through the status operation and sends the cookie using its existing same-origin API client.
- **Alternatives considered**: Sending `customer_id` on each transfer, putting the customer ID in an unsigned header, or connecting the frontend directly to PostgreSQL would bypass the established identity boundary and were rejected.

### PostgreSQL configuration

- **Decision**: Retain `DATABASE_URL` as the preferred application setting. When it is absent, construct the async PostgreSQL URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and `POSTGRES_DB` using SQLAlchemy's URL builder. Use the same helper for application connections and Alembic migrations. Continue to require `TEST_DATABASE_URL` for PostgreSQL integration tests.
- **Rationale**: The current backend settings consume `DATABASE_URL`, while [backend/.env.example](../../backend/.env.example) contains the separate `POSTGRES_*` components. The fallback lets the local seed workflow reuse the existing example without string-concatenating credentials or weakening the test database guard.
- **Alternatives considered**: Hard-coding a connection string or editing/reading other environment files was rejected. Requiring users to duplicate all `POSTGRES_*` values into a second URL was considered more error-prone.

### Validation strategy

- **Decision**: Test JWT issue/verify and invalid claims in unit tests; environment gate, status, sign-in/out, and transfer identity in API contract tests; additive seeds with the isolated PostgreSQL integration fixture; and the sign-in UI state with Vitest.
- **Rationale**: The security boundary spans configuration, data, API, and browser behavior. Each layer needs a focused test, while the integration suite proves the seeded customer exists in PostgreSQL.
- **Alternatives considered**: Mock-only tests cannot prove database seed behavior; relying on manual browser tests would not protect the environment gate or identity mapping.

## References

- [PyJWT usage documentation](https://pyjwt.readthedocs.io/en/stable/usage.html) — encoding/decoding examples and explicit algorithm selection.
- Existing project integration points: `backend/src/simple_bank/api/dependencies.py`, `backend/src/simple_bank/main.py`, and `frontend/src/services/api.ts`.
