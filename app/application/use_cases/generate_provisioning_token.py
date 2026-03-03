"""
Generate a provisioning token for a user.

The token is used during firmware captive portal provisioning.
Format: 6 digits only (e.g. 482931) — matches ESP32 captive portal input.
Single-use — expires after 5 minutes via Redis TTL.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.application.ports.provisioning_token_store import ProvisioningTokenStore
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 10
TOKEN_TTL_SECONDS = 300


@dataclass
class GenerateProvisioningTokenInput:
    user_id: str


class GenerateProvisioningToken:
    def __init__(self, token_store: ProvisioningTokenStore) -> None:
        self._token_store = token_store

    async def execute(self, input: GenerateProvisioningTokenInput) -> str:
        for attempt in range(MAX_RETRIES):
            token = f"{secrets.randbelow(1_000_000):06d}"
            if await self._token_store.set(token, input.user_id, TOKEN_TTL_SECONDS):
                logger.info(
                    "provisioning_token_generated",
                    user_id=input.user_id,
                    attempt=attempt + 1,
                )
                return token

        raise RuntimeError("Failed to generate unique provisioning token after retries")
