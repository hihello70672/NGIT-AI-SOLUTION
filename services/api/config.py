"""Environment-backed API configuration."""
from dataclasses import dataclass
import os

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
            url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        origins = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip())
        return cls(database_url=url, cors_origins=origins,
                   database_schema=os.getenv("DATABASE_SCHEMA", "ngit"))
