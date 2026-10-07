from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from simple_bank.models import Account, Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def completed_outgoing_total(
        self,
        customer_id: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Decimal:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
            .join(Account, Transaction.from_account == Account.account_number)
            .where(
                Account.customer_id == customer_id,
                Transaction.status == "COMPLETED",
                Transaction.created_at >= window_start,
                Transaction.created_at < window_end,
            )
        )
        return total if total is not None else Decimal("0.00")

    async def completed_outgoing_total_for_account(
        self,
        account_number: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Decimal:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
            .where(
                Transaction.from_account == account_number,
                Transaction.status == "COMPLETED",
                Transaction.created_at >= window_start,
                Transaction.created_at < window_end,
            )
        )
        return total if total is not None else Decimal("0.00")

    async def add(self, transaction: Transaction) -> None:
        self._session.add(transaction)
        await self._session.flush()

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        return await self._session.get(Transaction, transaction_id)
