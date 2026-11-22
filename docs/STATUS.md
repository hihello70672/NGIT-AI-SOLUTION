# Project status — Phases 1–4

This file records committed repository evidence, not proof of runtime behavior or test execution.

## Phase 1 — Foundation and architecture
**Status: Built.** Architecture, dependency and phase plans, shared protocols, environment examples, Compose PostgreSQL configuration, and initial schema are present.

## Phase 2 — Core data, security, API, and web foundation
**Status: Implemented foundation; integration/validation remains.** PostgreSQL schema and reference data, SQL checks, API authentication/security/user services and tests, and the `apps/web` React/TypeScript application are present. Validate migrations/RLS against disposable PostgreSQL and execute API/web suites before claiming verified.

## Phase 3 — Brain, model runtime, memory, and knowledge
**Status: Services implemented; runtime verification remains.** Brain intent/routing/runtime and REST contract have deterministic tests. Memory and knowledge use owner-scoped existing schema, lexical retrieval with optional owner-filtered vector adapter, and allowlist-verified supplied-text ingestion. URL crawling and schema redesign are not introduced. Tests/database integration have not been executed in this authoring environment.

## Phase 4 — Personal Agent, tools, browser/computer interfaces
**Status: Core engine committed; runtime verification and durable history remain.** The agent module provides a conservative planner, capability registry, sandboxed filesystem, HTTP(S)-validated browser adapter, optional injected computer-control interface, task observations/verification and owner-scoped history. Side-effecting writes, navigation and computer actions use restricted approval-required policies registered in the shared security engine when the explicitly provisioned `NGIT_AGENT_WORKSPACE` enables routes. One-time shared approvals are matched and consumed before side effects; no shell or implicit desktop access exists. Task execution is synchronous and history process-local. `services/api/tests/test_agent.py` covers planning, registration, sandboxing, approvals, isolation and adapter failure. Tests have not been run in this authoring environment.

Remaining: run `PYTHONPATH=. python -m unittest discover -s services/api/tests` with dependencies installed; validate API approval workflow and runtime/database behavior; choose durable task persistence/runner only through approved architecture.

## External AI and operations
External AI APIs are optional. These status statements describe committed code only, not test results. PostgreSQL RLS, Compose, and full API integration still require target-environment validation.
