from collections.abc import Awaitable, Callable

import jwt
from fastapi import Request

from simple_bank.api.errors import TransferError, TransferErrorCode
from simple_bank.auth.dev_jwt import DevJwtCodec
from simple_bank.dev_seed import DEMO_PROFILES

AuthenticatedCustomerResolver = Callable[[Request], Awaitable[str | None]]
_DEMO_CUSTOMER_IDS = frozenset(profile.customer_id for profile in DEMO_PROFILES)


async def resolve_dev_customer_id(request: Request) -> str | None:
    codec: DevJwtCodec | None = getattr(request.app.state, "dev_jwt_codec", None)
    token = request.cookies.get("dev_session")
    if codec is None or not token:
        return None

    try:
        customer_id = codec.verify(token)
    except jwt.InvalidTokenError:
        return None

    if customer_id not in _DEMO_CUSTOMER_IDS:
        return None
    return customer_id


async def get_authenticated_customer_id(request: Request) -> str:
    resolver: AuthenticatedCustomerResolver | None = getattr(
        request.app.state,
        "authenticated_customer_resolver",
        None,
    )
    if resolver is None:
        raise TransferError(TransferErrorCode.UNAUTHENTICATED)

    customer_id = await resolver(request)
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise TransferError(TransferErrorCode.UNAUTHENTICATED)

    return customer_id
