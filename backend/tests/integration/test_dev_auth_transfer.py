from collections.abc import AsyncIterator
from decimal import Decimal

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from simple_bank.api.v1.dev_auth import get_optional_dev_auth_session
from simple_bank.dev_seed import DEMO_ACCOUNT_NUMBERS, seed_demo_data
from simple_bank.main import create_app
from simple_bank.models import Account


def make_app(
    monkeypatch: pytest.MonkeyPatch,
    pg_sessions: async_sessionmaker[AsyncSession],
) -> FastAPI:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with pg_sessions() as session:
            yield session

    app.dependency_overrides[get_optional_dev_auth_session] = override_session
    return app


@pytest.mark.integration
async def test_seeded_demo_session_can_transfer_as_its_customer(
    pg_sessions: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_demo_data(pg_sessions)
    app = make_app(monkeypatch, pg_sessions)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        sign_in = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-1"},
        )
        transfer = await client.post(
            "/api/v1/transfers",
            json={
                "from_account": DEMO_ACCOUNT_NUMBERS["demo-user-1"],
                "to_account": DEMO_ACCOUNT_NUMBERS["demo-user-2"],
                "amount": "25.00",
            },
        )
        forged_identity = await client.post(
            "/api/v1/transfers",
            json={
                "from_account": DEMO_ACCOUNT_NUMBERS["demo-user-1"],
                "to_account": DEMO_ACCOUNT_NUMBERS["demo-user-2"],
                "amount": "25.00",
                "customer_id": "demo-customer-2",
            },
        )

    assert sign_in.status_code == 200
    assert "dev_session=" in sign_in.headers["set-cookie"]
    assert transfer.status_code == 201
    assert transfer.json()["status"] == "COMPLETED"
    assert transfer.json()["amount"] == "25.00"
    assert forged_identity.status_code == 422

    async with pg_sessions() as session:
        source = await session.get(Account, DEMO_ACCOUNT_NUMBERS["demo-user-1"])
        recipient = await session.get(Account, DEMO_ACCOUNT_NUMBERS["demo-user-2"])

    assert source is not None
    assert recipient is not None
    assert source.balance == Decimal("975.00")
    assert recipient.balance == Decimal("1025.00")
