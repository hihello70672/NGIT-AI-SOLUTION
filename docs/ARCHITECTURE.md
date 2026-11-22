# NGIT AI SOLUTION v4.0 — Architecture

**Status:** Approved target architecture. Repository status and validation evidence are tracked separately in [STATUS.md](STATUS.md). Phases 1–3 are partly implemented, not fully validated; checked-in tests do not prove execution or passing results.

## 1. System shape and stack

NGIT is a modular, web-first AI ecosystem. This milestone contains one frontend, `apps/web/`, backed by FastAPI services and PostgreSQL. NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID are future adaptations and must not delay or reshape the web/backend system before it is stable.

| Layer | Specification |
|---|---|
| Web client | React, TypeScript, and Vite in `apps/web/`. Responsive dark UI, green brand accents, Poppins or Inter, and consistent loading, empty, and error states. The frontend consumes backend APIs, is not an authorization boundary, and must not connect directly to PostgreSQL. |
| API and services | FastAPI in `services/api/`. REST is the default; use WebSockets only for justified streaming or bidirectional use cases. Apply boundary validation, service-layer authorization, safe errors, and background-task interfaces for long-running work. |
| Persistence | PostgreSQL is the system of record for identity, user isolation, conversations, memory, billing, optional provider metadata, media/video/presentation metadata, and audit logs. Services own persistence and migrations. |
| AI runtime | NGIT Brain retains a local or self-hosted model-runtime path. Third-party AI APIs are optional, not required for core operation. |
| Local development | Docker Compose supports local development. `compose.yaml` currently defines PostgreSQL only; API and web containers are not part of it. |
| Future clients | Windows, Kali, and Android projects are outside this milestone. |

The current status describes phases 1–3 as partly done, not fully validated. Tests and runtime checks have not been run according to the status record. Do not treat checked-in test sources as passing tests.

## 2. Repository layout

This layout is based on repository evidence. Proposed domain subdirectories must not be created as empty scaffolding; add paths only with working implementation or substantive documentation. Preserve the current API/module layout.

```text
NGIT-AI-SOLUTION/
├── apps/
│   └── web/                                      # Existing React/TypeScript/Vite frontend
├── services/
│   └── api/                                      # Existing FastAPI backend
│       ├── modules/                              # Existing feature modules; preserve layout
│       ├── db/
│       │   ├── migrations/                       # Five ordered SQL migrations, 0001–0005
│       │   └── tests/                            # Database test sources and README
│       └── tests/                                # API/backend test sources
├── docs/
│   ├── AGENT_ASSIGNMENTS.md
│   ├── ARCHITECTURE.md
│   ├── DEPENDENCY_MAP.md
│   ├── ERD.md
│   ├── PHASE_PLAN.md
│   ├── STATUS.md
│   └── interfaces/
├── infra/
│   └── docker/                                   # Local Docker guidance
├── .env.example
├── .gitignore
├── README.md
└── compose.yaml                                 # PostgreSQL service only
```

The migration inventory was inspected: `services/api/db/migrations/` contains exactly five ordered SQL migrations: `0001_initial_schema.sql`, `0002_seed_reference_data.sql`, `0003_secure_role_assignments.sql`, `0004_complete_domain_schema.sql`, and `0005_tenant_safe_video_source.sql`. `docs/TEST_REPORT.md` is absent and must only be created after tests have actually run, with exact commands, environment, and outcomes.

## 3. Module ownership and boundaries

Each module owns its behavior, input validation, persistence model and migrations, and tests. Consumers use published typed service contracts rather than importing private implementation details or writing another module’s tables.

| Module | Boundary and responsibility |
|---|---|
| Identity and users | Authentication, account lifecycle, identity, and user operations. Authentication/session format remains open where current code does not settle it. |
| Core security and audit | Server-derived caller context, authorization, policy and approval checks, restricted actions, audit, emergency controls, and secret-handling interfaces. |
| NGIT Brain and models | Intent recognition, reasoning orchestration, confidence detection, response generation, model registry/routing, and local or self-hosted runtime. External fallback is optional. |
| Memory and knowledge | User and conversation memory, retrieval, ingestion, provenance/source verification, preference memory, and user isolation. |
| Personal Agent | Planning, tool registry, execution, browser and computer-control interfaces, observation, verification, and permission checks. Sensitive actions require backend authorization and, where designated, approval. |
| Language intelligence | Language and dialect handling, translation, code-switching, multilingual responses, style adaptation, and coordinated voice, vision, and remote-control interfaces. |
| Providers and integrations | Optional provider configuration, connection and health checks, usage/cost, routing/fallback, search, and browser adapters. Credentials remain server-side. |
| Creative AI and media | Image, video, and document workflows; processing, composition, media management, and rendering. Prefer local or self-hosted processing where practical. |
| Video presentations | Text-to-script, scenes, storyboards, asset matching, timelines, audio sync, subtitles, previews, and export for specified presenter/content modes. |
| Presenter capability | Robot and human avatars, lip-sync, facial, gesture and body animation, text-to-speech, speech alignment, voice configuration, and virtual studio. |
| Newsroom | Aggregation, analysis, verification, headlines, scripts, narration, ticker, subtitles, and archives. Never fabricate real-world events or present generated footage as authentic. |
| Education | Lesson planning/generation, teaching presentations, virtual classroom/teacher, visual explanations, quizzes, and assessment. |
| Cybersecurity | Authorized network/web analysis, configuration audits, forensics, safe labs, and remediation reporting. Validate authorization and scope. |
| Billing | Plans, subscriptions, metering, quotas, payment verification, history, webhooks, renewals, and refunds. Do not assume a payment provider or expose credentials. |
| Administration | Backend-enforced administration for users, roles, models, knowledge, rules, services, reports, analytics, audit, and emergency controls. |
| Web application | The only frontend in this milestone. Consumes documented APIs and provides accessible, responsive operation states. |

## 4. Shared interfaces and protocols

The shared-interface documents are `docs/interfaces/SHARED_PROTOCOLS.md`, `AGENT.md`, `BRAIN.md`, and `MEMORY.md`. Inspect them and current code before extending interfaces. Changes to a shared contract or module boundary require Chief Architect review.

### Service contracts and authorization

- Publish typed request/result contracts and document failure behavior. Consumers must not rely on private persistence or implementation details.
- Authenticated services receive **server-derived caller context**. Never authorize based on a client-supplied user ID, role, permission, or approval.
- Enforce user ownership in service queries. Where PostgreSQL RLS is configured, test it using a non-owner, non-superuser application role without `BYPASSRLS`.
- Perform shared policy/approval checks immediately before sensitive execution when required, and record relevant audit outcomes.
- Long-running work defines task status and result, owner context, correlation, idempotency, retry, cancellation, and failure behavior before claiming reliability or durability.

### API, errors, and validation

- REST is the default. WebSockets require a justified streaming or bidirectional use case; authentication and reconnect behavior remain open.
- Validate all API-boundary inputs and enforce authorization in backend services.
- Use safe errors with stable machine-readable codes, user-safe messages, and request/correlation identifiers. Do not return secrets, internal traces, or other users’ data.
- Treat provider callbacks, imported knowledge, browser/tool output, and administrative inputs as untrusted.
- Keep credentials, tokens, prompts, stack traces, and other users’ data out of responses and logs.
- Preserve existing routes and schemas after inspection. API versioning, exact error envelope, and cross-language JSON casing must be reconciled with existing routes and schemas before standardization.

### Events, tasks, data, and naming

- An event/task envelope identifies type, correlation, owner context where applicable, timestamp, and payload. Consumers validate payloads and handle failure states.
- PostgreSQL is authoritative for persisted application data. Services own their tables and migrations; cross-module access uses contracts.
- Event transport and exact event schema are open decisions. Do not invent or standardize them without architecture review.
- Derive caller identity from authenticated server context and set PostgreSQL `ngit.user_id` transaction-locally from that context where required.
- Use repository conventions where needed for compatibility. New code uses Python `snake_case`, TypeScript `camelCase`, and SQL `snake_case`.

## 5. Dependency and security principles

Identity establishes authenticated context. Core security owns authorization, policy, approvals, audit, and emergency controls. Brain may consume Memory and optional provider capabilities; Agent uses registered tools and security controls; language intelligence is reusable by Brain, media, news, education, and presentations. Presentation orchestration consumes media and presenter contracts rather than embedding their internals. Newsroom, cybersecurity, billing, and administration cannot bypass authorization and audit. Optional integrations stay behind module contracts.

```text
Foundation: API configuration, database conventions, shared protocols
  └── Identity and users
        └── Core security and audit
              ├── Brain and model runtime
              │     └── Memory and knowledge
              │           └── Optional provider/integration capabilities
              │                 └── Personal Agent and registered tools
              │                       └── Administration and rules
              │                             └── Billing
              │                                   └── Language intelligence
              │                                         └── Voice, vision, remote-control interfaces
              ├── Brain
              │     └── Media and presentations
              │           └── Newsroom
              │                 └── Education
              └── Authorized Cybersecurity capabilities

Creative/media → Video presentation orchestration → Presenter capability
                    └── Language/voice capabilities
```

Newsroom → verified sources, language, media/presentation capabilities  
Education → Brain, language, media/presentation capabilities  
Cybersecurity → authorization, policy/approval, audit, safe-lab interfaces  
Administration/Billing/Integrations → identity, security, audit  
Web application → documented backend APIs only

Phase order is: (1) architecture, repository, database, shared protocols; (2) authentication, backend, security, users; (3) Brain, model runtime, memory, knowledge; (4) Personal Agent, tools, browser, computer interfaces; (5) multilingual, voice, vision, remote-control interfaces; (6) administration, rules, service control, billing; (7) optional provider management and browsing; (8) Creative Studio; (9) Content-to-Video, presenters, lip-sync, subtitles; (10) Newsroom, Teaching, Storytelling; (11) Cybersecurity Center; (12) integration, QA, documentation, verified local release.

## 6. Technical decisions and open questions

Established: web-first with React/TypeScript/Vite and FastAPI; PostgreSQL system of record; REST by default; module-owned persistence and published contracts; local/self-hosted Brain path with external AI optional; backend authorization and server-derived caller context; preservation of current implementation; no unverified test or release claims.

Open; do not silently decide: ORM and migration tooling; authentication/session design and durable token, approval, emergency-stop, and audit storage; RLS policy/context and application database role/grants; vector search and embeddings; local model runtime configuration/distribution; durable task runner and delivery/retry/cancellation semantics; WebSocket auth/reconnect; media/artifact storage; payment provider; approved external provider/search/browser adapters and secret management beyond environment lookup; event transport and exact envelope; production topology, monitoring, backup/recovery; API versioning, error envelope, JSON casing after code reconciliation; and engineering-role coordination. The approved specification identifies 19 specialist assignments; Chief Architect coordinates as the twentieth role without adding an implementation module.

## 7. Validation and references

Apply migrations to fresh PostgreSQL 16+, provision the intended non-owner/non-superuser role, verify grants and RLS, and test cross-user isolation. Run documented API/web suites, database/RLS tests, Compose lifecycle checks, production frontend build, and end-to-end local startup as applicable. These checks remain outstanding in the status record; checked-in tests do not prove they ran. Report exact commands and outcomes. Create `docs/TEST_REPORT.md` only after tests actually run.

- [Dependency map](DEPENDENCY_MAP.md)
- [Phase plan](PHASE_PLAN.md)
- [Agent assignments](AGENT_ASSIGNMENTS.md)
- [ERD](ERD.md)
- [Shared protocols](interfaces/SHARED_PROTOCOLS.md)
- [Agent](interfaces/AGENT.md), [Brain](interfaces/BRAIN.md), [Memory](interfaces/MEMORY.md)
- [Repository status and validation gaps](STATUS.md)
- [Local Docker guidance](../infra/docker/README.md)

Shared-contract or module-boundary changes require Chief Architect review. Preserve existing implementation and inspect interface documents before extending them.
