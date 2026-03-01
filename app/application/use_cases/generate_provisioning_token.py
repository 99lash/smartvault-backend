"""
Generate a provisioning token for a user.

The token is used during firmware captive portal provisioning.
Format: 6 digits + 2 uppercase letters (e.g. 482931KZ)
Single-use — cleared after device registration.
"""
from __future__ import annotations

import random
import string
from dataclasses import dataclass

from app.application.ports.user_repository import UserRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 10


@dataclass
class GenerateProvisioningTokenInput:
    user_id: str


class GenerateProvisioningToken:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, input: GenerateProvisioningTokenInput) -> str:
        for attempt in range(MAX_RETRIES):
            digits = "".join(random.choices(string.digits, k=6))
            letters = "".join(random.choices(string.ascii_uppercase, k=2))
            token = digits + letters

            if self._user_repo.get_by_provisioning_token(token) is None:
                self._user_repo.set_provisioning_token(input.user_id, token)
                logger.info(
                    "provisioning_token_generated",
                    user_id=input.user_id,
                    attempt=attempt + 1,
                )
                return token

        raise RuntimeError("Failed to generate unique provisioning token after retries")
