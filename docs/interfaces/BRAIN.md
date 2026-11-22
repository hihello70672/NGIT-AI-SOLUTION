# Brain and model runtime contract

Phase 3 implementation contract under `services/api/modules/brain`. HTTP routes live at `/api/v1/brain`; the module is called through typed `BrainRequest`/`BrainResponse` service objects, not another module's private persistence.

## Intent, confidence, and reasoning

`IntentRecognizer.recognize(text)` returns a stable intent label and confidence in `[0, 1]`. `HeuristicIntentRecognizer` is a deterministic offline baseline; it is replaceable and is not represented as a trained model. `BrainService.respond` validates generation limits, applies the caller-selected confidence threshold, selects an enabled chat model, builds system/user messages, and returns the generated response with intent, confidence, selected model ID, and fallback indicator. The threshold expresses classifier confidence, not factual correctness or answer quality.

## Registry, routing, and runtimes

`ModelRegistry` holds explicit `ModelDefinition` entries in process memory. Enabled entries advertising `chat` are candidates; lower numeric priority wins, then model ID provides a stable tie-break. Explicit unknown, disabled, or incompatible model selection is rejected rather than silently rerouted. Persistent model administration is not part of this phase.

`ModelRuntime.generate` is an asynchronous, timeout-bounded protocol. `OpenAICompatibleRuntime` posts chat messages to `{base_url}/chat/completions`; local Ollama and compatible self-hosted endpoints are supported. Credentials are optional and must be injected from server configuration, never request/browser data. HTTP, timeout, malformed JSON, and empty-output failures become safe runtime errors; upstream response bodies and credentials are not returned to callers.

The application may configure a primary local endpoint with `NGIT_LOCAL_MODEL_BASE_URL`, `NGIT_LOCAL_MODEL_ID`, `NGIT_LOCAL_MODEL_NAME`, and optional `NGIT_LOCAL_MODEL_API_KEY`. A second endpoint can be configured with `NGIT_SELF_HOSTED_MODEL_BASE_URL`, `NGIT_SELF_HOSTED_MODEL_ID`, `NGIT_SELF_HOSTED_MODEL_NAME`, and optional `NGIT_SELF_HOSTED_MODEL_API_KEY`. The optional fallback is attempted only when enabled on the request and a primary candidate fails. No external AI provider is required.

## REST contract

- `GET /api/v1/brain/models` returns configured enabled chat model IDs, names, capabilities, and priorities.
- `POST /api/v1/brain/generate` accepts `text`, optional `model_id`, bounded `temperature`/`max_tokens`, `min_confidence`, and `allow_fallback`. Success returns `text`, `intent`, `confidence`, `model_id`, and `fallback_used`.
- Domain failures use the shared error envelope: validation/low confidence/model selection errors are 422; no configured runtime or generation failure is 503. Error messages must not expose provider response bodies, credentials, prompts, or stack traces.

Authentication must be reviewed before exposing generation to untrusted users: the current foundation's Brain routes do not yet receive authenticated caller context. This is not suitable as a public production deployment without that security integration.

## Evaluation

`services/api/tests/test_brain.py` checks fixed intent examples and confidence bounds, priority selection, duplicate registration, local generation, optional self-hosted fallback, fallback opt-out, input/confidence/limit validation, explicit model selection, and safe generation failures. These are deterministic interface/evaluation checks, not broad language quality or model accuracy claims. They must be run in the project's API test environment before reporting results.

Registry and environment-configured models are process-local; multi-worker consistency and durable administration are open integration work.
```