# Module dependency map

This map describes approved service-contract dependencies, not proof that every target module or integration is implemented. Arrows represent published capability use; they do not authorize private imports or direct writes to another module's tables. See [repository status](STATUS.md).

```text
Foundation: API configuration, database conventions, shared protocols
  └── Identity and users
        └── Core security, policy, approvals, audit, emergency stop
              ├── Administration and rules
              ├── Personal Agent ──> registered tool/browser/computer adapters
              ├── Billing
              ├── Authorized Cybersecurity ──> scope and safe-lab controls
              ├── NGIT Brain ──> local/self-hosted runtime and model registry
              │     ├── Memory and knowledge (published retrieval/ingestion contracts)
              │     └── Optional provider/integration routing
              └── Language intelligence
                    ├── Voice, vision, remote-control interfaces
                    ├── Brain
                    └── Media/presentations, Newsroom, Education

Creative/media ──> Video presentation orchestration ──> Presenter capability
                                              ├──────> language/voice
                                              └──────> media capabilities
Newsroom ──> verified sources, language and media/presentation capabilities
Education ──> Brain, language and media/presentation capabilities
Cybersecurity ──> authorization, policy/approval, audit and safe-lab interfaces
Administration/Billing/Integrations ──> identity, security and audit
Web application ──> documented backend APIs only
```

## Dependency rules

1. Authenticated API boundaries derive caller context server-side. Client-supplied user IDs, roles, permissions, or approvals do not establish identity or authority.
2. Security and audit are shared capabilities. Feature modules must not create competing policy engines or bypass backend checks.
3. Brain consumes model/runtime contracts and may use Memory or optional providers. Memory does not own model routing. External AI is never mandatory for core operation.
4. Memory and knowledge are owner-scoped and consumed through published contracts. Any vector candidates must be restricted to the authenticated user's corpus.
5. Agent execution depends on policy, approvals, registered tools, and task contracts. Browser/computer adapters are not authorization authorities; sensitive side effects require backend authorization and any required approval immediately before execution.
6. Language intelligence is reusable across Brain, media, Newsroom, Education, and presentations; consumers should not duplicate translation or preference services.
7. Media and presenter capabilities are reusable. Presentation orchestration composes contracts; Newsroom and Education consume these capabilities rather than duplicating renderers.
8. Administration, billing, providers, and integrations have distinct ownership. Credentials and payment secrets remain server-side and never reach browser code.
9. PostgreSQL is authoritative for persisted state. Each module owns its tables and migrations; verify isolation and RLS using a non-owner, non-superuser application role without `BYPASSRLS`.
10. Task, event, WebSocket, storage, and provider implementation details remain open unless a reviewed module contract settles them. No broker, distributed service, vector persistence, or payment integration is implied.

See [shared protocols](interfaces/SHARED_PROTOCOLS.md) and [architecture open decisions](ARCHITECTURE.md#6-technical-decisions-and-open-questions). Changes to shared dependencies or boundaries require Chief Architect approval.
