# Project status — Phases 1–4

This status records repository implementation evidence accurately. Tests have not been run in this task; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, and local environment

**Built/committed:** Repository foundation and architecture documentation, approved phase plan and module boundaries, local PostgreSQL Docker Compose setup and usage documentation, environment examples, ordered SQL migrations and seed data, database schema checks/tests, and ERD documentation. The schema covers users and roles, user-scoped conversations/messages/memory, billing, optional provider configuration, media/presentation metadata, audit logs, indexes, ownership constraints, and row-level security; migration `0003` hardens role-assignment RLS.

**Remaining:** Execute migrations on a fresh PostgreSQL 16+ database, run schema/RLS tests using a non-owner, non-superuser app role, verify cross-user isolation and Compose lifecycle, and confirm API/database integration.

**Blocker/risk:** Migration integrity remains unresolved. A prior task accidentally replaced and restored `services/api/db/migrations/0001_initial_schema.sql` with content that may not preserve its original intent. Review/correct it against the intended schema before accepting Phase 1. Migrations are plain ordered SQL; apply lexicographically.

## Phase 2 — Authentication, security, API, and user management

**Built/committed:** FastAPI service with versioned registration/login/logout/current-user endpoints, protected Brain routes, memory and optional agent integration, request validation/IDs, safe error handling, password hashing, expiring/revocable bearer tokens, default-deny role and ownership checks, approval and audit primitives, and user-management services. API uses PostgreSQL-backed identity services and transaction-local user context for RLS. API/security tests and usage documentation are present.

**Remaining:** Run API/unit and live database integration tests; verify migration compatibility, authentication persistence, transaction-local RLS context, cross-user isolation, and complete authorization on sensitive Brain/tool actions. Token/approval/audit state is process-local; it supports only a single worker until an approved shared persistent adapter exists. Background tasks are in-process and not durable. Configure password/token peppers through deployment environment secrets; never commit real secrets.

**Blocker/risk:** External AI integrations remain optional and unconfigured. Shared persistence for security state and durable background execution are not implemented. Review action-specific authorization and caller context before enabling sensitive generation/tool actions. Existing APIs use request/response; no WebSocket was added.

## Phase 3 — Brain, model runtime, memory, and knowledge

**Built/committed:** Brain contracts and runtime under `services/api/modules/brain`. Deterministic offline intent classification with confidence scores (not represented as a trained model), generation orchestration, explicit in-process model registry and priority routing, timeout-bounded OpenAI-compatible chat-completion adapters, server-environment-configured local and self-hosted endpoints, model selection, and opt-in self-hosted fallback when a configured primary runtime fails. Memory service persists owner-scoped conversations/messages/typed memories and provides lexical/vector retrieval plus provenance-verified knowledge chunking. Authenticated Brain and memory REST routes are mounted; optional embedding search filters candidates to the requested owner. No third-party provider is required for basic operation.

**Evaluation present:** Brain and memory tests cover classifier examples, registry/model behavior, optional fallback, input/limit validation, safe runtime failures, owner isolation, vector filtering, and source verification. These are test sources, not evidence of execution or language-model quality.

**Remaining:** Run Brain, memory, API/web, and live database/RLS suites; validate configured local/self-hosted runtimes against compatible endpoints; verify authentication, database integration, and caller ownership in the complete service. Runtime registries and environment configuration are process-local; durable/multi-worker administration is not provided.

**Blocker/risk:** Runtime and tests remain unverified in this status update. Configure endpoint credentials only through deployment environment/secrets. Do not expose generation to untrusted users without deployment-appropriate authentication and authorization.

## Phase 4 — Personal Agent

**Built/committed:** Conservative deterministic task planning, explicit tool registry, synchronous owner-scoped task execution/history, observations and tool-result verification, authenticated REST endpoints, workspace-sandboxed UTF-8 filesystem access, HTTP(S) browser inspection/navigation adapters, and an injected computer-control interface with no implicit shell/OS access. Workspace writes, browser navigation, and computer actions are registered as restricted approval-required actions and use the existing shared `RestrictedActionManager`/`ApprovalEngine`; task execution pauses before a sensitive handler and resumes only with an exact action/resource one-time grant issued by a distinct reviewer. Approval rejection, failure, verification, and task ownership are handled fail-closed. Agent unit and API test sources are included.

**Remaining:** Run agent and broader API tests, validate browser/computer adapters in an explicitly provisioned environment, and consider persistence only through the approved shared security/persistence architecture. Task history and approval state are process-local; execution is synchronous, not a durable background worker. Agent routes are mounted only when `NGIT_AGENT_WORKSPACE` is configured.

**Validation record:** Tests were not run in this task. No runtime, integration, browser, computer-control, database, or passing test result is claimed. External AI APIs are not required by the planner.

## Validation record

Tests have not been run in this task. API, database/RLS, web, and integration results remain unverified; no passing result is claimed. Compose startup, migration runtime behavior, and local/self-hosted model endpoint behavior have also not been verified here.

## Phase sequence and boundaries

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved 12-phase delivery order. See [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md), [AGENT_ASSIGNMENTS.md](AGENT_ASSIGNMENTS.md), and [interfaces/SHARED_PROTOCOLS.md](interfaces/SHARED_PROTOCOLS.md) for module dependencies and boundary rules.

## Note

The repository contains later-phase web implementation, but this status scope records Phases 1–4. Migration-integrity warning above remains the concrete blocker for accepting Phase 1 database work.

## Phase 3 implementation record

The Brain runtime and deterministic evaluation suite were already present at the reviewed repository HEAD. This status preserves the actual scope distinction between committed implementation and unverified runtime/test behavior.

## Phase 4 implementation record

The Personal Agent implementation extends the existing agent module and security approval engine. Tool actions are explicit; the planner does not infer arbitrary commands. Approval routes create pending grants through the shared approval service, and a different reviewer must decide them using the existing workflow before a matching grant can be consumed. Filesystem and adapter side effects occur only after authorization. Task state/history are in-memory and are not durable across process restarts.
