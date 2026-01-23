# API Documentation

Quick reference for key components in `app/api`.

---

## `deps.py` - Dependency Injection

**Purpose**: Reusable components injected into FastAPI routes.

**Key Functions**:
- Database session management (prevents connection leaks)
- User authentication (extracts user from token)
- Authorization checks (reusable permission logic)
- Request-scoped resources (IDs, metadata, locale)

**Usage Example**:
```python
@router.post("/vaults/{id}/unlock")
def unlock_vault(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    ...
```

**Why It Matters**: Centralizes security/database logic, prevents code duplication, ensures consistent resource cleanup.

---

## `router.py` - Route Organization

**Purpose**: Organizes and centralizes API endpoint routing.

**Why It Matters**: Provides clear API structure, ensures routing consistency, simplifies maintenance.

---

## `v1/` - API Versioning

**Purpose**: Contains versioned endpoints for backward compatibility.

**Why It Matters**: Allows API evolution without breaking existing clients.