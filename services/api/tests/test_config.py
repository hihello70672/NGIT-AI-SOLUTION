"""Configuration tests using explicit environment dictionaries."""
from services.api.config import Settings


def test_database_url_encodes_credentials_and_validates_schema(monkeypatch):
    for key in ("DATABASE_URL", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "DATABASE_SCHEMA", "API_PREFIX", "CORS_ORIGINS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("POSTGRES_USER", "ngit user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss:word")
    settings = Settings.from_env()
    assert "ngit%20user:p%40ss%3Aword@" in settings.database_url
    assert settings.database_schema == "ngit"


def test_invalid_database_url_and_prefix_are_rejected(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///not-supported")
    try:
        Settings.from_env()
    except ValueError:
        pass
    else:
        raise AssertionError("non-PostgreSQL URL was accepted")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/ngit")
    monkeypatch.setenv("API_PREFIX", "relative")
    try:
        Settings.from_env()
    except ValueError:
        pass
    else:
        raise AssertionError("relative API prefix was accepted")
