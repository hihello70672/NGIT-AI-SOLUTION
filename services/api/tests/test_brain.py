"""Evaluation tests for Brain intent, confidence, routing, and fallback."""
import asyncio

import pytest

from services.api.modules.brain.runtime import (
    BrainError, BrainRequest, BrainService, Generation, HeuristicIntentRecognizer,
    ModelDefinition, ModelRegistry, RuntimeUnavailable,
)


class FakeRuntime:
    def __init__(self, output="test response", fails=False):
        self.output, self.fails, self.calls = output, fails, []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        if self.fails:
            raise RuntimeUnavailable("private runtime detail")
        return Generation(self.output, kwargs["model"])


def model(model_id, runtime, priority=10, enabled=True):
    return ModelDefinition(model_id, runtime, model_id, priority=priority, enabled=enabled)


def test_intent_evaluation_examples_and_confidence_range():
    classifier = HeuristicIntentRecognizer()
    cases = [("Hi there", "greeting"), ("How does this work?", "question"),
             ("Write a Python function", "code"), ("Summarize this", "summarization"),
             ("Translate this in Spanish", "translation"), ("Tell me a story", "general")]
    outcomes = [classifier.recognize(text) for text, _ in cases]
    assert [label for label, _ in outcomes] == [expected for _, expected in cases]
    assert all(0 <= score <= 1 for _, score in outcomes)
    assert classifier.recognize("  ") == ("unknown", 0.0)


def test_registry_priority_capability_and_validation():
    registry = ModelRegistry()
    registry.register(model("later", FakeRuntime(), priority=20))
    registry.register(model("first", FakeRuntime(), priority=1))
    assert [entry.model_id for entry in registry.candidates()] == ["first", "later"]
    with pytest.raises(ValueError, match="already registered"):
        registry.register(model("first", FakeRuntime()))
    with pytest.raises(ValueError, match="limits"):
        registry.register(ModelDefinition("bad", FakeRuntime(), "bad", timeout_seconds=0))


def test_local_model_generation_and_intent_confidence():
    runtime = FakeRuntime("answer")
    registry = ModelRegistry()
    registry.register(model("local", runtime))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("How are you?")))
    assert (result.text, result.model_id, result.intent) == ("answer", "local", "question")
    assert result.confidence >= 0.35 and not result.fallback_used
    assert runtime.calls[0]["temperature"] == 0.2


def test_failed_primary_routes_to_next_registered_model():
    first, second = FakeRuntime(fails=True), FakeRuntime("secondary")
    registry = ModelRegistry()
    registry.register(model("primary", first, priority=1))
    registry.register(model("secondary", second, priority=2))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("Explain this")))
    assert result.model_id == "secondary" and not result.fallback_used
    assert len(first.calls) == len(second.calls) == 1


def test_optional_self_hosted_fallback_and_opt_out():
    primary, fallback = FakeRuntime(fails=True), FakeRuntime("fallback answer")
    registry = ModelRegistry()
    registry.register(model("local", primary))
    service = BrainService(registry, fallback=model("self-hosted", fallback))
    result = asyncio.run(service.respond(BrainRequest("Explain this")))
    assert result.text == "fallback answer" and result.fallback_used
    with pytest.raises(BrainError) as error:
        asyncio.run(service.respond(BrainRequest("Explain this", allow_fallback=False)))
    assert error.value.code == "model_generation_failed"
    assert "private runtime detail" not in error.value.message


def test_low_confidence_and_invalid_generation_limits_are_rejected():
    registry = ModelRegistry()
    registry.register(model("local", FakeRuntime()))
    service = BrainService(registry)
    for request in (BrainRequest(" "), BrainRequest("hello", min_confidence=0.99),
                    BrainRequest("hello", max_tokens=0), BrainRequest("hello", temperature=float("nan"))):
        with pytest.raises(BrainError):
            asyncio.run(service.respond(request))


def test_unknown_or_disabled_explicit_model_is_not_silently_rerouted():
    registry = ModelRegistry()
    registry.register(model("disabled", FakeRuntime(), enabled=False))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("question?", model_id="missing")))
    assert error.value.code == "model_not_found"
PY
services/api/tests/test_brain_api.py