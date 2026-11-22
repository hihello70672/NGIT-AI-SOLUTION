# Language intelligence interfaces

Language intelligence is a reusable capability owned by `services/api/modules/language/`. Brain, Memory, voice, vision, remote-control, media, education, newsroom and presentation features consume typed contracts; consumers must not depend on private module persistence.

## Language service

- `LanguageService.detect(text, preferred_language)` returns a language tag, bounded heuristic confidence, dialect hint where recognized, and secondary languages observed in mixed-language input. Detection is a best-effort heuristic, not a correctness guarantee. Explicit user language preferences should take precedence when selecting response behavior.
- `LanguageProfile` carries language, optional dialect, response language, register, formality and code-switching preference. The current safe style adapter makes only limited, documented phrase substitutions and does not perform semantic translation.
- Response generation receives a Brain generator explicitly. This module does not add a required external AI provider or claim that deterministic phrase adaptation is multilingual generation.
- Translation is an injected adapter contract. An unavailable adapter produces an explicit error rather than returning the source as if translated.
- `PreferenceMemory` is a published owner-scoped contract. Owner IDs must be derived from authenticated server context; persistence remains the Memory module's responsibility. No process-local preference store is implied.

## Voice, vision and remote control

`VoiceRequest`, `VisionRequest`, and `RemoteControlRequest` define bounded input contracts. They do not execute model, media, microphone, camera, or device operations. Implementations must be explicitly injected, validate media ownership, and return safe typed failures. Remote-control execution requires backend authorization, scoped approval immediately before sensitive execution, and audit according to shared security contracts. Shape validation is not authorization or a device security boundary.

## Integration and validation

REST is the default. Profile routes are mounted by the host with its authenticated current-user dependency and a Memory-backed preference contract. No route trusts a client-supplied owner identifier. Tests cover deterministic detection/style, code-switch hints, adapter absence, owner scoping, profile API identity, and modality request validation. Test source presence is not evidence of execution; see `docs/STATUS.md` for validation state.
