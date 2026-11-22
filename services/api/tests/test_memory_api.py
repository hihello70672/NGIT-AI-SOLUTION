"""Memory route composition and authentication contract checks."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER","test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER","test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api.app import app

def test_memory_api_routes_are_composed_and_authenticated():
    paths={route.path for route in app.routes}
    assert "/api/v1/conversations" in paths
    assert "/api/v1/conversations/{conversation_id}/messages" in paths
    assert "/api/v1/memories/search" in paths
    with TestClient(app) as client:
        assert client.get("/api/v1/conversations").status_code==401

def test_memory_api_rejects_bad_pagination_without_auth():
    with TestClient(app) as client:
        response=client.get("/api/v1/memories",params={"limit":0})
        assert response.status_code==422
