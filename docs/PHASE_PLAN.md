# NGIT AI SOLUTION v4.0 — Phase plan

This plan records approved target deliverables, not completion claims. Implementation evidence and outstanding verification are tracked separately in [STATUS.md](STATUS.md). A source file or test existing does not establish runtime validation or passing results.

## Build step 1 — Phases 1–2

### Phase 1: Architecture, repository, database, shared protocols

Agree module ownership, dependency map and typed interfaces; review schema/migrations and ownership model; retain seed data and schema/isolation checks; document local Compose and setup. Verify migration integrity, fresh PostgreSQL 16+ migrations, schema/RLS behavior using a non-owner app role, cross-user isolation, Compose lifecycle, and API/database integration before accepting the foundation.

### Phase 2: Authentication, backend, security, users

Deliver authenticated server-derived caller context, authentication/user operations, backend policy and permission enforcement, audit foundation, validation/error conventions, and initial web integration. Test API/unit and live database behavior, persistence, transaction-local RLS context, isolation, and sensitive Brain/tool authorization. Do not imply durable state for process-local security or task behavior.

**Gate:** Run API and web suites, migrations and RLS checks against disposable PostgreSQL using a non-owner role; verify Compose/API/database lifecycle. Record exact commands and outcomes.

## Build step 2 — Phases 3–4

### Phase 3: Brain, model runtime, memory, knowledge

Deliver intent/reasoning orchestration, model registry/routing, local/self-hosted execution with optional provider fallback, confidence/response handling, user-isolated memory and retrieval, knowledge ingestion, source-verification interfaces, and evaluation coverage. Validate configured runtimes, ownership, and database/API integration; do not add crawling or vector persistence without approval.

### Phase 4: Personal Agent, tools, browser and computer interfaces

Deliver conservative planning, registered tools, bounded filesystem/browser/computer interfaces, policy and approval checks, observation/verification, and user-scoped task reporting. Define task acceptance/status/failure semantics before claiming durable asynchronous work. Test authorization, approval outcomes, isolation, and adapters.

**Gate:** Do not expose generation to untrusted callers before authentication/authorization. Verify retrieval isolation and action-specific approvals before expanding tools.

## Build step 3 — Phases 5–7

### Phase 5: Multilingual, voice, vision, remote interfaces

Deliver language/dialect handling, multilingual output, translation, code-switching/style adaptation and approved voice/vision/remote-control contracts. Define authorization, privacy, failure behavior, and tests; coordinate capability ownership to prevent duplicate services.

### Phase 6: Administration, rules, service control, billing

Deliver backend-enforced admin operations, roles, rules/service controls, audit/emergency controls, plans, metering, quotas and billing history/interfaces. No payment integration absent explicit approval. Test privileges, quotas, audit, and restricted actions.

### Phase 7: Optional provider management and browsing

Deliver optional provider registry/configuration, secret-safe credential references, connection/health and usage/cost reporting, routing/fallback, approved search/browser adapters. Demonstrate core Brain path without external providers; test failures, fallback, and secret handling.

**Gate:** Agree security, audit, billing, provider configuration and secret-handling contracts before dependent UI/integrations.

## Build step 4 — Phases 8–9

### Phase 8: Creative Studio

Deliver media workflows for image/video/documents, processing, asset management and rendering interfaces, with user ownership and practical local/self-hosted options. Define storage, task, and failure behavior; test API ownership and rendering errors.

### Phase 9: Content-to-Video, presenters, lip-sync, subtitles

Deliver scripts, scenes/storyboards, asset matching, timelines, audio sync, subtitles, previews/exports, and modes: Robot Presenter, Human Avatar Presenter, News Presenter, Teaching, Storytelling, Documentary, Presentation, and Live News. Keep presenter/avatar/TTS/speech-alignment capability on a distinct contract. Settle artifact metadata/storage and presenter boundaries before integration; test synchronization, subtitle behavior, ownership, exports, and failures.

**Gate:** Approve presenter boundary and artifact ownership/storage contracts before cross-module use.

## Build step 5 — Phases 10–11

### Phase 10: Newsroom, Teaching, Storytelling

Deliver aggregation, analysis, verification, scripts, narration, ticker/subtitles/archive; educational lessons, teaching presentations, classroom, explanations, quizzes/assessment; and approved storytelling/documentary flows. Preserve provenance: do not fabricate events or represent generated footage as authentic.

### Phase 11: Cybersecurity Center

Deliver authorized assessment, network/web analysis, configuration audits, forensics, safe labs, remediation and reports. Validate authorization and scope server-side; test rejection, safe-lab limits, audit, and reporting.

**Gate:** Verify source handling and cybersecurity target authorization before enabling workflows.

## Build step 6 — Phase 12

### Phase 12: Integration, QA, documentation, local release

Integrate approved modules; run and report API, authentication, ownership/isolation, billing, service control, media/video/subtitle/language, sensitive-action, web, and failure tests. Fix and retest defects. Document local installation, migrations, operations, and backup/recovery expectations to the extent decided. Verify a downloadable ZIP before claiming release readiness. Create `docs/TEST_REPORT.md` only after tests actually run, recording exact commands, environment, outcomes, blockers, and retests.

## Integration gates

1. Inventory actual code/contracts before changing paths; preserve working implementation.
2. Validate Phase 1–2 migrations, ownership/RLS, API, web, Compose and database behavior with recorded evidence.
3. Integrate Phases 3–4 through approved contracts and verify isolation, approvals and actual synchronous/process-local behavior separately from durable tasks.
4. Approve language, voice/vision/remote, administration, billing, providers, secrets, and streaming/task protocols before dependent integrations.
5. Before Phases 8–9 integration, agree artifact metadata/storage, task/status, subtitles, and presenter boundaries.
6. Gate agent, newsroom, cybersecurity, billing, and administration on backend authorization, audit, and verification tests.
7. Keep phase evidence, contract changes, dependencies, blockers, test outcomes, and risks current. Never claim unrun checks passed.

## Open decisions

See [architecture open decisions](ARCHITECTURE.md#decisions-still-open). This plan does not select a task runner, payment provider, vector stack, production topology, media storage backend, or secret-management product.
