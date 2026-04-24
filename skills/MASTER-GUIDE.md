# Master guide: when and how to use each skill

This guide explains every skill in the library — what it does, when to trigger it, what situations call for it, and what you get out of it. Use this as your first reference when a situation arises and you are not sure which skill applies.

---

## How to read this guide

Each entry answers four questions:

1. **What it is** — the core purpose of the skill
2. **When to use it** — the specific situations, triggers, and signals that call for this skill
3. **When NOT to use it** — adjacent situations that belong to a different skill
4. **What you get** — the concrete output the skill produces

---

## Phase 1 — Foundation and governance

These skills apply from day one of the engagement. They establish the framework within which everything else operates. If these are weak, everything downstream suffers.

---

### 1. Stakeholder sync
`phase1/stakeholder-sync/`

**What it is:** Async-first guidance for keeping external stakeholders aligned without ceremony — decision logging, scope change handling, status cadence, and lean escalation for a 3–5 person team.

**When to use it:**
- When drafting a status update, risk notification, or scope change communication to a client or external stakeholder
- When a decision is being made that stakeholders need to know about — log it
- When scope is proposed to expand or contract — use the scope change record
- When a disagreement is escalating and you need to decide who can unblock it
- When setting up a communication cadence for a project (async-first, sync only when stuck)
- At project kickoff: establish how decisions and scope changes will be communicated

**When NOT to use it:**
- Technical design decisions → architecture-decision-records
- API contract decisions → specification-driven-development
- Active production incidents → incident-postmortem
- Internal team process retrospectives → team-coaching-engineering-culture

**What you get:** Decision log entries, scope change records with impact analysis, status update drafts, lean escalation path, communication cadence setup.

---

### 2. Architecture review governance
`phase1/architecture-review-governance/`

**What it is:** The process and criteria for reviewing system architecture — both at design time and as the system evolves.

**When to use it:**
- Before any new service is built: run the architecture review checklist
- When reviewing a proposed design systematically before committing to it
- When reviewing a proposal that involves a new data store, a new service boundary, or a new integration pattern
- When you suspect architectural drift (what is deployed no longer matches what was designed)
- When NFRs (latency, throughput, availability) need to be formally defined and validated
- When choosing between architectural approaches: use the trade-off frameworks
- When an anti-pattern is suspected: distributed monolith, shared database, synchronous call chains without fallbacks
- During quarterly architecture health reviews

**When NOT to use it:**
- Individual PR code review → code-review-quality-gates
- Documenting a specific decision already made → architecture-decision-records
- Testing that the architecture performs to NFRs → performance-reliability-engineering

**What you get:** Architecture review report (via `review_report.py`), NFR templates, anti-pattern checklist, trade-off framework analysis.

---

### 3. Architecture decision records
`phase1/architecture-decision-records/`

**What it is:** The practice of documenting significant technical decisions as permanent records with context, alternatives considered, and consequences.

**When to use it:**
- Any time a significant technical choice is made that future engineers need to understand (technology selection, architecture pattern, security approach)
- When a design review produces a decision that needs to be recorded
- When onboarding a new team member who asks "why was X chosen?"
- When a past decision is being reconsidered — check whether an ADR already covers it
- When a vendor or external team makes a design decision that affects your systems
- At project handover: ensure all major decisions are recorded so the receiving team is not operating blind

**When NOT to use it:**
- Day-to-day technical discussions that do not produce a lasting decision
- Process decisions (meeting cadences, scope changes) → stakeholder-sync
- Documenting how to operate a system → documentation-system-design (runbooks)

**What you get:** Formatted ADR documents following the standard template, an ADR index for the project, and examples of good vs bad ADRs to calibrate quality.

---

### 4. Requirements tracer
`phase1/requirements-tracer/`

**What it is:** The framework for decomposing requirements into BDD acceptance criteria and verifying end-to-end traceability from requirement to test to code.

**When to use it:**
- When converting a business requirement into BDD acceptance criteria (Given/When/Then)
- When you need to verify that every requirement has a corresponding test and code module
- When a scope change is proposed: run scope impact analysis to understand what is affected
- When a deliverable milestone is approaching and you want evidence that all requirements are covered
- When there is a dispute about whether a feature is complete: trace from requirement to test
- When features are being built without clear traceability to the requirements that justify them
- Run `check_orphans.py` regularly to detect requirements with no tests, or tests with no requirements

**When NOT to use it:**
- Writing the acceptance tests themselves → executable-acceptance-verification
- Tracking which requirements made it into the product roadmap (product management)

**What you get:** Traceability matrix (Req ID → Feature → Story → Code → Test), acceptance criteria in BDD format, scope impact analysis, orphan detection report via `check_orphans.py`.

---

### 5. Technical risk management
`phase1/technical-risk-management/`

**What it is:** The structured process for identifying, rating, tracking, and responding to technical risks before they become incidents.

**When to use it:**
- At engagement kickoff: populate the risk register with known risks
- Any time a new technical risk is identified (architecture decision, dependency choice, timeline pressure, key person dependency)
- When making a go/no-go decision on a release: consult the risk register
- Monthly: review and update risk scores
- When a risk materialises into an incident: update status and trigger incident post-mortem
- When defining kill criteria: what conditions would justify stopping the project?

**When NOT to use it:**
- Risks that have already materialised → incident-postmortem
- Security-specific vulnerabilities → security-audit-secure-sdlc
- Dependency CVEs specifically → dependency-health-management

**What you get:** Risk register, P×I scoring, risk report via `risk_report.py`, kill criteria definitions, risk category taxonomy.

---

### 6. Specification-driven development
`phase1/specification-driven-development/`

**What it is:** The contract-first approach to API design — write and agree the specification before any implementation begins.

**When to use it:**
- At the start of any new REST API: design the OpenAPI spec first
- At the start of any new gRPC service: design the Protobuf spec first
- When designing Kafka topics, NATS subjects, event-driven microservices, or IoT telemetry streams: use the AsyncAPI spec first
- When adding new event types to existing systems: define the channel schema before publishing
- At the start of any new GraphQL API: write the `.graphql` schema file before any resolver code
- When making GraphQL schema changes: use the deprecation workflow before removing fields
- When reviewing a spec delivered by a vendor or external team for completeness and correctness
- When preparing to freeze a contract: use the contract review checklist and freeze process
- When a contract change is proposed after freeze: run `diff_contracts.py` to classify as breaking/non-breaking
- When validating that a spec meets quality standards: run `validate_openapi.py` in CI

**When NOT to use it:**
- Verifying that the implementation matches the spec (at runtime) → api-contract-enforcer
- Consumer-driven contract tests (Pact) → api-contract-enforcer

**What you get:** OpenAPI, Protobuf, AsyncAPI, and GraphQL worked examples; GraphQL schema design rules (nullable/non-null, DataLoader, flat mutations, federation); event-driven contract workflow (message envelope, delivery guarantee, schema evolution rules); contract review checklist; contract freeze process; `validate_openapi.py` and `diff_contracts.py` scripts.

---

### 7. Security audit and secure SDLC
`phase1/security-audit-secure-sdlc/`

**What it is:** The end-to-end security programme — from threat modelling at design time to supply chain controls to security gates in CI/CD.

**When to use it:**
- At design time for every new service: run STRIDE threat modelling (including AI-specific attack surfaces for any LLM features)
- During code review: apply the secure coding checklist for security-specific concerns
- When setting up or reviewing CI/CD pipelines: verify security gates and GitHub Actions hardening
- When releasing: generate SBOM (`syft`), scan vulnerabilities (`grype`), sign container images (`cosign`)
- When auditing a code deliverable for security issues
- When mapping your security controls to NIST SSDF or OWASP Top 10 for compliance
- When reviewing secrets management implementation
- When adding new dependencies: verify package name, provenance, and pin to exact hash

**When NOT to use it:**
- CVE management in existing dependencies → dependency-health-management
- Pipeline configuration review generally → devops-pipeline-governance
- Security incidents that have already occurred → incident-postmortem

**What you get:** STRIDE threat model template with AI-specific threats, secure coding standards, supply chain security guide (SBOM/Sigstore/typosquatting), CI/CD security hardening (OIDC, SHA-pinned actions, secret scanning), container security patterns, NIST SSDF mapping table.

---

### 36. Data governance and privacy
`phase1/data-governance-privacy/`

**What it is:** A systematic approach to data classification, Privacy Impact Assessments, GDPR/CCPA compliance workflows, data retention, and EU AI Act data transparency (Article 10, 13).

**When to use it:**
- When new data collection is being introduced (new fields, new event types, new user inputs)
- When new third-party data sharing is proposed (vendor integration, analytics SDK, processor agreement)
- When ML or LLM training is planned on user data — scope the lawful basis and transparency obligations before training starts
- During the annual retention review: verify every data type has a retention rule and that deletion actually runs
- When entering new jurisdictions (new region launch, new customer base) — confirm applicable privacy law coverage
- When a Subject Access Request (SAR) or erasure request arrives — follow the runbook end to end

**When NOT to use it:**
- Security threats (credential theft, injection, exfiltration as an attack) → security-audit-secure-sdlc
- Non-privacy technical risks (architecture, dependency, timeline) → technical-risk-management
- External stakeholder communication about a privacy matter → stakeholder-sync
- Data dictionaries and schema documentation → documentation-system-design

**What you get:** 4-tier data classification schema, completed Privacy Impact Assessment document, retention policy per data type, SAR/erasure runbook with response templates.

---

## Phase 2 — Delivery quality

These skills govern the day-to-day engineering process. They apply continuously throughout the engagement, every sprint, every PR, every deployment.

---

### 8. Code review and quality gates
`phase2/code-review-quality-gates/`

**What it is:** The standards and process for reviewing code quality — within the team and when accepting external deliverables.

**When to use it:**
- Every PR: apply the review checklist
- When accepting an external code deliverable: run the formal review process
- When recurring defect types suggest a systemic quality problem
- When calibrating review standards across the team
- When the review process is too slow (use SLA table to set expectations)

**When NOT to use it:**
- Architecture-level issues in a PR → architecture-review-governance
- Security-specific review → security-audit-secure-sdlc (use its checklist alongside this one)
- Acceptance of a complete milestone (multiple PRs/deliverables) → executable-acceptance-verification

**What you get:** PR review checklist, comment severity labels (Blocking/Suggestion/Question/Nitpick), review SLA table, code acceptance process, defect trend tracking format.

---

### 9. Comprehensive test strategy
`phase2/comprehensive-test-strategy/`

**What it is:** The complete testing framework — test pyramid ratios, each test layer defined, performance testing, LLM/AI feature testing, and test reporting.

**When to use it:**
- At the start of a project: agree the test strategy and pyramid ratios
- When test coverage is disputed
- When designing a new service: determine what tests are needed and at which layer
- When integration tests are failing intermittently: diagnose whether the issue is test design or system design
- When planning a performance test before a major release
- When building any LLM or AI feature: apply the eval-based testing pattern

**When NOT to use it:**
- Writing specific acceptance test scenarios → executable-acceptance-verification
- Setting up CI pipeline gates around tests → devops-pipeline-governance
- Contract tests between services specifically → api-contract-enforcer

**What you get:** Test pyramid guidance, unit/integration/contract/acceptance/performance test examples, LLM eval harness pattern (golden datasets, LLM-as-judge, prompt regression), k6 load test template, test environment strategy, test reporting format.

---

### 10. DevOps pipeline governance
`phase2/devops-pipeline-governance/`

**What it is:** The design, standards, and security controls for CI/CD pipelines.

**When to use it:**
- Designing a new CI/CD pipeline for a service
- Reviewing a pipeline configuration for security and quality
- When a deployment strategy needs to be chosen (blue-green vs canary vs rolling)
- When setting up IaC pipeline governance (Terraform plan/apply approval process)
- When a deployment fails and rollback procedures need to be followed
- When pipeline security is a concern (secrets in CI, third-party action pinning, feature flags)
- When a pipeline is taking too long and stages need to be reordered for fail-fast behaviour

**When NOT to use it:**
- Security gates within the pipeline (what the gates check) → security-audit-secure-sdlc
- Release sign-off and go/no-go decisions → release-readiness
- What tests run in the pipeline → comprehensive-test-strategy

**What you get:** Standard pipeline stage diagram, deployment strategy patterns (blue-green, canary, feature flags), IaC pipeline design, rollback procedures, pipeline security checklist, pipeline review format.

---

### 11. Documentation system design
`phase2/documentation-system-design/`

**What it is:** The standards and templates for operational documentation — system context diagrams, runbooks, API guides, and handover documents.

**When to use it:**
- Before a production deployment: verify runbooks exist for all P1/P2 scenarios
- When evaluating documentation quality as part of a milestone acceptance
- When a new service is being handed over to another team
- When onboarding a new engineer who needs to understand a system
- When an on-call engineer cannot diagnose an incident because runbooks are absent or wrong

**When NOT to use it:**
- Architecture decisions (ADRs) → architecture-decision-records
- API contract specification → specification-driven-development
- Post-incident findings → incident-postmortem

**What you get:** C4 context diagram examples, runbook template, API usage guide template, operational handover document template, documentation quality checklist.

---

### 12. Observability and SRE practice
`phase2/observability-sre-practice/`

**What it is:** The three-pillar observability framework (metrics, logs, traces), SLO/error budget management, and alerting standards.

**When to use it:**
- When instrumenting a new service: ensure all three pillars are covered
- When an SLO needs to be defined: use the template and recommended SLOs for the platform
- When error budget is burning faster than expected: trigger the budget consumption response
- When setting up alerting: apply the alerting standards (every alert must be actionable, have a runbook)
- When reviewing a new service's observability implementation for production readiness
- When investigating a production incident: use metrics, logs, and traces together

**When NOT to use it:**
- DORA metric calculation in depth → delivery-metrics-dora
- Incident investigation and RCA → incident-postmortem
- Production readiness sign-off → release-readiness

**What you get:** Prometheus metric examples, structured logging patterns, OpenTelemetry trace setup, SLO templates, Prometheus alert rules, SLO review report format.

---

### 13. API contract enforcer
`phase2/api-contract-enforcer/`

**What it is:** The runtime enforcement of API contracts — consumer-driven contract tests, schema registry compatibility, contract drift detection.

**When to use it:**
- When setting up Pact contract tests between the team's consumers and external provider services
- When something breaks at an integration boundary: determine if it is a contract violation or implementation bug
- When running the daily contract drift check in CI
- When an upstream service deploys a change and consumers start failing
- When schema registry compatibility rules need to be enforced for Kafka topics

**When NOT to use it:**
- Designing the API contract (spec-first) → specification-driven-development
- Comparing two spec versions for breaking changes → `diff_contracts.py` in specification-driven-development
- Acceptance testing a full feature → executable-acceptance-verification

**What you get:** Pact consumer and provider test examples, schema registry compatibility setup, runtime validation middleware, contract drift detection CI workflow, contract violation response procedure.

---

### 14. Executable acceptance verification
`phase2/executable-acceptance-verification/`

**What it is:** The framework for turning acceptance criteria into executable BDD tests and running formal milestone sign-offs.

**When to use it:**
- When converting a user story's acceptance criteria into runnable Gherkin scenarios
- When a milestone is approaching and "done" needs to be objectively verified
- When there is a dispute about whether a feature is complete
- When setting up the acceptance test suite for the engagement
- When a feature passes unit and integration tests but behaviour under realistic conditions is untested

**When NOT to use it:**
- Unit or integration tests → comprehensive-test-strategy
- Contract tests → api-contract-enforcer
- Performance acceptance → performance-reliability-engineering

**What you get:** Complete feature file examples, step definition patterns, pytest-bdd setup, test tagging strategy, acceptance sign-off document template.

---

### 15. Performance and reliability engineering
`phase2/performance-reliability-engineering/`

**What it is:** The complete performance testing and reliability pattern toolkit — from NFR definition to load tests to circuit breakers.

**When to use it:**
- When defining performance NFRs: use the template to make them specific and measurable
- Before a major production release: run load and stress tests
- When a production latency regression is detected: use the analysis patterns
- When designing a service that calls external dependencies: implement circuit breaker, retry, bulkhead
- When capacity planning: use the capacity model

**When NOT to use it:**
- SLO definition and error budget management → observability-sre-practice
- Chaos engineering for resilience → chaos-engineering (phase 3)
- Pipeline performance gates → devops-pipeline-governance

**What you get:** NFR templates, k6 load/stress/soak test scripts, performance anti-pattern catalogue (N+1, sync calls, missing indexes), reliability patterns (circuit breaker, retry, bulkhead, timeout), capacity model, performance test results format.

---

### 16. AI-assisted engineering
`phase2/ai-assisted-engineering/`

**What it is:** Practical governance for using AI coding tools effectively and safely — trust tiers, AI code security review, prompt engineering patterns, and Claude as a pipeline-integrated tool.

**When to use it:**
- When establishing which AI tools to use for which tasks (trust tier assignment)
- When reviewing code that may have been AI-generated — apply the AI-specific security checklist
- When an engineer is getting poor results from AI tools — use the prompt patterns
- When integrating Claude Code into the SDLC pipeline (which stage, which MCP servers)
- When building AI features and needing a security review of the AI-specific attack surfaces
- When setting up MCP server integrations (GitHub, Slack, Jira) within Claude Code

**When NOT to use it:**
- General code review → code-review-quality-gates (use the AI checklist as a supplement)
- Testing AI features (evals, prompt regression) → comprehensive-test-strategy
- Security review of AI attack surfaces (prompt injection, supply chain) → security-audit-secure-sdlc

**What you get:** Trust tier table (Claude Code agentic / Cursor inline / human-only), SDLC stage mapping (where Claude adds value at each stage), MCP integration setup guide, AI code security checklist (hallucinated APIs, insecure defaults, outdated patterns, over-permissive code), prompt pattern library.

---

### 17. LLM application development
`phase2/llm-app-development/`

**What it is:** The engineering discipline for building software products that call an LLM internally — eval-driven development, prompt versioning, pipeline pattern selection, RAG design, agent tool design, failure mode mitigations, and production LLM monitoring.

**When to use it:**
- Adding an LLM call to a service (summarisation, classification, extraction, generation)
- Designing or implementing a RAG pipeline
- Building an agent that calls external tools via function-calling
- Setting up an eval harness for a new or existing LLM feature
- Choosing between LLM pipeline patterns (single-shot / chain / router / orchestrator-worker)
- Defining production monitoring for LLM calls (latency, cost, quality score)
- Conducting prompt A/B tests or versioning a prompt change

**When NOT to use it:**
- Using AI tools to help write code faster → ai-assisted-engineering
- Defining the test strategy for an LLM feature that already exists → comprehensive-test-strategy
- Security threat modelling for AI-specific attacks → security-audit-secure-sdlc

**What you get:** Eval harness (golden dataset format, LLM-as-judge, CI gate), prompt versioning structure (file layout, promotion checklist, A/B test process), pipeline pattern selection guide (single-shot/chain/router/orchestrator-worker), RAG design guide (chunking strategies, embedding model selection, recall@k/MRR measurement, reranking), agent tool design rules, failure mode table (hallucination/prompt injection/context overflow/cost runaway), production monitoring spec.

---

### 18. Release readiness
`phase2/release-readiness/`

**What it is:** The systematic verification that all conditions are met before a production deployment — checklist, go/no-go process, and deployment plan.

**When to use it:**
- Before every production release: run the release readiness checklist
- When a release requires formal sign-off: use the go/no-go meeting format
- When planning a release with complex coordination (database migrations, partner dependencies, canary deployment)
- When verifying post-release that the deployment succeeded and no regressions occurred

**When NOT to use it:**
- Building the pipeline that executes the deployment → devops-pipeline-governance
- Deciding whether quality gates pass → code-review-quality-gates, comprehensive-test-strategy
- The performance test that is a pre-release gate → performance-reliability-engineering

**What you get:** Release readiness checklist (code+build+tests, database and data, rollback), go/no-go meeting format, deployment plan template, post-release checklist, release readiness report.

---

### 19. Feature flag lifecycle
`phase2/feature-flag-lifecycle/`

**What it is:** The full lifecycle for feature flags — creating, rolling out, monitoring, and removing flags before they become permanent debt.

**When to use it:**
- When merging an incomplete feature to main (release flag)
- When planning a gradual rollout or A/B test (experiment flag)
- When adding a kill switch for a risky feature (ops flag)
- When doing a monthly flag debt audit — any flag without an expiry or owner is debt
- When removing a flag that has been 100% on for 30+ days

**When NOT to use it:**
- Environment-specific configuration → use environment variables instead
- Permanent per-tenant feature gating (these are permission flags with a different lifecycle)
- Pipeline deployment strategies (blue-green, canary) → devops-pipeline-governance

**What you get:** Flag type taxonomy (release/experiment/ops/permission), 5-step lifecycle process (create → implement → roll out → monitor → remove), flag registry format (YAML and Markdown table), naming conventions (`release_`, `exp_`, `ops_`, `perm_` prefixes), monthly debt detection script.

---

### 20. Accessibility
`phase2/accessibility/`

**What it is:** WCAG 2.2 AA compliance mapped to development tasks — a 15-minute PR checklist, axe-core automated scanning in CI, keyboard and screen-reader testing, and the legal context (EU Accessibility Act, ADA) that makes accessibility non-negotiable for any customer-facing surface.

**When to use it:**
- Any customer-facing web or mobile UI being built or modified
- PR review of a component that renders to a user
- Setting up CI gates (axe-core) so accessibility regressions fail the build like any other test
- When evaluating an existing product against WCAG 2.2 AA before a release that triggers regulatory exposure (EU Accessibility Act, ADA)
- Onboarding a new engineer into the accessibility discipline and checklist
- When a customer or auditor raises an accessibility complaint and you need a structured remediation path

**When NOT to use it:**
- Purely internal tools with no external users — apply judgement; the full checklist may be overkill
- Design system decisions about colour and typography — upstream of this skill; feed their output in
- General UX polish unrelated to accessibility → product design, not this skill
- Legal interpretation of accessibility law beyond the practitioner summary → qualified legal counsel

**What you get:** 15-minute PR accessibility checklist, axe-core CI integration (GitHub Actions snippet), keyboard-navigation and screen-reader testing procedure, WCAG 2.2 AA criteria mapped to dev tasks, legal context summary (EU Accessibility Act, ADA), remediation prioritisation framework.

---

### 21. Architecture fitness functions
`phase2/architecture-fitness/`

**What it is:** Automated, CI-enforced architecture rules — import boundary enforcement, third-party dependency budgets, dead code detection, and coverage floors. The mechanism that prevents architectural drift between review cadences by failing the build when a rule is violated.

**When to use it:**
- When `architecture-review-governance` produces rules that must hold (module X never imports module Y, no circular imports, dependency count capped) — encode them here
- When setting up a new service: add `check_imports.py`, `dep_budget.py`, and `dead_code.py` to CI
- When architecture drift keeps being detected in quarterly reviews despite agreements — move enforcement from human review into CI
- When a new third-party dependency is proposed and the dependency budget needs to be checked
- When a module has not been touched or covered by tests in months — `dead_code.py` flags it for deletion or adoption

**When NOT to use it:**
- Human design review of a new architecture → `architecture-review-governance` (produces the rules; this skill enforces them)
- Writing the architecture decision itself → `architecture-decision-records`
- Runtime enforcement of API contracts → `api-contract-enforcer`
- General code quality linting (style, formatting) → language-specific linters in the CI pipeline, not this skill

**What you get:** `check_imports.py` (boundary and circular-import enforcement), `dep_budget.py` (third-party dependency count against configured budget), `dead_code.py` (coverage + git log cross-reference to surface abandoned modules), CI workflow snippets that fail the build on violation, configuration format for boundary rules and budgets.

---

### 37. Distributed systems patterns
`phase2/distributed-systems-patterns/`

**What it is:** Decision framework and worked patterns for multi-service and event-driven systems — sagas, event sourcing, CQRS, transactional outbox, idempotency keys, and consistency models.

**When to use it:**
- When designing or implementing a cross-service transaction (two or more services must succeed together)
- When events must be delivered at-least-once and consumers must handle duplicates safely
- When eventual consistency is acceptable and you need a pattern that makes that explicit
- When the domain is audit-heavy and event sourcing is being considered
- When a write path needs to remain responsive while a read path is derived asynchronously (CQRS)

**When NOT to use it:**
- General architecture review of a service boundary → architecture-review-governance
- API schema design and contract freeze → specification-driven-development
- Correctness proofs for a custom protocol → formal-verification
- In-process reliability patterns (retry, circuit breaker, bulkhead) → performance-reliability-engineering

**What you get:** Pattern selection decision (saga vs 2PC vs outbox, orchestration vs choreography), saga skeleton (orchestrator and choreography variants), transactional outbox DDL and dispatcher, idempotency key handler with storage schema.

---

### 38. Disaster recovery
`phase2/disaster-recovery/`

**What it is:** RTO/RPO tier definitions, backup strategy (3-2-1, immutable), multi-region failover patterns, DR drill runbooks, and restore verification.

**When to use it:**
- Any system with an availability SLA — assign a DR tier and document the plan
- Pre-launch for any customer-facing system: confirm backups, restore path, and failover are real, not assumed
- After a ransomware or outage event in the industry — re-verify that your own plan would have held
- For compliance audits that require DR evidence (SOC 2, GDPR Art. 32)

**When NOT to use it:**
- SLO and availability measurement → observability-sre-practice
- Fault injection and resilience experiments → chaos-engineering
- An active incident — mitigate first, then post-mortem → incident-postmortem
- Normal-operations reliability patterns → performance-reliability-engineering

**What you get:** DR tier classification table (RTO/RPO per tier), DR plan document, DR drill calendar, restore-verification checklist with success criteria.

---

### 39. Caching strategy
`phase2/caching-strategy/`

**What it is:** Cache layer design, pattern selection (cache-aside, read-through, write-through, write-behind, refresh-ahead), invalidation strategies, CDN configuration, and stampede prevention.

**When to use it:**
- When designing or debugging any caching layer (application, distributed, edge)
- When repeated database queries dominate latency and a cache is the obvious relief
- When introducing edge caching (CDN) for static or semi-static content
- When cache stampedes are observed in production — pick a prevention mechanism and deploy it

**When NOT to use it:**
- Capacity planning and load testing of the overall system → performance-reliability-engineering
- Schema or index changes in the underlying database → database-migration
- Setting up cache hit/miss metrics and dashboards → observability-sre-practice

**What you get:** Cache layer decision (where to cache), pattern selection (which pattern per data type), invalidation plan (TTL, event-driven, version key), CDN config, stampede prevention mechanism (single-flight, probabilistic early expiration, lock).

---

## Phase 3 — Sustained operations

These skills apply once the system is live and the engagement is in an ongoing operational phase. They keep quality, delivery, and team health from degrading over time.

---

### 22. Technical debt tracker
`phase3/technical-debt-tracker/`

**What it is:** The framework for making technical debt visible, categorised, prioritised, and managed as a first-class concern.

**When to use it:**
- When starting work on an unfamiliar codebase: conduct a debt assessment
- When delivery velocity is degrading and the cause is unclear: check debt accumulation
- Monthly: review and reprioritise the debt register
- When making the case to stakeholders for time allocated to debt reduction
- When a new team takes over a codebase and needs to understand its liabilities

**When NOT to use it:**
- Active security vulnerabilities (treat as risks, not debt) → technical-risk-management
- CVEs in dependencies → dependency-health-management
- Architecture concerns in a new design → architecture-review-governance

**What you get:** Debt taxonomy (7 types, 2 intentionality dimensions), debt item format with example, prioritisation scoring model, debt budget allocation guidance, register summary format, debt thresholds and escalation triggers.

---

### 23. Delivery metrics and DORA
`phase3/delivery-metrics-dora/`

**What it is:** The measurement framework for delivery performance — DORA metrics defined, collected, and reported, with cold-start guidance for new projects.

**When to use it:**
- When leadership asks "how well is the team delivering?" — provide DORA metrics, not anecdote
- Monthly: calculate and report the four DORA metrics
- When delivery velocity has dropped and you need data to diagnose why
- When setting contractual performance targets for the engagement
- At project start (month 0): instrument deployments and incidents immediately so data exists by month 3
- When you have fewer than 20 deployments: use the proxy metrics defined in the cold-start section

**When NOT to use it:**
- SLO and reliability metrics → observability-sre-practice
- Sprint velocity and backlog tracking (Jira/Linear metrics) — not in scope of this skill

**What you get:** DORA metric definitions with SQL queries, cold-start guide (proxy metrics for weeks 1–8, minimal Postgres DDL, when to switch to real DORA), performance band tables (Elite/High/Medium/Low), monthly delivery report template, quarterly delivery review format.

---

### 24. Dependency health management
`phase3/dependency-health-management/`

**What it is:** The ongoing programme for keeping third-party dependencies secure, current, and healthy.

**When to use it:**
- Monthly: run the dependency audit and CVE scan for all services
- When a new CVE is disclosed: use the impact assessment and triage process
- When a framework or runtime is approaching end-of-life: start the upgrade project
- When generating SBOMs for a release
- Quarterly: review the dependency health report and update the EOL watch list

**When NOT to use it:**
- Dependency security in new code (at PR time) → security-audit-secure-sdlc (Gate 3)
- Application-level technical debt → technical-debt-tracker

**What you get:** Dependency audit process (per language), CVE triage priority table, EOL planning rules and key dates, SBOM generation commands, major version upgrade project template, dependency health report format.

---

### 25. Incident post-mortem
`phase3/incident-postmortem/`

**What it is:** The blameless post-incident review process — timeline reconstruction, 5 Whys root cause analysis, action items.

**When to use it:**
- After every P1 incident (mandatory)
- After every P2 incident (mandatory)
- After P3 incidents that recur or reveal systemic issues
- When a security breach or near-miss occurs
- When action items from prior post-mortems are not being followed up

**When NOT to use it:**
- During an active incident (focus on mitigation first)
- Proactive risk identification → technical-risk-management
- Ongoing operational monitoring → observability-sre-practice

**What you get:** Incident severity classification, incident communication templates, full post-mortem document structure, blameless facilitation guide, action item tracking format.

---

### 26. Team coaching and engineering culture
`phase3/team-coaching-engineering-culture/`

**What it is:** Quarterly tools for tracking team health, distributing knowledge, maintaining engineering norms, and setting measurable growth goals — for a small senior team where culture problems manifest as delivery problems.

**When to use it:**
- Quarterly: run the structured retro, produce the Team Health Snapshot, update Growth Plans
- When the same quality problems recur despite technical fixes — the root cause may be cultural
- When a single engineer is the only person who knows a critical system (knowledge concentration risk)
- When Engineering Norms need updating after a recurring friction point
- When onboarding a new engineer into the team's standards

**When NOT to use it:**
- Individual engineer performance issues — HR matter, not engineering governance
- DORA metrics and delivery performance → delivery-metrics-dora
- Post-incident review → incident-postmortem
- Specific technical standards → the relevant technical skill

**What you get:** 45-minute quarterly retro format, Team Health Snapshot template (velocity, quality signals, satisfaction, risks, action items), per-person Growth Plan with measurability requirement, Engineering Norms Doc update process.

---

### 27. Chaos engineering
`phase3/chaos-engineering/`

**What it is:** Hypothesis-driven experiments that validate system resilience under real failure conditions — fault injection in CI, regular game days, and steady-state discipline.

**When to use it:**
- When circuit breakers, retries, and fallbacks have been implemented but never tested under real failure conditions
- Before a major launch or high-traffic event: run the chaos experiment catalogue
- Quarterly: run the standard experiment set and report results
- When a game day is needed to validate that the team can actually execute the runbooks
- When a new dependency is added that becomes a potential single point of failure

**When NOT to use it:**
- Standard load and performance testing → performance-reliability-engineering
- Designing the resilience patterns themselves → performance-reliability-engineering
- Formal protocol correctness proofs → formal-verification (phase 4)

**What you get:** Chaos experiment template (hypothesis, steady state, failure condition, scope, abort conditions, result), 5 standard experiments (pod failure, dependency outage, DB slow query, Kafka partition, network partition), Toxiproxy/Istio/k6 configurations, game day planning guide (quarterly, 2–3 hours).

---

### 28. Project closeout
`phase3/project-closeout/`

**What it is:** The formal end-of-project process — everything between "deployed and stable" and "project closed". Covers documentation audit, deliverables sign-off, knowledge transfer, operational handover, DORA final report, and lessons learned.

**When to use it:**
- When a project or contract engagement is wrapping up and needs formal closure
- When handing the system to a sustaining or operations team
- When verifying that operations can run the system without the original engineers present
- When a major release version closes and moves to maintenance mode
- When a lessons-learned session is overdue after a multi-month engagement

**When NOT to use it:**
- Post-incident review → incident-postmortem (covers a specific failure event, not a project ending)
- DORA metrics mid-project → delivery-metrics-dora standalone
- Ongoing health checks after closure → observability-sre-practice or technical-debt-tracker
- Sprint retrospectives → these are per-sprint, not engagement-level

**What you get:** Six-step closeout process (documentation audit, deliverables sign-off, knowledge transfer, operational handover, DORA final report, lessons learned); completed closeout summary format; full checklist in `references/closeout-checklist.md` suitable as a PR checklist or ticket description.

---

### 29. Cloud cost governance
`phase3/cloud-cost-governance/`

**What it is:** Infrastructure cost as a first-class engineering concern — cost attribution via mandatory IaC tagging, per-feature cost estimates in PRDs, monthly 30-minute optimization audit, budget alerts with a defined response, and a cost anomaly playbook. Cloud-specific (AWS, GCP, Azure).

**When to use it:**
- Every new service: define the tag policy and produce a cost estimate before the first resource is created
- Every PRD (Standard or Rigorous mode): include a cost NFR at design time
- Pre-release cost gate: estimate monthly cost at expected load before production deployment
- Monthly: run the 30-minute optimization audit (right-sizing, reserved capacity, orphaned resources, data-transfer review)
- Immediately: respond when a budget alert fires or when a bill spike appears — use the anomaly response playbook

**When NOT to use it:**
- On-premise infrastructure — different tooling, different economics
- FinOps for organisations with 100+ services — use dedicated FinOps tooling at that scale
- Software license and SaaS subscription costs — procurement, not cloud cost engineering
- Cost reduction that crosses an SLO boundary — that is a reliability decision, not a cost decision alone
- Technical debt (code or architecture issues that happen to inflate cost) → `technical-debt-tracker`. Cloud cost governance is infrastructure cost only.

**What you get:** Required tag policy with Terraform/Pulumi enforcement, per-feature cost estimation components (compute, storage, data transfer, managed services, API calls), cost gate thresholds ($500/$2,000/mo), monthly audit checklist (right-sizing / reserved capacity / orphaned resources / egress / managed services), cost anomaly response playbook, standard audit report format, cost efficiency metrics (cost per active user, cost per request, MoM delta).

---

### 40. Developer onboarding
`phase3/developer-onboarding/`

**What it is:** Day-1, week-1, and month-1 onboarding checklists, local dev setup standards (Docker Compose, tool version pinning), engineering norms codification (PR size, commit style, branching), and onboarding retros.

**When to use it:**
- When a new engineer is starting — run the day-1, week-1, and month-1 checklists
- When an engineer is re-onboarding after extended leave and the stack has moved
- When codifying engineering norms after a recurring friction point (PRs too large, inconsistent commits, unclear branching)
- During the annual norms review — confirm the norms doc still matches how the team actually works

**When NOT to use it:**
- Ongoing team health check-ins and quarterly retros → team-coaching-engineering-culture
- System documentation and runbooks → documentation-system-design
- End-of-project handover to another team → project-closeout

**What you get:** Day-1 / week-1 / month-1 onboarding checklists, engineering norms document, local dev setup template (Docker Compose with pinned tool versions), onboarding retro findings format.

---

## Phase 4 — Advanced assurance

Applied to the most critical systems where standard testing is insufficient — custom distributed protocols that cannot fail.

---

### 30. Formal verification
`phase4/formal-verification/`

**What it is:** TLA+ specification and TLC model checking for distributed protocols where correctness must be proven, not just tested. Rare — use only when designing a custom consensus, ordering, or idempotency protocol.

**When to use it:** Answer all three questions yes before using:
1. Are we designing a custom distributed protocol (not using a proven library)?
2. Would a correctness bug cause data loss, split-brain, or financial loss?
3. Would property-based testing be insufficient to cover the state space?

Typical triggers: custom at-least-once delivery guarantees, event idempotency across retries, leader election without an off-the-shelf library.

**When NOT to use it:**
- Standard CRUD APIs or REST services — no TLA+ needed
- When an off-the-shelf library (Kafka, Raft, Postgres) handles the protocol — trust the library
- For performance problems → performance-reliability-engineering
- For resilience validation → chaos-engineering

**What you get:** TLA+ module structure, TLC configuration and invocation commands, worked EventIdempotency module with counterexample trace, operator cheatsheet, common invariant and liveness patterns.

---

## Tracks — domain overlays

Tracks are not skills. They are curated overlays that a session opts into when the work is in a specific domain. Each track elevates optional skills to mandatory, tightens gate criteria, and injects domain-specific reference material when a skill fires. Zero tracks is valid — most projects run without one.

A session can be in multiple tracks at once. Composition is: skill elevation union, gate modification strictest-wins, reference injection additive.

Full concept: `docs/tracks.md`. Every track's TRACK.md lives under `skills/tracks/<name>/`.

### Track 1 — Fintech / Payments
`tracks/fintech-payments/`

**What it is:** Overlay for products handling card data, money movement, or regulated financial services. Elevates `security-audit-secure-sdlc`, `distributed-systems-patterns` (idempotency), `api-contract-enforcer`, and `observability-sre-practice`. Also elevates `disaster-recovery` (PCI DSS Req 12.3 — DR plan + tested restore), `architecture-fitness` (financial module boundary enforcement in CI), `cloud-cost-governance` (per-feature transaction infrastructure cost), `chaos-engineering` (payment-path resilience game days), and `incident-postmortem` (reconciliation-incident runbook + regulatory reporting). Adds PCI scope identification, reconciliation, and fraud-signal gates.

**When to activate:** "PCI", "card vault", "payment intent", "payout", "reconciliation", "KYC/AML", "crypto custody", "money transmitter".

**When NOT to activate:** Simple checkout delegated entirely to Stripe/Adyen hosted forms where your system is never in PCI scope.

**What you get:** Track-specific PCI DSS checklist, payment-idempotency pattern, reconciliation runbook, regulatory-reporting guide, fraud-signals integration pattern.

### Track 2 — SaaS B2B
`tracks/saas-b2b/`

**What it is:** Overlay for multi-tenant B2B products with SSO, RBAC, and contractual SLA obligations. Elevates `api-contract-enforcer`, `observability-sre-practice` (per-tenant SLOs), `feature-flag-lifecycle` (per-tenant rollout), `data-governance-privacy` (DPA), and `release-readiness` (customer comms for breaking changes). Also elevates `architecture-fitness` (tenant isolation boundary rules in CI), `cloud-cost-governance` (per-tenant cost attribution required for usage-based billing), and `caching-strategy` (per-tenant cache key scoping — shared cache keys are a tenant isolation failure).

**When to activate:** "multi-tenant", "tenant isolation", "SSO/SAML", "RBAC", "contractual uptime", "usage metering", "enterprise contract".

**When NOT to activate:** B2C consumer products (use Consumer track). Single-tenant internal tools.

**What you get:** Multi-tenancy patterns (pool/silo/bridge), SSO/SAML integration, RBAC design, SLA and metering, enterprise onboarding flow.

### Track 3 — Data platform / ML ops
`tracks/data-platform-mlops/`

**What it is:** Overlay for products where data pipelines, analytics, ML inference, or LLM pipelines are the product. Elevates `specification-driven-development` (data contracts), `comprehensive-test-strategy` (data quality tests), `llm-app-development` (eval regression gate), and `observability-sre-practice` (data freshness SLOs). Also elevates `cloud-cost-governance` (compute cost attribution per pipeline and model — training jobs and model serving dwarf all other costs; mandatory at Standard+).

**When to activate:** "data pipeline", "ETL/ELT", "schema registry", "data contract", "model versioning", "RAG pipeline", "feature store".

**When NOT to activate:** Single one-shot LLM call with no pipeline. A query that is just a SELECT.

**What you get:** Data contracts, schema registry design, data quality framework, model versioning, feature store patterns.

### Track 4 — Healthcare / HIPAA
`tracks/healthcare-hipaa/`

**What it is:** Overlay for products handling PHI. Elevates `data-governance-privacy` (PHI classification), `security-audit-secure-sdlc` (HIPAA Security Rule mapping), `documentation-system-design` (tamper-evident audit log), `dependency-health-management` (BAA-covered vendors), and `incident-postmortem` (breach notification). Also elevates `disaster-recovery` (HIPAA §164.308(a)(7) contingency plan — five required specifications including data backup, emergency mode operation, and test/revision procedures).

**When to activate:** "HIPAA", "PHI", "clinical notes", "EHR", "HL7/FHIR", "BAA", "de-identification".

**When NOT to activate:** Health-and-fitness apps that do not handle PHI.

**What you get:** PHI classification rules, HIPAA audit log requirements, de-identification methods, BAA workflow.

### Track 5 — Regulated / government
`tracks/regulated-government/`

**What it is:** Overlay for products under formal frameworks: FedRAMP, SOC 2, ISO 27001, CMMC, StateRAMP. Elevates `security-audit-secure-sdlc` (control mapping), `architecture-review-governance` (formal review), `documentation-system-design` (evidence library), `devops-pipeline-governance` (separation of duties), and `incident-postmortem` (regulatory reporting). Also elevates `disaster-recovery` (FedRAMP CP-9/CP-10, SOC 2 A1.2, ISO 27001 A.17 — restore tested and evidence filed), `architecture-fitness` (separation-of-duties and least-privilege boundary rules in CI), `formal-verification` (custom auth or cryptographic protocols at Standard+), and `chaos-engineering` (DR test is a required control; FedRAMP CP-4, SOC 2 CC7.5).

**When to activate:** "FedRAMP", "ATO", "SOC 2", "ISO 27001", "CMMC", "public sector".

**When NOT to activate:** Industry-specific compliance (HIPAA → Healthcare; PCI → Fintech). Pure commercial B2B without a formal framework.

**What you get:** FedRAMP evidence checklist, SOC 2 controls mapping, change management approvals, vulnerability disclosure policy.

### Track 6 — Real-time / streaming
`tracks/real-time-streaming/`

**What it is:** Overlay for low-latency or event-streaming systems. Elevates `distributed-systems-patterns`, `performance-reliability-engineering`, `observability-sre-practice` (lag + per-topic SLOs), `specification-driven-development` (AsyncAPI + schema registry), and `chaos-engineering` (broker failure, partition loss). Also elevates `caching-strategy` (materialised-view and state-store cache design at Standard+), `formal-verification` (custom consensus, leader-election, or ordering protocols at Rigorous), and `incident-postmortem` (consumer-lag incident runbook and DLQ overflow root-cause).

**When to activate:** "Kafka", "Kinesis", "Pulsar", "exactly-once", "backpressure", "windowing", "watermarks".

**When NOT to activate:** Periodic batch jobs (use Data platform track). Simple request-response APIs.

**What you get:** Streaming platform selection, exactly-once semantics, backpressure patterns, windowing and watermarks.

### Track 7 — Consumer product
`tracks/consumer-product/`

**What it is:** Overlay for B2C products with experimentation, product analytics, notification pipelines, content feeds, and viral mechanics. Elevates `feature-flag-lifecycle` (experiment flags), `accessibility`, `data-governance-privacy` (analytics consent), and `observability-sre-practice` (funnel + product metrics). Also elevates `caching-strategy` (feed and recommendation caching; cache poisoning invalidates A/B assignment at Standard+) and `performance-reliability-engineering` (consumer-scale p50/p95 targets; latency regression is a retention variable at Standard+).

**When to activate:** "A/B test", "experiment", "product analytics", "referral loop", "retention metric", "push notification", "content feed", "recommendation", "viral coefficient", "k-factor".

**When NOT to activate:** B2B products (use SaaS B2B). Internal tools.

**What you get:** A/B testing design, experiment statistics, event taxonomy, product analytics setup, notification pipeline design, feed caching architecture, viral/referral mechanics.

### Track 8 — Open source
`tracks/open-source/`

**What it is:** Overlay for publicly-published libraries, frameworks, and tools with external contributors and public API stability obligations. Elevates `specification-driven-development` (semver + deprecation), `api-contract-enforcer` (public contract tests), `documentation-system-design`, `dependency-health-management` (license hygiene), and `security-audit-secure-sdlc` (CVE disclosure). Also elevates `developer-onboarding` (CONTRIBUTING.md + contributor onboarding flow + issue triage SLA — the contributor pipeline is a user-facing system for OSS projects).

**When to activate:** "open source this", "publish to npm/PyPI/Crates.io", "semver", "CVE disclosure", "CONTRIBUTING.md".

**When NOT to activate:** Internal libraries never exposed publicly. Forks where upstream carries release obligations.

**What you get:** Semver discipline, deprecation policy, security disclosure policy, contributor experience, license compliance.

### Track 9 — Mobile
`tracks/mobile/`

**What it is:** Overlay for native mobile apps (iOS, Android) and cross-platform mobile (React Native, Flutter). Elevates `feature-flag-lifecycle` (remote config), `accessibility` (platform a11y audit), `performance-reliability-engineering` (crash-free rate, cold start), `release-readiness` (phased rollout), and `observability-sre-practice` (per-device-class). Also elevates `cloud-cost-governance` at Rigorous (store distribution costs + CDN delivery costs for large binaries become material at scale).

**When to activate:** "iOS", "Android", "React Native", "Flutter", "TestFlight", "APNS", "FCM".

**When NOT to activate:** Mobile web (use Consumer track). Desktop apps.

**What you get:** App store approval cycles, mobile version management, offline-first patterns, push notification design, mobile performance.

### Track 10 — Web product
`tracks/web-product/`

**What it is:** Overlay for multi-user web products with an API backend, browser frontend, relational database, and a user-facing identity model. The common product shape that the SaaS B2B track is too heavy for: standard auth, simple RBAC, subscription billing, and real tenant isolation — without enterprise ceremony. Elevates `api-contract-enforcer` (typed client generation from spec), `comprehensive-test-strategy` (full pyramid with cross-user leak tests and per-role E2E), `security-audit-secure-sdlc` (auth flows + OWASP Top 10 + tenant isolation threat class), `database-migration` (concurrency review), and `accessibility` (WCAG 2.1 AA, mandatory at Standard). Also elevates `technical-debt-tracker` (monthly debt register for auth/RBAC/isolation subsystems at Standard+) and `delivery-metrics-dora` (DORA metrics tracking feature impact at Standard+).

**When to activate:** "multi-user web app", "user accounts", "JWT auth", "RBAC", "subscription billing", "Stripe", "tenant isolation", "full-stack web app", "REST API and frontend", "web product".

**When NOT to activate:** Enterprise SSO/SAML required → SaaS B2B. Purely consumer B2C with no workspace concept → Consumer product. Mobile app → Mobile track.

**What you get:** Auth patterns (JWT vs sessions, OAuth2/PKCE, MFA, token revocation), lightweight tenant isolation (RLS, app-level scoping), simple RBAC model, API design patterns (spec-first, typed client generation), DB concurrency (optimistic locking, idempotency keys), frontend architecture (server state, error boundaries, optimistic UI), subscription billing (Stripe Checkout, webhooks, entitlements), rate limiting and abuse prevention.

---

## Workflow — SDLC pipeline orchestration

---

### 31. PRD creator
`phase1/prd-creator/`

**What it is:** The entry point for creating or validating a Product Requirements Document. Operates in three modes: interactive creation from scratch (Mode A), structuring from raw input (Mode B), and validating an existing PRD (Mode C).

**When to use it:**
- When starting a new feature with no structured requirements document
- When you have bullet points, meeting notes, or a rough draft that needs to become a proper PRD
- When an existing PRD needs to be validated before entering the development pipeline
- When the downstream pipeline keeps encountering scope disputes — the root cause is usually a weak PRD

**When NOT to use it:**
- When requirements already exist and are decomposed into stories → requirements-tracer
- When the PRD is approved and you need to design the system → design-doc-generator
- For documenting technical decisions → architecture-decision-records

**What you get:** `PRD.md` with all required sections complete, measurable goals, defined NFRs, success metrics with named data sources, and a signed approval block. Verified by the PRD quality checklist before exiting.

---

### 32. Design document generator
`phase1/design-doc-generator/`

**What it is:** Synthesises the outputs of `prd-creator`, `requirements-tracer`, `specification-driven-development`, and `architecture-decision-records` into a single implementation-ready `DESIGN.md`. This is the bridge between what to build and how to build it.

**When to use it:**
- After the PRD is approved, requirements are traced, and specs are frozen
- When the team is about to start implementation and there is no shared design reference
- When a vendor or external team delivers a spec and you need to design the consuming system
- When an architecture review has concluded and decisions need to be synthesised into a build plan

**When NOT to use it:**
- Before a PRD exists → prd-creator
- Before requirements are traced → requirements-tracer
- For documenting a specific decision already made → architecture-decision-records
- For reviewing an existing design → architecture-review-governance

**What you get:** `DESIGN.md` with system context diagram, component design, data flows for every user story, API contract references, data models with migrations, infrastructure requirements, security considerations, performance/reliability design, phased implementation plan, and open questions with owners.

---

### 33. Code implementer
`phase2/code-implementer/`

**What it is:** The execution engine for implementing code from an approved design document. Drives phase-by-phase implementation with inline security gates, test-alongside enforcement, and phase gates between each phase.

**When to use it:**
- When `DESIGN.md` is approved and implementation is ready to begin
- When implementing APIs against frozen OpenAPI/Protobuf/AsyncAPI specs
- When implementation needs to be structured into ordered tasks with dependency management
- When security and quality must be applied during implementation (not retrofitted)

**When NOT to use it:**
- Before `DESIGN.md` is approved — the design must be locked before coding
- For a quick prototype or spike — this skill is for production implementation
- For reviewing code someone else wrote → code-review-quality-gates

**What you get:** Production-quality code in ordered phases, unit and integration tests written alongside each component, acceptance tests passing for each story's BDD scenarios, `docs/implementation-status.md` task tracker, and ADR documentation for any deviations from the design.

---

### 34. PR and merge orchestrator
`phase2/pr-merge-orchestrator/`

**What it is:** The final gate before code enters the main branch. Runs the complete pre-merge checklist, generates the PR description from pipeline artifacts, coordinates review and approvals, executes the merge, and tags the release.

**When to use it:**
- When implementation is complete and tests pass — the code is ready to merge
- When a PR exists but is incomplete (missing description, missing approvals, failing gates)
- When managing a formal code acceptance process
- When a release needs to be tagged after merge

**When NOT to use it:**
- Before tests pass — fix the tests first
- Before acceptance criteria are verified → executable-acceptance-verification
- Before the security gate sign-off → security-audit-secure-sdlc

**What you get:** Pre-merge gate report (all gates verified), PR with a complete description generated from pipeline artifacts, coordinated review process (SLA tracking, blocking comment resolution), merged commit with meaningful commit message, release tag, and post-merge verification.

---

### 35. SDLC orchestrator
`workflow/sdlc-orchestrator/`

**What it is:** The master pipeline skill. Manages the full software development lifecycle from PRD through to merged, documented code. Does not replace individual skills — orchestrates them in the correct order, verifies stage gates, tracks pipeline status, and guides you through each stage transition.

**When to use it:**
- Starting any non-trivial feature from scratch — this is the single entry point
- Resuming a pipeline that was paused (reads `docs/sdlc-status.md`)
- Checking pipeline status ("where are we?")
- Jumping to a specific stage with prerequisite verification
- Re-running a stage after an upstream change

**When NOT to use it:**
- For a hotfix that bypasses the full pipeline (it handles this case, but tell it you want a hotfix)
- For operational work that has no product feature component

**What you get:** A managed, gated pipeline with a `docs/sdlc-status.md` dashboard, stage-by-stage verification, correct skill invocation at the right time, handoff templates between each stage pair, and a complete audit trail via `docs/skill-log.md`.

---

## Quick reference: situation → skill

| Situation | Primary skill | Supporting skills |
|-----------|--------------|------------------|
| Starting a new feature end-to-end | sdlc-orchestrator | all pipeline skills |
| Have an idea, no requirements yet | prd-creator | sdlc-orchestrator |
| Need a design doc from specs and requirements | design-doc-generator | architecture-review-governance, security-audit-secure-sdlc |
| Ready to implement a design | code-implementer | specification-driven-development, security-audit-secure-sdlc |
| Ready to merge code | pr-merge-orchestrator | code-review-quality-gates, release-readiness |
| Stakeholder needs a status update or scope change logged | stakeholder-sync | — |
| New service being designed | architecture-review-governance | specification-driven-development, security-audit-secure-sdlc |
| Technical decision needs to be recorded | architecture-decision-records | — |
| Requirement needs to be broken into tests | requirements-tracer | executable-acceptance-verification |
| New risk identified | technical-risk-management | — |
| Designing a new REST or gRPC API | specification-driven-development | — |
| Designing a new GraphQL API | specification-driven-development | api-contract-enforcer |
| Designing Kafka topics or event-driven schemas | specification-driven-development | api-contract-enforcer |
| Reviewing code for security | security-audit-secure-sdlc | code-review-quality-gates |
| AI-generated code needs security review | ai-assisted-engineering | security-audit-secure-sdlc |
| PR needs review | code-review-quality-gates | security-audit-secure-sdlc |
| Test coverage is inadequate | comprehensive-test-strategy | executable-acceptance-verification |
| Building an LLM or AI feature | llm-app-development | comprehensive-test-strategy, security-audit-secure-sdlc |
| Pipeline needs review or design | devops-pipeline-governance | security-audit-secure-sdlc |
| Documentation missing or poor | documentation-system-design | — |
| SLO being breached | observability-sre-practice | incident-postmortem |
| Integration boundary is broken | api-contract-enforcer | specification-driven-development |
| Milestone needs formal sign-off | executable-acceptance-verification | — |
| System is slow | performance-reliability-engineering | observability-sre-practice |
| AI tools in use; need governance or prompting help | ai-assisted-engineering | — |
| Release approaching | release-readiness | devops-pipeline-governance |
| Feature flag is stale or needs a rollout plan | feature-flag-lifecycle | devops-pipeline-governance |
| Delivery velocity is degrading | technical-debt-tracker | delivery-metrics-dora |
| Leadership asks how delivery is going | delivery-metrics-dora | observability-sre-practice |
| Project just started, no DORA data yet | delivery-metrics-dora | — |
| Dependency CVE disclosed | dependency-health-management | security-audit-secure-sdlc |
| Production incident occurred | incident-postmortem | observability-sre-practice |
| Team quality is consistently poor | team-coaching-engineering-culture | code-review-quality-gates |
| Resilience patterns need validation under real failures | chaos-engineering | performance-reliability-engineering |
| Project is wrapping up, need to formally close it | project-closeout | — |
| Handing off to ops team, need formal handover | project-closeout | documentation-system-design |
| Customer-facing UI needs accessibility review or axe-core CI gates | accessibility | code-review-quality-gates |
| Architecture rules need automated CI enforcement (imports, dep budgets, dead code) | architecture-fitness | architecture-review-governance |
| Cloud bill is surprising or needs attribution by feature | cloud-cost-governance | technical-debt-tracker |
| PRD needs a monthly cloud cost NFR | cloud-cost-governance | prd-creator |
| Custom distributed protocol must be provably correct | formal-verification | — |
| New data collection, third-party sharing, SAR, or retention review | data-governance-privacy | security-audit-secure-sdlc |
| Designing a cross-service transaction or event-driven flow | distributed-systems-patterns | specification-driven-development, api-contract-enforcer |
| System needs a DR plan, backup strategy, or restore drill | disaster-recovery | observability-sre-practice |
| Designing, debugging, or adding a cache layer (app, distributed, or CDN) | caching-strategy | performance-reliability-engineering |
| New engineer starting or engineering norms need codifying | developer-onboarding | team-coaching-engineering-culture |

---

## Skill interaction map

Some skills work best together. Key pairings:

| When you use... | Also consider... |
|----------------|-----------------|
| sdlc-orchestrator | All pipeline skills — it orchestrates them |
| prd-creator | requirements-tracer — PRD feeds directly into requirements decomposition |
| design-doc-generator | architecture-review-governance — design must be reviewed before implementation |
| design-doc-generator | security-audit-secure-sdlc — STRIDE threat model is a design gate |
| code-implementer | executable-acceptance-verification — BDD scenarios define implementation done |
| code-implementer | security-audit-secure-sdlc — inline security gates at each task |
| pr-merge-orchestrator | code-review-quality-gates — review process is part of PR orchestration |
| pr-merge-orchestrator | release-readiness — production deployment requires release gate |
| specification-driven-development | api-contract-enforcer — spec must be enforced at runtime |
| security-audit-secure-sdlc | dependency-health-management — both cover different aspects of security |
| architecture-review-governance | architecture-decision-records — review produces decisions that need recording |
| requirements-tracer | executable-acceptance-verification — traceability connects to runnable tests |
| observability-sre-practice | incident-postmortem — SLO breach triggers post-mortem |
| devops-pipeline-governance | release-readiness — pipeline executes what the release checklist verifies |
| performance-reliability-engineering | chaos-engineering — load tests + chaos tests complement each other |
| team-coaching-engineering-culture | delivery-metrics-dora — culture problems show up in DORA metrics |
| ai-assisted-engineering | comprehensive-test-strategy — AI code needs AI-aware testing (evals) |
| llm-app-development | comprehensive-test-strategy — use for test strategy once the feature is built; use llm-app-development to design and build it |
| llm-app-development | security-audit-secure-sdlc — LLM features need prompt injection and supply chain threat modelling |
| feature-flag-lifecycle | devops-pipeline-governance — flag rollout is a deployment strategy |
| chaos-engineering | incident-postmortem — game days reveal gaps that become post-mortem action items |
| delivery-metrics-dora | observability-sre-practice — DORA and SLOs measure complementary health signals |
| project-closeout | delivery-metrics-dora — closeout calls DORA for the final engagement summary |
| project-closeout | chaos-engineering — Standard/Rigorous mode projects run a final game day as part of handover |
| architecture-review-governance | architecture-fitness — design review produces the rules; architecture-fitness enforces them in CI |
| accessibility | code-review-quality-gates — accessibility checklist runs as part of every customer-facing PR review |
| cloud-cost-governance | prd-creator — every PRD carries a cost NFR; governance audits against it monthly |
| cloud-cost-governance | technical-debt-tracker — cost driven by code or architecture belongs in the debt register, not the cost audit |
| data-governance-privacy | security-audit-secure-sdlc — privacy and security share a threat surface but are distinct disciplines |
| data-governance-privacy | prd-creator — every PRD that collects new data carries a privacy note and retention choice |
| distributed-systems-patterns | specification-driven-development — event schemas and API contracts are the inputs to pattern selection |
| distributed-systems-patterns | api-contract-enforcer — outbox and idempotency guarantees must be enforced at runtime |
| disaster-recovery | observability-sre-practice — SLOs define what DR tier is needed; DR drills validate the SLO holds in failure |
| disaster-recovery | chaos-engineering | — regional failover is a chaos experiment on the largest scale |
| caching-strategy | performance-reliability-engineering — cache design is a latency and capacity decision |
| caching-strategy | observability-sre-practice — hit rate, staleness, and stampede signals must be on a dashboard |
| developer-onboarding | team-coaching-engineering-culture — onboarding norms and team norms are the same norms, written once |
| developer-onboarding | documentation-system-design — onboarding points new engineers to the runbooks and system docs |
