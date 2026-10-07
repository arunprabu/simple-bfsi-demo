import asyncio
import os
import platform
import socket
import time
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import uvicorn
from fastapi import Request
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from simple_bank.api.v1.transfers import get_transfer_service
from simple_bank.main import create_app
from simple_bank.models import Account, Customer
from simple_bank.repositories.unit_of_work import SqlAlchemyTransferUnitOfWork
from simple_bank.services.transfers import TransferService


@pytest.mark.performance
async def test_at_least_95_of_100_transfers_return_within_one_second(
    pg_sessions: async_sessionmaker[AsyncSession],
) -> None:
    if platform.system() != "Linux" or platform.machine().lower() != "x86_64":
        pytest.skip("Latency acceptance profile requires a Linux x86_64 runner.")

    cpu_count = os.cpu_count()
    if cpu_count is None or cpu_count < 2:
        pytest.skip("Latency acceptance profile requires at least 2 vCPU.")

    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        pytest.skip("Cannot verify the runner memory required by the latency profile.")
    memory_bytes = page_size * page_count
    if memory_bytes < 4 * 1024**3:
        pytest.skip("Latency acceptance profile requires at least 4 GiB RAM.")

    opened_at = datetime.now(UTC) - timedelta(days=31)
    async with pg_sessions() as session, session.begin():
        customer_ids = [f"latency-customer-{index:03d}" for index in range(110)]
        session.add_all(Customer(customer_id=value) for value in customer_ids)
        await session.flush()
        accounts: list[Account] = []
        for index, customer_id in enumerate(customer_ids):
            accounts.extend(
                [
                    Account(
                        account_number=f"{10_000_000 + index:08d}",
                        customer_id=customer_id,
                        balance=Decimal("1000.00"),
                        status="ACTIVE",
                        account_type="SAVINGS",
                        opened_at=opened_at,
                    ),
                    Account(
                        account_number=f"{20_000_000 + index:08d}",
                        customer_id=customer_id,
                        balance=Decimal("0.00"),
                        status="ACTIVE",
                        account_type="CURRENT",
                        opened_at=opened_at,
                    ),
                ]
            )
        session.add_all(accounts)

    async def resolve_customer(request: Request) -> str:
        return request.headers["x-performance-customer"]

    async def service_dependency() -> AsyncIterator[TransferService]:
        async with pg_sessions() as session:
            yield TransferService(lambda: SqlAlchemyTransferUnitOfWork(session))

    app = create_app(authenticated_customer_resolver=resolve_customer)
    app.dependency_overrides[get_transfer_service] = service_dependency

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.setblocking(False)
    port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
            lifespan="off",
        )
    )
    server_task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        for _ in range(500):
            if server.started:
                break
            if server_task.done():
                await server_task
                pytest.fail("The latency test HTTP server stopped before startup.")
            await asyncio.sleep(0.01)
        assert server.started, "The latency test HTTP server did not start."

        async with AsyncExitStack() as client_stack:
            clients = [
                await client_stack.enter_async_context(
                    AsyncClient(
                        base_url=f"http://127.0.0.1:{port}",
                        timeout=10.0,
                    )
                )
                for _ in range(10)
            ]

            async def submit(client: AsyncClient, index: int) -> float:
                started = time.perf_counter()
                response = await client.post(
                    "/api/v1/transfers",
                    headers={
                        "x-performance-customer": f"latency-customer-{index:03d}"
                    },
                    json={
                        "from_account": f"{10_000_000 + index:08d}",
                        "to_account": f"{20_000_000 + index:08d}",
                        "amount": "1.00",
                    },
                )
                elapsed = time.perf_counter() - started
                assert response.status_code == 201, response.text
                return elapsed

            await asyncio.gather(
                *(submit(client, index) for index, client in enumerate(clients))
            )

            async def submit_ten(worker: int, client: AsyncClient) -> list[float]:
                durations: list[float] = []
                for offset in range(10):
                    durations.append(await submit(client, 10 + worker * 10 + offset))
                return durations

            elapsed_seconds = [
                duration
                for worker_durations in await asyncio.gather(
                    *(
                        submit_ten(worker, client)
                        for worker, client in enumerate(clients)
                    )
                )
                for duration in worker_durations
            ]
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(server_task, timeout=10.0)
        finally:
            listener.close()

    within_target = sum(duration <= 1.0 for duration in elapsed_seconds)
    assert len(elapsed_seconds) == 100
    assert within_target >= 95, (
        f"{within_target}/100 transfer responses were within one second; "
        f"slowest response was {max(elapsed_seconds):.3f}s."
    )
