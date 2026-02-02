import pytest

from app.application.use_cases.create_user import CreateUser, CreateUserInput, DuplicateEmailError
from app.application.services.password_hasher_service import PBKDF2PasswordHasher
from app.infrastructure.db.repositories.in_memory_user_repository import InMemoryUserRepository


def test_create_user_happy_path():
    repo = InMemoryUserRepository()
    hasher = PBKDF2PasswordHasher(iterations=10_000)  
    uc = CreateUser(repo=repo, hasher=hasher)

    user = uc.execute(
        CreateUserInput(
            email="A@Example.com",
            password="verylongpassword!",
            full_name="Alice",
        )
    )

    assert user.id
    assert user.email == "a@example.com"
    assert user.full_name == "Alice"
    assert user.password_hash != "verylongpassword!"
    assert repo.get_by_email("a@example.com") is not None


def test_create_user_duplicate_email_raises():
    repo = InMemoryUserRepository()
    hasher = PBKDF2PasswordHasher(iterations=10_000)
    uc = CreateUser(repo=repo, hasher=hasher)

    uc.execute(CreateUserInput(email="a@example.com", password="verylongpassword!"))

    with pytest.raises(DuplicateEmailError):
        uc.execute(CreateUserInput(email="a@example.com", password="verylongpassword!"))
