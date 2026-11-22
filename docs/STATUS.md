# Project status — Phases 1–6

Status is based on committed files on `main`. Test sources do not establish that tests passed; runtime checks are reported only when actually executed.

## Phase 6 — Administration, rules, service control

**Implemented:** `services/api/modules/admin/` provides permission-gated REST and service operations for users and roles, configured model-provider listings, knowledge/memory listings, learning-request and audit/report views, rule management, service-control intent, aggregate analytics, audit events, and emergency controls. The API registers explicit admin-only actions in the existing permission engine and binds endpoint identity to authenticated `AuthContext`. User/service mutations pass through the existing restricted-action manager. Migration `0006_admin_control.sql` adds durable rule and service-control state with RLS. Administrative regression-test sources cover denial, identity binding, approval scopes, persistence calls, emergency controls and route availability.

**Caveats:** New administrative tests have not been run. Service-control rows record desired state but do not execute deployment-specific service operations. Learning-request and report listings reuse audit records because no separate learning/report domain persistence exists in the schema. The existing approval, emergency and audit engine state is process-local; the deployment must remain single-worker until shared durable state is implemented. Migration execution, database grants/RLS validation, integration tests and runtime checks remain outstanding.

## Verification record

No tests, builds, migrations, Compose lifecycle, or runtime checks were executed for this Phase 6 update. Checked-in test sources are not evidence of passing tests.
