# Internal Services — Data Structures

> Auto-generated from `internal_admin_api_ui_contract.md`, `internal-api-examples/`, and ORM models.
> All internal endpoints are under `/internal`, protected by `X-Admin-Token` header.

---

## Table of Contents

- [API Response Structures](#api-response-structures)
  - [1. Business Metrics](#1-business-metrics)
  - [2. Security Alerts](#2-security-alerts)
  - [3. Ops Summary](#3-ops-summary)
  - [4. Diagnostics](#4-diagnostics)
  - [5. Rate Limits](#5-rate-limits)
  - [6. Sessions](#6-sessions)
  - [7. Email Notifications](#7-email-notifications)
  - [8. Audit Logs](#8-audit-logs)
  - [9. API Key Management](#9-api-key-management)
- [Database Schema](#database-schema)
  - [users](#users)
  - [vaults](#vaults)
  - [access_logs](#access_logs)
  - [admin_audit_logs](#admin_audit_logs)
  - [api_keys](#api_keys)
  - [vault_authorizations](#vault_authorizations)
- [Open Gaps](#open-gaps)

---

## API Response Structures

---

### 1. Business Metrics

#### `GET /internal/business/overview`

```
generated_at            datetime
users
  total                 int
  new_today             int
  new_this_week         int
vaults
  total                 int
  with_pin              int
  by_status             dict[str, int]   ⚠️ keys unknown (data-driven)
members
  total_authorizations  int
  by_role               dict[str, int]   ⚠️ keys unknown (data-driven)
```

#### `GET /internal/business/activity`

Query params: `hours` (1–168, default 24), `limit` (1–100, default 50)

```
generated_at       datetime
period_hours       int
summary
  total_events     int
  vault_unlocks    int
  failed_unlocks   int
  pin_operations   int
  member_changes   int
  state_changes    int
entries[]
  id               str
  vault_id         str
  user_id          str | null
  action           str
  method           str
  metadata         dict | null
  created_at       datetime
```

#### `GET /internal/business/trends`

Query params: `days` (7–90, default 30)

```
generated_at       datetime
period_days        int
period_start       str (YYYY-MM-DD)
period_end         str (YYYY-MM-DD)
user_signups / vault_provisioning
  daily[]
    date           str (YYYY-MM-DD)
    count          int
  total            int
  average_per_day  float
  peak_date        str | null
  peak_count       int
  change_pct       float | null
```

---

### 2. Security Alerts

#### `GET /internal/security/alerts`

```
generated_at       datetime
status             "ok" | "warning" | "critical"
active_alerts[]
  type             str
  severity         "low" | "medium" | "high" | "critical"
  message          str
  count            int
  threshold        int
  window           "1h" | "24h"
last_24h
  failed_unlocks_1h    int
  failed_unlocks_24h   int
  pin_lockouts_24h     int
```

**Thresholds:**
- Failed unlocks: ≥5/hr → warning, ≥20/hr → critical
- PIN lockouts: ≥3/24h → warning, ≥10/24h → critical

---

### 3. Ops Summary

#### `GET /internal/ops/summary`

```
generated_at       datetime
overall_status     "ok" | "warning" | "critical"
business
  users            { total, new_today, new_this_week }
  vaults           { total, with_pin, by_status }
  members          { total_authorizations, by_role }
security
  status           str
  failed_unlocks_1h    int
  failed_unlocks_24h   int
  pin_lockouts_24h     int
  alert_count          int
activity
  period_hours         int
  total_events         int
  vault_unlocks        int
  failed_unlocks       int
  pin_operations       int
  member_changes       int
  state_changes        int
```

---

### 4. Diagnostics

#### `GET /internal/ops/diagnostics/redis`

```
status             "healthy" | "unhealthy"
connected          bool
memory_used_mb     float
total_keys         int
uptime_seconds     int
checked_at         datetime
```

#### `GET /internal/ops/diagnostics/database`

```
status             "healthy" | "unknown"
pool_size          int
checked_out        int
overflow           int
checked_at         datetime
```

#### `GET /internal/ops/diagnostics/websockets`

```
total_users              int
total_user_connections   int
total_vaults             int
subscriptions            int
online_vaults            list[str]
checked_at               datetime
```

---

### 5. Rate Limits

#### `GET /internal/ops/rate-limits`

```
total_active_keys  int
top_violators[]          (max 10, sorted desc by count)
  key              str
  current_count    int
  ttl_seconds      int
by_category        dict[str, int]
checked_at         datetime
```

---

### 6. Sessions

#### `GET /internal/ops/sessions/stats`

```
total_active_tokens  int
top_users[]          (max 10, sorted desc)
  user_id          str
  token_count      int
checked_at         datetime
```

#### `DELETE /internal/ops/sessions/{user_id}`

```
user_id            str   (echo)
sessions_revoked   int   (0 if none found — no 404)
```

---

### 7. Email Notifications

#### `GET /internal/ops/notifications/email`

```
service            str   (always "smtp")
status             str   (always "healthy" currently)
sent_today         int
failed_today       int
note               str   (static guidance string)
checked_at         datetime
```

> ⚠️ `sent_today` / `failed_today` always return 0 — counters not yet wired into `SMTPEmailService`.

---

### 8. Audit Logs

#### `GET /internal/ops/audit`

Query params: `page` (≥1, default 1), `limit` (1–100, default 50), `action` (str | null, optional exact-match filter)

```
items[]
  id               int
  action           str
  target_type      str
  target_id        str | null
  details          dict | null
  ip_address       str | null
  created_at       datetime
total              int
page               int
pages              int
```

Ordered by `created_at DESC`.

---

### 9. API Key Management

#### `GET /internal/ops/api-keys`

Query params: `active_only` bool (default true)

```
items[]
  id               int
  name             str
  created_by       str
  last_used_at     datetime | null
  expires_at       datetime | null
  is_active        bool
  created_at       datetime
```

Ordered by `created_at DESC`.

#### `POST /internal/ops/api-keys`

**Request body:**
```
name               str        (required, max 100 chars)
expires_in_days    int | null (optional; no bounds enforced)
```

**Response** (key shown **once only** — not stored in DB):
```
id                 int
key                str   (format: sk_<token_urlsafe(32)>)
name               str
expires_at         datetime | null
```

Status: `201 Created`

#### `DELETE /internal/ops/api-keys/{key_id}`

- `204 No Content` — soft-revoke (sets `is_active=False`)
- `404` — `{"detail": "API key {key_id} not found."}`

---

## Database Schema

> Source: `app/infrastructure/db/models/`
> These are the core tables. Internal endpoints query these — they do not have their own tables.

---

### `users`

| Column | Type | Constraints |
|---|---|---|
| `id` | String(36) | PK |
| `email` | String(320) | not null, unique, indexed |
| `password_hash` | Text | not null |
| `full_name` | String(200) | nullable |
| `created_at` | DateTime(tz) | not null, server default |
| `updated_at` | DateTime(tz) | not null, server default, auto-update |

---

### `vaults`

| Column | Type | Constraints |
|---|---|---|
| `id` | String | PK |
| `owner_id` | String | not null |
| `hardware_uuid` | String | not null, unique, indexed |
| `vault_name` | String | nullable |
| `status` | String | not null ⚠️ no enum enforced |
| `last_seen_at` | DateTime(tz) | nullable |
| `pin_hash` | String(255) | nullable |
| `pin_set_at` | DateTime(tz) | nullable |
| `created_at` | DateTime(tz) | not null, server default |
| `updated_at` | DateTime(tz) | not null, server default, auto-update |

---

### `access_logs`

| Column | Type | Constraints |
|---|---|---|
| `id` | String | PK |
| `vault_id` | String | not null, FK → vaults.id (CASCADE) |
| `user_id` | String | nullable, FK → users.id (SET NULL) |
| `action` | String(50) | not null ⚠️ full value set unknown |
| `method` | String(20) | not null ⚠️ full value set unknown |
| `metadata` | JSON | nullable |
| `created_at` | DateTime(tz) | not null, server default |

**Indexes:** `(vault_id, created_at)`, `(user_id, created_at)`

---

### `admin_audit_logs`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, autoincrement |
| `action` | String(100) | not null |
| `target_type` | String(50) | not null |
| `target_id` | String(255) | nullable |
| `details` | JSON | nullable |
| `ip_address` | String(45) | nullable |
| `created_at` | DateTime(tz) | not null, server default |

**Indexes:** `created_at`, `action`

> Note: No `admin_user_id` column — internal API uses a shared `X-Admin-Token`, not individual user identities.

---

### `api_keys`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, autoincrement |
| `key_hash` | String(255) | not null, unique |
| `name` | String(100) | not null |
| `created_by` | String(255) | not null |
| `last_used_at` | DateTime(tz) | nullable |
| `expires_at` | DateTime(tz) | nullable |
| `is_active` | Boolean | not null, default true |
| `created_at` | DateTime(tz) | not null, server default |

**Index:** `is_active`

> Note: `key_hash` is stored, not the raw key. The raw key is returned once on creation only.

---

### `vault_authorizations`

| Column | Type | Constraints |
|---|---|---|
| `id` | String | PK |
| `vault_id` | String | not null, FK → vaults.id (CASCADE) |
| `user_id` | String | not null, FK → users.id (CASCADE) |
| `role` | String(20) | not null ⚠️ no enum enforced |
| `granted_by` | String | nullable, FK → users.id (SET NULL) |
| `granted_at` | DateTime(tz) | not null |

**Unique constraint:** `(vault_id, user_id)`

**Relationships:** `vault` → VaultORM, `user` → UserORM, `granter` → UserORM

---

## Open Gaps

| Gap | Location | Notes |
|---|---|---|
| `vault.status` enum values | `vaults.by_status`, `vaults.status` | Data-driven; no enum enforced in DB or ORM |
| `vault_authorization.role` enum values | `members.by_role`, `vault_authorizations.role` | Data-driven; no enum enforced |
| `access_logs.action` full value set | `entries[].action`, `access_logs.action` | Partial list known; more may exist |
| `access_logs.method` full value set | `entries[].method`, `access_logs.method` | Unknown |
| `expires_in_days` validation | POST /ops/api-keys | Accepts negative/zero; no bounds enforced |
| Audit logging on API key create/revoke | POST + DELETE /ops/api-keys | Not wired |
| Email counters | `sent_today`, `failed_today` | Always 0; not wired into SMTPEmailService |
