# Administration interface

`services.api.modules.admin.api.create_admin_router(service, current_user)` builds the administrative REST router. The dependency must be the API's authenticated `AuthContext` provider; identity and roles are never accepted in request bodies or query parameters. `AdminService` uses the existing `PolicyEngine`, `RestrictedActionManager`, transaction-local database caller identity, and audit sink.

Routes cover resource listings (`users`, `roles`, `models`, `knowledge`, `learning-requests`, `reports`, `rules`, `audit-logs`), user status/role updates, rule creation, service control state, analytics, audit events, and emergency stop/reset. Writes to users/services require exact-scope approvals when policy says so. Rule changes are validated and stored in `admin_rules`; service state is stored in `service_controls`. External service executors and learning workflows are deliberately not implied by listing records. Audit and security primitives are process-local under current architecture; deploy one worker until shared durable stores are approved and implemented.

Every new permission action must be explicitly registered in `PolicyEngine`; unknown actions deny by default. Database row security remains an independent enforcement layer. Apply ordered migrations before use. Tests are in `services/api/tests/test_admin.py`.
