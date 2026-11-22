# NGIT AI SOLUTION — Architecture

**Status:** Approved target architecture. This document distinguishes repository evidence from planned capabilities; it does not claim every target module is implemented or runtime-validated. See [status](STATUS.md).

## System shape

NGIT is a web-first modular application. `apps/web` is the sole frontend in this milestone: React, TypeScript, and Vite. Windows, Kali, and Android clients are future adaptations and are out of scope until the web/backend system is stable. The backend is a modular FastAPI application under `services/api`; PostgreSQL is the system of record. Docker Compose provides the local PostgreSQL installation. Production topology and operational requirements remain open.

The web UI should be responsive, dark, use green brand accents and Poppins or Inter typography, and present clear loading, empty, and error states. The frontend consumes documented backend APIs; it never connects directly to the database or makes authorization decisions.

NGIT Brain must retain a local or self-hosted model-runtime path. External AI providers are optional integrations. Do not make core operation depend on external AI APIs. Use WebSockets only where streaming or bidirectional communication justifies them. Long-running work requires an explicit task status/result contract; runner technology, durability, retries, cancellation, and delivery guarantees remain open decisions.

## Repository layout and preservation

The following summarizes the existing repository roots and documented targets. It is not an assertion that every illustrative subdirectory exists. Preserve the current flat API files, `services/api/modules/`, migration and test paths; do not move working code merely to match a proposed tree. Add only paths backed by working implementation or substantial documentation.

```text
NGIT-AI-SOLUTION/
├── apps/web/                         # Existing React/TypeScript/Vite application
├── services/api/                     # Existing FastAPI backend and modules
│   ├── modules/                      # Existing feature modules
│   ├── db/migrations/                # Existing SQL migrations (verify before use)
│   └── tests/                        # Existing API test sources
├── docs/
│   └── interfaces/                   # Shared contract documents
├── infra/docker/                     # Local Compose guidance
├── .env.example
├── compose.yaml                      # Local PostgreSQL
└── README.md
```

An agreed future organization may group routes/schemas/dependencies under `api`, configuration/errors/logging/security under `core`, domain services under `modules`, and task interfaces under `tasks`. Verify current migration and test locations before proposing changes. Do not create empty scaffolding.

## Module ownership and boundaries

Each domain owns its behavior, validation, persistence model/migrations, and tests. Other modules call published typed service contracts; they do not import private internals or write another module’s tables.

| Capability | Responsibility |
|---|---|
| Identity and users | Authentication, account lifecycle, user records, and identity operations. Session/auth format remains a decision. |
| Core security and audit | Server-derived caller context, authorization, approvals, restricted actions, audit, emergency stop, and secret-handling interfaces. |
| NGIT Brain and models | Intent, reasoning orchestration, confidence, response generation, model registry/routing, and local/self-hosted runtime. External fallback is optional. |
| Memory and knowledge | User/conversation memory, retrieval, ingestion, source verification, preferences, and isolation. |
| Personal Agent | Planning, tools, execution, browser/computer interfaces, observation and verification. Sensitive actions require backend permissions and approval. |
| Language intelligence | Language/dialect handling, multilingual output, translation, code-switching, style, and coordinated voice/vision/remote interfaces. |
| Providers and integrations | Optional provider configuration, health/usage/cost, routing/fallback, search, and browser adapters. Keep credentials server-side. |
| Media and creative AI | Image/video/document workflows, processing, assets, composition, management, and rendering. Prefer local processing where practical. |
| Presentations | Scripts, scenes, storyboards, assets, timelines, sync, subtitles, preview/export, and specified modes. Presenter implementation remains separate. |
| Presenter capability | Avatar/robot presenters, animation, gestures, speech alignment, TTS, voice configuration, and virtual studio. |
| Newsroom | Aggregation, analysis, verification, scripts, narration, ticker, subtitles, and archives. Do not fabricate events or pass generated footage as authentic. |
| Education | Lessons, teaching presentations, virtual teacher/classroom, visual explanations, quizzes, and assessment. |
| Cybersecurity | Authorized assessments, network/web analysis, configuration audits, forensics, safe labs, and remediation reporting. Validate authorization and scope. |
| Billing | Plans, subscriptions, metering, quotas, payment verification, history, webhooks, renewals, and refunds. No payment provider is assumed. |
| Administration | Backend-protected user/role/model/knowledge/rule/service/audit/report and emergency operations. |
| Web application | The single frontend; consumes API contracts and provides accessible operation states. |

## Dependency and security principles

- Identity establishes authenticated context. Backend services enforce permissions; UI restrictions are not security controls.
- Every user-scoped service receives server-derived caller context. Never trust a user ID, role, permission, or approval supplied only by the client.
- Sensitive actions require policy checks and, when designated, explicit approval immediately before execution; record relevant outcomes in audit.
- PostgreSQL is authoritative. Enforce ownership in service queries and test isolation; validate RLS using a non-owner, non-superuser app role. RLS policy/context details require verification.
- Validate at trust boundaries, including provider callbacks, imported knowledge, browser/tool output, and administration. Errors must not expose secrets, prompts, stack traces, or other users’ data.
- Use environment/configuration or an approved secrets interface; never commit credentials. Keep external AI optional.
- Background jobs/events must preserve owner context and define status, correlation, idempotency, retry, and failure behavior before reliability claims.

## Decisions still open

ORM and migration tooling; authentication/session and security-state persistence; RLS policy/context; vector search and embeddings; local model runtime and configuration; durable task runner and guarantees; WebSocket authentication/reconnect semantics; media/artifact storage; payment provider; approved external adapters and secret management; production topology, monitoring, backup/recovery; and the twentieth engineering-role coordination. Do not silently choose these or imply production readiness.

## References

- [Dependency map](DEPENDENCY_MAP.md)
- [Phase plan](PHASE_PLAN.md)
- [Agent assignments](AGENT_ASSIGNMENTS.md)
- [Shared protocols](interfaces/SHARED_PROTOCOLS.md)
- [Agent](interfaces/AGENT.md), [Brain](interfaces/BRAIN.md), [Memory](interfaces/MEMORY.md)
- [Repository status and validation gaps](STATUS.md)
- [Local Docker guidance](../infra/docker/README.md)

Shared-contract or module-boundary changes require Chief Architect review. Preserve existing implementation and inspect existing interface documents before extending them.
