from datetime import UTC, datetime
from typing import Any

import jwt

DEV_JWT_ISSUER = "simple-bank-dev"
DEV_JWT_AUDIENCE = "simple-bank-dev"
DEV_JWT_LIFETIME_SECONDS = 60 * 60
_ALGORITHM = "HS256"


class DevJwtCodec:
    def __init__(self, signing_key: bytes) -> None:
        if len(signing_key) < 32:
            raise ValueError("The development JWT signing key must be at least 32 bytes.")
        self._signing_key = signing_key

    def issue(
        self,
        customer_id: str,
        *,
        now: datetime | None = None,
    ) -> str:
        issued_at = int((now or datetime.now(UTC)).timestamp())
        claims: dict[str, Any] = {
            "sub": customer_id,
            "demo": True,
            "iss": DEV_JWT_ISSUER,
            "aud": DEV_JWT_AUDIENCE,
            "iat": issued_at,
            "exp": issued_at + DEV_JWT_LIFETIME_SECONDS,
        }
        return jwt.encode(claims, self._signing_key, algorithm=_ALGORITHM)

    def verify(self, token: str) -> str:
        claims = jwt.decode(
            token,
            self._signing_key,
            algorithms=[_ALGORITHM],
            issuer=DEV_JWT_ISSUER,
            audience=DEV_JWT_AUDIENCE,
            options={"require": ["sub", "demo", "iss", "aud", "iat", "exp"]},
        )
        if claims.get("demo") is not True:
            raise jwt.InvalidTokenError("Token is not a development demo session.")
        customer_id = claims.get("sub")
        if not isinstance(customer_id, str) or not customer_id:
            raise jwt.InvalidTokenError("Token subject is invalid.")
        return customer_id
