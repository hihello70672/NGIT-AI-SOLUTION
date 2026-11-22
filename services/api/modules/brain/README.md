# NGIT Brain

The Brain module implements the Phase 3 intent-to-response orchestration contract. Its deterministic intent recognizer provides an offline baseline; generation delegates only to explicitly configured local or self-hosted model runtimes. No SaaS model is required.

## Runtime configuration

Set `NGIT_LOCAL_MODEL_BASE_URL` to an OpenAI-compatible chat endpoint root, such as `http://localhost:11434/v1` for an Ollama-compatible service. Configure `NGIT_LOCAL_MODEL_NAME` to the runtime's installed model name and `NGIT_LOCAL_MODEL_ID` to the stable Brain registry identifier. Optional server-side `NGIT_LOCAL_MODEL_API_KEY` supports protected self-hosted endpoints.

An optional second self-hosted endpoint uses the matching `NGIT_SELF_HOSTED_MODEL_*` variables. It is attempted only when generation allows fallback and the primary configured candidates fail. Keep credentials in deployment environment/secrets, not source control or client requests. With no endpoint configured, the API reports a safe model-unavailable response; it does not silently invoke an external provider.

The in-process registry orders enabled models by priority and supports explicit model selection, capability filtering, bounded token/temperature parameters, timeout enforcement, and safe failure handling. Intent confidence is a heuristic classifier score, not factual certainty. Registry and route configuration are process-local; this is not durable administration or multi-worker shared state.

## Security and testing caveat

The current Brain REST route is not yet protected by authenticated caller authorization. Do not expose generation to untrusted callers until server-derived caller context and backend authorization are integrated and tested. Tests are present at `services/api/tests/test_brain.py` and `test_brain_api.py`; their presence does not establish that they have run. See `docs/STATUS.md` for validation status.
