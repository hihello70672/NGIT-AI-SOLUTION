# NGIT PostgreSQL ERD

All application domain tables reside in isolated schema `ngit`. Identifiers are UUID; timestamps use `timestamptz`. Composite foreign keys include `user_id` where a child must belong to the same tenant as its parent.

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
```

`provider_configs` contains optional global provider metadata and opaque credential references only; it is disabled by default and never requires an external AI API. `schema_migrations` tracks applied SQL. `audit_logs` and provider configuration are privileged service data, not tenant-facing RLS records.

RLS is enabled and forced on user-scoped tables. Trusted API transactions set `ngit.user_id` from authenticated server context. Use a non-owner, non-superuser role without `BYPASSRLS`; table owners and superusers can bypass policy behavior. Composite owner FKs additionally prevent cross-user message/conversation, video/source-asset and slide/presentation links. Indexes serve owner-scoped recent lists, chronological message fetches, joins and audit timelines.

Apply migrations and run disposable-database checks per `services/api/db/README.md`. The presence of SQL checks does not mean they have executed.
