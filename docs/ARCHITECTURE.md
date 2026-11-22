# NGIT AI SOLUTION — Architecture

**Status:** Approved target architecture. This document distinguishes repository evidence from planned capabilities; it does not claim every target module is implemented or runtime-validated. See [status](STATUS.md).

## System shape and stack

NGIT is a modular, web-first application. `apps/web/` is the only frontend in this milestone: React, TypeScript, and Vite. Windows, Kali, and Android clients are future adaptations and must not delay or reshape the web/backend system before it is stable. The frontend should be responsive, dark, use green brand accents and Poppins or Inter typography, and show clear loading, empty, and error states. It consumes backend APIs; it is not an authorization boundary and never connects directly to PostgreSQL.

The backend is FastAPI under `services/api/`, exposing REST by default and WebSockets only where streaming or bidirectional interaction warrants them. Use service layers, boundary validation, consistent safe errors, and background-task interfaces for long-running work. PostgreSQL is the system of record for persisted application data. Enforce user ownership in backend queries and, where configured, database row-level security (RLS).

Docker Compose supports local PostgreSQL and application development. The current Compose file defines PostgreSQL only; API and web containers are not part of it. Production topology and operational requirements remain open. NGIT Brain must retain a local or self-hosted model-runtime path; third-party AI APIs are optional and must not be required for core operation.

## Repository layout and preservation

This layout reflects the repository evidence and approved target. The listed paths do not claim every proposed domain subdirectory exists. Preserve current API files, module layout, migrations, and tests; do not move working files or create empty scaffolding to match an illustration.

```text
NGIT-AI-SOLUTION/
├── apps/
│   └── web/                         # React/TypeScript/Vite frontend
├── services/
│   └── api/                         # FastAPI service
│       ├── modules/                 # Existing feature modules; preserve current layout
│       ├── db/migrations/           # Existing ordered SQL migrations 0001–0004
│       └── tests/                   # Existing API/database test sources
├── docs/
│   ├── AGENT_ASSIGNMENTS.md
│   ├── ARCHITECTURE.md
│   ├── DEPENDENCY_MAP.md
│   ├── ERD.md
│   ├── PHASE_PLAN.md
│   ├── STATUS.md
│   └── interfaces/
│       ├── AGENT.md
│       ├── BRAIN.md
│       ├── MEMORY.md
│       └── SHARED_PROTOCOLS.md
├── infra/docker/                    # Local Compose guidance
├── .env.example
├── .gitignore
├── README.md
└── compose.yaml                     # Local PostgreSQL
```

`docs/TEST_REPORT.md` is absent. Do not report a test report or validation artifact unless tests have actually run and the file is committed. Add paths only with working implementation or substantive documentation.

## Module ownership and boundaries

Each module owns its behavior, validation, persistence model and migrations, and tests. Other modules call published typed service contracts; they do not import private internals or write another module’s tables.

| Module | Boundary and responsibility |
|---|---|
| Identity and users | Authentication, account lifecycle, identity, and user operations. Authentication/session format remains open. |
| Core security and audit | Server-derived caller context, authorization, policy and approval checks, restricted actions, audit, emergency stop, and secret-handling interfaces. |
| NGIT Brain and models | Intent recognition, reasoning orchestration, confidence detection, response generation, model registry/routing, and local/self-hosted runtime. External fallback is optional. |
| Memory and knowledge | User and conversation memory, retrieval, ingestion, provenance/source verification, preference memory, and user isolation. |
| Personal Agent | Planning, tool registry, execution, browser and computer-control interfaces, observation, verification, and permission checks. Sensitive actions require backend authorization and, where designated, explicit approval. |
| Language intelligence | Language and dialect handling, translation, code-switching, multilingual responses, style adaptation, and coordinated voice, vision, and remote-control interfaces. |
| Providers and integrations | Optional provider configuration, connection and health checks, usage/cost, routing/fallback, search, and browser adapters. Credentials remain server-side. |
| Creative AI and media | Image, video, and document workflows; processing, composition, media management, and rendering. Prefer local/self-hosted processing where practical. |
| Video presentations | Text-to-script, scenes, storyboards, asset matching, timelines, audio sync, subtitles, previews, and export for specified presenter/content modes. |
| Presenter capability | Robot/human avatars, lip-sync, facial, gesture and body animation, text-to-speech, speech alignment, voice configuration, and virtual studio. |
| Newsroom | Aggregation, analysis, verification, headlines, scripts, narration, ticker, subtitles, and archives. Do not fabricate events or present generated footage as authentic. |
| Education | Lesson planning/generation, teaching presentations, virtual teacher/classroom, visual explanations, quizzes, and assessment. |
| Cybersecurity | Authorized assessments, network/web analysis, configuration audits, forensics, safe labs, and remediation reporting. Validate authorization and scope. |
| Billing | Plans, subscriptions, metering, quotas, payment verification, history, webhooks, renewals, and refunds. Do not assume a payment provider or expose credentials. |
| Administration | Backend-enforced administration for users, roles, models, knowledge, rules, services, reports, analytics, audit, and emergency controls. |
| Web application | The sole frontend in this milestone; consumes documented APIs and provides accessible operation states. |

## Shared interfaces and API conventions

The starting shared-interface documents are `docs/interfaces/SHARED_PROTOCOLS.md`, `AGENT.md`, `BRAIN.md`, and `MEMORY.md`. Inspect them and current code before extending them. Changes to a shared contract or module boundary require Chief Architect review.

- A module publishes typed request/result contracts and documented failure behavior. Consumers do not depend on private persistence or implementation.
- Authenticated services receive **server-derived caller context**. Never authorize from a client-supplied user ID, role, permission, or approval.
- User-scoped reads/writes enforce ownership in service queries. Test cross-user isolation; validate RLS using a non-owner, non-superuser application role.
- Sensitive operations use shared policy/approval immediately before execution when required and record relevant audit outcomes.
- Long-running work defines task status/result, owner context, correlation, idempotency, retry, cancellation, and failure behavior before reliability or durability claims.
- Keep credentials, provider secrets, tokens, prompts, stack traces, and other users’ data out of responses and logs.
- Validate requests at API boundaries and enforce authorization in backend services. Use safe errors with stable machine-readable codes, user-safe messages, and request/correlation identifiers. Do not return secrets, internal traces, or other users’ data.
- Preserve existing routes and schemas after inspection. Versioning, exact error envelope, and cross-language JSON casing must be reconciled with current API before standardization; do not silently break clients.
- PostgreSQL is authoritative. Services own their tables and migrations; cross-module access uses contracts. Validate provider callbacks, imported knowledge, browser/tool output, and administrative inputs as untrusted.
- Event/task envelopes identify type, correlation, owner context where applicable, timestamp, and payload; consumers validate payloads and handle failure states. Event transport and exact schema remain open.

Use Python `snake_case`, TypeScript `camelCase`, and SQL `snake_case` for new code unless inspected repository conventions require a compatibility-preserving choice. REST is default; WebSockets require a justified streaming/bidirectional use case.

## Dependency and security principles

Identity establishes authenticated context. Core security owns authorization, policy, approvals, audit, and emergency controls. Brain may consume Memory and optional provider capabilities; Agent uses registered tools and security controls; language intelligence is reusable by Brain, media, news, education, and presentations. Presentation orchestration consumes media and presenter contracts rather than embedding their internals. Newsroom, cybersecurity, billing, and administration cannot bypass authorization and audit. Optional integrations stay behind module contracts.

The dependency sequence is Foundation → Identity → Security → Brain/Memory → Agent/tools → Language/platform capabilities → Administration/Billing/optional integrations → Creative/media/presentations/presenters/newsroom/education/cybersecurity. Arrows indicate published capability use, not permission to access private internals. Brain generation must use authenticated caller authorization before exposure; the status report records that its generation endpoints remain separate from authenticated caller authorization.

## Decisions still open

ORM and migration tooling; authentication/session and durable persistence for tokens, approvals, emergency-stop state and audit; RLS policy/context and application database role; vector search and embeddings; local model runtime/configuration and distribution; durable task runner, delivery guarantees, retries and cancellation; WebSocket authentication/reconnect semantics; media/artifact storage; payment provider; approved external provider/search/browser adapters and secret management; production topology, monitoring, backup/recovery; and the twentieth engineering-role coordination (the specification names 19 specialist assignments). Do not silently choose these or imply production readiness.

## Validation and references

Apply migrations to fresh PostgreSQL 16+, verify constraints/RLS with a non-owner role, run cross-user database tests and Compose lifecycle checks. These checks are outstanding in the status record. Checked-in tests are not evidence that they ran. Report exact commands and outcomes; do not claim passing validation without execution.

- [Dependency map](DEPENDENCY_MAP.md)
- [Phase plan](PHASE_PLAN.md)
- [Agent assignments](AGENT_ASSIGNMENTS.md)
- [Shared protocols](interfaces/SHARED_PROTOCOLS.md)
- [Agent](interfaces/AGENT.md), [Brain](interfaces/BRAIN.md), [Memory](interfaces/MEMORY.md)
- [Repository status and validation gaps](STATUS.md)
- [Local Docker guidance](../infra/docker/README.md)

Shared-contract or module-boundary changes require Chief Architect review. Preserve existing implementation and inspect interface documents before extending them.
