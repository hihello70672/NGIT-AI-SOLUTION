# Project status — Phases 1–4

Status is based on files present in the reviewed default-branch tree. Tests and runtime checks are only reported as executed when actually run; checked-in tests alone do not establish passing outcomes.

## Phases 1–3

Foundation, architecture, database schema/migrations, reference seed data, ERD, and disposable PostgreSQL schema-isolation assertions are present. The schema covers users, roles, forced row-level isolation, conversations/messages, memories, billing reference/subscription/usage records, optional provider metadata, media/video/presentation metadata, audit logs, and supporting indexes. Five ordered migrations (`0001`–`0005`) are present. SQL tests and a runner are checked in; migration execution, database tests, grants, non-owner RLS behavior, and Compose lifecycle remain unverified. Brain and memory tests are present but no passing outcomes are claimed.

## Phase 2 — Authentication, backend security, users

Authentication and security services are present: password verification, opaque bearer tokens, server-derived roles, authenticated REST boundaries, owner checks, allow-list policy/RBAC, approval decisions with reviewer separation and one-use scoped grants, restricted-action gates, emergency stop, redacted audit events, and environment-backed secret lookup. These security primitives are process-local; run one worker until approved shared persistence is implemented and verified. Frontend sign-in, registration, dashboard, profile, and read-only administrator listing are present under `apps/web`. Tests cover the security engines and API boundaries; they have not been run as part of this work, so no passing result is claimed.

## Phase 4 — Personal Agent

Deterministic explicit-goal task planning; allowlisted tool registry; authenticated owner-scoped task submission, detail/history, execution, and rejection; bounded filesystem, browser, and injected computer-control interfaces; observations and verification; and shared policy/approval-gated sensitive actions are present. Sensitive actions authorize immediately before execution and use one-time approvals scoped to the exact action and task-step resource. Adapters are opt-in; browser URL syntax validation is not an SSRF/network boundary. Filesystem workspace confinement is not an OS sandbox. Task/security state remains process-local, so run a single worker.

Agent unit and API test sources are present. They have not been run as part of this implementation; no passing result is claimed. Cross-user isolation, approval lifecycle, rejection, and adapter behavior require execution-time validation.

## Remaining validation

Run the documented backend test suite and validate authenticated ownership, approval/reviewer separation, adapter safety, database migrations/RLS, and application startup before production or multi-worker use. See `docs/interfaces/AGENT.md` for operational boundaries.

## Security deployment caveats

The token pepper and password pepper must be set to deployment-specific random values; `.env.example` contains placeholders only. Authentication tokens, approvals, emergency-stop state, and audit events are process-local and are not durable across restarts or shared across workers. External AI APIs remain optional. Environment lookup is a configuration primitive, not a production secret manager.

## Verification record

No tests or runtime checks were run for this change.
