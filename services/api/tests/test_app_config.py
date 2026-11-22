"""Configuration boundary tests."""
import pytest
from services.api.config import Settings

def test_settings_uses_postgres_environment(monkeypatch):
    for key in ("DATABASE_URL","POSTGRES_PASSWORD"): monkeypatch.delenv(key,raising=False)
    monkeypatch.setenv("POSTGRES_USER","ngit user")
    settings=Settings.from_env()
    assert settings.database_url.startswith("postgresql://ngit%20user@localhost:5432/ngit")
    assert settings.api_prefix=="/api/v1" and settings.database_schema=="ngit"

def test_rejects_non_postgres_and_invalid_prefix(monkeypatch):
    monkeypatch.setenv("DATABASE_URL","sqlite:///bad")
    with pytest.raises(ValueError): Settings.from_env()
    monkeypatch.setenv("DATABASE_URL","postgresql://localhost/ngit")
    monkeypatch.setenv("API_PREFIX","/../admin")
    with pytest.raises(ValueError): Settings.from_env()

def test_pepper_minimum_lengths(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_PEPPER","short");monkeypatch.setenv("PASSWORD_PEPPER","also-short")
    with pytest.raises(ValueError): Settings.from_env().validate_security_configuration()
