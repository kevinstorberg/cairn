from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from fastapi import APIRouter

router = APIRouter()

try:
    _VERSION = pkg_version("cairn")
except PackageNotFoundError:
    _VERSION = "0.1.0"


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": "cairn",
        "version": _VERSION,
    }
