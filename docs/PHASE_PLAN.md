# NGIT AI SOLUTION v4.0 — Phase plan

This plan preserves the approved phase ordering. Repository status is recorded separately in [`STATUS.md`](STATUS.md); deliverables below are targets, not completion claims. Tests and integration are not verified merely because code or tests are present.

## Build step 1 — Phases 1–2

### Phase 1: Architecture, repository, database, shared protocols

Deliver architecture/dependency/phase/ownership documentation; shared interface/security/data protocols; PostgreSQL foundation and migrations for implemented domains; local Compose configuration; and an explicit open-decision record. Validate Compose/database and migration behavior before reporting runtime success.

### Phase 2: Authentication, backend, security, user management

Deliver FastAPI authentication/security foundations, user services, validation/error handling, and initial web integration; database-backed user scoping and security-sensitive audit; execute API, authorization, ownership-isolation, migration/RLS and frontend checks and report exact results.

## Build step 2 — Phases 3–4

### Phase 3: Brain, model runtime, memory, knowledge

Deliver intent/routing/runtime orchestration and typed REST contracts; local/self-hosted runtime interface with optional provider fallback; isolated memory/knowledge, retrieval/source verification and ingestion; ownership and integration checks. Current status describes deterministic tests but no execution in the authoring environment; URL crawling and schema redesign are not introduced by this plan.

### Phase 4: Personal Agent, tools, browser/computer interfaces

Deliver conservative planning, registered tools, controlled execution, observations/verification, sandboxed filesystem and validated browser interfaces; computer control only through explicitly injected interface; backend permission/approval and audit; owner-scoped history and tests. Decide durable history/runner through approved architecture; do not imply durability while execution is synchronous and history process-local.

## Build step 3 — Phases 5–7

### Phase 5: Multilingual, voice, vision, remote control

Deliver language/dialect detection, multilingual output, translation, code-switching and style through approved contracts; voice/vision/remote-control interfaces with authorization, privacy, failure behavior and tests.

### Phase 6: Administration, rules, service control, billing

Deliver backend-enforced admin roles/privileges and administration operations; billing plans, subscriptions, metering, quotas and history. Implement payment/webhook lifecycle only after an explicit provider choice. Test privileges, metering and audit.

### Phase 7: Optional provider management and browsing

Deliver optional provider registry/configuration and safe credential references, health checks, usage/cost, routing/fallback and optional search/browser adapters. Test failures, secret handling and fallback; prove Brain works without external providers.

## Build step 4 — Phases 8–9

### Phase 8: Creative Studio

Deliver media/document workflows, asset management and processing/rendering interfaces, local/self-hosted options where practical, agreed artifact ownership/storage/task/failure contracts, and isolation/API tests.

### Phase 9: Content-to-Video, presenters, lip-sync, subtitles

Deliver script, scenes, storyboard, asset matching, timelines, audio sync, subtitles, preview/export and the Robot Presenter, Human Avatar Presenter, News Presenter, Teaching, Storytelling, Documentary, Presentation, and Live News modes. Define the distinct Presenter contract and avatar/voice/TTS/alignment/lip-sync/animation/virtual studio capability. Test pipeline failures, subtitles and ownership.

## Build step 5 — Phases 10–11

### Phase 10: Newsroom, Teaching, Storytelling

Deliver aggregation, analysis, verification, scripts, narration, ticker, subtitles and archives; education lessons, teaching presentations, virtual teacher/classroom, visual explanations, quizzes and assessment. Test factual verification; never fabricate events or present generated footage as authentic.

### Phase 11: Cybersecurity Center

Deliver authorized assessments, network/web analysis, configuration audits, forensics, safe labs and remediation reporting. Validate authorization and target scope before execution; test unauthorized rejection, scope enforcement, audit and reporting.

## Build step 6 — Phase 12

### Phase 12: Integration, QA, documentation, local release

Run and record cross-module integration, API/authentication/isolation, billing, service-control, video/subtitle/language, failure and sensitive-action suites. Resolve reported failures, document local install/configuration/operations and backup/recovery to the extent decisions exist, validate Compose, and build and verify a downloadable ZIP. Do not claim release readiness until checks and artifact verification actually run.

## Integration gates

1. Review current code and interface documents before assigning file-level implementation or changing a contract.
2. Validate Phase 1–2 migrations and RLS on disposable PostgreSQL; run API/web suites and Compose startup, authentication/security and ownership tests; record exact commands, environment, outcomes and failures.
3. Integrate Phases 3–4 against shared contracts; exercise owner isolation, approval consumption, adapter failures and API workflows. Distinguish synchronous/process-local behavior from durable execution.
4. Agree contracts before Phases 5–7 for language, voice/vision/remote-control, admin, billing, providers, real-time/task protocols. Keep unresolved choices open until approved.
5. Before Phases 8–9 depend on them, agree artifact metadata, task/status, storage, timeline, subtitle formats and Presenter contract.
6. Gate newsroom, cybersecurity, agent, billing and admin with backend authorization, audit and verification tests.
7. Maintain one status record of phases, changed contracts, dependencies, blockers, executed tests/results and risks. Create `docs/TEST_REPORT.md` only when tests have actually run; it is not a placeholder.

## Open decisions

See [architecture](ARCHITECTURE.md#open-decisions). No task runner, payment provider, vector stack, deployment topology, or media storage backend is selected by this plan.