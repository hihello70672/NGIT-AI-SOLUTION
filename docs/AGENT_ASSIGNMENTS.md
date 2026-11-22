# Agent assignments

The Chief Architect coordinates across phases and approves shared architecture and contract changes. The 20th engineering-agent role is open because the plan names 19 module-owner roles.

| Phase | Primary owners | Coordination and collaboration |
|---|---|---|
| **1** | Backend Engineer; Database Architect; DevOps Engineer; Frontend Developer | Security Architect and QA Engineer review contracts, security foundations, and test strategy. Chief Architect coordinates boundaries, naming, dependencies, and open decisions. |
| **2** | Backend Engineer; Security Architect | Database Architect: migrations/data ownership; Frontend Developer: auth states; Administration Engineer: user/role requirements; QA Engineer: authz/isolation; DevOps Engineer: local configuration. |
| **3** | AI Systems Engineer; Memory Engineer | Backend Engineer: API/services; Database Architect: migrations/indexes; Integration Engineer: optional provider boundary; Security Architect: isolation/secrets; QA Engineer: model/memory/retrieval behavior. |
| **4** | Autonomous Agent Engineer | Security Architect: approvals/restricted actions; Backend Engineer: task/API; Integration Engineer: optional browser; QA Engineer: observation, verification, permission failures. |
| **5** | Language Intelligence Engineer | AI Systems Engineer: Brain integration; Frontend Developer: capability/failure states; Security Architect: remote access; QA Engineer: language and access tests. |
| **6** | Administration Engineer; Billing Engineer | Security Architect: enforcement review; Backend Engineer/Database Architect: APIs/data; Frontend Developer: screens; Integration Engineer only after provider approval; QA Engineer: privileged ops, quotas, billing. |
| **7** | Integration Engineer | AI Systems Engineer: optional routing/fallback; Security Architect: credentials; Backend Engineer: APIs; QA Engineer: failures, health, provider-independent operation. |
| **8** | Creative AI Engineer | Integration Engineer: optional adapters; Backend Engineer/Database Architect: tasks/assets; Frontend Developer: studio; DevOps Engineer: runtime needs; QA Engineer: pipeline failures/outputs. |
| **9** | Video Presentation Engineer; Presenter Engineer | Creative AI Engineer: media; Language Intelligence Engineer: speech/subtitles; Frontend Developer: workflows; Backend Engineer: tasks/metadata; QA Engineer: sync, previews, subtitles, exports. |
| **10** | News Intelligence Engineer; Educational AI Engineer | Video Presentation/Presenter Engineers: presentation outputs; Language Intelligence Engineer: multilingual; Security Architect: newsroom safeguards; QA Engineer: verification and education workflows/failures. |
| **11** | Cybersecurity Engineer | Security Architect: authorization/approval/audit; Autonomous Agent Engineer: approved tools; Backend Engineer: integration; QA Engineer: accepted/rejected targets. |
| **12** | QA Engineer; DevOps Engineer | Every owner fixes and verifies reported failures; Backend Engineer, Database Architect, Frontend Developer support integration; Security Architect reviews gates; Chief Architect coordinates acceptance and verified ZIP. |

All owners report actual status, dependencies, tests run, blockers, and proposed contract changes. No completion or passing-test claim without repository evidence and actual execution.
