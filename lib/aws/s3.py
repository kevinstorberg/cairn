from lib.aws.base import AWSClientProtocol


class S3Client(AWSClientProtocol):
    def __init__(self, bucket: str = "", region: str = "us-east-1"):
        self._bucket = bucket
        self._region = region
        self._client = None

    async def health_check(self) -> bool:
        return self._client is not None

    async def close(self) -> None:
        self._client = None

    async def upload(self, key: str, body: bytes, content_type: str = "application/octet-stream") -> str:
        raise NotImplementedError("S3Client requires `poetry install --with aws`")

    async def download(self, key: str) -> bytes:
        raise NotImplementedError("S3Client requires `poetry install --with aws`")

    async def delete(self, key: str) -> None:
        raise NotImplementedError("S3Client requires `poetry install --with aws`")
