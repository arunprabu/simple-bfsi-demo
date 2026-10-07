# Feature Specification: Fund Transfer

**Feature Branch**: `001-fund-transfer`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Original user description: "Build the Fund Transfer feature described in [requirements-fund-transfer.md](../../docs/requirements-fund-transfer.md). Write user stories, numbered requirements, and Given/When/Then acceptance criteria for every rule; flag unclear items." Update request: "Accounts opened less than 30 days ago have a daily transfer limit of Rs 50,000. All other accounts keep the Rs 1,00,000 limit. Add acceptance criteria and examples."

## Clarifications

### Session 2026-10-06

- Q: How quickly should customers receive a result for a transfer submission? (FR-009) → A: At least 95% of submissions receive a result within 1 second.
- Q: Should a transfer be allowed for any positive amount in paise, or must it be at least Rs 1.00? (FR-001) → A: The amount must be at least Rs 1.00.

## User Scenarios & Testing

### User Story 1 - Transfer Money to Another Bank Customer (Priority: P1)

A customer transfers money from their savings account to a different Simple Bank
account and receives the outcome and a transaction reference.

**Why this priority**: Completing a valid transfer is the central value of the feature.

**Independent Test**: With an authenticated customer, an active savings account with
sufficient funds, and a different active Simple Bank account, submit an eligible
transfer and verify the debit, credit, confirmation, and saved transaction reference.

**Acceptance Scenarios**:

1. **Given** the customer has an active savings account with sufficient balance and
   the recipient has a different active Simple Bank account, **When** the customer
   submits an amount of at least Rs 1.00 within the daily limit, **Then** the source is debited
   and the recipient is credited by that amount, and the customer receives a
   successful result with a transaction ID.
2. **Given** an eligible transfer has completed, **When** the customer receives its
   result, **Then** the transfer is saved with a unique transaction ID and the result
   is returned within the defined quick-response target.

---

### User Story 2 - Avoid Invalid or Over-Limit Transfers (Priority: P1)

A customer is told why a transfer cannot proceed when the amount, available balance,
daily limit, account relationship, or account status makes it ineligible.

**Why this priority**: Preventing unauthorized or invalid movement of funds protects
customers and the bank.

**Independent Test**: Submit transfers that independently violate each eligibility
rule and verify that each is declined, the reason is clear, and neither account
balance changes.

**Acceptance Scenarios**:

1. **Given** the requested amount is less than Rs 1.00, **When** the customer submits
   the transfer, **Then** the transfer is declined and no funds move.
2. **Given** the source account lacks sufficient available balance, **When** the
   customer submits the transfer, **Then** the transfer is declined and no funds move.
3. **Given** the customer's aggregate daily limit or the source account's applicable
   age-based daily limit has been reached, **When** the customer submits another
   transfer that would exceed an applicable limit, **Then** the transfer is declined
   and no funds move.
4. **Given** the source and recipient identify the same account, **When** the
   customer submits the transfer, **Then** the transfer is declined and no funds move.
5. **Given** either account is inactive or the recipient is not a Simple Bank
   account, **When** the customer submits the transfer, **Then** the transfer is
   declined and no funds move.
6. **Given** the source savings account was opened 29 elapsed days ago and its
   completed outgoing transfers for the current IST day total Rs 40,000, **When**
   the customer submits Rs 10,000 and the customer-wide total remains within
   Rs 1,00,000, **Then** the transfer may complete and bring the source-account
   total to exactly Rs 50,000.
7. **Given** the source savings account was opened less than 30 elapsed days ago
   and has already reached Rs 50,000 in completed outgoing transfers that day,
   **When** the customer submits another valid transfer, **Then** it is declined
   without moving funds.
8. **Given** the source savings account was opened exactly 30 elapsed days ago and
   both its and the customer's completed outgoing totals are Rs 80,000 for the
   current IST day, **When** the customer submits Rs 20,000 and all other
   requirements pass, **Then** the transfer may complete and bring both totals to
   Rs 1,00,000.
9. **Given** the customer's source account opened less than 30 elapsed days ago has
   reached Rs 50,000 and a different source account open at least 30 elapsed days
   has no outgoing transfers that day, **When** the customer submits Rs 50,000 from
   the mature account and the customer's aggregate total remains within
   Rs 1,00,000, **Then** the younger account's limit does not prevent the transfer.

### Edge Cases

- A transfer equal to the available source balance is eligible if all other rules
  pass; a transfer even slightly above it is declined.
- The minimum permitted transfer is Rs 1.00; a smaller positive amount is declined.
- A customer's completed outgoing transfers across all savings accounts may total
  exactly Rs 1,00,000 in an IST calendar day; a transfer that would exceed this
  aggregate is declined.
- A source savings account that is less than 30 elapsed days old at submission has
  a per-account daily limit of Rs 50,000. A transfer bringing its total to exactly
  Rs 50,000 is allowed; one that would take it over is declined.
- At exactly 30 elapsed days since opening, a source savings account uses the
  standard Rs 1,00,000 per-account daily limit.
- Both the customer aggregate and each source account's daily total reset at
  midnight India Standard Time (IST).
- A failed or declined transfer does not change either balance and does not count
  toward either daily transfer total.
- A transfer between two different accounts owned by the same customer is allowed
  when both accounts are otherwise eligible; only a transfer to the same account is
  prohibited.
- When a customer has multiple source accounts, the account-age limit applies only
  to the source account used for that transfer; the customer-wide Rs 1,00,000
  aggregate still applies across all their savings accounts.
- A destination that does not identify an existing Simple Bank account is declined.
- Concurrent submissions must not cause the customer or a source account to exceed
  an applicable daily limit or spend more than the available balance.
- Amounts with more than two decimal places are declined without changing balances
  or counting toward the daily limit.

## Requirements

### Functional Requirements

1. **FR-001 — Positive amount**: The system MUST accept only transfer amounts of at
   least Rs 1.00.
   - **AC-001** — **Given** a transfer amount is less than Rs 1.00, **When** the
     customer submits it, **Then** the system declines the transfer without changing
     either account balance.
   - **AC-002** — **Given** the amount is at least Rs 1.00 and all other requirements
     pass, **When** the customer submits the transfer, **Then** this amount rule does
     not prevent the transfer.

2. **FR-002 — Sufficient balance**: The system MUST decline a transfer when its amount
   exceeds the source savings account's available balance.
   - **AC-003** — **Given** the requested amount exceeds the available source balance,
     **When** the customer submits the transfer, **Then** the system declines it and
     neither account balance changes.
   - **AC-004** — **Given** the requested amount equals the available source balance
     and all other requirements pass, **When** the customer submits the transfer,
     **Then** the transfer may complete and leave the source balance at Rs 0.00.

3. **FR-003 — Customer daily limit**: The system MUST ensure a customer's completed
   outgoing transfers do not total more than Rs 1,00,000 during one India Standard
   Time (IST) calendar day.
   - **AC-005** — **Given** a customer's completed transfer total for the applicable
     day is Rs 80,000, **When** the customer submits a transfer for Rs 20,000 and all
     other requirements pass, **Then** the transfer may complete.
   - **AC-006** — **Given** a customer's completed transfer total for the applicable
     day is Rs 80,000, **When** the customer submits a transfer for more than
     Rs 20,000, **Then** the system declines it without changing either balance.
   - **AC-007** — **Given** a transfer has been declined, **When** the system
     calculates the customer's completed transfer total, **Then** the declined amount
     is not included.

4. **FR-004 — Different source and recipient accounts**: The system MUST decline a
   transfer when the source and recipient are the same account.
   - **AC-008** — **Given** the source and recipient account identifiers are the same,
     **When** the customer submits the transfer, **Then** the system declines it and
     no funds move.
   - **AC-009** — **Given** the source and recipient are different accounts, **When**
     the customer submits a transfer and all other requirements pass, **Then** this
     rule does not prevent the transfer, even if both accounts belong to the same
     customer.

5. **FR-005 — Simple Bank recipient**: The system MUST permit transfers only to an
   existing Simple Bank account.
   - **AC-010** — **Given** the recipient does not identify an existing Simple Bank
     account, **When** the customer submits the transfer, **Then** the system declines
     it and no funds move.
   - **AC-011** — **Given** the recipient identifies a different Simple Bank account,
     **When** the customer submits the transfer and all other requirements pass,
     **Then** this rule does not prevent the transfer.

6. **FR-006 — Active accounts**: The system MUST require both the source savings
   account and recipient account to be active when a transfer is submitted.
   - **AC-012** — **Given** either account is inactive, **When** the customer submits
     the transfer, **Then** the system declines it and neither balance changes.
   - **AC-013** — **Given** both accounts are active, **When** the customer submits
     the transfer and all other requirements pass, **Then** this rule does not prevent
     the transfer.

7. **FR-007 — Complete movement of funds**: For each completed transfer, the system
   MUST debit the source and credit the recipient by the same amount. A transfer MUST
   complete in full or leave both balances unchanged.
   - **AC-014** — **Given** an eligible transfer for Rs 125.50 completes, **When** the
     customer and recipient balances are checked, **Then** the source is lower by
     Rs 125.50 and the recipient is higher by Rs 125.50.
   - **AC-015** — **Given** a transfer cannot complete, **When** the result is returned,
     **Then** neither the source nor recipient balance has changed.

8. **FR-008 — Unique saved transfer record**: Every completed transfer MUST have a
   unique transaction ID and a saved record that can be retrieved by that ID.
   - **AC-016** — **Given** a transfer completes, **When** its result is returned,
     **Then** it includes a transaction ID and the corresponding transfer record can
     be retrieved.
   - **AC-017** — **Given** multiple transfers have completed, **When** their saved
     records are examined, **Then** each has a distinct transaction ID.

9. **FR-009 — Prompt result**: The system MUST return a clear success or decline
   result to the customer within 1 second for at least 95% of transfer submissions
   under normal service conditions.
   - **AC-018** — **Given** a transfer submission is processed under normal service
     conditions, **When** the customer submits it, **Then** at least 95 out of 100
     submissions receive a clear success or decline result within 1 second.
   - **AC-019** — **Given** a transfer is declined, **When** its result is returned,
     **Then** the result identifies the applicable reason in language the customer
     can understand.

10. **FR-010 — Monetary precision**: The system MUST use exact decimal arithmetic for
    transfer amounts, accept no more than two decimal places, and round monetary
    values to two decimal places at the applicable transaction boundary. The system
    MUST decline amounts with more than two decimal places rather than silently
    changing the requested amount.
    - **AC-020** — **Given** a valid transfer amount of Rs 123.45, **When** it is
      checked, debited, credited, and saved, **Then** each value is exactly Rs 123.45
      to two decimal places, without floating-point precision artifacts.
    - **AC-021** — **Given** a submitted amount has more than two decimal places,
      **When** the customer submits it, **Then** the system declines it without
      changing either balance or counting it toward the daily limit.

11. **FR-011 — Account-number privacy in logs**: The system MUST NOT log a full
    account number. If a log needs to identify an account, it MUST show only the last
    four digits in the format `XXXX1234`.
    - **AC-022** — **Given** a transfer involving account number `12345678` produces
      application logs, **When** those logs are inspected, **Then** they contain no
      full account number and any account reference is masked as `XXXX5678`.

12. **FR-012 — Transfer API contract**: The system MUST expose transfer submission
    through `POST /api/v1/transfers`, accept the request fields defined in the API
    section, and return the documented success or error response.
    - **AC-023** — **Given** an authenticated customer submits a valid request with
      `from_account`, `to_account`, and `amount`, **When** the request completes,
      **Then** the endpoint returns HTTP 201 with a transaction ID, completed status,
      amount, masked account references, and creation timestamp.
    - **AC-024** — **Given** a transfer request fails a documented validation or
      account rule, **When** the endpoint returns the result, **Then** its HTTP status
      and error code match the API error mapping and its message is customer-safe.

13. **FR-013 — Transfer data record**: The system MUST maintain the Account and
    Transaction information defined in the Data section for each completed transfer.
    - **AC-025** — **Given** a transfer completes, **When** its record and related
      accounts are examined, **Then** the record has a unique ID, source, destination,
      exact two-decimal amount, completed status, and creation time, and each account
      has its account number, owner, authoritative opening timestamp, balance,
      status, and type.
14. **FR-014 — Account-age-based daily limit**: The system MUST limit each source
    savings account's completed outgoing transfers per IST calendar day to
    Rs 50,000 when fewer than 30 elapsed days have passed since the account was
    opened at transfer submission. When at least 30 elapsed days have passed, the
    account's per-day limit is Rs 1,00,000. This limit applies only to the source
    account used for the transfer; each transfer MUST also satisfy the existing
    customer-wide Rs 1,00,000 limit in FR-003.
    - **AC-026** — **Given** the source savings account was opened less than 30
      elapsed days ago and its completed outgoing transfers for the current IST day
      total Rs 40,000, **When** the customer submits Rs 10,000 and the customer-wide
      total remains within Rs 1,00,000, **Then** the transfer may complete and bring
      the source account's total to exactly Rs 50,000.
    - **AC-027** — **Given** the source savings account was opened less than 30
      elapsed days ago and its completed outgoing transfers for the current IST day
      total Rs 50,000, **When** the customer submits a valid Rs 1.00 transfer and the
      customer-wide total is still below Rs 1,00,000, **Then** the system declines
      it without changing either balance or either daily total.
    - **AC-028** — **Given** the source savings account was opened exactly 30
      elapsed days ago and both its and the customer's completed outgoing totals
      for the current IST day are Rs 80,000, **When** the customer submits a
      transfer for Rs 20,000 and all other requirements pass, **Then** the transfer
      may complete and bring both totals to Rs 1,00,000.
    - **AC-029** — **Given** the customer's source account opened less than 30
      elapsed days ago has reached its Rs 50,000 limit and a different source
      savings account has been open at least 30 elapsed days with no outgoing
      transfers that day, **When** the customer submits Rs 50,000 from the mature
      account and the customer's aggregate total will not exceed Rs 1,00,000,
      **Then** the age-based limit on the first account does not prevent the
      transfer.

## API

### Submit a Transfer

- **Method and path**: `POST /api/v1/transfers`
- **Content type**: JSON
- The authenticated customer identity comes from the existing sign-in session; the
  request MUST NOT accept a caller-supplied `customer_id`.

#### Request fields

| Field | Type | Required | Meaning and validation |
|---|---|---:|---|
| `from_account` | String | Yes | Source savings account number owned by the authenticated customer. |
| `to_account` | String | Yes | Existing, different Simple Bank recipient account number. |
| `amount` | Decimal string | Yes | INR amount of at least Rs 1.00 with no more than two fractional digits. |

Example request:

```json
{
  "from_account": "source-account-number",
  "to_account": "recipient-account-number",
  "amount": "125.50"
}
```

#### Successful response

The endpoint MUST return HTTP `201 Created` after the transfer is completed and
saved.

| Field | Type | Meaning |
|---|---|---|
| `transaction_id` | String | Unique identifier for the saved transfer. |
| `status` | String | `COMPLETED`. |
| `from_account` | String | Source account reference masked to its last four digits. |
| `to_account` | String | Recipient account reference masked to its last four digits. |
| `amount` | Decimal string | Completed transfer amount, with two fractional digits. |
| `created_at` | String | ISO 8601 timestamp including its UTC offset. |

Example response:

```json
{
  "transaction_id": "txn-0001",
  "status": "COMPLETED",
  "from_account": "XXXX1234",
  "to_account": "XXXX5678",
  "amount": "125.50",
  "created_at": "2026-10-06T12:00:00Z"
}
```

#### Error response and codes

An error response MUST use the following JSON shape and MUST NOT indicate that funds
moved when the transfer was declined or could not complete:

```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "The source account does not have enough available funds."
  }
}
```

| HTTP status | Error code | Condition |
|---:|---|---|
| 400 | `INVALID_AMOUNT` | Amount is below Rs 1.00, non-positive, or has more than two decimal places. |
| 400 | `SAME_ACCOUNT` | Source and recipient are the same account. |
| 404 | `ACCOUNT_NOT_FOUND` | The recipient does not identify an existing Simple Bank account. |
| 409 | `ACCOUNT_INACTIVE` | The source or recipient account is inactive. |
| 409 | `INSUFFICIENT_BALANCE` | The source account does not have enough available funds. |
| 409 | `DAILY_LIMIT_EXCEEDED` | The transfer would exceed the customer's Rs 1,00,000 aggregate for the IST calendar day or the source account's age-based daily limit (Rs 50,000 if less than 30 days old; otherwise Rs 1,00,000). |
| 500 | `TRANSFER_FAILED` | The transfer could not complete; neither account balance is changed. |

`ACCOUNT_NOT_FOUND` and `TRANSFER_FAILED` are included to cover recipient lookup and
all-or-nothing transfer failures in addition to the requested error codes. Error
messages MUST be safe for customers and MUST NOT contain full account numbers.

## Data

### Customer

- `customer_id`: Customer identifier used to establish account ownership and
  aggregate the daily outgoing transfer limit. The API derives the initiating
  customer from the authenticated session.

### Account

| Field | Meaning and constraints |
|---|---|
| `account_number` | Unique account identifier; full values MUST NOT appear in logs. |
| `customer_id` | Identifier of the account owner; the source owner MUST match the authenticated customer. |
| `opened_at` | Timestamp when the account was opened; used to determine its age at transfer submission. |
| `balance` | INR monetary value using exact decimal arithmetic and two decimal places. |
| `status` | Account state; transfer requires `ACTIVE`. |
| `account_type` | Account kind; the source account MUST be `SAVINGS`. |

### Transaction

| Field | Meaning and constraints |
|---|---|
| `transaction_id` | Unique identifier for the completed transfer. |
| `from_account` | Reference to the source Account. |
| `to_account` | Reference to the recipient Account. |
| `amount` | INR value moved, using exact decimal arithmetic and two decimal places. |
| `status` | `COMPLETED` for a saved transfer. |
| `created_at` | Time the transfer completed, represented as an ISO 8601 timestamp including its UTC offset. |

Declined attempts do not create completed Transaction records. A saved Transaction
represents the full debit and credit; partial transfers are not permitted.

## Examples

| # | Source / recipient | Amount and starting conditions | Expected result |
|---:|---|---|---|
| 1 | Active source `…1234` to different active recipient `…5678` | Rs 125.50; source balance Rs 500.00; daily total Rs 0.00 | HTTP 201; `COMPLETED`; unique transaction ID saved; source Rs 374.50 and recipient credited Rs 125.50. |
| 2 | Active source `…1234` to active recipient `…5678` | Rs 0.50 | HTTP 400 `INVALID_AMOUNT`; no balance change and no completed transfer record. |
| 3 | Active source `…1234` to active recipient `…5678` | Rs 125.50; source balance Rs 100.00 | HTTP 409 `INSUFFICIENT_BALANCE`; no balance change. |
| 4 | Active source `…1234` (open at least 30 days) to active recipient `…5678` | Rs 1.01; customer's completed outgoing total for the IST day is Rs 99,999.00; this source account's total is Rs 0.00 | HTTP 409 `DAILY_LIMIT_EXCEEDED`; no balance change. |
| 5 | Active account `…1234` to the same account `…1234` | Rs 10.00 | HTTP 400 `SAME_ACCOUNT`; no balance change. |
| 6 | Active source account `…1234` (opened 29 elapsed days earlier) to active recipient `…5678` | Rs 10,000; source-account total Rs 40,000; customer-wide total Rs 40,000 | HTTP 201; transfer completes and the source-account total becomes exactly Rs 50,000. |
| 7 | Active source account `…1234` (opened 29 elapsed days earlier) to active recipient `…5678` | Rs 1.00; source-account total Rs 50,000; customer-wide total Rs 50,000 | HTTP 409 `DAILY_LIMIT_EXCEEDED`; no balance change and neither total includes the declined amount. |
| 8 | Active source account `…1234` (opened exactly 30 elapsed days earlier) to active recipient `…5678` | Rs 20,000; source-account and customer-wide totals are each Rs 80,000 | HTTP 201; transfer completes and both totals become exactly Rs 1,00,000. |
| 9 | Customer's young source account `…1234` has reached Rs 50,000; mature source account `…5678` is active | Rs 50,000 from the mature source; its total is Rs 0.00 and the customer's aggregate is Rs 50,000 | HTTP 201; transfer completes from the mature source and the customer-wide total becomes Rs 1,00,000. |

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of completed transfers debit and credit the two accounts by the
  same amount, to two decimal places; declined transfers change neither balance.
- **SC-002**: No customer can complete transfers totaling more than Rs 1,00,000 in
  one IST calendar day.
- **SC-003**: 100% of completed transfers have a distinct transaction ID and a
  retrievable saved record.
- **SC-004**: At least 95% of transfer submissions return a clear success or decline
  result within 1 second under normal service conditions.
- **SC-005**: Transfer log checks find zero full account numbers; any logged account
  reference displays only its last four digits.
- **SC-006**: No source savings account opened less than 30 elapsed days ago
  completes outgoing transfers totaling more than Rs 50,000 in an IST calendar day;
  source accounts at least 30 elapsed days old retain the Rs 1,00,000 per-account
  limit, subject to the existing Rs 1,00,000 customer-wide aggregate.

## Assumptions

- Amounts and the daily limit are in Indian rupees (INR); Rs 1,00,000 is INR 100,000.
- The minimum permitted transfer amount is Rs 1.00.
- The customer is authenticated by the existing bank experience and may initiate a
  transfer only from their own savings account.
- Each account's `opened_at` is the authoritative, timezone-aware instant when the
  bank opened it; existing accounts use their source-of-record opening instant.
  Account age is measured as elapsed time from `opened_at` to transfer submission;
  exactly 30 elapsed days qualifies for the standard limit.
- The Rs 50,000 limit is per source savings account and supplements the existing
  Rs 1,00,000 customer-wide aggregate across the customer's savings accounts.
- The customer-wide aggregate and each source account's daily outgoing total use an
  IST calendar day. Only completed transfers count toward either total.
- Transfer amounts with more than two decimal places are rejected; accepted monetary
  values use exact decimal arithmetic and two decimal places.
- "Quick response" means a clear result within 1 second for at least 95% of
  submissions under normal service conditions.
- Only completed transfers require a saved transfer record and transaction ID.
  Declined attempts do not change balances or count as completed transfers.
- No transfer fee is specified; the amount debited from the source equals the amount
  credited to the recipient.
- Transfers to a different account owned by the same customer are permitted when all
  other requirements pass.
- The project constitution's monetary-precision and account-number logging rules
  apply to this feature.