import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from simple_bank.config import Settings
from simple_bank.models import Account, Customer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoProfile:
    profile_id: str
    label: str
    customer_id: str
    account_number: str


DEMO_PROFILES = (
    DemoProfile(
        profile_id="demo-user-1",
        label="Demo user 1",
        customer_id="demo-customer-1",
        account_number="DEMO000000000001",
    ),
    DemoProfile(
        profile_id="demo-user-2",
        label="Demo user 2",
        customer_id="demo-customer-2",
        account_number="DEMO000000000002",
    ),
)
DEMO_ACCOUNT_NUMBERS = {
    profile.profile_id: profile.account_number for profile in DEMO_PROFILES
}


async def seed_demo_data(
    sessions: async_sessionmaker[AsyncSession],
    *,
    settings: Settings | None = None,
) -> None:
    active_settings = settings or Settings.from_environment()
    if (
        active_settings.app_env not in {"development", "test"}
        or not active_settings.fake_auth_enabled
    ):
        raise RuntimeError(
            "Demo data seeding requires fake auth to be enabled in development or test."
        )

    opened_at = datetime.now(UTC) - timedelta(days=60)
    async with sessions() as session, session.begin():
        for profile in DEMO_PROFILES:
            customer = await session.get(Customer, profile.customer_id)
            if customer is None:
                session.add(Customer(customer_id=profile.customer_id))

        await session.flush()

        for profile in DEMO_PROFILES:
            account = await session.get(Account, profile.account_number)
            if account is None:
                session.add(
                    Account(
                        account_number=profile.account_number,
                        customer_id=profile.customer_id,
                        opened_at=opened_at,
                        balance=Decimal("1000.00"),
                        status="ACTIVE",
                        account_type="SAVINGS",
                    )
                )
            elif account.customer_id != profile.customer_id:
                raise RuntimeError(
                    "A demo account identifier is already owned by a different customer."
                )

    logger.info("Demo customer and account records are available.")


async def _run_seed() -> None:
    settings = Settings.from_environment()
    if (
        settings.app_env not in {"development", "test"}
        or not settings.fake_auth_enabled
    ):
        raise RuntimeError(
            "Demo data seeding requires fake auth to be enabled in development or test."
        )

    engine = create_async_engine(
        settings.require_database_url(),
        pool_pre_ping=True,
    )
    try:
        await seed_demo_data(async_sessionmaker(engine, expire_on_commit=False), settings=settings)
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(_run_seed())


if __name__ == "__main__":
    main()
