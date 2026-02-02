import pytest
from fastapi.testclient import TestClient
from typing import Generator

from app.main import app
from app.api.deps import get_vault_repo
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository

@pytest.fixture
def vault_repo() -> Generator[InMemoryVaultRepository, None, None]:
    """
    Fixture that provides an empty in-memory repository
    and overrides the app's dependency.
    """
    repo = InMemoryVaultRepository()
    app.dependency_overrides[get_vault_repo] = lambda: repo
    yield repo
    app.dependency_overrides.clear()

@pytest.fixture
def client(vault_repo: InMemoryVaultRepository) -> Generator[TestClient, None, None]:
    """
    Fixture that provides a TestClient.
    Depends on vault_repo to ensure overrides are in place.
    """
    with TestClient(app) as c:
        yield c
