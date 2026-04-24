# Customer onboarding flow

Enterprise onboarding is the path from "contract signed" to "customer in production using the product". The path is predictable and the failure modes are predictable. Treat it as a pipeline with stages, owners, and gates. This reference documents the stages, the typical timing, the handover checklist, and what to do when a step stalls.

---

## The standard path

1. **MSA signed** — the master services agreement governs the commercial relationship (payment terms, liability caps, term, termination). Usually the longest leg of legal negotiation.
2. **DPA signed** — the data processing addendum governs how you handle the customer's data. Non-negotiable for any customer in the EU, UK, or California. See `data-governance-privacy` skill references.
3. **Order form signed** — the specific product, tier, quantity, and price the customer is buying under the MSA.
4. **SSO integration** — customer provides IdP metadata; you configure their tenant's ACS URL and signing cert; test SP-initiated and IdP-initiated flows. See `sso-saml-integration.md`.
5. **User provisioning** — SCIM (preferred, automated) or manual invite list. Roles assigned. See `rbac-design.md`.
6. **Initial training** — a session with their admin users. Record it. Follow up with written runbooks.
7. **Go-live** — customer is live in production. Success metric from the order form (first workflow completed, first integration running) is hit.

A small deal compresses this to days. A six-figure enterprise deal takes four to eight weeks from MSA to go-live. A public-sector or regulated deal takes months.

---

## Timing expectations

| Step | Typical duration | Common accelerator | Common blocker |
|------|-----------------|--------------------|-----------------| 
| MSA | 1–6 weeks | Customer accepts your paper | Customer's legal team requires redlines |
| DPA | 1–3 weeks | Your DPA template is pre-approved | Customer requires GDPR Article 28 revisions |
| Order form | 1–3 days | Standard pricing | Custom commercial terms |
| SSO integration | 2 days–2 weeks | Customer IT team available | Customer IT team has a 2-week ticket SLA |
| User provisioning | 1–3 days | SCIM automated | Manual invites to 200 users with role confusion |
| Initial training | 1 session (2h) | Recorded ahead of time | Scheduling across time zones and vacations |
| Go-live | Day after training | Clear success metric | Ambiguous "success" wording in the order form |

If any single step exceeds 150% of its typical duration, escalate — a stalled step rarely unblocks on its own.

---

## Handover checklist

Before marking a customer "live":

- [ ] MSA, DPA, and order form executed copies are in the document repository with the customer record
- [ ] Tenant is created in production with the correct plan and SLA tier
- [ ] SSO is working end-to-end (SP- and IdP-initiated tested with the customer's real IdP)
- [ ] At least one tenant admin can log in and reach the admin surface
- [ ] SCIM is running or the manual user list is imported
- [ ] Roles assigned per the customer's org chart
- [ ] Per-tenant SLO dashboards exist and are visible to internal on-call
- [ ] Per-tenant feature flags are set to the customer's contracted surface (nothing extra, nothing missing)
- [ ] Customer's technical contact (name, email, phone, Slack Connect if applicable) is in the tenant record
- [ ] Customer Success / AE owner is assigned
- [ ] Training session delivered; recording and written runbook delivered
- [ ] Billing is configured; first invoice date is in the billing system
- [ ] Success metric from the order form is instrumented; a dashboard shows progress toward it
- [ ] A 30-day check-in is scheduled with the customer

Any unchecked box is a go-live blocker, not a follow-up item.

---

## What to do when a step stalls

Stalls are the norm, not the exception. Some stalls are on your side; most are on the customer's. Triage:

**Legal stall (MSA / DPA redlines drag).** Assign an engineer or PM with decision authority to the redline thread. Most redlines are 3–5 clauses; resolving them is hours of focused work, not weeks of async. Escalate to the AE if the customer's legal team goes silent for more than a week.

**SSO stall (customer IT team unresponsive).** Common pattern: customer's IT ticket SLA is 5–10 business days per round-trip. Reduce round trips — send them a metadata XML, a screenshot of their ACS URL configured on your side, a checklist of what they need to do on theirs, and a test URL they can hit when ready. One email with everything beats seven emails per round trip.

**Provisioning stall (role confusion, users keep churning).** Pause manual provisioning. Get their admin to pilot SCIM on a test OU. If they do not have SCIM, get a CSV of users with proposed roles, confirm in writing, then import. Do not provision piecemeal — it breeds errors.

**Training stall (scheduling).** Deliver async. Record a screen-share walkthrough, share the runbook, offer office hours. "We will wait for everyone's calendars to align" is a four-week delay.

**Go-live stall (success metric ambiguous).** The order form wording was too loose. Meet with the customer's sponsor, agree on a concrete, measurable first milestone, write it down, and go live against it. Do not let the deal slip waiting for perfection.

**Stall with no obvious cause.** The customer has internal turmoil you do not see (re-org, budget cut, priority change). Ask the AE, not the technical contact. Escalate cleanly and offer a time-bounded pause ("we can hold the start date for 30 days; after that, we restart the clock").

---

## Ownership model

Each stage has exactly one owner at each end. Ambiguity is what causes stalls.

| Stage | Your owner | Customer owner |
|-------|-----------|----------------|
| MSA / DPA | Legal + AE | Legal + Procurement |
| Order form | AE | Business sponsor |
| Tenant creation | Implementation engineer | n/a |
| SSO | Implementation engineer | IT admin |
| Provisioning | Customer Success | IT admin / HR admin |
| Training | Customer Success | Business sponsor + admin users |
| Go-live | Customer Success | Business sponsor |
| First 30 days | Customer Success | Business sponsor |

For a 3–5 person engineering team, "Implementation engineer" and "Customer Success" may be the same person. Name them explicitly anyway; a handover to yourself is still a handover and forces you to check the checklist.

---

## After go-live

The first 30 days set the tone. Schedule:

- Day 7: check-in with admin. Any provisioning gaps? Any SSO weirdness?
- Day 14: check-in with business sponsor. Are the success-metric numbers moving?
- Day 30: formal review. Did we hit the success metric? What are the next 90 days of adoption?

If the success metric is not moving by day 30, that is the earliest signal of a churn risk. Do not wait for the renewal date to notice.
