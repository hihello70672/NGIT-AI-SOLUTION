from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.modules.language.api import create_language_router
from services.api.modules.language.service import (
    LanguageProfile, LanguageService, RemoteControlRequest, TranslationResult,
    VoiceRequest, VisionRequest, validate_remote_control_request,
    validate_voice_request, validate_vision_request,
)


def test_script_detection_and_english_dialect_hints():
    service = LanguageService()
    assert service.detect("नमस्ते दुनिया").language == "hi"
    assert service.detect("Hola, gracias por venir").language == "es"
    assert service.detect("The colour is lovely").dialect == "en-GB"


def test_code_switch_detection_reports_secondary_language():
    result = LanguageService().detect("Hola gracias, and please help")
    assert result.language == "es"
    assert "en" in result.code_switches


def test_adaptation_preserves_content_and_changes_only_supported_style():
    service = LanguageService()
    assert service.adapt("Hey, I'm gonna check", LanguageProfile(formality="formal")) == "hello, I'm going to check"
    assert service.adapt("The result", LanguageProfile(register="warm")) == "The result."


def test_generation_requires_explicit_brain_adapter_and_adapts():
    service = LanguageService()
    with pytest.raises(RuntimeError):
        service.generate_response("hello", LanguageProfile())
    result = service.generate_response("hello", LanguageProfile(register="warm"), generator=lambda text, profile: "Welcome")
    assert result.text == "Welcome."
    assert result.language == "en"


def test_translation_adapter_contract_and_no_false_translation_claim():
    with pytest.raises(RuntimeError, match="not configured"):
        LanguageService().translate("hello", target_language="fr")
    translated = LanguageService(lambda text, source, target: "bonjour").translate("hello", target_language="fr")
    assert translated == TranslationResult("bonjour", "en", "fr", True)


def test_profile_preference_is_owner_scoped_and_optional():
    class Memory:
        def __init__(self): self.values = {}
        def get_language_profile(self, owner_id): return self.values.get(owner_id)
        def save_language_profile(self, owner_id, profile): self.values[owner_id] = profile
    memory = Memory()
    service = LanguageService(preference_memory=memory)
    profile = LanguageProfile(language="pt", dialect="pt-BR", register="warm")
    service.save_preference("user-a", profile)
    assert service.get_preference("user-a") == profile
    assert service.get_preference("user-b") is None
    with pytest.raises(ValueError): service.get_preference("")


def test_voice_vision_remote_contract_validation():
    assert validate_voice_request(VoiceRequest("transcribe", "en-US"))
    assert validate_vision_request(VisionRequest("ocr", "hi", "media:123"))
    assert validate_remote_control_request(RemoteControlRequest("request_action", "device-1", approval_reference="approval-1"))
    with pytest.raises(ValueError): validate_remote_control_request(RemoteControlRequest("request_action", "device-1"))
    with pytest.raises(ValueError): validate_voice_request(VoiceRequest("synthesize", "bad tag"))


def test_authenticated_profile_api_uses_context_identity():
    @dataclass
    class Context:
        user_id: str
    class Memory:
        def __init__(self): self.values = {}
        def get_language_profile(self, owner_id): return self.values.get(owner_id)
        def save_language_profile(self, owner_id, profile): self.values[owner_id] = profile
    app = FastAPI()
    app.include_router(create_language_router(LanguageService(preference_memory=Memory()), lambda: Context("trusted-user")))
    client = TestClient(app)
    response = client.put("/language/profile", json={"language": "fr", "register": "formal"})
    assert response.status_code == 200
    assert response.json()["language"] == "fr"
    assert client.get("/language/profile").json()["register"] == "formal"
