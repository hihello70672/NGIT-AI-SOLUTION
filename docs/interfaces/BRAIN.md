# NGIT Brain interface

This document defines the Brain boundary/runtime requirements; it does not claim that each capability is production-ready or runtime-validated. Inspect existing routes, schemas and `services/api/modules/brain/` before extending. Shared contract changes require Chief Architect review.

## Ownership and dependencies

Brain owns intent recognition, orchestration, confidence handling, response generation, model registry/routing and runtime selection. It may consume Memory and optional provider capabilities only via published contracts. Core operation retains local/self-hosted model execution; external AI APIs remain optional.

## Contract/security requirements

- Validate typed input/output and bound size, time and resource use.
- Return sanitized typed failures; never expose provider credentials, prompts, internal traces or protected data.
- Authenticated generation uses server-derived identity and backend authorization. Do not expose generation to untrusted callers until authorization is integrated and tested.
- Memory/retrieval calls enforce authenticated owner scope. A client-supplied ID is not authorization.
- Confidence is classifier confidence, not evidence of factual correctness or answer quality.
- Provider fallback is explicit opt-in/server-configured, preserves safe errors and does not silently become required.

## Runtime and evidence

An optional unavailable runtime must not silently force external providers or make core offline behavior depend on them. Process-local registries are not durable shared administration. Status records say embeddings are not persisted and runtime/database checks are unrun; source-origin allowlisting does not establish fetched-content authenticity. Report only behavior actually verified by executed tests/runtime checks.
