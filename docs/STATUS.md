# Project status — Phases 1–3

This status records repository evidence and validation accurately. Tests have not been run in this task, and no passing result is claimed.

## Phase 1 — Foundation, architecture, database, and local environment

**Built/committed:** Repository foundation and architecture documentation, approved phase plan and module boundaries, local PostgreSQL Docker Compose setup and usage documentation, environment examples, ordered SQL migrations and seed data, database schema checks/tests, and ERD documentation. The schema covers users and roles, user-scoped conversations/messages/memory, billing, optional provider configuration, media/presentation metadata, audit logs, indexes, ownership constraints, and row-level security; migration `0003` hardens role-assignment RLS.

**Remaining:** Execute migrations on a fresh PostgreSQL 16+ database, run schema/RLS tests using a non-owner, non-superuser application role, verify cross-user isolation, validate Compose startup/database lifecycle, and confirm API database integration against the migrations.

**Blocker/risk:** Migration integrity remains unresolved. A prior task accidentally replaced and restored `services/api/db/migrations/0001_initial_schema.sql` with content that may not preserve its original intent. Review/correct it against the intended schema before accepting Phase 1 database work. The migrations are plain ordered SQL; apply lexicographically.

## Phase 2 — Authentication, security, API, and user management

**Built/committed:** FastAPI service with versioned registration/login/logout/current-user endpoints, protected Brain routes, memory and optional agent integration, request validation/IDs, safe error handling, password hashing, expiring/revocable bearer tokens, default-deny role and ownership checks, approval and audit primitives, and user-management services. The API uses PostgreSQL-backed identity services and transaction-local user context for RLS. API/security tests and usage documentation are present.

**Remaining:** Run API/unit and live database integration tests; verify migration compatibility, authentication persistence, transaction-local RLS context, cross-user isolation, and complete authorization on sensitive Brain/tool actions. Token/approval/audit state is process-local; it supports only a single worker until an approved shared persistent adapter is implemented. Background tasks are in-process and not durable. Configure password/token peppers through deployment environment secrets; no real secrets belong in source control.

**Blocker/risk:** External AI integrations remain optional and unconfigured. Shared persistence for security state and durable background execution are not implemented. Review action-specific authorization and caller context before enabling sensitive generation/tool actions. Existing APIs use request/response; no WebSocket was added.

## Phase 3 — Brain, model runtime, memory, and knowledge

**Built/committed:** Brain contracts and runtime under `services/api/modules/brain`. The module includes deterministic offline intent classification with confidence scores (not represented as a trained model), generation orchestration, explicit in-process model registry and priority routing, timeout-bounded OpenAI-compatible chat-completion runtime adapters, server-environment-configured local and self-hosted endpoints, model selection, and opt-in self-hosted fallback when a configured primary runtime fails. The API exposes model listing and generation using typed request/response contracts; error payloads do not expose upstream bodies or credentials. No third-party provider is required for operation; absent local configuration is reported as unavailable rather than faked. Brain route authentication is enforced in the FastAPI application via server-derived current-user context.

**Evaluation present:** `services/api/tests/test_brain.py` and `test_brain_api.py` cover deterministic intent/confidence examples, registry ordering/duplicate rejection, local generation, optional fallback and opt-out, input/confidence/limit validation, unknown/disabled model rejection, safe runtime failures, and REST behavior. These checks are interface/evaluation tests, not broad language-quality or model-accuracy claims.

**Remaining:** Run the Brain and broader API/web test suites; verify local/self-hosted runtimes against real compatible endpoints; validate authentication, database integration, and caller ownership in the full running service. Registry and environment-configured runtime state are process-local; durable/multi-worker model administration is not provided.

**Blocker/risk:** Runtime and tests remain unverified in this status update. Configure endpoint credentials only in server environment/secrets. Do not expose generation to untrusted users without deployment-appropriate authentication and authorization.

## Validation record

Tests have not been run in this task. API, database/RLS, and web test results remain unverified; no passing result is claimed. Compose startup, migration runtime behavior, and local/self-hosted model endpoint behavior have also not been verified here.

## Phase sequence and boundaries

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved 12-phase delivery order. See [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md), [AGENT_ASSIGNMENTS.md](AGENT_ASSIGNMENTS.md), and [interfaces/SHARED_PROTOCOLS.md](interfaces/SHARED_PROTOCOLS.md) for module dependencies and boundary rules.

## Note

The repository contains later-phase web implementation, but this status scope records Phases 1–3. The web tests have not been run. Migration-integrity warning above remains the concrete blocker for accepting Phase 1 database work.

## Phase 3 implementation record

The Brain runtime and deterministic evaluation suite were already present at the reviewed repository HEAD. This update records their actual scope and distinguishes committed implementation from unverified runtime/test behavior; it does not claim execution or completion of outstanding validation.