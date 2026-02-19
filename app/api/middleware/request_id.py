from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp
from structlog.contextvars import bind_contextvars, clear_contextvars


REQUEST_ID_HEADER = "X-Request-ID"

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns and propagates a request id for each request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        request_id = self._get_validated_request_id(request)
        bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    def _get_validated_request_id(self, request: Request) -> str:
        """Extract and validate request ID from header, or generate a new one.
        
        Returns a safe UUID string, rejecting:
        - Non-UUID formats
        - Oversized headers (>36 chars)
        - Missing values
        """
        client_id = request.headers.get(REQUEST_ID_HEADER)
        
        if not client_id:
            return str(uuid.uuid4())
        
        # Reject oversized headers
        if len(client_id) > 36:
            return str(uuid.uuid4())
        
        # Validate UUID format
        try:
            uuid.UUID(client_id)
            return client_id
        except (ValueError, AttributeError):
            return str(uuid.uuid4())
