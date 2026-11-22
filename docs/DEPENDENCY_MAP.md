# Module dependency map

This map describes approved service-contract dependencies, not proof that every module or integration is implemented. Consult [`STATUS.md`](STATUS.md) for repository evidence. An arrow means a module may call a published contract; it does not authorize access to private implementation or another module's tables.

```text
identity/users ───────────────► core/security
core/security ────────────────► audit
all user-scoped modules ──────► server-derived caller context
all long-running modules ────► tasks (after the shared contract is established)

brain ────────────────────────► models
brain ────────────────────────► memory/knowledge (approved retrieval contracts)
models ───────────────────────► providers (optional adapter)
brain ────────────────────────► providers (optional routing/fallback)

agent ────────────────────────► core/security, audit
agent ────────────────────────► permission-checked browser/computer tool interfaces

language ────────────────────► brain/media/presentations through contracts
media ────────────────────────► models/providers through approved interfaces
presentations ───────────────► media assets
presentations ───────────────► presenter capability (placement open; contract distinct)

newsroom ─────────────────────► approved ingestion/verification, language, presentations
education ────────────────────► brain, language, presentations
cybersecurity ────────────────► core/security, audit, task interfaces

billing ──────────────────────► identity/users, audit
administration ───────────────► identity/users, core/security, audit
apps/web ─────────────────────► documented backend API contracts only
```

## Dependency rules

1. `apps/web` calls documented public APIs only. It does not connect to PostgreSQL, hold provider credentials, or enforce authorization, billing, or user isolation.
2. Identity establishes authenticated caller context; each user-scoped module still enforces ownership for its own reads and writes. Client-supplied IDs are not ownership evidence.
3. Shared security and audit are infrastructure contracts. Domain modules must not create competing authorization or approval engines, and administrative UI cannot bypass backend policy.
4. Brain retains local/self-hosted operation. Provider, search, browser, and payment adapters are optional and enabled only through approved configuration; no external AI API is a core dependency.
5. Media, presentations, and presenter integrations use contracts. Presenter placement and artifact storage remain open decisions.
6. Module persistence is private. Cross-module operations use typed published services, not direct imports of private implementation or writes to another module's tables.
7. Do not add distributed services, a message broker, or an undocumented event bus without approved need. Establish shared task acceptance/status/failure semantics before dependent long-running work.
8. Preserve approved phase ordering and resolve cross-module contract changes through the Chief Architect.

See [shared protocols](interfaces/SHARED_PROTOCOLS.md) and [architecture open decisions](ARCHITECTURE.md#open-decisions).
