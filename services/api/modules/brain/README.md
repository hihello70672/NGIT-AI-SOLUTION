# NGIT Brain

The Brain module implements the Phase 3 intent-to-response orchestration contract. Its deterministic intent recognizer provides an offline baseline; response generation is delegated to an explicitly configured local or self-hosted model runtime. No SaaS model is required.

## Runtime configuration

Set `NGIT_LOCAL_MODEL_BASE_URL` to an OpenAI-compatible chat endpoint root, for example `http://localhost:11434/v1` for an Ollama-compatible service. Configure `NGIT_LOCAL_MODEL_NAME` to the runtime's installed model name; `NGIT_LOCAL_MODEL_ID` is the stable Brain registry identifier. Optional server-side `NGIT_LOCAL_MODEL_API_KEY` supports protected self-hosted endpoints.

A second optional self-hosted endpoint can be set through the matching `NGIT_SELF_HOSTED_MODEL_*` variables. It is used as fallback only when request fallback is enabled and a primary model fails. Keep credentials in deployment environment/secrets, not source control or browser requests. With no endpoint configured, the API reports model unavailable; the module remains importable and usable for deterministic tests.

Run API tests from the repository root with `pytest services/api/tests/test_brain.py services/api/tests/test_brain_api.py`. Test execution is not asserted by this document.

The registry and route configuration are process-local. Brain API authentication is not yet integrated; do not expose generation to untrusted users until authenticated caller context and authorization are enforced.
