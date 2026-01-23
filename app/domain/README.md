# Domain Layer Documentation

Quick reference for `app/domain` components.

---

## `events/` - Domain Events

**Purpose**: Represents significant business occurrences that trigger actions.

**Key Files**:
- `security_events.py` - Authentication/authorization events
- `vault_events.py` - Vault operation events

**Why It Matters**: Decouples components, provides audit trail, enables extensibility.

---

## `models/` - Domain Models

**Purpose**: Core business entities with their data and behavior.

**Key Files**:
- `access_log.py` - Access tracking
- `user.py` - User entity with auth details
- `vault.py` - Vault entity with status/operations

**Why It Matters**: Encapsulates business logic, provides clear domain structure.

---

## `value_objects/` - Immutable Values

**Purpose**: Self-contained, validated domain concepts.

**Key Files**:
- `biometric_result.py` - Biometric authentication results
- `vault_status.py` - Vault states (locked/unlocked)

**Why It Matters**: Ensures valid states, improves type safety and clarity.