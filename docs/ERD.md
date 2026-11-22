# NGIT PostgreSQL ERD

All domain objects reside in the `ngit` schema. IDs are UUIDs; time fields are `timestamptz`. The composite keys on tenant-owned parents enforce same-owner relationships in addition to row-level security (RLS).

```mermaid
erDiagram
 USERS ||--o{ USER_ROLES : assigned
 ROLES ||--o{ USER_ROLES : grants
 USERS ||--o{ CONVERSATIONS : owns
 CONVERSATIONS ||--o{ MESSAGES : contains
 USERS ||--o{ MESSAGES : owns
 USERS ||--o{ MEMORY_RECORDS : owns
 CONVERSATIONS o|--o{ MEMORY_RECORDS : scopes
 USERS ||--o{ SUBSCRIPTIONS : has
 BILLING_PLANS ||--o{ SUBSCRIPTIONS : defines
 SUBSCRIPTIONS o|--o{ USAGE_RECORDS : measures
 USERS ||--o{ USAGE_RECORDS : accrues
 USERS ||--o{ MEDIA_ASSETS : owns
 MEDIA_ASSETS o|--o{ VIDEOS : source
 USERS ||--o{ VIDEOS : owns
 USERS ||--o{ PRESENTATIONS : owns
 PRESENTATIONS ||--o{ PRESENTATION_SLIDES : contains
 USERS ||--o{ PRESENTATION_SLIDES : owns
 USERS o|--o{ AUDIT_LOGS : acts
}
```

`provider_configs` holds optional provider metadata and an opaque secret-manager reference only; it does not store credentials. Billing uses currency plus integer minor units. Media, video, presentation, conversation, memory, billing and usage rows are owner-scoped; the audit log is not exposed through ordinary user RLS. `roles`, `user_roles`, billing plans, provider configuration and audit administration require privileged service access policies outside the end-user policy.

## Isolation and migration

`messages` and `memory_records` reference conversation by `(user_id, conversation_id)`; slides reference presentations by `(user_id, presentation_id)`; optional video assets and usage subscriptions also use same-user composite foreign keys. This prevents cross-tenant links independently of application checks. RLS is enabled and forced on user-owned tables. Set `ngit.user_id` transaction-locally using authenticated server context; use a non-owner, non-superuser application DB role. No client-supplied owner context is trusted.

Apply migrations `0001_initial_schema.sql`, then `0002_seed_reference_data.sql` on a fresh PostgreSQL 16+ database. Schema changes are tracked in `schema_migrations`. See [`services/api/db/README.md`](../services/api/db/README.md) and [`services/api/db/tests/README.md`](../services/api/db/tests/README.md) for test execution. Tests require a disposable PostgreSQL database and have not been claimed as executed here.

Indexes follow tenant list/order and parent lookup paths. JSON metadata is not indexed without demonstrated query requirements.
