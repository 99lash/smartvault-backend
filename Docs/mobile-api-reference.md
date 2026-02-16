# SmartVault Mobile & Public API — Frontend Reference

## Authentication

All endpoints except health checks and auth flows require a JWT Bearer token.

```
Authorization: Bearer <access_token>
```

Tokens are obtained from the login or token refresh endpoints.

### Token Lifecycle

| Token | Lifetime | Storage recommendation |
|-------|----------|----------------------|
| `access_token` | `expires_in` seconds (default 1800 = 30 min) | Memory only (never localStorage) |
| `refresh_token` | Long-lived | httpOnly cookie or secure storage |

---

## Base URL

All endpoints are prefixed with:

```
/api/v1
```

Full example: `http://localhost:8000/api/v1/auth/login`

---

## Rate Limiting

Some endpoints are rate limited. When a limit is exceeded the server returns `429 Too Many Requests`. The client should back off and retry after a delay.

| Endpoint | Limit |
|----------|-------|
| `POST /auth/request-otp` | 3 requests per minute per IP |
| `POST /auth/login` | 5 requests per minute per IP |
| `POST /vaults/{id}/pin` | 10 requests per minute per user per vault |
| `DELETE /vaults/{id}/pin` | 10 requests per minute per user per vault |
| `POST /vaults/{id}/unlock/pin` | 15 requests per minute per user per vault |

---

## Endpoints

---

### Health

---

#### GET /health

Basic liveness check. No authentication required.

**Response (200):**

```json
{ "status": "ok" }
```

---

#### GET /health/detailed

Checks PostgreSQL and Redis connectivity. No authentication required.

**Response (200):**

```json
{
  "status": "healthy",
  "dependencies": [
    {
      "name": "postgresql",
      "status": "ok",
      "latency_ms": 1.23,
      "error": null
    },
    {
      "name": "redis",
      "status": "ok",
      "latency_ms": 0.45,
      "error": null
    }
  ]
}
```

**Notes:**
- `status` is one of: `"healthy"`, `"degraded"`, `"unhealthy"`
- Each dependency `status` is one of: `"ok"`, `"degraded"`, `"down"`
- `error` is `null` when healthy, a short string when not
- Always returns HTTP `200` — check the `status` field to determine health

---

### Authentication

All auth endpoints are unauthenticated (no Bearer token required).

---

#### POST /auth/request-otp

Sends a one-time password to the user's email. Used as the first step of signup.

**Request body:**

```json
{ "email": "user@example.com" }
```

**Response: `204 No Content`** (empty body)

**Notes:**
- Always returns 204 even if the email does not exist — intentional to prevent user enumeration
- Rate limited to 3 requests per minute per IP

---

#### POST /auth/verify-otp

Verifies the OTP and returns a short-lived signup ticket.

**Request body:**

```json
{
  "email": "user@example.com",
  "otp": "482910"
}
```

| Field | Constraints |
|-------|-------------|
| `otp` | Exactly 6 characters |

**Response (200):**

```json
{ "signup_ticket": "abc123...long-token..." }
```

**Error (422):** OTP is invalid or expired

---

#### POST /auth/signup

Creates a new user account. Requires a valid signup ticket from `verify-otp`.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "Jane Smith",
  "signup_ticket": "abc123...long-token..."
}
```

| Field | Constraints |
|-------|-------------|
| `password` | Min 12, max 128 characters |
| `full_name` | Optional, max 200 characters |
| `signup_ticket` | Min 20 characters, from `verify-otp` |

**Response (201):**

```json
{
  "id": "user-abc-123",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "created_at": "2025-01-16T10:30:00Z"
}
```

**Error (409):** Email already registered
**Error (422):** Signup ticket invalid or expired

---

#### POST /auth/login

Authenticates a user and returns access and refresh tokens.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Notes:**
- `expires_in` is in seconds
- Store the `access_token` in memory and `refresh_token` securely
- Rate limited to 5 requests per minute per IP

**Error (401):** Incorrect email or password

---

#### POST /auth/refresh

Rotates the refresh token and returns a new access/refresh token pair.

**Request body:**

```json
{ "refresh_token": "eyJ..." }
```

**Response (200):** Same shape as login response

**Notes:**
- **Token rotation** — the old `refresh_token` is invalidated on use. Store the new one immediately.
- If a refresh token is reused (replay attack), it returns `401` and all sessions for that user may be revoked

**Error (401):** Token invalid, expired, or already used

---

#### POST /auth/logout

Revokes the refresh token. The user is logged out on this device.

**Request body:**

```json
{ "refresh_token": "eyJ..." }
```

**Response: `204 No Content`** (empty body)

**Notes:**
- Always returns 204 even if the token is already invalid
- The access token is not invalidated (it expires naturally). Discard it client-side immediately.

---

#### POST /auth/request-password-reset

Sends a password reset email. No authentication required.

**Request body:**

```json
{ "email": "user@example.com" }
```

**Response: `204 No Content`**

**Notes:**
- Always returns 204 even if the email does not exist — prevents user enumeration

---

#### POST /auth/confirm-password-reset

Resets the password using the token from the reset email.

**Request body:**

```json
{
  "token": "reset-token-from-email...",
  "new_password": "newsecurepassword123"
}
```

| Field | Constraints |
|-------|-------------|
| `token` | Min 20 characters |
| `new_password` | Min 12, max 128 characters |

**Response: `204 No Content`**

**Error (422):** Token invalid, expired, or password too short

---

### Users

All user endpoints require Bearer token authentication.

---

#### GET /users/me

Returns the current authenticated user's profile.

**Response (200):**

```json
{
  "id": "user-abc-123",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "created_at": "2025-01-16T10:30:00Z"
}
```

**Notes:**
- `full_name` may be `null` if not set

**Error (404):** User not found (should not happen for a valid token)

---

#### PATCH /users/me

Updates the current user's profile.

**Request body:**

```json
{ "full_name": "Jane Doe" }
```

| Field | Constraints |
|-------|-------------|
| `full_name` | Optional, max 200 characters. Send `null` to clear. |

**Response (200):** Same shape as `GET /users/me`

---

### Vaults

All vault endpoints require Bearer token authentication.

---

#### POST /vaults/provision

Registers a new physical vault device with the system.

**Request body:**

```json
{
  "hardware_uuid": "ESP32-DEADBEEF-0001",
  "vault_name": "Front Door"
}
```

| Field | Constraints |
|-------|-------------|
| `hardware_uuid` | Required, must be unique across all vaults |
| `vault_name` | Optional display name |

**Response (201):**

```json
{
  "vault_id": "vault-abc-123",
  "hardware_uuid": "ESP32-DEADBEEF-0001",
  "vault_name": "Front Door",
  "status": "LOCKED"
}
```

**Notes:**
- `status` is always `"LOCKED"` on initial provisioning
- The authenticated user becomes the vault owner

**Error (409):** `hardware_uuid` already provisioned

---

#### GET /vaults/{vault_id}/status

Returns the current status of a vault.

**Path parameter:** `vault_id`

**Response (200):**

```json
{
  "vault_id": "vault-abc-123",
  "status": "LOCKED",
  "last_seen_at": "2025-01-16T10:28:00Z"
}
```

**Notes:**
- `status` is one of: `"LOCKED"`, `"UNLOCKED"`, `"OFFLINE"`
- `last_seen_at` is `null` if the device has never connected

**Error (403):** No access to this vault
**Error (404):** Vault not found

---

#### POST /vaults/{vault_id}/unlock

Sends an unlock command to a vault device via WebSocket.

**Path parameter:** `vault_id`

**No request body.**

**Response (202):**

```json
{
  "command_id": "cmd-abc-123",
  "vault_id": "vault-abc-123",
  "expires_at": "2025-01-16T10:31:00Z",
  "sent": true
}
```

**Notes:**
- `202 Accepted` means the command was sent — not that the vault actually unlocked
- `sent: true` means the vault device received the command via WebSocket
- `sent: false` means the command was created but the device was not connected at the time
- `expires_at` is typically 60 seconds from creation
- Requires ADMIN or MEMBER role (VIEWER cannot unlock)

**Error (403):** No access or insufficient role
**Error (404):** Vault not found
**Error (503):** Vault is offline

---

#### POST /vaults/{vault_id}/pin

Sets or updates the PIN for a vault.

**Path parameter:** `vault_id`

**Request body:**

```json
{ "pin": "482910" }
```

| Field | Constraints |
|-------|-------------|
| `pin` | Exactly 6 characters, numeric |

**Response (201):**

```json
{
  "vault_id": "vault-abc-123",
  "pin_set_at": "2025-01-16T10:30:00Z"
}
```

**Notes:**
- Replaces any existing PIN — calling this again updates the PIN
- Requires ADMIN or MEMBER role

**Error (403):** No access or insufficient role
**Error (404):** Vault not found
**Error (422):** PIN format invalid

---

#### DELETE /vaults/{vault_id}/pin

Removes the PIN from a vault.

**Path parameter:** `vault_id`

**Response (200):**

```json
{
  "vault_id": "vault-abc-123",
  "removed": true
}
```

**Error (403):** No access or insufficient role
**Error (404):** Vault not found
**Error (409):** No PIN is currently set

---

#### GET /vaults/{vault_id}/pin/status

Checks whether a PIN is currently set on a vault.

**Path parameter:** `vault_id`

**Response (200):**

```json
{
  "vault_id": "vault-abc-123",
  "is_set": true,
  "pin_set_at": "2025-01-10T08:00:00Z"
}
```

**Notes:**
- `pin_set_at` is `null` when `is_set` is `false`

**Error (403):** No access to this vault

---

#### POST /vaults/{vault_id}/unlock/pin

Unlocks a vault using the PIN.

**Path parameter:** `vault_id`

**Request body:**

```json
{ "pin": "482910" }
```

**Response (200):**

```json
{
  "vault_id": "vault-abc-123",
  "result": "SUCCESS",
  "attempts_remaining": null
}
```

**Notes:**
- `result` is one of: `"SUCCESS"`, `"INVALID"`, `"LOCKED_OUT"`
- `attempts_remaining` is `null` on success, an integer on `"INVALID"` showing how many tries are left before lockout
- `attempts_remaining` is `0` when `result` is `"LOCKED_OUT"`
- Rate limited to 15 requests per minute per user per vault

**Error (401):** PIN is incorrect (also reflected in `result: "INVALID"`)
**Error (403):** No access or insufficient role
**Error (404):** Vault not found
**Error (409):** No PIN is set on this vault
**Error (423):** Vault is locked out due to too many failed attempts

---

### Vault Members

All member endpoints require Bearer token authentication.

---

#### GET /vaults/{vault_id}/members

Lists all members of a vault.

**Path parameter:** `vault_id`

**Response (200):**

```json
{
  "vault_id": "vault-abc-123",
  "members": [
    {
      "user_id": "user-abc-123",
      "email": "jane@example.com",
      "full_name": "Jane Smith",
      "role": "ADMIN",
      "granted_at": "2025-01-10T08:00:00Z",
      "granted_by": "user-owner-456"
    }
  ]
}
```

**Notes:**
- `full_name` may be `null`
- `granted_by` may be `null` for the original owner
- `role` is one of: `"ADMIN"`, `"MEMBER"`, `"VIEWER"`
- The vault owner is not listed here — ownership is implicit

**Error (403):** No access to this vault
**Error (404):** Vault or user not found

---

#### POST /vaults/{vault_id}/members

Adds a member to a vault or updates their role if already a member.

**Path parameter:** `vault_id`

**Request body:**

```json
{
  "user_id": "user-xyz-789",
  "role": "MEMBER"
}
```

| Field | Constraints |
|-------|-------------|
| `user_id` | ID of an existing user |
| `role` | One of: `"ADMIN"`, `"MEMBER"`, `"VIEWER"` |

**Response (201):** A single `MemberResponse` object (same shape as one item from the list)

**Notes:**
- Idempotent — if the user is already a member, their role is updated
- Cannot add the vault owner as a member (they are already the owner)
- Only the vault owner can add members

**Error (403):** Caller is not the vault owner
**Error (404):** Vault or target user not found
**Error (422):** Attempting to add the vault owner as a member

---

#### DELETE /vaults/{vault_id}/members/{user_id}

Removes a member from a vault.

**Path parameters:** `vault_id`, `user_id`

**Response: `204 No Content`**

**Notes:**
- Idempotent — no error if the user is not a member
- Only the vault owner can remove members
- Cannot remove the vault owner

**Error (403):** Caller is not the vault owner
**Error (404):** Vault not found
**Error (422):** Attempting to remove the vault owner

---

### Activity

Requires Bearer token authentication.

---

#### GET /vaults/{vault_id}/activity

Returns the activity log for a specific vault.

**Path parameter:** `vault_id`

**Query parameters:**

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `limit` | integer | `50` | `1` | `100` | Max entries to return |

**Response (200):**

```json
{
  "vault_id": "vault-abc-123",
  "entries": [
    {
      "id": "log-abc-123",
      "vault_id": "vault-abc-123",
      "user_id": "user-abc-123",
      "action": "VAULT_UNLOCKED",
      "method": "PIN",
      "metadata": { "attempt": 1 },
      "created_at": "2025-01-16T10:28:00Z"
    }
  ],
  "count": 1
}
```

**Notes:**
- `user_id` may be `null` for system-initiated events
- `metadata` may be `null`
- Entries are ordered newest first
- Known `action` values: `VAULT_UNLOCKED`, `VAULT_UNLOCK_FAILED`, `PIN_SET`, `MEMBER_ADDED`, `MEMBER_REMOVED`, `VAULT_STATE_CHANGED`, `UNLOCK_COMMAND_SENT`

**Error (403):** No access to this vault

---

### WebSocket

---

#### WS /api/v1/ws/user

Real-time connection for user clients. Receives vault status changes and notifications.

**Connection URL:**

```
ws://localhost:8000/api/v1/ws/user?token=<access_token>
```

**Query parameter:** `token` — JWT access token (optional during development)

---

**On connect, the server sends:**

```json
{
  "type": "NOTIFICATION",
  "payload": {
    "title": "Connected",
    "message": "WebSocket connection established",
    "severity": "success"
  }
}
```

---

**Client → Server messages:**

Subscribe to vault updates:

```json
{
  "type": "SUBSCRIBE",
  "payload": {
    "vault_ids": ["vault-abc-123", "vault-def-456"]
  }
}
```

Unsubscribe from vault updates:

```json
{
  "type": "UNSUBSCRIBE",
  "payload": {
    "vault_ids": ["vault-abc-123"]
  }
}
```

---

**Server → Client messages:**

Vault status changed (broadcast after state update):

```json
{
  "type": "VAULT_STATUS_CHANGED",
  "payload": {
    "vault_id": "vault-abc-123",
    "status": "UNLOCKED",
    "changed_at": "2025-01-16T10:30:00Z",
    "changed_by": "user-abc-123"
  }
}
```

Notification:

```json
{
  "type": "NOTIFICATION",
  "payload": {
    "title": "Subscribed",
    "message": "Subscribed to 2 vaults",
    "severity": "info"
  }
}
```

`severity` values: `"info"`, `"warning"`, `"error"`, `"success"`

Error:

```json
{
  "type": "ERROR",
  "payload": {
    "error_code": "UNKNOWN_MESSAGE_TYPE",
    "message": "Unknown message type: PING"
  }
}
```

---

**Notes:**
- The vault device WebSocket (`/ws/vault`) is not yet implemented — do not use
- All messages are JSON strings
- The connection closes if the server receives invalid JSON

---

## Common Error Responses

| Status | When |
|--------|------|
| `401 Unauthorized` | Missing, invalid, or expired access token |
| `403 Forbidden` | Token valid but no permission for this resource |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | State conflict (duplicate email, PIN not set, etc.) |
| `422 Unprocessable Entity` | Validation error or business rule violation |
| `423 Locked` | Vault is locked out due to too many PIN attempts |
| `429 Too Many Requests` | Rate limit exceeded |
| `503 Service Unavailable` | Vault is offline |

All error responses have this shape:

```json
{ "detail": "Human-readable error message" }
```

---

## Authentication Flow Summary

### New user signup

```
POST /auth/request-otp   → 204
POST /auth/verify-otp    → { signup_ticket }
POST /auth/signup        → { id, email, ... }
POST /auth/login         → { access_token, refresh_token, expires_in }
```

### Returning user login

```
POST /auth/login         → { access_token, refresh_token, expires_in }
```

### Token refresh (before access token expires)

```
POST /auth/refresh       → { access_token, refresh_token, expires_in }
```

### Logout

```
POST /auth/logout        → 204
```

### Password reset

```
POST /auth/request-password-reset  → 204
(user clicks link in email)
POST /auth/confirm-password-reset  → 204
POST /auth/login                   → { access_token, refresh_token, expires_in }
```