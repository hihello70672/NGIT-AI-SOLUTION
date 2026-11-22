# Module dependency map

This map records approved service-contract dependencies, not proof that every target integration is implemented or validated. Arrows mean consumers use published capabilities; they do not authorize private imports or writes to another module's tables. See [STATUS.md](STATUS.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

```text
Foundation: API configuration, PostgreSQL/migrations, shared protocols
  ├── Identity and users
  │     └── Core security, policy, approvals, audit, emergency stop
  │            ├── Administration and rules
  │            ├── Billing
  │            ├── Personal Agent -> registered tool/browser/computer adapters
  │            └── Authorized Cybersecurity -> scope and safe-lab controls
  ├── NGIT Brain -> local/self-hosted runtime and model registry
  │     ├── Memory and Knowledge (published retrieval/ingestion contracts)
  │     ├── Optional provider/integration routing (optional only)
  │     └── Language intelligence
  │            └── Voice, vision, remote-control interfaces
  ├── Creative/media capabilities
  │     └── Video presentation orchestration
  │            ├── Presenter capability
  │            └── Language/voice and reusable media capabilities
  ├── Newsroom -> verified sources + language + media/presentation
  ├── Education -> Brain + language + media/presentation
  └── Web application -> documented backend APIs only
```

## Dependency constraints

1. Authenticated API boundaries derive caller context from verified server-side auth. Client-supplied IDs, roles, permissions or approvals do not establish identity or authority.
2. Identity/security owns authorization, policy, approvals, audit and emergency controls. Feature modules cannot create competing policy engines or bypass backend checks.
3. Brain consumes runtime/model contracts and may use Memory or optional provider capabilities. Memory does not own model routing. External AI is never mandatory for core operation.
4. Memory and knowledge are owner-scoped and consumed through published contracts. Retrieval candidates are restricted to the authenticated user's corpus and requested types.
5. Agent execution depends on policy, approval, registered tools and task contracts. Browser/computer adapters are not authorization authorities. Sensitive effects require server-side checks immediately before execution.
6. Language is reusable across Brain, media, newsroom, education and presentations; consumers do not duplicate translation/preferences services.
7. Media/presenter capabilities are reusable. Video presentation composes them; newsroom and education consume those contracts instead of duplicating renderers.
8. Administration, billing and provider integrations have distinct ownership. Credentials/payment secrets remain server-side and never enter browser code.
9. PostgreSQL is authoritative for persisted state. Modules own tables and migrations. Verify ownership/RLS as a non-owner, non-superuser role without `BYPASSRLS`; database RLS does not replace service authorization.
10. Task/event/WebSocket/storage/provider implementation specifics remain open until an approved contract settles them. Do not imply a broker, durable multi-worker execution, vector store, payment integration or production topology without evidence.

See [shared protocols](interfaces/SHARED_PROTOCOLS.md) and [architecture open decisions](ARCHITECTURE.md#6-decisions). Changes to shared dependencies or module boundaries require Chief Architect review.
