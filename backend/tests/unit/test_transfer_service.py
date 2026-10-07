import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import SQLAlchemyError

from simple_bank.api.errors import TransferError, TransferErrorCode
from simple_bank.services.transfers import TransferService

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


@dataclass
class MemoryAccount:
    account_number: str
    customer_id: str
    balance: Decimal
    status: str = "ACTIVE"
    account_type: str = "SAVINGS"
    opened_at: datetime = field(default_factory=lambda: NOW - timedelta(days=30))


@dataclass
class MemoryTransaction:
    transaction_id: uuid.UUID
    from_account: str
    to_account: str
    amount: Decimal
    status: str
    created_at: datetime


@dataclass
class MemoryStore:
    customers: set[str] = field(default_factory=lambda: {"customer-1", "customer-2"})
    accounts: dict[str, MemoryAccount] = field(default_factory=dict)
    transactions: list[MemoryTransaction] = field(default_factory=list)
    fail_on_add: bool = False


class MemoryAccountRepository:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    async def lock_customer(self, customer_id: str) -> str | None:
        return customer_id if customer_id in self.store.customers else None

    async def lock_accounts(self, account_numbers: list[str]) -> list[MemoryAccount]:
        return [
            self.store.accounts[number]
            for number in sorted(set(account_numbers))
            if number in self.store.accounts
        ]


class MemoryTransactionRepository:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    async def completed_outgoing_total(
        self,
        customer_id: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Decimal:
        total = Decimal("0.00")
        for transaction in self.store.transactions:
            source = self.store.accounts.get(transaction.from_account)
            if (
                source is not None
                and source.customer_id == customer_id
                and transaction.status == "COMPLETED"
                and window_start <= transaction.created_at < window_end
            ):
                total += transaction.amount
        return total

    async def completed_outgoing_total_for_account(
        self,
        account_number: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Decimal:
        return sum(
            (
                transaction.amount
                for transaction in self.store.transactions
                if transaction.from_account == account_number
                and transaction.status == "COMPLETED"
                and window_start <= transaction.created_at < window_end
            ),
            Decimal("0.00"),
        )

    async def add(self, transaction: MemoryTransaction) -> None:
        if self.store.fail_on_add:
            raise SQLAlchemyError("simulated persistence failure")
        self.store.transactions.append(transaction)


class MemoryUnitOfWork:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self.accounts = MemoryAccountRepository(store)
        self.transactions = MemoryTransactionRepository(store)

    async def __aenter__(self) -> "MemoryUnitOfWork":
        self._balances = {
            account_number: account.balance
            for account_number, account in self.store.accounts.items()
        }
        self._transaction_count = len(self.store.transactions)
        return self

    async def __aexit__(self, exc_type, _exc, _traceback) -> bool:
        if exc_type is not None:
            for account_number, balance in self._balances.items():
                self.store.accounts[account_number].balance = balance
            del self.store.transactions[self._transaction_count :]
        return False


def make_store(source_balance: str = "500.00") -> MemoryStore:
    return MemoryStore(
        accounts={
            "12345678": MemoryAccount(
                "12345678",
                "customer-1",
                Decimal(source_balance),
            ),
            "87654321": MemoryAccount(
                "87654321",
                "customer-2",
                Decimal("50.00"),
                account_type="CURRENT",
            ),
            "11223344": MemoryAccount(
                "11223344",
                "customer-1",
                Decimal("25.00"),
            ),
        }
    )


def make_service(store: MemoryStore) -> TransferService:
    return TransferService(
        lambda: MemoryUnitOfWork(store),
        clock=lambda: NOW,
    )


async def expect_error(
    service: TransferService,
    code: TransferErrorCode,
    *,
    customer_id: str = "customer-1",
    from_account: str = "12345678",
    to_account: str = "87654321",
    amount: str = "1.00",
) -> None:
    with pytest.raises(TransferError) as raised:
        await service.transfer(
            customer_id=customer_id,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
        )
    assert raised.value.code is code


async def test_valid_transfer_debits_and_credits_the_exact_amount() -> None:
    store = make_store()

    result = await make_service(store).transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="125.50",
    )

    assert store.accounts["12345678"].balance == Decimal("374.50")
    assert store.accounts["87654321"].balance == Decimal("175.50")
    assert len(store.transactions) == 1
    assert store.transactions[0].amount == Decimal("125.50")
    assert store.transactions[0].status == "COMPLETED"
    assert result.transaction_id == str(store.transactions[0].transaction_id)
    assert result.from_account == "XXXX5678"
    assert result.to_account == "XXXX4321"
    assert result.amount == Decimal("125.50")
    assert result.created_at == NOW


async def test_completed_transfers_receive_distinct_transaction_ids() -> None:
    store = make_store()
    service = make_service(store)

    first = await service.transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="1.00",
    )
    second = await service.transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="1.00",
    )

    assert first.transaction_id != second.transaction_id
    assert len(store.transactions) == 2


@pytest.mark.parametrize(
    "amount",
    ["0.99", "0", "1.001", "1.000", "NaN", "1e2", "-1", "", " 1.00"],
)
async def test_invalid_amounts_are_declined_without_state_changes(amount: str) -> None:
    store = make_store()

    await expect_error(make_service(store), TransferErrorCode.INVALID_AMOUNT, amount=amount)

    assert store.accounts["12345678"].balance == Decimal("500.00")
    assert store.accounts["87654321"].balance == Decimal("50.00")
    assert store.transactions == []


async def test_non_string_amount_is_rejected_without_float_conversion() -> None:
    store = make_store()
    service = make_service(store)

    with pytest.raises(TransferError) as raised:
        await service.transfer(
            customer_id="customer-1",
            from_account="12345678",
            to_account="87654321",
            amount=1.25,
        )

    assert raised.value.code is TransferErrorCode.INVALID_AMOUNT
    assert store.transactions == []


async def test_same_account_transfer_is_rejected() -> None:
    store = make_store()

    await expect_error(
        make_service(store),
        TransferErrorCode.SAME_ACCOUNT,
        to_account="12345678",
    )


@pytest.mark.parametrize(
    ("from_account", "to_account", "customer_id"),
    [
        ("missing", "87654321", "customer-1"),
        ("12345678", "missing", "customer-1"),
        ("12345678", "87654321", "missing-customer"),
    ],
)
async def test_missing_accounts_or_customer_are_not_revealed(
    from_account: str,
    to_account: str,
    customer_id: str,
) -> None:
    store = make_store()

    await expect_error(
        make_service(store),
        TransferErrorCode.ACCOUNT_NOT_FOUND,
        customer_id=customer_id,
        from_account=from_account,
        to_account=to_account,
    )


@pytest.mark.parametrize(
    ("account_number", "field", "value"),
    [
        ("12345678", "status", "INACTIVE"),
        ("87654321", "status", "INACTIVE"),
    ],
)
async def test_inactive_accounts_are_rejected(
    account_number: str,
    field: str,
    value: str,
) -> None:
    store = make_store()
    setattr(store.accounts[account_number], field, value)

    await expect_error(make_service(store), TransferErrorCode.ACCOUNT_INACTIVE)

    assert store.accounts["12345678"].balance == Decimal("500.00")
    assert store.accounts["87654321"].balance == Decimal("50.00")
    assert store.transactions == []


async def test_source_must_belong_to_customer_and_be_a_savings_account() -> None:
    store = make_store()
    store.accounts["12345678"].customer_id = "customer-2"

    await expect_error(make_service(store), TransferErrorCode.ACCOUNT_NOT_FOUND)

    store = make_store()
    store.accounts["12345678"].account_type = "CURRENT"
    await expect_error(make_service(store), TransferErrorCode.ACCOUNT_NOT_FOUND)


async def test_insufficient_balance_is_rejected_without_movement() -> None:
    store = make_store(source_balance="125.49")

    await expect_error(
        make_service(store),
        TransferErrorCode.INSUFFICIENT_BALANCE,
        amount="125.50",
    )

    assert store.accounts["12345678"].balance == Decimal("125.49")
    assert store.accounts["87654321"].balance == Decimal("50.00")
    assert store.transactions == []


async def test_transfer_equal_to_source_balance_is_allowed() -> None:
    store = make_store(source_balance="125.50")

    await make_service(store).transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="125.50",
    )

    assert store.accounts["12345678"].balance == Decimal("0.00")
    assert store.accounts["87654321"].balance == Decimal("175.50")


async def test_exact_daily_limit_is_allowed_and_excess_is_rejected() -> None:
    store = make_store(source_balance="100000.00")
    store.transactions.append(
        MemoryTransaction(
            uuid.uuid4(),
            "12345678",
            "87654321",
            Decimal("80000.00"),
            "COMPLETED",
            NOW,
        )
    )

    await make_service(store).transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="20000.00",
    )
    assert store.transactions[-1].amount == Decimal("20000.00")

    store = make_store(source_balance="100000.00")
    store.transactions.append(
        MemoryTransaction(
            uuid.uuid4(),
            "12345678",
            "87654321",
            Decimal("80000.00"),
            "COMPLETED",
            NOW,
        )
    )
    original_balances = {
        key: account.balance for key, account in store.accounts.items()
    }

    await expect_error(
        make_service(store),
        TransferErrorCode.DAILY_LIMIT_EXCEEDED,
        amount="20000.01",
    )

    assert {
        key: account.balance for key, account in store.accounts.items()
    } == original_balances
    assert len(store.transactions) == 1


async def test_young_source_account_allows_exactly_50000_but_rejects_more() -> None:
    store = make_store(source_balance="100000.00")
    store.accounts["12345678"].opened_at = NOW - timedelta(days=29)
    store.transactions.append(
        MemoryTransaction(
            uuid.uuid4(),
            "12345678",
            "87654321",
            Decimal("40000.00"),
            "COMPLETED",
            NOW - timedelta(minutes=1),
        )
    )
    service = make_service(store)

    await service.transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="10000.00",
    )

    assert len(store.transactions) == 2
    assert store.accounts["12345678"].balance == Decimal("90000.00")
    await expect_error(
        service,
        TransferErrorCode.DAILY_LIMIT_EXCEEDED,
        amount="1.00",
    )
    assert len(store.transactions) == 2
    assert store.accounts["12345678"].balance == Decimal("90000.00")


async def test_account_exactly_30_days_old_uses_100000_limit() -> None:
    store = make_store(source_balance="100000.00")
    store.accounts["12345678"].opened_at = NOW - timedelta(days=30)
    store.transactions.append(
        MemoryTransaction(
            uuid.uuid4(),
            "12345678",
            "87654321",
            Decimal("80000.00"),
            "COMPLETED",
            NOW - timedelta(minutes=1),
        )
    )

    await make_service(store).transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="20000.00",
    )

    assert len(store.transactions) == 2
    assert store.accounts["12345678"].balance == Decimal("80000.00")


async def test_young_account_limit_does_not_apply_to_mature_source_account() -> None:
    store = make_store(source_balance="100000.00")
    store.accounts["12345678"].opened_at = NOW - timedelta(days=29)
    store.accounts["11223344"].balance = Decimal("100000.00")
    store.accounts["11223344"].opened_at = NOW - timedelta(days=30)
    store.transactions.append(
        MemoryTransaction(
            uuid.uuid4(),
            "12345678",
            "87654321",
            Decimal("50000.00"),
            "COMPLETED",
            NOW - timedelta(minutes=1),
        )
    )

    await make_service(store).transfer(
        customer_id="customer-1",
        from_account="11223344",
        to_account="87654321",
        amount="50000.00",
    )

    assert len(store.transactions) == 2
    assert store.accounts["11223344"].balance == Decimal("50000.00")


async def test_transfers_between_distinct_accounts_of_same_customer_are_allowed() -> None:
    store = make_store()
    store.accounts["87654321"].customer_id = "customer-1"

    await make_service(store).transfer(
        customer_id="customer-1",
        from_account="12345678",
        to_account="87654321",
        amount="1.00",
    )

    assert store.accounts["12345678"].balance == Decimal("499.00")
    assert store.accounts["87654321"].balance == Decimal("51.00")


async def test_storage_failure_rolls_back_balance_changes() -> None:
    store = make_store()
    store.fail_on_add = True

    await expect_error(make_service(store), TransferErrorCode.TRANSFER_FAILED)

    assert store.accounts["12345678"].balance == Decimal("500.00")
    assert store.accounts["87654321"].balance == Decimal("50.00")
    assert store.transactions == []
