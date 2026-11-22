# Project status — Phases 1–3

Status is based on files present in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Local PostgreSQL Compose configuration and root `.env.example` are present. Five ordered SQL migrations (`0001`–`0005`) define the isolated `ngit` schema, users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation metadata, audit logs, indexes and forced RLS. Seed data and transactional SQL integration checks cover selected tenant isolation and constraints. Architecture, dependency, phase, assignment, ERD and shared-interface documentation are present.

**Remaining:** Apply migrations to fresh PostgreSQL 16+; validate schema, indexes and seed data; run isolation checks using a provisioned application role that is neither superuser nor table owner; verify migration/application grants; validate Compose lifecycle and local startup.

**Blockers/caveats:** Migration execution is privileged. Tenant checks must not run as superuser or table owner. Provision a separate non-owner/non-superuser role without `BYPASSRLS` and grant only required privileges. API code must set `ngit.user_id` transaction-locally from authenticated server context. Provider metadata stores opaque credential references, not secrets. External AI remains optional. Database and Compose behavior remain unverified.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe errors, auth/user services, REST schemas/routes, backend-enforced authorization and transaction-local database caller context are present. Security primitives include expiring/revocable bearer tokens, policy/ownership checks, approval/emergency-stop controls, redacted audit events and environment-secret lookup. React/TypeScript/Vite includes sign-in/registration, authenticated dashboard, profile settings, read-only administrator user listing, responsive design system and shared API client. Backend and frontend test sources are present.

**Remaining:** Run backend/frontend tests, frontend production build, PostgreSQL-backed API integration and end-to-end local startup; review security and database-role behavior.

**Blockers/caveats:** Replace example peppers with local secrets. Token, approval, emergency-stop and audit state is process-local; use one worker until shared durable state exists. Environment lookup is not production secret management. Browser local-storage bearer tokens are not an authorization boundary. Runtime checks and suites have not been run.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain supports deterministic offline intent recognition and confidence thresholds, typed request/response contracts, bounded generation, in-process model registry, deterministic priority routing, local/self-hosted OpenAI-compatible runtimes, optional self-hosted fallback and sanitized failures. Runtime configuration uses server environment variables; external AI APIs are not required. Evaluation tests cover intent examples, confidence, routing, local generation, opt-in fallback, validation and safe failures. Memory and knowledge provide authenticated owner-scoped conversation/message and typed-memory persistence on the existing schema, deterministic lexical retrieval, optional owner-filtered embedding vector search, bounded provenance-aware ingestion and exact URL-origin allowlisting without remote fetching. Privacy-focused source tests cover owner binding, cross-user retrieval filtering, schema usage and source verification.

**Remaining:** Run Python tests and database checks; validate RLS and vector-loader ownership; assess classifier/model quality with representative evaluation data. Runtime registry/configuration is process-local and not durable; durable model administration remains future work.

**Caveats:** Intent confidence measures classifier certainty, not factual correctness or response quality. Brain generation authorization remains a separate integration/security concern; do not expose generation to untrusted callers until authenticated caller authorization is integrated and tested. Origin allowlisting does not verify fetched content; embeddings are not persisted by the current schema.

## Validation record

No tests or runtime checks have been run for this update. This includes Python/API, SQL migration/RLS, Compose, frontend tests/build and live integration checks. Checked-in tests are not evidence of execution or passing results.

## Next work

Run documented API and web suites and resolve failures. Complete PostgreSQL migration/RLS checks with a non-owner role, verify grants and lifecycle, and validate Compose/end-to-end local startup. Review authorization boundaries and plan durable shared state before multi-worker use. Record exact commands, environment and outcomes only after validation.

Documented Python command (not reported as run):

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

Documented database integration tests require a disposable PostgreSQL instance; see `services/api/db/tests/README.md`.
