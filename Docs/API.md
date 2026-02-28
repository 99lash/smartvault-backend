# API Reference

This document provides a comprehensive reference for the SmartVault API, including authentication, endpoints, request/response formats, and conventions.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Base URLs](#base-urls)
3. [Common Headers](#common-headers)
4. [Error Handling](#error-handling)
5. [Endpoints](#endpoints)
   - [Health](#health)
   - [Authentication](#authentication)
   - [Users](#users)
   - [Vaults](#vaults)
   - [Vault Members](#vault-members)
   - [Activity](#activity)
6. [WebSocket API](#websocket-api)
7. [Rate Limiting](#rate-limiting)
8. [Token Reference](#token-reference)
9. [Authentication Flow Summary](#authentication-flow-summary)
10. [Internal API](#internal-api)

---

## API Overview

SmartVault provides a **RESTful JSON API** with the following characteristics:

- **Protocol:** HTTPS only (HTTP redirects to HTTPS in production)
- **Format:** JSON for all requests and responses
- **Authentication:** JWT Bearer tokens
- **Versioning:** URL-based (`/api/v1/...`)
- **Rate Limiting:** Redis-based, enforced per IP or per user per vault
- **CORS:** Configured per environment

**Design Principles:**
- RESTful resource naming
- Consistent error responses
- Idempotent operations where noted
- Clear HTTP status codes

---

## Base URLs

| Environment | Base URL |
|-------------|----------|
| **Development** | `http://localhost:8000/api/v1` |
| **Swagger UI** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |

---

## Common Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes* | Bearer token for authentication (`Bearer <token>`) |
| `Content-Type` | Yes** | Must be `application/json` for POST/PATCH requests with a body |

\* Required for all authenticated endpoints  
\** Required for requests that include a body

### Response Headers

| Header | Present | Description |
|--------|---------|-------------|
| `Content-Type` | Always | `application/json` |
| `X-RateLimit-Limit` | Rate-limited endpoints | Maximum requests allowed in the window |
| `X-RateLimit-Remaining` | Rate-limited endpoints | Remaining requests in the current window |
| `X-RateLimit-Reset` | Rate-limited endpoints | Unix timestamp when the limit resets |

---

## Error Handling

### Error Response Format

All error responses use a consistent shape:

```json
{
  "detail": "Human-readable message describing the error"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| `200` | OK | Successful GET / PATCH / DELETE with body |
| `201` | Created | Resource successfully created |
| `202` | Accepted | Command accepted for async processing |
| `204` | No Content | Successful operation with no response body |
| `401` | Unauthorized | Missing, invalid, or expired token; invalid credentials |
| `403` | Forbidden | Authenticated but not authorized for this resource |
| `404` | Not Found | Resource does not exist or caller has no access |
| `409` | Conflict | Duplicate resource or conflicting state |
| `422` | Unprocessable Entity | Semantic validation error (invalid ticket, bad field value) |
| `423` | Locked | Resource is locked (e.g., vault PIN lockout) |
| `429` | Too Many Requests | Rate limit exceeded |
| `503` | Service Unavailable | Dependency unavailable (e.g., device not connected) |

---

## Endpoints

---

### Health

#### Get Liveness Status

**`GET /api/v1/health`**  
**Authentication:** None  
**Description:** Lightweight liveness check. Use for load balancer health probes.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

#### Get Detailed Health Status

**`GET /api/v1/health/detailed`**  
**Authentication:** None  
**Description:** Readiness check with per-dependency status. Always returns HTTP 200 regardless of internal health.

**Response (200 OK — healthy):**
```json
{
  "status": "healthy",
  "dependencies": [
    {
      "name": "database",
      "status": "healthy",
      "latency_ms": 11.4,
      "error": null
    },
    {
      "name": "redis",
      "status": "healthy",
      "latency_ms": 1.8,
      "error": null
    }
  ]
}
```

**Response (200 OK — degraded):**
```json
{
  "status": "degraded",
  "dependencies": [
    {
      "name": "database",
      "status": "healthy",
      "latency_ms": 11.4,
      "error": null
    },
    {
      "name": "redis",
      "status": "unhealthy",
      "latency_ms": null,
      "error": "Connection refused"
    }
  ]
}
```

**`status` values:** `healthy` | `degraded` | `unhealthy`

> **Note:** This endpoint always returns HTTP 200. Inspect the `status` field to determine readiness.

---

### Authentication

All auth endpoints are under `/api/v1/auth`. No JWT is required unless stated.

---

#### Request OTP

**`POST /api/v1/auth/request-otp`**  
**Authentication:** None  
**Rate limit:** 3 requests / 1 min / IP

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |

```json
{
  "email": "user@example.com"
}
```

**Response (204 No Content):** No body. OTP is sent to the provided email address regardless of whether the address is already registered.

---

#### Verify OTP

**`POST /api/v1/auth/verify-otp`**  
**Authentication:** None

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `otp` | string | Yes | OTP received by email |

```json
{
  "email": "user@example.com",
  "otp": "847291"
}
```

**Response (200 OK):**
```json
{
  "signup_ticket": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
}
```

**Errors:**
- `422` — OTP is invalid or expired

---

#### Sign Up

**`POST /api/v1/auth/signup`**  
**Authentication:** None

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Min 12 chars, max 128 chars |
| `full_name` | string | No | Max 200 chars |
| `signup_ticket` | string | Yes | Min 20 chars; obtained from `verify-otp` |

```json
{
  "email": "user@example.com",
  "password": "correct-horse-battery-staple",
  "full_name": "Jane Smith",
  "signup_ticket": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "created_at": "2026-02-12T10:30:00Z"
}
```

**Errors:**
- `409` — Email is already registered
- `422` — `signup_ticket` is invalid or expired

---

#### Login

**`POST /api/v1/auth/login`**  
**Authentication:** None  
**Rate limit:** 5 requests / 1 min / IP

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Registered email address |
| `password` | string | Yes | Account password |

```json
{
  "email": "user@example.com",
  "password": "correct-horse-battery-staple"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` — Invalid email or password

---

#### Refresh Token

**`POST /api/v1/auth/refresh`**  
**Authentication:** None (uses refresh token in body)

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | Valid, unused refresh token |

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

> **Note:** Refresh token rotation is enforced. The submitted token is immediately invalidated and a new pair is returned. Reusing an old refresh token returns `401`.

**Errors:**
- `401` — Refresh token is invalid, expired, or has already been used

---

#### Logout

**`POST /api/v1/auth/logout`**  
**Authentication:** None (uses refresh token in body)

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | The refresh token to revoke |

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (204 No Content):** No body. The refresh token is revoked. The access token remains valid until it naturally expires.

---

#### Request Password Reset

**`POST /api/v1/auth/request-password-reset`**  
**Authentication:** None

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Email address to send the reset link to |

```json
{
  "email": "user@example.com"
}
```

**Response (204 No Content):** No body. A reset email is sent if the address is registered. The response is always 204 to prevent email enumeration.

---

#### Confirm Password Reset

**`POST /api/v1/auth/confirm-password-reset`**  
**Authentication:** None

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `token` | string | Yes | Reset token from the email link |
| `new_password` | string | Yes | Min 12 chars, max 128 chars |

```json
{
  "token": "reset-token-from-email",
  "new_password": "new-correct-horse-battery-staple"
}
```

**Response (204 No Content):** No body. Password has been updated.

**Errors:**
- `422` — Reset token is invalid or expired

---

### Users

All user endpoints require a valid JWT Bearer token.

---

#### Get Current User

**`GET /api/v1/users/me`**  
**Authentication:** Required

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "created_at": "2026-01-15T08:20:00Z"
}
```

> **Note:** `full_name` may be `null` if the user did not provide one at signup.

---

#### Update Current User

**`PATCH /api/v1/users/me`**  
**Authentication:** Required

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `full_name` | string \| null | No | Max 200 chars; pass `null` to clear |

```json
{
  "full_name": "Jane A. Smith"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane A. Smith",
  "created_at": "2026-01-15T08:20:00Z"
}
```

---

#### Search User by Email

**`GET /api/v1/users/search?email=<email>`**  
**Authentication:** Required

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string | Yes | Exact email address to look up |

**Response (200 OK):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "other@example.com",
  "full_name": "John Doe"
}
```

**Errors:**
- `404` — No user found with that email address

---

### Vaults

All vault endpoints require a valid JWT Bearer token.

---

#### List Vaults

**`GET /api/v1/vaults`**  
**Authentication:** Required  
**Description:** Returns all vaults the authenticated user owns or is a member of.

**Response (200 OK):**
```json
[
  {
    "vault_id": "vault-uuid-1",
    "vault_name": "Home Safe",
    "status": "LOCKED",
    "role": "ADMIN",
    "last_seen_at": "2026-02-12T10:30:00Z"
  },
  {
    "vault_id": "vault-uuid-2",
    "vault_name": "Office Vault",
    "status": "OFFLINE",
    "role": "VIEWER",
    "last_seen_at": null
  }
]
```

**`status` values:** `LOCKED` | `UNLOCKED` | `OFFLINE`  
**`role` values:** `ADMIN` | `MEMBER` | `VIEWER`

---

#### Provision Vault

**`POST /api/v1/vaults/provision`**  
**Authentication:** Required  
**Description:** Registers a new physical vault device. The caller becomes the vault owner.

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `hardware_uuid` | string | Yes | Unique hardware identifier of the device |
| `vault_name` | string | No | Human-readable name for the vault |

```json
{
  "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "vault_name": "Home Safe"
}
```

**Response (201 Created):**
```json
{
  "vault_id": "vault-uuid-1",
  "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "vault_name": "Home Safe",
  "status": "LOCKED"
}
```

> **Note:** `status` is always `LOCKED` immediately after provisioning.

**Errors:**
- `409` — A vault with this `hardware_uuid` is already registered

---

#### Get Vault Status

**`GET /api/v1/vaults/{vault_id}/status`**  
**Authentication:** Required

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Response (200 OK):**
```json
{
  "vault_id": "vault-uuid-1",
  "status": "UNLOCKED",
  "last_seen_at": "2026-02-12T10:45:00Z"
}
```

**`status` values:** `LOCKED` | `UNLOCKED` | `OFFLINE`

**Errors:**
- `403` — Caller is not a member of this vault
- `404` — Vault not found

---

#### Send Unlock Command

**`POST /api/v1/vaults/{vault_id}/unlock`**  
**Authentication:** Required  
**Description:** Sends an unlock command to the physical device via WebSocket. The device must be connected.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Response (202 Accepted):**
```json
{
  "command_id": "cmd-uuid-1",
  "vault_id": "vault-uuid-1",
  "expires_at": "2026-02-12T10:46:00Z",
  "sent": true
}
```

> **Note:** `sent: true` means the device received the command over the active WebSocket connection. `sent: false` means the command was queued but the device is not currently connected.

**Errors:**
- `403` — Caller is not authorized to unlock this vault
- `404` — Vault not found
- `503` — Device is not reachable and command could not be delivered

---

#### Set / Update PIN

**`POST /api/v1/vaults/{vault_id}/pin`**  
**Authentication:** Required  
**Authorization:** ADMIN or MEMBER role  
**Rate limit:** 10 requests / 1 min / user per vault

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `pin` | string | Yes | Exactly 6 numeric digits |

```json
{
  "pin": "482910"
}
```

**Response (201 Created):**
```json
{
  "vault_id": "vault-uuid-1",
  "pin_set_at": "2026-02-12T10:30:00Z"
}
```

**Errors:**
- `403` — Caller does not have ADMIN or MEMBER role
- `404` — Vault not found
- `422` — PIN does not meet format requirements (must be exactly 6 numeric digits)

---

#### Remove PIN

**`DELETE /api/v1/vaults/{vault_id}/pin`**  
**Authentication:** Required  
**Authorization:** ADMIN or MEMBER role  
**Rate limit:** 10 requests / 1 min / user per vault

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Response (200 OK):**
```json
{
  "vault_id": "vault-uuid-1",
  "removed": true
}
```

**Errors:**
- `403` — Caller does not have ADMIN or MEMBER role
- `404` — Vault not found
- `409` — No PIN is currently set on this vault

---

#### Get PIN Status

**`GET /api/v1/vaults/{vault_id}/pin/status`**  
**Authentication:** Required

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Response (200 OK):**
```json
{
  "vault_id": "vault-uuid-1",
  "is_set": true,
  "pin_set_at": "2026-02-12T10:30:00Z"
}
```

> **Note:** `pin_set_at` is `null` when `is_set` is `false`.

**Errors:**
- `403` — Caller is not a member of this vault

---

#### Unlock with PIN

**`POST /api/v1/vaults/{vault_id}/unlock/pin`**  
**Authentication:** Required  
**Rate limit:** 15 requests / 1 min / user per vault

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `pin` | string | Yes | 6-digit PIN to attempt |

```json
{
  "pin": "482910"
}
```

**Response (200 OK):**
```json
{
  "vault_id": "vault-uuid-1",
  "result": "SUCCESS",
  "attempts_remaining": null
}
```

**`result` values and `attempts_remaining` semantics:**

| `result` | `attempts_remaining` | Meaning |
|----------|---------------------|---------|
| `SUCCESS` | `null` | PIN was correct; vault unlocked |
| `INVALID` | integer (e.g. `3`) | PIN was incorrect; attempts remaining before lockout |
| `LOCKED_OUT` | `0` | Too many failed attempts; vault is locked out |

**Errors:**
- `401` — Caller is not authenticated
- `403` — Caller is not authorized for this vault
- `404` — Vault not found
- `409` — No PIN is set on this vault
- `423` — Vault is currently locked out due to too many failed attempts

---

### Vault Members

All vault member endpoints require a valid JWT Bearer token.

---

#### List Members

**`GET /api/v1/vaults/{vault_id}/members`**  
**Authentication:** Required

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Response (200 OK):**
```json
{
  "vault_id": "vault-uuid-1",
  "members": [
    {
      "user_id": "user-uuid-1",
      "email": "alice@example.com",
      "full_name": "Alice",
      "role": "ADMIN",
      "granted_at": "2026-02-01T09:00:00Z",
      "granted_by": "user-uuid-owner"
    },
    {
      "user_id": "user-uuid-2",
      "email": "bob@example.com",
      "full_name": null,
      "role": "VIEWER",
      "granted_at": "2026-02-05T14:30:00Z",
      "granted_by": "user-uuid-owner"
    }
  ]
}
```

> **Note:** The vault owner is not included in the members list.

**`role` values:** `ADMIN` | `MEMBER` | `VIEWER`

**Errors:**
- `403` — Caller is not a member of this vault
- `404` — Vault not found

---

#### Add / Update Member

**`POST /api/v1/vaults/{vault_id}/members`**  
**Authentication:** Required  
**Authorization:** Vault owner only  
**Description:** Adds a user as a member or updates their role if they are already a member. This operation is idempotent.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `user_id` | string | Yes | UUID of the user to add or update |
| `role` | string | Yes | `ADMIN`, `MEMBER`, or `VIEWER` |

```json
{
  "user_id": "user-uuid-1",
  "role": "MEMBER"
}
```

**Response (201 Created):**
```json
{
  "user_id": "user-uuid-1",
  "email": "alice@example.com",
  "full_name": "Alice",
  "role": "MEMBER",
  "granted_at": "2026-02-12T10:40:00Z",
  "granted_by": "user-uuid-owner"
}
```

**Errors:**
- `403` — Caller is not the vault owner
- `404` — Vault or target user not found
- `422` — Invalid role value

---

#### Remove Member

**`DELETE /api/v1/vaults/{vault_id}/members/{user_id}`**  
**Authentication:** Required  
**Authorization:** Vault owner only  
**Description:** Removes a member from the vault. This operation is idempotent (removing a non-member is a no-op).

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |
| `user_id` | UUID of the user to remove |

**Response (204 No Content):** No body.

**Errors:**
- `403` — Caller is not the vault owner, or caller is attempting to remove the owner
- `404` — Vault not found
- `422` — Cannot remove the vault owner

---

### Activity

#### Get Vault Activity

**`GET /api/v1/vaults/{vault_id}/activity`**  
**Authentication:** Required  
**Description:** Returns the audit log for a vault, ordered newest first.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `vault_id` | UUID of the vault |

**Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `limit` | integer | `50` | 1–100 | Maximum number of entries to return |

**Response (200 OK):**
```json
{
  "vault_id": "vault-uuid-1",
  "count": 3,
  "entries": [
    {
      "id": "entry-uuid-1",
      "vault_id": "vault-uuid-1",
      "user_id": "user-uuid-1",
      "action": "VAULT_UNLOCKED",
      "method": "PIN",
      "metadata": null,
      "created_at": "2026-02-12T10:45:00Z"
    },
    {
      "id": "entry-uuid-2",
      "vault_id": "vault-uuid-1",
      "user_id": null,
      "action": "VAULT_STATE_CHANGED",
      "method": "DEVICE",
      "metadata": { "previous_status": "UNLOCKED", "new_status": "LOCKED" },
      "created_at": "2026-02-12T10:44:00Z"
    },
    {
      "id": "entry-uuid-3",
      "vault_id": "vault-uuid-1",
      "user_id": "user-uuid-1",
      "action": "UNLOCK_COMMAND_SENT",
      "method": "APP",
      "metadata": { "command_id": "cmd-uuid-1" },
      "created_at": "2026-02-12T10:43:00Z"
    }
  ]
}
```

**Known `action` values:**

| Action | Description |
|--------|-------------|
| `VAULT_UNLOCKED` | Vault was successfully unlocked |
| `VAULT_UNLOCK_FAILED` | Unlock attempt failed (wrong PIN, etc.) |
| `PIN_SET` | A PIN was set or updated |
| `MEMBER_ADDED` | A member was added to the vault |
| `MEMBER_REMOVED` | A member was removed from the vault |
| `VAULT_STATE_CHANGED` | Vault hardware reported a state change |
| `UNLOCK_COMMAND_SENT` | An unlock command was dispatched to the device |

> **Note:** `user_id` may be `null` for system-generated events (e.g., device-initiated state changes). `metadata` may be `null` when no additional context is available.

**Errors:**
- `403` — Caller is not a member of this vault

---

## WebSocket API

### Connection

**URL:** `ws://<host>/api/v1/ws/user?token=<access_token>`

**Authentication:** Pass the JWT access token as a query parameter.

**Example:**
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/user?token=${accessToken}`
);

ws.onopen = () => {
  // Subscribe to vault status updates
  ws.send(JSON.stringify({
    type: "SUBSCRIBE",
    payload: { vault_ids: ["vault-uuid-1", "vault-uuid-2"] }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);
};
```

---

### On Connect — Server Notification

Immediately after a successful connection, the server sends a welcome notification:

**Server → Client:**
```json
{
  "type": "NOTIFICATION",
  "payload": {
    "title": "Connected",
    "message": "Real-time updates active.",
    "severity": "info"
  }
}
```

---

### Client → Server Messages

#### Subscribe to Vault Updates

```json
{
  "type": "SUBSCRIBE",
  "payload": {
    "vault_ids": ["vault-uuid-1", "vault-uuid-2"]
  }
}
```

#### Unsubscribe from Vault Updates

```json
{
  "type": "UNSUBSCRIBE",
  "payload": {
    "vault_ids": ["vault-uuid-1"]
  }
}
```

---

### Server → Client Messages

#### Vault Status Changed

Sent when a subscribed vault changes state.

```json
{
  "type": "VAULT_STATUS_CHANGED",
  "payload": {
    "vault_id": "vault-uuid-1",
    "status": "UNLOCKED",
    "changed_at": "2026-02-12T10:45:00Z",
    "changed_by": "user-uuid-1"
  }
}
```

#### Notification

Sent for informational alerts, warnings, or errors.

```json
{
  "type": "NOTIFICATION",
  "payload": {
    "title": "Vault Unlocked",
    "message": "Home Safe was unlocked by Jane Smith.",
    "severity": "success"
  }
}
```

**`severity` values:** `info` | `warning` | `error` | `success`

#### Error

Sent when the server encounters a problem processing a client message.

```json
{
  "type": "ERROR",
  "payload": {
    "error_code": "VAULT_NOT_FOUND",
    "message": "Vault vault-uuid-99 does not exist or you do not have access."
  }
}
```

---

## Rate Limiting

Rate limits are enforced using Redis. Exceeding a limit returns `429 Too Many Requests`.

### Limits by Endpoint

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| `POST /auth/request-otp` | 3 | 1 minute | Per IP |
| `POST /auth/login` | 5 | 1 minute | Per IP |
| `POST /vaults/{id}/pin` | 10 | 1 minute | Per user per vault |
| `DELETE /vaults/{id}/pin` | 10 | 1 minute | Per user per vault |
| `POST /vaults/{id}/unlock/pin` | 15 | 1 minute | Per user per vault |

### Rate Limit Headers

Rate-limited responses include standard headers:

```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1739354460
Retry-After: 45
```

---

## Token Reference

| Token | Lifetime | Storage Recommendation | Rotation |
|-------|----------|------------------------|----------|
| **Access Token** | 30 minutes | In-memory only (never persist to disk or localStorage) | No — obtain a new one via refresh |
| **Refresh Token** | 7 days | Secure storage (HttpOnly cookie or secure keychain) | Yes — rotated on every use; old token is immediately invalidated |

> **Security note:** Reusing a refresh token after it has been rotated will return `401` and may invalidate the entire session as a security measure.

---

## Authentication Flow Summary

### New User Registration

```
Client                          Server
  |                               |
  |-- POST /auth/request-otp ---> | (rate limited: 3/min/IP)
  |<-- 204 No Content ----------- | OTP sent to email
  |                               |
  |-- POST /auth/verify-otp ----> |
  |<-- 200 { signup_ticket } ---- |
  |                               |
  |-- POST /auth/signup --------> | (signup_ticket + credentials)
  |<-- 201 { id, email, ... } --- | Account created
  |                               |
  |-- POST /auth/login ---------->|
  |<-- 200 { access_token,        |
  |          refresh_token } ---- |
```

### Authenticated Session

```
Client                          Server
  |                               |
  |-- GET /users/me               |
  |   Authorization: Bearer <AT>->|
  |<-- 200 { user } ------------- |
  |                               |
  |   (access token expires)      |
  |                               |
  |-- POST /auth/refresh -------> | (refresh_token in body)
  |<-- 200 { new access_token,    |
  |          new refresh_token } -| (old refresh token invalidated)
```

### Password Reset

```
Client                          Server
  |                               |
  |-- POST /auth/request-         |
  |   password-reset -----------> | (always 204, no enumeration)
  |<-- 204 No Content ----------- | Reset email sent if address exists
  |                               |
  |-- POST /auth/confirm-         |
  |   password-reset -----------> | (token from email + new_password)
  |<-- 204 No Content ----------- | Password updated
```

### Vault Unlock (App Command)

```
Client                          Server                  Device
  |                               |                       |
  |-- POST /vaults/{id}/unlock -> |                       |
  |                               |-- WebSocket command ->|
  |<-- 202 { sent: true } ------- |                       |
  |                               |         (device unlocks physically)
  |                               |<-- status update ---- |
  |                               |-- WS VAULT_STATUS_    |
  |<-- WS VAULT_STATUS_CHANGED -- |   CHANGED broadcast   |
```

### Vault Unlock (PIN)

```
Client                          Server
  |                               |
  |-- POST /vaults/{id}/          |
  |   unlock/pin ---------------> | (rate limited: 15/min/user/vault)
  |<-- 200 { result: "SUCCESS",   |
  |          attempts_remaining:  |
  |          null } ------------- |
```

---

## Internal API

The Internal API is for **admin/ops use only** — not for mobile clients or end users.

**Base path:** `/api/internal`  
**Authentication:** `X-Admin-Token: <token>` header required on all endpoints (set via `ADMIN_API_TOKEN` env var)  
**Note:** All internal endpoints are excluded from the public Swagger docs (`include_in_schema=False`)

---

### Ping

#### GET /internal/ping

Connectivity check for the admin API.

**Response (200):**
```json
{
  "status": "ok",
  "admin_api": "operational",
  "version": "1.0.0"
}
```

---

### Business

#### GET /internal/business/overview

Aggregated business metrics: user counts, vault counts, member counts.

**Response (200):**
```json
{
  "generated_at": "2026-02-28T10:00:00Z",
  "users": {
    "total": 120,
    "new_today": 3,
    "new_this_week": 14
  },
  "vaults": {
    "total": 85,
    "with_pin": 72,
    "by_status": { "LOCKED": 60, "UNLOCKED": 25 }
  },
  "members": {
    "total_authorizations": 210,
    "by_role": { "ADMIN": 40, "MEMBER": 120, "VIEWER": 50 }
  }
}
```

---

#### GET /internal/business/activity

Recent activity across all vaults with aggregated summary.

**Query parameters:**

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `hours` | integer | `24` | `1` | `168` | Time window in hours |
| `limit` | integer | `50` | `1` | `100` | Max entries to return |

**Response (200):**
```json
{
  "generated_at": "2026-02-28T10:00:00Z",
  "period_hours": 24,
  "summary": {
    "total_events": 42,
    "vault_unlocks": 18,
    "failed_unlocks": 6,
    "pin_operations": 3,
    "member_changes": 2,
    "state_changes": 13
  },
  "entries": [
    {
      "id": "log-abc-123",
      "vault_id": "vault-abc-123",
      "user_id": "user-abc-123",
      "action": "VAULT_UNLOCKED",
      "method": "PIN",
      "metadata": { "ip": "192.168.1.10" },
      "created_at": "2026-02-28T09:45:00Z"
    }
  ]
}
```

---

#### GET /internal/business/trends

Daily time-series for user signups and vault provisioning.

**Query parameters:**

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `days` | integer | `30` | `7` | `90` | Window size in days |

**Response (200):**
```json
{
  "generated_at": "2026-02-28T10:00:00Z",
  "period_days": 30,
  "period_start": "2026-01-29",
  "period_end": "2026-02-28",
  "user_signups": {
    "daily": [{ "date": "2026-01-29", "count": 2 }],
    "total": 45,
    "average_per_day": 1.5,
    "peak_date": "2026-02-10",
    "peak_count": 8,
    "change_pct": 12.5
  },
  "vault_provisioning": {
    "daily": [{ "date": "2026-01-29", "count": 1 }],
    "total": 30,
    "average_per_day": 1.0,
    "peak_date": "2026-02-05",
    "peak_count": 5,
    "change_pct": -5.0
  }
}
```

**Notes:**
- `change_pct` compares first half vs second half of the window. Positive = growth, negative = decline, `null` = no prior data.
- Daily arrays are zero-filled — always exactly `days` entries per series.

---

### Security

#### GET /internal/security/alerts

Security alerts based on activity log patterns.

**Response (200):**
```json
{
  "generated_at": "2026-02-28T10:00:00Z",
  "status": "warning",
  "active_alerts": [
    {
      "type": "failed_unlock_spike",
      "severity": "high",
      "message": "6 failed vault unlock attempts in the last hour. Above normal threshold.",
      "count": 6,
      "threshold": 5,
      "window": "1h"
    }
  ],
  "last_24h": {
    "failed_unlocks_1h": 6,
    "failed_unlocks_24h": 14,
    "pin_lockouts_24h": 3
  }
}
```

**Notes:**
- `status`: `ok` | `warning` | `critical`
- `severity`: `low` | `medium` | `high` | `critical`
- Alert thresholds: failed unlocks warning ≥5/hr, critical ≥20/hr; PIN lockouts warning ≥3/24h, critical ≥10/24h

---

### Ops

#### GET /internal/ops/summary

Complete operational dashboard summary — business metrics, security status, and activity in one response.

**Response (200):**
```json
{
  "generated_at": "2026-02-28T10:00:00Z",
  "overall_status": "ok",
  "business": {
    "users": { "total": 120, "new_today": 3, "new_this_week": 14 },
    "vaults": { "total": 85, "with_pin": 72, "by_status": { "LOCKED": 60, "UNLOCKED": 25 } },
    "members": { "total_authorizations": 210, "by_role": { "ADMIN": 40, "MEMBER": 120, "VIEWER": 50 } }
  },
  "security": {
    "status": "ok",
    "failed_unlocks_1h": 1,
    "failed_unlocks_24h": 4,
    "pin_lockouts_24h": 0,
    "alert_count": 0
  },
  "activity": {
    "period_hours": 24,
    "total_events": 42,
    "vault_unlocks": 18,
    "failed_unlocks": 6,
    "pin_operations": 3,
    "member_changes": 2,
    "state_changes": 13
  }
}
```

---

#### GET /internal/ops/diagnostics/redis

Redis health and statistics.

**Response (200):**
```json
{
  "status": "healthy",
  "connected": true,
  "memory_used_mb": 12.4,
  "total_keys": 320,
  "uptime_seconds": 86400,
  "checked_at": "2026-02-28T10:00:00Z"
}
```

---

#### GET /internal/ops/diagnostics/websockets

WebSocket connection statistics.

**Response (200):**
```json
{
  "total_users": 5,
  "total_user_connections": 7,
  "total_vaults": 3,
  "subscriptions": 12,
  "online_vaults": ["vault-abc-123", "vault-def-456"],
  "checked_at": "2026-02-28T10:00:00Z"
}
```

---

#### GET /internal/ops/diagnostics/database

Database connection pool statistics.

**Response (200):**
```json
{
  "status": "healthy",
  "pool_size": 5,
  "checked_out": 1,
  "overflow": 0,
  "checked_at": "2026-02-28T10:00:00Z"
}
```

---

#### GET /internal/ops/rate-limits

Active rate limit keys with top violators.

**Response (200):**
```json
{
  "total_active_keys": 14,
  "top_violators": [
    { "key": "login_req:192.168.1.10", "current_count": 4, "ttl_seconds": 45 }
  ],
  "by_category": { "login_req": 3, "otp_req": 2, "pin:unlock": 9 },
  "checked_at": "2026-02-28T10:00:00Z"
}
```

---

#### GET /internal/ops/sessions/stats

Active refresh token session statistics.

**Response (200):**
```json
{
  "total_active_tokens": 38,
  "top_users": [
    { "user_id": "user-abc-123", "token_count": 3 }
  ],
  "checked_at": "2026-02-28T10:00:00Z"
}
```

---

#### DELETE /internal/ops/sessions/{user_id}

Force-logout a user by revoking all their refresh tokens.

**Path parameter:** `user_id`

**Response (200):**
```json
{
  "user_id": "user-abc-123",
  "sessions_revoked": 2
}
```

**Notes:**
- Use for compromised accounts or suspicious activity
- User must re-authenticate on all devices after this

---

#### GET /internal/ops/notifications/email

Email service health and today's send statistics.

**Response (200):**
```json
{
  "service": "dev",
  "status": "healthy",
  "sent_today": 12,
  "failed_today": 0,
  "note": "Wire increment_email_sent/failed into SMTPEmailService to populate counts.",
  "checked_at": "2026-02-28T10:00:00Z"
}
```

---

#### GET /internal/ops/audit

Paginated admin audit log.

**Query parameters:**

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `page` | integer | `1` | `1` | — | Page number |
| `limit` | integer | `50` | `1` | `100` | Items per page |
| `action` | string | — | — | — | Filter by action type (e.g. `SESSION_REVOKED`) |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "action": "SESSION_REVOKED",
      "target_type": "user",
      "target_id": "user-abc-123",
      "details": { "sessions_revoked": 2 },
      "ip_address": "192.168.1.10",
      "created_at": "2026-02-28T09:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

---

#### GET /internal/ops/api-keys

List API keys.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | `true` | When true, only active keys returned |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Mobile App Key",
      "created_by": "admin_console",
      "last_used_at": "2026-02-28T08:00:00Z",
      "expires_at": null,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

#### POST /internal/ops/api-keys

Create a new API key.

**Request body:**
```json
{
  "name": "Mobile App Key",
  "expires_in_days": 90
}
```

| Field | Constraints |
|-------|-------------|
| `name` | Required |
| `expires_in_days` | Optional — null means no expiry |

**Response (201):**
```json
{
  "id": 1,
  "key": "sv_live_abc123...",
  "name": "Mobile App Key",
  "expires_at": "2026-05-29T00:00:00Z"
}
```

**⚠️ Warning:** The `key` value is shown **once only**. Copy it immediately — it cannot be recovered.

---

#### DELETE /internal/ops/api-keys/{key_id}

Revoke an API key by ID.

**Path parameter:** `key_id` (integer)

**Response:** `204 No Content`

**Notes:**
- Sets `is_active=False` — row is kept for audit purposes
- Error 404 if key not found
