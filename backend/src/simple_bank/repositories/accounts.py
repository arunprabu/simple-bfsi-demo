from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from simple_bank.models import Account, Customer


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_customer(self, customer_id: str) -> bool:
        customer = await self._session.scalar(
            select(Customer)
            .where(Customer.customer_id == customer_id)
            .with_for_update()
        )
        return customer is not None

    async def lock_accounts(self, account_numbers: Sequence[str]) -> list[Account]:
        numbers = sorted(set(account_numbers))
        if not numbers:
            return []

        accounts = await self._session.scalars(
            select(Account)
            .where(Account.account_number.in_(numbers))
            .order_by(Account.account_number)
            .with_for_update()
        )
        return list(accounts)
