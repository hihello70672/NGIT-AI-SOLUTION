"""API behavior tests using an isolated in-memory user-service boundary."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from services.api import app as api_module

class FakeUsers:
    def __init__(self): self.rows = {}; self.next = 0
    def create(self, email, password_hash, display_name):
        self.next += 1
        row = {"id": str(self.next), "email": email, "password_hash": password_hash,
               "display_name": display_name, "status": "active", "roles": ["user"],
               "created_at": datetime.now(timezone.utc)}
        self.rows[row["id"]] = row
        return row.copy()
    def by_email(self, email):
        return next((r.copy() for r in self.rows.values() if r["email"] == email.lower()), None)
    def by_id(self, user_id):
        row = self.rows.get(user_id)
        return row.copy() if row else None
    def update_display_name(self, user_id, name):
        if user_id not in self.rows: return None
        self.rows[user_id]["display_name"] = name
        return self.rows[user_id].copy()

api_module.users = FakeUsers()
api_module.auth.users = api_module.users
client = TestClient(api_module.app)

def test_registration_profile_and_logout():
    response = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "long-enough-password", "display_name": "A"})
    assert response.status_code == 201
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/users/me", headers=headers).json()["email"] == "a@example.com"
    assert client.patch("/api/v1/users/me", headers=headers, json={"display_name": "Ada"}).json()["display_name"] == "Ada"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401

def test_validation_auth_and_brain_routes_are_protected():
    assert client.post("/api/v1/auth/register", json={"email": "bad", "password": "x", "display_name": ""}).status_code == 422
    assert client.get("/api/v1/users/me").status_code == 401
    for route in ("/api/v1/brain/health", "/api/v1/brain/generate"):
        response = client.get(route) if route.endswith("health") else client.post(route, json={})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthenticated"
