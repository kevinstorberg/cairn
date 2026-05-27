import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.routers import health
from src.routers.health import _VERSION
from src.websockets.router import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize memory backend singleton
    from memory.backends import get_backend
    app.state.memory_backend = get_backend()
    logger.info("Memory backend initialized in app lifespan")

    yield

    # Shutdown: Close memory backend if it has close method
    if hasattr(app.state, 'memory_backend'):
        backend = app.state.memory_backend
        if hasattr(backend, 'close'):
            await backend.close()
        logger.info("Memory backend closed")


def create_app() -> FastAPI:
    application = FastAPI(title="Cairn", version=_VERSION, lifespan=lifespan)
    application.include_router(health.router, tags=["health"])
    application.include_router(ws_router)
    return application


app = create_app()
