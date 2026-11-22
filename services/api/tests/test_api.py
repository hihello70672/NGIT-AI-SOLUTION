"""HTTP contract tests for authentication and the protected API."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from services.api import app as module

class FakeUsers:
    def __init__(self): self.rows = {}; self.counter = 0
    def create(self, email, password_hash, display_name):
        self.counter += 1
        row = {"id": str(self.counter), "email": email.lower(), "password_hash": password_hash, "display_name": display_name, "status": "active", "roles": ["user"], "created_at": datetime.now(timezone.utc)}
        self.rows[row["id"]] = row
        return row.copy()
    def by_email(self, email): return next((r.copy() for r in self.rows.values() if r["email"] == email.lower()), None)
    def by_id(self, user_id): return self.rows.get(user_id, {}).copy() or None
    def update_display_name(self, user_id, name):
        if user_id not in self.rows: return None
        self.rows[user_id]["display_name"] = name
        return self.rows[user_id].copy()

module.users = FakeUsers()
module.auth.users = module.users
client = TestClient(module.app)

def test_register_login_profile_update_and_logout():
    created = client.post("/api/v1/auth/register", json={"email":"person@example.com", "password":"long-enough-password", "display_name":"Person"})
    assert created.status_code == 201
    token = created.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/users/me", headers=headers).json()["email"] == "person@example.com"
    assert client.patch("/api/v1/users/me", headers=headers, json={"display_name":"Updated"}).json()["display_name"] == "Updated"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email":"person@example.com", "password":"long-enough-password"}).status_code == 200

def test_validation_request_id_and_brain_requires_authentication():
    assert client.post("/api/v1/auth/register", json={"email":"bad", "password":"x", "display_name":""}).status_code == 422
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.post("/api/v1/brain/generate", json={}).status_code == 401
    response = client.get("/health", headers={"X-Request-ID":"trace-123"})
    assert response.headers["X-Request-ID"] == "trace-123"
    assert response.json() == {"status":"ok"}

def test_unknown_fields_duplicate_registration_and_empty_patch():
    assert client.post("/api/v1/auth/login", json={"email":"x@example.com", "password":"x", "unexpected":True}).status_code == 422
    payload = {"email":"unique@example.com", "password":"long-enough-password", "display_name":"Person"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    token = first.json()["access_token"]
    assert client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={}).status_code == 422
