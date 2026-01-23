# Infrastructure Documentation

Quick reference for `app/infrastructure` components.

---

## `db/` - Database Layer

**Purpose**: Database interaction and data persistence.

**Contents**:
- `repositories/` - Data access implementations
- `models/` - ORM models and schema definitions

**Why It Matters**: Centralizes database logic, ensures consistent data access.

---

## `cache/` - Caching Layer

**Purpose**: Redis-based caching utilities.

**Why It Matters**: Improves performance, reduces database load, enhances scalability.

---

## `messaging/` - Real-Time Communication

**Purpose**: WebSocket and event bus utilities.

**Why It Matters**: Enables real-time updates, supports event-driven architecture.

---

## `notifications/` - Notification Services

**Purpose**: Push notification delivery.

**Why It Matters**: Reliable user engagement through timely notifications.

---

## `security/` - Security Utilities

**Purpose**: Password hashing, rate limiting, threat protection.

**Why It Matters**: Protects against common threats, ensures security compliance.

---

## `biometrics/` - Biometric Integration

**Purpose**: Face recognition and biometric authentication.

**Why It Matters**: Secure, convenient user authentication.