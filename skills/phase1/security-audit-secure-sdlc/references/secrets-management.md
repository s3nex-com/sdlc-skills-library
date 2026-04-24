# Secrets management

## The rule

No secret — API key, database credential, private key, OAuth client secret, signing certificate, or any other credential — is ever stored in:

- Source code (`.py`, `.go`, `.ts`, `.java`, etc.)
- Configuration files committed to version control (`.env`, `config.yaml`, `application.properties`)
- Container images (Dockerfile `ENV` or `RUN` commands)
- CI/CD pipeline configuration files (`.github/workflows/*.yml`, `Jenkinsfile`) except as references to secret store variables
- Log files
- Error messages returned to callers
- Slack, email, or any messaging system

This is a **non-negotiable control**. A single violation creates a risk that cannot be fully remediated (the secret must be rotated immediately because it may have already been exfiltrated by an automated scanner).

---

## Approved secrets stores

| Platform | Preferred secrets store |
|----------|------------------------|
| AWS | AWS Secrets Manager or AWS Parameter Store (SecureString) |
| GCP | GCP Secret Manager |
| Azure | Azure Key Vault |
| On-premises / Multi-cloud | HashiCorp Vault |
| GitHub Actions | GitHub Encrypted Secrets (for CI only; not for application secrets) |

**Application secrets** (database credentials, API keys, signing keys) must be stored in the secrets manager, not in CI/CD secrets variables. CI/CD variables are acceptable only for deployment tooling credentials (e.g., cloud provider credentials used to deploy the application).

---

## Secrets injection patterns

### Pattern 1: Environment injection via secrets agent (Vault Agent / AWS Secrets Manager sidecar)

The secrets agent runs as a sidecar or init container, fetches secrets from the vault at pod start, and writes them to a shared in-memory volume. The application reads the secret from the file, not from an environment variable.

```yaml
# Kubernetes pod with Vault Agent sidecar
apiVersion: v1
kind: Pod
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/agent-inject-secret-db-creds: "secret/data/edgeflow/db"
    vault.hashicorp.com/agent-inject-template-db-creds: |
      {{- with secret "secret/data/edgeflow/db" -}}
      DB_PASSWORD={{ .Data.data.password }}
      {{- end }}
    vault.hashicorp.com/role: "ingestion-service"
spec:
  containers:
  - name: ingestion-service
    image: companya/ingestion-service:1.2.0
    # Application reads from /vault/secrets/db-creds at startup
```

### Pattern 2: SDK-based retrieval at startup

```python
# Python: retrieve from AWS Secrets Manager at startup
import boto3
import json

def get_database_credentials() -> dict:
    client = boto3.client("secretsmanager", region_name="eu-west-1")
    response = client.get_secret_value(SecretId="edgeflow/ingestion/db")
    return json.loads(response["SecretString"])

# Called once at application startup, not on every request
_db_creds = get_database_credentials()
db_connection = create_connection(_db_creds["host"], _db_creds["password"])
```

```go
// Go: retrieve from HashiCorp Vault using AppRole auth
func getSecret(vaultAddr, roleID, secretID, secretPath string) (map[string]interface{}, error) {
    config := vault.DefaultConfig()
    config.Address = vaultAddr

    client, err := vault.NewClient(config)
    if err != nil {
        return nil, fmt.Errorf("vault client init failed: %w", err)
    }

    // Authenticate with AppRole
    data := map[string]interface{}{"role_id": roleID, "secret_id": secretID}
    resp, err := client.Logical().Write("auth/approle/login", data)
    if err != nil {
        return nil, fmt.Errorf("vault auth failed: %w", err)
    }
    client.SetToken(resp.Auth.ClientToken)

    // Read secret
    secret, err := client.Logical().Read(secretPath)
    if err != nil {
        return nil, fmt.Errorf("vault read failed: %w", err)
    }
    return secret.Data, nil
}
```

### Pattern 3: Dynamic secrets (Vault-generated credentials)

For database credentials, Vault can generate short-lived, unique credentials on demand. Each application instance receives credentials that expire after a configurable TTL (e.g., 1 hour). No static password is ever stored.

```hcl
# Vault database secrets engine configuration (Terraform)
resource "vault_database_secret_backend_role" "ingestion_service" {
  backend = vault_database_secrets_engine.edgeflow.path
  name    = "ingestion-service"
  db_name = vault_database_secret_backend_connection.postgres.name

  creation_statements = [
    "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
    "GRANT SELECT, INSERT, UPDATE ON telemetry_events TO \"{{name}}\";",
  ]

  default_ttl = "1h"
  max_ttl     = "4h"
}
```

**When to use dynamic secrets:** database credentials, cloud provider credentials for batch jobs, any credential used by a short-lived process. Do not use for API keys shared with external partners (these need stable, rotated static credentials).

---

## Secret rotation policy and procedures

### Rotation schedule

| Secret type | Rotation frequency | Owner | Automated? |
|-------------|-------------------|-------|------------|
| Partner API keys | Every 90 days | Both companies, mutually agreed | Partially (generation automated; distribution manual) |
| Database credentials | Every 90 days or on personnel departure | Infrastructure team | Yes (Vault dynamic or automated rotation) |
| JWT signing keys | Every 365 days | Platform team | Yes (key rotation with overlap period) |
| TLS certificates | On expiry or earlier (set 30-day alert) | Infrastructure team | Yes (cert-manager or ACM) |
| Service account credentials | Every 180 days | Platform team | Yes |
| Vault root token | After initial setup, unseal and revoke | Security team | No (manual, requires quorum) |

### Rotation procedure for partner API keys

Partner API keys require coordination because both companies need to update simultaneously to avoid downtime.

**Step 1:** Company A generates new API key in the secrets manager (does not yet revoke old key).

**Step 2:** Company A notifies Company B: "New API key available in shared secret store. Key ID: `key-2025-Q3`. Grace period: 14 days."

**Step 3:** Company B retrieves new key and deploys to all affected services during the grace period.

**Step 4:** Company B confirms rotation complete to Company A.

**Step 5:** Company A revokes old key. Old key is no longer valid.

**Never:** revoke the old key before Company B confirms the new key is deployed.

---

## Emergency rotation (suspected compromise)

If a secret is suspected to be compromised (found in a log, accidentally committed, insider threat):

1. **Rotate immediately** — do not wait to confirm the compromise. Assume the secret is compromised.
2. **Notify both companies' security leads** within 1 hour.
3. **Audit access logs** for the period the secret was potentially exposed. Look for unexpected access patterns.
4. **Review for exfiltration** — check for data access that would not occur under normal operations.
5. **Document** the incident: when the compromise was discovered, when rotation occurred, what access was potentially possible, findings from log review.
6. **Post-incident review** within 72 hours: how did the secret become exposed? What control failed?

### Detecting secrets in logs

Common patterns that indicate a secret has been logged accidentally:

```
# Database connection string with password
postgresql://user:S3cretP4ss@host:5432/db

# Bearer token in request log
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...

# API key in URL (never put secrets in URLs)
GET /events?api_key=sk_live_abc123def456

# Private key fragment in error message
Error: invalid PEM: -----BEGIN RSA PRIVATE KEY-----
```

Configure log scrubbing middleware to redact known secret patterns before they reach the log store. This is defence-in-depth, not a replacement for not logging secrets in the first place.

---

## Pre-commit secret detection setup

### gitleaks (recommended)

```bash
# Install
brew install gitleaks

# Run manually
gitleaks detect --source . --verbose

# Add as pre-commit hook
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF

pre-commit install
```

### detect-secrets (alternative)

```bash
# Install
pip install detect-secrets

# Create baseline (excludes known false positives)
detect-secrets scan > .secrets.baseline

# Run in CI
detect-secrets audit .secrets.baseline
detect-secrets scan --baseline .secrets.baseline
```

---

## Secrets management audit checklist

Run quarterly or after any security incident:

- [ ] Secrets manager inventory reviewed: are all secrets still needed?
- [ ] No secrets in version control (run gitleaks full history scan)
- [ ] No secrets in container image layers (`docker history --no-trunc IMAGE`)
- [ ] No secrets in CI/CD logs (review recent pipeline logs for accidental output)
- [ ] Rotation schedule followed for all secret types (check last rotation dates)
- [ ] TLS certificates expiry checked; alerts configured for 30-day warning
- [ ] Vault audit log reviewed for unusual access patterns
- [ ] All departed personnel's credentials rotated within 24 hours of departure
- [ ] Dynamic secrets TTL appropriate for each use case
- [ ] Vault AppRole secret IDs rotated and bounded (not perpetual)
