# Discovery questions for PRD creation (Mode A)

Use these questions when creating a PRD from scratch. Ask them in order. Do not move to the next group until the current group has answers. Record all answers verbatim — you will synthesise them into the PRD afterward.

---

## Group 1: Problem definition (ask first — always)

The goal of this group is to understand the problem before touching the solution.

1. In one sentence, what problem are you trying to solve?
2. Who has this problem? What is their role, and what are they trying to accomplish when the problem occurs?
3. How often does this problem happen, and how bad is it when it does? (Frequency × severity = priority signal)
4. What do people do today when this problem occurs? (Current workaround reveals the real pain)
5. What evidence do you have that this is a real problem? (Data, user research, support tickets, lost revenue, churn)
6. Why is now the right time to solve this? (What changed, or what will change if you don't?)

**Red flags to probe:**
- "Our users want this" → ask for the user research
- "The competition has it" → ask why it matters to YOUR users
- "It's technically interesting" → ask what user problem it solves

---

## Group 2: Success definition

1. If you launched this and it was a complete success, what would be different 3 months later? (Gets to the real goal)
2. How would you measure that success? What number would be different, and by how much?
3. What would failure look like? How would you know if this didn't work?
4. Is there anything this feature must NOT do — even if technically possible? (Seeds non-goals)

---

## Group 3: User personas

For each distinct user type:

1. What is their role (job title or function)?
2. What is their technical level (developer, business user, system administrator, etc.)?
3. What environment do they work in (web app, API, mobile, command line, etc.)?
4. Walk me through what they do today when they want to [achieve the thing this feature enables].
5. Where does it break down or frustrate them?
6. What would they expect this new feature to look like from their perspective?

**If multiple personas exist:** Ask which one is the primary user (the one you would optimise for if you had to choose one).

---

## Group 4: Functional scope

1. What are the 3-5 most important things this feature must be able to do? (Surfaces FR-NNN candidates)
2. For each: what does "done" look like? How would you know it works? (Surfaces acceptance criteria)
3. What does the feature NOT need to do, even if someone might expect it to? (Seeds non-goals and out-of-scope)
4. Are there any capabilities that are important but could be deferred to a later phase? (Seeds phase plan)

---

## Group 5: Non-functional requirements

Ask each explicitly — teams routinely forget NFRs until too late.

**Performance:**
1. How fast does the system need to respond? (Acceptable response time for the user)
2. How many users / requests / devices do you expect at launch? In 12 months?
3. What happens if it's slower than expected — is it annoying or is it a failure?

**Availability:**
1. What are the consequences of the system being unavailable? (This determines the SLA target)
2. Is there a time of day or week when availability is most critical?
3. What is acceptable planned downtime (maintenance windows)?

**Security:**
1. What data does this feature handle — is any of it sensitive, personal, or regulated?
2. Who should have access, and who should not?
3. Are there any compliance requirements (GDPR, HIPAA, SOC2, PCI, etc.)?

**Scale:**
1. How many users/records/events do you expect the system to handle?
2. Is the load constant, or are there peaks? What triggers peaks?

---

## Group 6: Constraints and dependencies

1. Are there existing systems or components this must integrate with?
2. Are there technology choices already made that constrain the design?
3. Is there a deadline? What drives it (contractual, business event, regulatory)?
4. Are there things the partner company must deliver before or alongside this?
5. What are you assuming is true that you haven't verified?

---

## Group 7: Open questions

1. What is the biggest thing you don't know yet that could change the design?
2. Who needs to make that decision, and when?
3. Is there anything in this PRD that you're not confident about?

---

## Synthesis instructions

After collecting all answers:

1. Map answers to PRD sections:
   - Group 1 answers → Sections 2 (problem statement) and 1 (executive summary)
   - Group 2 answers → Section 3 (goals) and 9 (success metrics)
   - Group 3 answers → Section 5 (personas)
   - Group 4 answers → Section 6 (functional requirements), 4 (non-goals), 10 (out of scope)
   - Group 5 answers → Section 7 (NFRs)
   - Group 6 answers → Section 8 (constraints)
   - Group 7 answers → Section 11 (open questions)

2. For each functional requirement: convert the "what does done look like" answer into a testable requirement statement using "The system shall..."

3. For each NFR: convert the answer into a measurable statement with a number (e.g., "responds fast" → "p99 latency < 200ms at 1,000 concurrent users")

4. Identify gaps — things not covered by any answer — and flag them as open questions with owners

5. Present the draft PRD for review before finalising
