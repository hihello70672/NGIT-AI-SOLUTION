from services.api.schemas import LoginRequest, RegisterRequest, UserUpdateRequest
from pydantic import ValidationError


def test_register_email_password_and_profile_validation():
    RegisterRequest(email="one@example.com", password="long-password-123", display_name="  One  ")
    try:
        RegisterRequest(email="bad", password="short", display_name=" ")
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid registration accepted")


def test_login_rejects_unknown_fields():
    try:
        LoginRequest(email="one@example.com", password="password", elevated=True)
    except ValidationError:
        pass
    else:
        raise AssertionError("unknown login field accepted")


def test_update_requires_nonblank_optional_name():
    try:
        UserUpdateRequest(display_name=" ")
    except ValidationError:
        pass
    else:
        raise AssertionError("blank display name accepted")
    assert UserUpdateRequest(display_name=" Updated ").display_name == "Updated"
