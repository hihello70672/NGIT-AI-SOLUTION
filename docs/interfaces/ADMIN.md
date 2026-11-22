# Administration interface

The Administration module owns admin operations and must use the existing server-authenticated caller context, shared `PolicyEngine`, restricted-action/approval controls, transactional DB identity and audit contracts. Never accept identity or role authority from request bodies. See [shared protocols](SHARED_PROTOCOLS.md), [status](../STATUS.md) and current implementation under `services/api/modules/admin/`.

Administrative capabilities include user/role/model/provider/knowledge listings, learning/report views, rules, service-control intent, analytics, audit and emergency stop/reset. Mutations and restricted actions require backend authorization and exact-resource approval where policy requires it. Unknown actions deny by default. Record security-relevant outcomes in audit.

The current implementation/status records migration-backed admin rule/service-control desired state; deployment-specific executors are outside this module. Learning requests/reports currently have no dedicated tables and may reuse audit records. Approval, stop-state and permission engine state are process-local; use one API worker until shared persistence is implemented and validated. Apply ordered migrations before enabling endpoints and validate DB grants/RLS for the deployed roles. Existing tests are source coverage, not evidence of execution.

Any new admin operation must specify owner, public typed contract, permissions/approval, persistence owner, safe failure behavior and tests before integration. Do not invent deployment service executors or parallel policy engines.
