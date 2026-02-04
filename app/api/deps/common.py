import os

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db


def running_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db
