# Project status — Phases 1–4

This file records committed repository evidence, not proof of runtime behavior or test execution.

## Phase 1 — Foundation and architecture
**Status: Built.** Architecture, dependency and phase plans, shared protocols, environment examples, Compose PostgreSQL configuration, and initial schema are present.

## Phase 2 — Core data, security, API, and web foundation
**Status: Implemented foundation; integration/validation remains.** PostgreSQL schema and reference data, SQL checks, API authentication/security/user services and tests, and the `apps/web` React/TypeScript application are present. Shared security contains opaque bearer tokens (process-local registry), RBAC/policy authorization, one-time distinct-reviewer approvals, restricted action checks, an emergency stop, redacted in-memory audit events, and an environment-backed secret interface. These controls and audit/approval state are process-local and are not durable or cross-worker. Validate migrations/RLS against disposable PostgreSQL and execute API/web suites before claiming verified behavior.

## Phase 3 — Brain, model runtime, memory, and knowledge
**Status: Services implemented; runtime verification remains.** Brain intent/routing/runtime and REST contract have deterministic tests. Memory/knowledge use owner-scoped existing schema, lexical retrieval with optional owner-filtered vector adapter, and allowlist-verified supplied-text ingestion. URL crawling and schema redesign are not introduced. Tests/database integration have not been executed in this authoring environment.

## Phase 4 — Personal Agent, tools, browser/computer interfaces
**Status: Core engine committed; runtime verification and durable history remain.** Conservative planner, registered capabilities, sandboxed filesystem, validated browser adapter, optional injected computer interface, task observations/verification, owner-scoped process-local history are present. Side-effecting capabilities use approval-required restricted policies; there is no shell or implicit desktop access. Tests have not been run in this authoring environment.

## Remaining gates
- Run `PYTHONPATH=. python -m unittest discover -s services/api/tests` with dependencies installed; validate SQL migrations/RLS on a disposable PostgreSQL database and run the DB test runner.
- Validate API approval workflow and lifespan/database behavior; web suite and integration checks remain outstanding.
- Choose durable task/history persistence only through approved architecture.

External AI APIs remain optional. These status statements describe committed code only; they do not assert tests passed.

**Phase 2 security follow-up:** hardened audit-key redaction, validates role/action identifiers, rejects approval of expired grants, and regression tests these cases. No test suite execution is claimed here.
