from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    tags=["system"],
)
def health_check() -> HealthResponse:
    """
    Basic liveness probe.

    Returns 200 if the service is running.
    No external dependencies are checked here.
    """
    return HealthResponse(status="ok")
