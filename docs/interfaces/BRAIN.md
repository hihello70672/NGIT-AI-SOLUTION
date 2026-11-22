# Brain and model runtime contract

Phase 3 implementation contract under `services/api/modules/brain`. HTTP routes live at `/api/v1/brain`; the module is called through typed `BrainRequest`/`BrainResponse` service objects, not through another module's private persistence.

## Intent and confidence

`IntentRecognizer.recognize(text)` returns a stable intent label and confidence in `[0, 1]`. The deterministic `HeuristicIntentRecognizer` is an initial offline baseline; it is intentionally replaceable and is not represented as a trained model. The service rejects blank text, invalid generation bounds, and input below the caller's confidence threshold with stable `BrainError` codes.

## Model registry and selection

`ModelRegistry` holds explicit `ModelDefinition` entries in process memory. Only enabled entries advertising `chat` are candidates; lower numeric priority wins, with model ID as a stable tie-breaker. An explicit unknown/disabled model selection is rejected rather than silently routed elsewhere. Persistent model administration is not in this phase's implementation.

## Runtime adapter

`ModelRuntime.generate` is an asynchronous, timeout-bounded protocol. `OpenAICompatibleRuntime` posts JSON chat messages to `{base_url}/chat/completions`, supports an optional server-side bearer credential, and returns normalized `Generation` values. Configure `NGIT_LOCAL_MODEL_BASE_URL` and `NGIT_LOCAL_MODEL_NAME` for a local runtime, or a compatible self-hosted service. Runtime failures are mapped to safe errors and do not expose endpoint response bodies or credentials.

A secondary self-hosted runtime can be configured with `NGIT_SELF_HOSTED_MODEL_BASE_URL`, `NGIT_SELF_HOSTED_MODEL_ID`, and `NGIT_SELF_HOSTED_MODEL_NAME`. It is attempted only when enabled in the request and a configured primary candidate fails. This is an optional self-hosted adapter, not a mandatory third-party fallback. If no runtime is configured, generation returns `model_unavailable`.

## REST

- `GET /api/v1/brain/models` returns configured enabled chat model IDs, names, capabilities, and priorities.
- `POST /api/v1/brain/generate` accepts `text`, optional `model_id`, bounded `temperature`/`max_tokens`, `min_confidence`, and `allow_fallback`. Success returns `text`, `intent`, `confidence`, `model_id`, and `fallback_used`.
- Validation is handled by FastAPI request schemas; domain failures map to 422 or 503 with a stable `detail.code` and safe message. Authentication requirements should be reviewed before exposing generation to untrusted users; this foundation currently exposes the Brain routes without an authenticated user context and is not suitable as a public production deployment.

## Tests and evaluation

`services/api/tests/test_brain.py` checks six fixed intent examples, confidence range, priority selection, fallback success and opt-out, empty/low-confidence rejection, duplicate registration, and safe generation failure. `test_brain_api.py` verifies route contracts with an injected fake runtime and no configured-runtime behavior. These are deterministic interface/evaluation checks, not claims of broad language quality or model accuracy.
