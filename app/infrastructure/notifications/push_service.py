from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.infrastructure.db.models.device_token_orm import DeviceTokenORM

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class ExpoPushService:
    """
    Push notification delivery via Expo Push Notification Service.

    Expo routes messages to FCM (Android) and APNS (iOS) transparently.
    No Firebase project or Apple certificates needed on the backend —
    only the Expo push token obtained from the mobile app.

    All methods are fire-and-forget: failures are logged, never raised,
    so a push outage never breaks the main request flow.
    """

    async def send(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        sound: str = "default",
        priority: str = "high",
    ) -> None:
        """Send push notification to a list of Expo push tokens."""
        if not tokens:
            return

        messages = [
            {
                "to": token,
                "title": title,
                "body": body,
                "data": data or {},
                "sound": sound,
                "priority": priority,
            }
            for token in tokens
        ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    EXPO_PUSH_URL,
                    json=messages,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        "expo_push_non_200",
                        extra={"status": response.status_code, "body": response.text[:200]},
                    )
                else:
                    logger.debug("expo_push_sent", extra={"token_count": len(tokens), "title": title})
        except Exception as exc:
            logger.error("expo_push_failed", extra={"error": str(exc), "title": title})

    async def send_to_user(
        self,
        db: Session,
        user_id: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Look up all device tokens for a user and send a push notification."""
        rows = db.query(DeviceTokenORM).filter(DeviceTokenORM.user_id == user_id).all()
        tokens = [row.token for row in rows]

        if not tokens:
            logger.debug("expo_push_no_tokens", extra={"user_id": user_id})
            return

        await self.send(tokens, title, body, data)


# Singleton — reuse across requests
push_service = ExpoPushService()
