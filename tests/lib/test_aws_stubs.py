import pytest

from lib.aws.documentdb import DocumentDBClient
from lib.aws.s3 import S3Client


@pytest.mark.asyncio
async def test_documentdb_health_reflects_client_state_and_close_clears_client():
    client = DocumentDBClient("mongodb://example")

    assert await client.health_check() is False

    client._client = object()
    assert await client.health_check() is True

    await client.close()
    assert await client.health_check() is False


def test_s3_client_stub_methods_fail_clearly():
    client = S3Client(bucket="bucket")

    with pytest.raises(NotImplementedError, match="S3Client requires `poetry install --with aws`"):
        client.upload("file.txt", b"content")
