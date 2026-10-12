from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI

from simple_bank.api.dependencies import (
    AuthenticatedCustomerResolver,
    resolve_dev_customer_id,
)
from simple_bank.api.errors import TransferError, transfer_exception_handler
from simple_bank.api.v1.router import api_router
from simple_bank.auth.dev_jwt import DevJwtCodec
from simple_bank.config import Settings
from simple_bank.db.session import dispose_database


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await dispose_database()


def create_app(
    authenticated_customer_resolver: AuthenticatedCustomerResolver | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    fake_auth_enabled = (
        active_settings.fake_auth_enabled
        and authenticated_customer_resolver is None
    )
    dev_jwt_codec = (
        DevJwtCodec(secrets.token_bytes(32)) if fake_auth_enabled else None
    )
    resolver = authenticated_customer_resolver
    if resolver is None and fake_auth_enabled:
        resolver = resolve_dev_customer_id

    app = FastAPI(
        title="Simple Bank Fund Transfer API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.fake_auth_enabled = fake_auth_enabled
    app.state.dev_jwt_codec = dev_jwt_codec
    app.state.authenticated_customer_resolver = resolver
    app.add_exception_handler(TransferError, transfer_exception_handler)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
