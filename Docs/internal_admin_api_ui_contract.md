# Internal Admin API - UI Contract (as of 2026-02-16)

All endpoints live under the `/internal` FastAPI router (`app/api/internal/router.py`). The router is tagged `internal`, excluded from the public schema, and protected by the `require_admin_token` dependency (`app/api/internal/deps/admin_auth.py:21`).

## Router Map

| METHOD | PATH | Handler (file:line) |
| --- | --- | --- |
| GET | /internal/ping | app/api/internal/router.py:30 |
| GET | /internal/business/overview | app/api/internal/business/overview.py:61 |
| GET | /internal/business/activity | app/api/internal/business/activity.py:61 |
| GET | /internal/business/trends | app/api/internal/business/trends.py:69 |
| GET | /internal/security/alerts | app/api/internal/security/alerts.py:190 |
| GET | /internal/ops/summary | app/api/internal/ops/summary.py:130 |
| GET | /internal/ops/diagnostics/redis | app/api/internal/ops/diagnostics.py:67 |
| GET | /internal/ops/diagnostics/websockets | app/api/internal/ops/diagnostics.py:84 |
| GET | /internal/ops/diagnostics/database | app/api/internal/ops/diagnostics.py:102 |
| GET | /internal/ops/rate-limits | app/api/internal/ops/rate_limits.py:49 |
| GET | /internal/ops/sessions/stats | app/api/internal/ops/sessions.py:56 |
| DELETE | /internal/ops/sessions/{user_id} | app/api/internal/ops/sessions.py:86 |
| GET | /internal/ops/notifications/email | app/api/internal/ops/notifications.py:36 |
| GET | /internal/ops/audit | app/api/internal/ops/audit.py:56 |
| GET | /internal/ops/api-keys | app/api/internal/ops/api_keys.py:76 |
| POST | /internal/ops/api-keys | app/api/internal/ops/api_keys.py:113 |
| DELETE | /internal/ops/api-keys/{key_id} | app/api/internal/ops/api_keys.py:146 |

**Global auth/dependency**: `require_admin_token` (X-Admin-Token header). Failures:
- 503 + body `{"detail": "Admin API is not configured"}` when `settings.ADMIN_API_TOKEN` falsy.
- 401 + `WWW-Authenticate: ApiKey` + body `{"detail": "Admin token required"}` when header missing.
- 401 + `WWW-Authenticate: ApiKey` + body `{"detail": "Invalid admin token"}` when token mismatch.  
Source: `app/api/internal/deps/admin_auth.py:21-54`.

**Framework validation errors**: FastAPI 422 with standard shape `{"detail":[{"loc":[...],"msg":...,"type":...}]}` when query/path/body validation fails (for example, `hours>168`).

---

## GET /internal/ping
**Summary**: Connectivity check. Returns static payload.  
Auth: X-Admin-Token (global dependency). No role/perm checks. No caching.

**Request**  
- Headers: `X-Admin-Token` (string, required by dependency).  
- Path/query/body: none.

**Response (success)**  
- Status: 200 (default).  
- Model `AdminPingResponse` (`app/schemas/admin.py:6`). Fields (all strings, non-null): `status="ok"`, `admin_api="operational"`, `version="1.0.0"` set in handler (`app/api/internal/router.py:30-36`).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401 / 503 from `require_admin_token` (see global auth above).  
- 422 standard validation if header present but unparsable (framework-level).

**Notes**  
- Handler: `app/api/internal/router.py:30`.  
- Response model defined in `app/schemas/admin.py:6`.

---

## GET /internal/business/overview
**Summary**: Aggregated counts for users, vaults, and member authorizations. Live DB query per request.  
Auth: X-Admin-Token. Dependencies: `get_db` session. No caching or rate limits.

**Request**  
- Headers: `X-Admin-Token` required.  
- Query/path/body: none.

**Response (success)**  
- Status: 200.  
- Model `BusinessOverviewResponse` (`app/api/internal/business/overview.py:44`). Fields:
  - `generated_at` (datetime, tz-aware ISO 8601, set to `datetime.now(timezone.utc)`).
  - `users` (`UserOverview`, line 24): `total`, `new_today`, `new_this_week` (ints).
  - `vaults` (`VaultOverview`, line 31): `total` int, `with_pin` int, `by_status` dict[str,int] (keys = vault status strings from DB; values counts). **Statuses themselves are UNKNOWN (needs backend confirmation); inspect `vaults.status` values in DB.**
  - `members` (`MemberOverview`, line 38): `total_authorizations` int, `by_role` dict[str,int]; roles come from `vault_authorizations.role` values. Exact role set UNKNOWN (inspect DB or ORM constraints).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 from auth.  
- 422 only on auth header validation. DB errors not handled explicitly (would surface as 500).

**Notes**  
- Handler: `app/api/internal/business/overview.py:61`.  
- Metrics queries: `app/infrastructure/db/queries/business_metrics.py`.

---

## GET /internal/business/activity
**Summary**: Recent activity window with summary counts. Entries ordered newest first.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- Query:
  - `hours` int, default 24, constraints ge=1 le=168 (line 63).  
  - `limit` int, default 50, constraints ge=1 le=100 (line 64).  
- Path/body: none.

**Response (success)**  
- Status: 200.  
- Model `ActivityResponse` (`app/api/internal/business/activity.py:44`):
  - `generated_at` datetime (utc now).  
  - `period_hours` int (echoes `hours`).  
  - `summary` (`ActivitySummaryResponse`, line 34): ints `total_events`, `vault_unlocks`, `failed_unlocks`, `pin_operations`, `member_changes`, `state_changes`. Values derived from grouped counts in `get_activity_summary` (counts use action names `VAULT_UNLOCKED`, `VAULT_UNLOCK_FAILED`, `PIN_SET`, `MEMBER_ADDED`, `MEMBER_REMOVED`, `VAULT_STATE_CHANGED`, `UNLOCK_COMMAND_SENT`).
  - `entries` list of `ActivityEntry` (line 23): `id` str, `vault_id` str, `user_id` str|null, `action` str, `method` str, `metadata` dict|null, `created_at` datetime. Ordered by `created_at` DESC (source `get_recent_activity`).
  - Possible `action` or `method` values beyond those used in summary are data-driven and UNKNOWN; inspect `access_logs.action` and `access_logs.method` in DB for full set.

**Pagination / Filtering / Sorting**  
- Not paginated. `limit` caps number of rows (max 100). Sorted by `created_at desc`. Filtered to last `hours` hours.

**Errors**  
- 401/503 auth.  
- 422 for `hours`/`limit` violating bounds (standard FastAPI 422). Example: `{"detail":[{"loc":["query","hours"],"msg":"ensure this value is less than or equal to 168","type":"value_error.number.not_le_allowed","ctx":{"limit_value":168}}]}`.

**Notes**  
- Handler: `app/api/internal/business/activity.py:61`.  
- Models: lines 23/34/44.  
- Queries: `app/infrastructure/db/queries/activity_queries.py`.

---

## GET /internal/business/trends
**Summary**: Daily time-series for user signups and vault provisioning over a 7-90 day window. Zero-filled; summaries precomputed.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- Query: `days` int, default 30, ge=7, le=90 (line 73).  
- Body/path: none.

**Response (success)**  
- Status: 200.  
- Model `BusinessTrendsResponse` (`app/api/internal/business/trends.py:50`):
  - `generated_at` datetime (utc now).  
  - `period_days` int (echo request).  
  - `period_start` / `period_end` strings (YYYY-MM-DD) derived from first/last entry of user series (empty string if no data).  
  - `user_signups` and `vault_provisioning`: `TrendSeriesResponse` (line 40) with fields:
    - `daily` list of `DailyCountResponse` (line 34) ordered by date asc, zero-filled.
    - `total` int (sum), `average_per_day` float (rounded 1 decimal), `peak_date` str|null, `peak_count` int, `change_pct` float|null (first half vs second half comparison; null if insufficient prior data).
  - Date strings formatted `%Y-%m-%d`. Counts may be zero.

**Pagination / Filtering / Sorting**: none beyond `days` window; daily arrays always length = `days`, ordered ascending.

**Errors**  
- 401/503 auth.  
- 422 for `days` outside [7,90] with standard FastAPI error body.

**Notes**  
- Handler: `app/api/internal/business/trends.py:69`.  
- Series builder: `app/infrastructure/db/queries/business_trends.py`.

---

## GET /internal/security/alerts
**Summary**: Detects suspicious activity spikes (failed unlocks 1h, PIN lockouts 24h) and returns active alerts plus counts.  
Auth: X-Admin-Token. Dependency: `get_db`. No caching.

**Request**  
- Headers: `X-Admin-Token`.  
- No path/query/body.

**Response (success)**  
- Status: 200.  
- Model `SecurityAlertsResponse` (`app/api/internal/security/alerts.py:70`):
  - `generated_at` datetime (utc now).  
  - `status`: Literal `"ok"|"warning"|"critical"` computed by `_determine_status` (critical if any alert severity=`critical`, warning if any alerts else ok).  
  - `active_alerts`: list of `SecurityAlert` (line 53) with fields `type` str, `severity` Literal `"low"|"medium"|"high"|"critical"` (currently constructed severities: `critical`, `high`, `medium`), `message` str, `count` int, `threshold` int, `window` str ("1h" or "24h").  
  - `last_24h`: `SecuritySummaryResponse` (line 63) with `failed_unlocks_1h`, `failed_unlocks_24h`, `pin_lockouts_24h` ints.
  - Thresholds: warning >=5/hr, critical >=20/hr for failed unlocks; warning >=3/24h, critical >=10/24h for PIN lockouts (constants in `app/infrastructure/db/queries/security_metrics.py:35-38`).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- 422 only on auth header validation.

**Notes**  
- Handler: `app/api/internal/security/alerts.py:190`.  
- Alert builders: same file lines 87-157.  
- Metrics query: `app/infrastructure/db/queries/security_metrics.py`.

---

## GET /internal/ops/summary
**Summary**: Dashboard aggregate combining business metrics, security status, and 24h activity counts.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- No query/path/body.

**Response (success)**  
- Status: 200.  
- Model `OpsSummaryResponse` (`app/api/internal/ops/summary.py:76`):
  - `generated_at` datetime (utc now).  
  - `overall_status`: Literal `"ok"|"warning"|"critical"` derived by `_security_status` using same thresholds as security alerts.  
  - `business`: `OpsBusinessSummary` (line 52) with nested user/vault/member summaries (lines 35/41/47) mirroring counts from business metrics; `by_status` and `by_role` dictionaries as returned from DB (keys UNKNOWN; inspect DB for possible values).  
  - `security`: `OpsSecuritySummary` (line 58) includes counts plus `alert_count` (number of breached warning thresholds via `_alert_count`).  
  - `activity`: `OpsActivitySummary` (line 66) reflects 24h activity summary from `get_activity_summary`.

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- 422 on auth header validation only.

**Notes**  
- Handler: `app/api/internal/ops/summary.py:130`.  
- Models defined same file lines 35-76.  
- Uses queries from business_metrics, security_metrics, activity_queries.

---

## GET /internal/ops/diagnostics/redis
**Summary**: Redis health snapshot (async).  
Auth: X-Admin-Token. No caching.

**Request**  
- Headers: `X-Admin-Token`.  
- No query/path/body.

**Response (success)**  
- Status: 200.  
- Model `RedisDiagnosticsResponse` (`app/api/internal/ops/diagnostics.py:32`):
  - `status` str ("healthy" or "unhealthy" from `get_redis_health`).  
  - `connected` bool.  
  - `memory_used_mb` float (rounded to 2).  
  - `total_keys` int.  
  - `uptime_seconds` int.  
  - `checked_at` datetime (utc now).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- Redis exceptions are caught inside `get_redis_health`, returning `status="unhealthy"` with zeros instead of raising.

**Notes**  
- Handler: `app/api/internal/ops/diagnostics.py:67`.  
- Metrics source: `app/infrastructure/db/queries/system_metrics.py`.

---

## GET /internal/ops/diagnostics/websockets
**Summary**: Current websocket connection stats from in-process manager.  
Auth: X-Admin-Token.

**Request**  
- Headers: `X-Admin-Token`. No other inputs.

**Response (success)**  
- Status: 200.  
- Model `WebSocketDiagnosticsResponse` (`app/api/internal/ops/diagnostics.py:41`):
  - `total_users`, `total_user_connections`, `total_vaults`, `subscriptions` (ints from `get_connection_stats`, default 0 when missing).  
  - `online_vaults` list[str] from `manager.get_online_vaults()`.  
  - `checked_at` datetime (utc now).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- No explicit error handling; unexpected exceptions propagate as 500.

**Notes**  
- Handler: `app/api/internal/ops/diagnostics.py:84`.  
- Stats source: `app/infrastructure/messaging/websocket_manager.py`.

---

## GET /internal/ops/diagnostics/database
**Summary**: SQLAlchemy pool stats.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`. No query/path/body.

**Response (success)**  
- Status: 200.  
- Model `DatabaseDiagnosticsResponse` (`app/api/internal/ops/diagnostics.py:50`):
  - `status` str ("healthy" or "unknown" on exception).  
  - `pool_size`, `checked_out`, `overflow` ints from SQLAlchemy pool.  
  - `checked_at` datetime (utc now).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- Pool inspection exceptions caught in `get_database_pool_metrics` return `status="unknown"` with zeros.

**Notes**  
- Handler: `app/api/internal/ops/diagnostics.py:102`.  
- Metrics: `app/infrastructure/db/queries/system_metrics.py`.

---

## GET /internal/ops/rate-limits
**Summary**: Lists active rate-limit keys from Redis; top violators and category counts.  
Auth: X-Admin-Token.

**Request**  
- Headers: `X-Admin-Token`.  
- No query/path/body.

**Response (success)**  
- Status: 200.  
- Model `RateLimitsResponse` (`app/api/internal/ops/rate_limits.py:33`):
  - `total_active_keys` int (all scanned `rate_limit:*` keys).  
  - `top_violators` list of `ViolatorResponse` (line 27): `key` str (prefix removed), `current_count` int, `ttl_seconds` int. Sorted desc by `current_count`, limited to top 10. Keys with TTL <=0 or missing count are excluded.  
  - `by_category` dict[str,int] counting keys by first segment after prefix.  
  - `checked_at` datetime (utc now).

**Pagination / Filtering / Sorting**: none (top_violators already limited to 10 and sorted).

**Errors**  
- 401/503 auth.  
- Redis errors not caught here, so 500 possible.

**Notes**  
- Handler: `app/api/internal/ops/rate_limits.py:49`.  
- Metrics query: `app/infrastructure/db/queries/rate_limit_metrics.py`.

---

## GET /internal/ops/sessions/stats
**Summary**: Refresh-token counts and top users (sync Redis scan).  
Auth: X-Admin-Token.

**Request**  
- Headers: `X-Admin-Token`. No query/path/body.

**Response (success)**  
- Status: 200.  
- Model `SessionStatsResponse` (`app/api/internal/ops/sessions.py:36`):
  - `total_active_tokens` int (all `refresh:*` keys).  
  - `top_users` list of `TopUserResponse` (line 31): `user_id` str, `token_count` int, sorted desc, limited to 10.  
  - `checked_at` datetime (utc now).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- Redis exceptions not caught, so 500 possible.

**Notes**  
- Handler: `app/api/internal/ops/sessions.py:56`.  
- Metrics source: `app/infrastructure/services/session_metrics.py`.

---

## DELETE /internal/ops/sessions/{user_id}
**Summary**: Deletes all refresh tokens for the given user ID.  
Auth: X-Admin-Token.

**Request**  
- Headers: `X-Admin-Token`.  
- Path param: `user_id` str (no regex or length validation).  
- Body/query: none.

**Response (success)**  
- Status: 200 (default).  
- Model `RevokeSessionsResponse` (`app/api/internal/ops/sessions.py:42`): `user_id` str (echo) and `sessions_revoked` int (count deleted; may be 0 if none).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- No 404 on missing user; returns `sessions_revoked=0`.  
- Validation 422 only if `user_id` missing from path.

**Notes**  
- Handler: `app/api/internal/ops/sessions.py:86`.  
- Revocation logic: `app/infrastructure/services/session_metrics.py:90` (scans Redis and deletes matching keys).

---

## GET /internal/ops/notifications/email
**Summary**: Email service health plus today's send/fail counters from Redis.  
Auth: X-Admin-Token.

**Request**  
- Headers: `X-Admin-Token`. No query/path/body.

**Response (success)**  
- Status: 200.  
- Model `EmailStatusResponse` (`app/api/internal/ops/notifications.py:22`):
  - `service` str (currently always `"smtp"` from metrics).  
  - `status` str (currently `"healthy"` in metrics; no enum enforced).  
  - `sent_today` int, `failed_today` int.  
  - `note` str (static guidance about wiring counters).  
  - `checked_at` datetime (utc now).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- Redis errors not caught, so 500 possible.

**Notes**  
- Handler: `app/api/internal/ops/notifications.py:36`.  
- Metrics: `app/infrastructure/notifications/email_metrics.py`.

---

## GET /internal/ops/audit
**Summary**: Paginated admin audit logs (written elsewhere via `create_audit_log`). Ordered newest first.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- Query params:
  - `page` int, default 1, ge=1.  
  - `limit` int, default 50, ge=1, le=100 (capped to 100 in query).  
  - `action` str | null, optional exact-match filter.  
- Path/body: none.

**Response (success)**  
- Status: 200.  
- Model `AuditLogsResponse` (`app/api/internal/ops/audit.py:40`):
  - `items` list of `AuditLogItem` (line 30): `id` int, `action` str, `target_type` str, `target_id` str|null, `details` dict[str,Any]|null, `ip_address` str|null, `created_at` datetime.  
  - `total` int (count after filter), `page` int (echo), `pages` int (0 when total=0; else ceil(total/limit)).  
  - Items ordered by `created_at desc` (see `get_audit_logs`).

**Pagination / Filtering / Sorting**  
- Style: page + limit. Default limit 50; max 100. Sort fixed `created_at desc`. Filter: optional `action` exact match.

**Errors**  
- 401/503 auth.  
- 422 for invalid `page`/`limit`.  
- DB errors propagate as 500.

**Notes**  
- Handler: `app/api/internal/ops/audit.py:56`.  
- Query: `app/infrastructure/db/queries/audit_queries.py`.

---

## GET /internal/ops/api-keys
**Summary**: List API keys (optionally active-only). Ordered newest first.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- Query: `active_only` bool, default True (implicit query param from function signature, no validation).  
- Path/body: none.

**Response (success)**  
- Status: 200.  
- Model `APIKeysListResponse` (`app/api/internal/ops/api_keys.py:51`):
  - `items` list of `APIKeyItem` (line 41): `id` int, `name` str, `created_by` str, `last_used_at` datetime|null, `expires_at` datetime|null, `is_active` bool, `created_at` datetime.
  - Items sorted by `created_at desc`. Only `is_active=True` returned when `active_only` true.

**Pagination / Filtering / Sorting**  
- No pagination. Filter: `active_only` flag. Sort fixed `created_at desc`.

**Errors**  
- 401/503 auth.  
- 422 only on auth header.

**Notes**  
- Handler: `app/api/internal/ops/api_keys.py:76`.  
- Query: `app/infrastructure/db/queries/api_key_queries.py:list_api_keys`.  
- Name uniqueness: **no validation; duplicates allowed** (DB column length 100 only).  
- `expires_at` may be null; `last_used_at` may be null until first use.

---

## POST /internal/ops/api-keys
**Summary**: Create new API key; returns plain key once.  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- Body (JSON), model `CreateAPIKeyRequest` (`app/api/internal/ops/api_keys.py:55`):
  - `name`: str (required; no length/charset validation beyond DB column 100 chars).  
  - `expires_in_days`: int|null (optional; no bounds, negative or zero allowed, will produce past or immediate expiry). If constraints are required, backend change needed.

**Response (success)**  
- Status: 201 Created (explicit).  
- Model `CreatedAPIKeyResponse` (`app/api/internal/ops/api_keys.py:60`):
  - `id` int (DB PK).  
  - `key` str - plain API key generated by `generate_api_key` (`app/infrastructure/security/api_key_hasher.py:18`), format `sk_<token_urlsafe(32)>`. Returned **once only**; not stored in DB (only hash stored).  
  - `name` str.  
  - `expires_at` datetime|null (utc now + `expires_in_days` if provided, else null).

**Pagination / Filtering / Sorting**: none.

**Errors**  
- 401/503 auth.  
- 422 for missing/invalid body fields (FastAPI validation).  
- DB errors (for example, unique constraint on `key_hash` is theoretically possible) surface as 500; no custom handling.

**Notes**  
- Handler: `app/api/internal/ops/api_keys.py:113`.  
- DB model: `app/infrastructure/db/models/api_key_orm.py` (name max 100 chars; key_hash unique; is_active default true).  
- Audit logging is not triggered here (no hook in this handler).

---

## DELETE /internal/ops/api-keys/{key_id}
**Summary**: Soft-revoke API key (sets `is_active=False`).  
Auth: X-Admin-Token. Dependency: `get_db`.

**Request**  
- Headers: `X-Admin-Token`.  
- Path param `key_id` int (no additional validation).  
- Body/query: none.

**Response (success)**  
- Status: 204 No Content (explicit). Body: empty.

**Errors**  
- 401/503 auth.  
- 404 with body `{"detail": "API key {key_id} not found."}` when ID missing (raised in handler).  
- 422 for invalid path type.

**Notes**  
- Handler: `app/api/internal/ops/api_keys.py:146`.  
- Revocation logic: `app/infrastructure/db/queries/api_key_queries.py:84` (sets `is_active=False`, keeps row).  
- No audit log emission here.

---

## Pagination / Sorting quick reference
- Page+limit: only `/internal/ops/audit` (page>=1, limit<=100, ordered created_at desc).
- Offset-less capped lists: `/internal/business/activity` uses `limit` (<=100) and `created_at desc`. `/internal/ops/api-keys` sorted created_at desc. `/internal/ops/rate-limits` top_violators sorted by count desc, max 10.
- Fixed windows: `/internal/business/trends` length=`days`, ordered asc dates; `/internal/business/activity` filtered to last `hours` hours.

## Common headers
- All endpoints rely on `X-Admin-Token` checked by `require_admin_token` (see top). No other custom headers required.

## Example payloads
Schema-derived examples (placeholder values consistent with code) are stored in `Docs/internal-api-examples/`:
- Success responses: see corresponding `get_*.json` / `post_*.json` / `delete_*.json` files.
- `delete_internal_ops_api-keys_keyid.txt` documents the 204 empty body.

## Unknowns / follow-ups
- Vault status values (`vaults.by_status`) and member roles (`members.by_role`) are data-driven; inspect DB enumerations (`vaults.status`, `vault_authorizations.role`) to enumerate for UI dropdowns.  
- Access log `action` and `method` value set beyond those counted in summaries is UNKNOWN; inspect `access_logs` data or producing services for full list.  
- API key name constraints beyond DB length (100) are not enforced; define allowed charset/uniqueness if UI needs validation.  
- `expires_in_days` accepts negative/zero; clarify desired constraints to avoid immediate-expiry keys.  
- No audit logging wired in API key create/revoke endpoints; if UI depends on audit trail, backend change may be required.
