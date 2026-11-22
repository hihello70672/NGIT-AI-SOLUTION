import pytest

from services.api.config import Settings


def test_settings_build_postgres_url_and_default_prefix(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "db.local")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "ngit")
    monkeypatch.setenv("POSTGRES_USER", "api user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings.from_env()
    assert settings.database_url.startswith("postgresql://api%20user:secret@db.local:5433/ngit")
    assert settings.api_prefix == "/api/v1"


def test_settings_reject_invalid_api_prefix(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/ngit")
    monkeypatch.setenv("API_PREFIX", "relative")
    with pytest.raises(ValueError):
        Settings.from_env()
