from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.models.user import User
from app.application.ports.user_repository import UserRepository

# Define Protocol for hasher to avoid direct dependency on infrastructure
class PasswordHasher(Protocol):
    def verify(self, raw_password: str, encoded: str) -> bool:
        ...

@dataclass
class LoginInput:
    email: str
    password: str

class InvalidCredentialsError(Exception):
    pass

class AuthenticateUser:
    
    _DUMMY_HASH = "pbkdf2$210000$ZHJleHlsbA$Gw2y/k6e/sI2Z1k0LgJq3l5e8X7f5b1c"
    
    def __init__(self, repo: UserRepository, hasher: PasswordHasher):
        self._repo = repo
        self._hasher = hasher

    def execute(self, data: LoginInput) -> User:
        user = self._repo.get_by_email(data.email)
        if not user:
            # Timing attack mitigation (verify a fake hash)? 
            # For now, simple return to avoid complexity over-engineering
            self._hasher.verify(data.password, self._DUMMY_HASH)
            raise InvalidCredentialsError("Invalid email or password")
        
        if not self._hasher.verify(data.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
            
        return user