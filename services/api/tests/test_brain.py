"""Evaluation tests for Brain intent, confidence, routing and fallback."""
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


def model(model_id, runtime, priority=10):
    return ModelDefinition(model_id, runtime, model_id, priority=priority)


def test_intent_recognizer_baseline_evaluation():
    classifier = HeuristicIntentRecognizer()
    examples = [
        ("Hi there", "greeting"),
        ("How does this work?", "question"),
        ("Write a Python function", "code"),
        ("Summarize this document", "summarization"),
        ("Translate this in Spanish", "translation"),
        ("Tell me a story", "general"),
    ]
    outcomes = [classifier.recognize(text) for text, _ in examples]
    accuracy = sum(intent == expected for (intent, _), (_, expected) in zip(outcomes, examples)) / len(examples)
    assert accuracy == 1.0
    assert all(0 <= confidence <= 1 for _, confidence in outcomes)


def test_routes_by_priority_and_returns_confidence():
    first, second = FakeRuntime("answer one"), FakeRuntime("answer two")
    registry = ModelRegistry()
    registry.register(model("second", second, priority=20))
    registry.register(model("first", first, priority=1))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("What is NGIT?")))
    assert result.text == "answer one"
    assert result.model_id == "first"
    assert result.intent == "question" and result.confidence >= 0.35
    assert len(first.calls) == 1 and not second.calls


def test_falls_back_only_when_enabled_and_primary_fails():
    primary, fallback = FakeRuntime(fails=True), FakeRuntime("fallback answer")
    registry = ModelRegistry()
    registry.register(model("primary", primary))
    result = asyncio.run(BrainService(registry, fallback=model("fallback", fallback)).respond(
        BrainRequest("Explain this", allow_fallback=True)
    ))
    assert result.text == "fallback answer" and result.fallback_used


def test_disabled_fallback_does_not_call_fallback_runtime():
    primary, fallback = FakeRuntime(fails=True), FakeRuntime("should not run")
    registry = ModelRegistry()
    registry.register(model("primary", primary))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry, fallback=model("fallback", fallback)).respond(
            BrainRequest("Explain this", allow_fallback=False)
        ))
    assert error.value.code == "model_generation_failed"
    assert not fallback.calls


def test_low_confidence_and_empty_input_are_rejected():
    service = BrainService(ModelRegistry())
    with pytest.raises(BrainError) as low:
        asyncio.run(service.respond(BrainRequest("", min_confidence=0)))
    assert low.value.code == "validation_error"
    with pytest.raises(BrainError) as uncertain:
        asyncio.run(service.respond(BrainRequest("a", min_confidence=0.9)))
    assert uncertain.value.code == "low_confidence"


def test_registry_rejects_duplicate_and_selects_enabled_chat_models():
    runtime = FakeRuntime()
    registry = ModelRegistry()
    registry.register(model("available", runtime))
    with pytest.raises(ValueError):
        registry.register(model("available", runtime))
    assert [item.model_id for item in registry.candidates()] == ["available"]


def test_generation_failure_exposes_safe_error_not_runtime_detail():
    registry = ModelRegistry()
    registry.register(model("offline", FakeRuntime(fails=True)))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("Explain this")))
    assert error.value.code == "model_generation_failed"
    assert "offline" not in error.value.message
