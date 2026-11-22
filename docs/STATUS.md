# Project status — Phases 1–4

Status is based on files present in the reviewed default-branch tree. Tests and runtime checks are only reported as executed when actually run; checked-in tests alone do not establish passing outcomes.

## Phases 1–3

Foundation, architecture, database schema/migrations, reference seed data, ERD, and disposable PostgreSQL schema-isolation assertions are present. Five ordered migrations (`0001`–`0005`) are present. SQL tests and a runner are checked in; migration execution, database tests, grants, non-owner RLS behavior, and Compose lifecycle remain unverified. Brain and memory test sources are present, with no passing outcomes claimed.

## Phase 2 — Authentication, backend security, users, and web

Backend authentication and security services are present: password verification, opaque bearer tokens, server-derived roles, authenticated REST boundaries, ownership checks, allow-list policy/RBAC, approval decisions with reviewer separation and one-use scoped grants, restricted-action gates, emergency stop, redacted audit events, and environment-backed secret lookup. Security primitives are process-local; use one worker until approved shared persistence is implemented and verified.

The React/TypeScript/Vite frontend in `apps/web` provides sign-in and registration, a responsive dark green-accented workspace shell, overview, Brain chat, Personal Agent tasks, profile settings, and a read-only administrator user listing. The web API client consumes the existing backend auth, profile, user-list, Brain, and Agent routes. UI test sources cover authentication errors, navigation, API-backed chat and agent flows, profile updates, and administrator access. Tests and build checks have not been run for this work; no passing result is claimed.

## Phase 4 — Personal Agent

Deterministic explicit-goal task planning; allowlisted tool registry; authenticated owner-scoped task submission, detail/history, execution, and rejection; bounded filesystem, browser, and injected computer-control interfaces; observations and verification; and shared policy/approval-gated sensitive actions are present. Sensitive actions authorize immediately before execution and use one-time approvals scoped to the exact action and task-step resource. Browser URL syntax validation is not an SSRF/network boundary. Filesystem workspace confinement is not an OS sandbox. Task/security state remains process-local, so run a single worker.

Agent unit and API test sources are present. They have not been run as part of this implementation; no passing result is claimed. Cross-user isolation, approval lifecycle, rejection, and adapter behavior require execution-time validation.

## Verification record

No tests or runtime checks were run for this change.

## Security deployment caveats

The token pepper and password pepper must be set to deployment-specific random values; `.env.example` contains placeholders only. Authentication tokens, approvals, emergency-stop state, and audit events are process-local and are not durable across restarts or shared across workers. External AI APIs remain optional. Environment lookup is a configuration primitive, not a production secret manager.
