from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from simple_bank.api.v1.transfers import get_transfer_service
from simple_bank.api.v1.dev_auth import get_optional_dev_auth_session
from simple_bank.main import create_app
from simple_bank.models import Customer
from simple_bank.services.transfers import TransferResult

VALID_TRANSFER = {
    "from_account": "12345678",
    "to_account": "87654321",
    "amount": "25.00",
}


class StubSession:
    async def get(self, model: type[Customer], customer_id: str) -> Customer | None:
        if model is Customer and customer_id == "demo-customer-1":
            return Customer(customer_id=customer_id)
        return None


class StubTransferService:
    def __init__(self) -> None:
        self.customer_ids: list[str] = []

    async def transfer(
        self,
        *,
        customer_id: str,
        from_account: str,
        to_account: str,
        amount: str,
    ) -> TransferResult:
        self.customer_ids.append(customer_id)
        return TransferResult(
            transaction_id="transaction-test",
            from_account="XXXX5678",
            to_account="XXXX4321",
            amount=Decimal(amount),
            created_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        )


def override_database_session(app: FastAPI) -> None:
    async def get_test_session() -> AsyncIterator[StubSession]:
        yield StubSession()

    app.dependency_overrides[get_optional_dev_auth_session] = get_test_session


async def make_client(app: FastAPI) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


async def test_fake_auth_is_off_by_default_and_unauthenticated_transfer_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("FAKE_AUTH_ENABLED", raising=False)
    app = create_app()
    service = StubTransferService()
    app.dependency_overrides[get_transfer_service] = lambda: service

    async with await make_client(app) as client:
        status = await client.get("/api/v1/dev-auth/session")
        login = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-1"},
        )
        transfer = await client.post("/api/v1/transfers", json=VALID_TRANSFER)

    assert status.status_code == 200
    assert status.json()["fake_auth_enabled"] is False
    assert login.status_code == 403
    assert "set-cookie" not in login.headers
    assert transfer.status_code == 401
    assert transfer.json()["error"]["code"] == "UNAUTHENTICATED"
    assert service.customer_ids == []


@pytest.mark.parametrize("app_env", ["production", "staging", ""])
def test_fake_auth_configuration_is_rejected_outside_allowed_environments(
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
) -> None:
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")

    with pytest.raises(ValueError):
        create_app()


async def test_supplied_bank_resolver_takes_precedence_over_demo_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")

    async def resolve_bank_customer(_request: Request) -> str | None:
        return "bank-session-customer"
    app = create_app(authenticated_customer_resolver=resolve_bank_customer)
    app = create_app(authenticated_customer_resolver=resolve_bank_customer)
    service = StubTransferService()
    app.dependency_overrides[get_transfer_service] = lambda: service

    async with await make_client(app) as client:
        status = await client.get("/api/v1/dev-auth/session")
        login = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-1"},
        )
        transfer = await client.post("/api/v1/transfers", json=VALID_TRANSFER)

    assert status.json()["fake_auth_enabled"] is False
    assert login.status_code == 403
    assert transfer.status_code == 201
    assert service.customer_ids == ["bank-session-customer"]


async def test_logout_clears_demo_cookie_and_returns_anonymous_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")
    app = create_app()
    override_database_session(app)

    async with await make_client(app) as client:
        login = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-1"},
        )
        logout = await client.delete("/api/v1/dev-auth/session")
        status = await client.get("/api/v1/dev-auth/session")

    assert login.status_code == 200
    assert logout.status_code == 200
    assert "max-age=0" in logout.headers["set-cookie"].lower()
    assert status.json()["authenticated"] is False
