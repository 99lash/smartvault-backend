from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings


@lru_cache
def _get_engine():
    settings = Settings()
    return create_engine(settings.DATABASE_URL)


@lru_cache
def _get_sessionmaker():
    return sessionmaker(bind=_get_engine(), autocommit=False, autoflush=False)


def get_db():
    SessionLocal = _get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
