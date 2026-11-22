import pytest

from services.api.services.auth import AuthService
from services.api.security import AuthContext, Authenticator, SecurityError


class Users:
    def __init__(self, user):
        self.user = user

    def by_email(self, _email):
        return self.user

    def create(self, email, password_hash, display_name):
        return {"id": "u-1", "email": email, "password_hash": password_hash,
                "display_name": display_name, "status": "active", "roles": ["user"]}


def test_register_hashes_password_and_issues_user_role_token():
    auth = AuthService(Users(None), Authenticator("t" * 32), "p" * 16)
    user, token = auth.register("person@example.com", "correct horse battery", "Person")
    assert user["password_hash"] != "correct horse battery"
    assert auth.authenticate(token).user_id == "u-1"
    assert auth.authenticate(token).roles == frozenset({"user"})


def test_login_is_generic_for_unknown_user_and_wrong_password():
    auth = AuthService(Users(None), Authenticator("t" * 32), "p" * 16)
    with pytest.raises(SecurityError) as error:
        auth.login("unknown@example.com", "wrong password")
    assert error.value.code == "unauthenticated"


def test_logout_revokes_token():
    authenticator = Authenticator("t" * 32)
    token = authenticator.issue("u-1", frozenset({"user"}))
    authenticator.revoke(token)
    with pytest.raises(SecurityError):
        authenticator.authenticate(token)
