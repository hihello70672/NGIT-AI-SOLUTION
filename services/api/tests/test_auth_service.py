"""Unit tests for password storage and authentication lifecycle."""
import pytest
from services.api.security import Authenticator, SecurityError
from services.api.services.auth import AuthService


class Repository:
    def __init__(self): self.record = None
    def create(self, email, password_hash, display_name):
        self.record = {"id": "u-1", "email": email, "password_hash": password_hash, "display_name": display_name, "status": "active", "roles": ["user"]}
        return self.record
    def by_email(self, email): return self.record if self.record and self.record["email"] == email else None
    def by_id(self, user_id): return self.record if self.record and self.record["id"] == user_id else None


def service(monkeypatch):
    monkeypatch.setenv("PASSWORD_PEPPER", "unit-test-password-pepper")
    return AuthService(Repository(), Authenticator("a" * 32))


def test_password_hash_and_login(monkeypatch):
    auth = service(monkeypatch)
    user, token = auth.register("u@example.com", "a-secure-password", "User")
    assert "a-secure-password" not in user["password_hash"]
    assert auth.login("u@example.com", "a-secure-password")[0]["id"] == "u-1"
    with pytest.raises(SecurityError): auth.login("u@example.com", "wrong-password")
    assert auth.authenticate(token).user_id == "u-1"


def test_inactive_user_invalidates_tokens(monkeypatch):
    auth = service(monkeypatch)
    _, token = auth.register("u@example.com", "a-secure-password", "User")
    auth.users.record["status"] = "disabled"
    with pytest.raises(SecurityError): auth.authenticate(token)
