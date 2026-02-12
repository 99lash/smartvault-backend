import socket
from dataclasses import replace
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from contextlib import asynccontextmanager

from app.main import create_app
from app.api.deps.vaults import get_vault_repo, get_vault_auth_repo
from app.api.deps.auth import get_email_service, get_rate_limiter, get_current_user_id as auth_get_current_user_id
from app.api.deps.users import get_user_repo, get_current_user
from app.core.settings import settings
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.infrastructure.db.repositories.in_memory_vault_authorization_repository import (
    InMemoryVaultAuthorizationRepository,
)
from app.application.ports.user_repository import UserRepository

_in_memory_vault_auth_repo = InMemoryVaultAuthorizationRepository()
from app.domain.models.user import User
from app.tests.fakes.email_service import CaptureEmailService
from app.infrastructure.cache.redis_client import redis_shutdown


@pytest.fixture
def app():
    previous = settings.DEV_AUTH_BYPASS
    settings.DEV_AUTH_BYPASS = True
    previous_redis_url = settings.REDIS_URL
    settings.REDIS_URL = f"redis://{_detect_redis_host()}:6379/0"
    # Skip expensive/external lifespan work (Redis, websocket manager) during tests
    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app = create_app()
    app.router.lifespan_context = _noop_lifespan
    try:
        app.dependency_overrides[auth_get_current_user_id] = lambda: "test-user-id"
        yield app
    finally:
        app.dependency_overrides.pop(auth_get_current_user_id, None)
        settings.DEV_AUTH_BYPASS = previous
        settings.REDIS_URL = previous_redis_url


def _detect_redis_host() -> str:
    """
    Determine Redis host usable in both host and container test environments.

    Tries Docker service DNS name 'redis' first (works in container network).
    Falls back to localhost (works when using forwarded port from host).
    """
    for host in ("redis", "localhost"):
        try:
            socket.getaddrinfo(host, 6379)
            return host
        except socket.gaierror:
            continue
    return "localhost"


@pytest.fixture(autouse=True)
def _force_test_redis_url():
    """Ensure Redis URL points at reachable Redis for tests."""
    previous = settings.REDIS_URL
    host = _detect_redis_host()
    settings.REDIS_URL = f"redis://{host}:6379/0"
    yield
    settings.REDIS_URL = previous


@pytest.fixture(autouse=True)
async def _reset_redis_singleton():
    try:
        await redis_shutdown()
    except RuntimeError:
        pass
    yield
    try:
        await redis_shutdown()
    except RuntimeError:
        pass


@pytest.fixture(autouse=True)
def _clear_in_memory_vault_auth_repo():
    """Clear in-memory vault authorization repo between tests."""
    _in_memory_vault_auth_repo.clear()
    yield
    _in_memory_vault_auth_repo.clear()


class _FakeUserRepo(UserRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, object] = {}
        self._by_email: dict[str, object] = {}

    def clear(self) -> None:
        self._by_id.clear()
        self._by_email.clear()

    def save(self, user):
        self._by_id[user.id] = user
        self._by_email[user.email.strip().lower()] = user

    def get_by_email(self, email: str):
        return self._by_email.get(email.strip().lower())

    def create(self, user):
        self.save(user)
        return user

    def get_by_id(self, user_id: str):
        return self._by_id.get(user_id)

    def get_by_ids(self, user_ids: list[str]) -> dict[str, object]:
        return {uid: user for uid, user in self._by_id.items() if uid in user_ids}

    def update_profile(self, user_id: str, full_name: str | None):
        user = self.get_by_id(user_id)
        if not user:
            return None
        updated = replace(user, full_name=full_name)
        self.save(updated)
        return updated

    def update_password(self, user_id: str, password_hash: str):
        user = self.get_by_id(user_id)
        if not user:
            return None
        updated = replace(user, password_hash=password_hash)
        self.save(updated)
        return updated


class _NoopRateLimiter:
    async def allow_request(self, *args, **kwargs):
        return None


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
def user_repo(app) -> Generator[_FakeUserRepo, None, None]:
    repo = _FakeUserRepo()
    test_user = User(
        id="demo-user-1",
        email="owner@example.com",
        password_hash="test-hash",
        full_name="Vault Owner",
        created_at=datetime.now(timezone.utc),
    )
    repo.save(test_user)
    app.dependency_overrides[get_user_repo] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield repo
    app.dependency_overrides.pop(get_user_repo, None)
    app.dependency_overrides.pop(get_current_user, None)
    repo.clear()


@pytest.fixture
def vault_auth_repo(app):
    app.dependency_overrides[get_vault_auth_repo] = lambda: _in_memory_vault_auth_repo
    yield _in_memory_vault_auth_repo
    app.dependency_overrides.pop(get_vault_auth_repo, None)


@pytest.fixture
def rate_limiter(app):
    limiter = _NoopRateLimiter()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    yield limiter
    app.dependency_overrides.pop(get_rate_limiter, None)


@pytest.fixture
def client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
