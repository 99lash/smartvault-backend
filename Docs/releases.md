# SmartVault Releases & Checkpoints

This document tracks **production-ready releases**, **pre-release checkpoints**, and **recovery references** for the SmartVault project.

> Policy: Production releases use **SemVer** tags (`vMAJOR.MINOR.PATCH`).  
> Optional suffixes are used for non-prod checkpoints (e.g., `-rc.1`, `-preobs`, `-backup.20260212`).

---

## 1) Tag Strategy (Production-Ready)

### 1.1 Production Releases (SemVer)

**Format**

```
v{MAJOR}.{MINOR}.{PATCH}
```

**Examples**
- `v1.0.0` — first stable release
- `v1.1.0` — new features, backward compatible
- `v1.1.1` — patch / bugfix

**Rules**
- `MAJOR`: breaking API changes
- `MINOR`: new features, backward compatible
- `PATCH`: bugfixes only, backward compatible

---

### 1.2 Pre-Releases (for staging / QA)

**Format**

```
v{MAJOR}.{MINOR}.{PATCH}-{channel}.{N}
```

**Channels**
- `rc` (release candidate)
- `beta`
- `alpha`

**Examples**
- `v1.1.0-rc.1`
- `v1.2.0-beta.2`

---

### 1.3 Operational Checkpoints (Non-Release Backups)

Use this for "savepoints" that are not official product releases.

**Format**

```
checkpoint-{YYYYMMDD}-{slug}
```

**Examples**
- `checkpoint-20260212-pre-observability`
- `checkpoint-20260212-post-sentry`

> Note: Your existing tag `backup-2026-02-12` is valid; consider standardizing it to the `checkpoint-*` format going forward.

---

## 2) Release Branching Model

### Branches
- `main`: production-ready, tagged releases only
- `dev`: integration branch for upcoming changes
- `release/vX.Y.Z`: stabilization branch for a release
- `hotfix/vX.Y.(Z+1)`: urgent production fix

### High-Level Flow
1. Feature work → `dev`
2. Stabilize → `release/vX.Y.Z`
3. Tag on `main` → `vX.Y.Z`
4. If urgent bug → `hotfix/*` → tag patch

---

## 3) Required Release Artifacts

For each **production** tag:
- ✅ tests passing
- ✅ DB migrations reviewed (if any)
- ✅ Docker compose / deployment updated (if needed)
- ✅ CHANGELOG entry added
- ✅ Git tag annotated and pushed
- ✅ GitHub Release created (optional but recommended)

---

## 4) Commands Cheat Sheet

### 4.1 List / Inspect Tags

```bash
git tag --list
git tag -l "v*"
git show v1.0.0
```

### 4.2 Create an Annotated Production Tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 4.3 Create an Annotated Pre-Release Tag

```bash
git tag -a v1.1.0-rc.1 -m "Release candidate 1 for v1.1.0"
git push origin v1.1.0-rc.1
```

### 4.4 Create an Operational Checkpoint Tag

```bash
git tag -a checkpoint-20260212-pre-observability -m "Stable backup before observability integration"
git push origin checkpoint-20260212-pre-observability
```

---

## 5) Recovery (Safe Defaults)

### 5.1 Checkout a Tag (Read-only / Inspection)

```bash
git checkout v1.0.0
```

### 5.2 Create a Recovery Branch from a Tag (Recommended)

```bash
git checkout -b recovery/v1.0.0 v1.0.0
git push -u origin recovery/v1.0.0
```

### 5.3 Restore a Specific File or Directory from a Tag

```bash
git checkout v1.0.0 -- path/to/file.py
git checkout v1.0.0 -- app/infrastructure/
```

### 5.4 Compare Two Releases / Checkpoints

```bash
git diff v1.0.0 v1.1.0
git diff checkpoint-20260212-pre-observability v1.1.0-rc.1
```

> Avoid `git push --force` as a recovery mechanism. Prefer creating recovery branches.

---

## 6) Release History

> Keep this section **short and factual**. Put deep technical detail in CHANGELOG / docs.

### v1.0.0

* **Type:** Production release
* **Summary:** Baseline stable release
* **Notes:** First tagged production version

### checkpoint-20260212-pre-observability

* **Type:** Operational checkpoint
* **Message:** Stable backup before observability integration
* **Purpose:** Reference point before Prometheus/Grafana rollout

---

## 7) Release Checklist (Production)

- [ ] `dev` is green (tests pass)
- [ ] Create stabilization branch:
  ```bash
  git checkout dev
  git checkout -b release/vX.Y.Z
  git push -u origin release/vX.Y.Z
  ```
- [ ] Fix only release blockers on `release/vX.Y.Z`
- [ ] Merge to `main`:
  ```bash
  git checkout main
  git merge --no-ff release/vX.Y.Z
  git push origin main
  ```
- [ ] Tag release on `main`:
  ```bash
  git tag -a vX.Y.Z -m "Release vX.Y.Z"
  git push origin vX.Y.Z
  ```
- [ ] Merge back to `dev`:
  ```bash
  git checkout dev
  git merge --no-ff main
  git push origin dev
  ```
- [ ] (Optional) Create GitHub Release + attach notes

---

## 8) Files That Should Exist Alongside This Doc

* `CHANGELOG.md` — user-facing changes per release
* `docs/observability.md` — Prometheus/Grafana/Sentry setup
* `docs/runbook.md` — operational procedures / rollback playbook (optional)

---

## Appendix A) Recommended Naming Conventions

### Release branches
* `release/v1.2.0`

### Hotfix branches
* `hotfix/v1.2.1`

### Recovery branches
* `recovery/v1.2.0`

### Checkpoints
* `checkpoint-20260212-pre-observability`
* `checkpoint-20260212-post-sentry`n 