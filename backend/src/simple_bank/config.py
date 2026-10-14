import os
from dataclasses import dataclass, field

from sqlalchemy.engine import URL

_FAKE_AUTH_ENVIRONMENTS = frozenset({"development", "test"})


class DatabaseConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    # The URL can embed the database password, so keep it out of repr() output.
    database_url: str | None = field(repr=False)
    app_env: str | None
    fake_auth_enabled: bool

    @classmethod
    def from_environment(cls) -> "Settings":
        app_env_value = os.environ.get("APP_ENV")
        app_env = app_env_value.strip().lower() if app_env_value else None
        if not app_env:
            app_env = None

        raw_fake_auth = os.environ.get("FAKE_AUTH_ENABLED", "false").strip().lower()
        if raw_fake_auth not in {"true", "false"}:
            raise ValueError("FAKE_AUTH_ENABLED must be either 'true' or 'false'.")
        fake_auth_enabled = raw_fake_auth == "true"
        if fake_auth_enabled and app_env not in _FAKE_AUTH_ENVIRONMENTS:
            raise ValueError(
                "FAKE_AUTH_ENABLED can only be true when APP_ENV is development or test."
            )

        database_url = os.environ.get("DATABASE_URL") or _postgres_database_url()
        return cls(
            database_url=database_url,
            app_env=app_env,
            fake_auth_enabled=fake_auth_enabled,
        )

    def require_database_url(self) -> str:
        if not self.database_url:
            raise DatabaseConfigurationError(
                "Set DATABASE_URL or complete POSTGRES_* settings before using the database."
            )
        return self.database_url


def _postgres_database_url() -> str | None:
    host = os.environ.get("POSTGRES_HOST")
    database = os.environ.get("POSTGRES_DB")
    postgres_values = (
        os.environ.get("POSTGRES_USER"),
        os.environ.get("POSTGRES_PASSWORD"),
        database,
        host,
        os.environ.get("POSTGRES_PORT"),
    )
    if not any(postgres_values):
        return None
    if not host or not database:
        raise DatabaseConfigurationError(
            "POSTGRES_HOST and POSTGRES_DB are required when using POSTGRES_* settings."
        )

    username = os.environ.get("POSTGRES_USER") or None
    password = os.environ.get("POSTGRES_PASSWORD") or None
    if password and not username:
        raise DatabaseConfigurationError(
            "POSTGRES_USER is required when POSTGRES_PASSWORD is set."
        )

    port_value = os.environ.get("POSTGRES_PORT")
    try:
        port = int(port_value) if port_value else 5432
    except ValueError as exc:
        raise DatabaseConfigurationError("POSTGRES_PORT must be an integer.") from exc

    return URL.create(
        drivername="postgresql+asyncpg",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    ).render_as_string(hide_password=False)
