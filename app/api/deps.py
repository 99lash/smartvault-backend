# To organize and centralize dependencies, preventing clutter in the router files.

from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository

_vault_repo = InMemoryVaultRepository()

def get_vault_repo():
    return _vault_repo


def get_current_user_id() -> str:
    return "demo-user-1"
