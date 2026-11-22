# Module dependency map

This map describes approved service-contract dependencies, not a claim that every module or integration is implemented. Consult [`STATUS.md`](STATUS.md) for repository evidence. Dependencies do not permit importing another module’s private implementation or writing to its tables.

```text
core configuration, contracts, database, shared security/audit
 ├── identity, users
 │    └── authenticated caller context for downstream user-scoped operations
 ├── tasks (shared submission/status/failure interface; runner undecided)
 └── domain modules
      ├── brain, models
      │    ├── memory, knowledge (retrieval/ingestion contracts)
      │    ├── language (language/style capabilities)
      │    └── providers (optional routing/fallback only)
      ├── agent
      │    ├── shared security/approval and audit
      │    ├── tasks (when asynchronous execution is adopted)
      │    └── registered tools/adapters (browser, filesystem, computer)
      ├── language
      │    └── voice/vision/remote-control interfaces (placement open)
      ├── media
      │    └── presentations
      │         └── presenter capability (distinct contract; placement open)
      ├── newsroom ──> media/presentations as needed
      ├── education ──> brain/language/presentations as needed
      ├── cybersecurity ──> shared security, authorization, audit
      ├── billing ──> identity/users, shared security, audit
      ├── providers ──> shared secret/config interfaces; optional adapters
      └── administration ──> identity/users, models, knowledge, billing,
                             service controls, shared security, audit

apps/web ──> documented backend API contracts only
```

## Dependency rules

1. The frontend consumes public API contracts only; it never connects to PostgreSQL or holds provider credentials.
2. Identity establishes caller context but does not replace per-module owner checks.
3. Shared security and audit are infrastructure. Domain modules must not implement competing authorization or approval engines; admin UI cannot bypass backend policy.
4. Brain and core capabilities must retain local/self-hosted operation. Provider, search, browser, and payment adapters are optional and enabled only through approved configuration.
5. Media, presentations, and Presenter coordinate through contracts; final placement/storage choices remain open.
6. Module persistence is private. Use published typed services for cross-module operations and keep user ownership enforced at every read/write.
7. Do not add distributed services or a broker without an approved need. Agree on shared interfaces before downstream feature work and preserve the phase order.

## Governance

The Chief Architect approves changes to shared contracts or module boundaries. See [shared protocols](interfaces/SHARED_PROTOCOLS.md) and [architecture open decisions](ARCHITECTURE.md#open-decisions).