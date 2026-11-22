# Project status — Phases 1–4

This file records committed repository evidence, not proof of runtime behavior or test execution.

## Phase 1 — Foundation and architecture
**Status: Built.** Project architecture, dependency and phase plans, shared protocols, environment examples, Compose PostgreSQL configuration, and initial schema are present.

## Phase 2 — Core data, security, API, and web foundation
**Status: Implemented foundation; integration/validation remains.** The repository includes PostgreSQL schema and reference data, SQL checks, API authentication/security/user services and tests, and the `apps/web` React/TypeScript application. Validate migrations/RLS against disposable PostgreSQL and execute the API/web suites before claiming verified.

## Phase 3 — Brain, model runtime, memory, and knowledge
**Status: Services implemented; runtime verification remains.** Brain intent/routing/runtime and REST contract are implemented with deterministic tests. Memory and knowledge persistence use owner-scoped existing schema, lexical retrieval with an optional owner-filtered vector adapter, and allowlist-verified supplied-text ingestion. No URL crawling or schema redesign is introduced. Tests/database integration have not been executed in this authoring environment; use the API README instructions.

## Phase 4 — Personal Agent, tools, browser/computer interfaces
**Status: Core engine committed; runtime verification and durable history remain.** The agent module includes a conservative explicit planner, allowlisted registry, sandboxed workspace filesystem tools, HTTP(S)-validated browser adapter, opt-in computer adapter, observations and verification, owner-scoped task lookup/history, and authenticated REST contracts. Side-effecting filesystem writes, browser navigation, and computer actions are registered in the shared policy engine as restricted and approval-required capabilities when an explicitly provisioned `NGIT_AGENT_WORKSPACE` enables the routes. Grants are checked through the existing one-time approval engine before side effects. No shell or implicit desktop access is enabled. History is process-local and task execution is synchronous in this initial interface. Tests cover planning, registry, sandboxing, approval gating, isolation and adapter failures; tests have not been run in this authoring environment.

Remaining: run `PYTHONPATH=. python -m unittest discover -s services/api/tests` with dependencies installed; validate API approval workflow and runtime/database behavior; choose durable task persistence/runner only through an approved architecture decision.

## External AI and operational validation
External AI APIs are optional. Status statements describe committed code only, not test results. PostgreSQL RLS, Compose, and full API integration still require validation in their target environments.
