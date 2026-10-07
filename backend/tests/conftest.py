import asyncio
import os
import re
import subprocess
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_TEST_DATABASE_NAME = re.compile(r"(?:^|[_-])test(?:[_-]|$)", re.IGNORECASE)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if os.environ.get("TEST_DATABASE_URL"):
        return

    skip_postgres = pytest.mark.skip(
        reason=(
            "Set TEST_DATABASE_URL to an isolated PostgreSQL database whose name "
            "contains 'test' to run these tests."
        )
    )
    for item in items:
        if "integration" in item.keywords or "performance" in item.keywords:
            item.add_marker(skip_postgres)


@pytest.fixture(scope="session")
def migrated_test_database_url() -> str:
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests.")

    try:
        parsed_url = make_url(raw_url)
    except (ArgumentError, TypeError, ValueError):
        pytest.fail("TEST_DATABASE_URL is not a valid SQLAlchemy database URL.")

    if (
        parsed_url.get_backend_name() != "postgresql"
        or not parsed_url.database
        or not _TEST_DATABASE_NAME.search(parsed_url.database)
    ):
        pytest.fail(
            "TEST_DATABASE_URL must use PostgreSQL and a database name containing 'test'."
        )

    async_url = parsed_url.set(drivername="postgresql+asyncpg")
    database_url = async_url.render_as_string(hide_password=False)
    migration_environment = os.environ.copy()
    migration_environment["DATABASE_URL"] = database_url
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=BACKEND_ROOT,
        env=migration_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        pytest.fail(
            "Alembic migration failed for TEST_DATABASE_URL. Verify that the isolated "
            "test database is reachable and its migrations are valid."
        )

    return database_url


@pytest.fixture(scope="session")
def postgres_engine(
    migrated_test_database_url: str,
) -> Iterator[AsyncEngine]:
    engine = create_async_engine(
        migrated_test_database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture
async def pg_sessions(
    postgres_engine: AsyncEngine,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    async def clear_transfer_tables() -> None:
        async with postgres_engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE TABLE transactions, accounts, customers "
                    "RESTART IDENTITY CASCADE"
                )
            )

    await clear_transfer_tables()
    yield async_sessionmaker(postgres_engine, expire_on_commit=False)
    await clear_transfer_tables()
