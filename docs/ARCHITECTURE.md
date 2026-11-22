# NGIT AI SOLUTION — Architecture

**Status:** Approved target architecture. This document distinguishes repository evidence from planned capabilities; it is not a claim that all target modules are implemented or runtime-validated.

## Repository baseline

The repository contains a React/TypeScript frontend under `apps/web`, a FastAPI API under `services/api`, PostgreSQL schema migrations and tests, shared interface documentation, and a Docker Compose PostgreSQL service. The status record describes Phases 1–4 as built or partly implemented. Those statements are committed-code evidence only: PostgreSQL/RLS, Compose, API/web suites, and end-to-end integrations still require validation. See [`STATUS.md`](STATUS.md). Do not infer that target-only paths or future modules exist.

## System shape

NGIT is web-first. `apps/web` is the only frontend in this milestone. NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID are out of scope until the web/backend system is stable.

The backend is a modular FastAPI application. Domain modules share one application and PostgreSQL initially while retaining clear ownership and service boundaries. PostgreSQL is the system of record. Do not introduce distributed services, a message broker, or mandatory third-party AI providers without approved need. NGIT Brain must retain a local/self-hosted runtime path; external APIs are optional.

The web UI should be responsive, dark, use green brand accents and Poppins or Inter typography, and provide clear loading, empty, and error states. Docker Compose is the local installation path. Production topology remains unspecified. Background work needs a shared acceptance/status/failure interface; its runner and delivery guarantees are open.

## Target repository layout

This is an architectural target, not evidence that every listed path currently exists. Add paths only with working implementation or substantive documentation; avoid empty scaffolding.

```text
NGIT-AI-SOLUTION/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── compose.yaml
├── apps/
│   └── web/                 # Sole frontend in this milestone
│       ├── README.md
│       ├── package.json
│       └── src/{app,components,features,lib,styles,tests}/
├── services/
│   └── api/
│       ├── README.md
│       ├── main.py
│       ├── app/
│       ├── api/{deps.py,v1/{router.py,routes/}}
│       ├── core/{config.py,errors.py,logging.py,security/}
│       ├── contracts/
│       ├── db/{base.py,session.py,migrations/}
│       ├── modules/{identity,users,brain,models,memory,knowledge,agent,language,media,presentations,newsroom,education,cybersecurity,providers,billing,administration,audit}/
│       ├── tasks/
│       └── tests/
├── docs/{architecture,api,operations,status}/
└── infra/{docker,scripts}/
```

The implementation currently uses several flat `services/api` files and `services/api/modules`; preserve these working paths. Do not migrate or duplicate them merely to match the target tree. Existing interface documents live in `docs/interfaces/`.

## Module ownership and boundaries

Each module owns its domain logic, validation, persistence models/migrations, and tests. It may use another module’s published service contract, but must not access another module’s private implementation or write to its tables.

| Module/capability | Responsibility |
|---|---|
| `identity`, `users` | Authentication/account lifecycle, roles, profiles; shared security enforces authorization policy. |
| `brain`, `models` | Intent, orchestration, confidence, response generation, model registry/routing, local/self-hosted runtime interfaces; provider fallback optional. |
| `memory`, `knowledge` | User/conversation memory, retrieval, ingestion, source verification, user-isolated knowledge. |
| `agent` | Planning, tool registry/execution, browser/computer interfaces, observation/verification, backend permission and approval checks. |
| `language` | Language/dialect detection, multilingual output, translation, code-switching, style, and voice/vision/remote-control interfaces. |
| `media` | Creative image/video/document workflows, processing, asset management; prefer local/self-hosted processing where practical. |
| `presentations` | Scripts, scenes, storyboards, assets, timelines, audio sync, subtitles, preview/export for specified modes. |
| Presenter capability | Avatar, lip-sync, facial/body/gesture animation, TTS, speech alignment, voice configuration, virtual studio. Placement is open; contract is distinct. |
| `newsroom` | Aggregation, analysis, verification, scripts, narration, ticker, subtitles, archives. Never fabricate real-world events or represent generated footage as authentic. |
| `education` | Lesson generation, teaching presentations, virtual teacher/classroom, visual explanations, quizzes, assessment. |
| `cybersecurity` | Authorized assessment, network/web analysis, configuration audits, forensics, safe labs, remediation; validate authorization and constrain targets. |
| `providers` | Optional provider configuration and credential references, health/usage/cost, routing/fallback, search/browser adapters. |
| `billing` | Plans, subscriptions, metering, quotas, payment verification, history, webhooks, renewals/refunds. No payment provider selected. |
| `administration` | Backend-protected operations for users, roles, models, knowledge, requests, reports, rules, service controls, analytics, audit, emergency controls. |
| `core/security`, `audit` | Shared authentication/authorization, approvals, restricted actions, audit, secret-handling interfaces, emergency stop. |
| `tasks` | Shared background-task submission/status interface; runner undecided. |
| `apps/web` | UI that calls documented backend APIs; never authoritative for permissions, billing, or user isolation. |

## Shared implementation rules

- Expose domain operations through typed service interfaces. HTTP handlers remain thin: validate/parse, acquire authenticated context, invoke services, serialize, and map errors.
- User-scoped operations receive explicit server-derived caller context. Client-supplied IDs do not prove ownership.
- Modules use their own persistence; cross-module access goes through published contracts. Validate at API boundaries and again across internal/background trust boundaries.
- Long-running/external work needs explicit acceptance, observable status, actionable failure and timeout behavior. Do not claim durability before selecting and validating a runner.
- PostgreSQL user-owned records require enforceable ownership relationships and authenticated user-scoped queries. Cross-user access must be tested. RLS validation remains outstanding; whether to use RLS in addition to service checks remains an open decision.
- Audit security-sensitive and administrative operations. Never log credentials, tokens, private prompts, or unnecessary personal data.
- Use stable documented enum values; money is currency plus integer minor units, never floating point.
- Python modules/functions and database identifiers use `snake_case`; Python types use `PascalCase`; API paths are lowercase.
- Secrets come from environment/configuration or an approved secret interface, never source control or browser code.
- Sensitive agent actions require backend authorization and any required approval; UI confirmation is not authorization. Use shared security/audit rather than competing engines.

## Open decisions

1. Frontend framework details, package manager, build tool beyond reported React/TypeScript.
2. ORM/query and migration tooling.
3. Authentication method, session/token format, account recovery.
4. PostgreSQL RLS in addition to service-layer ownership checks.
5. Embedding/vector search and acceptable models.
6. First local/self-hosted model runtime, formats, hardware requirements.
7. Background-task runner and delivery guarantees; current agent history is process-local.
8. WebSocket auth, reconnect, delivery semantics.
9. Presenter placement and media/artifact storage.
10. Payment provider, if any; no integration selected.
11. Approved external adapters and secret storage.
12. Deployment, monitoring, backup/restore, retention, recovery objectives beyond local Compose.
13. The 20th engineering role: the specification names 19 module-owner roles; Chief Architect coordinates the remaining seat without inventing a product module.

## Governance

The Chief Architect coordinates boundaries and approves shared-contract or module-boundary changes. Owners report status, dependencies, actual test execution/results, blockers, and proposed contract changes. Preserve working code and follow approved phase ordering.

## References

- [Dependency map](DEPENDENCY_MAP.md)
- [Phase plan](PHASE_PLAN.md)
- [Agent assignments](AGENT_ASSIGNMENTS.md)
- [Shared protocols](interfaces/SHARED_PROTOCOLS.md)
- [Current implementation status](STATUS.md)
- [Agent contract](interfaces/AGENT.md), [Brain contract](interfaces/BRAIN.md), [Memory contract](interfaces/MEMORY.md)
- [Local container guidance](../infra/docker/README.md)

All interface documents describe the existing documented contracts and must be reviewed before extension; do not define conflicting parallel contracts.