from collections.abc import AsyncIterator
import secrets

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from simple_bank.api.v1.dev_auth import get_optional_dev_auth_session
from simple_bank.main import create_app
from simple_bank.models import Customer


class StubSession:
    def __init__(
        self,
        customer_ids: set[str],
        fail: bool = False,
    ) -> None:
        self.customer_ids = customer_ids
        self.fail = fail

    async def get(self, model: type[Customer], customer_id: str) -> Customer | None:
        if self.fail:
            raise SQLAlchemyError("database detail must not be returned")
        if model is Customer and customer_id in self.customer_ids:
            return Customer(customer_id=customer_id)
        return None


def make_app(
    monkeypatch,
    session: StubSession,
) -> FastAPI:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")
    app = create_app()

    async def override_session() -> AsyncIterator[StubSession]:
        yield session

    app.dependency_overrides[get_optional_dev_auth_session] = override_session
    return app


async def test_session_status_lists_only_seeded_demo_profiles(monkeypatch) -> None:
    app = make_app(
        monkeypatch,
        StubSession({"demo-customer-1"}),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/dev-auth/session")

    assert response.status_code == 200
    assert response.json() == {
        "fake_auth_enabled": True,
        "authenticated": False,
        "profiles": [
            {"profile_id": "demo-user-1", "label": "Demo user 1"},
        ],
    }


async def test_sign_in_sets_http_only_cookie_without_returning_token(
    monkeypatch,
) -> None:
    app = make_app(
        monkeypatch,
        StubSession({"demo-customer-1"}),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-1"},
        )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["current_profile"] == {
        "profile_id": "demo-user-1",
        "label": "Demo user 1",
    }
    set_cookie = response.headers["set-cookie"]
    assert "dev_session=" in set_cookie
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()
    assert "path=/api/v1" in set_cookie.lower()
    assert response.json().get("token") is None


async def test_sign_in_rejects_password_fields(monkeypatch) -> None:
    app = make_app(
        monkeypatch,
        StubSession({"demo-customer-1"}),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/dev-auth/session",
            json={
                "profile_id": "demo-user-1",
                "password": secrets.token_urlsafe(16),
            },
        )

    assert response.status_code == 422
    assert "set-cookie" not in response.headers


async def test_unknown_or_unseeded_profile_does_not_create_session(
    monkeypatch,
) -> None:
    app = make_app(
        monkeypatch,
        StubSession({"demo-customer-1"}),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        unknown = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "not-allowlisted"},
        )
        unseeded = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-2"},
        )

    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "DEMO_PROFILE_NOT_FOUND"
    assert unseeded.status_code == 404
    assert unseeded.json()["error"]["code"] == "DEMO_PROFILE_NOT_FOUND"
    assert "set-cookie" not in unknown.headers
    assert "set-cookie" not in unseeded.headers


async def test_database_failure_returns_safe_demo_data_error(monkeypatch) -> None:
    app = make_app(monkeypatch, StubSession(set(), fail=True))
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/dev-auth/session",
            json={"profile_id": "demo-user-1"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEMO_DATA_UNAVAILABLE"
    assert "database detail" not in response.text
    assert "set-cookie" not in response.headers
