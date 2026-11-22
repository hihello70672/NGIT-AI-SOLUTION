# Administration module

`create_admin_router` exposes `/admin` endpoints under the configured API prefix. Permission checks use registered `PolicyEngine` actions and authenticated `AuthContext`; request payloads cannot specify actor identity or roles. Restricted user and service mutations use exact-resource approvals through `RestrictedActionManager`.

| Endpoint | Permission action | Purpose |
| --- | --- | --- |
| `GET /admin/{users,roles,models,knowledge,learning-requests,reports,rules,audit-logs}` | Resource-specific `admin.*.read` | Bounded read-only listings from existing tables |
| `PATCH /admin/users/{id}` | `admin.users.manage` | Update account status and/or role assignments |
| `POST /admin/rules` | `admin.rules.manage` | Add validated permission actions |
| `PUT /admin/services/{name}` | `admin.services.control` | Persist desired service state |
| `GET /admin/analytics/overview` | `admin.analytics.read` | Aggregate user status and enabled provider totals |
| `GET /admin/audit/events` | `admin.audit.read` | Read persistent audit records |
| `POST /admin/emergency` | `admin.emergency.engage` / `admin.emergency.reset` | Engage or reset security engine stop state |

Migration `0006_admin_control.sql` creates RLS-protected tables for admin rules and service-control state. Existing user, role, provider, memory, and audit records are reused. Learning and report lists currently select matching/general audit data because the schema has no separate learning-request/report entities. Service-control rows are persisted intent, not a deployment executor. The permission engine dynamically receives a new rule only after durable insertion succeeds; rules require restart/reload to populate process-local engines in other workers. Approval, stop and audit engines remain process-local, so run one API worker until approved shared persistence is implemented.
