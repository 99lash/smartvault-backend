# Internal Ops API

This document describes the internal operational endpoints used by the Admin Console TUI and other internal tools. These endpoints are strictly for administrative usage and monitoring.

---

## Authentication

All internal endpoints are protected by an api key mechanism.

**Header:**
```http
X-Admin-Token: <SECRET_TOKEN>
```

**Base URL:** `/internal`

---

## Endpoints

### 1. Operations Dashboard

#### Get Summary
**Endpoint:** `GET /internal/ops/summary`  
**Description:** Aggregates key business metrics and system status.

**Response:**
```json
{
  "overall_status": "ok",
  "users_total": 120,
  "vaults_active": 45,
  "vaults_locked": 3,
  "alerts_active": 1,
  "last_updated": "2026-02-15T12:00:00Z"
}
```

---

### 2. Notifications

#### Get Email Service Status
**Endpoint:** `GET /internal/ops/notifications/email`  
**Description:** Checks the health of the email notification system.

**Response:**
```json
{
  "service": "smtp",
  "status": "operational",
  "sent_today": 150,
  "failed_today": 2,
  "note": "All systems go",
  "checked_at": "2026-02-15T12:05:00Z"
}
```

**Status Values:** `operational`, `degraded`, `outage`, `maintenance`.

---

### 3. Security

#### List Alerts
**Endpoint:** `GET /internal/security/alerts?status=open&limit=10`  
**Description:** Fetches security alerts requiring attention.

**Response:**
```json
{
  "items": [
    {
      "id": "alert-123",
      "severity": "high",
      "type": "brute_force",
      "source_ip": "192.168.1.100",
      "timestamp": "2026-02-15T10:00:00Z",
      "status": "open"
    }
  ],
  "total": 1
}
```

#### Resolve Alert
**Endpoint:** `POST /internal/security/alerts/{alert_id}/resolve`
**Description:** Marks an alert as resolved.

---

### 4. API Keys (Internal Management)

#### List Keys
**Endpoint:** `GET /internal/ops/api-keys`  
**Description:** Lists active internal API keys.

#### Create Key
**Endpoint:** `POST /internal/ops/api-keys`  
**Body:** `{"name": "DevOps Tool", "scopes": ["read:metrics"]}`

#### Revoke Key
**Endpoint:** `DELETE /internal/ops/api-keys/{key_id}`

---

## Error Handling

Standard HTTP status codes apply:
- `401 Unauthorized`: Invalid or missing `X-Admin-Token`.
- `403 Forbidden`: Token lacks required scope (if scopes implemented).
- `404 Not Found`: Resource checks failed.
- `500 Internal Server Error`: Backend failure.
