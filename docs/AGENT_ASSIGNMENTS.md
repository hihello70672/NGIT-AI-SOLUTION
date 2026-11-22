# Phase agent assignments

Assignments identify accountable owners and collaborators; they are not evidence of completion. The specification names 19 module-owner engineering roles. The Chief Architect coordinates the twentieth seat’s shared-architecture approval, dependency order, and cross-module contract disputes; this is not a new product module.

| Phase | Accountable lead(s) | Supporting owners and coordination |
|---|---|---|
| **1. Architecture, repository, database, protocols** | Chief Architect; Database Architect; DevOps Engineer; Backend Engineer | Security Architect reviews trust boundaries/isolation/audit; Frontend Developer inventories web contracts; QA Engineer defines validation coverage; Chief Architect approves shared contracts. |
| **2. Authentication, backend, security, users** | Backend Engineer; Security Architect | Database Architect handles schema/isolation; Administration Engineer specifies role needs; Frontend Developer integrates contracts; QA tests auth, permissions, errors and isolation; DevOps validates local configuration. |
| **3. Brain, runtime, memory, knowledge** | AI Systems Engineer; Memory Engineer | Backend integrates API/services; Security reviews caller context/secrets; Database Architect reviews ownership/indexes; Integration Engineer supports optional adapters; QA runs evaluation/isolation checks. |
| **4. Personal Agent, tools, browser/computer** | Autonomous Agent Engineer; Security Architect | Backend integrates API/task contracts; AI Systems Engineer supplies Brain contract; Memory Engineer supplies retrieval contract; QA tests policy, approvals, tools and adapters; DevOps provisions test environment. |
| **5. Language, voice, vision, remote interfaces** | Language Intelligence Engineer | AI Systems integrates Brain behavior; Autonomous Agent owns remote-control execution boundaries; Presenter and Creative AI coordinate capability interfaces; Security reviews permissions/privacy; QA tests languages and failures. |
| **6. Administration, rules, service control, billing** | Administration Engineer; Billing Engineer | Security defines enforcement/audit; Backend integrates services; Database Architect reviews persistence; Frontend builds UI; QA tests roles, quotas, billing flows and restricted actions; DevOps supports operations. |
| **7. Optional provider management and browsing** | Integration Engineer | AI Systems owns routing contracts; Autonomous Agent coordinates browser-tool boundary; Security reviews credentials/permissions; DevOps handles configuration/health; QA tests connection, failures, fallback and secret handling. |
| **8. Creative Studio** | Creative AI Engineer | Backend integrates services; Language supports language contracts; Database Architect reviews metadata/ownership; Frontend builds Studio UI; QA tests media errors, ownership and rendering; DevOps supports local runtime. |
| **9. Content-to-Video, presenters, subtitles** | Video Presentation Engineer; Presenter Engineer | Creative AI supplies assets/rendering; Language supports voice/subtitles; Backend integrates services; Frontend builds workflow UI; QA tests timeline, synchronization, export, modes and failures; Chief Architect approves boundary changes. |
| **10. Newsroom, Teaching, Storytelling** | News Intelligence Engineer; Educational AI Engineer | Video Presentation and Presenter integrate approved contracts; Language supports multilingual content; Creative AI supports media; Security reviews provenance/safety; QA tests provenance, subtitles, lessons and assessment. |
| **11. Cybersecurity Center** | Cybersecurity Engineer; Security Architect | Backend integrates authorization/audit; Administration coordinates service controls; Database Architect reviews audit persistence; Frontend builds UI; QA tests authorization, safe-lab limits and reporting. |
| **12. Integration, QA, docs, local release** | QA Engineer; DevOps Engineer; Backend Engineer | All module owners fix/retest; Database Architect verifies migrations/RLS; Security signs off authorization/secrets; Frontend verifies web flows; Chief Architect coordinates integration and approves shared contracts. |

## Operating expectations

- Preserve working code and paths; inspect existing contracts before implementation. Do not duplicate services or create empty scaffolding.
- Report dependencies, blockers, exact test commands and actual outcomes. QA participates throughout the phases.
- Keep authorization, ownership, audit, secrets, and approval requirements explicit for each capability.
- Chief Architect approval is required for shared contracts, dependency changes, and module-boundary changes.
- External AI APIs remain optional. Windows, Kali, and Android are not current frontend deliverables.
