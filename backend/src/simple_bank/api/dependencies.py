from collections.abc import Awaitable, Callable

from fastapi import Request

from simple_bank.api.errors import TransferError, TransferErrorCode

AuthenticatedCustomerResolver = Callable[[Request], Awaitable[str | None]]


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
