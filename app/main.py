from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.request_id import RequestIDMiddleware
from app.api.router import api_router
from app.core.settings import settings
from app.core.logging import get_logger, setup_logging
from app.core.sentry import init_sentry
from app.infrastructure.messaging.websocket_manager import manager
from app.infrastructure.cache.redis_client import redis_startup, redis_shutdown
from app.infrastructure.services.session_metrics import close_session_metrics_pool

from prometheus_fastapi_instrumentator import Instrumentator
from app.infrastructure.monitoring.metrics import set_app_info

init_sentry()

# Create instrumentor once at module level to avoid duplicate metric registration
_instrumentator = None
logger = get_logger(__name__)


def get_instrumentator() -> Instrumentator:
    """Get or create the reusable Prometheus instrumentator."""
    global _instrumentator
    if _instrumentator is None:
        _instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=False,
            should_instrument_requests_inprogress=True,
            excluded_handlers=[
                "/metrics",
                "/api/v1/health",
                "/api/v1/health/detailed",
                "/docs",
                "/openapi.json",
            ],
        )
    return _instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    await redis_startup()
    await manager.start()
    logger.info("websocket_manager_started")

    yield

    await manager.stop()
    await redis_shutdown()
    close_session_metrics_pool()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )

    cors_origins = list(
        dict.fromkeys([*(settings.CORS_ORIGINS or []), "http://localhost:5173"])
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Admin-Token"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(api_router, prefix="/api")

    # Only instrument if not already done to avoid duplicate metrics
    if not hasattr(app, "_instrumented"):
        get_instrumentator().instrument(app).expose(
            app,
            endpoint="/metrics",
            include_in_schema=False,
        )
        app._instrumented = True

    set_app_info(
        version=app.version,
        environment=settings.environment,
    )

    return app


app = create_app()


# ============================================
# Quick test endpoint to verify WebSocket works
# ============================================

@app.get("/api")
async def api_root():
    stats = manager.get_connection_stats()
    return {
        "message": "SmartVault API",
        "websocket_stats": stats,
    }