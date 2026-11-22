# Project status — Phases 1–3

This status records repository evidence on `main`. A committed file is evidence of code/documentation, not proof that runtime behavior or tests have been validated.

## Phase 1 — Foundation and architecture

**Status: Built.** Project overview, architecture/dependency/phase/assignment guidance, shared protocols, environment examples, and a Docker Compose PostgreSQL service are present. Tooling choices are recorded where implemented; outstanding architecture choices remain open unless explicitly resolved by code.

## Phase 2 — Core data, security, API, and web foundation

**Status: Implemented foundation; integration and validation remain.** Repository contains PostgreSQL schema/reference-data migrations and SQL checks, API authentication/security/user services, task boundary, API and security tests, and the `apps/web` React/TypeScript application. Remaining: validate database migrations and row-level security against disposable PostgreSQL; run API/frontend test suites and production build; finish end-to-end integration; address the documented process-local token/approval store limitation before production.

## Phase 3 — Brain, model runtime, memory, and knowledge

**Status: Brain/model-runtime foundation implemented; memory and knowledge are not implemented.** The repository now contains a typed intent-recognition and Brain service contract, deterministic baseline intent classifier, confidence gating, in-process model registry and priority routing, asynchronous OpenAI-compatible local/self-hosted runtime adapter, optional configured self-hosted fallback, `/api/v1/brain/models` and `/api/v1/brain/generate` routes, and deterministic evaluation/API tests. External AI providers are not required. Registry configuration remains process-local. Memory, knowledge ingestion/retrieval, persistent model administration, and their isolation tests remain unimplemented; do not treat Phase 3 as fully complete.

## Tests and blockers

No tests or build commands were run for this change in the available environment. Brain tests are committed but unverified here. Execute `PYTHONPATH=. pytest services/api/tests` with dependencies installed; the API lifespan may require PostgreSQL for broader tests. The Brain unit tests use fake runtimes and should not contact external model APIs. No successful test or build result is claimed.

Remaining Phase 3 verification includes installing local dependencies, running API tests, and exercising the OpenAI-compatible adapter against a local/self-hosted test endpoint. Evaluation examples are a small deterministic contract check, not a production quality benchmark.

Current blockers: local dependencies and disposable PostgreSQL are required for full API/database validation. No other blocker has been confirmed by repository review.
