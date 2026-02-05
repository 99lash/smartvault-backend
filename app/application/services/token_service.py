from __future__ import annotations

from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.settings import settings

class TokenService:
    def create_access_token(self, subject: str | int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        return encoded_jwt