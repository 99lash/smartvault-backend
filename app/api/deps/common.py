import os

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.infrastructure.db.session import get_db


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user_id(x_dev_user_id: str | None = Header(None, convert_underscores=False)) -> str:
    # TODO: replace with real authentication (JWT/session)
    env = (settings.environment or "").lower()
    if settings.DEV_AUTH_BYPASS:
        return "demo-user-1"
    if env == "development" and x_dev_user_id:
        return x_dev_user_id
    raise HTTPException(status_code=401, detail="Authentication required")
