from datetime import UTC, datetime, timedelta
import secrets
import time

import jwt
import pytest

from simple_bank.auth.dev_jwt import (
    DEV_JWT_AUDIENCE,
    DEV_JWT_ISSUER,
    DevJwtCodec,
)


def make_claims(**overrides: object) -> dict[str, object]:
    now = int(time.time())
    return {
        "sub": "demo-customer-1",
        "demo": True,
        "iss": DEV_JWT_ISSUER,
        "aud": DEV_JWT_AUDIENCE,
        "iat": now,
        "exp": now + 3600,
        **overrides,
    }


def test_issued_token_contains_only_the_expected_one_hour_claims() -> None:
    signing_key = secrets.token_bytes(32)
    codec = DevJwtCodec(signing_key)

    token = codec.issue("demo-customer-1")
    claims = jwt.decode(
        token,
        signing_key,
        algorithms=["HS256"],
        issuer=DEV_JWT_ISSUER,
        audience=DEV_JWT_AUDIENCE,
    )

    assert codec.verify(token) == "demo-customer-1"
    assert set(claims) == {"sub", "demo", "iss", "aud", "iat", "exp"}
    assert claims["demo"] is True
    assert claims["exp"] - claims["iat"] == 3600


def test_verifier_rejects_invalid_signature() -> None:
    signing_key = secrets.token_bytes(32)
    codec = DevJwtCodec(signing_key)
    token = jwt.encode(make_claims(), secrets.token_bytes(32), algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        codec.verify(token)


def test_verifier_rejects_unexpected_algorithm() -> None:
    signing_key = secrets.token_bytes(64)
    codec = DevJwtCodec(signing_key)
    token = jwt.encode(make_claims(), signing_key, algorithm="HS512")

    with pytest.raises(jwt.InvalidTokenError):
        codec.verify(token)


@pytest.mark.parametrize(
    "claims",
    [
        make_claims(iss="unexpected-issuer"),
        make_claims(aud="unexpected-audience"),
        make_claims(demo=False),
        make_claims(sub=""),
        make_claims(exp=int((datetime.now(UTC) - timedelta(seconds=1)).timestamp())),
    ],
)
def test_verifier_rejects_invalid_claims(claims: dict[str, object]) -> None:
    signing_key = secrets.token_bytes(32)
    codec = DevJwtCodec(signing_key)
    token = jwt.encode(claims, signing_key, algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        codec.verify(token)


def test_verifier_rejects_malformed_token() -> None:
    codec = DevJwtCodec(secrets.token_bytes(32))

    with pytest.raises(jwt.InvalidTokenError):
        codec.verify("not-a-jwt")
