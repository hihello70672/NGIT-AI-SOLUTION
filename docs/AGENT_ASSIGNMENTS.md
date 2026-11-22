# Phase agent assignments

Assignments identify accountable owners and collaborators; they are not evidence that work is complete. The specification names 19 module-owner engineering roles. The Chief Architect is the twentieth coordination seat, responsible for shared architecture approval, dependency order, and cross-module contract disputes—not a new product module.

| Phase | Accountable owner(s) | Required collaborators |
|---|---|---|
| **1. Architecture, repository, database, shared protocols** | Chief Architect; Database Architect; DevOps Engineer; Backend Engineer | Security Architect reviews isolation/audit/trust boundaries; QA Engineer defines validation coverage; Chief Architect approves shared contracts. |
| **2. Authentication, backend, security, user management** | Backend Engineer; Security Architect | Database Architect; Frontend Developer; Administration Engineer; QA Engineer; DevOps Engineer. |
| **3. Brain, model runtime, memory, knowledge** | AI Systems Engineer; Memory Engineer | Backend Engineer integrates authenticated routes/services; Database Architect reviews schema; Security Architect reviews caller context; Integration Engineer and QA Engineer support adapters and ownership validation. |
| **4. Personal Agent, tools, browser/computer interfaces** | Autonomous Agent Engineer | Backend Engineer; Security Architect; Integration Engineer; QA Engineer; Database Architect for persistence decisions. |
| **5. Multilingual, voice, vision, remote control** | Language Intelligence Engineer | AI Systems Engineer; Backend Engineer; Security Architect; Frontend Developer; QA Engineer. |
| **6. Administration, rules, service control, billing** | Administration Engineer; Billing Engineer | Security Architect; Backend Engineer; Database Architect; Frontend Developer; QA Engineer; DevOps Engineer. |
| **7. Optional provider management and browsing** | Integration Engineer | AI Systems Engineer; Autonomous Agent Engineer; Security Architect; Backend Engineer; QA Engineer. |
| **8. Creative Studio** | Creative AI Engineer | Backend Engineer; Database Architect; Frontend Developer; AI Systems Engineer; QA Engineer; DevOps Engineer. |
| **9. Content-to-Video, presenters, lip-sync, subtitles** | Video Presentation Engineer; Presenter Engineer | Creative AI Engineer; Language Intelligence Engineer; Backend Engineer; Frontend Developer; QA Engineer. Chief Architect approves Presenter boundary/placement changes. |
| **10. Newsroom, Teaching, Storytelling** | News Intelligence Engineer; Educational AI Engineer | Video Presentation Engineer; Presenter Engineer; Creative AI Engineer; AI Systems Engineer; Security Architect; QA Engineer; Backend Engineer; Frontend Developer. |
| **11. Cybersecurity Center** | Cybersecurity Engineer | Security Architect reviews authorization/audit; Backend Engineer; Autonomous Agent Engineer; Administration Engineer; QA Engineer. |
| **12. Integration, QA, documentation, local release** | QA Engineer; DevOps Engineer | All module owners verify their integration; Backend Engineer; Database Architect; Security Architect; Frontend Developer; Chief Architect coordinates integration and release gates. |

## Operating rules

- Preserve working code and paths; do not duplicate services or create empty scaffolding. Review relevant contracts before selecting implementation paths.
- Record dependencies and blockers early. Report exact test commands and outcomes; never claim tests passed unless they ran.
- Route shared-interface and module-boundary proposals through the Chief Architect for approval.
- Follow the approved dependency order. External AI providers remain optional.
- See the [phase plan](PHASE_PLAN.md), [architecture](ARCHITECTURE.md), and [status](STATUS.md) for gates, current evidence, and outstanding validation.
