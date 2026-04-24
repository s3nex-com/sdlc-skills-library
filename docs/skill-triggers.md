# Skill triggers — natural language reference

When you say something to Claude, the right skill should fire. This document maps what engineers actually say to the skill that handles it.

---

## Quick lookup

| Situation | Skill |
|-----------|-------|
| Starting a new feature | sdlc-orchestrator |
| I have an idea, no docs yet | prd-creator |
| Need to break requirements into testable stories | requirements-tracer |
| Ready to write the design doc | design-doc-generator |
| Designing a new REST or gRPC API | specification-driven-development |
| Reviewing a new service architecture | architecture-review-governance |
| Need to record a technical decision | architecture-decision-records |
| New risk identified or risk register needs updating | technical-risk-management |
| Security review or threat modelling | security-audit-secure-sdlc |
| Data classification, GDPR/CCPA, retention policy | data-governance-privacy |
| Stakeholder needs a status update | stakeholder-sync |
| Ready to write code | code-implementer |
| PR needs review | code-review-quality-gates |
| Test coverage is thin or undefined | comprehensive-test-strategy |
| PR is ready to merge | pr-merge-orchestrator |
| Setting up or fixing CI/CD | devops-pipeline-governance |
| Going to production tomorrow | release-readiness |
| Docs are missing or out of date | documentation-system-design |
| SLOs, alerting, or observability setup | observability-sre-practice |
| Integration boundary is broken | api-contract-enforcer |
| Feature needs formal sign-off | executable-acceptance-verification |
| System is slow or needs load testing | performance-reliability-engineering |
| Using AI tools, need governance or prompts | ai-assisted-engineering |
| Building a product that uses an LLM | llm-app-development |
| Feature flag is stale or needs a rollout plan | feature-flag-lifecycle |
| UI feature needs accessibility review | accessibility |
| Adding a column, renaming a table, backfilling data | database-migration |
| Cache strategy, invalidation, CDN config | caching-strategy |
| Sagas, event sourcing, CQRS, outbox, idempotency | distributed-systems-patterns |
| RTO/RPO, DR drill, multi-region failover, backups | disaster-recovery |
| Import boundaries drifting, dependency count growing | architecture-fitness |
| Delivery velocity is degrading | technical-debt-tracker |
| Leadership asks how delivery is going | delivery-metrics-dora |
| CVE disclosed or dependency audit time | dependency-health-management |
| Something broke in prod | incident-postmortem |
| Team quality keeps slipping | team-coaching-engineering-culture |
| Onboarding new engineer, engineering norms | developer-onboarding |
| Resilience patterns need validation under real failures | chaos-engineering |
| Project is done, hand over to client | project-closeout |
| Cloud bill is growing, cost attribution missing | cloud-cost-governance |
| Custom distributed protocol must be provably correct | formal-verification |
| Domain says "PCI" / "payment intent" / "card vault" | fintech-payments track |
| Domain says "multi-tenant" / "SSO" / "SLA" | saas-b2b track |
| Domain says "multi-user web app" / "user accounts" / "subscription billing" / "JWT auth" / "REST API and frontend" | web-product track |
| Domain says "data contract" / "schema registry" / "feature store" | data-platform-mlops track |
| Domain says "HIPAA" / "PHI" / "HL7/FHIR" | healthcare-hipaa track |
| Domain says "FedRAMP" / "SOC 2" / "CMMC" | regulated-government track |
| Domain says "Kafka" / "exactly-once" / "watermarks" | real-time-streaming track |
| Domain says "A/B test" / "experiment" / "product analytics" | consumer-product track |
| Domain says "semver" / "CVE disclosure" / "CONTRIBUTING" | open-source track |
| Domain says "iOS" / "Android" / "TestFlight" / "APNS" | mobile track |

---

## Orchestrator and modes

---

## sdlc-orchestrator
`workflow/sdlc-orchestrator/`

**Fires when you say things like:**
- "start a new feature"
- "begin the pipeline"
- "run the SDLC for device telemetry ingestion"
- "we already have a PRD, start at the design stage"
- "where are we in the pipeline?"
- "resume the workflow for auth service"
- "build this from requirements to production"
- "full pipeline, standard mode"
- "new project, what do we need to do first?"

**Situation triggers:**
- Starting any non-trivial feature with no pipeline in flight
- Resuming work after a pause (`docs/sdlc-status.md` exists but pipeline incomplete)
- Checking pipeline state across multiple skills
- Stage gate has failed and you need to decide what to reset

**Does NOT fire for:** Tasks already mid-pipeline where you need one specific skill (jump directly to that skill). Hotfix emergencies (tell the orchestrator "this is a hotfix" — it switches to the hotfix path).

---

## Mode triggers

Declare a mode at session start or the orchestrator will derive one from three questions. Explicit declarations override derivation.

| What you say | Mode activated |
|---|---|
| "nano mode", "quick fix", "internal tool", "two-hour task", "admin script", "just a small change" | Nano |
| "lean mode", "standard feature", "build this properly", "small user group" | Lean |
| "standard mode", "customer-facing", "external API", "billing", "auth", "this touches external contracts" | Standard |
| "rigorous mode", "payments", "authentication", "regulated", "HIPAA", "PCI", "SOC2", "critical infrastructure", "data loss risk" | Rigorous |
| "hotfix", "production is down", "emergency fix", "patch this now" | Hotfix path |
| "spike", "explore", "investigate", "proof of concept", "should we use X or Y?", "is this feasible?" | Spike path |
| "inherited codebase", "taking over this project", "assess what we have", "post-acquisition review", "no docs exist" | Brownfield path |

---

## Track triggers

Tracks overlay a mode with domain-specific mandatory skills and tighter gates. Declare one or more together with the mode. The orchestrator can also suggest a track from PRD keywords — it asks to confirm before activating.

| What you say | Track activated |
|---|---|
| "fintech track", "PCI", "cardholder data", "card vault", "tokenization", "payment intent", "payout", "reconciliation", "chargeback", "money transmitter", "KYC/AML", "crypto custody" | fintech-payments |
| "saas b2b track", "multi-tenant", "tenant isolation", "SSO", "SAML", "OIDC", "enterprise login", "RBAC", "SLA", "usage metering", "MSA", "DPA" | saas-b2b |
| "web product track", "web app track", "multi-user web app", "user accounts", "user registration", "subscription billing", "Stripe Checkout", "pricing tiers", "JWT auth", "OAuth2", "refresh tokens", "REST API and frontend", "API with React", "API with Next.js", "full-stack web app", "RBAC for web", "optimistic locking", "idempotency key", "rate limiting" | web-product |
| "data platform track", "data pipeline", "ETL", "ELT", "data warehouse", "data lake", "schema registry", "Avro", "Protobuf topic", "data contract", "ML model", "model versioning", "MLflow", "feature store", "RAG pipeline", "prompt eval in CI" | data-platform-mlops |
| "healthcare track", "HIPAA", "PHI", "clinical notes", "EHR", "HL7", "FHIR", "BAA", "de-identification", "Safe Harbor method", "Expert Determination", "medical device", "SaMD" | healthcare-hipaa |
| "regulated track", "FedRAMP", "StateRAMP", "ATO", "authority to operate", "SOC 2", "ISO 27001", "CMMC", "FISMA", "public sector", "defense contractor", "CUI" | regulated-government |
| "streaming track", "Kafka", "Kinesis", "Pub/Sub", "NATS", "Pulsar", "RabbitMQ streams", "exactly-once", "at-least-once", "backpressure", "windowing", "watermarks", "Flink", "Spark Streaming", "Kafka Streams" | real-time-streaming |
| "consumer track", "A/B test", "experiment", "split test", "variant", "product analytics", "Amplitude", "Mixpanel", "Heap", "PostHog", "Segment", "referral", "viral loop", "retention metric", "content feed", "notification campaign", "push campaign", "notification inbox", "viral coefficient", "k-factor", "recommendation engine" | consumer-product |
| "open source track", "open source this", "publish to npm/PyPI/Crates.io", "semver", "breaking change policy", "deprecation", "CONTRIBUTING.md", "security advisory", "CVE disclosure", "SPDX", "OSI-approved" | open-source |
| "mobile track", "iOS", "Android", "React Native", "Flutter", "App Store Connect", "Play Console", "TestFlight", "APNS", "FCM", "offline-first", "sync engine" | mobile |

Multiple tracks compose: "Rigorous mode, Healthcare + Regulated tracks — clinical notes with FedRAMP Moderate". Full guide: `docs/tracks.md`.

---

## Phase 1 — Foundation

---

## prd-creator
`phase1/prd-creator/`

**Fires when you say things like:**
- "create a PRD for this feature"
- "I have some notes, turn them into a proper PRD"
- "we need requirements for X, start from scratch"
- "validate this existing PRD before we proceed"
- "I have bullet points from a meeting, make them a PRD"
- "the team keeps arguing about scope — we need a real PRD"
- "new feature: device telemetry ingestion, build the PRD"

**Situation triggers:**
- No structured requirements document exists and work is about to begin
- A rough draft, Slack thread, or meeting notes need to be formalised
- Downstream stages (design, implementation) keep encountering scope disputes
- An existing PRD needs a quality gate before the pipeline proceeds

**Does NOT fire for:** Requirements already decomposed into user stories (use `requirements-tracer`). System design questions when a PRD already exists (use `design-doc-generator`).

---

## requirements-tracer
`phase1/requirements-tracer/`

**Fires when you say things like:**
- "decompose these requirements into acceptance criteria"
- "I need BDD stories from the PRD"
- "write Given/When/Then for this user story"
- "check traceability — do all our requirements have tests?"
- "run orphan detection on requirements"
- "scope just changed, what does that affect?"
- "a milestone is coming — show me everything requirement maps to code"
- "we need evidence the feature is complete"

**Situation triggers:**
- PRD is approved and stories need to be written
- Deliverable milestone approaching; need objective coverage evidence
- Feature is disputed as complete — trace requirement to test
- Requirements exist in code with no test backing (orphan risk)

**Does NOT fire for:** Writing the actual acceptance tests (use `executable-acceptance-verification`). Tracking roadmap priority or product backlog ordering.

---

## design-doc-generator
`phase1/design-doc-generator/`

**Fires when you say things like:**
- "generate the design doc from the PRD and specs"
- "the PRD is approved, write the DESIGN.md"
- "synthesise our requirements and architecture decisions into a build plan"
- "we're about to start implementation, we need a design reference"
- "a vendor delivered a spec, design the consuming system"
- "architecture review is done, now write the design"

**Situation triggers:**
- PRD approved, requirements traced, specs frozen — team is ready to implement
- Vendor or external team has delivered specs and the consuming system needs a design
- Architecture review concluded and decisions need to be translated into a concrete build plan
- No shared design reference exists and implementation is about to start

**Does NOT fire for:** Before a PRD exists (use `prd-creator` first). Documenting a specific decision already made (use `architecture-decision-records`). Reviewing an existing design for quality (use `architecture-review-governance`).

---

## specification-driven-development
`phase1/specification-driven-development/`

**Fires when you say things like:**
- "write the OpenAPI spec for this API before we start coding"
- "design the Protobuf spec for this gRPC service"
- "define the Kafka topic schemas and message envelope first"
- "we need a contract-first approach for this REST API"
- "review this OpenAPI spec a vendor sent us"
- "is this spec change breaking or non-breaking?"
- "freeze the API contract before implementation starts"
- "validate the spec in CI"

**Situation triggers:**
- Starting any new REST, gRPC, or event-driven service — spec before code
- Vendor or partner team delivers a spec for review
- Contract freeze is needed before implementation begins
- Adding new event types to an existing Kafka or NATS-based system

**Does NOT fire for:** Runtime verification that implementations match specs (use `api-contract-enforcer`). Consumer-driven contract tests with Pact (use `api-contract-enforcer`).

---

## architecture-review-governance
`phase1/architecture-review-governance/`

**Fires when you say things like:**
- "review this architecture before we commit to it"
- "run the architecture review checklist on this proposal"
- "we're introducing a new service — is the design sound?"
- "I think we have a distributed monolith, how do we audit it?"
- "we need to pick between these two architectural approaches"
- "NFRs haven't been formally defined — help set them"
- "quarterly architecture health review"
- "the deployed system doesn't match what was designed"

**Situation triggers:**
- Before any new service is built — run the checklist
- When a proposal introduces a new data store, service boundary, or integration pattern
- Suspected architectural drift (what's deployed no longer matches the design)
- Anti-pattern suspected: shared database, synchronous call chains without fallbacks, god service

**Does NOT fire for:** Code-level PR review (use `code-review-quality-gates`). Recording a decision already made (use `architecture-decision-records`). Load testing that the architecture meets NFRs (use `performance-reliability-engineering`).

---

## architecture-decision-records
`phase1/architecture-decision-records/`

**Fires when you say things like:**
- "write an ADR for this decision"
- "record that we chose Kafka over NATS and why"
- "create an ADR for the auth approach"
- "onboarding a new engineer — document why we made these decisions"
- "a past decision is being challenged, check if we have an ADR"
- "project handover — make sure all major decisions are documented"
- "we deviated from the design, record it"

**Situation triggers:**
- Any significant technology selection, architecture pattern, or security approach decision
- Design review produces a decision that needs a permanent record
- Team member asks "why was X chosen?" and there is no written answer
- Vendor or external team makes a decision that affects your systems

**Does NOT fire for:** Day-to-day discussions that do not produce a lasting decision. Process decisions like meeting cadences or scope changes (use `stakeholder-sync`). Operational how-to documentation (use `documentation-system-design` runbooks).

---

## technical-risk-management
`phase1/technical-risk-management/`

**Fires when you say things like:**
- "populate the risk register for this project"
- "new risk identified — we only have one engineer who knows the payment service"
- "go/no-go decision is coming — what's our risk exposure?"
- "monthly risk review"
- "what are our kill criteria for this project?"
- "timeline pressure is building, log that as a risk"
- "should we be worried about this dependency choice?"

**Situation triggers:**
- Engagement kickoff — seed the risk register
- New technical risk surfaces from architecture decisions, dependency choices, or team changes
- Go/no-go approaching — consult the register before deciding
- Risk score needs updating after a change in circumstances

**Does NOT fire for:** Risks that have already become incidents (use `incident-postmortem`). Security vulnerabilities in code (use `security-audit-secure-sdlc`). CVEs in dependencies (use `dependency-health-management`).

---

## security-audit-secure-sdlc
`phase1/security-audit-secure-sdlc/`

**Fires when you say things like:**
- "run STRIDE threat modelling on this service"
- "security review before we ship"
- "audit the CI/CD pipeline for security issues"
- "generate the SBOM for this release"
- "we're adding a new dependency — verify its provenance"
- "secure coding checklist for this PR"
- "this feature has an LLM — what are the AI-specific threats?"
- "map our controls to NIST SSDF"
- "secrets management review"

**Situation triggers:**
- Design time for every new service — STRIDE before code starts
- CI/CD pipeline setup or review — verify security gates and hardening
- Before any release — SBOM, image signing, vulnerability scan
- Any feature that includes LLM or AI components — AI-specific attack surface review

**Does NOT fire for:** Managing CVEs in existing dependencies (use `dependency-health-management`). General pipeline configuration (use `devops-pipeline-governance`). Security incidents that have already occurred (use `incident-postmortem`).

---

## data-governance-privacy
`phase1/data-governance-privacy/`

**Fires when you say things like:**
- "classify this data — is it PII or sensitive?"
- "GDPR compliance check before we ship"
- "run a PIA for this feature"
- "what's our retention policy for user events?"
- "right to erasure — how do we handle deletion requests?"
- "EU AI Act data requirements for this model"
- "CCPA data subject access request handling"
- "cross-border data transfer assessment"

**Situation triggers:**
- New feature collects, stores, or processes personal data — privacy impact assessment needed
- Retention policy undefined or inconsistent across data stores
- Regulated market entry (EU, California) and compliance posture is unclear
- LLM or AI feature under EU AI Act Article 10/13 scope — data governance and transparency required

**Does NOT fire for:** Pure security threats like injection or auth bypass (use `security-audit-secure-sdlc`). Non-privacy risks like vendor lock-in or timeline pressure (use `technical-risk-management`).

---

## stakeholder-sync
`phase1/stakeholder-sync/`

**Fires when you say things like:**
- "draft a status update for the client"
- "we need to communicate this scope change"
- "log this decision so stakeholders are informed"
- "set up communication cadence for this project"
- "there's a disagreement — who can unblock it?"
- "the client is asking about timeline, prepare an update"
- "we're changing scope, document the impact"

**Situation triggers:**
- Delivering a status update, risk notification, or scope change communication to any external party
- Project kickoff — establish how decisions and scope changes will be communicated
- Scope is proposed to expand or contract
- A disagreement is escalating and someone needs to decide who owns the unblock

**Does NOT fire for:** Technical design decisions (use `architecture-decision-records`). API contract decisions (use `specification-driven-development`). Active production incidents (use `incident-postmortem`). Internal team retrospectives (use `team-coaching-engineering-culture`).

---

## Phase 2 — Delivery quality

---

## code-implementer
`phase2/code-implementer/`

**Fires when you say things like:**
- "DESIGN.md is approved, start implementing"
- "implement this phase by phase from the design doc"
- "write the code for this feature"
- "start building — design is locked"
- "implement the API against the frozen OpenAPI spec"
- "break the design into ordered implementation tasks and start"

**Situation triggers:**
- `DESIGN.md` is approved and implementation is ready to begin
- Implementing against frozen OpenAPI, Protobuf, or AsyncAPI specs
- Security and quality must be applied during implementation, not retrofitted

**Does NOT fire for:** Before `DESIGN.md` is approved — design must be locked first. Quick prototypes or spikes (use the spike workflow path). Reviewing code someone else wrote (use `code-review-quality-gates`).

---

## code-review-quality-gates
`phase2/code-review-quality-gates/`

**Fires when you say things like:**
- "review this PR"
- "run the code review checklist"
- "the team keeps missing the same issues in review — calibrate standards"
- "review this external code deliverable"
- "code review is taking too long, set SLA expectations"
- "what's the blocking comment vs suggestion label convention?"
- "defects keep slipping through review"

**Situation triggers:**
- Every PR before merge — apply the checklist
- Accepting an external code deliverable — run the formal review process
- Recurring defect types suggest a systemic review quality problem
- Review SLA is undefined and the team has differing expectations

**Does NOT fire for:** Architecture-level issues in a PR (use `architecture-review-governance`). Security-specific review (use `security-audit-secure-sdlc` alongside this). Formal milestone acceptance across multiple PRs (use `executable-acceptance-verification`).

---

## comprehensive-test-strategy
`phase2/comprehensive-test-strategy/`

**Fires when you say things like:**
- "define the test strategy for this project"
- "what tests do we need and at which layer?"
- "test coverage is disputed — establish the standard"
- "integration tests keep failing intermittently — is it the tests or the system?"
- "planning a performance test before the major release"
- "we're building an LLM feature — how do we test it?"
- "agree test pyramid ratios for the team"
- "write an eval harness for this AI feature"

**Situation triggers:**
- Start of a project — agree the test strategy before coding begins
- Test coverage is inadequate or disputed
- Designing a new service — determine test layers needed
- Building any LLM or AI feature — need eval-based testing pattern

**Does NOT fire for:** Writing specific acceptance test scenarios (use `executable-acceptance-verification`). Setting up CI pipeline gates (use `devops-pipeline-governance`). Consumer-driven contract tests (use `api-contract-enforcer`).

---

## pr-merge-orchestrator
`phase2/pr-merge-orchestrator/`

**Fires when you say things like:**
- "PR is ready to merge"
- "run the pre-merge gate"
- "generate the PR description from the pipeline artifacts"
- "implementation is done and tests pass — ship it"
- "PR exists but is missing approvals and a proper description"
- "tag this release after merge"
- "coordinate the review and get this merged"

**Situation triggers:**
- Implementation is complete, tests pass, and code is ready for main
- PR exists but is incomplete — missing description, approvals, or failing gates
- A release needs to be tagged after merge

**Does NOT fire for:** Before tests pass — fix the tests first. Before acceptance criteria are verified (use `executable-acceptance-verification` first). Before security gate sign-off (use `security-audit-secure-sdlc` first).

---

## devops-pipeline-governance
`phase2/devops-pipeline-governance/`

**Fires when you say things like:**
- "design the CI/CD pipeline for this service"
- "review our pipeline configuration for security and quality"
- "should we use blue-green or canary deployment?"
- "set up the Terraform plan/apply approval process"
- "the deployment failed — walk me through rollback"
- "secrets are leaking through CI, review pipeline security"
- "the pipeline is too slow — reorder stages to fail fast"
- "IaC pipeline governance"

**Situation triggers:**
- Designing a new CI/CD pipeline from scratch
- Pipeline configuration review for security or quality problems
- Deployment strategy decision is needed
- Pipeline is too slow, insecure, or fragile

**Does NOT fire for:** What the security gates check (use `security-audit-secure-sdlc`). Release sign-off and go/no-go (use `release-readiness`). Which tests run in the pipeline (use `comprehensive-test-strategy`).

---

## release-readiness
`phase2/release-readiness/`

**Fires when you say things like:**
- "we're going to production tomorrow — are we ready?"
- "run the release checklist"
- "go/no-go decision for this release"
- "plan the deployment for the canary rollout"
- "verify post-release the deployment succeeded"
- "production release requires database migrations and partner dependencies — coordinate"
- "release readiness report"

**Situation triggers:**
- Before every production release — run the checklist
- When a release requires formal sign-off or complex coordination
- Verifying post-release that deployment succeeded and no regressions occurred

**Does NOT fire for:** Building the pipeline that executes the deployment (use `devops-pipeline-governance`). The quality gates themselves (use `code-review-quality-gates`, `comprehensive-test-strategy`). The pre-release performance test (use `performance-reliability-engineering`).

---

## documentation-system-design
`phase2/documentation-system-design/`

**Fires when you say things like:**
- "docs are missing — what do we need before go-live?"
- "write a runbook for this operational scenario"
- "we're handing this service to another team — what docs do they need?"
- "on-call can't diagnose incidents because runbooks don't exist"
- "onboarding a new engineer — document how the system works"
- "API guide for the new endpoints"
- "C4 context diagram for this service"
- "documentation quality checklist before milestone sign-off"

**Situation triggers:**
- Before a production deployment — verify runbooks exist for all P1/P2 scenarios
- New service being handed over to another team
- Evaluating documentation quality as part of milestone acceptance
- An on-call engineer cannot diagnose an incident because docs are absent

**Does NOT fire for:** Architecture decisions (use `architecture-decision-records`). API contract specification (use `specification-driven-development`). Post-incident findings (use `incident-postmortem`).

---

## observability-sre-practice
`phase2/observability-sre-practice/`

**Fires when you say things like:**
- "instrument this new service with metrics, logs, and traces"
- "define SLOs for this service"
- "our error budget is burning faster than expected"
- "every alert must have a runbook — review alerting setup"
- "review the observability implementation before production"
- "investigating a prod incident — show me metrics, logs, traces together"
- "SLO definition and error budget policy"

**Situation triggers:**
- Instrumenting a new service — ensure all three pillars are covered
- SLO definition needed before go-live
- Error budget burning faster than expected — trigger the budget consumption response
- Alerting setup is noisy or missing runbook links

**Does NOT fire for:** DORA metric calculation (use `delivery-metrics-dora`). Incident investigation and RCA after the fact (use `incident-postmortem`). Production readiness sign-off overall (use `release-readiness`).

---

## disaster-recovery
`phase2/disaster-recovery/`

**Fires when you say things like:**
- "disaster recovery plan for this service"
- "what's our backup strategy for the primary database?"
- "define RTO and RPO tiers per service"
- "RPO is 15 minutes — can our replication meet that?"
- "multi-region failover runbook"
- "schedule the next DR drill"
- "ransomware recovery — are our backups isolated?"
- "test restore from backup — has anyone actually done it?"

**Situation triggers:**
- New service going to production — RTO/RPO tier and backup plan required
- Backups exist but restore has never been tested end-to-end
- Multi-region strategy needed for tier-1 systems
- Scheduled quarterly DR drill or post-drill action review

**Does NOT fire for:** SLO and error budget definition (use `observability-sre-practice`). Fault injection and controlled failure experiments (use `chaos-engineering`). Active production incidents (use `incident-postmortem`).

---

## api-contract-enforcer
`phase2/api-contract-enforcer/`

**Fires when you say things like:**
- "set up Pact contract tests between our services"
- "something broke at the integration boundary — is it a contract violation?"
- "run the daily contract drift check in CI"
- "upstream service deployed a change and consumers are failing"
- "enforce schema registry compatibility for Kafka topics"
- "consumer-driven contract testing setup"

**Situation triggers:**
- Setting up Pact tests between the team's consumers and external provider services
- Integration boundary failure — determine contract violation vs implementation bug
- Schema registry compatibility rules need enforcement for Kafka topics
- Upstream service changed without warning and consumers are broken

**Does NOT fire for:** Designing the API contract spec-first (use `specification-driven-development`). Comparing two spec versions for breaking changes (use `diff_contracts.py` in `specification-driven-development`). Acceptance testing a full feature (use `executable-acceptance-verification`).

---

## executable-acceptance-verification
`phase2/executable-acceptance-verification/`

**Fires when you say things like:**
- "convert the acceptance criteria into runnable BDD tests"
- "write the Gherkin scenarios for this story"
- "milestone is approaching — verify done objectively"
- "there's a dispute about whether this feature is complete"
- "set up the acceptance test suite for this engagement"
- "unit and integration pass but real-world behaviour is untested"
- "produce the formal acceptance sign-off"

**Situation triggers:**
- User story acceptance criteria exist and need to become runnable Gherkin scenarios
- Milestone approaching — need objective, automated evidence of completeness
- Dispute about whether a feature is done — run the scenarios and let them decide
- Acceptance test suite needs to be bootstrapped for the project

**Does NOT fire for:** Unit or integration tests (use `comprehensive-test-strategy`). Contract tests (use `api-contract-enforcer`). Performance acceptance criteria (use `performance-reliability-engineering`).

---

## performance-reliability-engineering
`phase2/performance-reliability-engineering/`

**Fires when you say things like:**
- "define performance NFRs for this service"
- "run load and stress tests before the release"
- "production latency regressed — analyse it"
- "this service calls three external dependencies — add circuit breakers"
- "capacity planning for the next quarter"
- "k6 load test for the ingest API"
- "system is slow — where's the bottleneck?"
- "retry and bulkhead patterns for this service"

**Situation triggers:**
- Defining performance NFRs — making them specific and measurable before building
- Before a major production release — load and stress tests required
- Production latency regression detected — analysis and diagnosis
- Designing a service that calls external dependencies — resilience patterns needed

**Does NOT fire for:** SLO definition and error budget management (use `observability-sre-practice`). Chaos engineering for resilience validation (use `chaos-engineering`). Pipeline performance gates (use `devops-pipeline-governance`).

---

## distributed-systems-patterns
`phase2/distributed-systems-patterns/`

**Fires when you say things like:**
- "saga pattern for this multi-service checkout"
- "event sourcing for the order aggregate"
- "CQRS — split the read and write models"
- "idempotency key design for this payment endpoint"
- "outbox pattern so we don't lose events"
- "distributed transaction — what's the right approach?"
- "eventual consistency strategy for this service mesh"
- "orchestration vs choreography for this saga"

**Situation triggers:**
- Designing a workflow that spans multiple services or data stores — pick a coordination pattern
- Dual-write problem suspected (DB + message broker not atomic) — outbox required
- Retries are producing duplicate side effects — idempotency keys missing
- Read and write workloads diverging in shape or scale — CQRS evaluation

**Does NOT fire for:** General design review of a new service (use `architecture-review-governance`). Protocol correctness proofs for custom consensus (use `formal-verification`). In-process reliability patterns like circuit breakers and retries (use `performance-reliability-engineering`).

---

## ai-assisted-engineering
`phase2/ai-assisted-engineering/`

**Fires when you say things like:**
- "what AI tools should we use for which tasks?"
- "this code looks AI-generated — apply the AI security checklist"
- "I'm getting poor results from Claude — help with prompts"
- "integrate Claude Code into the SDLC pipeline"
- "set up MCP server integrations for GitHub and Jira"
- "AI governance for the team — what's permitted?"
- "how do we review AI-generated code safely?"

**Situation triggers:**
- Establishing which AI tools to use and at which trust tier
- Reviewing code that may have been AI-generated — AI-specific security checklist
- Engineer is getting poor results from AI tools
- MCP server integrations (GitHub, Slack, Jira) need setup within Claude Code

**Does NOT fire for:** General code review (use `code-review-quality-gates` — the AI checklist supplements it). Testing AI features with evals (use `comprehensive-test-strategy`). Security review of AI attack surfaces like prompt injection (use `security-audit-secure-sdlc`).

---

## llm-app-development
`phase2/llm-app-development/`

**Fires when you say things like:**
- "build a feature that calls an LLM to summarise documents"
- "set up an eval harness for this prompt"
- "we changed the system prompt and don't know if it regressed"
- "design the RAG pipeline for document search"
- "prompt versioning — how do we manage prompt changes like code changes?"
- "the LLM is hallucinating on edge cases — how do we detect this in CI?"
- "design the agent tool set for this workflow"
- "LLM cost is spiking — track cost per request"
- "router pattern: which model handles which request type?"

**Situation triggers:**
- You are building or modifying a feature that uses an LLM as a component
- You need an eval harness to catch prompt regressions before shipping
- RAG pipeline design (chunking, embedding, retrieval, reranking)
- Agent tool design — deciding what tools to give a model and how to scope them
- Production LLM monitoring: cost, latency, eval score tracking

**Does NOT fire for:** Using AI tools to write your code (use `ai-assisted-engineering`). General test strategy for non-LLM features (use `comprehensive-test-strategy`). Prompt injection defense in a non-LLM-powered app (use `security-audit-secure-sdlc`).

---

## feature-flag-lifecycle
`phase2/feature-flag-lifecycle/`

**Fires when you say things like:**
- "merge this incomplete feature to main behind a flag"
- "plan the gradual rollout — 10% then 50% then 100%"
- "add a kill switch for this risky feature"
- "monthly flag audit — which flags are stale?"
- "this flag has been 100% on for six weeks, remove it"
- "flag registry is a mess — clean it up"
- "what flag type should this be — release, experiment, or ops?"

**Situation triggers:**
- Merging an incomplete feature to main (release flag needed)
- Planning a gradual rollout or A/B test (experiment flag)
- Adding a kill switch for a risky or reversible feature (ops flag)
- Monthly flag debt audit — any flag without an expiry or owner is debt

**Does NOT fire for:** Environment-specific config (use environment variables instead). Permanent per-tenant feature gating (permission flags have a different lifecycle). Pipeline deployment strategies like blue-green or canary (use `devops-pipeline-governance`).

---

## database-migration
`phase2/database-migration/`

**Fires when you say things like:**
- "I need to add a column to this table in production"
- "rename this column safely — the app is still reading the old name"
- "backfill data into the new column without locking the table"
- "zero-downtime migration for this schema change"
- "review this migration PR before it merges"
- "what's the expand-contract pattern for dropping a column?"
- "this ALTER TABLE will lock the table — what's the safe way?"
- "migration plan for the release"
- "production schema change sequence"

**Situation triggers:**
- Adding, modifying, or removing any column, table, index, or constraint in a production database
- Column rename or type change — expand-contract pattern required
- Backfilling large volumes of existing data without a table lock
- Reviewing a migration PR for safety before it merges

**Does NOT fire for:** Seed data or reference data loads (use your migration tool's seed mechanism). Application-level data transformations in code. Schema design decisions (use `design-doc-generator` or `architecture-decision-records`). Overall release sequencing and go/no-go (use `release-readiness` — this skill feeds into it).

---

## caching-strategy
`phase2/caching-strategy/`

**Fires when you say things like:**
- "add caching to this hot read path"
- "cache invalidation strategy for the product catalog"
- "configure the CDN for static assets and API responses"
- "cache hit rate is low — tune it"
- "cache stampede is taking down Redis"
- "Redis caching layer for this endpoint"
- "cache-aside vs read-through for this service"
- "TTL policy across services is inconsistent"

**Situation triggers:**
- Hot read path identified and latency budget demands caching
- Invalidation correctness suspect — stale reads observed
- CDN configuration for a new customer-facing surface
- Cache stampede, thundering herd, or hot key problems in production

**Does NOT fire for:** Load testing and capacity planning (use `performance-reliability-engineering`). Cache metrics and alert setup (use `observability-sre-practice`).

---

## accessibility
`phase2/accessibility/`

**Fires when you say things like:**
- "this form needs to be keyboard-navigable"
- "screen reader is not reading this modal correctly"
- "run the axe-core audit before we ship"
- "WCAG 2.2 compliance check on the new checkout flow"
- "color contrast is failing on this button"
- "the EU Accessibility Act applies to us — what do we need?"
- "can someone using only a keyboard complete this flow?"
- "pa11y CI is failing on the dashboard"
- "focus management is broken after the modal closes"

**Situation triggers:**
- Any user-facing feature — web, mobile, or desktop
- Pre-release accessibility audit for a customer-facing release
- Accessibility CI (axe-core / pa11y) is failing in the pipeline
- Legal question about EU Accessibility Act 2025, ADA, or EN 301 549 compliance

**Does NOT fire for:** Internal tools where no team member has accessibility needs. Screen reader testing of non-interactive content (static docs). API endpoints with no UI surface. Security review of inaccessible inputs (use `security-audit-secure-sdlc`).

---

## architecture-fitness
`phase2/architecture-fitness/`

**Fires when you say things like:**
- "import boundaries are drifting — enforce them in CI"
- "we have a circular import between these two packages"
- "the API layer is importing from the database layer directly"
- "dependency count is growing out of control — set a budget"
- "this module has no tests and no recent commits — is it dead code?"
- "set up architecture fitness checks in the CI pipeline"
- "the coverage floor for this module keeps slipping"
- "define the allowed import graph for this service"
- "run the fitness function checks before the release"

**Situation triggers:**
- Architecture boundaries are drifting between PRs without anyone noticing
- Circular imports detected or suspected
- Dependency count growing beyond what the team can maintain
- Dead code accumulating — modules with no tests and no activity
- You want import boundary rules enforced automatically in CI

**Does NOT fire for:** One-time architecture review at design time (use `architecture-review-governance`). Deciding what the architecture should be (use `design-doc-generator` or `architecture-decision-records`). Load and performance characteristics (use `performance-reliability-engineering`).

---

## Phase 3 — Sustained operations

---

## technical-debt-tracker
`phase3/technical-debt-tracker/`

**Fires when you say things like:**
- "I just got handed this codebase — assess the debt"
- "delivery velocity is dropping and I don't know why"
- "monthly debt review and reprioritisation"
- "make the case to stakeholders for tech debt time"
- "new team taking over — what are this codebase's liabilities?"
- "the codebase is slowing us down, categorise what's wrong"
- "debt register needs updating after this sprint"

**Situation triggers:**
- Starting work on an unfamiliar codebase — debt assessment first
- Delivery velocity degrading without obvious cause
- Monthly debt register review
- New team inheriting a codebase

**Does NOT fire for:** Active security vulnerabilities — treat as risks (use `technical-risk-management`). CVEs in dependencies (use `dependency-health-management`). Architecture concerns in a new design (use `architecture-review-governance`).

---

## delivery-metrics-dora
`phase3/delivery-metrics-dora/`

**Fires when you say things like:**
- "how well is the team delivering? show me the data"
- "calculate DORA metrics for last month"
- "deployment frequency has dropped — diagnose with data"
- "set delivery performance targets for this engagement"
- "project just started, instrument it for DORA from day one"
- "we have fewer than 20 deployments — what proxy metrics do we use?"
- "monthly delivery report"
- "how do we measure lead time?"

**Situation triggers:**
- Leadership asks about delivery performance — provide metrics not anecdote
- Monthly DORA calculation and reporting
- Delivery velocity has dropped and data is needed to diagnose why
- Project start — instrument deployments and incidents immediately so data exists at month 3

**Does NOT fire for:** SLO and reliability metrics (use `observability-sre-practice`). Sprint velocity and backlog tracking — Jira/Linear metrics, not in scope of this skill.

---

## dependency-health-management
`phase3/dependency-health-management/`

**Fires when you say things like:**
- "run the monthly dependency audit"
- "a CVE was just disclosed — assess our exposure"
- "this framework is approaching end-of-life"
- "generate the SBOM for this release"
- "dependency health report for the quarter"
- "Node 18 is EOL — upgrade plan"
- "are any of our dependencies near end-of-life?"

**Situation triggers:**
- Monthly dependency audit and CVE scan across all services
- New CVE disclosed — impact assessment and triage
- Framework or runtime approaching end-of-life — start the upgrade project
- Generating SBOMs for a release

**Does NOT fire for:** New dependency security at PR time (use `security-audit-secure-sdlc` Gate 3). Application-level technical debt (use `technical-debt-tracker`).

---

## incident-postmortem
`phase3/incident-postmortem/`

**Fires when you say things like:**
- "we had a P1 last night, run the postmortem"
- "blameless RCA for the database outage"
- "5 Whys on why the auth service went down"
- "reconstruct the timeline from last week's incident"
- "postmortem action items aren't being followed — review them"
- "we keep having the same incidents — something systemic is wrong"
- "security breach occurred — start the incident review"

**Situation triggers:**
- After every P1 or P2 incident — mandatory
- After a P3 incident that recurs or reveals a systemic issue
- After a security breach or near-miss
- Prior postmortem action items are not being followed up

**Does NOT fire for:** During an active incident — fix it first, review after. Proactive risk identification (use `technical-risk-management`). Ongoing operational monitoring (use `observability-sre-practice`).

---

## team-coaching-engineering-culture
`phase3/team-coaching-engineering-culture/`

**Fires when you say things like:**
- "quarterly retro time"
- "the same quality problems keep recurring despite technical fixes"
- "one engineer knows the whole payment service — knowledge concentration risk"
- "update the engineering norms doc after this friction point"
- "onboarding a new engineer — what are our standards?"
- "team health snapshot for the quarter"
- "growth plans for the engineers"

**Situation triggers:**
- Quarterly — run the structured retro, produce the Team Health Snapshot, update Growth Plans
- Recurring quality problems despite technical fixes — root cause may be cultural
- Single engineer is the only one who knows a critical system
- Engineering Norms need updating after a recurring friction point

**Does NOT fire for:** Individual engineer performance issues — HR matter. DORA metrics and delivery performance (use `delivery-metrics-dora`). Post-incident review (use `incident-postmortem`). Specific technical standards — use the relevant technical skill.

---

## developer-onboarding
`phase3/developer-onboarding/`

**Fires when you say things like:**
- "new engineer joining next Monday — prep the onboarding"
- "day-1, week-1, month-1 onboarding checklist"
- "local dev setup is broken for new hires"
- "codify the engineering norms so we stop re-explaining them"
- "first week tasks for the new backend engineer"
- "write the engineering handbook"
- "onboarding keeps missing the same gaps — fix the checklist"
- "buddy assignment and first-PR ramp plan"

**Situation triggers:**
- A new engineer is joining and the onboarding path is ad-hoc
- Local dev environment has drifted and setup takes more than half a day
- Engineering norms exist as tribal knowledge rather than written artifact
- Post-onboarding retro surfaces repeat gaps to close

**Does NOT fire for:** Ongoing team health, retros, or quarterly growth plans (use `team-coaching-engineering-culture`). System and runbook documentation (use `documentation-system-design`).

---

## chaos-engineering
`phase3/chaos-engineering/`

**Fires when you say things like:**
- "circuit breakers are implemented but never tested under real failure"
- "before the launch, run the chaos experiment catalogue"
- "quarterly chaos engineering session"
- "game day — validate the team can actually execute the runbooks"
- "we added a new dependency that's a potential single point of failure"
- "fault injection in CI"
- "inject dependency outage and see what happens"
- "resilience patterns need real-world validation"

**Situation triggers:**
- Resilience patterns (circuit breakers, retries, fallbacks) implemented but never validated under real failure
- Before a major launch or high-traffic event
- Quarterly — run the standard experiment set
- New dependency added that becomes a potential single point of failure

**Does NOT fire for:** Standard load and performance testing (use `performance-reliability-engineering`). Designing the resilience patterns themselves (use `performance-reliability-engineering`). Formal protocol correctness proofs (use `formal-verification`).

---

## project-closeout
`phase3/project-closeout/`

**Fires when you say things like:**
- "project is done — hand it over to the client"
- "documentation audit before we close out"
- "knowledge transfer session for the incoming team"
- "final DORA report for the engagement"
- "deliverables sign-off checklist"
- "lessons learned retrospective at the end of the project"
- "operational handover — client needs to run this themselves"
- "we're wrapping up — what still needs to be documented?"

**Situation triggers:**
- Project is complete and transitioning to a new team or client ownership
- Operational handover — client or ops team needs runbooks, architecture docs, on-call guide
- Final documentation audit before close
- DORA final report for the engagement

**Does NOT fire for:** Ongoing post-go-live operations (use `observability-sre-practice`, `incident-postmortem`, `delivery-metrics-dora` on a regular cadence). Mid-project retros (use `team-coaching-engineering-culture`).

---

## cloud-cost-governance
`phase3/cloud-cost-governance/`

**Fires when you say things like:**
- "our AWS bill jumped 40% this month — diagnose it"
- "tag all resources before the release"
- "what does this feature cost to run per month?"
- "right-size these idle EC2 instances"
- "set up a cost anomaly alert"
- "monthly cloud cost optimization audit"
- "orphaned snapshots and volumes are costing us money"
- "reserved instances vs on-demand — when to switch?"
- "cost gate before we release this new service"
- "the data transfer costs are invisible until they're huge"

**Situation triggers:**
- Monthly cloud cost optimization review
- Cloud bill anomaly — unexpected spike needs diagnosis
- New service about to go to production — estimate monthly cost before deploying
- Resources are untagged — no cost attribution to project/feature/owner
- Idle or over-provisioned infrastructure suspected

**Does NOT fire for:** Application performance profiling (use `performance-reliability-engineering`). CI/CD pipeline costs — treat those as fixed infrastructure. Dependency licensing costs (use `dependency-health-management`).

---

## Phase 4 — Advanced assurance

---

## formal-verification
`phase4/formal-verification/`

**Fires when you say things like:**
- "we're building a custom consensus protocol — prove it correct"
- "TLA+ spec for the event idempotency protocol"
- "distributed protocol with at-least-once delivery — verify the guarantees"
- "we're doing leader election without using Raft — model check it"
- "TLC model checking for this ordering protocol"
- "we need to prove correctness, not just test it"

**Situation triggers** — all three must be yes before using this skill:
- You are designing a custom distributed protocol (not using a proven library)
- A correctness bug would cause data loss, split-brain, or financial loss
- Property-based testing would be insufficient to cover the state space

**Does NOT fire for:** Standard CRUD APIs or REST services. Systems using off-the-shelf libraries that handle the protocol (Kafka, Raft, Postgres — trust the library). Performance problems (use `performance-reliability-engineering`). Resilience validation (use `chaos-engineering`).

---

## Workflow paths

Workflow paths are orthogonal to mode and domain track — they modify *which stages run* (Hotfix skips Stages 1–2; Spike skips Stages 3–5; Brownfield prepends an assessment). A session can combine a mode, zero or more domain tracks, and a workflow path: `Lean mode + Fintech track + Hotfix path` is valid.

(Earlier docs called these "special tracks". Renamed to "workflow paths" to free up "track" for domain specialization. See `docs/tracks.md`.)

---

## Hotfix path
(via `sdlc-orchestrator`)

**Fires when you say things like:**
- "production is down"
- "emergency fix needed"
- "hotfix for the auth bug"
- "patch this now and ship it"
- "critical bug in production — bypass the full pipeline"
- "we need a fix in the next hour"

**What activates:** Tell the orchestrator "this is a hotfix". Bypasses Stages 1–2. Starts at Stage 3 with a tight scope definition. Still requires Stage 4 (security scan) and Stage 5 (PR + merge gate). Produces an ADR if the fix has architectural implications.

---

## Spike path
(via `sdlc-orchestrator`)

**Fires when you say things like:**
- "should we use Kafka or NATS for this?"
- "spike: can we achieve p99 < 100ms with this approach?"
- "explore whether we can integrate with this third-party API in time"
- "proof of concept before we commit to building"
- "investigate why this query is slow at scale"
- "timebox this — 4 hours, answer one question"
- "feasibility check before the PRD"

**What activates:** Tell the orchestrator this is a spike. Timebox is 2–4 hours, 1-day hard cap. Produces an ADR (the decision is the artifact, not the code). Does NOT produce PRD.md, DESIGN.md, or merged code. Exits into Stage 1 if the spike produces "adopt".

---

## Brownfield path
(via `sdlc-orchestrator`)

**Fires when you say things like:**
- "I just got handed this codebase"
- "taking over this project — assess what we have"
- "inheriting a project mid-flight with no documentation"
- "post-acquisition technical due diligence"
- "we need a baseline before we add new features"
- "no docs, no ADRs, no tests — where do we start?"

**What activates:** Tell the orchestrator this is a brownfield assessment. Runs `technical-debt-tracker`, `delivery-metrics-dora`, `security-audit-secure-sdlc`, `dependency-health-management`, and `architecture-review-governance` in sequence to establish a baseline. Produces `docs/brownfield-assessment.md`. New features on the brownfield codebase then proceed through the normal pipeline in the appropriate mode.
