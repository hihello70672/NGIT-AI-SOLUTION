"""Deterministic multilingual helpers and opt-in modality contracts.

This module deliberately has no required external model dependency. A host application
may inject a translator/generator adapter; the built-in path provides bounded,
transparent behavior and never pretends to translate when no adapter exists.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Protocol
import re


@dataclass(frozen=True)
class LanguageProfile:
    language: str = "en"
    dialect: str | None = None
    register: str = "neutral"
    formality: str = "balanced"
    response_language: str | None = None
    code_switching: bool = True

    def __post_init__(self) -> None:
        for name in ("language", "response_language"):
            value = getattr(self, name)
            if value is not None and not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", value):
                raise ValueError(f"{name} must be a language tag such as en or pt-BR")
        if self.dialect is not None and (len(self.dialect) > 64 or not self.dialect.strip()):
            raise ValueError("dialect must be a non-empty label of at most 64 characters")
        if self.register not in {"neutral", "casual", "formal", "technical", "warm"}:
            raise ValueError("unsupported communication register")
        if self.formality not in {"informal", "balanced", "formal"}:
            raise ValueError("unsupported formality preference")


@dataclass(frozen=True)
class LanguageResult:
    text: str
    language: str
    confidence: float
    dialect: str | None = None
    code_switches: tuple[str, ...] = ()


@dataclass(frozen=True)
class TranslationResult:
    text: str
    source_language: str
    target_language: str
    translated: bool


class Translator(Protocol):
    def __call__(self, text: str, source_language: str, target_language: str) -> str: ...


class PreferenceMemory(Protocol):
    """Published memory boundary; owner identity comes from trusted server context."""
    def get_language_profile(self, owner_id: str) -> LanguageProfile | None: ...
    def save_language_profile(self, owner_id: str, profile: LanguageProfile) -> None: ...


@dataclass(frozen=True)
class VoiceRequest:
    operation: str
    language: str
    text: str | None = None
    audio_reference: str | None = None
    voice_id: str | None = None


@dataclass(frozen=True)
class VisionRequest:
    operation: str
    language: str
    media_reference: str
    prompt: str | None = None


@dataclass(frozen=True)
class RemoteControlRequest:
    operation: str
    target_id: str
    parameters: Mapping[str, str] = field(default_factory=dict)
    approval_reference: str | None = None


class LanguageService:
    """Language detection, dialect hints, adaptation, response and translation contracts."""

    _HINTS: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("hi", re.compile(r"[\u0900-\u097f]")),
        ("ar", re.compile(r"[\u0600-\u06ff]")),
        ("ru", re.compile(r"[\u0400-\u04ff]")),
        ("zh", re.compile(r"[\u4e00-\u9fff]")),
        ("ja", re.compile(r"[\u3040-\u30ff]")),
        ("ko", re.compile(r"[\uac00-\ud7af]")),
        ("th", re.compile(r"[\u0e00-\u0e7f]")),
        ("el", re.compile(r"[\u0370-\u03ff]")),
        ("he", re.compile(r"[\u0590-\u05ff]")),
    )
    _WORD_HINTS: Mapping[str, frozenset[str]] = {
        "es": frozenset({"hola", "gracias", "buenos", "porque", "quiero", "estoy"}),
        "fr": frozenset({"bonjour", "merci", "avec", "pourquoi", "je", "nous"}),
        "de": frozenset({"hallo", "danke", "und", "nicht", "ich", "bitte"}),
        "pt": frozenset({"olá", "obrigado", "você", "não", "porque", "estou"}),
        "it": frozenset({"ciao", "grazie", "perché", "sono", "questa", "buongiorno"}),
        "en": frozenset({"the", "and", "what", "please", "hello", "thanks"}),
    }
    _DIALECT_HINTS: Mapping[str, Mapping[str, tuple[str, ...]]] = {
        "en": {"en-US": ("color", "sidewalk", "truck"), "en-GB": ("colour", "pavement", "lorry"), "en-AU": ("arvo", "mate", "reckon")},
        "pt": {"pt-BR": ("você", "celular", "ônibus"), "pt-PT": ("telemóvel", "autocarro", "fixe")},
    }

    def __init__(self, translator: Translator | None = None, preference_memory: PreferenceMemory | None = None):
        self._translator = translator
        self._memory = preference_memory

    def detect(self, text: str, *, preferred_language: str = "en") -> LanguageResult:
        if not isinstance(text, str) or not text.strip() or len(text) > 20_000:
            raise ValueError("text must contain 1 to 20000 characters")
        script_hits = [(lang, len(pattern.findall(text))) for lang, pattern in self._HINTS]
        script_hits = [(lang, count) for lang, count in script_hits if count]
        words = re.findall(r"[\w’'-]+", text.casefold(), flags=re.UNICODE)
        tokens = set(words)
        lexical = [(lang, len(tokens & hints)) for lang, hints in self._WORD_HINTS.items()]
        lexical = [(lang, score) for lang, score in lexical if score]
        scores: dict[str, int] = {}
        for lang, count in script_hits:
            scores[lang] = count * 3
        for lang, count in lexical:
            scores[lang] = scores.get(lang, 0) + count
        if not scores:
            language, confidence = preferred_language, 0.35
        else:
            ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
            language = ranked[0][0]
            total = sum(scores.values())
            confidence = min(0.99, scores[language] / max(1, total))
        dialect = None
        for tag, hints in self._DIALECT_HINTS.get(language, {}).items():
            if any(hint in tokens for hint in hints):
                dialect = tag
                break
        switches = tuple(lang for lang, score in sorted(scores.items(), key=lambda item: -item[1]) if lang != language and score > 0)
        return LanguageResult(text=text, language=language, confidence=confidence, dialect=dialect, code_switches=switches)

    def adapt(self, text: str, profile: LanguageProfile) -> str:
        """Apply safe, non-semantic presentation adjustments without rewriting meaning."""
        if not isinstance(text, str) or len(text) > 20_000:
            raise ValueError("text must be a string of at most 20000 characters")
        value = text.strip()
        if profile.register == "warm" and value and value[-1] not in "!?…":
            value += "."
        if profile.register == "technical":
            return value
        if profile.formality == "formal":
            value = re.sub(r"\b(hey|hiya)\b", "hello", value, flags=re.IGNORECASE)
            value = re.sub(r"\b(gonna)\b", "going to", value, flags=re.IGNORECASE)
        elif profile.formality == "informal":
            value = re.sub(r"\b(therefore)\b", "so", value, flags=re.IGNORECASE)
        return value

    def generate_response(self, text: str, profile: LanguageProfile, *, generator: Callable[[str, LanguageProfile], str] | None = None) -> LanguageResult:
        if generator is None:
            raise RuntimeError("response generation requires an explicitly configured Brain generator")
        if not callable(generator):
            raise ValueError("generator must be callable")
        detected = self.detect(text, preferred_language=profile.language)
        result = generator(text, profile)
        if not isinstance(result, str) or not result.strip() or len(result) > 20_000:
            raise ValueError("generator returned an invalid response")
        return LanguageResult(self.adapt(result, profile), profile.response_language or profile.language, detected.confidence, profile.dialect, detected.code_switches)

    def translate(self, text: str, *, target_language: str, source_language: str | None = None) -> TranslationResult:
        detected = self.detect(text, preferred_language=source_language or "en")
        source = source_language or detected.language
        if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", target_language):
            raise ValueError("target_language must be a language tag")
        if self._translator is None:
            if source == target_language:
                return TranslationResult(text, source, target_language, False)
            raise RuntimeError("translation adapter is not configured")
        translated = self._translator(text, source, target_language)
        if not isinstance(translated, str) or not translated.strip() or len(translated) > 20_000:
            raise ValueError("translator returned an invalid result")
        return TranslationResult(translated, source, target_language, True)

    def get_preference(self, owner_id: str) -> LanguageProfile | None:
        if not owner_id or len(owner_id) > 200:
            raise ValueError("a server-derived owner identifier is required")
        return self._memory.get_language_profile(owner_id) if self._memory else None

    def save_preference(self, owner_id: str, profile: LanguageProfile) -> None:
        if not owner_id or len(owner_id) > 200:
            raise ValueError("a server-derived owner identifier is required")
        if self._memory is None:
            raise RuntimeError("language preference memory is not configured")
        self._memory.save_language_profile(owner_id, profile)


def validate_voice_request(request: VoiceRequest) -> VoiceRequest:
    if request.operation not in {"transcribe", "synthesize", "stream"}:
        raise ValueError("unsupported voice operation")
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", request.language):
        raise ValueError("invalid language tag")
    if request.text is not None and len(request.text) > 20_000:
        raise ValueError("voice text exceeds limit")
    if request.audio_reference is not None and len(request.audio_reference) > 512:
        raise ValueError("audio reference exceeds limit")
    return request


def validate_vision_request(request: VisionRequest) -> VisionRequest:
    if request.operation not in {"describe", "ocr", "ask"}:
        raise ValueError("unsupported vision operation")
    if not request.media_reference or len(request.media_reference) > 512:
        raise ValueError("invalid media reference")
    if request.prompt is not None and len(request.prompt) > 4000:
        raise ValueError("vision prompt exceeds limit")
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", request.language):
        raise ValueError("invalid language tag")
    return request


def validate_remote_control_request(request: RemoteControlRequest) -> RemoteControlRequest:
    """Validate shape only; callers must enforce auth, scope and immediate approval."""
    if request.operation not in {"observe", "request_action", "cancel"}:
        raise ValueError("unsupported remote-control operation")
    if not request.target_id or len(request.target_id) > 200:
        raise ValueError("invalid remote-control target")
    if len(request.parameters) > 32 or any(len(str(k)) > 64 or len(str(v)) > 1024 for k, v in request.parameters.items()):
        raise ValueError("remote-control parameters exceed limits")
    if request.operation == "request_action" and not request.approval_reference:
        raise ValueError("remote-control action requires an approval reference")
    return request
