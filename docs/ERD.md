# NGIT PostgreSQL ERD

All domain objects live in the `ngit` schema. IDs use UUIDs and timestamps use `timestamptz`. Composite foreign keys enforce that user-owned children point only to parents owned by the same user.

```mermaid
erDiagram
 USERS ||--o{ USER_ROLES : assigned
 ROLES ||--o{ USER_ROLES : grants
 USERS ||--o{ CONVERSATIONS : owns
 CONVERSATIONS ||--o{ MESSAGES : contains
 USERS ||--o{ MEMORY_RECORDS : owns
 CONVERSATIONS o|--o{ MEMORY_RECORDS : scopes
 USERS ||--o{ SUBSCRIPTIONS : has
 BILLING_PLANS ||--o{ SUBSCRIPTIONS : defines
 SUBSCRIPTIONS o|--o{ USAGE_RECORDS : measures
 USERS ||--o{ MEDIA_ASSETS : owns
 MEDIA_ASSETS o|--o{ VIDEOS : source
 USERS ||--o{ VIDEOS : owns
 USERS ||--o{ PRESENTATIONS : owns
 PRESENTATIONS ||--o{ PRESENTATION_SLIDES : contains
 USERS o|--o{ AUDIT_LOGS : acts
}
```

`provider_configs` contains optional provider metadata and an opaque secret-manager reference, never credentials. Billing stores currency and integer minor units. Conversations, messages, memory, subscriptions, usage, media, video, presentation, slide, user-role grant rows are tenant-scoped. Audit records are privileged service data and have no end-user RLS policy.

RLS is enabled and forced on user-owned tables. Each request must set `ngit.user_id` transaction-locally from authenticated server context, never client input. The API DB role must not be superuser or table owner. Composite FKs independently prevent cross-user links.

Apply ordered `services/api/db/migrations/*.sql` on a fresh PostgreSQL 16+ database. See database READMEs for disposable test instructions. Test execution is not asserted unless run in the target environment.

Indexes support tenant-scoped chronological lists, relationship lookups, enabled provider lookup, role reverse lookup, and audit timelines. JSON metadata is not indexed absent query evidence.
