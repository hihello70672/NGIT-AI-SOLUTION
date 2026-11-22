# Phase agent assignments

Assignments designate accountable owners and collaborators, not evidence that work is complete. The Chief Architect coordinates integration, owns boundary/shared-contract approval, and runs phase gates. The specification names 19 module-owner engineering roles; the Chief Architect is the 20th team member, not a new product module.

| Phase | Accountable owner(s) | Required collaborators |
|---|---|---|
| 1. Architecture, repository, database, shared protocols | Chief Architect; Database Architect; Backend Engineer | Security Architect; DevOps Engineer; QA Engineer. Chief Architect approves shared boundaries/contracts. |
| 2. Authentication, backend, security, user management | Backend Engineer; Security Architect; Database Architect | Frontend Developer; Administration Engineer; QA Engineer; DevOps Engineer. |
| 3. Brain, model runtime, memory, knowledge | AI Systems Engineer; Memory Engineer | Backend Engineer; Database Architect; Integration Engineer; QA Engineer; Security Architect. |
| 4. Personal Agent, tools, browser/computer interfaces | Autonomous Agent Engineer | Backend Engineer; Security Architect; Integration Engineer; QA Engineer; Database Architect for persistence decisions. |
| 5. Multilingual, voice, vision, remote control | Language Intelligence Engineer | AI Systems Engineer; Backend Engineer; Security Architect; Frontend Developer; QA Engineer. |
| 6. Administration, rules, service control, billing | Administration Engineer; Billing Engineer; Security Architect | Backend Engineer; Database Architect; Frontend Developer; QA Engineer; DevOps Engineer. |
| 7. Optional provider management and browsing | Integration Engineer | AI Systems Engineer; Autonomous Agent Engineer; Security Architect; Backend Engineer; QA Engineer. |
| 8. Creative Studio | Creative AI Engineer | Backend Engineer; Database Architect; Frontend Developer; AI Systems Engineer; QA Engineer; DevOps Engineer. |
| 9. Content-to-Video, presenters, lip-sync, subtitles | Video Presentation Engineer; Presenter Engineer | Creative AI Engineer; Language Intelligence Engineer; Backend Engineer; Frontend Developer; QA Engineer. Chief Architect approves Presenter boundary/placement changes. |
| 10. Newsroom, Teaching, Storytelling | News Intelligence Engineer; Educational AI Engineer | Video Presentation Engineer; Presenter Engineer; Creative AI Engineer; AI Systems Engineer; Security Architect; QA Engineer. |
| 11. Cybersecurity Center | Cybersecurity Engineer; Security Architect | Backend Engineer; Autonomous Agent Engineer; Administration Engineer; QA Engineer. Security Architect reviews authorization/audit controls. |
| 12. Integration, QA, documentation, local release | QA Engineer; DevOps Engineer | All module owners; Backend Engineer; Database Architect; Frontend Developer; Chief Architect coordinates integration and release gates. |

## Operating rules

- Preserve working code; do not duplicate services or create empty scaffolding.
- Review existing code and relevant interface docs before assigning implementation paths.
- Document dependencies and report blockers early.
- Add tests with implementation; report exact tests actually executed and results. Never claim tests passed unless run.
- Route proposed shared-interface and module-boundary changes through the Chief Architect.
- Keep downstream work in approved phase order; external AI integrations remain optional.

See the [phase plan](PHASE_PLAN.md), [architecture](ARCHITECTURE.md), and [status](STATUS.md) for gates, current evidence, and outstanding verification.