import os

import pytest

from services.api.config import Settings


def test_database_url_is_built_with_escaped_credentials(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "api user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pass@word:/")
    settings = Settings.from_env()
    assert settings.database_url == "postgresql://api%20user:pass%40word%3A%2F@localhost:5432/ngit"


def test_env_origins_and_schema_are_validated(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " https://one.test,https://two.test,,")
    monkeypatch.setenv("DATABASE_SCHEMA", "app_data")
    settings = Settings.from_env()
    assert settings.cors_origins == ("https://one.test", "https://two.test")
    assert settings.database_schema == "app_data"
    monkeypatch.setenv("DATABASE_SCHEMA", "bad-name")
    with pytest.raises(ValueError, match="database schema"):
        Settings.from_env()


def test_deployment_peppers_must_be_configured(monkeypatch):
    monkeypatch.delenv("AUTH_TOKEN_PEPPER", raising=False)
    monkeypatch.delenv("PASSWORD_PEPPER", raising=False)
    with pytest.raises(ValueError, match="AUTH_TOKEN_PEPPER"):
        Settings.from_env().validate_security_configuration()
    monkeypatch.setenv("AUTH_TOKEN_PEPPER", "t" * 32)
    monkeypatch.setenv("PASSWORD_PEPPER", "p" * 16)
    Settings.from_env().validate_security_configuration()
