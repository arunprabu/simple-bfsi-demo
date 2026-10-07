from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient, Response
import pytest

from simple_bank.api.errors import TransferError, TransferErrorCode
from simple_bank.api.v1.transfers import get_transfer_service
from simple_bank.main import create_app
from simple_bank.services.transfers import TransferResult

VALID_REQUEST = {
    "from_account": "12345678",
    "to_account": "87654321",
    "amount": "125.50",
}


class StubTransferService:
    def __init__(
        self,
        result: TransferResult | None = None,
        error: TransferError | None = None,
    ) -> None:
        self.result = result or TransferResult(
            transaction_id="transaction-123",
            from_account="XXXX5678",
            to_account="XXXX4321",
            amount=Decimal("125.50"),
            created_at=datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
        )
        self.error = error
        self.calls: list[dict[str, str]] = []

    async def transfer(
        self,
        *,
        customer_id: str,
        from_account: str,
        to_account: str,
        amount: str,
    ) -> TransferResult:
        self.calls.append(
            {
                "customer_id": customer_id,
                "from_account": from_account,
                "to_account": to_account,
                "amount": amount,
            }
        )
        if self.error is not None:
            raise self.error
        return self.result


def make_app(
    service: StubTransferService,
    authenticated: bool = True,
) -> FastAPI:
    async def resolve_customer(_request: Request) -> str | None:
        return "customer-from-session"

    app = create_app(
        authenticated_customer_resolver=resolve_customer if authenticated else None
    )
    app.dependency_overrides[get_transfer_service] = lambda: service
    return app


async def post_transfer(app: FastAPI, body: dict[str, str]) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.post("/api/v1/transfers", json=body)


async def test_successful_transfer_returns_documented_response() -> None:
    service = StubTransferService()
    response = await post_transfer(make_app(service), VALID_REQUEST)

    assert response.status_code == 201
    assert response.json() == {
        "transaction_id": "transaction-123",
        "status": "COMPLETED",
        "from_account": "XXXX5678",
        "to_account": "XXXX4321",
        "amount": "125.50",
        "created_at": "2026-10-07T12:00:00Z",
    }
    assert service.calls == [
        {
            "customer_id": "customer-from-session",
            "from_account": "12345678",
            "to_account": "87654321",
            "amount": "125.50",
        }
    ]


async def test_request_body_cannot_override_authenticated_customer() -> None:
    service = StubTransferService()
    response = await post_transfer(
        make_app(service),
        {**VALID_REQUEST, "customer_id": "attacker"},
    )

    assert response.status_code == 422
    assert service.calls == []


async def test_missing_authenticated_identity_returns_401() -> None:
    service = StubTransferService()
    response = await post_transfer(
        make_app(service, authenticated=False),
        VALID_REQUEST,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert service.calls == []


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (TransferErrorCode.INVALID_AMOUNT, 400),
        (TransferErrorCode.SAME_ACCOUNT, 400),
        (TransferErrorCode.ACCOUNT_NOT_FOUND, 404),
        (TransferErrorCode.ACCOUNT_INACTIVE, 409),
        (TransferErrorCode.INSUFFICIENT_BALANCE, 409),
        (TransferErrorCode.DAILY_LIMIT_EXCEEDED, 409),
        (TransferErrorCode.TRANSFER_FAILED, 500),
        (TransferErrorCode.UNAUTHENTICATED, 401),
    ],
)
async def test_domain_errors_map_to_documented_status_and_error_code(
    code: TransferErrorCode,
    status: int,
) -> None:
    service = StubTransferService(error=TransferError(code))
    response = await post_transfer(make_app(service), VALID_REQUEST)

    assert response.status_code == status
    assert response.json()["error"]["code"] == code.value
    assert isinstance(response.json()["error"]["message"], str)
    assert response.json()["error"]["message"]
    assert "12345678" not in response.json()["error"]["message"]
    assert "87654321" not in response.json()["error"]["message"]


async def test_daily_limit_error_identifies_both_limit_scopes() -> None:
    service = StubTransferService(
        error=TransferError(TransferErrorCode.DAILY_LIMIT_EXCEEDED)
    )

    response = await post_transfer(make_app(service), VALID_REQUEST)

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "DAILY_LIMIT_EXCEEDED",
        "message": (
            "The transfer exceeds the applicable source-account or customer-wide "
            "daily transfer limit."
        ),
    }
