# Project status — Phases 1–4

This status reflects committed implementation in the reviewed `main` tree. Checked-in tests are source coverage, not evidence of execution. No tests were run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** Repository layout, web application under `apps/web`, FastAPI service, PostgreSQL Compose configuration and environment example, architecture/dependency/phase/assignment/shared-protocol documentation, ERD, ordered migrations `0001`–`0004`, reference seed data, schema checks, and migration instructions. The schema includes user-scoped conversations/messages and memories with row-level security, billing, provider metadata, media/video/presentation metadata, audit logs, and indexes.

**Remaining verification:** Apply migrations to fresh PostgreSQL 16+, verify migration integrity, schema constraints and RLS with an explicitly provisioned non-owner, non-superuser application role. Existing SQL checks cover RLS reads/writes, tenant-composite foreign keys, seeds and indexes, but have not been executed. See `services/api/db/tests/README.md` for role and runner caveats.

## Phase 2 — Authentication, security, API, users

**Built/committed:** FastAPI lifespan/entry point, validated configuration, request correlation, error mapping, authentication and user services, validated REST routes, backend-enforced authorization, transaction-local database caller context, approval and emergency-stop controls, audit redaction, and React/TypeScript/Vite registration and authenticated profile flows. Opaque expiring/revocable bearer tokens and password verification are wired to PostgreSQL-backed services. API contract tests cover registration/login/profile/logout, request IDs, validation, conflict response, and protected Brain routes; security regression coverage lives in `services/api/tests/test_security.py`.

**Runtime limits:** Tokens, approvals, emergency-stop state and audit events are process-local. Use a single worker until approved shared persistence/lifecycle replaces these primitives. Admin user listing is not implemented. Secret lookup uses environment configuration; production secret-manager integration remains open. Brain generation endpoints are authenticated at the API boundary.

## Phase 3 — NGIT Brain and private memory/knowledge services

**Built/committed:** Brain runtime provides deterministic intent classification, confidence checks, in-process model registry and priority routing, bounded asynchronous generation, local/self-hosted OpenAI-compatible runtime, and opt-in self-hosted fallback. Memory persists conversations/messages and profile/preference/fact/summary records using existing schema. Retrieval combines lexical search with optional vector candidates intersected against the authenticated user's database corpus. Knowledge ingestion chunks caller-provided text and stores provenance; allowlisted URL verification checks origin without fetching remote content. Authenticated REST endpoints use server-derived identity.

**Runtime limits:** Vector embeddings/indexing are an optional external adapter because the schema has no embedding column or vector extension. No external AI API is required.

## Phase 4 — Personal Agent, tools, browser and computer interfaces

**Built/committed:** Conservative deterministic one-step planner, explicit tool registry, bounded workspace filesystem access, HTTPS-only browser adapter boundary, injected computer-control adapter boundary, observations and verification, owner-scoped process-local task history, and authenticated task APIs. Filesystem writes, browser navigation and computer actions are registered as restricted, approval-required policies in shared security. Tasks pause before side effects; exact action/resource one-time approval is consumed by the shared `RestrictedActionManager` before continuing. Rejection, mismatched/expired grants, emergency stop, tool failures and failed verification do not produce task success. Optional adapter loading is controlled by environment configuration.

**Runtime limits:** Task history and approval/security state are process-local; execution is synchronous, single-worker suitable, and not a durable background runner. Browser/computer operations require explicitly configured adapters. Workspace must be explicitly configured before agent routes are mounted. Validation remains outstanding.

## Validation record

Tests and runtime checks were not run for this update; no passing result is claimed. Database migration/RLS checks, Compose, API integration, external adapter behavior, and all test-suite outcomes remain unverified. Do not report checks as passing until run and record exact commands, environment, results, blockers, and retests.

## Phase 1 database verification gaps

- The migration test runner applies SQL using supplied `DATABASE_URL`; its role needs schema/table creation privileges and is therefore not inherently a non-owner application role. The schema's forced RLS assertions only prove isolation if executed by a non-owner role without `BYPASSRLS`; provision that test role explicitly.
- `0001_initial_schema.sql` creates the `ngit` schema but does not grant schema usage/table privileges to an application role. Provision those privileges out of band for deployments/tests; do not use a superuser, table owner, or `BYPASSRLS` role for tenant request paths.
- The migration ledger is created in `public`, while application tables live in `ngit`; verify deployment grants and migration execution ownership separately.
- Role-assignment policies are intentionally privileged service operations, not end-user self-service grants.
- Migration/runtime validation remains pending; no SQL execution is claimed.

## Phase 2 security implementation boundaries

Security engines are implemented in `services/api/security.py`, with regression coverage in `services/api/tests/test_security.py`. Their token, approval, stop and audit state is process-local, not durable/shared across workers. Environment-backed `SecretStore` is a lookup boundary, not production secret-manager integration. API initialization requires `AUTH_TOKEN_PEPPER`, configured with at least 32 bytes; `.env.example` documents a non-secret replacement instruction. Keep deployment single-worker until shared state and its lifecycle are designed and validated.

## Phase 3 / Phase 4 validation boundaries

Vector persistence, durable task execution and external adapters are optional/open architecture decisions. No external AI API is required. Browser/computer tools stay disabled unless configured. Do not infer runtime validation from checked-in tests.

## Phase 5

Not started.

Tests and runtime checks were not run for this update; no passing result is claimed.

## Phase 2 API integration follow-up

The API entry point and contract tests were extended in this update to keep Brain routes behind bearer authentication. Existing test sources were reviewed, but test execution remains unverified.
