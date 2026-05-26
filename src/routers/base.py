from fastapi import APIRouter


def create_router(*, prefix: str = "", tags: list[str] | None = None) -> APIRouter:
    return APIRouter(prefix=prefix, tags=tags or [])
