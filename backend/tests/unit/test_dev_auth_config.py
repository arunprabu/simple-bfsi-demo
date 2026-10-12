import secrets

import pytest
from sqlalchemy.engine import make_url

from simple_bank.config import Settings

DATABASE_ENVIRONMENT_KEYS = (
    "DATABASE_URL",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
)


def clear_database_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in DATABASE_ENVIRONMENT_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_database_url_setting_takes_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_database_environment(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://override-host/sample_db",
    )
    monkeypatch.setenv("POSTGRES_HOST", "ignored-host")
    monkeypatch.setenv("POSTGRES_DB", "ignored_db")

    settings = Settings.from_environment()

    assert settings.require_database_url() == (
        "postgresql+asyncpg://override-host/sample_db"
    )


def test_postgres_environment_components_build_a_sqlalchemy_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_database_environment(monkeypatch)
    password = secrets.token_urlsafe(18)
    username = f"unit_{secrets.token_hex(4)}"
    monkeypatch.setenv("POSTGRES_USER", username)
    monkeypatch.setenv("POSTGRES_PASSWORD", password)
    monkeypatch.setenv("POSTGRES_DB", "simple_bank_test")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")

    parsed_url = make_url(Settings.from_environment().require_database_url())

    assert parsed_url.drivername == "postgresql+asyncpg"
    assert parsed_url.username == username
    assert parsed_url.password == password
    assert parsed_url.database == "simple_bank_test"
    assert parsed_url.host == "localhost"
    assert parsed_url.port == 5433


def test_fake_auth_is_disabled_when_environment_flag_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FAKE_AUTH_ENABLED", raising=False)

    assert Settings.from_environment().fake_auth_enabled is False


@pytest.mark.parametrize("app_env", ["development", "test"])
def test_fake_auth_requires_an_allowed_environment(
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
) -> None:
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")

    assert Settings.from_environment().fake_auth_enabled is True


@pytest.mark.parametrize("app_env", ["production", "staging", ""])
def test_fake_auth_cannot_be_enabled_outside_development_or_test(
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
) -> None:
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "true")

    with pytest.raises(ValueError):
        Settings.from_environment()


def test_fake_auth_flag_rejects_unrecognized_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("FAKE_AUTH_ENABLED", "sometimes")

    with pytest.raises(ValueError):
        Settings.from_environment()


def test_database_url_requires_a_complete_postgres_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_database_environment(monkeypatch)
    monkeypatch.setenv("POSTGRES_USER", "demo_user")

    with pytest.raises(RuntimeError):
        Settings.from_environment().require_database_url()
