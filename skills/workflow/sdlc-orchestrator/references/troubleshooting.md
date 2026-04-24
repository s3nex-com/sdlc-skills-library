# Troubleshooting: when the pipeline gets stuck

This guide covers the most common failure modes at each stage and what to do about them. The answer to every stuck pipeline is the same structure: (1) understand why it is stuck, (2) address the root cause, (3) re-run the stage, (4) verify the gate passes.

---

## General principles

**Do not skip a gate because it is inconvenient.** A gate failure is information. It tells you something is wrong that will be more expensive to fix later.

**Do not implement around a design problem.** If Stage 5 (implementation) reveals that Stage 4 (design) is wrong, fix the design. Implementing around a design problem produces code that does not match the design doc, which produces a divergence that grows until it breaks something.

**A stage that cannot complete is not stuck — it is blocked.** Blocked stages have a specific blocker (a person, a decision, an external dependency). Record the blocker in `docs/sdlc-status.md` with an owner and a deadline. If the deadline passes without resolution, escalate.

---

## Stage 1: PRD creation

### Problem: Goals cannot be made measurable

**Symptom:** The team keeps rewriting goals but they remain vague.
**Root cause:** The team has not agreed what success looks like, or the problem is not well enough understood.
**Resolution:**
1. Stop writing and go back to the problem statement. If the problem is not clear, the success criteria cannot be clear.
2. Use discovery question Group 2 from `references/discovery-questions.md` specifically.
3. If the team genuinely does not know the metric yet: accept a proxy metric as a placeholder with a named owner who will validate or replace it within [N] days. Document this in the open questions section with a hard deadline.
4. Do not proceed with a vague goal — it will produce scope disagreements during implementation.

### Problem: NFRs keep being deferred

**Symptom:** "We'll define those later" is the response to every NFR question.
**Root cause:** The team does not feel capable of defining NFRs at this stage.
**Resolution:**
1. Start with the consequences: "If the API is unavailable, what happens? How often can that happen before it is unacceptable?" — this produces the availability NFR.
2. For performance: "What response time would make a user notice a problem? What would make them leave?" — this produces the latency NFR.
3. If truly unknowable: use industry defaults as a starting point and flag them as "provisional — to be validated in performance testing." Document the assumption.
4. Do not proceed without NFRs. The design doc cannot be written without them.

### Problem: Partner company will not approve the PRD

**Symptom:** The partner company keeps requesting changes without converging on an approval.
**Root cause:** Either the PRD has real quality problems, or there is a disagreement about scope/goals that is not being surfaced.
**Resolution:**
1. Ask the partner company to identify their top 3 objections specifically.
2. For each objection: is it a PRD quality issue or a scope/goals disagreement?
3. Quality issues: fix them.
4. Scope/goals disagreement: escalate via `stakeholder-sync` — this is a stakeholder alignment issue, not a PRD quality issue.
5. If the partner company is requesting features as goals: return to Section 3 of `discovery-questions.md`.

---

## Stage 2: Requirements tracing

### Problem: A requirement cannot be written as a testable user story

**Symptom:** The team keeps writing stories but the acceptance criteria remain vague.
**Root cause:** The underlying requirement is too vague to be implemented. This is a Stage 1 problem that arrived at Stage 2.
**Resolution:**
1. Return to the source FR-NNN in the PRD.
2. Apply the requirement quality review from `prd-creator` SKILL.md: is it unambiguous, measurable, achievable, independent?
3. If the FR fails the quality test: update the PRD (this requires re-running the Stage 1 gate for the affected section).
4. If the FR is quality-passing but the story cannot be written: ask "what would a tester do to verify this?" — if they cannot answer, the FR is not specific enough.

### Problem: Partner company interprets a requirement differently

**Symptom:** Partner handshake reveals conflicting interpretations.
**Root cause:** The requirement was not specific enough — or each company assumed their interpretation was the only reasonable one.
**Resolution:**
1. Do not proceed until interpretations converge. Divergent interpretations mean two incompatible implementations will be built.
2. Write out both interpretations explicitly.
3. Go to the product owner with both interpretations and ask "which did you mean?" — often neither, and the requirement needs updating.
4. Update the PRD and re-run the Stage 1 gate for the affected FR.
5. Do not compromise by implementing "both interpretations" — pick one, document it in an ADR.

---

## Stage 3: Specification

### Problem: The spec design reveals an architectural disagreement

**Symptom:** Company A wants REST, Company B wants gRPC. Or: the spec design requires a breaking change to an existing contract.
**Root cause:** Architectural decisions were not made in Stage 4 (design) because it has not happened yet. The spec design is surfacing the decision prematurely.
**Resolution:**
1. Stop spec design for the contested surface.
2. Create an ADR item for the contested decision: "Decision required: [topic]"
3. Invoke `architecture-decision-records` to drive the decision to conclusion.
4. Resume spec design once the ADR is accepted.
5. Do not design the spec to avoid the decision — that just defers the conflict to implementation.

### Problem: The spec cannot be frozen because partner company has not responded

**Symptom:** The spec has been submitted for partner review but no feedback has arrived within the SLA.
**Root cause:** Either the partner company has not prioritised it, or there is no agreed review SLA.
**Resolution:**
1. Check: was a review SLA agreed? If not: this is a `stakeholder-sync` issue — establish a review SLA as part of the cadence framework.
2. If an SLA was agreed and missed: send a formal SLA breach notification via `stakeholder-sync`.
3. Do not freeze the spec unilaterally without partner review — this creates a dispute point later.

---

## Stage 4: Design document

### Problem: Architecture review produces blocking findings

**Symptom:** The architecture review finds anti-patterns, NFR violations, or missing components.
**Root cause:** The design has real problems. This is the gate working correctly.
**Resolution:**
1. Categorise findings: are they blocking (must fix before implementation) or advisory (improve but can proceed)?
2. For blocking findings: update `DESIGN.md` to address them. Re-submit for review.
3. Do not treat the architecture review as a checkbox. Blocking findings are the gate — they exist for a reason.
4. If a finding requires a significant design change: assess the impact on the implementation phases and update the phase plan if needed.

### Problem: STRIDE threat model has a threat with no viable mitigation

**Symptom:** A STRIDE threat is identified (e.g., information disclosure via API responses) but the proposed mitigation is architecturally expensive or the team does not know how to mitigate it.
**Root cause:** Either the design has a fundamental security gap, or the team is unfamiliar with standard mitigations.
**Resolution:**
1. Document the threat with full detail: what data is at risk, in what scenario, with what impact.
2. Consult `security-audit-secure-sdlc` — secure coding standards and secure-by-default patterns often have the mitigation.
3. If the mitigation requires a design change: update `DESIGN.md` before proceeding.
4. If the mitigation is not technically feasible within constraints: escalate to `technical-risk-management` — document it as an accepted risk with a named owner and a remediation plan with a date.
5. Do not proceed to Stage 5 with an unmitigated STRIDE finding that has no accepted risk record.

---

## Stage 5: Implementation

### Problem: A design doc error is discovered during implementation

**Symptom:** Implementing a component reveals that the design is wrong, incomplete, or internally inconsistent.
**Root cause:** The design doc had a gap that the implementation work revealed.
**Resolution:**
1. Stop implementing the affected component.
2. Document the problem specifically: "DESIGN.md Section 3 says [X], but when implementing [task], we discovered [Y] because [reason]."
3. Raise a DQ item in `DESIGN.md` Section 11 (or if the design is clearly wrong, raise it as a blocking deviation in `docs/implementation-status.md`).
4. Get the design fixed before continuing.
5. Do not implement a workaround around the design error — this creates a permanent divergence between the design doc and the code.

### Problem: A phase gate fails on coverage

**Symptom:** Code coverage is below the threshold when the phase gate runs.
**Root cause:** Either tests were written incompletely, or coverage thresholds were set unrealistically.
**Resolution:**
1. Run coverage with detail: which paths are untested?
2. If untested paths are legitimate code paths (not trivial getters/setters): write the missing tests. Do not skip the gate.
3. If the threshold was set incorrectly: review with the team and agree a revised threshold. Document the rationale. Do not lower the threshold without a deliberate decision.
4. Do not count tests that assert implementation details (mock call counts, internal method calls) toward coverage of behaviour.

### Problem: An external dependency is not ready

**Symptom:** A task depends on a partner company API, a third-party service, or another team's work that has not been delivered.
**Root cause:** Dependency management failure — the dependency was not tracked in the risk register.
**Resolution:**
1. Record the dependency as a blocker in `docs/implementation-status.md`.
2. Invoke `technical-risk-management` — this is a dependency risk that should be tracked.
3. Identify what work CAN proceed without this dependency (domain models, repository layer, unit tests with stubs).
4. Define a stub/interface for the dependency so implementation can continue behind it.
5. Set a deadline for the dependency: if it does not arrive by [date], escalate via `stakeholder-sync`.
6. Do not implement against the stub permanently — when the real dependency arrives, replace the stub and add integration tests.

---

## Stage 6: Acceptance testing

### Problem: A BDD scenario fails and the root cause is unclear

**Symptom:** A scenario fails but the test error does not explain whether the implementation is wrong or the scenario is wrong.
**Root cause:** Either the implementation has a bug, or the acceptance criterion was not specific enough when written.
**Resolution:**
1. Read the failing scenario carefully. Does it describe the correct expected behaviour?
2. If the scenario is correct and the implementation is wrong: fix the implementation (return to Stage 5).
3. If the scenario expects something that was never agreed: return to Stage 2, update the acceptance criterion, get partner sign-off on the change, then re-run.
4. If the scenario is ambiguous: it was not specific enough when written. Fix it in Stage 2 and re-run.
5. Do not make the test pass by weakening the assertion. The assertion must reflect the agreed acceptance criterion.

---

## Stage 7: Security gate

### Problem: SAST produces a large volume of findings

**Symptom:** Running SAST for the first time on a codebase produces hundreds of findings.
**Root cause:** Either the codebase has real issues, or the SAST tool has a high false positive rate, or findings from previous code are being included in the current PR's scope.
**Resolution:**
1. Separate findings by severity: address all Critical and High. Triage Medium and Low.
2. Separate new findings (introduced by this PR) from existing findings. Existing findings are not a gate for this PR — they belong in the technical debt tracker.
3. For High findings: verify each one. SAST High findings are often real but sometimes false positives. For each: (a) reproduce the vulnerability manually, or (b) document why it is a false positive.
4. Do not mass-suppress findings with `// nosec` or similar without reviewing each one.

---

## Stage 8: PR and merge

### Problem: A reviewer is unresponsive

**Symptom:** A required reviewer has not responded within the SLA.
**Root cause:** Competing priorities, missed notification, or unclear expectations.
**Resolution:**
1. Ping the reviewer directly (not a broadcast) with the specific PR and what you need.
2. If no response after one additional business day: escalate to the engineering lead.
3. For external-stakeholder reviews: escalate via `stakeholder-sync` — use the formal escalation path if the review SLA is contractual.
4. Do not merge without required approvals. Do not substitute a less senior reviewer for a required senior one.

### Problem: CI fails on main after merge

**Symptom:** The merge itself passed, but the CI pipeline fails on the main branch after merge.
**Root cause:** A merge conflict was resolved incorrectly, or a concurrent merge introduced an incompatibility.
**Resolution:**
1. Immediately create a revert PR (do not leave main broken — broken main blocks everyone).
2. After reverting: investigate the root cause on a branch.
3. Fix the root cause and re-submit as a new PR.
4. If the failure is minor and can be fixed with a fast follow-up commit: assess blast radius first — if no one is affected by the broken state right now, a fast follow-up is acceptable. Otherwise: revert.

---

## Stage 9: Documentation

### Problem: The team treats documentation as optional

**Symptom:** Stage 9 is perpetually "in progress" or skipped entirely.
**Root cause:** Documentation is treated as a separate task from delivery, so it is always deprioritised in favour of the next feature.
**Resolution:**
1. The pipeline is not complete until Stage 9 is done. Do not mark the feature as shipped until documentation is updated.
2. If documentation is consistently the bottleneck: reduce the documentation surface. Runbooks for P1/P2 scenarios are mandatory; everything else can be prioritised.
3. Assign documentation to a specific person at the start of Stage 9 — "the team will do it" means no one will do it.
4. Use `documentation-system-design` — it has templates that make documentation faster to produce.
