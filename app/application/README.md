# Application Documentation

Quick reference for `app/application` components.

---

## `use_cases/` - Business Logic

**Purpose**: Encapsulates specific business workflows and operations.

**Key Files**:
- `authenticate_user.py` - User authentication and token generation
- `provision_vault.py` - Vault initialization and configuration
- `unlock_vault.py` - Vault unlocking and access control
- `enroll_biometrics.py` - Biometric enrollment
- `log_activity.py` - Activity and event logging

**Why It Matters**: Separates business logic from other layers, making code testable and reusable.

---

## `services/` - Shared Utilities

**Purpose**: Reusable functionality supporting multiple use cases.

**Key Files**:
- `token_service.py` - Token generation and validation
- `authorization_service.py` - Permission checks
- `liveness_service.py` - Health monitoring

**Why It Matters**: Prevents duplication, ensures consistency across use cases.