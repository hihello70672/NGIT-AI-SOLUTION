# Project status — Phases 1–3

This file records committed repository evidence, not proof of runtime behavior or test execution.

## Phase 1 — Foundation and architecture
**Status: Built.** Project architecture, dependency and phase plans, shared protocols, environment examples, Compose PostgreSQL configuration, and initial schema are present.

## Phase 2 — Core data, security, API, and web foundation
**Status: Implemented foundation; integration/validation remains.** Repository includes PostgreSQL schema and reference data, SQL checks, API authentication/security/user services, API/security tests, and `apps/web` React/TypeScript application. Database migrations and RLS should be validated against disposable PostgreSQL; full API/web test and build suites still require execution.

## Phase 3 — Brain, model runtime, memory, and knowledge
**Status: Services implemented; runtime verification remains.** Brain intent/routing/runtime and REST contract are implemented with deterministic tests. Memory and knowledge services now persist conversations/messages/memory records using the established schema; retrieval provides local lexical search plus an optional vector-search adapter; knowledge ingestion chunks supplied text and verifies sources against an explicit allowlist. REST routes are mounted beneath the API prefix and depend on authenticated user context. Every persistence query is owner scoped and sets transaction-local RLS context; vector results are additionally restricted to the owner's persisted memory IDs. Existing schema has no vector column, so durable vector indexing/embedding generation remains an optional integration rather than a schema redesign. Source ingestion does not fetch external URLs.

`services/api/tests/test_memory.py` adds deterministic privacy, SQL scope, vector filtering, source verification, and chunking coverage. Tests and database integration have not been executed in this authoring environment. Run `PYTHONPATH=. pytest services/api/tests` with dependencies installed and `services/api/db/tests/run.sh` against disposable PostgreSQL. The Brain and memory functionality should not be considered fully verified until these execute successfully.

Remaining Phase 3 items: execute service and API tests; validate RLS and composite constraints against PostgreSQL; provide a concrete vector backend/embedding adapter only when deployment infrastructure and schema policy are approved; consider persistent model registry administration. External AI services remain optional.
