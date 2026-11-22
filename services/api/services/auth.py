"""Password verification and bearer-token lifecycle for identity service."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from services.api.security import Authenticator, AuthContext, SecretStore, SecurityError


class AuthService:
    """Credential service backed by the user repository and shared authenticator."""

    def __init__(self, users, authenticator: Authenticator):
        self.users, self.authenticator = users, authenticator
        pepper = SecretStore().get("PASSWORD_PEPPER")
        if not isinstance(pepper, str) or len(pepper.encode()) < 16:
            raise ValueError("PASSWORD_PEPPER must be configured and at least 16 bytes")
        self.pepper = pepper

    def _hash_password(self, password: str, salt: bytes | None = None) -> str:
        if not isinstance(password, str) or not 12 <= len(password) <= 128:
            raise ValueError("password length must be between 12 and 128 characters")
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.scrypt((password + self.pepper).encode(), salt=salt, n=2**14, r=8, p=1)
        return f"scrypt${salt.hex()}${digest.hex()}"

    def _verify(self, password: str, encoded: str) -> bool:
        try:
            scheme, salt_hex, expected = encoded.split("$", 2)
            if scheme != "scrypt":
                return False
            actual = self._hash_password(password, bytes.fromhex(salt_hex)).split("$", 2)[2]
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError, AttributeError):
            return False

    def register(self, email: str, password: str, display_name: str):
        user = self.users.create(email, self._hash_password(password), display_name)
        roles = set(user.get("roles") or ["user"])
        token = self.authenticator.issue(str(user["id"]), roles)
        return user, token

    def login(self, email: str, password: str):
        user = self.users.by_email(email)
        if not user or user.get("status") != "active" or not self._verify(password, user.get("password_hash", "")):
            raise SecurityError("unauthenticated", "Invalid email or password")
        roles = set(user.get("roles") or ["user"])
        return user, self.authenticator.issue(str(user["id"]), roles)

    def authenticate(self, token: str) -> AuthContext:
        context = self.authenticator.authenticate(token)
        user = self.users.by_id(context.user_id)
        if not user or user.get("status") != "active":
            self.authenticator.revoke(token)
            raise SecurityError("unauthenticated", "Authentication required")
        # Roles come from the authoritative server-side user record, not a
        # potentially stale role snapshot embedded in an issued token.
        roles = frozenset(user.get("roles") or ["user"])
        return AuthContext(context.user_id, roles, context.token_id)
