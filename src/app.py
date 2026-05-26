from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.routers import health
from src.routers.health import _VERSION
from src.websockets.router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Cairn", version=_VERSION, lifespan=lifespan)
    application.include_router(health.router, tags=["health"])
    application.include_router(ws_router)
    return application


app = create_app()
