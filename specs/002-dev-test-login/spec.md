# Feature Specification: Development/Test Fake Sign-In

**Feature Branch**: `Not created`

**Created**: 2026-10-12

**Status**: Draft

**Input**: Add a fake sign-in flow so the fund-transfer web app can be tested locally. Fake sign-in is limited to development and automated testing, uses existing demo customer and account data, and must not replace real authentication outside those environments.

## User Scenarios & Testing

### User Story 1 - Sign In to the Local Test App (Priority: P1)

A developer or tester opens the local Simple Bank app, selects the clearly labeled demo sign-in option, and reaches the existing transfer screen without entering real credentials or depending on an external sign-in provider.

**Why this priority**: The transfer interface cannot be tested end to end without a local authenticated identity.

**Independent Test**: In a permitted development or test environment with demo customer and account data available, sign in as the demo customer, submit an otherwise eligible transfer, and verify that the normal transfer rules and confirmation apply to that customer.

**Acceptance Scenarios**:

1. **Given** fake sign-in is explicitly permitted and a designated demo customer with eligible accounts is available, **When** the tester chooses the demo sign-in option, **Then** the tester reaches the transfer screen as that customer without entering a real password.
2. **Given** a demo customer is signed in, **When** the tester submits a transfer, **Then** the transfer is evaluated for the signed-in customer and the existing transfer rules remain in effect.
3. **Given** no demo customer is available or the local data store cannot be reached, **When** the tester attempts to sign in, **Then** the app explains that demo sign-in is unavailable and does not create an authenticated session.

---

### User Story 2 - Preserve Authentication Outside Local Testing (Priority: P1)

A customer using the bank application outside development or automated testing continues to use the bank's real sign-in experience; the local fake sign-in cannot create a production session.

**Why this priority**: A demo sign-in must never become a way to impersonate a customer in a real banking environment.

**Independent Test**: Attempt to use fake sign-in outside an explicitly permitted development or test environment and verify that no authenticated session is created and an unsigned transfer is rejected without moving funds.

**Acceptance Scenarios**:

1. **Given** the application is not in an explicitly permitted development or test environment, **When** a user attempts fake sign-in, **Then** the attempt is unavailable or rejected and creates no authenticated session.
2. **Given** the user has no valid bank or demo session, **When** the user submits a transfer, **Then** the transfer is rejected as unauthenticated and neither account balance changes.
3. **Given** a demo customer is signed in, **When** the tester signs out, **Then** the demo session ends and subsequent transfer attempts are rejected as unauthenticated.

### Edge Cases

- The demo customer or its required accounts have not been prepared.
- The local data store is unavailable during sign-in.
- Fake sign-in is requested when the environment is not explicitly permitted.
- A session is missing, expired, or ended by sign-out when a transfer is submitted.
- A transfer request attempts to substitute a different customer identity from the identity established at sign-in.
- A user attempts to enter real credentials into the fake sign-in flow.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST make fake sign-in available only in an explicitly permitted development or automated test environment. It MUST NOT create a fake authenticated session in any other environment.
  - **AC-001** — **Given** the application is explicitly configured for local development or automated testing, **When** a tester opens the app, **Then** a clearly labeled demo sign-in option is available.
  - **AC-002** — **Given** the application is not in an explicitly permitted environment, **When** a fake sign-in is attempted, **Then** no authenticated session is created.

- **FR-002**: Fake sign-in MUST identify only a designated demo customer whose record is available in the development or test data. It MUST NOT request or store a real customer password or credential.
  - **AC-003** — **Given** a designated demo customer is available, **When** the tester completes fake sign-in, **Then** the resulting identity corresponds to that demo customer and the app identifies the session as a demo session.
  - **AC-004** — **Given** the requested demo identity is not designated or cannot be resolved, **When** sign-in is attempted, **Then** sign-in fails with a clear message and no session is created.

- **FR-003**: A transfer submitted during a demo session MUST use the customer identity established by that session. A caller MUST NOT be able to change the transfer identity by supplying a customer identifier with transfer details.
  - **AC-005** — **Given** a tester is signed in as a demo customer, **When** a transfer is submitted, **Then** the transfer uses that session's customer identity and cannot be used to act as another customer.

- **FR-004**: The system MUST end a demo session when the tester signs out. A transfer submitted without a valid session MUST be rejected as unauthenticated without changing balances or creating a completed transfer.
  - **AC-006** — **Given** a demo session has ended or is no longer valid, **When** a transfer is submitted, **Then** the system returns the unauthenticated result and no funds move.

- **FR-005**: The development or test setup MUST provide a designated demo customer with an active source savings account and a different active recipient account suitable for exercising the existing transfer flow.
  - **AC-007** — **Given** the documented local test setup has completed, **When** the tester signs in as the demo customer, **Then** the available demo data permits at least one valid transfer attempt subject to the existing fund-transfer rules.

- **FR-006**: If required demo data or the local data store is unavailable, the system MUST report the setup problem clearly and MUST NOT silently assign an identity or bypass authentication.
  - **AC-008** — **Given** required demo data cannot be loaded, **When** fake sign-in is attempted, **Then** the tester receives an actionable failure result and no authenticated session is created.

### Key Entities

- **Demo customer**: A designated, non-production Simple Bank customer used only to exercise the local test experience; it has the existing account ownership and transfer eligibility rules.
- **Demo session**: The active sign-in state associated with a designated demo customer; it can be ended by signing out and is not a real customer credential.
- **Demo accounts**: The existing source and recipient accounts prepared for the demo customer to exercise the fund-transfer flow.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A tester with prepared demo data can reach the transfer screen within 30 seconds of opening the local app, without entering a real password.
- **SC-002**: 100% of fake sign-in attempts outside explicitly permitted development or test environments create no authenticated session.
- **SC-003**: 100% of transfer attempts made without a valid session are rejected as unauthenticated, with no balance changes.
- **SC-004**: In a prepared local test scenario, a signed-in demo customer can complete an otherwise eligible transfer and see its completion confirmation.
- **SC-005**: The fake sign-in screen clearly identifies the session as a demo/test identity and never requests real customer credentials.

## Assumptions

- Real bank authentication remains authoritative outside local development and automated testing.
- Fake sign-in is a local testing aid, not a production customer feature or a substitute for customer authentication.
- Development or test data can include a designated demo customer and eligible accounts without changing production customer data.
- The existing fund-transfer flow derives the initiating customer from the active session and applies all existing ownership, balance, account-status, and daily-limit rules.
- The project already provides local database configuration; the feature reuses that configuration and does not introduce real customer credentials.
