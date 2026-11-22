"""Brain REST contract tests using deterministic runtimes."""
from fastapi.testclient import TestClient

from services.api.app import app
from services.api.modules.brain import api as brain_api
from services.api.modules.brain.runtime import Generation, ModelDefinition


class FakeRuntime:
    async def generate(self, **kwargs):
        return Generation("contract answer", kwargs["model"])


def test_brain_api_model_list_generation_and_validation():
    brain_api.configure_models(ModelDefinition("local-test", FakeRuntime(), "test-model"))
    try:
        with TestClient(app) as client:
            models = client.get("/api/v1/brain/models")
            assert models.status_code == 200
            assert models.json()["models"][0]["model_id"] == "local-test"
            response = client.post("/api/v1/brain/generate", json={"text": "How are you?"})
            assert response.status_code == 200
            assert response.json()["text"] == "contract answer"
            assert response.json()["intent"] == "question"
            assert client.post("/api/v1/brain/generate", json={"text": "", "max_tokens": 0}).status_code == 422
    finally:
        brain_api.reset_configured_models()


def test_brain_api_reports_missing_runtime_without_provider_leakage():
    brain_api.configure_models()
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/brain/generate", json={"text": "Explain NGIT"})
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "model_unavailable"
    finally:
        brain_api.reset_configured_models()
