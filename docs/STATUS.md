# Project status — Phases 1–4

This status reflects committed implementation in the reviewed `main` tree. Checked-in tests are source coverage, not evidence of execution. No tests were run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** Repository layout, web application under `apps/web`, FastAPI service, PostgreSQL Compose configuration and environment example, architecture/dependency/phase/assignment/shared-protocol documentation, ERD, ordered migrations `0001`–`0004`, reference seed data, schema checks, and migration instructions. The schema includes user-scoped conversations/messages and memories and row-level security.

**Remaining:** Apply migrations to fresh PostgreSQL 16+ and verify migration integrity, schema constraints, and RLS using a non-owner application role; run cross-user database integration checks and Compose lifecycle verification.

## Phase 2 — Authentication, security, API, users

**Built/committed:** API configuration, transaction-local database caller context, authentication and user services, REST routes, request/response schemas, authorization controls, approval controls, emergency stop, and audit redaction. React/TypeScript/Vite frontend includes sign-in/registration and authenticated user-management flows.

**Runtime limits:** Authentication tokens, approvals, emergency-stop state, and audit events are process-local. Admin user listing is not implemented; deployment must remain single-worker until state durability and lifecycle are designed. Brain generation endpoints remain separate from authenticated caller authorization.

## Phase 3 — NGIT Brain and private memory/knowledge services

**Built/committed:** Brain runtime provides deterministic intent classification, confidence checks, in-process model registry and priority routing, bounded asynchronous generation, local/self-hosted OpenAI-compatible runtime, and opt-in self-hosted fallback. Memory persists conversations/messages and profile/preference/fact/summary records using the existing schema. Retrieval combines lexical search with optional vector candidates intersected against the authenticated user's database corpus. Knowledge ingestion chunks caller-provided text and stores provenance; allowlisted URL verification checks origin without fetching remote content. Authenticated REST endpoints use server-derived identity.

**Runtime limits:** Vector embeddings/indexing are an optional external adapter because the schema has no embedding column or vector extension. No external AI API is required.

## Phase 4 — Personal Agent, tools, browser and computer interfaces

**Built/committed:** Conservative deterministic one-step planner, explicit tool registry, bounded workspace filesystem access, HTTP(S)-only browser adapter boundary, injected computer-control adapter boundary, observations and verification, owner-scoped process-local task history, and authenticated task APIs. Filesystem writes, browser navigation, and computer actions are registered as restricted, approval-required policies in the shared security engine. Tasks pause before side effects; exact action/resource one-time approval is consumed by the shared `RestrictedActionManager` before continuing. Rejection, mismatched/expired grants, emergency stop, tool failures and failed verification do not produce task success. Optional adapter loading is controlled by environment configuration.

**Runtime limits:** Task history and approval/security state are process-local; execution is synchronous, single-worker suitable, and not a durable background runner. Browser/computer operations require explicit configured adapters. Workspace must be explicitly configured before agent routes are mounted. Tests were added but were not run for this update.

## Validation record

Tests have not been run for this update. Checked-in tests are source coverage, not evidence of passing execution. Database migration/RLS, Compose, API integration, external adapter behavior, and all test-suite outcomes remain unverified. Do not report checks as passing until run and record exact commands, environment, results, blockers, and retests.
