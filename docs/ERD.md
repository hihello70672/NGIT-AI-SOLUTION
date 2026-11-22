# NGIT PostgreSQL ERD

Application tables are isolated in the `ngit` schema. UUID identifiers and `timestamptz` timestamps are used throughout. Composite tenant keys ensure child records cannot reference another user's parent records.

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
  MEDIA_ASSETS o|--o{ VIDEOS : source
  USERS ||--o{ VIDEOS : owns
  USERS ||--o{ PRESENTATIONS : owns
  PRESENTATIONS ||--o{ PRESENTATION_SLIDES : contains
  USERS ||--o{ PRESENTATION_SLIDES : owns
  USERS o|--o{ AUDIT_LOGS : acts
```

`provider_configs` contains optional global provider metadata and opaque credential references only; no secret material is stored and external AI is not required. `schema_migrations` records applied migration versions. Role assignments, audit logs, provider metadata, billing reference plans, and schema bookkeeping are privileged service data, not user-readable data.

Forced RLS is enabled for user-owned application data. Authenticated server code must set transaction-local `ngit.user_id` from trusted caller context; never derive it from client-provided identity. The application DB role must be non-owner, non-superuser, and without `BYPASSRLS`. Composite foreign keys preserve tenant ownership for conversation messages, media/video source links and presentation slides. Indexes support owner-scoped recent lists, chronological message retrieval, joins, enabled-provider lookup, and audit timelines.

Apply `services/api/db/migrations/*.sql` in lexical order and run disposable-database assertions as documented in `services/api/db/tests/README.md`. Checked-in assertions are not evidence that migrations or tests have run.
