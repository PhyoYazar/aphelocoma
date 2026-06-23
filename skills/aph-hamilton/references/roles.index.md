# Role Catalog

Every role Hamilton can activate. A **crew size preset** (see `sizes.yaml`) selects
which subset is active for a project; unselected roles stay dormant. A role may be
instantiated more than once (e.g. `fullstack-developer#1`, `#2`). Full job descriptions
live in `roles/<role-id>.md`.

| Role ID | Title | Level | Reports to | One-line responsibility |
|---|---|---|---|---|
| ceo | Chief Executive Officer | exec | — | Owns product/business vision, goals, and priorities. |
| cto | Chief Technology Officer | exec | ceo | Owns technology direction, architecture-level calls, and technical risk. |
| vp-engineering | VP of Engineering | exec | cto | Turns tech vision into execution: org, delivery process, budget. |
| engineering-manager | Engineering Manager | manager | vp-engineering | Breaks roadmap into tasks, assigns them, removes blockers, owns delivery. |
| software-architect | Software Architect | senior | cto | Designs system structure, picks tech, writes specs with acceptance criteria. |
| fullstack-developer | Full-stack Developer | ic | engineering-manager | Builds end-to-end features (frontend + backend); generalist for small teams. |
| frontend-lead | Frontend Lead | senior | engineering-manager | Owns frontend architecture, standards, and frontend task breakdown. |
| frontend-developer | Frontend Developer | ic | frontend-lead | Builds UI components, screens, and client logic. |
| backend-lead | Backend Lead | senior | engineering-manager | Owns API design, backend architecture, and backend task breakdown. |
| backend-developer | Backend Developer | ic | backend-lead | Builds APIs, business logic, and data access. |
| mobile-developer | Mobile Developer | ic | engineering-manager | Builds iOS/Android (or cross-platform) apps. |
| devops-engineer | DevOps Engineer | senior | engineering-manager | Builds CI/CD, pipelines, environments; integrates and ships. |
| sre | Site Reliability Engineer | senior | engineering-manager | Owns availability, monitoring, incident response, performance. |
| cloud-engineer | Cloud Engineer | senior | engineering-manager | Provisions cloud infra: networks, compute, storage, security. |
| dba | Database Administrator | senior | engineering-manager | Owns database design, performance, backup, and security. |
| data-engineer | Data Engineer | ic | engineering-manager | Builds data pipelines and the data warehouse. |
| data-scientist | Data Scientist | senior | engineering-manager | Analyzes data; builds models, predictions, and insights. |
| ml-engineer | Machine Learning Engineer | senior | engineering-manager | Productionizes models as services/APIs. |
| security-engineer | Security Engineer | senior | cto | Protects systems: authn/z, encryption, vulnerability management. |
| appsec-engineer | Application Security Engineer | senior | security-engineer | Reviews code/API security (OWASP); prevents injection/XSS/authz bugs. |
| qa-engineer | QA Engineer | ic | engineering-manager | Verifies features against acceptance criteria; finds bugs. |
| automation-test-engineer | Automation Test Engineer | ic | qa-engineer | Writes and maintains automated test suites. |
| product-manager | Product Manager | manager | ceo | Decides what to build and why; owns priorities and requirements. |
| business-analyst | Business Analyst | ic | product-manager | Translates business needs into requirements, flows, and rules. |
| uiux-designer | UI/UX Designer | ic | product-manager | Designs UX, wireframes, and UI specs. |
| tech-support-engineer | Technical Support Engineer | ic | engineering-manager | Handles user issues; triages bugs back to engineering. |
| technical-writer | Technical Writer | ic | engineering-manager | Produces documentation, API docs, and user guides. |

**27 roles total.** Sizes: `solo` (~2), `startup` (~6), `mid` (~12), `big` (~25, full chart), or `custom`.
