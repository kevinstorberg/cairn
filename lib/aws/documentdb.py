from lib.aws.base import AWSClientProtocol


class DocumentDBClient(AWSClientProtocol):
    def __init__(self, connection_string: str = ""):
        self._connection_string = connection_string
        self._client = None

    async def health_check(self) -> bool:
        return self._client is not None

    async def close(self) -> None:
        self._client = None
