#!/usr/bin/env bash
# Post-deployment smoke test for the Simple Bank backend.
# Usage: smoke-test.sh <base-url>   e.g. smoke-test.sh http://my-alb-123.eu-north-1.elb.amazonaws.com
# Needs no database or credentials: it checks the API is up and that demo
# sign-in is disabled in the deployed environment.
set -euo pipefail

BASE_URL="${1:?Usage: smoke-test.sh <base-url>}"
BASE_URL="${BASE_URL%/}"
BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE"' EXIT

fail() {
  echo "SMOKE TEST FAILED: $*" >&2
  if [[ -s "$BODY_FILE" ]]; then
    echo "Last response body:" >&2
    cat "$BODY_FILE" >&2
    echo >&2
  fi
  exit 1
}

# Prints the HTTP status; the response body is left in $BODY_FILE.
request() {
  local method="$1" path="$2" payload="${3:-}"
  local args=(--silent --show-error --max-time 15 --output "$BODY_FILE"
              --write-out '%{http_code}' --request "$method")
  if [[ -n "$payload" ]]; then
    args+=(--header 'Content-Type: application/json' --data "$payload")
  fi
  curl "${args[@]}" "${BASE_URL}${path}"
}

expect_status() {
  local expected="$1" actual="$2" label="$3"
  [[ "$actual" == "$expected" ]] || fail "$label: expected HTTP $expected, got $actual"
  echo "ok - $label (HTTP $actual)"
}

expect_json() {
  local filter="$1" label="$2"
  jq -e "$filter" "$BODY_FILE" >/dev/null || fail "$label: unexpected response"
  echo "ok - $label"
}

echo "Waiting for ${BASE_URL} to become reachable..."
curl --silent --show-error --fail --max-time 10 --output /dev/null \
  --retry 18 --retry-delay 10 --retry-all-errors --retry-connrefused \
  "${BASE_URL}/openapi.json" || fail "API did not become reachable"

status="$(request GET /openapi.json)"
expect_status 200 "$status" "OpenAPI document is served"
expect_json '.info.title == "Simple Bank Fund Transfer API"' "OpenAPI title matches"
expect_json '.paths | has("/api/v1/transfers")' "Transfers route is registered"

status="$(request GET /api/v1/dev-auth/session)"
expect_status 200 "$status" "Demo auth status endpoint responds"
expect_json '.fake_auth_enabled == false' "Fake auth is disabled"

status="$(request POST /api/v1/dev-auth/session '{"profile_id":"demo-user-1"}')"
expect_status 403 "$status" "Demo sign-in is rejected"

status="$(request POST /api/v1/transfers '{"from_account":"12345678","to_account":"87654321","amount":"25.00"}')"
expect_status 401 "$status" "Unauthenticated transfer is rejected"
expect_json '.error.code == "UNAUTHENTICATED"' "Transfer error code is stable"

echo "All smoke tests passed."
