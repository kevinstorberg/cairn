from assets.base import StorageBackend


class S3Storage(StorageBackend):
    def __init__(self):
        pass

    async def upload(self, key: str, content: bytes, content_type: str = "") -> str:
        raise NotImplementedError("S3Storage requires `poetry install --with aws`")

    async def download(self, key: str) -> bytes:
        raise NotImplementedError("S3Storage requires `poetry install --with aws`")

    async def delete(self, key: str) -> None:
        raise NotImplementedError("S3Storage requires `poetry install --with aws`")

    async def exists(self, key: str) -> bool:
        raise NotImplementedError("S3Storage requires `poetry install --with aws`")
