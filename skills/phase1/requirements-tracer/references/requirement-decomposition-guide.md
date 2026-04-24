# Requirement decomposition guide

## The decomposition hierarchy

```
Business goal
  └── Epic (multi-sprint capability)
        └── Feature (deliverable component)
              └── User story (specific user behaviour)
                    └── Acceptance criteria (testable conditions)
```

Each level answers a different question:
- **Epic:** What large capability are we building?
- **Feature:** What part of that capability is deliverable in this sprint or milestone?
- **User story:** Who benefits, what do they do, and why?
- **Acceptance criteria:** How will we know, with certainty, that the story is done?

---

## Worked example 1: Functional requirement

### Starting point (vague business ask)
> "Users must be able to reset their password."

This is a business ask, not a requirement. It is incomplete: which users? Through what mechanism? With what security controls? What happens if the reset link is clicked twice?

### Step 1 — Clarify the ask

Ask: Who are the users? (Answer: registered dashboard users with email-based accounts.) What mechanism? (Answer: email link.) What security requirements? (Answer: link expires after 30 minutes; single use; requires current email confirmation.) Are there non-obvious edge cases? (Answer: inactive accounts should not be able to reset.)

### Step 2 — Write the Epic

**Epic EP-004: User account self-service**
The ability for registered users to manage their own account credentials without administrator intervention.

### Step 3 — Decompose to Features

| Feature ID | Feature |
|------------|---------|
| EP-004-F01 | Password reset via email link |
| EP-004-F02 | Email address change with verification |
| EP-004-F03 | Account deactivation self-service |

*We will decompose only EP-004-F01 here.*

### Step 4 — Write User stories for EP-004-F01

| Story ID | Story |
|----------|-------|
| EP-004-F01-S01 | As a registered user who has forgotten their password, I want to request a password reset link via my email address, so that I can regain access to my account without contacting support. |
| EP-004-F01-S02 | As a registered user with a valid reset link, I want to set a new password, so that I can log in with my new credentials. |
| EP-004-F01-S03 | As a system, I want to invalidate a reset link after it has been used or after 30 minutes, so that stolen reset links cannot be used to take over accounts. |

### Step 5 — Write Acceptance criteria (Given/When/Then)

**EP-004-F01-S01: Request a reset link**

```
Scenario 1: Successful reset request for active account
Given I am on the "Forgot password" page
And I enter an email address that is registered to an active account
When I submit the form
Then the system sends a password reset email to that address within 60 seconds
And the response page shows "If this email is registered, you will receive a reset link"
And only one active reset token exists for this email at a time (previous tokens are invalidated)

Scenario 2: Request for unknown email (security — no enumeration)
Given I am on the "Forgot password" page
And I enter an email address that is not registered
When I submit the form
Then the response page shows the same message: "If this email is registered, you will receive a reset link"
And no email is sent
And the response time is indistinguishable from the success case (prevents timing attacks)

Scenario 3: Request for inactive account
Given I am on the "Forgot password" page
And I enter an email address belonging to an account with status "Inactive"
When I submit the form
Then no reset email is sent
And the same generic response is shown (no enumeration of inactive accounts)
```

**EP-004-F01-S02: Set a new password via reset link**

```
Scenario 1: Valid, unexpired, unused reset link
Given I have received a password reset email
And the link is less than 30 minutes old and has not been used
When I click the link
Then I am directed to the "Set new password" page
When I enter a valid new password (meets complexity requirements) and confirm it
And I submit the form
Then my password is updated
And I am redirected to the login page with a success message
And all existing sessions for my account are invalidated
And the reset token is marked as used

Scenario 2: Expired reset link
Given I have received a password reset email
And the link is more than 30 minutes old
When I click the link
Then I see an error: "This password reset link has expired. Please request a new one."
And no password change occurs

Scenario 3: Already-used reset link
Given I have already used a reset link to change my password
When I click the same link again
Then I see an error: "This password reset link has already been used."
And no password change occurs
```

---

## Worked example 2: Performance requirement

### Starting point (vague business ask)
> "The API must respond quickly under normal load."

"Quickly" and "normal load" are undefined. This cannot be tested.

### Step 1 — Clarify the ask

Ask: What operation? (Answer: the telemetry ingestion endpoint — `POST /v1/telemetry/events`.) What does "quickly" mean in business terms? (Answer: device firmware has a 1-second cycle time; if the API takes more than 500ms, the device falls behind.) What is "normal load"? (Answer: the fleet will have approximately 5,000 devices each sending one event per second.)

### Step 2 — Write the NFR as an Epic item

**Epic EP-007-NFR: Telemetry API performance**
The ingestion API must meet defined latency and throughput targets under both normal and peak load conditions.

### Step 3 — Write Features

| Feature ID | Feature |
|------------|---------|
| EP-007-NFR-F01 | Sub-500ms p99 latency at normal load |
| EP-007-NFR-F02 | Sub-100ms p50 latency at normal load |
| EP-007-NFR-F03 | Maintain 0% error rate at 1.5× normal load (peak buffer) |

### Step 4 — Write Acceptance criteria

**EP-007-NFR-F01: Sub-500ms p99 latency**

```
Scenario: Load test at normal load (5,000 events/second sustained)
Given the ingestion API is deployed in the staging environment
And the load test is configured with 5,000 virtual devices each posting one event per second
When the load test runs for 10 minutes
Then the p99 response time for POST /v1/telemetry/events is ≤ 500ms
And the error rate (4xx and 5xx responses) is < 0.1%
And no database connection pool exhaustion errors appear in the service logs

Scenario: Load test at peak load (7,500 events/second sustained for 5 minutes)
Given the same staging environment
When the load test runs at 1.5× normal load for 5 minutes
Then the p99 response time is ≤ 800ms (20% SLO relaxation permitted at peak)
And the error rate is < 0.5%
And after load returns to normal, p99 returns to ≤ 500ms within 60 seconds
```

**Key observations from this example:**
- The performance criterion is now testable with specific numbers
- Both normal and peak conditions are defined
- Recovery behaviour is specified (system returns to SLO after load normalises)
- The acceptance test can be run in CI/CD automatically on every release candidate
