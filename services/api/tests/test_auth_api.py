import pytest
from fastapi.testclient import TestClient
from services.api import app as app_module


class FakeDatabase:
    def open(self): pass
    def close(self): pass


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "db", FakeDatabase())
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_health_and_request_id(client):
    response = client.get("/health", headers={"X-Request-ID": "safe-id_1"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "safe-id_1"


def test_registration_validation_and_unknown_fields(client):
    invalid = client.post("/api/v1/auth/register", json={"email": "bad", "password": "short", "display_name": " "})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
    extra = client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "pass", "admin": True})
    assert extra.status_code == 422


def test_auth_endpoints_use_database_backed_services(client, monkeypatch):
    user = {"id": "123", "email": "person@example.com", "display_name": "Person", "status": "active", "roles": ["user"], "created_at": "2026-01-01T00:00:00+00:00"}
    monkeypatch.setattr(app_module.auth, "register", lambda email, password, name: (user, "token"))
    monkeypatch.setattr(app_module.auth, "login", lambda email, password: (user, "token"))
    register = client.post("/api/v1/auth/register", json={"email": "person@example.com", "password": "long-password-123", "display_name": "Person"})
    assert register.status_code == 201
    assert register.json()["access_token"] == "token"
    login = client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "long-password-123"})
    assert login.status_code == 200
    assert login.json()["user"]["roles"] == ["user"]


def test_auth_error_payload_does_not_disclose_credentials(client):
    response = client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "a-secret-password"})
    assert response.status_code == 401
    assert "a-secret-password" not in response.text
    assert response.json()["error"]["request_id"]


def test_api_openapi_has_auth_contract(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/users/me" in schema["paths"]
