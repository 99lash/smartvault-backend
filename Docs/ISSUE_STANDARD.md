# 📘 SmartVault – GitHub Issue Creation Standard

This document defines how issues must be written in SmartVault to ensure:

* Architectural clarity
* Security awareness
* Observability correctness
* Test enforcement
* Predictable execution

This is **mandatory for all new issues**.

---

## 1️⃣ Issue Title Format

Prefix with **Type + Surface + Short Description**.

### Format

```
<Type>: <Surface>: <Short Action-Oriented Summary>
```

### Types

* `Bug` — Something is broken or behaving incorrectly
* `Security` — Security vulnerability or hardening needed
* `Refactor` — Code improvement without changing behavior
* `Enhancement` — New feature or capability
* `Observability` — Metrics, logging, or monitoring improvement
* `Docs` — Documentation update
* `Infra` — Infrastructure or deployment change
* `Test` — Test addition or improvement

### Surfaces

* `API` — API layer (FastAPI routers, endpoints)
* `Application` — Application layer (use cases, services)
* `Domain` — Domain layer (business models, value objects)
* `Infrastructure` — Infrastructure layer (database, Redis, external services)
* `Internal Admin` — Internal admin endpoints (`/api/internal/admin/*`)
* `Internal Ops` — Internal ops endpoints (`/api/internal/ops/*`)
* `CI` — CI/CD pipeline
* `Docs` — Documentation

### Examples

* `Bug: API: /health/detailed always returns 200`
* `Security: API: Sanitize request_id header`
* `Refactor: Application: Consolidate duplicate get_db`
* `Observability: Application: Prevent false-positive unlock metrics`
* `Enhancement: Domain: Add vault sharing with permissions`
* `Test: Infrastructure: Add Redis connection failure tests`

---

## 2️⃣ Required Issue Template

Every issue must contain the following sections.

---

### 🧾 Summary

Short explanation of:

* What is wrong or needed
* Why it matters
* Which system layer it affects

**Keep this under 5 sentences.**

**Example:**
```
The /health/detailed endpoint always returns 200 OK even when 
database or Redis connections fail. This prevents Kubernetes 
readiness probes from detecting unhealthy instances. The issue 
is in the API layer health route handler.
```

---

### 📂 Scope (Files Affected)

List exact files.

**Example:**

```
app/api/v1/health.py
app/api/deps/db.py
app/application/use_cases/unlock_vault_with_pin.py
```

If multiple modules are affected, be explicit.

This prevents ambiguity and helps reviewers understand impact.

---

### ❗ Problem Statement

#### For Bugs

**Expected Behavior**

* What should happen

**Actual Behavior**

* What currently happens

**Example:**
```
Expected Behavior:
- /health/detailed should return 503 when database is unreachable
- Response should include error details in "checks" object

Actual Behavior:
- Endpoint returns 200 even when database connection fails
- Exception is logged but not reflected in response
```

---

#### For Enhancements / Refactors

* Current limitation
* Desired behavior
* Architectural alignment requirement

**Example:**
```
Current Limitation:
- Vaults can only have one owner
- No way to share vault access with team members

Desired Behavior:
- Vault owners can add members with specific roles (ADMIN, MEMBER, VIEWER)
- Members can unlock vault based on their permissions
- Access is revocable

Architectural Alignment Requirement:
- New VaultMembership domain model
- Updates to domain layer only, no infrastructure changes in this phase
```

---

### ⚠ Risk & Impact

This section is mandatory.

Select at least one:

* 🔐 **Security risk** — Vulnerability or authentication/authorization issue
* 📊 **Metrics corruption** — Incorrect metric tracking or labeling
* 🧪 **Test instability** — Flaky or unreliable tests
* 🚨 **Production outage risk** — Could cause downtime or service degradation
* 🧱 **Architectural boundary violation** — Layer dependency violation
* 🧍 **PII exposure** — Personal data logging or exposure risk
* 🧩 **Developer confusion / tech debt** — Code maintainability issue

Explain briefly.

**Example:**
```
⚠ Risk & Impact:
- 🚨 Production outage risk: Unhealthy instances remain in load balancer rotation
- 📊 Metrics corruption: Health check metrics don't reflect actual service state
```

---

### ✅ Acceptance Criteria

Checklist only. Must be testable.

**Example:**

```
- [ ] _check_database no longer async when using sync Session
- [ ] Health endpoint returns 503 on critical failure
- [ ] No duplicate get_db implementations exist
- [ ] All imports updated to canonical implementation
- [ ] Full test suite passes
```

If applicable:

```
- [ ] CI green
- [ ] No regression in metrics
- [ ] OpenAPI docs unchanged (if internal route)
```

---

### 🧪 Testing Requirements

Specify what level of testing is required.

#### Unit

* Required?
* What should be tested?

#### Integration

* Required?
* What external dependency must be mocked?

#### Manual Verification

Include curl examples when applicable:

```bash
# Example
curl -H "Authorization: Bearer <ADMIN_TOKEN>" \
  http://localhost:8000/api/internal/admin/users

# Health check with database down
docker compose stop db
curl http://localhost:8000/api/v1/health/detailed
# Should return 503
```

---

### 📈 Severity / Priority Matrix

Must include both.

#### Severity (Impact)

* `S0` – Critical (Security breach / Data loss)
* `S1` – High (Production risk)
* `S2` – Medium (Functional bug / Incorrect behavior)
* `S3` – Low (Docs / Minor improvement)

#### Priority (Execution Urgency)

* `P0` – Immediate
* `P1` – High
* `P2` – Normal
* `P3` – Backlog

**Example:**

```
Severity: S1
Priority: P1
```

---

### 🏷 Labels

Use consistent labels:

* `bug`
* `security`
* `observability`
* `internal-admin`
* `internal-ops`
* `tech-debt`
* `refactor`
* `documentation`
* `ci`
* `metrics`

---

## 3️⃣ Rules for SmartVault Issues

### Rule 1 — Always Specify Layer

Every issue must clearly indicate if it touches:

* **API layer** — FastAPI routers, endpoints, middleware
* **Application layer** — Use cases, services, ports
* **Domain layer** — Business models, value objects, events
* **Infrastructure layer** — Database, Redis, external services

**Clean Architecture boundaries must not be blurred.**

---

### Rule 2 — No Vague Issues

❌ **Bad:**

> Fix logging problem.

✅ **Good:**

> Security: API: Sanitize request_id before binding to structlog to prevent header injection.

---

### Rule 3 — Metrics Must Be Precise

If touching metrics:

* Specify counter/histogram name
* Specify labels
* Specify when increment should happen
* Specify when it must NOT happen

**Example:**

```
The track_vault_member_added counter must only increment when 
updated is truthy (i.e., when a member is actually added, not 
when the operation is a no-op).

Labels: vault_id, user_id, role
```

---

### Rule 4 — Internal Routes Must Not Leak

If the issue involves:

* `/api/internal/*`

It must verify:

* Hidden from OpenAPI
* Requires admin token
* Not accessible publicly

---

### Rule 5 — CI Must Be Mentioned

If issue affects:

* Dependencies
* Health checks
* Database
* Redis
* Metrics registry

**CI impact must be considered.**

**Example:**

```
Acceptance Criteria:
- [ ] CI pipeline passes with new dependency
- [ ] Docker build succeeds
- [ ] Health checks work in CI environment
```

---

## 4️⃣ SmartVault Issue Template (Copy-Paste)

Use this for all future issues:

```markdown
Title:
<Type>: <Surface>: <Short Summary>

---

## 🧾 Summary
<Short description>

## 📂 Scope (Files Affected)
```
<Exact files>
```

## ❗ Problem Statement

### For Bugs
**Expected Behavior:**

**Actual Behavior:**

### For Enhancements / Refactors
**Current Limitation:**

**Desired Behavior:**

**Architectural Alignment Requirement:**

## ⚠ Risk & Impact
- 

## ✅ Acceptance Criteria
- [ ]
- [ ]
- [ ] Full test suite passes

## 🧪 Testing Requirements

### Unit Tests


### Integration Tests


### Manual Verification


## 📈 Severity / Priority Matrix

**Severity:** 
**Priority:** 

## 🏷 Labels

```

---

## 5️⃣ Using the GitHub Issue Template

When creating a new issue in GitHub:

1. Click **"New Issue"**
2. Select **"SmartVault Standard Issue"** template
3. Fill out all required sections
4. Update the title using the format: `<Type>: <Surface>: <Summary>`
5. Add appropriate labels
6. Assign to team member if known
7. Link to related issues or PRs if applicable

---

## 6️⃣ Examples

### Example 1: Bug

```markdown
Title: Bug: API: /health/detailed always returns 200

## 🧾 Summary
The /health/detailed endpoint returns 200 OK even when database 
or Redis are unreachable. This prevents Kubernetes readiness 
probes from working correctly. Issue is in API layer.

## 📂 Scope (Files Affected)
```
app/api/v1/health.py
```

## ❗ Problem Statement

### For Bugs
**Expected Behavior:**
- Endpoint should return 503 when database is down
- Endpoint should return 503 when Redis is down
- Response should include failure details

**Actual Behavior:**
- Always returns 200 even on connection failures
- Exceptions are logged but not reflected in response

## ⚠ Risk & Impact
- 🚨 Production outage risk: Unhealthy instances stay in rotation
- 📊 Metrics corruption: Health metrics don't reflect reality

## ✅ Acceptance Criteria
- [ ] Returns 503 when database connection fails
- [ ] Returns 503 when Redis connection fails
- [ ] Response includes error details in checks object
- [ ] Full test suite passes
- [ ] Manual verification with docker compose stop db

## 🧪 Testing Requirements

### Unit Tests
Yes - Mock database and Redis failures

### Integration Tests
Yes - Test with actual containers stopped

### Manual Verification
```bash
# Stop database
docker compose stop db

# Should return 503
curl http://localhost:8000/api/v1/health/detailed
```

## 📈 Severity / Priority Matrix
**Severity:** S1
**Priority:** P1

## 🏷 Labels
bug, observability, production-risk
```

---

### Example 2: Enhancement

```markdown
Title: Enhancement: Domain: Add vault sharing with role-based permissions

## 🧾 Summary
Add ability for vault owners to share access with multiple users
using role-based permissions (ADMIN, MEMBER, VIEWER). This 
enhances the domain layer with VaultMembership model.

## 📂 Scope (Files Affected)
```
app/domain/models/vault.py
app/domain/models/vault_membership.py (new)
app/domain/value_objects/vault_role.py (new)
app/tests/domain/test_vault_membership.py (new)
```

## ❗ Problem Statement

### For Enhancements / Refactors
**Current Limitation:**
Vaults can only have one owner. No sharing capability.

**Desired Behavior:**
- Vault owners can add members with roles
- Members can unlock vault based on permissions
- Access is revocable
- Audit trail for membership changes

**Architectural Alignment Requirement:**
- Pure domain layer implementation
- No infrastructure dependencies
- Domain events for membership changes

## ⚠ Risk & Impact
- 🧱 Architectural boundary violation risk: Must stay in domain layer
- 🧩 Developer confusion: Clear separation needed

## ✅ Acceptance Criteria
- [ ] VaultMembership domain model created
- [ ] VaultRole value object created (ADMIN, MEMBER, VIEWER)
- [ ] Vault.add_member() method implemented
- [ ] Vault.remove_member() method implemented
- [ ] Domain events emitted for membership changes
- [ ] Unit tests for all membership operations
- [ ] Full test suite passes
- [ ] No infrastructure imports in domain layer

## 🧪 Testing Requirements

### Unit Tests
Yes - Test all membership operations, role validation, events

### Integration Tests
Not in this phase - domain layer only

### Manual Verification
N/A - domain layer testing via unit tests

## 📈 Severity / Priority Matrix
**Severity:** S2
**Priority:** P2

## 🏷 Labels
enhancement, domain-layer
```

---

### Example 3: Security

```markdown
Title: Security: API: Sanitize request_id header to prevent injection

## 🧾 Summary
The request_id from X-Request-ID header is bound directly to 
structlog without sanitization. Malicious headers could inject
newlines or control characters into logs, corrupting log parsers.
Affects API middleware layer.

## 📂 Scope (Files Affected)
```
app/api/middleware/request_id.py
app/tests/api/middleware/test_request_id.py
```

## ❗ Problem Statement

### For Bugs
**Expected Behavior:**
- request_id should only contain alphanumeric + hyphen + underscore
- Invalid characters should be stripped or rejected
- Log injection should be impossible

**Actual Behavior:**
- Any header value is accepted
- Newlines and control characters are logged
- Could corrupt log aggregation systems

## ⚠ Risk & Impact
- 🔐 Security risk: Log injection vulnerability
- 📊 Metrics corruption: Could affect metric labels

## ✅ Acceptance Criteria
- [ ] request_id validated against safe character set [a-zA-Z0-9_-]
- [ ] Invalid characters stripped or request rejected
- [ ] Test for newline injection blocked
- [ ] Test for control character injection blocked
- [ ] Full test suite passes
- [ ] Security scan clean

## 🧪 Testing Requirements

### Unit Tests
Yes - Test various malicious payloads

### Integration Tests
Yes - Test via API endpoints

### Manual Verification
```bash
# Should strip invalid chars
curl -H "X-Request-ID: test\ninjection" http://localhost:8000/api/v1/health

# Check logs - should not contain newline
```

## 📈 Severity / Priority Matrix
**Severity:** S0
**Priority:** P0

## 🏷 Labels
security, bug, critical
```

---

## 7️⃣ FAQ

### Q: Do I need to fill out every section?

**A:** Yes. All sections are mandatory. Use "N/A" with explanation if truly not applicable.

### Q: Can I create issues without the template?

**A:** No. All issues must follow this standard for consistency and completeness.

### Q: What if I'm not sure about severity/priority?

**A:** Make your best estimate. Reviewers will adjust if needed. When in doubt, mark as S2/P2.

### Q: Can I add custom sections?

**A:** Yes, but don't remove required sections. Additional context is welcome.

### Q: How detailed should file scope be?

**A:** List specific files. Avoid "app/api/*" — be explicit about which files will change.

---

## 8️⃣ Benefits of This Standard

✅ **Clarity** — No ambiguity about what needs to be done

✅ **Architectural alignment** — Layer boundaries are explicit

✅ **Risk awareness** — Security and production impacts are front and center

✅ **Testability** — Testing requirements are defined upfront

✅ **Prioritization** — Severity and priority help with backlog management

✅ **Quality** — Consistent format improves code review efficiency

✅ **Observability** — Metrics and logging considerations built in

✅ **Onboarding** — New contributors understand expectations

---

## 9️⃣ Enforcement

* All issues must pass template compliance check
* PRs should reference issues following this standard
* Code reviewers verify issue completeness before approval
* Non-compliant issues will be sent back for revision

---

**This standard is mandatory for all SmartVault issues.**

For questions or suggestions, open a discussion in the repository.
