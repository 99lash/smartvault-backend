import pytest
from fastapi.testclient import TestClient
from typing import Generator

from app.main import create_app
from app.api.deps.vaults import get_vault_repo
from app.api.deps.auth import get_email_service
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.tests.fakes.email_service import CaptureEmailService
from app.infrastructure.cache.redis_client import redis_shutdown


@pytest.fixture
def app():
    return create_app()


@pytest.fixture(autouse=True)
async def _reset_redis_singleton():
    await redis_shutdown()
    yield
    await redis_shutdown()


@pytest.fixture
def vault_repo(app) -> Generator[InMemoryVaultRepository, None, None]:
    repo = InMemoryVaultRepository()
    app.dependency_overrides[get_vault_repo] = lambda: repo
    yield repo
    app.dependency_overrides.pop(get_vault_repo, None)


@pytest.fixture
def capture_email_service(app) -> Generator[CaptureEmailService, None, None]:
    svc = CaptureEmailService()
    app.dependency_overrides[get_email_service] = lambda: svc
    yield svc
    app.dependency_overrides.pop(get_email_service, None)


@pytest.fixture
def client(app, vault_repo) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
