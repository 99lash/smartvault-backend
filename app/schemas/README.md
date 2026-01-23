# Schemas Documentation

Quick reference for `app/schemas` components.

---

## Overview

**Purpose**: Pydantic schemas for data validation and serialization.

**Why It Matters**: Ensures consistent data structure, validates input/output, provides type safety.

---

## Key Files

| File | Purpose |
|------|---------|
| `auth.py` | Login, token generation, authentication models |
| `users.py` | User creation, updates, retrieval models |
| `vaults.py` | Vault operations and data models |
| `biometrics.py` | Biometric enrollment and authentication models |
| `activity.py` | Activity logging and retrieval models |

---

## Common Benefits

- **Validation**: Ensures data conforms to expected structure
- **Consistency**: Standardized data handling across the application
- **Security**: Validates sensitive data (auth, biometrics)
- **Maintainability**: Centralized schema definitions