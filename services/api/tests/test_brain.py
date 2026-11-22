"""Evaluation tests for Brain intent, confidence, routing, and fallback."""
import asyncio

import pytest

from services.api.modules.brain.runtime import (
    BrainError, BrainRequest, BrainService, Generation, HeuristicIntentRecognizer,
    ModelDefinition, ModelRegistry, OpenAICompatibleRuntime, RuntimeUnavailable,
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
    examples = [("Hi there", "greeting"), ("How does this work?", "question"),
                ("Write a Python function", "code"), ("Summarize this", "summarization"),
                ("Translate into Spanish", "translation"), ("Tell me a story", "general")]
    results = [classifier.recognize(text) for text, _ in examples]
    assert [label for label, _ in results] == [expected for _, expected in examples]
    assert all(0 <= score <= 1 for _, score in results)
    assert classifier.recognize("  ") == ("unknown", 0.0)


def test_registry_orders_by_priority_and_validates_definitions():
    registry = ModelRegistry()
    registry.register(model("later", FakeRuntime(), priority=20))
    registry.register(model("first", FakeRuntime(), priority=1))
    assert [m.model_id for m in registry.candidates()] == ["first", "later"]
    with pytest.raises(ValueError, match="already registered"):
        registry.register(model("first", FakeRuntime()))
    with pytest.raises(ValueError, match="limits"):
        registry.register(ModelDefinition("bad", FakeRuntime(), "bad", timeout_seconds=0))


def test_primary_generates_answer_with_intent_and_confidence():
    runtime = FakeRuntime("answer")
    registry = ModelRegistry()
    registry.register(model("local", runtime))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("How are you?")))
    assert (result.text, result.model_id, result.intent) == ("answer", "local", "question")
    assert result.confidence == 0.82 and not result.fallback_used
    assert runtime.calls[0]["temperature"] == 0.2


def test_failed_primary_routes_to_next_registered_model():
    failed, secondary = FakeRuntime(fails=True), FakeRuntime("secondary")
    registry = ModelRegistry()
    registry.register(model("primary", failed, priority=1))
    registry.register(model("secondary", secondary, priority=2))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("Explain this")))
    assert result.model_id == "secondary" and result.text == "secondary"
    assert not result.fallback_used and len(failed.calls) == len(secondary.calls) == 1


def test_optional_fallback_can_be_disabled_and_errors_are_safe():
    registry = ModelRegistry()
    registry.register(model("local", FakeRuntime(fails=True)))
    service = BrainService(registry, fallback=model("self-hosted", FakeRuntime("fallback")))
    result = asyncio.run(service.respond(BrainRequest("Explain this")))
    assert result.text == "fallback" and result.fallback_used
    with pytest.raises(BrainError) as error:
        asyncio.run(service.respond(BrainRequest("Explain this", allow_fallback=False)))
    assert error.value.code == "model_generation_failed"
    assert "private runtime detail" not in error.value.message


def test_low_confidence_invalid_limits_and_explicit_model_validation():
    registry = ModelRegistry()
    registry.register(model("local", FakeRuntime()))
    service = BrainService(registry)
    for request in (BrainRequest("  "), BrainRequest("hello", min_confidence=0.99),
                    BrainRequest("hello", max_tokens=0), BrainRequest("hello", temperature=float("nan"))):
        with pytest.raises(BrainError):
            asyncio.run(service.respond(request))
    with pytest.raises(BrainError) as error:
        asyncio.run(service.respond(BrainRequest("question?", model_id="missing")))
    assert error.value.code == "model_not_found"


def test_runtime_url_rejects_embedded_secrets_and_query_data():
    for url in ("https://user:pass@model.local/v1", "http://model.local/v1?token=secret"):
        with pytest.raises(ValueError):
            OpenAICompatibleRuntime(url)


def test_generation_timeout_is_safely_reported():
    class SlowRuntime:
        async def generate(self, **kwargs):
            await asyncio.sleep(0.05)
            return Generation("late", "slow")
    registry = ModelRegistry()
    registry.register(ModelDefinition("slow", SlowRuntime(), "slow", timeout_seconds=0.001))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("help")))
    assert error.value.code == "model_generation_failed"
