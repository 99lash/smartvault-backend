from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.settings import Settings


@lru_cache
def _get_engine():
    settings = Settings()
    return create_engine(settings.DATABASE_URL)


@lru_cache
def _get_sessionmaker():
    return sessionmaker(bind=_get_engine(), autocommit=False, autoflush=False)


# Export SessionLocal for use in dependencies
SessionLocal = _get_sessionmaker()


def get_db():
    """Provide database session for request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
