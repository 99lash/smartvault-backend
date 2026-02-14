---
name: SmartVault Standard Issue
about: Create an issue following SmartVault architectural and quality standards
title: '<Type>: <Surface>: <Short Summary>'
labels: ''
assignees: ''
---

<!-- 
📘 SmartVault Issue Creation Standard

This template ensures:
- Architectural clarity
- Security awareness
- Observability correctness
- Test enforcement
- Predictable execution

Please fill out all sections below.
-->

## 🧾 Summary

<!-- Short explanation of:
- What is wrong or needed
- Why it matters
- Which system layer it affects

Keep this under 5 sentences. -->



## 📂 Scope (Files Affected)

<!-- List exact files that will be modified or created.

Example:
```
app/api/v1/health.py
app/api/deps/db.py
app/application/use_cases/unlock_vault_with_pin.py
```

If multiple modules are affected, be explicit. This prevents ambiguity. -->

```

```

## ❗ Problem Statement

<!-- Choose the appropriate section below based on issue type -->

### For Bugs

**Expected Behavior**


**Actual Behavior**


---

### For Enhancements / Refactors

**Current Limitation:**


**Desired Behavior:**


**Architectural Alignment Requirement:**


## ⚠ Risk & Impact

<!-- This section is mandatory. Select at least one and explain briefly:

- 🔐 Security risk
- 📊 Metrics corruption
- 🧪 Test instability
- 🚨 Production outage risk
- 🧱 Architectural boundary violation
- 🧍 PII exposure
- 🧩 Developer confusion / tech debt
-->



## ✅ Acceptance Criteria

<!-- Checklist only. Must be testable. -->

- [ ] 
- [ ] 
- [ ] 
- [ ] Full test suite passes

<!-- If applicable, add: -->
<!-- - [ ] CI green -->
<!-- - [ ] No regression in metrics -->
<!-- - [ ] OpenAPI docs unchanged (if internal route) -->

## 🧪 Testing Requirements

### Unit Tests
<!-- Required? What should be tested? -->


### Integration Tests
<!-- Required? What external dependency must be mocked? -->


### Manual Verification
<!-- Include curl examples when applicable:

```bash
curl -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/...
```
-->


## 📈 Severity / Priority Matrix

<!-- Select one severity and one priority level:

Severity (Impact):
- S0 – Critical (Security breach / Data loss)
- S1 – High (Production risk)
- S2 – Medium (Functional bug / Incorrect behavior)
- S3 – Low (Docs / Minor improvement)

Priority (Execution Urgency):
- P0 – Immediate
- P1 – High
- P2 – Normal
- P3 – Backlog
-->

**Severity:** 

**Priority:**

## 🏷 Labels

<!-- Use consistent labels (select all that apply):
- bug
- security
- observability
- internal-admin
- internal-ops
- tech-debt
- refactor
- documentation
- ci
- metrics
-->

