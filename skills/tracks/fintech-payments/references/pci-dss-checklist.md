# PCI DSS 4.0 — engineering checklist

Developer-facing checklist for building and maintaining systems in PCI scope. Not an audit guide — work with your QSA for formal validation. This file tells engineers what to do in code, config, and infra so the audit is boring.

A component is "in scope" if it stores, processes, or transmits cardholder data (CHD) or sensitive authentication data (SAD), or is connected to a component that does. Every item below applies only to in-scope components unless otherwise noted.

---

## 1. Network segmentation (Req 1)

Reduce scope by keeping in-scope components on their own network. Anything that can route to an in-scope component is itself in scope — segmentation is the only way to keep your environment small.

- [ ] In-scope components live in a dedicated VPC or subnet with no default route to non-PCI environments.
- [ ] Ingress to the CDE (cardholder data environment) is restricted to named services by security group / NACL. No `0.0.0.0/0` rules except through a WAF.
- [ ] Egress from the CDE is allow-listed: only the processor endpoints, monitoring, and logging destinations.
- [ ] Segmentation is tested at least annually (penetration test must include segmentation validation per Req 11.4.5).
- [ ] Jump hosts / bastions require MFA and log every session.

Example Terraform snippet for the egress allow-list:

```hcl
resource "aws_security_group_rule" "cde_egress_processor" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = var.stripe_api_cidrs  # pinned, reviewed quarterly
  security_group_id = aws_security_group.cde.id
}
```

---

## 2. Encryption at rest (Req 3)

Never store PAN in cleartext. Tokenize at the earliest possible point. If you must store PAN, use strong cryptography with proper key management.

- [ ] PAN is tokenized at the edge. The token vault is the only component that stores PAN.
- [ ] Storage of SAD (CVV, full track, PIN) is forbidden after authorization. Verify with a periodic grep-for-patterns job on logs and backups.
- [ ] Databases holding tokens or truncated PAN use AES-256 with keys held in a KMS (AWS KMS, GCP KMS, HashiCorp Vault Transit, Azure Key Vault).
- [ ] Disk-level encryption (EBS, GCE PD) is always on. This is necessary but not sufficient — column-level encryption still required for PAN.
- [ ] Backups are encrypted with the same rigor as primary storage. Verify restore path preserves encryption.

Envelope encryption example (Python, AWS KMS):

```python
import boto3, os
kms = boto3.client("kms")

def encrypt_pan(pan: str, key_id: str) -> dict:
    # Generate a per-record data key
    resp = kms.generate_data_key(KeyId=key_id, KeySpec="AES_256")
    cipher = AES_GCM(resp["Plaintext"])  # your AES-GCM wrapper
    ct = cipher.encrypt(pan.encode(), aad=b"pan-v1")
    return {"ciphertext": ct, "wrapped_key": resp["CiphertextBlob"]}
```

Plaintext data keys must never be logged, cached to disk, or transmitted. Zero memory after use.

---

## 3. Encryption in transit (Req 4)

All CHD transmission over public or untrusted networks uses TLS 1.2 or higher. TLS 1.0 and 1.1 are forbidden. SSL is forbidden.

- [ ] All public endpoints negotiate TLS 1.2+ only. Disable 1.0, 1.1, SSLv3.
- [ ] Cipher suites are restricted to strong AEAD suites (AES-GCM, ChaCha20-Poly1305). No RC4, no 3DES, no CBC-mode-only.
- [ ] HSTS is enabled with `max-age` >= 1 year on customer-facing domains.
- [ ] Internal service-to-service traffic in the CDE is mTLS or service-mesh encrypted (Istio, Linkerd, AWS App Mesh).
- [ ] Certificate expiry alerts fire 30 days before expiry. Rotation is automated (Let's Encrypt, ACM, cert-manager).

nginx snippet enforcing TLS 1.2+:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers on;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

Test with `sslyze example.com` — any "VULNERABLE" or "WEAK" result is a hard fail.

---

## 4. Access control and key management (Req 7, 8, 3.5/3.6)

Least privilege on PAN, tokens, and cryptographic keys. Separate duties between developers and production operators.

- [ ] Access to PAN is role-gated. Developers have zero access to production PAN data by default.
- [ ] All access to the CDE requires MFA (Req 8.4).
- [ ] Service accounts for applications use short-lived credentials (IAM roles, Vault dynamic secrets, Workload Identity). No long-lived API keys in code or env files.
- [ ] Data encryption keys (DEKs) are rotated at least annually. Key encryption keys (KEKs) in KMS are rotated annually (AWS KMS auto-rotation enabled).
- [ ] Split knowledge or dual control for key management ceremonies (two separate engineers required to perform key operations on HSM-backed KEKs).
- [ ] Quarterly access review: every identity with CDE access is confirmed by the engineer's manager.

Vault dynamic DB credentials example (every request gets a fresh short-lived user):

```hcl
path "database/creds/payments-read" {
  capabilities = ["read"]
}
# TTL 10 minutes; Vault revokes the user automatically on expiry.
```

Key rotation cadence:

| Key type | Rotation | Trigger |
|----------|----------|---------|
| TLS cert | 90 days | Automated (ACM / Let's Encrypt) |
| KMS KEK | 1 year | AWS KMS auto-rotate |
| DEK (envelope) | 1 year | Re-wrap on rotation; re-encrypt on next write |
| Service account token | 1 hour | Short-lived IAM / Vault |
| Human SSO session | 12 hours | IdP policy |

---

## 5. Logging and monitoring (Req 10)

Every access to CHD, every privilege-sensitive action, and every auth event is logged. Logs themselves are tamper-evident and retained for a year (90 days immediately available).

- [ ] Every API call that touches PAN, token, or vault operation is logged with: actor, timestamp, source IP, request ID, action, object reference (never the PAN itself).
- [ ] Authentication success and failure are logged. Failed logins trigger rate-limit and alert at 5/min per identity.
- [ ] Admin actions (IAM changes, security group changes, key rotations) are logged via CloudTrail / Cloud Audit Logs, shipped to a logging account the operator cannot modify.
- [ ] Log retention: 1 year total, last 90 days queryable without restore.
- [ ] Log integrity: use immutable storage (S3 Object Lock, GCS Bucket Lock) or SIEM with write-once ingestion.
- [ ] Daily review of security events — automated alerts for patterns, not a manual log-reading exercise.

Never log these: full PAN (even partial beyond last 4 digits must be masked), CVV, track data, PIN, passwords, API tokens, session cookies, JWTs with PII.

Structured logging example (Python):

```python
logger.info("vault.detokenize", extra={
    "actor": ctx.user_id,
    "token_ref": token_id,      # opaque reference, not PAN
    "request_id": ctx.request_id,
    "source_ip": ctx.source_ip,
})
```

---

## 6. Vulnerability management (Req 6, 11)

Patch fast. Scan continuously. Test changes.

- [ ] SAST runs on every PR. Blocking: critical findings in CHD-handling paths.
- [ ] SCA runs on every PR and daily against `main`. Blocking: critical CVEs in dependencies with a published fix.
- [ ] DAST or authenticated scan runs weekly against staging.
- [ ] Quarterly internal + external vulnerability scan by an ASV (approved scanning vendor). Remediate critical/high within 30 days.
- [ ] Annual penetration test including segmentation validation.
- [ ] Patch SLA: critical 7 days, high 30 days, medium 90 days, low best-effort.
- [ ] WAF in front of all customer-facing endpoints with OWASP core rule set.

---

## 7. Secure SDLC (Req 6.2, 6.3, 6.5)

Security is a build-time property, not a post-hoc review.

- [ ] Every change is peer-reviewed. CHD-touching changes require review by an engineer outside the immediate author's sub-team (separation of duties).
- [ ] Threat model exists for every in-scope service and is reviewed when the data flow changes.
- [ ] Security training for all engineers annually — OWASP Top 10, secure coding in the languages used, incident response basics.
- [ ] No production data in non-production environments. Use synthetic data or tokenized copies only.
- [ ] Secrets in CI are injected from a secrets manager, never stored in repo or CI config files. Rotate CI service tokens quarterly.
- [ ] Pre-commit hooks and CI scan for secret patterns (truffleHog, gitleaks).
- [ ] Feature flags for risky changes so rollback does not require a deploy.

---

## 8. Scope review cadence

- Quarterly: re-draw the CDE network diagram and compare against last quarter. New components? Why? Can they be moved out of scope?
- On every major architecture change: re-confirm no CHD path sneaks into a previously out-of-scope service.
- Annually: full Self-Assessment Questionnaire (SAQ) or Report on Compliance (RoC) depending on merchant level.

When in doubt about whether something is in scope, assume yes and justify no. Scope creep is far more common than scope shrink and only the first kind causes an audit failure.
