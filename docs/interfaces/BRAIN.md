# Brain and model runtime contract

The phase 3 implementation contract is under `services/api/modules/brain`; this document does not assert runtime validation. HTTP routes are recorded under `/api/v1/brain`; typed `BrainRequest`/`BrainResponse` service objects form the module boundary. Consumers use the service contract, not another module’s private persistence.

## Intent, confidence, and reasoning

`IntentRecognizer.recognize(text)` returns a stable intent label and confidence in `[0, 1]`. The heuristic recognizer is a deterministic offline baseline, not a trained model. `BrainService.respond` validates generation limits, applies the configured minimum classifier-confidence threshold, selects an enabled chat model, builds system/user messages, and returns generated text, intent, confidence, model ID, and fallback indicator. Classifier confidence is not factual correctness or answer quality.

## Registry, routing, and runtime

`ModelRegistry` holds explicit in-process model definitions. Enabled chat entries are candidates; lower numeric priority wins, with model ID as a deterministic tie-breaker. Unknown, disabled, or incompatible explicit selections are rejected rather than silently rerouted. Persistent model administration is outside the current phase.

`ModelRuntime.generate` is asynchronous and timeout-bounded. The OpenAI-compatible runtime posts chat messages to `{base_url}/chat/completions`; local Ollama and compatible self-hosted endpoints are supported. Credentials are optional server configuration and must never come from request/browser data. HTTP, timeout, malformed JSON, and empty-output failures become safe runtime errors; upstream bodies and credentials are not returned.

A local endpoint may use `NGIT_LOCAL_MODEL_BASE_URL`, `NGIT_LOCAL_MODEL_ID`, `NGIT_LOCAL_MODEL_NAME`, and optional `NGIT_LOCAL_MODEL_API_KEY`. An optional second self-hosted endpoint may use `NGIT_SELF_HOSTED_MODEL_BASE_URL`, `NGIT_SELF_HOSTED_MODEL_ID`, `NGIT_SELF_HOSTED_MODEL_NAME`, and optional `NGIT_SELF_HOSTED_MODEL_API_KEY`. Fallback is opt-in per request and only attempted after a primary candidate failure. No external AI provider is required.

## REST, security, and validation

- `GET /api/v1/brain/models` lists configured enabled chat model IDs, names, capabilities, and priorities.
- `POST /api/v1/brain/generate` accepts `text`, optional `model_id`, bounded `temperature`/`max_tokens`, `min_confidence`, and `allow_fallback`; success returns `text`, `intent`, `confidence`, `model_id`, `fallback_used`.
- Domain validation/low-confidence/model-selection failures use 422; unavailable runtime/generation failures use 503. Safe messages must not expose provider bodies, credentials, prompts, or stack traces.
- **Authorization caveat:** The status record says Brain generation endpoints remain separate from authenticated caller authorization. Do not expose generation to untrusted callers until authenticated caller authorization is integrated and tested.

The status records deterministic tests in `services/api/tests/test_brain.py`; they have not been run for this update. They cover intent examples, confidence bounds, routing, local generation, optional self-hosted fallback, opt-out, bounds, explicit model selection, and safe failure behavior—not broad language quality or model accuracy. Runtime registry/configuration remains process-local; multi-worker consistency and durable administration are open work.
