# Project status — Phases 1–4

This status records repository implementation evidence. Tests have not been run in this task; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, and local environment

**Built/committed:** Repository foundation and architecture documentation, approved phase plan and module boundaries, local PostgreSQL Docker Compose setup and usage documentation, environment examples, ordered SQL migrations and seed data, database schema checks/tests, and ERD documentation. The schema covers users/roles, user-scoped conversations/messages/memory, billing, optional provider configuration, media/presentation metadata, audit logs, ownership constraints, and row-level security; migration `0003` hardens role-assignment RLS.

**Remaining:** Execute migrations on fresh PostgreSQL 16+; run schema/RLS checks with a non-owner, non-superuser app role; verify cross-user isolation, Compose lifecycle, and API/database integration.

**Blocker/risk:** Migration integrity remains unresolved. A prior task accidentally replaced and restored `services/api/db/migrations/0001_initial_schema.sql` with content that may not preserve original intent. Review/correct against intended schema before accepting Phase 1. Migrations are plain ordered SQL; apply lexicographically.

## Phase 2 — Authentication, security, API, and user management

**Built/committed:** FastAPI registration/login/logout/current-user endpoints, protected Brain routes, optional memory and agent integration, request validation/IDs, safe error handling, password hashing, expiring/revocable opaque bearer tokens, server-derived role context, and PostgreSQL-backed identity services with transaction-local user context for RLS. The shared security module implements default-deny RBAC/resource ownership policies, approval-gated restricted actions, one-time expiring approvals requiring a distinct reviewer, emergency stop, secret-name validated environment lookup, and recursively filtered thread-safe in-process audit events. Authentication re-reads active account state and roles on each request, rather than relying on token role snapshots. API/security test sources and usage documentation are present.

**Runtime boundaries:** Authentication tokens, approvals, emergency stop, and audit events are process-local and not restart- or multi-worker-safe. They require an approved shared persistence adapter before deployment with multiple workers or reliance on durable security state. Background tasks are in-process and not durable. Password and token peppers must be provided as deployment environment secrets; `.env.example` contains no usable authentication pepper values. Never use a committed or example credential as a production secret. Audit redaction is best-effort defense-in-depth; callers must not pass sensitive data.

**Remaining:** Run API/unit tests and live database integration; verify migration compatibility, password/token/approval/audit persistence expectations, transaction-local RLS context and cross-user isolation, and authorization at each sensitive Brain/tool operation. Review the current action-specific policy coverage before exposing additional actions. Configure peppers through deployment secrets; no production secret manager is selected.

**Blocker/risk:** External AI integrations are optional and unconfigured. Shared persistence for security state and durable background execution are not implemented. Review caller context and specific authorization checks before enabling sensitive generation or tools.

## Phase 3 — Brain, model runtime, memory, and knowledge

**Built/committed:** Brain contracts and runtime under `services/api/modules/brain`. Deterministic offline intent classification with confidence scores (not represented as a trained model), generation orchestration, explicit in-process model registry and priority routing, timeout-bounded OpenAI-compatible chat-completion adapters, server-environment-configured local and self-hosted endpoints, model selection, and opt-in self-hosted fallback when a configured primary runtime fails. Memory service persists owner-scoped conversations/messages/typed memories and provides lexical/vector retrieval plus provenance-verified knowledge chunking. Authenticated Brain and memory REST routers are mounted; optional embedding search filters candidates to requested owner. No third-party provider is required for basic operation.

**Evaluation present:** Brain and memory tests cover classifier examples, registry/model behavior, optional fallback, input/limit validation, safe runtime failures, owner isolation, vector filtering, and source verification. These are test sources, not evidence of execution or model quality.

**Remaining:** Run Brain, memory, API/web, and live database/RLS suites; validate configured local/self-hosted runtimes against compatible endpoints; verify authentication, database integration, and caller ownership in the complete service. Runtime registries/configuration are process-local; durable/multi-worker administration is not provided.

**Blocker/risk:** Runtime and tests remain unverified. Configure endpoint credentials only through deployment environment/secrets. Do not expose generation to untrusted users without deployment-appropriate authentication and authorization.

## Phase 4 — Personal Agent

**Built/committed:** Conservative deterministic task planning, explicit tool registry, synchronous owner-scoped task execution/history, observations and tool-result verification, authenticated REST endpoints, sandboxed UTF-8 workspace file operations, HTTP(S)-only browser inspection/navigation adapters, and injected computer-control interface with no implicit shell/OS access. Workspace writes, browser navigation, and computer actions are registered as restricted approval-required actions using the shared `RestrictedActionManager`/`ApprovalEngine`; execution pauses for a distinct reviewer and resumes only with an exact one-time action/resource grant. Approval rejection, failure, verification, and task ownership are handled fail-closed. Agent unit/API test sources are included; routes mount only when `NGIT_AGENT_WORKSPACE` is configured.

**Remaining:** Run Agent and broader API tests; validate browser/computer adapters in an explicitly provisioned environment. Consider persistence only through approved shared security/persistence architecture. Task history and approval state are in-memory and execution is synchronous, not a durable background worker.

**Validation record:** Tests have not been run in this task. No runtime, integration, browser, computer-control, database, or passing test result is claimed. External AI APIs are not required by the planner.

## Validation record

Tests have not been run in this task. API, database/RLS, web, and integration results remain unverified; no passing result is claimed. Compose startup, migration runtime behavior, and local/self-hosted model endpoint behavior have also not been verified here.

## Phase sequence and boundaries

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved 12-phase delivery order. See [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md), [AGENT_ASSIGNMENTS.md](AGENT_ASSIGNMENTS.md), and [interfaces/SHARED_PROTOCOLS.md](interfaces/SHARED_PROTOCOLS.md) for module dependencies and boundary rules.

## Note

The repository contains later-phase web implementation, but this status scope records Phases 1–4. The migration-integrity warning above remains the concrete blocker for accepting Phase 1 database work.

## Phase 3 implementation record

The Brain runtime and deterministic evaluation suite were already present at the reviewed repository HEAD. This status preserves the distinction between committed implementation and unverified runtime/test behavior.

## Phase 4 implementation record

The Personal Agent implementation extends the existing agent module and shared security approval engine. Tool actions are explicit; the planner does not infer arbitrary commands. Approval routes create pending grants through the shared approval service, and a distinct reviewer must decide them before a matching grant is consumed. Task state/history is in-memory and does not survive process restart.

## Phase 2 security implementation note

The security primitives are useful for a single-process development deployment only. In particular, in-memory token revocation, emergency-stop state, approvals, and audit events are not durable. Configure `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` through deployment secret injection; never commit real values. A shared durable security-state implementation and production-grade secret-management integration remain open architecture decisions.

Tests were not run for this status update.
