"""Brain REST contract tests with deterministic runtimes."""
from fastapi.testclient import TestClient

from services.api.app import app
from services.api.modules.brain import api as brain_api
from services.api.modules.brain.runtime import ModelDefinition


class FakeRuntime:
    async def generate(self, **kwargs):
        from services.api.modules.brain.runtime import Generation
        return Generation("contract answer", kwargs["model"])


def test_brain_api_models_generation_and_safe_unavailable(monkeypatch):
    brain_api.configure_models(ModelDefinition("local-test", FakeRuntime(), "test-model"))
    client = TestClient(app)
    models = client.get("/api/v1/brain/models")
    assert models.status_code == 200
    assert models.json()["models"][0]["model_id"] == "local-test"
    response = client.post("/api/v1/brain/generate", json={"text": "How are you?"})
    assert response.status_code == 200
    assert response.json()["text"] == "contract answer"
    assert response.json()["intent"] == "question"
    assert client.post("/api/v1/brain/generate", json={"text": "", "min_confidence": 0}).status_code == 422
    brain_api.configure_models(None)
    unavailable = client.post("/api/v1/brain/generate", json={"text": "Explain NGIT"})
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"]["code"] == "model_unavailable"
    brain_api.reset_configured_models()
