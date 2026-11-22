"""HTTP contract for the NGIT Brain."""
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.api.modules.brain.runtime import (
    BrainError, BrainRequest, BrainService, ModelDefinition, ModelRegistry,
    OpenAICompatibleRuntime,
)

router = APIRouter(prefix="/brain", tags=["brain"])
registry = ModelRegistry()


def _register_configured_models() -> ModelDefinition | None:
    """Build process-local routes from server environment, never client input."""
    local_url = os.getenv("NGIT_LOCAL_MODEL_BASE_URL", "").strip()
    if local_url:
        registry.register(ModelDefinition(
            model_id=os.getenv("NGIT_LOCAL_MODEL_ID", "local-default"),
            runtime=OpenAICompatibleRuntime(
                local_url, os.getenv("NGIT_LOCAL_MODEL_API_KEY") or None
            ),
            model_name=os.getenv("NGIT_LOCAL_MODEL_NAME", "local-model"),
            priority=10,
        ))
    fallback_url = os.getenv("NGIT_SELF_HOSTED_MODEL_BASE_URL", "").strip()
    if not fallback_url:
        return None
    return ModelDefinition(
        model_id=os.getenv("NGIT_SELF_HOSTED_MODEL_ID", "self-hosted-fallback"),
        runtime=OpenAICompatibleRuntime(
            fallback_url, os.getenv("NGIT_SELF_HOSTED_MODEL_API_KEY") or None
        ),
        model_name=os.getenv("NGIT_SELF_HOSTED_MODEL_NAME", "self-hosted-model"),
        priority=50,
    )


fallback = _register_configured_models()
brain = BrainService(registry, fallback=fallback)


class GenerateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    model_id: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=8192)
    min_confidence: float = Field(default=0.35, ge=0, le=1)
    allow_fallback: bool = True


class GenerateResponse(BaseModel):
    text: str
    intent: str
    confidence: float
    model_id: str
    fallback_used: bool


@router.get("/models")
def list_models() -> dict[str, list[dict[str, object]]]:
    return {"models": [
        {"model_id": item.model_id, "model_name": item.model_name,
         "capabilities": sorted(item.capabilities), "priority": item.priority}
        for item in registry.candidates()
    ]}


@router.post("/generate", response_model=GenerateResponse)
async def generate(body: GenerateRequest) -> GenerateResponse:
    try:
        result = await brain.respond(BrainRequest(
            text=body.text, model_id=body.model_id, temperature=body.temperature,
            max_tokens=body.max_tokens, min_confidence=body.min_confidence,
            allow_fallback=body.allow_fallback,
        ))
    except BrainError as exc:
        status = 503 if exc.code in {"model_unavailable", "model_generation_failed"} else 422
        raise HTTPException(status_code=status,
                            detail={"code": exc.code, "message": exc.message}) from exc
    return GenerateResponse(**result.__dict__)


def configure_models(primary: ModelDefinition | None,
                     fallback_model: ModelDefinition | None = None) -> None:
    """Explicit configuration hook for tests and application composition."""
    global registry, brain
    registry = ModelRegistry()
    if primary is not None:
        registry.register(primary)
    brain = BrainService(registry, fallback=fallback_model)


def reset_configured_models() -> None:
    """Rebuild configured runtime registry after test overrides."""
    global registry, brain
    registry = ModelRegistry()
    configured_fallback = _register_configured_models()
    brain = BrainService(registry, fallback=configured_fallback)


# Existing consumers/tests can replace registry and brain directly. The explicit
# configuration functions make lifecycle changes clear without duplicate services.
