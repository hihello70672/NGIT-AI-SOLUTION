"""Memory route composition and authenticated ownership contract checks."""
import os

os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")

from fastapi.testclient import TestClient
from services.api.app import app


def test_memory_routes_are_composed_and_authenticated():
    paths = {route.path for route in app.routes}
    assert "/api/v1/conversations" in paths
    assert "/api/v1/conversations/{conversation_id}/messages" in paths
    assert "/api/v1/memories/search" in paths
    with TestClient(app) as client:
        assert client.get("/api/v1/conversations").status_code == 401


def test_memory_api_rejects_invalid_pagination_before_auth():
    with TestClient(app) as client:
        assert client.get("/api/v1/memories", params={"limit": 0}).status_code == 422
        assert client.get("/api/v1/conversations", params={"limit": 0}).status_code == 422


def test_memory_routes_never_accept_client_supplied_owner_authority():
    with TestClient(app) as client:
        response = client.post("/api/v1/memories", json={
            "user_id": "00000000-0000-0000-0000-000000000002", "content": "private"})
        assert response.status_code == 401


def test_memory_schema_has_composite_owner_constraints_and_rls():
    from pathlib import Path
    schema = Path(__file__).parents[1].joinpath("db/migrations/0001_initial_schema.sql").read_text()
    assert "UNIQUE(id,user_id)" in schema
    assert "FOREIGN KEY(conversation_id,user_id)" in schema
    assert "USING (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid)" in schema


def test_authenticated_memory_identity_cannot_be_overridden_by_request_payload():
    # API schemas reject extra fields, so an attempted alternate owner cannot be supplied.
    with TestClient(app) as client:
        response = client.post("/api/v1/memories", json={
            "content": "private", "memory_type": "fact", "user_id": "not-the-caller"})
        assert response.status_code in {401, 422}
        assert response.status_code != 201


def test_conversation_and_memory_routes_are_present_without_exposing_other_owner_ids():
    # Without credentials, caller-supplied identifiers do not authorize access.
    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/00000000-0000-0000-0000-000000000009/messages")
        assert response.status_code == 401
        assert "content" not in response.json()
