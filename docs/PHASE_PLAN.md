# NGIT AI SOLUTION v4.0 — Phase plan

This plan preserves the approved phase order. Repository status is recorded separately in [`STATUS.md`](STATUS.md). Deliverables below are targets, not completion claims. Presence of code or tests alone does not establish runtime validation or passing results.

## Build step 1 — Phases 1–2

### Phase 1: Architecture, repository, database, shared protocols

Deliver architecture, dependency, phase, ownership, and shared-interface documentation; PostgreSQL schema/migrations for implemented domains; ownership model; local Compose foundation; and schema/isolation checks. Validate Compose and database/migration behavior before asserting runtime success.

### Phase 2: Authentication, backend, security, user management

Deliver authenticated FastAPI caller context, authentication/security foundations, user operations, validation and error handling, security-sensitive audit, and initial web integration. Exercise authorization, ownership isolation, migrations/RLS, and frontend behavior. Production durability must not be implied for process-local state.

**Gate:** Run API/unit and web suites, migrations and RLS checks against disposable PostgreSQL with a non-owner application role, and Compose/API/database lifecycle checks. Record exact commands and outcomes.

## Build step 2 — Phases 3–4

### Phase 3: Brain, model runtime, memory, knowledge

Deliver intent/routing/runtime orchestration and typed REST contracts; retain a local/self-hosted runtime with optional provider fallback; implement user-isolated memory/retrieval and source-verified knowledge ingestion. Validate ownership, retrieval, and integration. Do not add URL crawling or vector persistence without approved design.

### Phase 4: Personal Agent, tools, browser and computer interfaces

Deliver conservative planning, registered tools, controlled execution, observation/verification, isolated filesystem and validated browser/computer interfaces, backend permission/approval checks, and user-scoped history. Agree task acceptance/status/failure semantics and runner guarantees before claiming durable asynchronous execution.

**Gate:** Do not expose Brain generation to untrusted callers before authentication and authorization. Validate retrieval isolation and approval semantics before expanding tool capabilities.

## Build step 3 — Phases 5–7

### Phase 5: Multilingual, voice, vision, remote control

Deliver language/dialect handling, multilingual output, translation, code-switching and style through approved contracts. Voice, vision, and remote control require defined authorization, privacy, failure behavior, and tests.

### Phase 6: Administration, rules, service control, billing

Deliver backend-protected administration, rules/service controls, audit/emergency controls, plans, subscriptions, metering, quotas, and history. Select no payment integration without explicit approval. Test privileges, metering, and audit.

### Phase 7: Optional provider management and browsing

Deliver optional provider registry/configuration, safe credential references, health/usage/cost, routing/fallback, and approved search/browser adapters. Test failures and secret handling; demonstrate Brain operation without external providers.

**Gate:** Agree shared security, audit, billing, provider-configuration, and secret-handling contracts before dependent UI or integrations.

## Build step 4 — Phases 8–9

### Phase 8: Creative Studio

Deliver image/video/document workflows, asset management, processing/rendering interfaces, and isolation/API tests. Prefer local/self-hosted processing where practical. Define artifact ownership, storage, task, and failure behavior before claiming export guarantees.

### Phase 9: Content-to-Video, presenters, lip-sync, subtitles

Deliver scripts, scenes/storyboards, asset matching, timelines, audio sync, subtitles, preview/export and specified presentation modes. Keep presenter/avatar/TTS/speech-alignment capability on its distinct approved contract. Test pipeline failures, subtitle behavior, and ownership; settle presenter placement and artifact metadata first.

**Gate:** Approve presenter boundary and artifact ownership/storage contracts before cross-module integration.

## Build step 5 — Phases 10–11

### Phase 10: Newsroom, Teaching, Storytelling

Deliver aggregation, analysis and verification, scripts, narration, ticker, subtitles and archives; educational lessons, teaching presentations, classroom, explanations, quizzes and assessment; plus approved storytelling/documentary workflows. Verify sources; do not fabricate events or present generated footage as authentic.

### Phase 11: Cybersecurity Center

Deliver authorized assessments, network/web analysis, configuration audits, forensics, safe labs, remediation, and reports. Enforce authorization and authorized target/safe-lab restrictions in the backend; test rejection, scope enforcement, audit, and reporting.

**Gate:** Verify newsroom source handling and cybersecurity target authorization before enabling those workflows.

## Build step 6 — Phase 12

### Phase 12: Integration, QA, documentation, local release

Integrate approved modules and run/report API, authentication, isolation, billing, service-control, media/video/subtitle/language, failure, sensitive-action, and web checks. Resolve and re-test failures. Document local installation/operations and validate Compose, migrations, and backup/recovery expectations to the extent decisions exist. Build and verify a downloadable ZIP before claiming release readiness.

Create `docs/TEST_REPORT.md` only after tests actually run; record commands, environment, outcomes, blockers, and retests. Do not claim unexecuted checks passed or assert production readiness without deployment evidence.

## Integration gates

1. Review current implementation and shared interface documents before changing paths or contracts.
2. Validate Phase 1–2 migrations/RLS on disposable PostgreSQL and run API/web checks with exact outcomes recorded.
3. Integrate Phases 3–4 against approved contracts; test ownership, approvals, adapter failures, and distinguish synchronous/process-local behavior from durable execution.
4. Approve language, voice/vision/remote control, admin, billing, providers, and real-time/task protocols before dependent work.
5. Before Phases 8–9 integrations, agree artifact metadata, task/status, storage, subtitle formats, and presenter boundaries.
6. Gate agent, newsroom, cybersecurity, billing, and administration on backend authorization, audit, and verification tests.
7. Maintain a status record of phase evidence, contract changes, dependencies, blockers, executed tests/results, and risks.

## Open decisions

See [architecture open decisions](ARCHITECTURE.md#open-decisions). This plan does not select a task runner, payment provider, vector stack, production topology, or media storage backend.
