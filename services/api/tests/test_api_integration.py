"""Opt-in PostgreSQL integration tests for the identity API and RLS context.

Use NGIT_TEST_DATABASE_URL for a disposable migrated database accessed by a
non-owner, non-superuser role without BYPASSRLS.
"""
import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("NGIT_TEST_DATABASE_URL"), reason="requires disposable PostgreSQL integration database")


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["NGIT_TEST_DATABASE_URL"])
    monkeypatch.setenv("AUTH_TOKEN_PEPPER", "integration-auth-pepper-at-least-32-bytes")
    monkeypatch.setenv("PASSWORD_PEPPER", "integration-password-pepper")
    from fastapi.testclient import TestClient
    from services.api import app as api
    api.db.pool.conninfo = os.environ["NGIT_TEST_DATABASE_URL"]
    api.app.dependency_overrides.clear()
    with TestClient(api.app) as client:
        yield client
    api.authenticator._tokens.clear()


def test_register_database_login_profile_and_logout(api_client):
    email = f"api-{uuid.uuid4().hex}@example.test"
    payload = {"email": email, "password": "integration-secure-password", "display_name": "Integration"}
    created = api_client.post("/api/v1/auth/register", json=payload)
    assert created.status_code == 201
    token = created.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert api_client.post("/api/v1/auth/login", json={"email": email, "password": payload["password"]}).status_code == 200
    assert api_client.get("/api/v1/users/me", headers=headers).json()["email"] == email
    assert api_client.patch("/api/v1/users/me", headers=headers, json={"display_name": "Updated"}).json()["display_name"] == "Updated"
    assert api_client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert api_client.get("/api/v1/users/me", headers=headers).status_code == 401


def test_registration_persists_default_role(api_client):
    from services.api import app as api
    email = f"role-{uuid.uuid4().hex}@example.test"
    result = api_client.post("/api/v1/auth/register", json={"email": email, "password": "integration-secure-password", "display_name": "Role"})
    assert result.status_code == 201
    assert result.json()["user"]["roles"] == ["user"]
    assert api.users.by_email(email)["roles"] == ["user"]


def test_nonexistent_resource_and_pagination_errors(api_client):
    assert api_client.get("/api/v1/users/me").status_code == 401
    assert api_client.get("/api/v1/users", params={"limit": 101}).status_code == 422
