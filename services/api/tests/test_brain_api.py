"""Brain REST contract tests with deterministic runtimes."""
from fastapi.testclient import TestClient

from services.api.app import app
from services.api.modules.brain import api as brain_api
from services.api.modules.brain.runtime import Generation, ModelDefinition


class FakeRuntime:
    async def generate(self, **kwargs):
        return Generation("contract answer", kwargs["model"])


def test_brain_api_model_list_generation_and_safe_unavailable_response():
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
            assert client.post("/api/v1/brain/generate", json={"text": ""}).status_code == 422
    finally:
        brain_api.reset_configured_models()


def test_brain_api_reports_no_configured_runtime_safely():
    brain_api.reset_configured_models()
    with TestClient(app) as client:
        response = client.post("/api/v1/brain/generate", json={"text": "Explain NGIT"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_unavailable"


def test_brain_api_validates_generation_bounds():
    with TestClient(app) as client:
        response = client.post("/api/v1/brain/generate", json={"text": "question?", "max_tokens": 0})
    assert response.status_code == 422
PY
services/api/modules/brain/api.py