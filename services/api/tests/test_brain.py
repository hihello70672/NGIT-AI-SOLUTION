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
            raise RuntimeUnavailable("private runtime detail")
        return Generation(self.output, kwargs["model"])


def definition(model_id, runtime, priority=10, enabled=True):
    return ModelDefinition(model_id, runtime, model_id, priority=priority, enabled=enabled)


def test_intent_evaluation_examples_and_confidence_range():
    classifier = HeuristicIntentRecognizer()
    examples = [
        ("Hi there", "greeting"), ("How does this work?", "question"),
        ("Write a Python function", "code"), ("Summarize this document", "summarization"),
        ("Translate this in Spanish", "translation"), ("Tell me a story", "general"),
    ]
    results = [classifier.recognize(text) for text, _ in examples]
    assert [label for label, _ in results] == [expected for _, expected in examples]
    assert all(0 <= score <= 1 for _, score in results)
    assert classifier.recognize("  ") == ("unknown", 0.0)


def test_registry_routes_by_priority_and_rejects_duplicate_or_bad_limits():
    registry = ModelRegistry()
    registry.register(definition("later", FakeRuntime(), priority=20))
    registry.register(definition("first", FakeRuntime(), priority=1))
    assert [model.model_id for model in registry.candidates()] == ["first", "later"]
    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition("first", FakeRuntime()))
    with pytest.raises(ValueError, match="limits"):
        registry.register(ModelDefinition("bad", FakeRuntime(), "bad", timeout_seconds=0))


def test_local_runtime_generation_and_confidence_detection():
    runtime = FakeRuntime("answer")
    registry = ModelRegistry()
    registry.register(definition("local", runtime))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("How are you?")))
    assert (result.text, result.model_id, result.intent) == ("answer", "local", "question")
    assert result.confidence >= 0.35 and not result.fallback_used
    assert runtime.calls[0]["temperature"] == 0.2


def test_fallback_opt_in_and_failed_primary_routes_to_next_model():
    primary, secondary = FakeRuntime(fails=True), FakeRuntime("secondary answer")
    registry = ModelRegistry()
    registry.register(definition("primary", primary, priority=1))
    registry.register(definition("secondary", secondary, priority=2))
    result = asyncio.run(BrainService(registry).respond(BrainRequest("Explain this")))
    assert result.model_id == "secondary" and not result.fallback_used
    assert len(primary.calls) == len(secondary.calls) == 1

    local, fallback = FakeRuntime(fails=True), FakeRuntime("fallback response")
    registry2 = ModelRegistry()
    registry2.register(definition("local", local))
    service = BrainService(registry2, fallback=definition("self-hosted", fallback))
    result = asyncio.run(service.respond(BrainRequest("Explain this")))
    assert result.text == "fallback response" and result.fallback_used
    with pytest.raises(BrainError) as error:
        asyncio.run(service.respond(BrainRequest("Explain this", allow_fallback=False)))
    assert error.value.code == "model_generation_failed"


def test_low_confidence_empty_input_and_generation_limits_are_rejected():
    service = BrainService(ModelRegistry())
    for request in (BrainRequest("  "), BrainRequest("a", min_confidence=0.9),
                    BrainRequest("valid", max_tokens=0),
                    BrainRequest("valid", temperature=float("nan"))):
        with pytest.raises(BrainError):
            asyncio.run(service.respond(request))


def test_explicit_unknown_disabled_or_incompatible_model_is_not_rerouted():
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
    assert "private runtime detail" not in error.value.message
    assert error.value.code == "model_generation_failed"


@pytest.mark.parametrize("url", ["file:///etc/passwd", "https://user:pass@host/model",
                                 "https://host/path?token=secret"])
def test_runtime_rejects_unsafe_url_shapes(url):
    from services.api.modules.brain.runtime import OpenAICompatibleRuntime
    with pytest.raises(ValueError):
        OpenAICompatibleRuntime(url)
