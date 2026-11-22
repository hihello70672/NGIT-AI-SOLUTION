# NGIT Brain interface

This document describes the Brain boundary and runtime requirements; it does not claim every capability is production-ready or runtime-validated. See [project status](../STATUS.md). Inspect existing Brain routes, schemas, runtime code, and [shared protocols](SHARED_PROTOCOLS.md) before changes. Shared-contract changes require Chief Architect review.

## Responsibility and dependencies

Brain owns intent recognition, reasoning orchestration, confidence handling, response generation, model registry/routing, and runtime selection. It may consume Memory and optional provider capabilities only through published contracts. Core operation retains a local or self-hosted model-runtime path; external AI APIs remain optional.

## Contract and security requirements

- Validate typed requests and bound input/output size, timeouts, and resource use.
- Return typed results and sanitized failure behavior; do not expose provider credentials, stack traces, prompts, or internal data.
- Authenticated generation must use server-derived caller context and backend authorization. Do not expose generation to untrusted callers until authorization is integrated and tested.
- Apply user ownership to memory/retrieval calls; never accept a client-supplied identity as authorization.
- Confidence is classifier confidence only; it is not evidence of factual correctness or response quality.
- Provider fallback is opt-in, server-configured, and must preserve safe error and secret-handling behavior.

## Runtime guidance

Local/self-hosted OpenAI-compatible runtimes may be configured server-side. A missing optional runtime must not silently force an external provider or make core offline behavior depend on one. Model registry/runtime process-local behavior must not be described as durable administration or multi-worker shared state.

## Current operational caveat

The status record reports test sources but no executed test/runtime results for this update. Embeddings are not persisted by the reported schema, and source-origin allowlisting does not verify fetched content. Report only behavior verified in current code and tests actually run.
