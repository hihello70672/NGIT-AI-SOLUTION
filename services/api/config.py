"""Validated environment-backed API configuration."""
from dataclasses import dataclass
import os
from urllib.parse import quote


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = ()
    database_schema: str = "ngit"

    @classmethod
    def from_env(cls) -> "Settings":
        url = os.getenv("DATABASE_URL")
        if not url:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            name = os.getenv("POSTGRES_DB", "ngit")
            user = os.getenv("POSTGRES_USER", "ngit")
            password = os.getenv("POSTGRES_PASSWORD", "")
            auth = quote(user, safe="")
            if password:
                auth += ":" + quote(password, safe="")
            url = f"postgresql://{auth}@{host}:{port}/{name}"
        origins = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip())
        schema = os.getenv("DATABASE_SCHEMA", "ngit")
        if not schema.replace("_", "").isalnum() or not schema[0].isalpha():
            raise ValueError("invalid database schema")
        return cls(database_url=url, cors_origins=origins, database_schema=schema)

    def validate_security_configuration(self) -> None:
        """Reject unsafe deploy configs, but defer defaults to the security services."""
        token_pepper = os.getenv("AUTH_TOKEN_PEPPER", "")
        password_pepper = os.getenv("PASSWORD_PEPPER", "")
        if not token_pepper or len(token_pepper.encode()) < 32:
            raise ValueError("AUTH_TOKEN_PEPPER must contain at least 32 bytes")
        if not password_pepper or len(password_pepper.encode()) < 16:
            raise ValueError("PASSWORD_PEPPER must contain at least 16 bytes")


def get_settings() -> Settings:
    """Settings object, with local-only peppers supplied by the services as needed."""
    return Settings.from_env()
