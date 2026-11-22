# NGIT PostgreSQL ERD

Application tables live in the isolated `ngit` schema. UUID primary keys and `timestamptz` timestamps are used throughout. Composite tenant keys preserve ownership across dependent rows.

```mermaid
erDiagram
  USERS ||--o{ USER_ROLES : assigned
  ROLES ||--o{ USER_ROLES : grants
  USERS ||--o{ CONVERSATIONS : owns
  CONVERSATIONS ||--o{ MESSAGES : contains
  USERS ||--o{ MESSAGES : owns
  USERS ||--o{ MEMORIES : owns
  USERS ||--o| BILLING_ACCOUNTS : has
  USERS ||--o{ SUBSCRIPTIONS : subscribes
  BILLING_PLANS ||--o{ SUBSCRIPTIONS : defines
  SUBSCRIPTIONS ||--o{ USAGE_RECORDS : measures
  USERS ||--o{ USAGE_RECORDS : accrues
  USERS ||--o{ MEDIA_ASSETS : owns
  MEDIA_ASSETS ||--o{ VIDEOS : source
  USERS ||--o{ VIDEOS : owns
  USERS ||--o{ PRESENTATIONS : owns
  PRESENTATIONS ||--o{ PRESENTATION_SLIDES : contains
  USERS ||--o{ PRESENTATION_SLIDES : owns
  USERS o|--o{ AUDIT_LOGS : acts
```

`provider_configs` contains optional global provider metadata and opaque credential references only; it never stores secret material. `schema_migrations` records applied versions. Role assignments, audit logs, provider metadata, billing reference plans, and schema bookkeeping are privileged service data, not user-readable data.

Forced RLS is enabled for user-owned application rows. Trusted server code sets transaction-local `ngit.user_id` from authenticated caller context; it must never be derived from client-provided identity. The application role must be non-owner, non-superuser and lack `BYPASSRLS`. Composite foreign keys ensure child records cannot refer across tenants. Indexes support owner-scoped recent lists, chronological message retrieval, joins, enabled-provider lookup and audit timelines.

Apply `services/api/db/migrations/*.sql` in lexical order and run disposable-database assertions documented in `services/api/db/tests/README.md`. Checked-in assertions are not evidence that migrations or tests have run.
