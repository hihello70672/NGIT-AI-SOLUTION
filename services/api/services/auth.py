"""Password verification and bearer token lifecycle."""
import hashlib
import hmac
import os
import secrets

from services.api.security import Authenticator, AuthContext, SecurityError


class AuthService:
    def __init__(self, users, authenticator: Authenticator):
        self.users, self.authenticator = users, authenticator
        self.pepper = os.getenv("PASSWORD_PEPPER", "")
        if not self.pepper or len(self.pepper.encode()) < 16:
            raise ValueError("PASSWORD_PEPPER must be configured and at least 16 bytes")

    def _hash_password(self, password: str, salt: bytes | None = None) -> str:
        if not isinstance(password, str) or not 12 <= len(password) <= 1024:
            raise ValueError("password length must be between 12 and 1024 characters")
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.scrypt((password + self.pepper).encode(), salt=salt, n=2**14, r=8, p=1)
        return f"scrypt${salt.hex()}${digest.hex()}"

    def _verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, salt_hex, digest_hex = encoded.split("$", 2)
            if algorithm != "scrypt":
                return False
            actual = hashlib.scrypt((password + self.pepper).encode(), salt=bytes.fromhex(salt_hex),
                                    n=2**14, r=8, p=1).hex()
            return hmac.compare_digest(actual, digest_hex)
        except (ValueError, TypeError, AttributeError):
            return False

    def register(self, email: str, password: str, display_name: str):
        password_hash = self._hash_password(password)
        user = self.users.create(email, password_hash, display_name)
        token = self.authenticator.issue(str(user["id"]), set(user.get("roles", ["user"])))
        user["roles"] = list(user.get("roles", ["user"]))
        return user, token

    def login(self, email: str, password: str):
        user = self.users.by_email(email)
        if not user or user["status"] != "active" or not self._verify(password, user["password_hash"]):
            raise SecurityError("unauthenticated", "Invalid email or password")
        return user, self.authenticator.issue(str(user["id"]), set(user.get("roles", ["user"])))

    def authenticate(self, token: str) -> AuthContext:
        context = self.authenticator.authenticate(token)
        user = self.users.by_id(context.user_id)
        if not user or user["status"] != "active":
            self.authenticator.revoke(token)
            raise SecurityError("unauthenticated", "Authentication required")
        # Role state is read from the server on every request, not trusted from token claims.
        return AuthContext(context.user_id, frozenset(user.get("roles", [])), context.token_id)
