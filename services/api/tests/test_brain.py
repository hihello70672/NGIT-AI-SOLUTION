"""Evaluation tests for Brain intent, confidence, routing, and fallback."""
import asyncio

import pytest

from services.api.modules.brain.runtime import (
    BrainError, BrainRequest, BrainService, Generation, HeuristicIntentRecognizer,
    ModelDefinition, ModelRegistry, RuntimeUnavailable,
)


class FakeRuntime:
    def __init__(self, output="test response", fails=False):
        self.output = output
        self.fails = fails
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        if self.fails:
            raise RuntimeUnavailable("offline")
        return Generation(self.output, kwargs["model"])


def definition(model_id, runtime, priority=10, enabled=True):
    return ModelDefinition(model_id, runtime, model_id, priority=priority, enabled=enabled)


def test_intent_fixed_evaluation_examples_and_confidence_range():
    classifier = HeuristicIntentRecognizer()
    examples = [
        ("Hi there", "greeting"), ("How does this work?", "question"),
        ("Write a Python function", "code"),
        ("Summarize this document", "summarization"),
        ("Translate this in Spanish", "translation"),
        ("Tell me a story", "general"),
    ]
    results = [classifier.recognize(text) for text, _ in examples]
    assert [label for label, _ in results] == [label for _, label in examples]
    assert all(0 <= score <= 1 for _, score in results)


def test_registry_routes_by_priority_and_rejects_duplicates():
    registry = ModelRegistry()
    registry.register(definition("later", FakeRuntime(), priority=20))
    registry.register(definition("first", FakeRuntime(), priority=1))
    assert [model.model_id for model in registry.candidates()] == ["first", "later"]
    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition("first", FakeRuntime()))


def test_local_primary_runtime_generates_response_and_detects_confidence():
    runtime = FakeRuntime("answer")
    registry = ModelRegistry()
    registry.register(definition("local", runtime))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("How are you?")))
    assert (result.text, result.model_id, result.intent) == ("answer", "local", "question")
    assert result.confidence >= 0.35 and not result.fallback_used
    assert runtime.calls[0]["temperature"] == 0.2


def test_self_hosted_fallback_is_used_only_when_enabled_and_primary_fails():
    primary, fallback = FakeRuntime(fails=True), FakeRuntime("fallback response")
    registry = ModelRegistry()
    registry.register(definition("primary", primary))
    service = BrainService(registry, fallback=definition("self-hosted", fallback))
    result = asyncio.run(service.respond(BrainRequest("Explain this")))
    assert result.text == "fallback response" and result.fallback_used
    assert len(primary.calls) == len(fallback.calls) == 1

    with pytest.raises(BrainError) as error:
        asyncio.run(service.respond(BrainRequest("Explain this", allow_fallback=False)))
    assert error.value.code == "model_generation_failed"
    assert len(fallback.calls) == 1


def test_failed_primary_candidate_routes_to_next_registry_model():
    unavailable, healthy = FakeRuntime(fails=True), FakeRuntime("second model")
    registry = ModelRegistry()
    registry.register(definition("first", unavailable, priority=1))
    registry.register(definition("second", healthy, priority=2))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("Explain this")))
    assert result.model_id == "second" and result.text == "second model"


def test_low_confidence_empty_input_and_generation_limits_are_rejected():
    service = BrainService(ModelRegistry())
    with pytest.raises(BrainError) as empty:
        asyncio.run(service.respond(BrainRequest("  ")))
    assert empty.value.code == "validation_error"
    with pytest.raises(BrainError) as uncertain:
        asyncio.run(service.respond(BrainRequest("a", min_confidence=0.9)))
    assert uncertain.value.code == "low_confidence"
    with pytest.raises(BrainError) as invalid:
        asyncio.run(service.respond(BrainRequest("valid", max_tokens=0)))
    assert invalid.value.code == "validation_error"


def test_explicit_disabled_or_unknown_model_is_not_silently_rerouted():
    registry = ModelRegistry()
    registry.register(definition("disabled", FakeRuntime(), enabled=False))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("question?", model_id="missing")))
    assert error.value.code == "model_not_found"


def test_generation_failure_does_not_expose_runtime_details():
    registry = ModelRegistry()
    registry.register(definition("offline", FakeRuntime(fails=True)))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("question?")))
    assert error.value.code == "model_generation_failed"
    assert "offline" not in error.value.message
