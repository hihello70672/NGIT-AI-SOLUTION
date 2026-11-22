# Phase agent assignments

Assignments identify accountable owners and collaborators; they are not evidence of completion. The approved specification names 19 specialist engineering roles. Chief Architect governance is required, but the missing twentieth engineering role has not been defined and must not be invented.

| Phase | Lead and contributing agents |
|---|---|
| **1. Foundation** | **Lead:** Database Architect for schema/migrations; Backend Engineer for API/service foundation; DevOps Engineer for Compose/local environment. **Contributors:** Security Architect for trust-boundary/RLS requirements; QA Engineer for validation plan; Chief Architect for architecture and shared-contract approval. |
| **2. Authentication and security** | **Lead:** Security Architect for identity, policy, approvals, audit, emergency controls; Backend Engineer for API/service integration. **Contributors:** Database Architect for persistence/RLS; Frontend Developer for web flows; Administration Engineer for user/role operations; QA Engineer for auth, authorization, and isolation tests. |
| **3. Brain and memory** | **Lead:** AI Systems Engineer for Brain/model runtime; Memory Engineer for user/conversation memory and knowledge. **Contributors:** Backend Engineer for APIs/services; Database Architect for schema/query implications; Integration Engineer for optional adapters; QA Engineer for model, retrieval, and isolation tests. |
| **4. Personal Agent** | **Lead:** Autonomous Agent Engineer for planning, tools, execution. **Contributors:** Security Architect for permission/approval controls; Backend Engineer for task/API contracts; Integration Engineer for browser/external adapters; QA Engineer for side effects, rejection, verification, and failure tests. |
| **5. Language, voice, vision, remote control** | **Lead:** Language Intelligence Engineer. **Contributors:** Backend Engineer for service/API integration; AI Systems Engineer for Brain integration; Security Architect for remote-control permissions; Frontend Developer for operation states; QA Engineer for languages and error coverage. |
| **6. Administration, rules, service control, billing** | **Leads:** Administration Engineer for admin/service controls; Billing Engineer for billing. **Contributors:** Security Architect for enforcement/audit; Backend Engineer and Database Architect for APIs/persistence; Frontend Developer for admin/billing UI; QA Engineer for authorization, quotas, billing tests. |
| **7. Optional provider management and browsing** | **Lead:** Integration Engineer for provider registry, health, usage, routing, search, browser integrations. **Contributors:** AI Systems Engineer for routing/fallback; Security Architect for credentials/policy; Backend Engineer for contracts; QA Engineer for optionality, failure, and secret handling. |
| **8. Creative Studio** | **Lead:** Creative AI Engineer. **Contributors:** Backend Engineer for workflows/APIs; Database Architect for media metadata; Integration Engineer for optional processing adapters; Frontend Developer for studio UI; QA Engineer for processing/failure cases. |
| **9. Content-to-Video and presenters** | **Leads:** Video Presentation Engineer for orchestration, timelines, subtitles, preview/export; Presenter Engineer for avatars, animation, lip-sync, speech. **Contributors:** Creative AI Engineer for assets/rendering; Language Intelligence Engineer for language/voice interfaces; Backend Engineer for APIs; QA Engineer for pipeline/subtitle tests. |
| **10. Newsroom, Teaching, Storytelling** | **Leads:** News Intelligence Engineer for newsroom; Educational AI Engineer for education; Video Presentation Engineer and Presenter Engineer for delivery. **Contributors:** Security Architect for safety/audit; AI Systems Engineer for generation integration; QA Engineer for verification and education workflows. |
| **11. Cybersecurity Center** | **Lead:** Cybersecurity Engineer. **Contributors:** Security Architect for authorization, scope, safety; Backend Engineer for service/API; Administration Engineer for controls/report access; QA Engineer for authorized-target and safe-lab tests. |
| **12. Integration, QA, documentation, local release** | **Leads:** QA Engineer for integrated test report/retests; DevOps Engineer for Compose, packaging, release verification. **Contributors:** All module owners for fixes/evidence; Database Architect for migration/RLS checks; Backend Engineer and Frontend Developer for end-to-end fixes; Chief Architect for integration/boundary review. |

## Operating expectations

- Module owners remain responsible for implementation evidence, tests, documentation, and persistence changes.
- Chief Architect approves shared-boundary, shared-contract, and dependency changes; governance does not create an additional product module.
- QA participates throughout. Record exact test commands, environment, results, blockers, and retests. A checked-in test is not proof it ran.
- Preserve existing paths and working code; inspect contracts before changes and avoid duplicate services or empty scaffolding.
- Keep authorization, ownership, audit, secrets, and required approvals explicit for every capability.
- External AI APIs remain optional. Windows, Kali, and Android are not frontend deliverables in this milestone.
