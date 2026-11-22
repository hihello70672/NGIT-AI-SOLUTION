# NGIT AI SOLUTION — Architecture

**Status:** Approved target architecture; not a claim that the planned product modules have been implemented.

## Repository baseline

At planning time the repository contained only a title-only `README.md`. This is a fresh build. The paths and module descriptions below define the target; folders should be added with real implementation or documentation, not empty scaffolding.

## System shape

NGIT is web-first. Build the web application and backend before considering platform-specific projects. The only frontend in this milestone is `apps/web`; NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID are out of scope.

The backend is a modular FastAPI application. Domain modules share one application and PostgreSQL initially, while retaining clear ownership and service boundaries. PostgreSQL is the system of record, with migrations and enforceable user isolation as domain data is implemented. Do not introduce distributed services, a message broker, or mandatory third-party AI providers without an approved need.

The web UI should be responsive, dark, use green brand accents and Poppins or Inter typography, and provide clear loading, empty, and error states. The frontend framework remains open. Local installation uses Docker Compose. Production deployment topology is unspecified.

## Target repository layout

```text
NGIT-AI-SOLUTION/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── compose.yaml
├── apps/
│   └── web/                         # Sole frontend in this milestone
│       ├── README.md
│       ├── package.json
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── features/
│       │   ├── lib/
│       │   └── styles/
│       └── tests/
├── services/
│   └── api/
│       ├── README.md
│       ├── app/
│       │   ├── main.py
│       │   ├── api/{deps.py,v1/{router.py,routes/}}
│       │   ├── core/{config.py,errors.py,logging.py,security/}
│       │   ├── contracts/
│       │   ├── db/{base.py,session.py,migrations/}
│       │   ├── modules/{identity,users,brain,models,memory,knowledge,agent,language,media,presentations,newsroom,education,cybersecurity,providers,billing,administration,audit}/
│       │   └── tasks/
│       └── tests/
├── docs/{architecture,api,operations,status}/
├── infra/{docker,scripts}/
└── tests/integration/
```

This is a target map, not evidence that every listed path exists. Add module-specific subfolders when needed for working implementation.

## Module ownership and boundaries

Each module owns its domain logic, validation, persistence models/migrations, and tests. It may use another module's published service contract, but must not access another module's private implementation or write to its tables.

| Module | Ownership |
|---|---|
| `identity`, `users` | Authentication and account lifecycle, roles, and profile data. Authorization policy enforcement belongs to shared security. |
| `brain`, `models` | Intent, orchestration, confidence, response generation, model registry/routing, and local/self-hosted runtime interfaces. Provider fallback is optional. |
| `memory`, `knowledge` | User/conversation memory, retrieval, ingestion, source verification, isolated user-scoped knowledge. |
| `agent` | Planning, tool registry/execution, browser/computer interfaces, observation/verification, sensitive-action permission and approval checks. |
| `language` | Language/dialect detection, multilingual output, code-switching, translation, style, and voice/vision/remote-control interfaces. |
| `media` | Creative image, video, and document workflows and asset management; prefer local/self-hosted processing where practical. |
| `presentations` | Scripts, scenes, storyboards, assets, timelines, audio sync, subtitles, preview, and export for specified modes. |
| Presenter capability | Avatar, lip-sync, facial/body/gesture animation, TTS, speech alignment, voice configuration, and virtual studio. Placement is open; it must have a distinct service contract. |
| `newsroom` | Aggregation, analysis, verification, headlines, scripts, narration, ticker, subtitles, archives. Do not fabricate real-world events or pass generated footage as authentic. |
| `education` | Lesson generation, teaching presentations, virtual teacher/classroom, visual explanations, quizzes, assessment. |
| `cybersecurity` | Authorized assessment, network/web analysis, configuration audits, forensics, safe labs, remediation. Validate authorization and constrain targets. |
| `providers` | Optional provider configuration/credential references, health checks, usage/cost, routing/fallback, search/browser adapters. External APIs remain optional. |
| `billing` | Plans, subscriptions, metering, quotas, payment verification, history, webhooks, renewals, refunds. No provider integration until selected. |
| `administration` | Admin operations for users, roles, models, knowledge, learning requests, reports, rules, service controls, analytics, audits, emergency controls. Enforce privileges in backend. |
| `core/security`, `audit` | Shared authn/authz infrastructure, approvals, restricted-action enforcement, audit, secret-handling interfaces, emergency stop. |
| `tasks` | Shared background-task submission/status interface. Runner is unselected. |
| `apps/web` | Web screens/components calling backend APIs; never authority for permissions, billing, or user isolation. |

## Shared implementation rules

- Expose domain operations through typed service interfaces. Keep HTTP route handlers thin: parse, acquire authentication context, serialize, map errors.
- User-scoped operations receive explicit caller/user context. Never infer ownership from client-supplied IDs.
- Modules use their own persistence layer; cross-module access goes through a published service contract.
- Validate at API boundaries and again when internal/background inputs cross trust boundaries.
- Background work has acceptance, status, and failure reporting. Long/external operations have explicit states, actionable errors, and timeout/status behavior.
- PostgreSQL user-owned records have enforceable ownership relationships and are queried under authenticated user scope. Test cross-user access.
- Record security-sensitive and administrative audit events. Do not log credentials, tokens, private prompts, or unnecessary personal data.
- Use stable enum values; represent money as currency plus integer minor units, never floating point.
- Python modules/functions and database identifiers use `snake_case`; Python types use `PascalCase`; API paths are lowercase.
- Secrets come from environment/configuration or a secret-management interface, never source control or browser code.
- Sensitive agent actions require backend authorization and policy-required approval; UI confirmation is not authorization.
- Domain modules call shared security/audit services, not competing policy implementations.

## Open decisions (not silently selected)

1. Frontend framework, package manager, and build tool.
2. Database migration and ORM/query tooling.
3. Authentication method, session/token format, and account recovery.
4. PostgreSQL row-level security in addition to service ownership checks.
5. Embedding/vector search approach and acceptable embedding models.
6. First local/self-hosted model runtime, model formats, and hardware requirements.
7. Background-task runner and delivery guarantees.
8. WebSocket auth, reconnection, and delivery semantics.
9. Presenter placement under presentations/media or separate module.
10. Media/generated-artifact storage backend.
11. Payment provider, if any; no integration until selected.
12. Approved external model/search/provider adapters and secret storage.
13. Deployment, monitoring, backup/restore, retention, and recovery objectives beyond local Compose.
14. Role of the 20th engineering agent; only 19 module-owner roles are named.

## Architecture governance

The Chief Architect coordinates boundaries and approves changes to shared contracts or module boundaries. Owners report status, dependencies, actual tests, blockers, and proposed contract changes. Follow the approved phase order; do not begin downstream feature modules ahead of shared dependencies and contracts.
