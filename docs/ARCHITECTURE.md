# NGIT AI SOLUTION v4.0 — Architecture

**Status:** Approved target architecture. Repository implementation status and validation evidence are recorded separately in [STATUS.md](STATUS.md). Reported/checked-in implementation is not equivalent to verified runtime behavior; a checked-in test does not demonstrate that it ran or passed.

## 1. Product boundary and system shape

NGIT is a modular, web-first AI ecosystem, not a chatbot demo. This milestone contains the web application and backend. Future NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID projects are out of scope until the web/backend system is stable.

1. **Web client:** React, TypeScript, and Vite, located only under `apps/web/`.
2. **API/application services:** FastAPI REST endpoints, selective WebSockets, validation, server-derived identity and authorization, orchestration, safe errors, and background-task interfaces under `services/api/`.
3. **Persistence:** PostgreSQL with ordered migrations, indexes, user isolation and auditability. PostgreSQL is authoritative for persisted application state.
4. **Domain modules:** independently owned capabilities that interact through published service/task contracts, not private implementation imports or cross-module table writes.
5. **Operations/delivery:** local Compose, environment-based configuration, observability and production operations decisions, backup/recovery guidance, and evidence-based release verification.

Local or self-hosted AI operation is a core supported path. External AI/provider APIs are optional and cannot become a mandatory dependency for core Brain operation.

| Layer | Required direction |
|---|---|
| Web | Responsive React/TypeScript/Vite client, dark UI with green accents, Poppins or Inter typography, shared design system, clear loading/error states. Consume backend APIs; never connect directly to PostgreSQL or act as the authoritative security boundary. |
| API/services | FastAPI, REST by default, WebSockets only for justified streaming/bidirectional use, service-layer domain logic, validated contracts, server-side authorization, safe errors and task interfaces. |
| Database | PostgreSQL, ordered SQL migrations, transaction boundaries, indexes, user isolation and audit records. ORM/migration framework and final role/RLS deployment policy remain open. |
| AI runtime | NGIT Brain must retain local/self-hosted runtime and routing. Provider fallback is optional, configured server-side, and not a single point of dependency. |
| Local development | Docker Compose and environment configuration documented for startup and recovery. Current Compose boundary is PostgreSQL-only; API/web containers are not implied. |

## 2. Repository layout and reconciliation

Current paths are authoritative. Preserve working code and inspect actual routes, schemas, migrations, module layout and tests before changing them. Do not move or rename code simply to match a target sketch, and do not add empty scaffolding.

```text
NGIT-AI-SOLUTION/
├── apps/web/                       # Sole frontend application this milestone
├── services/api/                   # Existing FastAPI app and feature modules
│   ├── modules/                    # Existing domain modules; preserve their layout
│   ├── db/migrations/              # Existing ordered PostgreSQL SQL migrations
│   ├── db/tests/                   # SQL schema/isolation test sources
│   └── tests/                      # API/module test sources
├── docs/                           # Architecture, ERD, dependency, phase, status, ownership
│   └── interfaces/                 # Shared and module contracts
├── infra/docker/                   # Local Docker and PostgreSQL support/guidance
├── compose.yaml                    # Local PostgreSQL service
├── .env.example                    # Configuration examples; never credentials for deploy
└── README.md
```

Target responsibilities within the existing paths: `apps/web/src/` may organize application shell/routes, features, shared components, design system, API transports and types as implementation warrants. `services/api/` owns FastAPI composition, core configuration/security/error behavior, shared primitives, domain modules, DB/session integration and worker interfaces. Add paths only with working implementation or substantive documentation. Existing SQL migration tooling is ordered plain SQL; do not introduce an ORM or another migration system without an approved decision.

## 3. Module boundaries and responsibilities

Each module owns domain behavior, boundary validation, application services, persistence model/migrations and tests. Consumers use documented typed public contracts. Shared infrastructure must not turn into an unowned duplicate domain service.

| Module | Ownership boundary |
|---|---|
| Backend platform | FastAPI composition, route registration, dependency injection, REST/WebSocket transport, validation, common safe errors and task interfaces. |
| Database | PostgreSQL schema/migrations/indexes, transactions, role grants and user-isolation policy; module data remains module-owned. |
| Identity/security | Authenticated identity context, RBAC/policy, permissions, sensitive-action approvals, audit, emergency stop and secret-handling interfaces. Authoritative checks execute on the backend. |
| NGIT Brain | Intent recognition, orchestration, local/self-hosted runtime, registry/routing, confidence handling, response generation and optional external fallback. |
| Memory/knowledge | User/conversation memory, preferences, ingestion, provenance, retrieval and optional vector search; enforce owner scope. |
| Personal Agent | Planning, task lifecycle, registered tools, execution/observation/verification, and permission/approval gates. Browser, filesystem and computer adapters are constrained capabilities, not authorities. |
| Language intelligence | Language/dialect detection, multilingual responses, translation/code switching, style preferences and voice/vision/remote-control interfaces. |
| Providers/integrations | Optional server-side provider config, health/usage/cost, routing/fallback, search/browser adapters and credential references. Secrets are not exposed to clients. |
| Billing | Plans, subscriptions, metering, quotas, payment verification, history, webhooks, renewals and refunds. Provider choice and production execution are not assumed. |
| Administration | Backend-enforced user/role/model/knowledge/rule/report/service-control/analytics/audit/emergency operations. |
| Creative/media | Image/video/document workflows, composition/rendering, artifact ownership/storage/lifecycle and processing safety. Prefer local/self-hosted processing where practical. |
| Video/presenter | Script/scenes/storyboards/assets/timeline/audio sync/subtitles/preview/export and reusable robot/human presenter, animation, voice and speech-alignment capabilities. |
| Newsroom | Aggregation, analysis, verification, scripts, narration, ticker, subtitles and archives. Do not fabricate real-world events or depict generated footage as authentic. |
| Education | Lessons, teaching presentations, virtual classroom/teacher, visual explanations, quizzes and assessment. |
| Cybersecurity | Authorized assessments, safe labs, network/web/configuration analysis, forensics, reports and remediation. Validate authorization/scope and audit activity. |
| Web application | User-facing UI/API client only; no authoritative access, billing or policy decisions. |

## 4. Shared contracts and protocols

The canonical cross-module guidance is [SHARED_PROTOCOLS.md](interfaces/SHARED_PROTOCOLS.md). Existing module contracts include `ADMIN.md`, `AGENT.md`, `BILLING.md`, `BRAIN.md`, `LANGUAGE.md` and `MEMORY.md`. Inspect contracts and implementation before extension. Changes to shared boundaries/dependencies require Chief Architect review and corresponding contract documentation.

- Modules publish typed input/result contracts and document validation, authorization context, persistence ownership, dependencies and failure behavior.
- Routes translate transport into service calls; business logic is not exclusively embedded in handlers.
- Authenticated operations receive server-derived identity. A user ID, role, permission or approval in an untrusted client payload is not authority.
- User-owned reads/writes/searches/artifacts are owner-scoped at service boundaries. Where RLS is enabled, test as a non-owner, non-superuser role without `BYPASSRLS`; RLS is defense in depth, not a substitute for service authorization.
- Sensitive actions require shared policy checks and designated approval immediately before execution; fail closed if authorization, approval, verification or emergency-state checks fail. Record relevant outcomes through audit contracts.
- Long-running work defines owner context, correlation, status/result/failure, idempotency, retries and cancellation before claiming durability. The runner/scheduling implementation remains open.
- REST is default. WebSockets require a defined reason, auth, authorization, message schemas, reconnect and close/error behavior before dependent features use them.
- Validate all boundary data. Provider callbacks, imported knowledge, browser/tool outputs and administrative input are untrusted. Bound size/time/resource use, avoid leaking secrets/prompts/traces/other-user data.
- Preserve existing API paths and schemas. API versioning, exact error envelope and cross-language JSON casing must be reconciled with actual code before standardization.
- PostgreSQL is authoritative persisted state. Modules own their tables/migrations; cross-module access uses contracts. Event transport and exact event envelope/version/delivery guarantees remain open.

## 5. Dependency direction

```text
Web client (apps/web) -> documented FastAPI API contracts
                              |
Identity/users -> Core security/policy/approval/audit
                              |
                 +------------+------------------+
                 |                               |
              NGIT Brain                     Billing/Admin
                 |                               |
       Memory/Knowledge <-> Language          Identity/security
                 |
      Optional provider adapters (not required for local runtime)
                 |
       Personal Agent -> registered tools + policy/approval + task interface
                              |
       Creative/media -> video/presenter -> Newsroom and Education
                              |
       Cybersecurity -> authorized scope + safe lab + audit
```

Security context and PostgreSQL isolation are foundational. Brain can consume Memory and optional providers by contract. Agent depends on registered tools, authorization/approval and task contracts. Language is reusable by Brain/media/news/education/presentation. Presentation composes media and presenter capabilities; Newsroom and Education consume them rather than duplicate renderers. Cybersecurity is authorized-target/safe-lab only. No domain may bypass identity, ownership, policy, audit or contract boundaries.

## 6. Decisions

**Established by the specification:** web-first milestone; only `apps/web` frontend; FastAPI backend; PostgreSQL persisted data; REST default and selective WebSockets; module-owned service/data contracts; local/self-hosted Brain operation; external providers optional; backend authorization; approval and audit for sensitive actions; cybersecurity restricted to authorized scope/safe labs; preserve existing code; no unverified QA/release claims.

**Still open; do not silently invent incompatible module decisions:** ORM/migration tool beyond current SQL inventory; auth/session and durable token strategy; durable approval/emergency-stop/audit storage; app DB grants/RLS deployment roles; vector search/embedding persistence; local model packaging/configuration; durable task runner/scheduling; WebSocket auth/reconnect; media/artifact storage/lifecycle; payment provider and verification; external provider adapters/secret management; event transport/schema/delivery/versioning; production topology/monitoring/backup/recovery; API version/error envelope/JSON casing; engineering-role coordination. Record and review decisions before dependent production implementation.

## 7. Validation and release evidence

The [phase plan](PHASE_PLAN.md) defines integration gates. Run migrations on a fresh disposable PostgreSQL instance, verify grants and owner isolation through the intended non-owner/non-superuser role, run API/web tests and builds, Compose lifecycle and relevant runtime checks. Record exact commands, environment and outcomes only after execution. Checked-in tests/docs are not execution evidence. Create `docs/TEST_REPORT.md`, release/tag or ZIP claim only after corresponding verification is actually performed.
