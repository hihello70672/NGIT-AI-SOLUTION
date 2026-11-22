# Project status — Phases 1–3

This status reflects committed implementation in the reviewed `main` tree. It distinguishes implementation from execution: this update has not run the test suite, so no test passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** Repository layout, web application under `apps/web`, FastAPI service, PostgreSQL Compose configuration and environment example, architecture/dependency/phase/assignment/shared-protocol documentation, ERD, ordered migrations `0001`–`0004`, reference seed data, schema checks, and migration instructions. The schema includes user-scoped conversations/messages and memories and row-level security.

**Remaining:** Apply migrations to fresh PostgreSQL 16+ and verify migration integrity, schema constraints, and RLS using a non-owner application role; run cross-user database integration checks and Compose lifecycle verification.

## Phase 2 — Authentication, security, API, users

**Built/committed:** API configuration, transaction-local database caller context, authentication and user services, REST routes, request/response schemas, authorization controls, approval controls, emergency stop, and audit redaction. React/TypeScript/Vite frontend includes sign-in/registration and authenticated user-management flows.

**Runtime limits:** Authentication tokens, approvals, emergency-stop state, and audit events are process-local. Admin user listing is not implemented; deployment must remain single-worker until state durability and lifecycle are designed. Brain generation endpoints remain separate from the authenticated caller dependency.

## Phase 3 — NGIT Brain and private memory/knowledge services

**Built/committed:** Brain runtime provides deterministic intent classification, confidence checks, in-process model registry and priority routing, bounded asynchronous generation, local/self-hosted OpenAI-compatible runtime, and opt-in self-hosted fallback. Memory services persist conversations/messages and profile/preference/fact/summary records using the existing `conversations`, `messages`, and `memories` schema. Retrieval combines lexical search with optional vector candidates intersected against the authenticated user's database corpus. Knowledge ingestion chunks caller-provided text and stores provenance; allowlisted URL verification checks origin without fetching remote content. Authenticated REST endpoints use the server-derived user identity and explicit source allowlist.

**Runtime limits:** Memory and knowledge HTTP routes are authenticated; the brain API remains separately mounted and should not be exposed as authenticated user generation until caller authorization is integrated. Vector embeddings/indexing remain an optional external adapter because the schema has no embedding column or vector extension. No external AI APIs are required.

**Remaining:** Run memory, brain, API and database integration tests; verify migrations and RLS with a non-owner role; provide a production vector backend only with schema-approved owner filtering; consider transactional chunk-ingestion behavior and source-allowlist operations.

## Validation record

Tests have not been run for this update. Checked-in tests are source coverage, not evidence of passing execution. Database migration/RLS, Compose, API integration, and vector-provider behavior remain unverified. Do not report these checks as passing until run and record exact commands/environment.
