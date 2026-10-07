<!--
Sync Impact Report
Version change: none → 1.0.0
Modified principles: none (initial constitution)
Added sections: Core Principles; Technology and Interface Constraints;
Development and Compliance; Governance
Removed sections: none
Follow-up TODOs: Confirm the original ratification date.
-->
# Simple Bank Constitution

## Core Principles

### I. Decimal Money and Rounding
All monetary values and calculations MUST use decimal arithmetic; binary floating-point
types MUST NOT be used for money. Monetary values MUST be rounded to exactly two decimal
places at the applicable transaction or persistence boundary. Automated tests MUST verify
precision, rounding behavior, and relevant boundary cases for every monetary operation.

### II. Account-Number Privacy
Full account numbers MUST NOT appear in logs. When an account number is needed in a log,
the application MUST display only its last four digits in the format `XXXX1234`. Automated
tests MUST verify that logging paths redact account numbers and never emit the full value.

### III. Every Rule Is Tested
Every normative application rule MUST have an automated test that verifies its required
behavior. Tests MUST cover applicable success, failure, and boundary cases. Changes that
introduce or modify a rule MUST include or update its test; a rule without a corresponding
test is non-compliant.

### IV. Versioned API Boundary
All application API endpoints MUST begin with `/api/v1`. Automated API tests MUST verify
the versioned route prefix and the expected behavior of each endpoint.

### V. Customer Web App Uses the API
The customer web application MUST use React and Vite. It MUST access application data and
capabilities only through the `/api/v1` API; it MUST NOT bypass that API to access
databases, internal services, or other application backends directly. Automated tests
MUST verify the supported API integration and prevent direct backend access.

## Technology and Interface Constraints

The API version prefix is `/api/v1`. Changes that introduce a new API version or alter
the customer web application technology MUST be made through a constitution amendment.
Money and account-number handling MUST follow Core Principles I and II at every relevant
application boundary.

## Development and Compliance

Each feature and change MUST identify the application rules it affects and include tests
for those rules. Reviewers MUST verify that monetary operations use decimal arithmetic
and two-decimal rounding, that logs redact account numbers, that the API uses the
required prefix, and that the customer web app communicates only through the API.
Automated test results MUST be part of the change validation.

## Governance

This constitution governs project implementation and supersedes conflicting development
guidance. Amendments MUST be documented in the constitution, reviewed for their impact
on existing rules and tests, and accompanied by updates to affected tests and guidance.

The constitution version MUST follow semantic versioning: MAJOR for incompatible
governance changes or removal of a principle, MINOR for a new principle or material
expansion, and PATCH for clarifications and non-semantic refinements. Compliance MUST
be reviewed for every change through code review and relevant automated tests.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-10-06
