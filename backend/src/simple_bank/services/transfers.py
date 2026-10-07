import re
import uuid
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Protocol
from zoneinfo import ZoneInfo

from sqlalchemy.exc import SQLAlchemyError

from simple_bank.api.errors import TransferError, TransferErrorCode
from simple_bank.logging import log_transfer_event, mask_account_number
from simple_bank.models import Account, Transaction

MINIMUM_AMOUNT = Decimal("1.00")
DAILY_TRANSFER_LIMIT = Decimal("100000.00")
NEW_ACCOUNT_DAILY_TRANSFER_LIMIT = Decimal("50000.00")
NEW_ACCOUNT_AGE = timedelta(days=30)
CENT = Decimal("0.01")
IST = ZoneInfo("Asia/Kolkata")
AMOUNT_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")


class AccountState(Protocol):
    account_number: str
    customer_id: str
    balance: Decimal
    status: str
    account_type: str
    opened_at: datetime


class TransferRecord(Protocol):
    transaction_id: uuid.UUID
    from_account: str
    to_account: str
    amount: Decimal
    status: str
    created_at: datetime


class AccountRepositoryProtocol(Protocol):
    async def lock_customer(self, customer_id: str) -> bool: ...

    async def lock_accounts(
        self,
        account_numbers: list[str],
    ) -> list[AccountState]: ...


class TransactionRepositoryProtocol(Protocol):
    async def completed_outgoing_total(
        self,
        customer_id: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Decimal: ...

    async def completed_outgoing_total_for_account(
        self,
        account_number: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Decimal: ...

    async def add(self, transaction: TransferRecord) -> None: ...


class TransferUnitOfWork(Protocol):
    accounts: AccountRepositoryProtocol
    transactions: TransactionRepositoryProtocol

    async def __aenter__(self) -> "TransferUnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> bool | None: ...


@dataclass(frozen=True)
class TransferResult:
    transaction_id: str
    from_account: str
    to_account: str
    amount: Decimal
    created_at: datetime


def parse_transfer_amount(value: object) -> Decimal:
    if not isinstance(value, str) or not AMOUNT_PATTERN.fullmatch(value):
        raise TransferError(TransferErrorCode.INVALID_AMOUNT)

    amount = Decimal(value)
    if amount < MINIMUM_AMOUNT:
        raise TransferError(TransferErrorCode.INVALID_AMOUNT)

    return amount.quantize(CENT)


def ist_day_window(now: datetime) -> tuple[datetime, datetime]:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("The transfer clock must return a timezone-aware datetime.")

    local_date: date = now.astimezone(IST).date()
    local_start = datetime.combine(local_date, time.min, tzinfo=IST)
    local_end = local_start + timedelta(days=1)
    return local_start.astimezone(UTC), local_end.astimezone(UTC)


class TransferService:
    def __init__(
        self,
        unit_of_work_factory: Callable[
            [], AbstractAsyncContextManager[TransferUnitOfWork]
        ],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def transfer(
        self,
        *,
        customer_id: str,
        from_account: str,
        to_account: str,
        amount: str,
    ) -> TransferResult:
        try:
            parsed_amount = parse_transfer_amount(amount)
            if from_account == to_account:
                raise TransferError(TransferErrorCode.SAME_ACCOUNT)

            now = self._clock()
            window_start, window_end = ist_day_window(now)
            result = await self._perform_transfer(
                customer_id=customer_id,
                from_account=from_account,
                to_account=to_account,
                amount=parsed_amount,
                created_at=now.astimezone(UTC),
                window_start=window_start,
                window_end=window_end,
            )
        except TransferError as error:
            log_transfer_event(
                "declined",
                from_account=from_account,
                to_account=to_account,
                result_code=error.code.value,
            )
            raise
        except SQLAlchemyError as error:
            log_transfer_event(
                "failed",
                from_account=from_account,
                to_account=to_account,
                result_code=TransferErrorCode.TRANSFER_FAILED.value,
            )
            raise TransferError(TransferErrorCode.TRANSFER_FAILED) from error

        log_transfer_event(
            "completed",
            from_account=from_account,
            to_account=to_account,
            result_code="COMPLETED",
        )
        return result

    async def _perform_transfer(
        self,
        *,
        customer_id: str,
        from_account: str,
        to_account: str,
        amount: Decimal,
        created_at: datetime,
        window_start: datetime,
        window_end: datetime,
    ) -> TransferResult:
        async with self._unit_of_work_factory() as unit_of_work:
            if not await unit_of_work.accounts.lock_customer(customer_id):
                raise TransferError(TransferErrorCode.ACCOUNT_NOT_FOUND)

            locked_accounts = await unit_of_work.accounts.lock_accounts(
                [from_account, to_account]
            )
            accounts = {account.account_number: account for account in locked_accounts}
            source = accounts.get(from_account)
            recipient = accounts.get(to_account)
            if source is None or recipient is None:
                raise TransferError(TransferErrorCode.ACCOUNT_NOT_FOUND)
            if source.customer_id != customer_id or source.account_type != "SAVINGS":
                raise TransferError(TransferErrorCode.ACCOUNT_NOT_FOUND)
            if source.status != "ACTIVE" or recipient.status != "ACTIVE":
                raise TransferError(TransferErrorCode.ACCOUNT_INACTIVE)
            if source.balance < amount:
                raise TransferError(TransferErrorCode.INSUFFICIENT_BALANCE)

            outgoing_total = await unit_of_work.transactions.completed_outgoing_total(
                customer_id,
                window_start,
                window_end,
            )
            if outgoing_total + amount > DAILY_TRANSFER_LIMIT:
                raise TransferError(TransferErrorCode.DAILY_LIMIT_EXCEEDED)

            source_account_total = await unit_of_work.transactions.completed_outgoing_total_for_account(
                source.account_number,
                window_start,
                window_end,
            )
            source_account_limit = (
                NEW_ACCOUNT_DAILY_TRANSFER_LIMIT
                if created_at - source.opened_at.astimezone(UTC) < NEW_ACCOUNT_AGE
                else DAILY_TRANSFER_LIMIT
            )
            if source_account_total + amount > source_account_limit:
                raise TransferError(TransferErrorCode.DAILY_LIMIT_EXCEEDED)

            source.balance -= amount
            recipient.balance += amount
            transaction = Transaction(
                transaction_id=uuid.uuid4(),
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                status="COMPLETED",
                created_at=created_at,
            )
            await unit_of_work.transactions.add(transaction)

            return TransferResult(
                transaction_id=str(transaction.transaction_id),
                from_account=mask_account_number(from_account),
                to_account=mask_account_number(to_account),
                amount=amount,
                created_at=created_at,
            )
