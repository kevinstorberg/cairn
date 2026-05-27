from lib.aws.base import AWSClientProtocol
from lib.cairn.stubs import stub_method

_STUB_MESSAGE = "S3Client requires `poetry install --with aws`"


class S3Client(AWSClientProtocol):
    def __init__(self, bucket: str = "", region: str = "us-east-1"):
        self._bucket = bucket
        self._region = region
        self._client = None

    async def health_check(self) -> bool:
        return self._client is not None

    async def close(self) -> None:
        self._client = None

    upload = stub_method(_STUB_MESSAGE)
    download = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
