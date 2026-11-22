"""Password verification and bearer-token lifecycle for identity service."""
import hashlib
import hmac
import os
import secrets

from services.api.security import Authenticator, AuthContext, SecurityError


class AuthService:
    def __init__(self, users, authenticator: Authenticator):
        self.users, self.authenticator = users, authenticator
        self.pepper = os.getenv("PASSWORD_PEPPER", "")
        if len(self.pepper.encode()) < 16:
            raise ValueError("PASSWORD_PEPPER must contain at least 16 bytes")

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
        user["roles"] = list(user.get("roles") or ["user"])
        return user, self.authenticator.issue(str(user["id"]), set(user["roles"]))

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
        return AuthContext(context.user_id, frozenset(user.get("roles") or []), context.token_id)
