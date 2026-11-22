# Module dependency map

This map describes approved service-contract dependencies, not proof that every module or integration is implemented. See [repository status](STATUS.md). An arrow means a consumer may call a published contract; it does not authorize private imports or direct writes to another module’s tables.

```text
apps/web
  └── documented Backend API
       ├── Identity / Users ──────> Core Security ──────> Audit
       ├── Administration ────────> Identity, Security, Audit
       ├── Billing ───────────────> Identity, Audit
       ├── Brain ─────────────────> Models / Runtime
       │    ├── optional Providers
       │    └── Memory / Knowledge (published retrieval contract)
       ├── Agent ─────────────────> Security, Approvals, Audit, Tasks
       │    ├── Browser / computer tool adapters (permission checked)
       │    └── Brain (when reasoning is required)
       ├── Language ──────────────> Brain / Media / Presentations contracts
       ├── Media / Creative AI ───> Models / optional Providers
       ├── Presentations ─────────> Media assets, Presenter capability
       ├── Newsroom ──────────────> approved ingestion, Language, Presentations
       ├── Education ─────────────> Brain, Language, Presentations
       └── Cybersecurity ─────────> Security, Approvals, Audit, Tasks

Shared infrastructure: PostgreSQL (system of record), shared protocols,
configuration, and task interface. Concrete runners/storage remain decisions.
```

## Dependency rules

1. The authenticated API boundary derives caller context. Each protected service enforces permissions and ownership; client-supplied IDs do not establish identity.
2. Core security and audit are shared infrastructure. Feature modules must not create competing authorization/approval engines or bypass backend checks.
3. Brain uses model/runtime contracts and may consume memory or optional provider contracts. Memory does not own model routing. External providers are never mandatory for core operation.
4. Agent depends on policy, approvals, registered tools, and task contracts. Browser/computer adapters are tools, not authorization authorities; sensitive execution cannot bypass security.
5. Language is reusable across Brain, media, newsroom, education, and presentations; consumers should not duplicate language preference and translation services.
6. Media and presenter capabilities are reusable. Presentations orchestrate those contracts; newsroom and education consume them rather than owning duplicate renderers.
7. Provider configuration, credentials, billing, and administration have separate ownership. Secrets and payment credentials never reach browser code.
8. PostgreSQL remains authoritative. Cross-module access respects ownership and user isolation; test RLS with a non-owner, non-superuser application role.
9. Tasks, WebSockets, and external adapters use shared contracts. Runner choice, durability, delivery, retries, cancellation, and streaming semantics are not implied by this diagram.
10. No distributed services, broker, vector persistence, payment integration, or other external dependency is introduced without approved need.

See [shared protocol conventions](interfaces/SHARED_PROTOCOLS.md) and open decisions in [architecture](ARCHITECTURE.md#decisions-still-open). Changes to shared dependencies or boundaries require Chief Architect approval.
