# NGIT AI SOLUTION v4.0 — Phase plan

This plan records approved target deliverables, not completion claims. Implementation evidence and outstanding verification are tracked separately in [STATUS.md](STATUS.md). A source file or checked-in test does not prove runtime validation or passing results.

## Build step A — Phases 1–2: Foundation, authentication, backend, security, users

### Phase 1 — Architecture, repository, database, shared protocols

**Deliverables:** Approved architecture and module boundaries; shared contracts; PostgreSQL schema/migrations/indexes; local Compose setup; migration and RLS verification.

**Status record:** Architecture, dependency, phase, assignment, ERD, and shared-interface documentation; FastAPI/web roots; Compose/environment example; migrations `0001`–`0004`; seed/reference data and schema checks are recorded. Migration integrity, RLS under non-owner role, cross-user checks, and Compose lifecycle remain unverified.

### Phase 2 — Authentication, backend, security, user management

**Deliverables:** Validated authentication/security design; backend-enforced authorization, approvals, audit and emergency controls; user APIs and frontend flows; security tests.

**Status record:** Authentication/user services/routes/schemas, authorization and approval controls, emergency stop, audit redaction, and frontend sign-in/registration and authenticated user-management flows are recorded. Tokens, approvals, emergency-stop state, and audit events are process-local; admin user listing is missing; Brain generation authorization is separate. Runtime validation is outstanding.

## Build step B — Phases 3–4: Brain, model runtime, memory, knowledge, Agent

### Phase 3 — Brain, model runtime, memory, knowledge

**Deliverables:** Intent/reasoning orchestration, confidence handling, model registry/routing, local/self-hosted runtime, optional fallback, memory retrieval, knowledge ingestion/provenance, user isolation, and evaluation coverage.

**Status record:** Deterministic intent classification and confidence checks; in-process registry/priority routing; bounded async generation; local/self-hosted OpenAI-compatible runtime and opt-in self-hosted fallback; persisted conversations/messages and memory records; lexical retrieval plus optional vector candidates; provenance-aware text ingestion; URL-origin allowlist verification without fetching remote content. Embeddings/vector indexing remain optional external adapters. Runtime/integration checks are unverified.

### Phase 4 — Personal Agent, tools, browser and computer interfaces

**Deliverables:** Planner/tool contracts; scoped execution; observation/verification; policy and approval gates; owner-scoped task status/results; failure and side-effect tests.

**Status record:** Conservative one-step planner, tool registry, bounded workspace filesystem access, HTTP(S)-only browser boundary, injected computer-control boundary, observations and verification, and authenticated task APIs are recorded. Restricted actions pause for exact action/resource approval. Rejection, mismatched/expired grants, emergency stop, tool failures, and failed verification do not produce success. Security/task state is process-local and execution synchronous; adapters and workspace need configuration. Validation is outstanding.

## Build step C — Phases 5–7: Language, administration, billing, optional integrations

### Phase 5 — Multilingual, voice, vision, remote interfaces

Deliver language/dialect handling, translation, code-switching, style/preferences, and approved voice/vision/remote-control contracts. Define permission, privacy, failure behavior, and language/error coverage.

### Phase 6 — Administration, rules, service control, billing

Deliver backend-enforced administration and audit; roles/rules/service controls and emergency operations; plans, quotas, metering, payment-verification interfaces, and billing history. Do not assume a payment provider.

### Phase 7 — Optional provider management and browsing

Deliver optional provider configuration/registry, server-side secret references, connection/health and usage/cost reporting, routing/fallback, and approved search/browser adapters. Demonstrate a core Brain path without external providers.

**Status for phases 5–7:** Not started in the status record.

## Build step D — Phases 8–9: Creative Studio, Content-to-Video, presenters

### Phase 8 — Creative Studio

Deliver image/video/document workflows, processing, composition, user-owned media management and rendering; prefer local/self-hosted options where practical. Define storage/task/failure behavior and ownership tests.

### Phase 9 — Content-to-Video, presenters, lip-sync, subtitles

Deliver scripts, scenes, storyboards, asset matching, timelines, audio sync, subtitles, preview/export, and modes: Robot Presenter, Human Avatar Presenter, News Presenter, Teaching, Storytelling, Documentary, Presentation, and Live News. Keep presentation orchestration separate from presenter/avatar/TTS/speech-alignment contracts. Set artifact ownership/storage boundaries before integration.

**Status for phases 8–9:** Not started in the status record.

## Build step E — Phases 10–11: Newsroom, Teaching, Storytelling, Cybersecurity

### Phase 10 — Newsroom, Teaching, Storytelling

Deliver aggregation, analysis, verification, scripts, narration, ticker, subtitles, and archives; educational lesson/presentation generation, virtual teacher/classroom, visual explanations, quizzes, and assessment; integrate through phase 9 presentation contracts. Preserve provenance: do not fabricate events or present generated footage as authentic.

### Phase 11 — Cybersecurity Center

Deliver authorized vulnerability assessment, network/web analysis, configuration audits, forensics, safe labs, scope validation, remediation reporting, and security tests. Validate authorization and target scope on the server.

**Status for phases 10–11:** Not started in the status record.

## Build step F — Phase 12: Integration, QA, documentation, local release

### Phase 12 — Integration, QA, documentation, local release

Integrate approved modules and run/report API, auth, ownership/isolation, billing, service-control, media/video/subtitle/language, sensitive-action, web, and failure tests. Fix and retest defects. Document local setup, migrations, operations, and decided backup/recovery expectations. Verify a downloadable ZIP before claiming release readiness. Create `docs/TEST_REPORT.md` only after tests actually run, recording exact commands, environment, outcomes, blockers, and retests.

**Status record:** README, local Docker guidance, API/database test sources, and phase/status/interface documentation exist. `docs/TEST_REPORT.md` is absent; no tests were run for this update; migration/RLS, Compose, API, adapters, and suites remain unverified. No release or tag is recorded.

## Integration gates and evidence discipline

1. Inventory actual code/contracts before changing paths; preserve working implementation.
2. Verify migrations, ownership/RLS, API, web, Compose, and database behavior with recorded evidence.
3. Integrate phases 3–4 using reviewed contracts; distinguish process-local/synchronous behavior from durable task execution.
4. Approve language, voice/vision/remote, administration, billing, provider, secret, task, and streaming protocols before dependent integration.
5. Settle artifact storage, task/status, subtitle, and presenter boundaries before phases 8–9 integration.
6. Gate Agent, newsroom, cybersecurity, billing, and administration on backend authorization, audit, and relevant verification tests.
7. Record implementation separately from validation. Never claim an unrun check passed.

## Open decisions

See [architecture open decisions](ARCHITECTURE.md#decisions-still-open). This plan does not select ORM, authentication format, durable runner, payment provider, vector stack, production topology, media storage, or secret-management product.
