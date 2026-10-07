import asyncio
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from simple_bank.api.errors import TransferError, TransferErrorCode
from simple_bank.models import Account, Customer, Transaction
from simple_bank.repositories.transactions import TransactionRepository
from simple_bank.repositories.unit_of_work import SqlAlchemyTransferUnitOfWork
from simple_bank.services.transfers import TransferResult, TransferService


def make_account(
    account_number: str,
    customer_id: str,
    balance: str,
    account_type: str = "SAVINGS",
    opened_at: datetime = datetime(2026, 9, 1, tzinfo=UTC),
) -> Account:
    return Account(
        account_number=account_number,
        customer_id=customer_id,
        balance=Decimal(balance),
        status="ACTIVE",
        account_type=account_type,
        opened_at=opened_at,
    )


async def seed_accounts(
    sessions: async_sessionmaker[AsyncSession],
    accounts: Iterable[Account],
    transactions: Iterable[Transaction] = (),
) -> None:
    account_list = list(accounts)
    customer_ids = {account.customer_id for account in account_list}
    async with sessions() as session, session.begin():
        session.add_all(Customer(customer_id=value) for value in customer_ids)
        await session.flush()
        session.add_all(account_list)
        await session.flush()
        session.add_all(list(transactions))


async def submit_transfer(
    sessions: async_sessionmaker[AsyncSession],
    *,
    customer_id: str = "customer-1",
    from_account: str = "12345678",
    to_account: str = "87654321",
    amount: str = "125.50",
    now: datetime = datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
) -> TransferResult:
    async with sessions() as session:
        service = TransferService(
            lambda: SqlAlchemyTransferUnitOfWork(session),
            clock=lambda: now,
        )
        return await service.transfer(
            customer_id=customer_id,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
        )


@pytest.mark.integration
async def test_valid_transfer_persists_equal_movements_and_retrievable_id(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    await seed_accounts(
        pg_sessions,
        [
            make_account("12345678", "customer-1", "500.00"),
            make_account("87654321", "customer-2", "25.00", "CURRENT"),
        ],
    )

    result = await submit_transfer(pg_sessions)

    async with pg_sessions() as session:
        source = await session.get(Account, "12345678")
        recipient = await session.get(Account, "87654321")
        transaction = await TransactionRepository(session).get_by_id(
            uuid.UUID(result.transaction_id)
        )

    assert source is not None
    assert recipient is not None
    assert transaction is not None
    assert source.balance == Decimal("374.50")
    assert recipient.balance == Decimal("150.50")
    assert transaction.amount == Decimal("125.50")
    assert transaction.from_account == "12345678"
    assert transaction.to_account == "87654321"
    assert transaction.status == "COMPLETED"
    assert transaction.created_at.tzinfo is not None
    assert result.transaction_id == str(transaction.transaction_id)


@pytest.mark.integration
async def test_declined_daily_limit_transfer_leaves_state_unchanged(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    prior_transfer = Transaction(
        transaction_id=uuid.uuid4(),
        from_account="12345678",
        to_account="87654321",
        amount=Decimal("99999.50"),
        status="COMPLETED",
        created_at=datetime(2026, 10, 7, 8, 0, tzinfo=UTC),
    )
    await seed_accounts(
        pg_sessions,
        [
            make_account("12345678", "customer-1", "200.00"),
            make_account("87654321", "customer-2", "10.00"),
        ],
        [prior_transfer],
    )

    with pytest.raises(TransferError) as raised:
        await submit_transfer(pg_sessions, amount="1.00")

    assert raised.value.code is TransferErrorCode.DAILY_LIMIT_EXCEEDED
    async with pg_sessions() as session:
        source = await session.get(Account, "12345678")
        recipient = await session.get(Account, "87654321")
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )

    assert source is not None and source.balance == Decimal("200.00")
    assert recipient is not None and recipient.balance == Decimal("10.00")
    assert transaction_count == 1


@pytest.mark.integration
async def test_postgres_transaction_rolls_back_on_persistence_failure(
    pg_sessions: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_accounts(
        pg_sessions,
        [
            make_account("12345678", "customer-1", "200.00"),
            make_account("87654321", "customer-2", "10.00"),
        ],
    )

    async def fail_add(_repository, _transaction: Transaction) -> None:
        raise SQLAlchemyError("simulated persistence failure")

    monkeypatch.setattr(TransactionRepository, "add", fail_add)

    with pytest.raises(TransferError) as raised:
        await submit_transfer(pg_sessions, amount="25.00")

    assert raised.value.code is TransferErrorCode.TRANSFER_FAILED
    async with pg_sessions() as session:
        source = await session.get(Account, "12345678")
        recipient = await session.get(Account, "87654321")
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )

    assert source is not None and source.balance == Decimal("200.00")
    assert recipient is not None and recipient.balance == Decimal("10.00")
    assert transaction_count == 0


@pytest.mark.integration
async def test_ist_daily_limit_resets_at_midnight(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    prior_transfer = Transaction(
        transaction_id=uuid.uuid4(),
        from_account="12345678",
        to_account="87654321",
        amount=Decimal("100000.00"),
        status="COMPLETED",
        created_at=datetime(2026, 10, 6, 18, 29, 59, tzinfo=UTC),
    )
    await seed_accounts(
        pg_sessions,
        [
            make_account("12345678", "customer-1", "200.00"),
            make_account("87654321", "customer-2", "10.00"),
        ],
        [prior_transfer],
    )
    midnight_ist = datetime(
        2026,
        10,
        7,
        0,
        0,
        1,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )

    result = await submit_transfer(
        pg_sessions,
        amount="1.00",
        now=midnight_ist,
    )

    assert result.amount == Decimal("1.00")
    async with pg_sessions() as session:
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )
    assert transaction_count == 2


@pytest.mark.integration
async def test_concurrent_transfers_cannot_overspend_source_account(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    await seed_accounts(
        pg_sessions,
        [
            make_account("12345678", "customer-1", "100.00"),
            make_account("87654321", "customer-2", "0.00", "CURRENT"),
        ],
    )

    results = await asyncio.gather(
        submit_transfer(pg_sessions, amount="60.00"),
        submit_transfer(pg_sessions, amount="60.00"),
        return_exceptions=True,
    )

    completed = [result for result in results if isinstance(result, TransferResult)]
    declined = [result for result in results if isinstance(result, TransferError)]
    assert len(completed) == 1
    assert len(declined) == 1
    assert declined[0].code is TransferErrorCode.INSUFFICIENT_BALANCE
    async with pg_sessions() as session:
        source = await session.get(Account, "12345678")
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )
    assert source is not None and source.balance == Decimal("40.00")
    assert transaction_count == 1


@pytest.mark.integration
async def test_concurrent_source_accounts_cannot_exceed_customer_daily_limit(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    await seed_accounts(
        pg_sessions,
        [
            make_account("12345678", "customer-1", "100000.00"),
            make_account("11223344", "customer-1", "100000.00"),
            make_account("87654321", "customer-2", "0.00", "CURRENT"),
        ],
    )

    results = await asyncio.gather(
        submit_transfer(
            pg_sessions,
            from_account="12345678",
            amount="60000.00",
        ),
        submit_transfer(
            pg_sessions,
            from_account="11223344",
            amount="60000.00",
        ),
        return_exceptions=True,
    )

    completed = [result for result in results if isinstance(result, TransferResult)]
    declined = [result for result in results if isinstance(result, TransferError)]
    assert len(completed) == 1
    assert len(declined) == 1
    assert declined[0].code is TransferErrorCode.DAILY_LIMIT_EXCEEDED
    async with pg_sessions() as session:
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )
        outgoing_total = await session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
        )
    assert transaction_count == 1
    assert outgoing_total == Decimal("60000.00")


@pytest.mark.integration
async def test_concurrent_young_account_transfers_cannot_exceed_50000(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    prior_transfer = Transaction(
        transaction_id=uuid.uuid4(),
        from_account="12345678",
        to_account="87654321",
        amount=Decimal("49999.00"),
        status="COMPLETED",
        created_at=datetime(2026, 10, 7, 11, 59, tzinfo=UTC),
    )
    await seed_accounts(
        pg_sessions,
        [
            make_account(
                "12345678",
                "customer-1",
                "100.00",
                opened_at=datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
                - timedelta(days=29),
            ),
            make_account("87654321", "customer-2", "0.00", "CURRENT"),
        ],
        [prior_transfer],
    )

    results = await asyncio.gather(
        submit_transfer(pg_sessions, amount="1.00"),
        submit_transfer(pg_sessions, amount="1.00"),
        return_exceptions=True,
    )

    completed = [result for result in results if isinstance(result, TransferResult)]
    declined = [result for result in results if isinstance(result, TransferError)]
    assert len(completed) == 1
    assert len(declined) == 1
    assert declined[0].code is TransferErrorCode.DAILY_LIMIT_EXCEEDED
    async with pg_sessions() as session:
        source = await session.get(Account, "12345678")
        transaction_count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )
        source_total = await TransactionRepository(session).completed_outgoing_total_for_account(
            "12345678",
            datetime(2026, 10, 7, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC),
            datetime(2026, 10, 8, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC),
        )

    assert source is not None and source.balance == Decimal("99.00")
    assert transaction_count == 2
    assert source_total == Decimal("50000.00")


@pytest.mark.integration
async def test_young_account_and_customer_totals_reset_at_ist_midnight(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    prior_transfer = Transaction(
        transaction_id=uuid.uuid4(),
        from_account="12345678",
        to_account="87654321",
        amount=Decimal("50000.00"),
        status="COMPLETED",
        created_at=datetime(2026, 10, 6, 18, 29, 59, tzinfo=UTC),
    )
    await seed_accounts(
        pg_sessions,
        [
            make_account(
                "12345678",
                "customer-1",
                "100.00",
                opened_at=datetime(2026, 10, 7, 0, 0, 1, tzinfo=ZoneInfo("Asia/Kolkata"))
                - timedelta(days=29),
            ),
            make_account("87654321", "customer-2", "0.00", "CURRENT"),
        ],
        [prior_transfer],
    )

    result = await submit_transfer(
        pg_sessions,
        amount="1.00",
        now=datetime(2026, 10, 7, 0, 0, 1, tzinfo=ZoneInfo("Asia/Kolkata")),
    )

    assert result.amount == Decimal("1.00")
    async with pg_sessions() as session:
        customer_total = await TransactionRepository(
            session
        ).completed_outgoing_total(
            "customer-1",
            datetime(2026, 10, 7, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC),
            datetime(2026, 10, 8, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC),
        )
        source_total = await TransactionRepository(
            session
        ).completed_outgoing_total_for_account(
            "12345678",
            datetime(2026, 10, 7, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC),
            datetime(2026, 10, 8, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC),
        )

    assert customer_total == Decimal("1.00")
    assert source_total == Decimal("1.00")
