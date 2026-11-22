"""Brain API contract tests; model backends are replaced with deterministic fakes."""
from fastapi.testclient import TestClient

from services.api import app as api_module
from services.api.modules.brain import api as brain_api
from services.api.modules.brain.runtime import (
    BrainService, Generation, ModelDefinition, ModelRegistry,
)


class FakeRuntime:
    async def generate(self, **kwargs):
        return Generation("mock response", kwargs["model"])


def test_brain_routes_expose_generation_and_model_registry(monkeypatch):
    registry = ModelRegistry()
    registry.register(ModelDefinition("test", FakeRuntime(), "test-model"))
    monkeypatch.setattr(brain_api, "registry", registry)
    monkeypatch.setattr(brain_api, "brain", BrainService(registry))
    client = TestClient(api_module.app)
    models = client.get("/api/v1/brain/models")
    assert models.status_code == 200
    assert models.json()["models"][0]["model_id"] == "test"
    response = client.post("/api/v1/brain/generate", json={"text": "How are you?"})
    assert response.status_code == 200
    assert response.json()["text"] == "mock response"
    assert response.json()["intent"] == "question"


def test_generate_without_runtime_returns_actionable_unavailable(monkeypatch):
    registry = ModelRegistry()
    monkeypatch.setattr(brain_api, "registry", registry)
    monkeypatch.setattr(brain_api, "brain", BrainService(registry))
    response = TestClient(api_module.app).post(
        "/api/v1/brain/generate", json={"text": "Explain NGIT"}
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_unavailable"
