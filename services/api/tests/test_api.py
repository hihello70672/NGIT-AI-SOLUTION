"""HTTP API contract checks with an isolated, replaceable user store."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from services.api import app as api_module


class FakeUsers:
    def __init__(self):
        self.rows = {}
        self.counter = 0

    def create(self, email, password_hash, display_name):
        self.counter += 1
        row = {"id": str(self.counter), "email": email.lower(), "password_hash": password_hash,
               "display_name": display_name, "status": "active", "roles": ["user"],
               "created_at": datetime.now(timezone.utc)}
        self.rows[row["id"]] = row
        return row.copy()

    def by_email(self, email):
        return next((row.copy() for row in self.rows.values() if row["email"] == email.lower()), None)

    def by_id(self, user_id):
        row = self.rows.get(user_id)
        return row.copy() if row else None

    def update_display_name(self, user_id, name):
        if user_id not in self.rows:
            return None
        self.rows[user_id]["display_name"] = name
        return self.rows[user_id].copy()


api_module.users = FakeUsers()
api_module.auth.users = api_module.users
client = TestClient(api_module.app)


def test_register_login_profile_update_and_logout():
    response = client.post("/api/v1/auth/register", json={"email": "person@example.com", "password": "long-enough-password", "display_name": "Person"})
    assert response.status_code == 201
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/users/me", headers=headers).json()["email"] == "person@example.com"
    assert client.patch("/api/v1/users/me", headers=headers, json={"display_name": "Updated"}).json()["display_name"] == "Updated"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "long-enough-password"}).status_code == 200


def test_validation_authentication_and_request_id():
    assert client.post("/api/v1/auth/register", json={"email": "bad", "password": "x", "display_name": ""}).status_code == 422
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.post("/api/v1/brain/generate", json={}).status_code == 401
    response = client.get("/health", headers={"X-Request-ID": "trace-123"})
    assert response.headers["X-Request-ID"] == "trace-123"


def test_unknown_fields_empty_patch_and_duplicate_registration():
    assert client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "x", "unexpected": True}).status_code == 422
    response = client.post("/api/v1/auth/register", json={"email": "duplicate@example.com", "password": "long-enough-password", "display_name": "Person"})
    token = response.json()["access_token"]
    assert client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={}).status_code == 422
    payload = {"email": "duplicate@example.com", "password": "long-enough-password", "display_name": "Duplicate"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    conflict = client.post("/api/v1/auth/register", json=payload)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "conflict"
