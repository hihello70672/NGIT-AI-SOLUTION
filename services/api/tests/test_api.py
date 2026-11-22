"""HTTP contract tests for identity, authorization and profile APIs."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")

from fastapi.testclient import TestClient
from services.api import app as module


class FakeUsers:
    def __init__(self):
        self.rows = {}
        self.counter = 0

    def create(self, email, password_hash, display_name):
        if self.by_email(email):
            from psycopg.errors import UniqueViolation
            raise UniqueViolation("duplicate")
        self.counter += 1
        row = {"id": str(self.counter), "email": email.lower(), "display_name": display_name, "status": "active", "roles": ["user"], "created_at": "now", "password_hash": password_hash}
        self.rows[row["id"]] = row
        return row

    def by_email(self, email):
        return next((dict(row) for row in self.rows.values() if row["email"] == email.lower()), None)

    def by_id(self, user_id):
        row = self.rows.get(user_id)
        return dict(row) if row else None

    def update_display_name(self, user_id, name):
        row = self.rows.get(user_id)
        if row:
            row["display_name"] = name
            return dict(row)
        return None

    def list_users(self, limit=100, offset=0):
        return list(self.rows.values())[offset:offset + limit]


def client_for_test():
    fake = FakeUsers()
    module.users = fake
    module.auth.users = fake
    module.authenticator, module.policies, module.approvals, module.audit, module.emergency, module.actions = module.create_default_security()
    module.auth.authenticator = module.authenticator
    return TestClient(module.app), fake


def test_register_login_profile_and_revoke_flow():
    client, fake = client_for_test()
    registered = client.post("/api/v1/auth/register", json={"email": "Person@example.com", "password": "long-enough-password", "display_name": "Person"})
    assert registered.status_code == 201
    token = registered.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/users/me", headers=headers).json()["email"] == "person@example.com"
    assert client.patch("/api/v1/users/me", headers=headers, json={"display_name": "Updated"}).json()["display_name"] == "Updated"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401


def test_login_rejects_invalid_credentials_and_registration_conflict():
    client, _ = client_for_test()
    payload = {"email": "user@example.com", "password": "long-enough-password", "display_name": "User"}
    assert client.post("/api/v1/auth/login", json=payload).status_code == 401
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_profile_and_admin_listing_authorization_and_validation():
    client, fake = client_for_test()
    first = client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "long-enough-password", "display_name": "User"}).json()
    user_headers = {"Authorization": f"Bearer {first['access_token']}"}
    assert client.get("/api/v1/users", headers=user_headers).status_code == 403
    assert client.patch("/api/v1/users/me", headers=user_headers, json={}).status_code == 422
    assert client.get("/api/v1/users", headers=user_headers, params={"limit": 101}).status_code == 422
    admin = fake.create("admin@example.com", "not-used", "Admin")
    admin["roles"] = ["admin"]
    admin_token = module.authenticator.issue(admin["id"], {"admin"})
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200 and len(response.json()["users"]) == 2


def test_request_id_is_sanitized_and_added_to_errors():
    client, _ = client_for_test()
    response = client.get("/api/v1/users/me", headers={"X-Request-ID": "bad request !"})
    assert response.status_code == 401
    assert response.headers["X-Request-ID"] != "bad request !"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
