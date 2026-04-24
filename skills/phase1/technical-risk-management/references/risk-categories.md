# Risk categories

Seven categories cover the full risk landscape of a cross-company software engagement. Check all seven at every risk identification session.

---

## Category 1: Architecture risks

**Definition:** Risks arising from the technical design of the system — choices that may not meet requirements, scale sufficiently, or integrate correctly.

**Examples:**
- The chosen message broker cannot meet the peak throughput target (only discovered during load testing)
- Service boundaries are poorly defined, creating hidden coupling that makes independent deployment impossible
- The data model cannot efficiently support the query patterns required by the analytics features
- A chosen third-party SDK does not support the target runtime environment
- The selected consistency model (eventual consistency) is incompatible with the business requirement for strong consistency in a specific workflow

**Typical mitigations:**
- Proof-of-concept spikes for unproven technology choices before commitment
- Architecture review with external perspective for novel or high-stakes designs
- NFRs defined and validated with load tests before milestone acceptance

**Early warning indicators:**
- Prototype performance significantly below target
- Architects from both companies cannot agree on service boundaries
- Integration test failures that require changes to agreed contracts

---

## Category 2: Delivery risks

**Definition:** Risks to the execution of the work — schedule, capacity, scope, and process failures that affect whether the agreed deliverables are produced on time and to quality.

**Examples:**
- Company B overcommits to a sprint and consistently delivers 60% of committed stories
- A developer critical to the implementation is pulled onto another project without notice
- Scope creep absorbs sprint capacity without formal change requests
- Test coverage requirements are not met at milestone time, blocking acceptance
- The integration test environment is unavailable for two weeks due to infrastructure issues

**Typical mitigations:**
- Velocity tracking from Sprint 1 to detect delivery patterns early
- Formal scope change process to prevent silent scope growth
- Sprint commitment review at the start of each sprint (is the commitment realistic based on velocity?)
- Infrastructure environment health monitoring and ownership clarity

**Early warning indicators:**
- Sprint velocity below baseline by >20% for two consecutive sprints
- Increasing number of stories carrying over between sprints
- Integration environment uptime below 90%
- Company B's daily standup consistently reports the same blockers without resolution

---

## Category 3: Dependency risks

**Definition:** Risks from external systems, services, or components that are outside the direct control of either company — third-party APIs, libraries, cloud services, open-source projects.

**Examples:**
- A critical open-source library releases a breaking change in a minor version update
- A third-party geolocation API changes its pricing to make the current usage cost-prohibitive
- A managed cloud service (e.g., Confluent Cloud) suffers an extended outage
- A dependency has a known CVE that cannot be patched without a breaking change to the integration
- The company that provides a critical SDK is acquired and the product is discontinued

**Typical mitigations:**
- Pin dependency versions; automated CVE scanning; maintain a list of alternative providers
- Design abstraction layers around third-party APIs so they can be swapped if needed
- Evaluate backup providers at the start of the engagement, not when the primary fails
- Review licence terms and support commitments before adopting any critical dependency

**Early warning indicators:**
- Dependency's release cadence slows significantly or stops
- CVE reported against a dependency with no patch available
- Third-party API response time degrades by >50% from baseline
- Vendor announces end-of-life with a timeline that overlaps the project

---

## Category 4: Security risks

**Definition:** Risks that expose the system, its data, or either company to security compromise, compliance failure, or legal liability.

**Examples:**
- A vulnerability in the authentication implementation allows token forging
- API keys are stored in a git repository (even a private one)
- A third-party dependency has a CVE that enables remote code execution
- The system stores PII without proper encryption at rest
- SAST tooling identifies SQL injection in a data access layer
- The secrets rotation process is undefined, meaning old credentials may be valid indefinitely

**Typical mitigations:**
- SAST and SCA integrated into CI/CD from Sprint 1
- Secrets management policy enforced with automated pre-commit hooks
- Security review at each milestone gate
- Threat model created before implementation begins

**Early warning indicators:**
- SAST tools begin reporting new High or Critical findings in PRs
- Company B engineers report finding credentials in configuration files
- Dependency scanner flags a new CVE in a production dependency
- Security review raises findings that Company B has not addressed in >1 sprint

---

## Category 5: Operational risks

**Definition:** Risks that arise from deploying, running, and maintaining the system in production — gaps in monitoring, runbooks, rollback capability, and incident response readiness.

**Examples:**
- No runbooks exist for common operational scenarios; first production incident takes 4 hours to resolve
- Rollback procedure has never been tested; when a bad deployment occurs, the rollback itself fails
- Alerting is misconfigured and a production degradation goes undetected for 6 hours
- The on-call rotation does not include anyone from Company B, leaving company A to triage issues in Company B's code
- Database backups exist but have never been tested for restore; a restore attempt fails

**Typical mitigations:**
- Runbooks required for all services before pre-release gate
- Rollback tested in staging as part of the release readiness process
- Alerting reviewed at the pre-release gate; synthetic monitoring in production from day one
- On-call coverage agreed and documented before production deployment
- Backup restore tested on a defined schedule (at minimum, before production launch)

**Early warning indicators:**
- Runbooks not yet written for services approaching production
- Staging environment does not have the same alerting configuration as production
- No one on either team has performed a rollback drill

---

## Category 6: Contractual risks

**Definition:** Risks that arise from ambiguities, disagreements, or failures in the legal and commercial relationship between the two companies — scope interpretation, IP ownership, SLA breach, payment, and liability.

**Examples:**
- Both companies interpret "real-time" differently — Company A expects <1 second; Company B implemented <30 seconds
- Company B inadvertently uses GPL-licensed code in the deliverable, creating IP contamination
- The SLA clause is ambiguous about whether planned maintenance windows count against availability
- Company A disputes that a delivered milestone meets acceptance criteria; Company B believes it does
- A scope creep dispute: Company B claims Feature X was always in scope; Company A says it was a new request

**Typical mitigations:**
- All technical terms defined precisely in the charter or a project glossary
- Licence scanning in CI/CD; dependency approval process that includes licence review
- Formal acceptance criteria and milestone acceptance process (not "done when Company A is satisfied")
- Scope change process documented and both companies trained on it at kickoff
- Decision log captures every scope and architecture decision with both-company sign-off

**Early warning indicators:**
- Recurring disagreements about whether specific work is in scope
- Company B regularly completes work that Company A considers out of scope (or vice versa)
- SLA language questioned at multiple steering meetings
- Either company requests a legal review of the project charter

---

## Category 7: Organisational risks

**Definition:** Risks from people, culture, communication, and process across the two organisations — the human factors that are often the hardest to detect and manage.

**Examples:**
- Key person dependency: one engineer at Company B is the only person who understands the Kafka configuration; they leave
- Culture clash: Company A expects detailed upfront design; Company B prefers rapid iteration — creating friction in every sprint
- Communication breakdown: timezone differences and unclear ownership cause decisions to be delayed or made incorrectly
- Management changes: a new CTO at Company B decides this engagement is not a priority
- Escalation avoidance: problems are not raised to leadership at either company until they are crises

**Typical mitigations:**
- Knowledge transfer documented in runbooks; pair programming for critical components
- Explicit agreement at kickoff on development methodology and meeting cadences
- Clear escalation path defined and tested — raise a non-critical issue through the process so both companies know it works
- Regular relationship health check at monthly steering ("how is the partnership working?")
- Single point of contact at each company for cross-company decisions

**Early warning indicators:**
- A single person's absence causes significant slowdown (key person dependency identified)
- Meeting attendance from one company drops
- Action items from weekly sync are repeatedly not completed
- Informal communication channels are used for significant decisions without documentation
