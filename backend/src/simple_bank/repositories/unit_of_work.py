from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from simple_bank.repositories.accounts import AccountRepository
from simple_bank.repositories.transactions import TransactionRepository


class SqlAlchemyTransferUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.accounts = AccountRepository(session)
        self.transactions = TransactionRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> Self:
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self._transaction is None:
            raise RuntimeError("The transfer unit of work has not been entered.")
        return await self._transaction.__aexit__(exc_type, exc, traceback)
