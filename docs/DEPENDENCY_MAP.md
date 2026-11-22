# Module dependency map

This map describes the approved service-contract dependency order, not proof that every target module or integration is implemented. See [repository status](STATUS.md). An arrow means a consumer may call a published capability; it does not authorize private imports or direct writes to another module’s tables.

```text
Foundation: configuration, PostgreSQL, migrations, shared protocols
    └── Identity and users
          ├── Core security, policy, approvals, audit, emergency stop
          │     ├── Administration
          │     ├── Personal Agent ──> registered tool/browser/computer adapters
          │     ├── Billing
          │     └── Cybersecurity (authorized scope and safe-lab controls)
          ├── NGIT Brain ──> local/self-hosted runtime and model registry
          │     ├── Memory and knowledge (published retrieval/ingestion contracts)
          │     └── Optional provider/integration routing
          └── Language intelligence
                 ├── Voice/vision/remote-control interfaces
                 └── Creative AI/media, presentations, presenters, education, newsroom
```

Additional shared capabilities: PostgreSQL is authoritative; each module owns its tables and migrations. Presentations orchestrate media and presenter contracts rather than owning their internals. Newsroom, education, and cybersecurity use applicable language/media capabilities through contracts and cannot bypass security/audit. Provider, payment, and media integrations remain optional and vendor-neutral until approved.

## Dependency rules

1. Authenticated API boundaries derive caller context server-side. User IDs, roles, permissions, or approvals supplied only by clients do not establish identity or authority.
2. Security and audit are shared infrastructure. Feature modules must not create competing policy engines or bypass backend checks.
3. Brain uses model/runtime contracts and may consume Memory or optional providers. Memory does not own model routing. External AI is never mandatory for core operation.
4. Memory and knowledge are owner-scoped and consumed through published contracts; vector candidates, if used, must be restricted to the authenticated user's corpus.
5. Agent execution depends on policy, approvals, registered tools, and task contracts. Browser/computer adapters are not authorization authorities. Sensitive side effects require backend authorization and any required approval immediately before execution.
6. Language intelligence is reusable across Brain, media, newsroom, education, and presentations; consumers should not duplicate translation/preferences services.
7. Media and presenter capabilities are reusable. Presentation orchestration composes their contracts; newsroom and education consume those capabilities rather than duplicate renderers.
8. Administration, billing, providers, and integrations have distinct ownership. Credentials and payment secrets remain server-side and must not reach browser code.
9. PostgreSQL owns persisted state. User isolation is enforced in service queries and tested; validate RLS under a non-owner, non-superuser application role.
10. Task, event, WebSocket, storage, and provider implementation details remain open unless an approved module contract settles them. No broker, distributed service, vector persistence, or payment integration is implied.

See [shared protocols](interfaces/SHARED_PROTOCOLS.md) and open decisions in [architecture](ARCHITECTURE.md#decisions-still-open). Changes to shared dependencies or boundaries require Chief Architect approval.
