from datetime import UTC, datetime
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from simple_bank.dev_seed import DEMO_ACCOUNT_NUMBERS, seed_demo_data
from simple_bank.models import Account, Customer, Transaction


@pytest.mark.integration
async def test_demo_seed_is_additive_and_idempotent(
    pg_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")
    await seed_demo_data(pg_sessions)

    async with pg_sessions() as session, session.begin():
        source = await session.get(Account, DEMO_ACCOUNT_NUMBERS["demo-user-1"])
        recipient = await session.get(Account, DEMO_ACCOUNT_NUMBERS["demo-user-2"])
        assert source is not None
        assert recipient is not None
        source.balance = Decimal("877.65")
        session.add(
            Transaction(
                transaction_id=uuid.uuid4(),
                from_account=source.account_number,
                to_account=recipient.account_number,
                amount=Decimal("122.35"),
                status="COMPLETED",
                created_at=datetime.now(UTC),
            )
        )

    caplog.clear()
    await seed_demo_data(pg_sessions)

    async with pg_sessions() as session:
        source = await session.get(Account, DEMO_ACCOUNT_NUMBERS["demo-user-1"])
        customer_count = await session.scalar(
            select(func.count()).select_from(Customer)
        )
        account_count = await session.scalar(
            select(func.count()).select_from(Account)
        )
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )

    assert source is not None
    assert source.balance == Decimal("877.65")
    assert customer_count == 2
    assert account_count == 2
    assert transaction_count == 1
    assert all(
        account_number not in caplog.text
        for account_number in DEMO_ACCOUNT_NUMBERS.values()
    )
