# Phase plan

## Baseline

At approval, the repository contained one title-only `README.md`; there were no application folders, docs, phase status files, releases, or tags. No phase implementation or completion was evidenced. The lists below are planned deliverables, not completion claims.

## Build step 1 — Phases 1–2

| Phase | Scope and deliverables | Baseline evidence |
|---|---|---|
| **1. Architecture, repository, database, shared protocols** | Approved module boundaries/dependencies; naming and API/event/error conventions; populated docs; FastAPI startup skeleton; PostgreSQL config/connection; initial migration workflow; Docker Compose startup; health checks; backend/web test scaffolding; documented open decisions. | Only title-only README; no application, DB, Compose, docs, or status evidence. |
| **2. Authentication, backend, security, user management** | Authentication and lifecycle; backend authorization/user context; role/permission foundations; security audit; consistent validation/error mapping; user isolation tests; protected API examples and frontend auth states. | No implementation/status evidence. |

## Build step 2 — Phases 3–4

| Phase | Scope and deliverables | Baseline evidence |
|---|---|---|
| **3. Brain, model runtime, memory, knowledge** | Intent/orchestration contracts; model registry/routing; local/self-hosted runtime interface; confidence/response flow; user/conversation memory; ingestion/retrieval; source verification; isolation/runtime tests. Provider fallback optional. | No implementation/status evidence. |
| **4. Personal Agent, tools, browser and computer interfaces** | Planner; tool registry/execution boundary; background task/status; browser/computer interfaces; observation/verification; permission/approval checks; controlled safe tests. | No implementation/status evidence. |

## Build step 3 — Phases 5–7

| Phase | Scope and deliverables | Baseline evidence |
|---|---|---|
| **5. Multilingual, voice, vision, remote control** | Language/dialect, multilingual/code-switched responses, translation/style preferences; voice/vision/remote-control contracts; capability/error/loading states; language and permission tests. | No implementation/status evidence. |
| **6. Admin, rules, service control, billing** | Backend-enforced admin operations; user/role/model/knowledge/rule controls; service controls, analytics/audits; quotas/metering; payment interfaces only per approved choices; provider-specific behavior only after selection. | No implementation/status evidence. |
| **7. Optional API provider management and browsing** | Optional provider registry and secure credential references; health/connection, usage/cost, routing/fallback; search/browser adapters; prove core works without external AI providers. | No implementation/status evidence. |

## Build step 4 — Phases 8–9

| Phase | Scope and deliverables | Baseline evidence |
|---|---|---|
| **8. Creative Studio** | Image/video/document workflows; media assets and rendering interfaces; local/self-hosted options where practical; task/asset/error states and tests. | No implementation/status evidence. |
| **9. Content-to-Video, presenters, lip-sync, subtitles** | Script-to-scenes/storyboards; asset/timeline, audio sync, subtitles, preview/export; presenter modes; avatar/lip-sync, TTS/alignment, voice config, virtual studio. | No implementation/status evidence. |

## Build step 5 — Phases 10–11

| Phase | Scope and deliverables | Baseline evidence |
|---|---|---|
| **10. Newsroom, Teaching, Storytelling** | News aggregation/verification and content workflows; prevent fabricated news and misleading generated footage; lesson, teacher/classroom, visual explanation, quiz/assessment workflows; presentation integration. | No implementation/status evidence. |
| **11. Cybersecurity Center** | Authorized intake and target-scope validation; safe labs; network/web/config audits; forensics/remediation; audit and rejection tests for unauthorized targets. | No implementation/status evidence. |

## Build step 6 — Phase 12

| Phase | Scope and deliverables | Baseline evidence |
|---|---|---|
| **12. Integration, QA, documentation, local release** | End-to-end module/API/auth/isolation/billing/service-control/media/language/error/security tests; recorded failures and verified fixes; user/admin/operations docs; local install, backup/recovery/config; CI/release checks; build and verify downloadable ZIP before describing a release. | No tests, docs, release, tag, ZIP, or phase status evidence. |

## Integration sequence

1. Coordinate and review paths, contracts, naming, ownership, and dependencies before parallel work; architect approval required for shared contract changes.
2. Phase 1 establishes documented foundations, startup, migrations, Compose, and tests; make early tooling decisions explicit.
3. Phase 2 delivers identity, authorization, user management, audit, and error behavior before user-owned feature data.
4. Phases 3–4 integrate Brain/runtime/memory/knowledge and agent tools with user context and permission/approval contracts.
5. Phases 5–7 add language interfaces, admin/rules/service control/billing, and optional provider/browsing adapters.
6. Phases 8–9 compose shared media/language services; agree task, asset, subtitle, timeline, export contracts first.
7. Phases 10–11 build on identity, safety, audit, and content; enforce newsroom verification and authorized cybersecurity targets in backend.
8. Phase 12 runs integration, UI, security, isolation, and workflow tests; verify fixes, local install/recovery docs, and ZIP contents/usability. Claim no test/release until checked.
9. Throughout, owners report status, dependencies, tests actually run, blockers, and contract changes. Preserve working code and document approved deviations.
