# Module dependency map

This map describes planned service dependencies, not implemented integrations.

```text
apps/web
  └── REST / WebSocket contracts
       └── FastAPI API layer
            ├── core/security ───── identity, users, administration
            ├── audit
            ├── tasks
            └── domain services
                 ├── brain ─────── models, memory, knowledge, language
                 ├── agent ─────── core/security, audit, providers (optional),
                 │                  browser/computer tool interfaces
                 ├── language ──── brain, optional voice/vision providers
                 ├── media ─────── providers (optional)
                 ├── presentations ─ media, language, presenter capability
                 ├── newsroom ──── providers (optional), language, presentations
                 ├── education ─── brain, language, presentations
                 ├── cybersecurity core/security, audit, agent tool interfaces
                 ├── billing ───── users, provider/payment adapter (only if selected)
                 └── administration users, models, knowledge, billing, audit
```

## Dependency rules

1. `apps/web` uses public API contracts only; it never connects to PostgreSQL or provider credentials.
2. Security and audit are shared infrastructure. Domain services use them; administrative UI paths cannot bypass backend enforcement.
3. `brain` works against a local/self-hosted model interface and does not require a third-party AI API.
4. Provider, search, browser, and payment integrations are optional adapters, not core-module dependencies.
5. Media, presentations, news, and education compose services through contracts rather than duplicating rendering, language, or asset-management logic.
6. Persistence ownership follows modules. Shared identity references are allowed; domain data access remains owner-controlled.
7. Preserve phase ordering and establish shared dependencies/contracts before dependent feature work.

## Contract governance

Modules expose typed service interfaces and may depend only on published contracts. They must not import private functions/models or write directly to another module's tables. The Chief Architect approves shared contract or boundary changes. Concrete interfaces and protocol conventions are documented in [Shared protocols](interfaces/SHARED_PROTOCOLS.md).
