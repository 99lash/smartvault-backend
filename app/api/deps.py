# What deps.py Is Responsible For?
# deps.py should contain only things that FastAPI injects into routes.
# Typical examples:
    #1 Database session lifecycle (Database Session Dependency)
        # Creates and cleans up a DB session per request.
        # Why:
            # Ensures proper lifecycle management
            # Prevents connection leaks
            # Keeps DB logic out of routes
    #2 Current authenticated user (Current User Resolution)
    # Extracts the user from a token and returns a domain-safe object.
    # Why:
        # Routes shouldn’t decode tokens
        # Centralizes auth behavior
        # Keeps security logic consistent
    #3 Authorization checks (Authorization Guards)
    # Reusable permission checks.
    # Why:
        # Prevents copy-pasted access checks
        # Makes authorization explicit at the route level
    #4 Request-scoped resources (Request Context Dependencies)
    # Examples:
        # Correlation IDs
        # Request metadata
        # Locale or timezone
    # Why:
        # Improves logging and tracing
        # Avoids global state

# How Routes Use deps.py
# Routes declare dependencies, they don’t implement them.
    # @router.post("/vaults/{id}/unlock")
    # def unlock_vault(
    #     user = Depends(get_current_user),
    #     db = Depends(get_db)
    # ):
    #     ...

