# API Documentation

This document provides an overview of the key components in the `app/api` directory, explaining their roles and importance.

---

## @/app/api/deps.py

### What does this file do?
The `deps.py` file contains dependencies that FastAPI injects into routes. These dependencies are reusable components that handle specific tasks, ensuring clean and maintainable code.

### Role
- **Dependency Injection**: Centralizes the logic for managing dependencies like database sessions, authentication, and authorization.
- **Shared Utilities**: Provides utilities that are reused across multiple routes, such as extracting the current user or managing request-scoped resources.

### Why is it important?
- **Lifecycle Management**: Ensures proper management of resources like database sessions, preventing connection leaks and ensuring efficient resource usage.
- **Security**: Centralizes authentication and authorization logic, ensuring consistency and reducing the risk of security vulnerabilities.
- **Maintainability**: Avoids code duplication by reusing dependencies across routes, making the codebase easier to maintain and update.

### Key Responsibilities
1. **Database Session Lifecycle**:
   - Creates and cleans up a database session per request.
   - Ensures proper lifecycle management and prevents connection leaks.
   - Keeps database logic out of routes.

2. **Current Authenticated User**:
   - Extracts the user from a token and returns a domain-safe object.
   - Centralizes authentication behavior and keeps security logic consistent.

3. **Authorization Checks**:
   - Provides reusable permission checks.
   - Prevents copy-pasted access checks and makes authorization explicit at the route level.

4. **Request-Scoped Resources**:
   - Manages resources like correlation IDs, request metadata, and locale/timezone settings.
   - Improves logging and tracing while avoiding global state.

### How Routes Use deps.py
Routes declare dependencies using FastAPI's `Depends` mechanism. For example:
```python
@router.post("/vaults/{id}/unlock")
def unlock_vault(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    ...
```

---

## @/app/api/router.py

### What does this file do?
The `router.py` file organizes API endpoints and centralizes routing logic for the application.

### Role
- **Endpoint Organization**: Groups related API endpoints into logical units, making the API structure clear and easy to navigate.
- **Centralized Routing Logic**: Manages the routing logic in a single place, ensuring consistency and reducing redundancy.

### Why is it important?
- **Clarity**: Provides a clear structure for the API, making it easier for developers to understand and extend.
- **Consistency**: Ensures that routing logic is consistent across the application, reducing the risk of errors.
- **Maintainability**: Centralizes routing logic, making it easier to update and maintain the API.

---

## @/app/api/v1

### What does this folder do?
The `v1` folder contains the versioned API endpoints, ensuring backward compatibility and structured API evolution.

### Role
- **Versioning**: Manages different versions of the API, allowing for backward compatibility and smooth transitions between versions.
- **Structured Evolution**: Provides a structured way to evolve the API, ensuring that changes are managed in a controlled manner.

### Why is it important?
- **Backward Compatibility**: Ensures that existing clients continue to work even as the API evolves.
- **Structured Changes**: Allows for structured and controlled changes to the API, reducing the risk of breaking existing functionality.
- **Future-Proofing**: Makes it easier to introduce new features and changes without disrupting existing clients.