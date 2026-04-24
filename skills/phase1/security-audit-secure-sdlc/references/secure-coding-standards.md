# Secure coding standards

## Purpose

These standards apply to all code delivered by either company in this engagement. They are not aspirational guidelines — they are minimum requirements. Findings against these standards in code review block PR merge at Gate 2.

---

## Universal rules (all languages)

### 1. Input validation

**Rule:** Validate ALL input at trust boundaries. Reject invalid input; never attempt to sanitise or coerce dangerous values.

```python
# BAD — trying to clean potentially dangerous input
def get_device(device_id):
    clean_id = device_id.replace("'", "").replace(";", "")  # Do not do this
    return db.query(f"SELECT * FROM devices WHERE id = '{clean_id}'")

# GOOD — parameterised query, validation upfront
def get_device(device_id: str):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', device_id):
        raise ValidationError("device_id must be 1-64 alphanumeric characters")
    return db.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
```

**Checklist:**
- [ ] Input type validated (not just cast)
- [ ] Input length bounded (reject overlength values)
- [ ] Input format validated against an allowlist pattern where applicable
- [ ] Numeric inputs have min/max range checks
- [ ] Enum inputs validated against the defined set of values

### 2. SQL and NoSQL injection prevention

**Rule:** Never build queries by string concatenation with user-controlled values. Always use parameterised queries or ORM safe methods.

```go
// BAD — SQL injection via string format
query := fmt.Sprintf("SELECT * FROM events WHERE device_id = '%s'", deviceID)

// GOOD — parameterised
row := db.QueryRowContext(ctx, "SELECT * FROM events WHERE device_id = $1", deviceID)
```

### 3. Authentication and authorisation

**Rule:** Every endpoint that modifies state or returns non-public data must verify both authentication (who you are) and authorisation (what you are allowed to do). These are separate checks.

```python
# BAD — authentication checked, authorisation assumed from route path
@app.route("/admin/users")
@require_authenticated  # This only checks that the user is logged in
def list_all_users():
    return User.query.all()  # Any authenticated user gets all users

# GOOD — explicit authorisation check
@app.route("/admin/users")
@require_authenticated
@require_permission("admin:users:read")
def list_all_users():
    return User.query.all()
```

**Checklist:**
- [ ] No endpoint is unauthenticated unless explicitly designed to be public
- [ ] Authorisation checked server-side on every request (not cached from previous call)
- [ ] Resource ownership validated (user can only access their own resources unless admin)
- [ ] Horizontal privilege escalation prevented (user cannot manipulate IDs to access others' data)

### 4. Secrets and credentials

**Rule:** Zero secrets in code. Zero secrets in configuration files committed to version control. Zero secrets in container images or environment variable files that are committed.

```yaml
# BAD — secret in config file (even in example/template)
database:
  host: db.example.com
  password: "super-secret-password-123"  # NEVER commit this

# GOOD — reference to secrets manager
database:
  host: db.example.com
  password: "${vault:secret/data/db#password}"  # Resolved at runtime
```

**Detection tools required:**
- `gitleaks` or `detect-secrets` pre-commit hook to prevent accidental commit
- GitHub secret scanning enabled on all repositories
- CI pipeline fails on any detected secret

### 5. Error handling and logging

**Rule:** Log the full error server-side. Return a sanitised, consistent error envelope to the caller. Never expose internal details in API responses.

```python
# BAD — internal details in response
except DatabaseError as e:
    return jsonify({"error": str(e)}), 500
    # Returns: {"error": "psycopg2.errors.UndefinedTable: relation \"devics\" does not exist"}

# GOOD — sanitised response, full detail in logs
except DatabaseError as e:
    logger.error("Database error on device lookup", extra={
        "error": str(e),
        "device_id": device_id,
        "trace_id": request.trace_id
    })
    return jsonify({
        "error": "internal_server_error",
        "message": "An internal error occurred. Reference: " + request.trace_id
    }), 500
```

**Logging checklist:**
- [ ] All authentication failures logged with timestamp, IP, attempted identity
- [ ] All authorisation failures logged with user identity and requested resource
- [ ] All state-changing operations logged with actor, action, resource, outcome
- [ ] Sensitive values (passwords, tokens, PII) never written to logs
- [ ] Log entries include trace_id for correlation with upstream requests

---

## Python-specific rules

### Dependency management
- Use `pip-compile` (pip-tools) or Poetry to generate pinned `requirements.txt` / `pyproject.lock`
- Commit the lock file; never commit only `requirements.in` without the resolved lock
- Run `pip-audit` in CI to detect CVEs in dependencies

### Common Python pitfalls
```python
# BAD — shell injection via subprocess
import subprocess
result = subprocess.run(f"ls {user_path}", shell=True)  # Never use shell=True with user input

# GOOD — no shell, args as list
result = subprocess.run(["ls", user_path], capture_output=True, check=True)

# BAD — insecure deserialization
import pickle
data = pickle.loads(user_supplied_bytes)  # Arbitrary code execution

# GOOD — use json for structured data
import json
data = json.loads(user_supplied_bytes)  # Only data, no code

# BAD — YAML with full loader
import yaml
config = yaml.load(user_data)  # yaml.load() with default loader allows code execution

# GOOD — safe loader
config = yaml.safe_load(user_data)
```

---

## Go-specific rules

### Common Go pitfalls
```go
// BAD — integer overflow in security context
var userID int32 = int32(userIDFromRequest)  // Truncation if ID > 2^31

// GOOD — use appropriate integer type and validate range
userID, err := strconv.ParseInt(userIDFromRequest, 10, 64)
if err != nil || userID <= 0 {
    return nil, ErrInvalidUserID
}

// BAD — goroutine leak via unclosed channel or context
go func() {
    result := longRunningOperation()  // Goroutine leaks if caller stops waiting
    resultChan <- result
}()

// GOOD — respect context cancellation
go func() {
    select {
    case <-ctx.Done():
        return
    case resultChan <- longRunningOperation(ctx):
    }
}()

// BAD — error silencing
result, _ := dangerousOperation()  // Silenced error

// GOOD — always handle errors
result, err := dangerousOperation()
if err != nil {
    return fmt.Errorf("dangerous operation failed: %w", err)
}
```

### TLS configuration
```go
// BAD — insecure TLS config
tlsConfig := &tls.Config{
    InsecureSkipVerify: true,  // Never in production
}

// GOOD — secure TLS config with minimum version
tlsConfig := &tls.Config{
    MinVersion:               tls.VersionTLS12,
    PreferServerCipherSuites: true,
    CipherSuites: []uint16{
        tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
        tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
    },
}
```

---

## TypeScript / JavaScript-specific rules

### Common pitfalls
```typescript
// BAD — prototype pollution
function merge(target: any, source: any) {
    for (const key of Object.keys(source)) {
        target[key] = source[key];  // Allows __proto__ or constructor pollution
    }
}

// GOOD — safe merge, reject dangerous keys
function merge(target: Record<string, unknown>, source: Record<string, unknown>) {
    const dangerous = new Set(['__proto__', 'constructor', 'prototype']);
    for (const key of Object.keys(source)) {
        if (!dangerous.has(key)) {
            target[key] = source[key];
        }
    }
}

// BAD — eval with user input (XSS / code injection)
const result = eval(userInput);  // Never

// BAD — innerHTML with user content (XSS)
element.innerHTML = userProvidedHtml;  // Never without sanitisation

// GOOD — textContent for user data
element.textContent = userProvidedText;  // Text only, no HTML parsing
```

### npm dependency rules
- Commit `package-lock.json` or `yarn.lock`
- Run `npm audit` in CI; block on Critical severities
- Avoid packages with `postinstall` scripts that run arbitrary code unless thoroughly reviewed

---

## Code review security checklist

Use this during every PR review for security-sensitive changes:

### Input handling
- [ ] New inputs validated at trust boundary entry points
- [ ] No new SQL string concatenation with external values
- [ ] New file path operations validate against a safe base directory (path traversal)
- [ ] New XML parsing does not enable external entity processing (XXE)

### Authentication and authorisation
- [ ] New endpoints have authentication middleware applied
- [ ] New endpoints have authorisation checks that verify the caller's permission to the specific resource
- [ ] No new bypass of authentication for "convenience" (test flags, debug modes, skipped middleware)

### Data handling
- [ ] No new secrets written to logs
- [ ] No new PII written to unencrypted storage without explicit design approval
- [ ] New database columns containing sensitive data are flagged for encryption review

### Dependencies
- [ ] No new dependencies added without a brief security rationale in the PR description
- [ ] No new dependencies pinned to a range (e.g., `^1.0.0`) without understanding the update policy

### Error handling
- [ ] All new error paths return sanitised messages to callers
- [ ] All new error paths log sufficient context for incident investigation
