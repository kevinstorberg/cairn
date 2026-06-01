import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.loader import load_default_config
from src.routers import health
from src.routers.health import _VERSION
from src.websockets.router import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from cache.backends import get_cache_backend
    from memory.backends import get_backend

    # Startup
    app.state.memory_backend = get_backend()
    app.state.cache_backend = get_cache_backend()

    # Trigger service auto-registration
    import src.services  # noqa: F401

    logger.info("App startup complete")

    yield

    # Shutdown
    if hasattr(app.state, "memory_backend"):
        backend = app.state.memory_backend
        if hasattr(backend, "close"):
            await backend.close()

    from db.connection import dispose_engine

    await dispose_engine()
    logger.info("App shutdown complete")


def create_app() -> FastAPI:
    config = load_default_config()

    application = FastAPI(title="Cairn", version=_VERSION, lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, tags=["health"])
    application.include_router(ws_router)
    return application


app = create_app()
