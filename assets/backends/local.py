from pathlib import Path

from assets.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str):
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    async def upload(self, key: str, content: bytes, content_type: str = "") -> str:
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    async def download(self, key: str) -> bytes:
        path = self._base / key
        if not path.exists():
            raise FileNotFoundError(f"Asset not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        path = self._base / key
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        return (self._base / key).exists()
