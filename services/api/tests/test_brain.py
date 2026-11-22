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


def definition(model_id, runtime, priority=10):
    return ModelDefinition(model_id, runtime, model_id, priority=priority)


def test_intent_classifier_fixed_evaluation_examples_and_confidence_range():
    classifier = HeuristicIntentRecognizer()
    examples = [
        ("Hi there", "greeting"), ("How does this work?", "question"),
        ("Write a Python function", "code"),
        ("Summarize this document", "summarization"),
        ("Translate this in Spanish", "translation"),
        ("Tell me a story", "general"),
    ]
    outcomes = [classifier.recognize(text) for text, _ in examples]
    assert [label for label, _ in outcomes] == [expected for _, expected in examples]
    assert all(0 <= confidence <= 1 for _, confidence in outcomes)


def test_model_registry_priority_selection_and_duplicate_rejection():
    registry = ModelRegistry()
    registry.register(definition("later", FakeRuntime(), priority=20))
    registry.register(definition("first", FakeRuntime(), priority=1))
    assert [entry.model_id for entry in registry.candidates()] == ["first", "later"]
    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition("first", FakeRuntime()))


def test_primary_local_runtime_generates_response():
    runtime = FakeRuntime("answer")
    registry = ModelRegistry()
    registry.register(definition("local", runtime))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("How are you?")))
    assert result.text == "answer" and result.model_id == "local"
    assert result.intent == "question" and result.confidence >= 0.35
    assert not result.fallback_used


def test_self_hosted_fallback_runs_only_when_enabled_and_primary_fails():
    primary, fallback = FakeRuntime(fails=True), FakeRuntime("fallback answer")
    registry = ModelRegistry()
    registry.register(definition("primary", primary))
    result = asyncio.run(BrainService(registry, fallback=definition("self-hosted", fallback)).respond(
        BrainRequest("Explain this", allow_fallback=True)
    ))
    assert result.text == "fallback answer" and result.fallback_used
    assert len(primary.calls) == len(fallback.calls) == 1


def test_disabled_fallback_is_not_called():
    primary, fallback = FakeRuntime(fails=True), FakeRuntime("must not run")
    registry = ModelRegistry()
    registry.register(definition("primary", primary))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry, fallback=definition("fallback", fallback)).respond(
            BrainRequest("Explain this", allow_fallback=False)
        ))
    assert error.value.code == "model_generation_failed"
    assert not fallback.calls


def test_input_confidence_and_generation_limits_are_validated():
    service = BrainService(ModelRegistry())
    with pytest.raises(BrainError) as empty:
        asyncio.run(service.respond(BrainRequest("", min_confidence=0)))
    assert empty.value.code == "validation_error"
    with pytest.raises(BrainError) as uncertain:
        asyncio.run(service.respond(BrainRequest("a", min_confidence=0.9)))
    assert uncertain.value.code == "low_confidence"
    with pytest.raises(BrainError) as invalid:
        asyncio.run(service.respond(BrainRequest("valid", max_tokens=0)))
    assert invalid.value.code == "validation_error"


def test_explicit_disabled_or_unknown_model_is_not_silently_rerouted():
    registry = ModelRegistry()
    registry.register(ModelDefinition("disabled", FakeRuntime(), "disabled", enabled=False))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("question?", model_id="missing")))
    assert error.value.code == "model_not_found"


def test_generation_failure_does_not_leak_runtime_details():
    registry = ModelRegistry()
    registry.register(definition("offline", FakeRuntime(fails=True)))
    with pytest.raises(BrainError) as error:
        asyncio.run(BrainService(registry).respond(BrainRequest("question?")))
    assert error.value.code == "model_generation_failed"
    assert "offline" not in error.value.message
