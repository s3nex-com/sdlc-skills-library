# SSO and SAML integration

Enterprise customers stop evaluating a product the moment they see "supports Google and Microsoft social login" on the pricing page. SSO via their IdP is a baseline expectation above a certain deal size — typically the first six-figure contract, sometimes earlier. This reference covers the protocol choice, integration flows, the IdPs you will actually meet, and the lifecycle operations that break if not planned.

---

## SAML vs OIDC — picking the protocol

| Dimension | SAML 2.0 | OIDC |
|-----------|----------|------|
| Age | 2005, XML | 2014, JSON |
| Enterprise IdP ubiquity | Universal | Growing; some legacy IdPs do SAML only |
| Mobile / SPA support | Awkward | Native |
| Assertion format | Signed XML | Signed JWT |
| Customer familiarity | "SSO means SAML" for most IT teams | Familiar with developers, newer to IT |
| Tooling | Mature, ugly | Mature, pleasant |

Decision rule:

- Build SAML first if your enterprise buyer is an IT admin. They will ask for SAML by name, hand you metadata XML, and expect SP-initiated and IdP-initiated flows.
- Build OIDC first if your buyer is a developer platform or a greenfield company.
- Above a certain ARR, you will support both. The protocol layer is a small subsystem; do not spend months picking sides.

A pragmatic shortcut: use WorkOS, Auth0, or Clerk to speak both protocols with one integration on your side. You ship faster and let them carry the IdP-specific quirks. See `rbac-design.md` for role sync considerations that interact with the SSO layer.

---

## SP-initiated vs IdP-initiated flows

**SP-initiated (Service Provider starts the flow).** User lands on your app, clicks "Sign in", you redirect them to their IdP, they authenticate, IdP posts an assertion back to your ACS URL. This is the common case and the only case OIDC handles cleanly.

**IdP-initiated (IdP starts the flow).** User is already logged into their IdP (typically Okta's tile portal), clicks your app's tile, IdP posts an unsolicited assertion to your ACS URL. You did not issue an AuthnRequest — there is no InResponseTo to validate against. Enterprises expect this to work; it is the reason they bought an IdP.

Implementation implications:

- Your ACS endpoint must accept assertions without a prior AuthnRequest. Validate signature, issuer, audience, NotOnOrAfter, and recipient. Reject replay via a short-lived nonce cache of processed AssertionIDs.
- Build a RelayState contract for deep-linking. A user clicking a Slack link to `/reports/123` should end up at `/reports/123` after SSO, not at your default landing page.
- Test both flows. IdP-initiated is the one that usually has bugs at launch because it was not in the SP-initiated test plan.

---

## The IdPs you will meet

| IdP | Market | Quirks worth knowing |
|-----|--------|----------------------|
| Okta | Largest enterprise IdP by mindshare | Great SAML. SCIM is well-documented. Admin console is customer-facing; write docs assuming the customer's IT admin. |
| Microsoft Entra ID (Azure AD) | Largest by deployment | "Enterprise Applications" terminology. SAML and OIDC both solid. App gallery submission is painful; do it anyway for discoverability. |
| Google Workspace | Tech-forward orgs | SAML supported; OIDC via Sign in with Google for consumer-ish use cases. Custom attribute mapping is clunkier than Okta. |
| Ping Identity | Large enterprise, government | SAML solid. More on-prem deployments than the others; network paths may need diagnostic help. |
| OneLogin | Mid-market | SAML and OIDC fine. Smaller ecosystem but same protocol surface. |
| JumpCloud | SMB / DevOps-heavy | Combined IdP + MDM. Reasonable SAML, active OIDC. |

Test against Okta and Entra ID sandboxes at minimum. Both offer free developer tenants. Put those tenant URLs in the Stage 4 verification runbook.

---

## JIT provisioning

Just-in-time provisioning creates a user in your system on first SSO login. The assertion carries email, name, and group/role claims; your code creates the user on the fly.

```python
def handle_sso_assertion(assertion: SamlAssertion, tenant_id: UUID) -> User:
    email = assertion.attributes["email"]
    user = users.find_by_email_and_tenant(email, tenant_id)
    if user is None:
        user = users.create(
            tenant_id=tenant_id,
            email=email,
            display_name=assertion.attributes.get("name", email),
            source="sso_jit",
        )
    sync_roles_from_assertion(user, assertion.attributes.get("groups", []))
    return user
```

Rules:

- JIT creates; JIT does not delete. Deprovisioning requires SCIM or an explicit admin action. A user who stops logging in is not the same as a user who was fired — you cannot tell them apart from the assertion alone.
- Map IdP groups to your roles explicitly. Never assume a group named "admins" on their side means admin on yours. The tenant admin configures the mapping in your app settings.
- Enforce domain-to-tenant binding. An assertion for `evil@customer-a.com` arriving at tenant B's ACS URL must be rejected, even if the signature is valid for some tenant.

---

## SCIM for user lifecycle

SCIM (System for Cross-domain Identity Management) is the deprovisioning story that JIT cannot tell. The IdP pushes user create / update / delete events to your SCIM endpoint; you apply them.

Minimum SCIM 2.0 surface to implement:

- `POST /scim/v2/Users` — create user
- `GET /scim/v2/Users/{id}` — read user
- `PATCH /scim/v2/Users/{id}` — update user (activate / deactivate)
- `DELETE /scim/v2/Users/{id}` — delete user (usually soft delete)
- `GET /scim/v2/Users?filter=...` — list with filter
- `POST /scim/v2/Groups` and related — if you support group sync

Authentication is a bearer token the customer generates in your admin UI and pastes into their IdP. Rotate-ability is expected.

Deactivation semantics: `active: false` on a SCIM PATCH should kill the user's sessions and refuse new logins, but preserve their data and audit trail. Hard deletion is for GDPR erasure, not offboarding.

Testing SCIM is tedious. Script a fake IdP that drives the full lifecycle (create → update name → change role → deactivate → reactivate → delete) against a staging tenant, and run it nightly.

---

## Metadata exchange and certificate rotation

SAML relies on signed XML; signing certificates expire. Plan for rotation from day one.

- Publish your SP metadata at a stable URL (`/sso/saml/metadata.xml`). Serve it with a long Cache-Control but ensure customers can re-fetch on demand.
- Accept IdP metadata both as an uploaded file (for air-gapped IT teams) and as a URL (for auto-rotation).
- When your signing cert rotates, publish both the old and new certs in your metadata for an overlap window. Give customers 30+ days notice.
- Alert on certs approaching expiry (30 days, 14 days, 7 days). A SAML cert expiring at 3am on Saturday is a predictable P1.
- Log every assertion failure with the failure reason. The most common production issue is "certificate changed on their side; they forgot to tell us" — a good log saves an hour of debugging.

---

## Verification checklist for Stage 4

- SP-initiated login works end-to-end against Okta sandbox.
- IdP-initiated login works end-to-end against Okta sandbox.
- SP-initiated login works against Entra ID sandbox.
- Assertion replay is rejected (second POST of the same AssertionID fails).
- Assertion with mismatched audience is rejected.
- Assertion arriving at the wrong tenant's ACS URL is rejected.
- RelayState deep-link routes to the intended path.
- SCIM create, deactivate, reactivate, and delete all behave as specified.
- Certificate rotation rehearsed on a staging tenant.
