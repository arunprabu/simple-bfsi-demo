# Development/Test Fake Sign-In Data Model

This feature reuses existing Customer and Account records. It does not add a password field, auth table, or persistent session table.

## Demo Profile

A non-secret local label that maps to one allowlisted demo customer. `demo-user-1` maps to `demo-customer-1`, and `demo-user-2` maps to `demo-customer-2`. Profiles are available only when fake auth is enabled in development or test.

| Attribute | Type / constraint | Purpose |
|---|---|---|
| `profile_id` | Stable allowlisted string (`demo-user-1` or `demo-user-2`) | Identifies the demo option selected in the local sign-in UI. |
| `label` | Non-sensitive display text | Helps the tester distinguish seeded demo profiles. |
| `customer_id` | Required reference to an existing Customer (`demo-customer-1` or `demo-customer-2`) | Subject used when the backend issues and verifies the demo session. |

The profile identifier is not a password or a credential. The backend must resolve it through the allowlist and confirm that its Customer record exists before issuing a token.

## Customer

The feature uses the existing `Customer` entity and its stable `customer_id`. Demo seed records are clearly identifiable as test data and are never created in a production environment.

## Account

The feature uses existing Account records for the demo flow.

| Attribute | Constraint used by this feature |
|---|---|
| `account_number` | Unique synthetic test value; never write the full value to logs. |
| `customer_id` | Required existing Customer reference. |
| `opened_at` | Required timezone-aware timestamp, consistent with the existing account model. |
| `balance` | Exact two-decimal INR value; seeded and handled with Decimal semantics. |
| `status` | Demo transfer accounts are `ACTIVE`. |
| `account_type` | At least one demo source account is `SAVINGS`; recipient must be a different account. |

At least two demo customers and a source/recipient account pair are seeded so a tester can exercise ownership and transfer rules. Seeded source accounts have sufficient balance for an otherwise eligible transfer. The seed process inserts missing rows only; it does not reset existing balances or delete transactions.

## Demo JWT Session

The signed token is an in-memory credential for this local/test feature; it is not encrypted and must not contain passwords, full account numbers, or other customer data.

| Claim / property | Constraint | Purpose |
|---|---|---|
| `sub` | Existing allowlisted demo `customer_id` | Establishes the authenticated customer identity. |
| `demo` | Boolean `true` | Distinguishes the local/test token from any bank session. |
| `iss` / `aud` | Fixed local issuer and audience | Restricts token acceptance to this application and fake-auth flow. |
| `iat` | Required issued-at timestamp | Supports token age validation. |
| `exp` | Required; one hour after issue | Limits token lifetime. |
| Signature | HS256, verified with the process-local generated key | Prevents changing the token subject without detection. |
| Browser cookie | `dev_session`; HttpOnly, SameSite=Lax, path `/api/v1`; Secure when served over HTTPS | Sends the session to the same-origin API without exposing it to frontend JavaScript. |

No token or customer identity is accepted in transfer form fields. The transfer API continues to derive identity from the verified resolver result.

## State Transitions

```text
Demo profile absent ──seed──> Available
Anonymous tester ──successful demo sign-in──> Active demo session
Active demo session ──sign-out or token expiry──> Anonymous tester
Unavailable profile/data or disabled fake auth ──sign-in attempt──> Anonymous tester
```

## Validation Rules

1. Fake sign-in is enabled only when the environment is explicitly `development` or `test` and the fake-auth flag is true.
2. Only allowlisted demo profile identifiers may be selected.
3. The profile must map to an existing seeded Customer before a token is issued.
4. JWT verification requires the expected signature algorithm, issuer/audience, demo marker, and non-expired `exp`.
5. Missing, expired, malformed, or invalid sessions do not authenticate transfer requests.
6. A sign-out clears the browser cookie; subsequent transfer requests without a valid cookie receive the existing unauthenticated result.
7. The seed command is additive and gated to local/test environments. Automated tests continue to use the dedicated `TEST_DATABASE_URL` whose name contains a test component.
