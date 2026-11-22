"""Provider-neutral local and self-hosted text-generation runtimes."""
from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

import httpx


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    finish_reason: str | None = None


class ModelRuntime(Protocol):
    """Cancelable asynchronous text-generation contract."""

    async def generate(self, *, model: str, messages: list[dict[str, str]], temperature: float,
                       max_tokens: int, timeout: float) -> Generation: ...


class RuntimeErrorBase(Exception):
    """Safe caller-facing runtime failure."""


class RuntimeUnavailable(RuntimeErrorBase):
    """Runtime failed or returned unusable output."""


class OpenAICompatibleRuntime:
    """HTTP adapter for explicitly configured local/self-hosted endpoints."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Model runtime URL must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Model runtime URL must not contain credentials or query data")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def generate(self, *, model: str, messages: list[dict[str, str]], temperature: float,
                       max_tokens: int, timeout: float) -> Generation:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        body = {"model": model, "messages": messages, "temperature": temperature,
                "max_tokens": max_tokens}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=body,
                                             headers=headers)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeUnavailable("Model runtime request failed") from exc
        try:
            choice = payload["choices"][0]
            text = choice["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("empty response")
            return Generation(text.strip(), str(payload.get("model") or model),
                              choice.get("finish_reason"))
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeUnavailable("Model runtime returned an invalid response") from exc


@dataclass(frozen=True)
class ModelDefinition:
    model_id: str
    runtime: ModelRuntime
    model_name: str
    capabilities: frozenset[str] = frozenset({"chat"})
    priority: int = 100
    enabled: bool = True
    timeout_seconds: float = 60.0
    max_tokens: int = 1024


class ModelRegistry:
    """In-process model catalog; durable administration is a separate concern."""

    def __init__(self) -> None:
        self._models: dict[str, ModelDefinition] = {}

    def register(self, definition: ModelDefinition) -> None:
        if not definition.model_id.strip() or not definition.model_name.strip():
            raise ValueError("model identifiers must not be empty")
        if (not math.isfinite(definition.timeout_seconds) or definition.timeout_seconds <= 0
                or definition.max_tokens <= 0 or not definition.capabilities):
            raise ValueError("model limits and capabilities must be valid")
        if definition.model_id in self._models:
            raise ValueError(f"model already registered: {definition.model_id}")
        self._models[definition.model_id] = definition

    def get(self, model_id: str) -> ModelDefinition | None:
        return self._models.get(model_id)

    def candidates(self, capability: str = "chat") -> list[ModelDefinition]:
        return sorted((m for m in self._models.values()
                       if m.enabled and capability in m.capabilities),
                      key=lambda m: (m.priority, m.model_id))


@dataclass(frozen=True)
class BrainRequest:
    text: str
    system_prompt: str = "You are NGIT, a helpful assistant."
    model_id: str | None = None
    temperature: float = 0.2
    max_tokens: int | None = None
    min_confidence: float = 0.35
    allow_fallback: bool = True


@dataclass(frozen=True)
class BrainResponse:
    text: str
    intent: str
    confidence: float
    model_id: str
    fallback_used: bool


class IntentRecognizer(Protocol):
    def recognize(self, text: str) -> tuple[str, float]: ...


class HeuristicIntentRecognizer:
    """Deterministic offline baseline classifier; not a trained model."""

    _RULES = (
        ("greeting", ("hello", "hi", "hey", "good morning", "good evening")),
        ("question", ("what", "why", "when", "where", "who", "how", "?")),
        ("code", ("python", "javascript", "typescript", "code", "function", "bug")),
        ("summarization", ("summarize", "summary", "tl;dr", "key points")),
        ("translation", ("translate", "in spanish", "in french", "in arabic")),
    )

    def recognize(self, text: str) -> tuple[str, float]:
        normalized = " ".join(text.lower().split())
        if not normalized:
            return "unknown", 0.0
        for intent, terms in self._RULES:
            if any(term in normalized for term in terms):
                return intent, 0.82
        return "general", 0.55


class BrainError(Exception):
    """Domain error with stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BrainService:
    """Intent, confidence, model routing, generation, and optional fallback."""

    def __init__(self, registry: ModelRegistry, recognizer: IntentRecognizer | None = None,
                 fallback: ModelDefinition | None = None) -> None:
        self.registry = registry
        self.recognizer = recognizer or HeuristicIntentRecognizer()
        self.fallback = fallback

    async def respond(self, request: BrainRequest) -> BrainResponse:
        text = request.text.strip()
        if not text:
            raise BrainError("validation_error", "Input text must not be empty")
        if not math.isfinite(request.temperature) or not 0 <= request.temperature <= 2:
            raise BrainError("validation_error", "Temperature must be between 0 and 2")
        if request.max_tokens is not None and not 1 <= request.max_tokens <= 8192:
            raise BrainError("validation_error", "Maximum tokens must be between 1 and 8192")
        if not math.isfinite(request.min_confidence) or not 0 <= request.min_confidence <= 1:
            raise BrainError("validation_error", "Minimum confidence must be between 0 and 1")
        intent, confidence = self.recognizer.recognize(text)
        if confidence < request.min_confidence:
            raise BrainError("low_confidence", "Could not confidently identify the request")

        if request.model_id:
            selected = self.registry.get(request.model_id)
            if selected is None or not selected.enabled or "chat" not in selected.capabilities:
                raise BrainError("model_not_found", "Requested model is unavailable")
            candidates = [selected]
        else:
            candidates = self.registry.candidates("chat")
        if not candidates:
            raise BrainError("model_unavailable", "No chat model is configured")

        messages = [{"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": text}]
        attempted: set[str] = set()
        last_error: RuntimeErrorBase | None = None
        queue = list(candidates)
        if request.allow_fallback and self.fallback is not None:
            queue.append(self.fallback)
        for definition in queue:
            if definition.model_id in attempted:
                continue
            attempted.add(definition.model_id)
            try:
                result = await asyncio.wait_for(
                    definition.runtime.generate(
                        model=definition.model_name, messages=messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens or definition.max_tokens,
                        timeout=definition.timeout_seconds),
                    timeout=definition.timeout_seconds)
                if not isinstance(result, Generation) or not result.text.strip():
                    raise RuntimeUnavailable("Model runtime returned unusable output")
                return BrainResponse(result.text.strip(), intent, confidence, definition.model_id,
                                     definition not in candidates)
            except (RuntimeErrorBase, asyncio.TimeoutError) as exc:
                last_error = (exc if isinstance(exc, RuntimeErrorBase)
                              else RuntimeUnavailable("Model runtime timed out"))
        raise BrainError("model_generation_failed", "No configured model could generate a response") from last_error


__all__ = ["BrainError", "BrainRequest", "BrainResponse", "BrainService", "Generation",
           "HeuristicIntentRecognizer", "IntentRecognizer", "ModelDefinition", "ModelRegistry",
           "ModelRuntime", "OpenAICompatibleRuntime", "RuntimeErrorBase", "RuntimeUnavailable"]
