import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str | None

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(database_url=os.environ.get("DATABASE_URL"))

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL must be configured before using the database.")
        return self.database_url
