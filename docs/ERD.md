# NGIT PostgreSQL ERD

All application tables live in the isolated `ngit` schema. UUID identifiers and `timestamptz` timestamps are used. Composite owner foreign keys ensure a user-owned child cannot point to a parent owned by a different user.

```mermaid
erDiagram
 USERS ||--o{ USER_ROLES : assigned
 ROLES ||--o{ USER_ROLES : grants
 USERS ||--o{ CONVERSATIONS : owns
 CONVERSATIONS ||--o{ MESSAGES : contains
 USERS ||--o{ MESSAGES : owns
 USERS ||--o{ MEMORIES : owns
 USERS ||--|| BILLING_ACCOUNTS : has
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
}
```

`provider_configs` is optional global provider metadata; it stores opaque `credential_ref` only, never credentials. Provider rows are disabled by default, so local/self-hosted operation does not depend on external AI. Billing uses currency plus integer minor units. Audit logs are privileged service data and have no end-user RLS policy.

RLS is enabled and forced on user-scoped records. Trusted API code must set `ngit.user_id` transaction-locally from authenticated context; the app role must not be superuser or table owner. Composite FKs constrain cross-owner message, video-source and slide relationships. Indexes support tenant-scoped recent lists, joins, enabled provider lookup, and audit timelines. Check migrations for exact columns and policies; schema runtime verification remains pending.

Apply ordered SQL files under `services/api/db/migrations/` on fresh PostgreSQL 16+. Run database checks per `services/api/db/tests/README.md`; no test execution is claimed here.
