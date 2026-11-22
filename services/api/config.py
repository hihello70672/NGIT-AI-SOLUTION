"""Validated environment-backed API configuration."""
from dataclasses import dataclass
import os
from urllib.parse import quote, urlparse


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = ()
    database_schema: str = "ngit"

    @classmethod
    def from_env(cls) -> "Settings":
        url = os.getenv("DATABASE_URL", "")
        if not url:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            name = os.getenv("POSTGRES_DB", "ngit")
            user = os.getenv("POSTGRES_USER", "ngit")
            password = os.getenv("POSTGRES_PASSWORD", "")
            auth = quote(user, safe="") + ((":" + quote(password, safe="")) if password else "")
            url = f"postgresql://{auth}@{host}:{port}/{name}"
        parsed = urlparse(url)
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path.strip("/"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL with host and database")
        schema = os.getenv("DATABASE_SCHEMA", "ngit")
        if not schema or not schema.replace("_", "").isalnum() or not schema[0].isalpha():
            raise ValueError("invalid database schema")
        prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
        if not prefix.startswith("/") or ".." in prefix:
            raise ValueError("API_PREFIX must be an absolute URL path")
        origins = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip())
        return cls(url, prefix, origins, schema)

    def validate_security_configuration(self) -> None:
        if len(os.getenv("AUTH_TOKEN_PEPPER", "").encode()) < 32:
            raise ValueError("AUTH_TOKEN_PEPPER must contain at least 32 bytes")
        if len(os.getenv("PASSWORD_PEPPER", "").encode()) < 16:
            raise ValueError("PASSWORD_PEPPER must contain at least 16 bytes")
