# Fund Transfer Data Model

This model describes the logical entities needed for the feature. Names are
conceptual; implementation mappings belong to implementation tasks and migrations.

## Customer

| Attribute | Type / constraint | Purpose |
|---|---|---|
| `customer_id` | Stable unique identifier | Account owner and subject of the daily outgoing transfer limit. |

The customer identity used for authorization is supplied by the authenticated
session, not by the transfer request body.

## Account

| Attribute | Type / constraint | Purpose |
|---|---|---|
| `account_number` | Unique identifier | Identifies an account; never log the full value. |
| `customer_id` | Required reference to Customer | Establishes ownership and daily-limit grouping. |
| `opened_at` | Required, immutable, timezone-aware timestamp stored as an instant | Authoritative account-opening instant used to calculate account age at transfer submission. Existing accounts are populated from their source-of-record opening time, not the migration time. |
| `balance` | INR `NUMERIC(18, 2)`; non-negative | Exact account balance. |
| `status` | `ACTIVE` or inactive state | Only active accounts may participate. |
| `account_type` | Account type; source must be `SAVINGS` | Enforces source account eligibility. |

Both source and recipient accounts must be active. The source account must belong
to the authenticated customer and be a savings account. The recipient may belong to
the same customer, but must be a different account.

## Transaction

| Attribute | Type / constraint | Purpose |
|---|---|---|
| `transaction_id` | Unique identifier | Stable reference returned for a completed transfer. |
| `from_account` | Required reference to Account | Debited source account. |
| `to_account` | Required reference to Account; different from source | Credited recipient account. |
| `amount` | INR `NUMERIC(18, 2)`; at least Rs 1.00 | Exact amount debited and credited. |
| `status` | `COMPLETED` for committed rows | Represents a fully completed transfer. |
| `created_at` | Timezone-aware timestamp stored as an instant | Transfer completion time; used to compute the IST daily window. |

Declined attempts do not create completed Transaction records. A committed transfer
has one Transaction row and matching source debit and destination credit. These
changes commit or roll back as one unit.

## Invariants and validation

1. Monetary request values are parsed as decimal values, never binary floats.
2. Amount is at least Rs 1.00 and contains no more than two fractional digits.
3. Persisted balances and transaction amounts use exact two-decimal storage.
4. Source and recipient identifiers differ; both accounts are active at transfer
   time.
5. The authenticated customer owns the source savings account.
6. The customer's total completed outgoing amounts in the current IST calendar day,
   including the new amount, do not exceed Rs 1,00,000.
7. The source account's completed outgoing amounts in the current IST calendar day,
   including the new amount, do not exceed Rs 50,000 when fewer than 30 elapsed days
   have passed since `opened_at` at transfer submission, or Rs 1,00,000 when at
   least 30 elapsed days have passed. Exactly 30 elapsed days uses the Rs 1,00,000
   tier. Every transfer must satisfy both this per-account limit and invariant 6.
8. A completed transaction's amount equals both the source debit and recipient
   credit.
9. A failure before commit leaves both balances and completed transaction history
   unchanged.
10. Full account numbers are not written to logs; account references in logs are
   masked to the last four digits.

## Relationships and transaction flow

```text
Customer 1 ── * Account
Account  1 ── * Transaction (as from_account)
Account  1 ── * Transaction (as to_account)
```

For a transfer, capture the submission instant, serialize the customer's limit
decisions, lock source and recipient rows in deterministic order, and revalidate
ownership, status, balance, and `opened_at`. Compute both the customer's and the
source account's completed outgoing totals for the current IST calendar day; select
the source-account tier from its elapsed age at submission. Apply debit, credit, and
Transaction insertion in one database transaction. Any failed invariant aborts the
database transaction.
