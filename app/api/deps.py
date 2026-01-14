from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository

_vault_repo = InMemoryVaultRepository()

def get_vault_repo():
    return _vault_repo
