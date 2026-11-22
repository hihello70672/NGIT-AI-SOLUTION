# Language intelligence interface

Language intelligence is a reusable capability owned by `services/api/modules/language/`. Brain, Memory, voice/vision/remote-control, media, education, newsroom and presentation consumers use typed public contracts rather than private persistence.

## Language service contract

- `LanguageService.detect(text, preferred_language)` returns a language tag, bounded heuristic confidence, recognized dialect hint if available, and secondary language tags observed in mixed-language input. Detection is best-effort, not correctness-guaranteed; explicit user preference takes precedence for response behavior.
- `LanguageProfile` carries language, optional dialect, response language, register, formality and code-switch preference. The current safe style adapter is limited phrase substitution; do not represent it as semantic translation or general multilingual generation.
- Response generation receives a Brain generator explicitly. This module does not require an external AI provider and does not claim deterministic phrase adaptation is full multilingual generation.
- Translation is an injected adapter contract. An unavailable adapter returns an explicit failure rather than echoing source text as translated.
- Preference memory is an owner-scoped published contract; derive owner from authenticated server context and leave persistence to the Memory module. No process-local preference store is implied.

## Voice, vision and remote control

`VoiceRequest`, `VisionRequest` and `RemoteControlRequest` define bounded inputs only; they do not execute models, media, microphone, camera or device operations. Implementations must be explicitly injected, validate media ownership and return typed safe failures. Remote-control execution requires backend authorization, exact-scope approval immediately before sensitive action and audit. Schema validation is not authorization or device security.

## API and validation

REST is default. Profile routes use the host's authenticated current-user dependency and Memory-backed preference contract; do not trust client-supplied owner identifiers. Tests should cover deterministic detection/style, code-switch hints, missing adapters, owner scoping, profile API identity and modality validation. Test source existence is not evidence of execution; check `docs/STATUS.md`.
