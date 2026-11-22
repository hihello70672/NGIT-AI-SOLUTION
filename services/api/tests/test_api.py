"""HTTP contract tests for authentication, authorization and profile APIs."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api import app as module


class FakeUsers:
    def __init__(self): self.rows = {}; self.counter = 0
    def create(self, email, password_hash, display_name):
        if self.by_email(email):
            from psycopg.errors import UniqueViolation
            raise UniqueViolation("duplicate")
        self.counter += 1
        row = {"id": str(self.counter), "email": email.lower(), "password_hash": password_hash, "display_name": display_name, "status": "active", "roles": ["user"], "created_at": "now"}
        self.rows[row["id"]] = row
        return row
    def by_email(self, email): return next((dict(r) for r in self.rows.values() if r["email"] == email.lower()), None)
    def by_id(self, user_id): return dict(self.rows[user_id]) if user_id in self.rows else None
    def update_display_name(self, user_id, name):
        if user_id not in self.rows: return None
        self.rows[user_id]["display_name"] = name
        return self.by_id(user_id)
    def list_users(self, limit=100, offset=0): return list(self.rows.values())[offset:offset+limit]


def setup_client():
    fake = FakeUsers()
    module.users = fake
    module.auth.users = fake
    module.authenticator, module.policies, module.approvals, module.audit, module.emergency, module.actions = module.create_default_security()
    module.auth.authenticator = module.authenticator
    return TestClient(module.app), fake


def test_register_profile_update_logout_and_authentication():
    client, _ = setup_client()
    result = client.post("/api/v1/auth/register", json={"email": "person@example.com", "password": "long-enough-password", "display_name": "Person"})
    assert result.status_code == 201
    token = result.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/users/me", headers=headers).json()["email"] == "person@example.com"
    assert client.patch("/api/v1/users/me", headers=headers, json={"display_name": "Updated"}).json()["display_name"] == "Updated"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401


def test_validation_duplicate_registration_and_default_deny_admin_list():
    client, _ = setup_client()
    data = {"email": "user@example.com", "password": "long-enough-password", "display_name": "User"}
    first = client.post("/api/v1/auth/register", json=data)
    assert first.status_code == 201
    assert client.post("/api/v1/auth/register", json=data).status_code == 409
    token = first.json()["access_token"]
    assert client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"}).status_code == 403
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={}).status_code == 422


def test_request_id_and_health_contract():
    client, _ = setup_client()
    response = client.get("/health", headers={"X-Request-ID": "trace-42"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-42"
    assert response.json() == {"status": "ok"}
