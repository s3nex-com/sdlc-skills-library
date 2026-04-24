# Master Skill Build Prompt
## Inter-Company Software Project Leadership — 24 Claude Skills

**Authored for:** VP of Engineering, 35 years experience  
**Context:** Cross-company software project requiring governance, quality enforcement, documentation, testing, and AI-assisted engineering at the highest professional level  
**Purpose:** This document is a complete, self-contained prompt to pass to an AI tool (Claude or equivalent) to build each of the 24 skills defined below. Each skill must be built as a proper Claude skill package with a `SKILL.md` file, supporting reference files, and scripts where applicable.

---

## How to Use This Document

Pass this entire document to your AI tool with the following instruction prepended:

> "I need you to build a Claude skill. Read this entire document carefully. At the end you will find 24 skill definitions. I will tell you which skill number to build. Build it completely — SKILL.md, all reference files, all scripts, and all assets — following every convention and quality standard described in the CONTEXT and CONVENTIONS sections below. Do not skip any section of the skill. Do not produce placeholder content. Every section must be production-ready."

Then specify: **"Build Skill #[N]: [Skill Name]"**

You can build them one at a time or in batches. The phase groupings at the end of this document indicate the recommended build order.

---

## Part 1 — What a Claude Skill Is

A Claude skill is a structured knowledge and instruction package that tells Claude how to handle a specific category of task. When a user's request matches a skill's description, Claude reads the skill's instructions and follows them to produce a better, more consistent, more expert result than it would without the skill.

### File Structure

Every skill must follow this directory layout:

```
skill-name/
├── SKILL.md                  ← Required. The core instruction file.
└── references/               ← Optional but usually needed for complex skills.
    ├── reference-topic-a.md
    ├── reference-topic-b.md
    └── ...
└── scripts/                  ← Optional. Python or bash scripts for repeatable tasks.
    ├── some-script.py
    └── ...
└── assets/                   ← Optional. Templates, checklists, schema files.
    ├── template.md
    └── ...
```

### SKILL.md Structure

Every `SKILL.md` must start with a YAML frontmatter block, followed by the body:

```markdown
---
name: skill-identifier-in-kebab-case
description: >
  A detailed paragraph describing EXACTLY what this skill does AND
  every context in which it should trigger. This is the primary mechanism
  Claude uses to decide whether to invoke the skill. Be explicit, be
  comprehensive, list trigger phrases and scenarios. Err on the side of
  being too specific rather than too vague. The description should make
  Claude want to use this skill whenever the scenario is even adjacent
  to what it covers.
---

# Skill Title

[Body content — see conventions below]
```

### Three-Level Progressive Disclosure

Skills are loaded progressively:

1. **Metadata only** (name + description) — always in Claude's context. ~100 words max. This is what triggers the skill.
2. **SKILL.md body** — loaded when the skill triggers. Keep under 500 lines. This is the main instruction set.
3. **Reference files and scripts** — loaded or executed on demand. Unlimited size. SKILL.md must clearly state when and why to read each one.

---

## Part 2 — Conventions and Quality Standards

These conventions apply to every single skill in this document. They are non-negotiable.

### Writing Style

- Use the **imperative form** for all instructions: "Review the architecture", not "You should review the architecture"
- **Explain the why** behind every instruction. Do not just say MUST or NEVER. Say why the thing matters. Claude follows reasoning better than commands.
- **No placeholder content.** Every section must be complete and usable the first time.
- **Sentence case** everywhere. Never ALL CAPS headings, never Title Case in body text beyond headings.
- Use `code style` for file names, commands, tool names, and technical identifiers.
- Keep the SKILL.md body under 500 lines. If the content is larger, split it into reference files and point to them from SKILL.md with clear guidance on when to read each one.

### Output Format Standards

Every skill that produces a report, review, audit, or structured output must define its output format explicitly in the SKILL.md using a template block like this:

```markdown
## Output format

Always produce output in this exact structure:

### [Section Title]
[What goes here]

### [Section Title]
[What goes here]
```

### Severity and Priority Ratings

Skills that produce findings, issues, or recommendations must use a consistent severity system:

- **Critical** — Blocks release, breaks contract, introduces security risk, or causes data loss
- **High** — Significant quality, reliability, or maintainability impact
- **Medium** — Should be addressed before next milestone
- **Low** — Good to fix, not urgent
- **Informational** — Observation with no required action

### Cross-Company Context

This skill set is designed for a VP of Engineering operating in a **cross-company engagement** where:

- The partner company writes code that you must review and approve
- You are responsible for quality, architecture, security, and delivery without micromanaging
- All findings must be communicated precisely — technically for engineers, diplomatically for stakeholders
- Decisions and deviations must be documented because they may have legal or contractual implications
- "Done" must be objectively verifiable, not a matter of opinion

Every skill must take this context into account. Where a skill produces communication output (reports, reviews, notifications), it must be suitable for a cross-company professional audience.

### Trigger Description Writing Rules

The `description` field in SKILL.md frontmatter is what causes Claude to use the skill. Write it to be slightly "pushy" — it should cover not just the primary use case but all adjacent scenarios where this skill adds value. Include:

- What the skill does in one sentence
- A list of trigger phrases and contexts
- Adjacent scenarios where the skill is still relevant even if not explicitly requested

Example of a good description:
```
Governs architecture review and technical decision-making in a cross-company
software project. Use this skill whenever the user wants to: review a system
design, evaluate a technical proposal, check architecture against principles,
produce an ADR (Architecture Decision Record), flag architectural drift, assess
trade-offs between technical approaches, or ensure a component design meets
quality and scalability standards. Also trigger when the user asks about
integration design, service boundaries, data flow, or any question involving
how parts of the system fit together.
```

---

## Part 3 — The 24 Skills

The skills are organized into four build phases. Build Phase 1 skills first — they establish the governance and contractual foundation before code is written. Phase 2 skills support active development. Phase 3 skills mature the engagement. Phase 4 is advanced practice.

---

### PHASE 1 — Before Code Is Written
*Build these before any development begins. They establish authority, boundaries, and shared understanding.*

---

#### Skill #1: Project & Partner Governance

**Skill identifier:** `project-partner-governance`  
**Difficulty:** 3/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

This skill governs the structural foundation of a cross-company software engagement. It covers everything that happens before and around the code: how decisions are made, who owns what, how scope changes are handled, how risks are escalated, and how both companies stay aligned over time.

Specifically it must handle:

- Drafting and reviewing project charters (purpose, scope, success metrics, exit criteria)
- Building and maintaining RACI matrices (who is Responsible, Accountable, Consulted, Informed for every key decision type)
- Defining and enforcing SLA and SLO commitments between companies
- Escalation path design — what triggers escalation, to whom, in what timeframe
- Scope change control — how changes are requested, evaluated, approved, and documented
- OKR alignment — ensuring engineering OKRs link to business outcomes both companies agreed on
- Governance meeting cadence — what meetings are required, who attends, what decisions require which meeting
- Joint decision log — a running record of every significant technical and business decision, who made it, when, and why
- Deviation tracking — when delivery deviates from agreed scope, architecture, or quality, how it is recorded and resolved

**Reference files to create:**

- `references/charter-template.md` — A complete project charter template with all required sections
- `references/raci-template.md` — RACI matrix template with example decision categories pre-filled
- `references/decision-log-template.md` — Decision log format with fields for decision, context, owner, date, alternatives considered, consequences
- `references/scope-change-template.md` — Scope change request format including impact assessment fields
- `references/governance-meeting-cadences.md` — Recommended meeting types, frequencies, attendees, and agendas

**Scripts to create:**

- `scripts/generate_charter.py` — Takes project name, company names, high-level goals as input and generates a populated charter draft in Markdown
- `scripts/generate_raci.py` — Takes a list of decision categories and role names and outputs a formatted RACI table

**Trigger phrases for description:**

"set up project governance", "create a charter", "RACI matrix", "who owns what", "scope is creeping", "we need an escalation path", "partner company is not aligned", "document a decision", "scope change request", "governance structure", "joint OKRs", "project kickoff", "SLA between companies", "partner SLA"

---

#### Skill #2: Architecture Review & Governance

**Skill identifier:** `architecture-review-governance`  
**Difficulty:** 5/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

This skill governs the technical architecture of the project — defining what the right architecture is, enforcing it as delivery proceeds, and catching drift before it becomes debt. Given the VP's experience spanning operating systems, HCI platforms, and edge AI, this skill must be sophisticated enough to handle both high-level system design and low-level component decisions.

Specifically it must handle:

- Defining and documenting architecture principles (the non-negotiables that both companies must follow)
- Reviewing architecture proposals against defined principles and quality attributes
- Evaluating trade-offs between architectural approaches (microservices vs monolith, sync vs async, edge vs cloud, etc.)
- Identifying architectural anti-patterns, hidden coupling, and scalability traps
- Enforcing service and component boundaries — what each service is allowed to do and not do
- Integration architecture — how components connect, what protocols are used, what failure modes exist
- Data architecture — ownership, flow, consistency model, retention, residency
- Non-functional requirement validation — latency, throughput, availability, security posture, maintainability score
- Architecture drift detection — when implementation deviates from agreed architecture
- Review gates — defining formal checkpoints where architecture must be reviewed before proceeding

**Reference files to create:**

- `references/architecture-principles-template.md` — Template for capturing project-specific architecture principles with rationale for each
- `references/review-checklist.md` — Multi-dimensional architecture review checklist covering: scalability, security, operability, maintainability, integration safety, data integrity, and failure modes
- `references/anti-patterns.md` — Catalogue of common architecture anti-patterns with examples and why each is dangerous
- `references/trade-off-frameworks.md` — Structured frameworks for evaluating common architecture trade-offs (e.g. CAP theorem, PACELC, build vs buy, sync vs async)
- `references/nfr-template.md` — Non-functional requirements specification template with measurable acceptance criteria fields

**Scripts to create:**

- `scripts/review_report.py` — Takes a list of architecture review findings and generates a structured report with severity ratings, categorized by domain (security, scalability, etc.)

**Trigger phrases for description:**

"review this architecture", "evaluate this design", "microservices vs monolith", "is this the right approach", "architecture proposal", "service boundaries", "check our design", "architecture drift", "system design review", "integration design", "data flow", "scalability concerns", "architecture principles", "non-functional requirements", "architecture gate"

---

#### Skill #3: Architecture Decision Records (ADR)

**Skill identifier:** `architecture-decision-records`  
**Difficulty:** 2/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

ADRs are the institutional memory of technical decision-making. Every major technical decision — technology choices, architectural patterns, interface contracts, security posture decisions, tooling selections — must be captured in a structured, version-controlled record that explains not just what was decided but why, what alternatives were considered, and what the consequences are expected to be. Without ADRs, knowledge lives in people's heads and Slack threads, architecture drift is invisible, and onboarding new team members or auditors becomes painful.

This skill must handle:

- Creating new ADRs from a decision description — prompting for all required fields and producing a complete, well-reasoned document
- Reviewing proposed decisions before they are finalized — checking that alternatives were genuinely considered and consequences thought through
- Updating ADRs when decisions are superseded or reversed — maintaining the history trail
- Searching and referencing existing ADRs when a new decision touches the same domain
- ADR numbering and index maintenance — keeping a navigable index of all decisions
- Recognizing when a decision warrants an ADR — not every choice needs one, but anything affecting architecture, interfaces, security, or external dependencies does
- Formatting ADRs consistently for cross-company readability

**Required ADR fields** (every ADR must have all of these):

- Number and title
- Date and status (Proposed / Accepted / Deprecated / Superseded)
- Context — what situation forced this decision
- Decision — what was decided, stated precisely
- Alternatives considered — at minimum two real alternatives with honest pros and cons
- Consequences — what becomes easier, what becomes harder, what new risks this introduces
- Owner — who made or approved this decision
- Review date — when this decision should be re-evaluated

**Reference files to create:**

- `references/adr-template.md` — Complete ADR template with all required fields, instructions for each field, and a filled example
- `references/adr-index-template.md` — Index page format for maintaining a navigable list of all ADRs
- `references/adr-good-vs-bad.md` — Examples of well-written and poorly written ADRs with annotations explaining what makes the difference

**Trigger phrases for description:**

"create an ADR", "architecture decision record", "document this decision", "why did we choose", "record a technical decision", "decision log", "technology choice", "why are we using X", "supersede a decision", "decision history", "log a design decision"

---

#### Skill #4: Requirements Tracer & Scope Control

**Skill identifier:** `requirements-tracer`  
**Difficulty:** 4/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

Vague requirements are the root cause of most failed inter-company projects. This skill converts business asks into testable, traceable, deliverable units — and then keeps them linked to everything built from them. It also enforces scope discipline: every feature must trace back to an agreed requirement, and every requirement must have a clear acceptance criterion before work begins.

Specifically it must handle:

- Decomposing high-level business goals into epics, features, and user stories with explicit acceptance criteria
- Writing acceptance criteria in the Given/When/Then (BDD) format for testability
- Traceability matrix maintenance — linking requirements → features → code → tests
- Orphan detection — flagging code or tests that have no traceable requirement, and requirements that have no implementation
- Scope change impact analysis — when a new request arrives, showing what it touches, what it risks, and what it costs
- Phase and milestone planning — slicing requirements into coherent delivery increments
- Requirement quality review — checking that requirements are unambiguous, measurable, achievable, and independent
- Partner requirement handshake — ensuring both companies agree on the same requirement definition before work starts

**Reference files to create:**

- `references/requirement-decomposition-guide.md` — Step-by-step guide to decomposing a vague business ask into well-formed requirements, with worked examples
- `references/acceptance-criteria-patterns.md` — Catalogue of BDD Given/When/Then patterns for common requirement types (functional, performance, security, integration)
- `references/traceability-matrix-template.md` — Template for the requirements traceability matrix
- `references/scope-impact-template.md` — Template for scope change impact analysis

**Scripts to create:**

- `scripts/check_orphans.py` — Takes a requirements list and a codebase/test manifest and identifies requirements with no implementation and code with no requirement

**Trigger phrases for description:**

"decompose requirements", "write acceptance criteria", "traceability", "scope creep", "this feature is not in scope", "requirements matrix", "BDD", "given when then", "what does done mean", "orphaned code", "requirements traceability", "user story", "feature breakdown", "scope change impact"

---

#### Skill #5: Technical Risk Management

**Skill identifier:** `technical-risk-management`  
**Difficulty:** 4/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

Late surprises kill projects. This skill forces risks to be identified, rated, owned, and mitigated early — and tracked visibly so both companies can see the risk landscape at any time. This covers technical risks (architecture, scaling, dependencies), delivery risks (timeline, capacity, partner execution), security risks, operational risks, and partnership risks (IP, contractual, communication).

Specifically it must handle:

- Risk identification across all categories: architecture, delivery, dependency, security, operational, contractual, organisational
- Risk rating using a consistent Probability × Impact matrix
- Mitigation strategy design — for each risk, a concrete action that reduces probability or impact
- Kill criteria — explicit conditions under which the project should be stopped or restructured
- Risk register creation and maintenance — a living document updated every sprint or milestone
- Risk status tracking — risks move through: Identified → Being Mitigated → Resolved / Accepted / Escalated
- Early warning indicators — leading metrics that signal a risk is materialising before it becomes an incident
- Cross-company risk reporting — a risk summary suitable for executive and partner stakeholder consumption

**Reference files to create:**

- `references/risk-register-template.md` — Complete risk register template with all required fields and example entries across all risk categories
- `references/risk-rating-matrix.md` — Probability × Impact matrix with rating definitions (1-5 scale for both axes, producing a composite score)
- `references/risk-categories.md` — Taxonomy of risk categories relevant to cross-company software projects with examples for each
- `references/kill-criteria-examples.md` — Examples of well-defined kill criteria with rationale

**Scripts to create:**

- `scripts/risk_report.py` — Takes a risk register (CSV or JSON) and generates a formatted risk summary report sorted by composite risk score

**Trigger phrases for description:**

"risk register", "identify risks", "what could go wrong", "risk assessment", "risk mitigation", "kill criteria", "technical risks", "dependency risk", "partner risk", "risk rating", "early warning", "risk tracking", "project risk", "delivery risk"

---

#### Skill #6: Inter-Company Communications

**Skill identifier:** `inter-company-communications`  
**Difficulty:** 2/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

In a cross-company engagement, how you communicate is as important as what you communicate. This skill produces technically precise, professionally calibrated communications for every type of inter-company interaction. The VP speaks to multiple audiences simultaneously: the partner company's engineers (peer technical level), the partner company's leadership (executive level), your own leadership, and mixed groups. Each requires a different register while conveying the same facts.

Specifically it must handle:

- Status reports — what was delivered, what is at risk, what is blocked, what is next
- Escalation communications — when something is going wrong and a partner stakeholder must act
- Scope pushback — diplomatically but firmly declining or deferring out-of-scope requests
- Risk notifications — informing partners of a risk they must be aware of without causing panic
- Technical decisions for non-technical audiences — explaining an architecture or technology choice in business terms
- Milestone acceptance / rejection communications — formally accepting or rejecting a deliverable with evidence
- Meeting summaries — concise, action-item-forward summaries of governance and technical meetings
- Difficult conversations — quality issues, missed commitments, IP concerns — framed constructively

**Reference files to create:**

- `references/communication-templates.md` — A library of templates for every communication type listed above, with tone guidance for each audience
- `references/audience-calibration-guide.md` — How to adjust the same technical message for engineers, technical managers, executives, and legal/contractual stakeholders
- `references/escalation-framework.md` — When to escalate, to whom, using what channel, with what urgency level

**Trigger phrases for description:**

"write a status report", "draft an escalation", "communicate this risk", "meeting summary", "push back on this request", "explain this decision to stakeholders", "email to partner", "decline this scope", "milestone rejection", "formal communication", "notify partner", "executive summary", "inter-company message"

---

#### Skill #7: Specification-Driven & Contract-First Development

**Skill identifier:** `specification-driven-development`  
**Difficulty:** 3/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

No code is written until the interfaces, contracts, schemas, and workflows are defined and agreed. This is especially critical in a cross-company context where both teams build components that must integrate — if the interface is ambiguous, each team implements their interpretation and integration becomes a debugging marathon.

Contract-first development means: define the API contract (OpenAPI, Protobuf, AsyncAPI, JSON Schema, etc.), review it, freeze it, then build to it. The contract is the truth. Code is secondary.

Specifically it must handle:

- OpenAPI 3.x specification authoring — writing complete, production-quality API specs from a natural language description of the API
- Protobuf / gRPC schema authoring — for services using binary protocols
- AsyncAPI specification authoring — for event-driven and message-queue interfaces
- JSON Schema definition — for data payloads, configuration files, event envelopes
- Contract review — checking specs for completeness, consistency, ambiguity, versioning correctness, and error model completeness
- Interface negotiation — when both companies need to agree on a contract, structuring the discussion and producing the final agreed spec
- Workflow and sequence specification — documenting multi-step interactions using sequence diagrams or structured workflow definitions before implementation
- Contract freeze process — the formal sign-off that locks a contract and prevents unilateral changes

**Reference files to create:**

- `references/openapi-guide.md` — Complete guide to writing production-quality OpenAPI 3.x specs including: info block, paths, operations, request/response schemas, error models, security schemes, versioning conventions
- `references/protobuf-guide.md` — Guide to writing Protobuf schemas including: field numbering, reserved fields, backward compatibility rules, service definitions
- `references/asyncapi-guide.md` — Guide to AsyncAPI specification for event-driven interfaces
- `references/contract-review-checklist.md` — Checklist for reviewing any API or data contract before freezing it
- `references/contract-freeze-process.md` — Step-by-step process for formally freezing a contract with both company sign-off

**Scripts to create:**

- `scripts/validate_openapi.py` — Validates an OpenAPI spec file for structural correctness, completeness, and common issues (missing error responses, undocumented fields, etc.)
- `scripts/diff_contracts.py` — Takes two versions of a contract and produces a structured diff highlighting breaking vs non-breaking changes

**Trigger phrases for description:**

"write an API spec", "OpenAPI", "contract-first", "define the interface before coding", "Protobuf", "AsyncAPI", "JSON Schema", "freeze the contract", "API contract review", "service contract", "define the schema", "specification", "interface agreement", "contract negotiation", "sequence diagram"

---

#### Skill #8: Security Audit & Secure SDLC

**Skill identifier:** `security-audit-secure-sdlc`  
**Difficulty:** 4/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 1

**What it covers:**

Security must be designed in from the start, not bolted on at the end. In a cross-company context, security failures create legal liability and destroy trust. This skill governs security across the entire SDLC — from threat modeling in design through secure coding standards, automated scanning in CI/CD, dependency hygiene, secrets management, and release governance.

Specifically it must handle:

- Threat modeling — STRIDE-based analysis of the system to identify attack surfaces before code is written
- Secure design principles — least privilege, defence in depth, fail-secure defaults, zero trust assumptions
- Secure coding standards — what patterns are required and forbidden in this codebase
- Dependency hygiene — known CVE scanning, license compatibility checking, EOL tracking
- Secrets management — no secrets in code, in logs, or in config files; vault or secrets manager required
- SAST (Static Application Security Testing) — required tools and gates in CI/CD
- DAST (Dynamic Application Security Testing) — required for pre-production environments
- SCA (Software Composition Analysis) — scanning third-party libraries for vulnerabilities
- Build integrity — verifying that the build pipeline has not been tampered with
- Compliance baseline — NIST SSDF, OWASP Top 10, and project-specific compliance requirements
- Security review gates — formal checkpoints before milestone completion where security must be signed off

**Reference files to create:**

- `references/threat-modeling-guide.md` — Step-by-step STRIDE threat modeling process with worked example
- `references/secure-coding-standards.md` — Language-agnostic secure coding standards covering: input validation, output encoding, authentication, authorisation, cryptography, error handling, logging
- `references/dependency-hygiene.md` — Policy and tooling guidance for dependency management, CVE scanning, and licence compliance
- `references/secrets-management.md` — Standards for secrets handling: what is a secret, where secrets live, how they are rotated, what to do when a secret is leaked
- `references/security-gates.md` — Formal security review gate checklist for each milestone (design, pre-development, pre-release, post-release)
- `references/nist-ssdf-mapping.md` — How this project's security practices map to the NIST Secure Software Development Framework

**Trigger phrases for description:**

"threat model", "security review", "STRIDE", "secure coding", "SAST", "DAST", "SCA", "dependency scan", "secrets in code", "security gate", "OWASP", "NIST SSDF", "security posture", "vulnerability", "secure design", "penetration test prep", "compliance", "security audit"

---

### PHASE 2 — During Active Development
*Build these once development begins. They enforce quality, test coverage, and delivery discipline.*

---

#### Skill #9: Code Review & Quality Gates

**Skill identifier:** `code-review-quality-gates`  
**Difficulty:** 3/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 2

**What it covers:**

Code review is the primary quality enforcement mechanism in a cross-company engagement. This skill governs the entire code review process — from what reviewers look for, to how findings are communicated, to what gates must be passed before code merges. It is not just about catching bugs — it enforces structure, readability, operability, security posture, test coverage, and adherence to architectural decisions.

Specifically it must handle:

- Multi-dimensional review framework — checking code across: correctness, security, performance, maintainability, testability, observability, error handling, architectural compliance, documentation
- Pull request template design — mandatory checklists that authors must complete before requesting review
- Review comment standards — how to write a review comment that is precise, respectful, actionable, and severity-rated
- Code ownership — who must review what (by component, by risk level, by security sensitivity)
- Automated gate configuration — what automated checks must pass before a human reviewer even looks at code
- Review escalation — when a review disagreement requires a third party or architecture decision
- Cross-company review protocol — how the VP or senior engineers on your side review code from the partner company
- Quality metrics — tracking review turnaround time, defect density, rework rate, and gate pass rate

**Reference files to create:**

- `references/review-dimensions.md` — Detailed explanation of each review dimension with examples of what to look for and common failure patterns
- `references/pr-template.md` — Complete pull request template with author checklist, reviewer checklist, and required sections
- `references/review-comment-guide.md` — How to write review comments at each severity level with examples
- `references/automated-gates.md` — Recommended automated gate configuration: linting, type checking, test coverage thresholds, security scanning, dependency checking
- `references/code-ownership-matrix.md` — Template for defining code ownership by component and risk level

**Trigger phrases for description:**

"code review", "review this code", "pull request", "PR review", "quality gate", "code quality", "review checklist", "what to look for in code review", "review standards", "merge gate", "automated checks", "static analysis", "linting", "code ownership", "review process"

---

#### Skill #10: Comprehensive Test Strategy

**Skill identifier:** `comprehensive-test-strategy`  
**Difficulty:** 5/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 2

**What it covers:**

"Tested" must mean something. This skill designs and enforces a complete testing system — not just unit tests, but the entire pyramid from unit through integration, contract, end-to-end, performance, chaos, and security testing. It defines who owns each test type, what coverage is required, how tests are automated, and how testing results are reported.

Specifically it must handle:

- Testing pyramid design — the right proportion of unit, integration, contract, E2E, and other test types for this project
- Unit test standards — what must be unit tested, minimum coverage thresholds, mocking policy, test isolation requirements
- Integration test strategy — what integrations must be tested, in what environment, with what data
- Contract testing — using tools like Pact to verify that both companies' services honour their agreed contracts
- End-to-end testing — critical user journey coverage, environment requirements, data management
- Performance testing — load profiles, latency SLOs, throughput targets, and how to run and interpret results
- Chaos and resilience testing — fault injection scenarios, recovery time objectives, partner system failure simulation
- Security testing — DAST, fuzzing, authentication/authorisation boundary testing
- Test ownership matrix — which team owns which test type, and what happens when a test fails
- Coverage gates in CI/CD — minimum coverage thresholds that block deployment if not met
- Test reporting — how results are communicated and what constitutes a test failure vs a flaky test

**Reference files to create:**

- `references/testing-pyramid.md` — The specific testing pyramid for this project with rationale for the proportions chosen
- `references/unit-test-standards.md` — Unit test writing standards including: naming conventions, arrange-act-assert pattern, mocking rules, coverage requirements
- `references/contract-testing-guide.md` — How to implement Pact-based contract testing between the two companies' services
- `references/performance-testing-guide.md` — How to design, run, and interpret performance tests including load profiles and SLO validation
- `references/chaos-testing-guide.md` — Chaos engineering principles and a catalogue of fault injection scenarios relevant to this project type
- `references/test-ownership-matrix-template.md` — Template for assigning test ownership by test type and component

**Scripts to create:**

- `scripts/coverage_report.py` — Parses test coverage output and produces a structured report showing coverage by module against defined thresholds
- `scripts/test_health_check.py` — Analyses test suite for flaky tests, unused mocks, and tests with no assertions

**Trigger phrases for description:**

"test strategy", "testing plan", "unit tests", "integration tests", "contract testing", "Pact", "end-to-end tests", "E2E", "performance testing", "chaos testing", "test coverage", "test ownership", "testing pyramid", "load testing", "resilience testing", "security testing", "test standards", "what to test"

---

#### Skill #11: DevOps Pipeline Governance & CI/CD

**Skill identifier:** `devops-pipeline-governance`  
**Difficulty:** 4/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 2

**What it covers:**

The CI/CD pipeline is the nervous system of delivery. This skill governs pipeline design, quality gates within pipelines, environment promotion rules, rollback capability, and policy enforcement. It turns delivery from heroics into an engineered process that both companies can trust and audit.

Specifically it must handle:

- Pipeline-as-code design — all pipeline definitions in version control, no clickops
- Stage design — what stages every pipeline must have (lint, test, security scan, build, publish, deploy)
- Gate configuration — what quality thresholds must pass at each stage before proceeding
- Policy-as-code — using OPA (Open Policy Agent) or equivalent to programmatically enforce policies (no unapproved base images, no secrets in environment variables, required labels on every deployment)
- Multi-environment promotion rules — what must be true before code moves from dev → staging → production
- Rollback design — every deployment must have a tested, documented, automated rollback path
- Release controls — who can approve a production deployment, what evidence is required
- Partner pipeline review — how to audit and approve the partner company's pipeline configuration
- Pipeline observability — how to monitor pipeline health, detect flakiness, and alert on failures

**Reference files to create:**

- `references/pipeline-stages.md` — Required pipeline stages with gate definitions for each stage
- `references/environment-promotion.md` — Promotion rules and evidence requirements for each environment transition
- `references/policy-as-code-examples.md` — Example OPA policies for common enforcement scenarios
- `references/rollback-playbook.md` — Template rollback playbook that every service deployment must have
- `references/partner-pipeline-audit.md` — Checklist for auditing a partner company's CI/CD pipeline

**Trigger phrases for description:**

"CI/CD", "pipeline", "deployment pipeline", "GitHub Actions", "Jenkins", "build pipeline", "quality gate in pipeline", "policy as code", "OPA", "environment promotion", "deploy to production", "rollback", "pipeline review", "release gate", "pipeline governance", "pipeline audit", "devops pipeline"

---

#### Skill #12: Documentation System Design

**Skill identifier:** `documentation-system-design`  
**Difficulty:** 3/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 2

**What it covers:**

Documentation is not a deliverable you produce at the end — it is a living system that grows with the project. This skill designs and enforces a layered documentation architecture that covers every audience and every need, from product vision through to operational runbooks.

Specifically it must handle:

- Documentation architecture design — defining the layers (product, architecture, API, operational) and what goes in each
- Docs-as-code implementation — documentation lives in the repository, is versioned with code, and is built and published via CI/CD
- Auto-generation — extracting documentation from code comments, OpenAPI specs, and test results rather than writing it by hand
- ADR integration — architecture decisions are part of the documentation system (see Skill #3)
- API documentation — complete, accurate, example-rich API docs generated from specs
- Runbooks — step-by-step operational procedures for every critical operation (deployment, rollback, incident response, scaling, backup)
- Onboarding documentation — what a new engineer on either team needs to get productive in under one day
- Architecture documentation — system overview, component descriptions, data flows, integration maps
- Documentation freshness — a process for identifying and updating stale documentation
- Cross-company documentation sharing — what documentation is shared with the partner company and in what format

**Reference files to create:**

- `references/documentation-layers.md` — The complete documentation architecture with layer definitions, audience for each layer, and update frequency
- `references/docs-as-code-setup.md` — How to configure a docs-as-code pipeline using MkDocs or Docusaurus with CI/CD publishing
- `references/runbook-template.md` — Complete runbook template with all required sections: purpose, prerequisites, steps, verification, rollback, escalation
- `references/onboarding-doc-template.md` — New engineer onboarding documentation template covering: environment setup, architecture overview, first tasks, who to contact
- `references/api-doc-standards.md` — Standards for API documentation: required sections, example quality, error documentation, versioning

**Scripts to create:**

- `scripts/doc_freshness_check.py` — Scans documentation files and flags those not updated in a configurable number of days or whose referenced code files have changed since the doc was last updated
- `scripts/generate_api_docs.py` — Takes an OpenAPI spec and generates formatted Markdown documentation

**Trigger phrases for description:**

"documentation", "docs", "write docs", "runbook", "onboarding documentation", "API docs", "architecture docs", "docs as code", "MkDocs", "documentation system", "stale docs", "documentation structure", "technical writing", "document this", "create a runbook"

---

#### Skill #13: Observability & SRE Practice

**Skill identifier:** `observability-sre-practice`  
**Difficulty:** 4/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 2

**What it covers:**

A system you cannot observe is a system you cannot operate. Observability must be designed in from the start, not added after the first production incident. This skill governs the design and implementation of logs, metrics, traces, SLOs, alerts, and dashboards — using OpenTelemetry as the vendor-neutral foundation.

Specifically it must handle:

- OpenTelemetry instrumentation strategy — what to instrument, how to instrument it, what SDK to use for each language
- Log standards — structured logging format (JSON), required fields (timestamp, severity, trace_id, service, environment), log levels and when to use each
- Metrics design — what metrics are required (RED: Rate, Errors, Duration; USE: Utilisation, Saturation, Errors), naming conventions, cardinality management
- Distributed tracing — trace propagation across service boundaries, span naming, attribute standards
- SLI and SLO definition — what Service Level Indicators measure the user experience, and what Service Level Objectives both companies agree to meet
- Error budget tracking — how to calculate and communicate error budget consumption
- Alerting design — alert routing, severity levels, escalation paths, alert fatigue prevention
- Dashboard design — what dashboards exist, what they show, who they serve (engineering vs executive vs on-call)
- Incident response integration — how observability data feeds into incident detection and resolution
- Partner observability standards — what the partner company must implement before their code is accepted

**Reference files to create:**

- `references/opentelemetry-setup.md` — OpenTelemetry SDK setup guide for the project's primary languages with instrumentation examples
- `references/log-standards.md` — Structured logging standards with required fields, format examples, and anti-patterns
- `references/metrics-catalogue.md` — The required metrics catalogue: service metrics, infrastructure metrics, business metrics — with naming conventions
- `references/slo-template.md` — SLI/SLO definition template with worked examples
- `references/alerting-guide.md` — Alert design principles, severity definitions, escalation paths, and anti-patterns (alert storms, alert fatigue)
- `references/dashboard-templates.md` — Specifications for required dashboards: service health, deployment dashboard, SLO dashboard, incident overview

**Trigger phrases for description:**

"observability", "OpenTelemetry", "logging", "metrics", "tracing", "SLO", "SLI", "error budget", "alerting", "dashboards", "monitoring", "SRE", "distributed tracing", "log standards", "instrumentation", "what metrics to collect", "service health"

---

#### Skill #14: API Contract Enforcer

**Skill identifier:** `api-contract-enforcer`  
**Difficulty:** 3/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 2

**What it covers:**

Once a contract is frozen (see Skill #7), this skill enforces it at runtime and in CI/CD. It validates that implementations actually honour their specs, catches breaking changes before they reach integration environments, and manages the versioning lifecycle of APIs used by both companies.

This skill is distinct from Skill #7 (which defines contracts before code) — this skill enforces contracts after code is written.

Specifically it must handle:

- Runtime contract validation — verifying that requests and responses match the OpenAPI/Protobuf/AsyncAPI spec
- Breaking change detection — automated detection of changes that break backward compatibility before they merge
- API versioning — semantic versioning for APIs, deprecation lifecycle, sunset policy
- Consumer impact analysis — when a contract change is proposed, identifying which consumers are affected and what they must change
- Contract test enforcement in CI/CD — Pact or equivalent contract tests that run on every PR
- Cross-company API audit — reviewing the partner company's APIs for contract compliance and quality
- Deprecation management — communicating deprecations to both internal and partner consumers with adequate notice

**Reference files to create:**

- `references/breaking-change-rules.md` — Comprehensive list of what constitutes a breaking vs non-breaking API change for REST, gRPC, and event schemas
- `references/versioning-policy.md` — API versioning policy: when to bump major/minor/patch, how versions are communicated, deprecation timeline
- `references/deprecation-process.md` — Step-by-step deprecation process including: notice period, migration guide requirements, sunset communication

**Scripts to create:**

- `scripts/detect_breaking_changes.py` — Takes two OpenAPI spec versions and outputs a structured report of breaking and non-breaking changes with severity ratings
- `scripts/contract_test_runner.py` — Runs contract tests against a live service and reports pass/fail with detailed mismatch information

**Trigger phrases for description:**

"API breaking change", "backward compatibility", "contract enforcement", "API versioning", "deprecate an API", "consumer impact", "API compliance", "contract test", "Pact", "API sunset", "breaking vs non-breaking", "runtime contract validation"

---

#### Skill #15: Executable Acceptance & Verification

**Skill identifier:** `executable-acceptance-verification`  
**Difficulty:** 4/5 | **Necessity:** 5/5 | **Priority:** Critical  
**Build phase:** Phase 2

**What it covers:**

In a cross-company engagement, "done" cannot be a feeling. Delivery must be accepted or rejected based on objective, pre-agreed, executable criteria. This skill converts business outcomes into runnable acceptance tests, demo scripts, quality exit gates, and formal acceptance records that both companies sign off on.

Specifically it must handle:

- Acceptance criteria conversion — turning business requirements into executable test scenarios
- Demo script design — structured scripts for milestone demonstrations that verify functionality against agreed criteria
- Release exit gates — a checklist of conditions that must all be true before a release is accepted: test pass rate, coverage, security scan clean, performance SLO met, documentation complete
- Formal acceptance records — documents that both companies sign (or formally acknowledge) to record that a milestone was accepted
- Partial acceptance — when some criteria are met and some are not, how to record, negotiate, and track what remains
- Rejection communication — formally rejecting a deliverable with specific, evidenced reasons and required remediation steps
- Acceptance test automation — making acceptance tests repeatable and automated so they can run in CI/CD

**Reference files to create:**

- `references/acceptance-criteria-to-tests.md` — Guide to converting BDD acceptance criteria into executable test code with examples
- `references/release-exit-gate.md` — The complete release exit gate checklist with pass/fail criteria for each item
- `references/formal-acceptance-template.md` — Formal milestone acceptance record template for cross-company sign-off
- `references/rejection-template.md` — Formal deliverable rejection template with required sections: criteria not met, evidence, required remediation, deadline

**Trigger phrases for description:**

"acceptance criteria", "release gate", "define done", "milestone acceptance", "reject a deliverable", "formal sign-off", "exit gate", "acceptance test", "delivery acceptance", "is this done", "verify delivery", "demo script", "acceptance record", "release readiness check"

---

#### Skill #16: Performance & Reliability Engineering

**Skill identifier:** `performance-reliability-engineering`  
**Difficulty:** 4/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 2

**What it covers:**

Non-functional requirements — performance, reliability, availability, scalability — are the requirements most often underspecified and most catastrophically discovered in production. This skill designs, validates, and enforces NFR compliance throughout development.

Specifically it must handle:

- Performance requirement definition — specific, measurable latency, throughput, and capacity targets for every critical path
- Performance baseline establishment — measuring current performance before any optimisation claim can be made
- Load test design — defining realistic load profiles (normal, peak, spike, soak) and success criteria
- Bottleneck identification — systematic approach to finding performance bottlenecks across: application code, database queries, network, infrastructure, and external dependencies
- Degradation behaviour design — how the system behaves under load it cannot fully serve (queue, shed, degrade gracefully vs fail hard)
- Fault tolerance patterns — circuit breakers, retry with backoff, bulkhead isolation, timeout design
- Recovery time objectives — how long is acceptable to recover from each failure mode, and how this is tested
- Reliability budgets — relating reliability targets to allowable failure rates
- Partner performance accountability — holding the partner company to agreed performance targets with evidence requirements

**Reference files to create:**

- `references/performance-requirements-template.md` — Template for specifying measurable performance requirements by system component and user journey
- `references/load-profile-guide.md` — How to design realistic load profiles for this type of system with example profiles
- `references/fault-tolerance-patterns.md` — Catalogue of fault tolerance patterns with implementation guidance and when to use each
- `references/performance-review-checklist.md` — Code and architecture review checklist items specifically for performance

**Trigger phrases for description:**

"performance", "latency", "throughput", "load test", "performance test", "bottleneck", "slow", "capacity", "reliability", "fault tolerance", "circuit breaker", "retry", "degradation", "NFR", "non-functional requirements", "performance target", "SLO breach", "performance review"

---

#### Skill #17: AI-Assisted Engineering & Guardrails

**Skill identifier:** `ai-assisted-engineering`  
**Difficulty:** 3/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 2

**What it covers:**

AI tools accelerate engineering but introduce new quality risks — hallucinated dependencies, subtly wrong logic, security vulnerabilities that look plausible, and documentation drift. This skill governs the integration of AI tools (Claude, GitHub Copilot, CodeLlama, custom prompt pipelines) into the engineering workflow with the guardrails, review steps, and quality controls that make AI an amplifier of good engineering rather than a source of hidden debt.

Specifically it must handle:

- AI tool selection and governance — which AI tools are approved for use, in what contexts, with what restrictions
- Prompt engineering for engineering tasks — how to write effective prompts for code generation, test generation, documentation, refactoring, and code review
- Output verification protocol — mandatory review steps for every piece of AI-generated code before it enters the codebase
- AI-specific code review checklist — what to look for in AI-generated code that human reviewers often miss (hallucinated imports, plausible-but-wrong logic, subtle security issues)
- Prohibited AI uses — what must never be generated by AI without deep expert review (cryptography, authentication, authorisation, financial calculations, safety-critical logic)
- AI-assisted documentation — using AI to generate first-draft documentation from code, specs, and comments with a review workflow
- AI-assisted test generation — generating test cases with AI and the verification steps to ensure they actually test the right thing
- AI usage disclosure — requiring engineers to declare when code was AI-generated so reviewers apply appropriate scrutiny
- Measuring AI impact — tracking whether AI tools are improving or degrading quality metrics (defect density, rework rate, review cycle time)

**Reference files to create:**

- `references/approved-tools.md` — List of approved AI tools, their approved use cases, and restrictions
- `references/prompt-library.md` — Curated prompt templates for common engineering tasks: code generation, test generation, documentation, refactoring, code review, architecture analysis
- `references/ai-review-checklist.md` — Specific review checklist for AI-generated code covering: hallucinated dependencies, logic correctness, security, performance, test quality
- `references/prohibited-uses.md` — Detailed list of prohibited AI-generated code categories with rationale and the required alternative process
- `references/ai-disclosure-policy.md` — Policy requiring disclosure of AI-generated code in commit messages and PR descriptions

**Scripts to create:**

- `scripts/check_ai_disclosure.py` — Scans recent commits and PRs for AI disclosure markers and flags non-compliant contributions
- `scripts/prompt_tester.py` — Runs a prompt template against the configured AI API and evaluates the output against a defined quality rubric

**Trigger phrases for description:**

"AI-generated code", "Copilot", "LLM", "AI tools", "prompt engineering", "code generation", "AI review", "guardrails for AI", "AI in engineering", "review AI output", "AI-assisted", "AI disclosure", "Claude for code", "AI code quality", "AI test generation", "AI documentation"

---

#### Skill #18: Release Readiness

**Skill identifier:** `release-readiness`  
**Difficulty:** 3/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 2

**What it covers:**

A release is not ready when engineering says it is. It is ready when a structured, evidence-based checklist says it is. This skill runs pre-release readiness assessments, enforces release exit criteria, coordinates cross-company release approval, and produces the release documentation package.

Specifically it must handle:

- Release readiness checklist execution — systematically verifying every release condition across: code quality, test results, security scan status, performance validation, documentation completeness, rollback readiness, monitoring readiness, stakeholder communication
- Go/No-go decision support — producing a structured go/no-go recommendation with evidence for each criterion
- Release notes generation — producing release notes that are technically accurate, business-relevant, and audience-appropriate
- Cross-company release coordination — ensuring both companies are aligned on release timing, responsibilities, and communication
- Release communication — internal and external release announcements
- Post-release verification — what must be checked in the first hours after a release to confirm it succeeded
- Rollback trigger criteria — the specific conditions that should trigger an immediate rollback

**Reference files to create:**

- `references/release-readiness-checklist.md` — The complete release readiness checklist with pass/fail criteria and evidence requirements for each item
- `references/go-nogo-template.md` — Go/No-go decision document template with sections for each criterion and a summary recommendation
- `references/release-notes-template.md` — Release notes template with sections for: highlights, changes, bug fixes, known issues, upgrade instructions
- `references/post-release-verification.md` — The first-hour verification checklist after a production release

**Trigger phrases for description:**

"release readiness", "ready to release", "go/no-go", "release checklist", "pre-release", "release gate", "is this ready to ship", "release notes", "release approval", "release coordination", "post-release check", "deploy to production check"

---

### PHASE 3 — As the Project Matures
*Build these once the project has rhythm. They instrument, improve, and sustain delivery quality.*

---

#### Skill #19: Technical Debt Tracker

**Skill identifier:** `technical-debt-tracker`  
**Difficulty:** 3/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 3

**What it covers:**

Technical debt is not a failure — it is a financial instrument. The danger is untracked, unowned, accumulating debt that silently degrades velocity and quality. This skill identifies, categorises, quantifies, and manages technical debt with enough business-facing framing that it can be prioritised alongside feature work in a cross-company context.

Specifically it must handle:

- Debt identification — recognising technical debt in code reviews, architecture reviews, retrospectives, and incident postmortems
- Debt categorisation — architecture debt, code debt, test debt, documentation debt, infrastructure debt, dependency debt, security debt
- Debt quantification — estimating the cost to fix vs the ongoing cost of leaving it (interest rate analogy)
- Debt register maintenance — a living, prioritised register of known debt items
- Business impact framing — translating technical debt into terms that non-technical stakeholders understand (delivery slowdown, incident risk, scaling ceiling)
- Debt remediation planning — sprint-level plans for addressing debt alongside feature work
- Partner company debt attribution — when debt is introduced by the partner company, documenting it clearly for contractual purposes
- Debt trend tracking — whether the debt load is growing, stable, or shrinking over time

**Reference files to create:**

- `references/debt-register-template.md` — Complete technical debt register template with all required fields
- `references/debt-categories.md` — Detailed taxonomy of debt categories with examples and typical remediation approaches for each
- `references/debt-business-framing.md` — Guide to translating technical debt into business language with example framings for common debt types

**Scripts to create:**

- `scripts/debt_report.py` — Takes a debt register (JSON or CSV) and produces a formatted summary report showing debt by category, trend over time, and top priority items

**Trigger phrases for description:**

"technical debt", "debt register", "code smell", "refactoring backlog", "debt backlog", "this is getting hard to maintain", "legacy code", "debt remediation", "debt tracking", "debt quantification", "debt trend", "interest rate on debt"

---

#### Skill #20: Delivery Metrics & DORA Instrumentation

**Skill identifier:** `delivery-metrics-dora`  
**Difficulty:** 3/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 3

**What it covers:**

You cannot manage what you do not measure. This skill defines, instruments, and interprets the engineering metrics that tell you whether the project is healthy — both for your own team and for the partner company. DORA metrics (Lead Time for Changes, Deployment Frequency, Change Failure Rate, Mean Time to Recover) are the baseline; this skill extends them with project-specific health indicators.

Specifically it must handle:

- DORA metrics definition and instrumentation — how to collect each DORA metric in this project's CI/CD and incident management systems
- DORA metric interpretation — what the numbers mean, what good looks like, and how to diagnose degradation
- Extended metrics definition — defect escape rate, test flakiness rate, review cycle time, documentation freshness, environment stability, onboarding time
- Metrics dashboard design — how metrics are displayed and to whom (engineering dashboard vs executive dashboard vs partner dashboard)
- Metric-driven decision making — how to use metrics to justify process changes, resource requests, or partner performance conversations
- Partner performance metrics — using shared metrics to objectively evidence whether the partner company is performing to expectation
- Metric gaming prevention — common ways metrics are gamed and how to detect and prevent it
- Regular metrics reviews — cadence and format for reviewing metrics with both companies

**Reference files to create:**

- `references/dora-metrics-guide.md` — Complete DORA metrics implementation guide: what each metric means, how to collect it, what good/acceptable/poor looks like, and how to improve it
- `references/extended-metrics.md` — Definition and instrumentation guide for the extended project health metrics
- `references/metrics-dashboard-spec.md` — Specification for the engineering health dashboard: what it shows, data sources, refresh frequency, audience

**Scripts to create:**

- `scripts/dora_calculator.py` — Takes deployment event logs and incident logs as input and calculates current DORA metric values with trend data
- `scripts/metrics_report.py` — Generates a formatted weekly/sprint metrics summary report

**Trigger phrases for description:**

"DORA metrics", "deployment frequency", "lead time", "MTTR", "change failure rate", "engineering metrics", "delivery metrics", "measure our engineering", "are we getting better", "velocity", "defect rate", "metrics dashboard", "partner performance metrics", "health metrics"

---

#### Skill #21: Dependency Health Management

**Skill identifier:** `dependency-health-management`  
**Difficulty:** 2/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 3

**What it covers:**

Every third-party dependency is a liability — a potential source of security vulnerabilities, licensing risk, breaking changes, or abandonment. In a cross-company context, dependency health is also a legal matter: licence incompatibilities can affect IP ownership. This skill monitors, reports, and manages the health of all project dependencies.

Specifically it must handle:

- CVE scanning — continuous scanning of all dependencies for known security vulnerabilities
- Licence compliance — checking that all dependency licences are compatible with the project's licensing requirements and the cross-company IP agreement
- EOL (End-of-Life) tracking — identifying dependencies that are no longer maintained or approaching end of support
- Dependency update management — policy for how quickly different classes of CVE must be patched, and how updates are tested and deployed
- Transitive dependency visibility — understanding not just direct dependencies but the full dependency tree
- Dependency approval process — new dependencies must be reviewed and approved before introduction, with rationale documented
- Partner dependency accountability — ensuring the partner company follows the same dependency hygiene standards
- Dependency health reporting — regular summary of dependency health for cross-company review

**Reference files to create:**

- `references/dependency-policy.md` — Complete dependency management policy: approval process, CVE response SLAs, licence allowlist/blocklist, EOL response process
- `references/licence-compatibility.md` — Guide to common open-source licence types, their compatibility with commercial projects, and red-flag licences to avoid
- `references/cve-response-sla.md` — Response time requirements by CVE severity level (Critical/High/Medium/Low) with remediation workflow

**Scripts to create:**

- `scripts/dependency_audit.py` — Runs dependency scanning tools, aggregates CVE, licence, and EOL findings, and produces a prioritised dependency health report

**Trigger phrases for description:**

"dependency", "CVE", "vulnerability", "library", "package", "npm audit", "licence", "open source licence", "EOL dependency", "dependency health", "third party", "transitive dependency", "dependency approval", "dependency scan", "dependency update"

---

#### Skill #22: Incident Postmortem & Learning

**Skill identifier:** `incident-postmortem`  
**Difficulty:** 2/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 3

**What it covers:**

Every incident is a learning opportunity. Blameless postmortems extract systemic lessons and produce actionable remediation items that prevent recurrence. In a cross-company context, postmortems also serve a documentation and accountability function — both companies must agree on what happened, why, and what each side will do about it.

Specifically it must handle:

- Blameless postmortem facilitation — guiding a postmortem that focuses on systems and processes, not individuals
- Timeline reconstruction — building an accurate incident timeline from logs, alerts, and team input
- Root cause analysis — using the Five Whys and contributing factors analysis to find systemic causes, not just proximate ones
- Contributing factors identification — technical, process, communication, and organisational factors that allowed the incident to occur
- Action item generation — concrete, owned, time-bound remediation actions that actually address the root causes
- Action item tracking — following through on postmortem actions until they are resolved
- Cross-company postmortem coordination — when an incident involves both companies, structuring a joint postmortem process
- Postmortem sharing — what is shared with the partner company and what remains internal
- Learning propagation — ensuring lessons from postmortems reach the engineers who need them, not just the ones in the room

**Reference files to create:**

- `references/postmortem-template.md` — Complete blameless postmortem template with all required sections: summary, timeline, root cause, contributing factors, action items
- `references/five-whys-guide.md` — How to facilitate a Five Whys root cause analysis effectively, with common pitfalls
- `references/blameless-culture.md` — Principles of blameless postmortem culture and how to handle situations where blame is tempting

**Trigger phrases for description:**

"postmortem", "incident review", "root cause analysis", "five whys", "what went wrong", "incident report", "blameless", "RCA", "contributing factors", "action items from incident", "learning from incidents", "incident timeline", "cross-company incident"

---

#### Skill #23: Team Coaching & Engineering Culture

**Skill identifier:** `team-coaching-engineering-culture`  
**Difficulty:** 2/5 | **Necessity:** 4/5 | **Priority:** High  
**Build phase:** Phase 3

**What it covers:**

Superbly guided code comes from engineers who understand why quality matters, not just engineers who follow rules. This skill governs the mentoring, coaching, and culture-building activities that create a high-performance engineering culture across both companies — without micromanaging.

Specifically it must handle:

- Onboarding acceleration — getting new engineers productive quickly on both sides of the engagement
- Code walkthrough rituals — structured sessions where senior engineers walk through code with juniors to transfer architectural understanding
- Pair programming governance — when pair programming is recommended, how sessions are structured, what outcomes are expected
- Style guide authoring — creating internal style guides that explain the why behind every standard, making engineers understand rather than just comply
- Engineering principles articulation — documenting the engineering values and principles that guide decision-making on this project
- Feedback culture — how to give and receive technical feedback constructively in a cross-company setting
- Cross-company knowledge transfer — ensuring both companies build capability rather than creating dependency on key individuals
- Engineering retrospectives — structuring team retrospectives that surface process issues and generate real improvements
- Recognition and growth — how to recognise quality work and support growth within the engagement constraints

**Reference files to create:**

- `references/engineering-principles-template.md` — Template for articulating project engineering principles with rationale
- `references/code-walkthrough-format.md` — How to structure and facilitate a productive code walkthrough session
- `references/feedback-guide.md` — How to give constructive technical feedback in a cross-company context at each severity level
- `references/retrospective-formats.md` — Three retrospective formats suitable for different team situations (standard sprint retro, mid-project health check, cross-company alignment retro)

**Trigger phrases for description:**

"coaching", "mentoring", "engineering culture", "code walkthrough", "pair programming", "style guide", "engineering principles", "onboarding", "feedback culture", "retrospective", "team health", "knowledge transfer", "growing engineers", "cross-company culture"

---

### PHASE 4 — Advanced Practice
*Build this last. It requires a mature engineering base to be useful.*

---

#### Skill #24: Formal Verification & Chaos Engineering

**Skill identifier:** `formal-verification-chaos-engineering`  
**Difficulty:** 5/5 | **Necessity:** 3/5 | **Priority:** Medium  
**Build phase:** Phase 4

**What it covers:**

For systems where correctness under concurrency, distributed state, and failure conditions is critical — operating systems, HCI platforms, edge AI runtimes — standard testing is insufficient. Formal verification mathematically proves that a system cannot enter certain bad states. Chaos engineering deliberately causes failures in controlled conditions to verify that the system recovers correctly. Together they provide a level of confidence beyond what any test suite can offer.

Specifically it must handle:

- TLA+ specification writing — formally modelling critical system components (consensus protocols, state machines, concurrent data structures) in TLA+
- TLA+ model checking — running the TLC model checker to verify safety and liveness properties
- Property-based testing — using tools like Hypothesis (Python) or fast-check (JS) to generate thousands of random test cases and verify system invariants
- Chaos engineering design — designing fault injection experiments for this system type (network partition, node failure, disk full, clock skew, memory pressure)
- Chaos experiment execution — safely running chaos experiments in staging with blast radius controls and monitoring
- Resilience verification — verifying that recovery time objectives are met under each fault scenario
- Cross-company chaos coordination — when chaos experiments affect partner-built components, how to design and execute them jointly

**Reference files to create:**

- `references/tla-plus-guide.md` — Introduction to TLA+ for engineers familiar with distributed systems: key concepts, specification structure, the TLC model checker, and worked examples relevant to this project type
- `references/property-based-testing.md` — How to use property-based testing in the project's languages with examples of good properties to test
- `references/chaos-experiment-catalogue.md` — A catalogue of chaos experiments appropriate for this system type, with design templates and safety controls for each
- `references/chaos-safety-controls.md` — Required safety controls for chaos experiments: blast radius limits, monitoring requirements, abort criteria, rollback procedures

**Scripts to create:**

- `scripts/chaos_experiment_runner.py` — Orchestrates a chaos experiment: injects a defined fault, monitors system behaviour, verifies recovery, and produces a structured experiment report
- `scripts/property_test_generator.py` — Takes a module description and generates a skeleton of property-based tests with common invariants pre-populated

**Trigger phrases for description:**

"TLA+", "formal verification", "model checking", "chaos engineering", "fault injection", "resilience testing", "property-based testing", "distributed systems correctness", "state machine verification", "chaos experiment", "blast radius", "network partition test", "race condition prevention", "Hypothesis", "fast-check"

---

## Part 4 — Build Order and Phase Summary

| Phase | Skills to Build | When |
|-------|----------------|------|
| Phase 1 | #1 Project Governance, #2 Architecture Review, #3 ADRs, #4 Requirements Tracer, #5 Risk Management, #6 Inter-Company Communications, #7 Specification-Driven Dev, #8 Security Audit | Before any code is written |
| Phase 2 | #9 Code Review, #10 Test Strategy, #11 DevOps/CI-CD, #12 Documentation System, #13 Observability/SRE, #14 API Contract Enforcer, #15 Executable Acceptance, #16 Performance Engineering, #17 AI-Assisted Engineering, #18 Release Readiness | During active development |
| Phase 3 | #19 Technical Debt, #20 DORA Metrics, #21 Dependency Health, #22 Incident Postmortem, #23 Team Coaching | Once the project has rhythm |
| Phase 4 | #24 Formal Verification & Chaos | When system complexity demands it |

---

## Part 5 — Global Quality Checklist

Before considering any skill complete, verify:

- [ ] SKILL.md frontmatter has `name` and `description` fields, description is detailed and trigger-rich
- [ ] SKILL.md body is under 500 lines; overflow goes to reference files
- [ ] Every reference file mentioned in SKILL.md actually exists and is complete
- [ ] Every script mentioned in SKILL.md actually exists and runs without errors
- [ ] Output format is explicitly defined with a template
- [ ] Severity ratings are defined for any skill that produces findings
- [ ] Cross-company context is addressed — the skill handles the dual-company scenario
- [ ] Trigger phrases cover: direct requests, adjacent scenarios, and cases where the user describes the problem without naming the skill
- [ ] No placeholder content anywhere — every section is production-ready
- [ ] Imperative form used throughout — "Review the X", not "You should review the X"
- [ ] The why is explained for every major instruction
- [ ] All templates include example content, not just field labels

---

*End of Master Skill Build Prompt*  
*Total skills: 24 | Phases: 4 | Build order: Phase 1 → 2 → 3 → 4*
