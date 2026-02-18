# Database Seeder

Seeds the database with test data for development and testing.

---

## Usage

```bash
# Seed the database (skips if data already exists)
make seed

# Reset database and re-seed from scratch
make reseed
```

---

## Test Credentials

All users share the same password: `smartvault123!`

| Email | Password | Role | Access |
|-------|----------|------|--------|
| `owner@smartvault.dev` | `smartvault123!` | **Owner** | Full access to all vaults |
| `admin@smartvault.dev` | `smartvault123!` | **Admin** | Can unlock + manage members on Home Vault |
| `member@smartvault.dev` | `smartvault123!` | **Member** | Can unlock Home Vault only |
| `viewer@smartvault.dev` | `smartvault123!` | **Viewer** | View-only access on Home Vault |

---

## Seed Data Overview

### Users (4)

| Name | Email | Role |
|------|-------|------|
| John Owner | owner@smartvault.dev | Owner |
| Jane Admin | admin@smartvault.dev | Admin |
| Mike Member | member@smartvault.dev | Member |
| Vera Viewer | viewer@smartvault.dev | Viewer |

### Vaults (2)

| Name | Hardware UUID | Status | PIN | Owner |
|------|--------------|--------|-----|-------|
| Home Vault | ESP32-SV-001-ABCDEF | LOCKED | `482916` | owner@smartvault.dev |
| Office Vault | ESP32-SV-002-GHIJKL | UNLOCKED | (none) | owner@smartvault.dev |

### Vault Authorizations (3)

All on **Home Vault**:

| User | Role | Granted By |
|------|------|------------|
| admin@smartvault.dev | ADMIN | Owner |
| member@smartvault.dev | MEMBER | Owner |
| viewer@smartvault.dev | VIEWER | Admin |

### Access Logs (3)

| Action | User | Method | Vault |
|--------|------|--------|-------|
| VAULT_UNLOCKED | Owner | PIN | Home Vault |
| MEMBER_ADDED | Owner | COMMAND | Home Vault |
| VAULT_UNLOCK_FAILED | Member | PIN | Home Vault |

---

## Notes

- The seeder is **idempotent** — it skips if users already exist in the database.
- To re-seed, run `make reseed` (resets DB + Redis, re-runs migrations, then seeds).
- Passwords are hashed with PBKDF2-SHA256 (same as production).
- PIN `482916` is also hashed with PBKDF2.
