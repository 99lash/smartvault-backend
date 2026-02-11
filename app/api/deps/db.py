"""
Database dependencies for FastAPI endpoints.

Provides database session via dependency injection.
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Provide database session for request.
    
    Usage in endpoint:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    
    Yields:
        Database session
        
    Note:
        Session is automatically closed after request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()