# Changelog

All notable changes to **SmartVault** will be documented in this file.

The format is based on:
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning (SemVer)](https://semver.org/)

---

## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

### Security
-

---

## [backup-2026-02-12] - 2026-02-12

> Operational checkpoint (non-production tag)

### Context
Created as a stable backup checkpoint after adding **Sentry error tracking**, and before continuing the broader observability rollout (e.g., Prometheus/Grafana/internal ops work).

### Added
- Sentry error tracking integration (FastAPI integration)
- Environment-driven Sentry configuration (DSN, environment, sample rates)
- `.env.example` Sentry configuration placeholders

### Security
- Sentry configured to keep PII sending disabled by default (`SENTRY_SEND_DEFAULT_PII=false`)
- Sensitive data scrubbing expected/required (tokens/PIN/passwords must not be sent)

### Rollback Notes
- No database migrations expected at this checkpoint
- Safe rollback by branching from this tag and redeploying

### Reference
- Tag points to commit: `4dc7414903bd650d7b1db24ee267130d43843d8f`

---

# Versioning Guidelines

- `MAJOR` — Breaking API or contract changes
- `MINOR` — Backward-compatible feature additions
- `PATCH` — Backward-compatible bug fixes

Operational checkpoints:
- Not production releases
- Used for operational safety and architecture savepoints
- Documented here for historical clarity
