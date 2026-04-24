# Supply chain security — reference

Detailed commands and setup for SBOM generation, Sigstore signing, and dependency provenance. Apply these at every release build. The SKILL.md has the checklist items; this file has the how.

---

## SBOM generation and scanning (syft + grype)

### Install

```bash
# syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
```

### Generate and scan

```bash
# Generate SBOM in CycloneDX JSON format
syft packages . -o cyclonedx-json > sbom.json

# Scan SBOM for CVEs (exit code 1 on Critical findings — blocks CI)
grype sbom:sbom.json --fail-on critical

# Scan a container image directly
grype <image>:<tag> --fail-on critical

# Output as table (human-readable) or JSON (for CI ingestion)
grype sbom:sbom.json -o json > grype-report.json
```

### CI integration (GitHub Actions)

```yaml
- name: Generate SBOM
  run: syft packages . -o cyclonedx-json > sbom.json

- name: Scan for vulnerabilities
  run: grype sbom:sbom.json --fail-on critical

- name: Attach SBOM to release
  uses: actions/upload-artifact@<sha>
  with:
    name: sbom
    path: sbom.json
```

---

## Container image signing (Sigstore / cosign)

### Install cosign

```bash
# macOS
brew install cosign

# Linux (latest release)
curl -O -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
chmod +x cosign-linux-amd64 && mv cosign-linux-amd64 /usr/local/bin/cosign
```

### Keyless signing (recommended — uses OIDC identity, no key management)

```bash
# Sign (run in CI after image push; OIDC token provided by GitHub Actions / GCP / AWS)
cosign sign --yes <registry>/<image>:<tag>

# Verify (run in deploy step or admission controller)
cosign verify \
  --certificate-identity-regexp="https://github.com/<org>/<repo>/.github/workflows/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  <registry>/<image>:<tag>
```

### Key-based signing (if OIDC not available)

```bash
# Generate key pair (store private key in Vault or secrets manager — never in repo)
cosign generate-key-pair

# Sign
cosign sign --key cosign.key <registry>/<image>:<tag>

# Verify
cosign verify --key cosign.pub <registry>/<image>:<tag>
```

### GitHub Actions: sign on push

```yaml
- name: Sign container image
  run: |
    cosign sign --yes ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
  env:
    COSIGN_EXPERIMENTAL: "1"  # enables keyless signing
```

---

## Dependency provenance

### Lock file discipline

```bash
# Node.js — always commit package-lock.json
npm ci  # install from lock file (not npm install)

# Python — use poetry.lock or requirements.txt with hashes
pip install --require-hashes -r requirements.txt

# Go — go.sum is the lock file; never gitignore it
go mod verify  # verifies checksums in go.sum

# Rust — Cargo.lock; commit it for binaries, optional for libraries
```

### Typosquatting verification checklist

Before adding a new dependency:

1. Verify the package name on the registry (npmjs.com, pypi.org, pkg.go.dev)
2. Check the publish date — a package published last week with 0 prior versions is suspicious
3. Check download counts — a legitimate transitive dependency will have millions of downloads
4. Check the maintainer count and account age
5. Compare the package name to known similar names (e.g. `colourama` vs `colorama`)
6. For critical dependencies, read the source

Tools:
- `npm audit` — audits installed packages
- `pip-audit` — audits Python environments
- `ossf-scorecard` — rates open-source projects on security practices

---

## GitHub Actions hardening

### Pin actions to full commit SHA

```yaml
# Bad — tag can be moved by attacker
- uses: actions/checkout@v4

# Good — SHA is immutable
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af68  # v4.2.2
```

Use `renovate` or `dependabot` to keep SHA pins up to date automatically.

### Minimum permissions

```yaml
permissions:
  contents: read        # only what this job needs
  packages: write       # for image push
  id-token: write       # for OIDC keyless signing only
```

Set `permissions: {}` at the workflow level, then grant minimum permissions per job.

### OIDC token exchange (no long-lived secrets)

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@<sha>
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
    aws-region: us-east-1
    # No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed
```

### Scan for injection vectors

Untrusted values in `run:` steps:

```yaml
# Dangerous — PR title can contain shell metacharacters
- run: echo "PR title: ${{ github.event.pull_request.title }}"

# Safe — use environment variable, not inline interpolation
- run: echo "PR title: $PR_TITLE"
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
```

---

## Secret scanning

### Pre-commit hook setup (detect-secrets)

```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
# Add to .pre-commit-config.yaml:
#   - repo: https://github.com/Yelp/detect-secrets
#     hooks:
#       - id: detect-secrets
#         args: ['--baseline', '.secrets.baseline']
```

### gitleaks in CI

```yaml
- name: Scan for secrets
  uses: gitleaks/gitleaks-action@<sha>
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Kubernetes admission control for image verification

### Kyverno policy (verify cosign signature before pod admission)

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-cosign
      match:
        resources:
          kinds: [Pod]
      verifyImages:
        - imageReferences: ["registry.example.com/*"]
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/<org>/<repo>/.github/workflows/build.yml@refs/heads/main"
                    issuer: "https://token.actions.githubusercontent.com"
```
