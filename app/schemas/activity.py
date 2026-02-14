from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ActivityLogEntry(BaseModel):
    """Single activity log entry returned by the API."""
    id: str
    vault_id: str
    user_id: str | None
    action: str
    method: str
    metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogResponse(BaseModel):
    """Paginated list of activity log entries for a vault."""
    vault_id: str
    entries: list[ActivityLogEntry]
    count: int