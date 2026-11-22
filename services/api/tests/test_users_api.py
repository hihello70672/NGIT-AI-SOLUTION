from fastapi.testclient import TestClient

from services.api.app import app


def test_health_endpoint_is_live():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unauthenticated_profile_has_safe_error_shape():
    response = TestClient(app).get("/api/v1/users/me")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "unauthenticated"
    assert error["request_id"]
    assert "details" in error
