from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from simple_bank.api.dependencies import AuthenticatedCustomerResolver
from simple_bank.api.errors import TransferError, transfer_exception_handler
from simple_bank.api.v1.router import api_router
from simple_bank.db.session import dispose_database


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await dispose_database()


def create_app(
    authenticated_customer_resolver: AuthenticatedCustomerResolver | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Simple Bank Fund Transfer API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.authenticated_customer_resolver = authenticated_customer_resolver
    app.add_exception_handler(TransferError, transfer_exception_handler)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
