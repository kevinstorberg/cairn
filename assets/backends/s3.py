"""S3 storage backend skeleton.

EXTENSION POINT: This is scaffolding for the AWS S3 storage backend.
Install dependencies with `poetry install --with aws`, then implement
the methods below for cloud object storage.

See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
"""

from assets.base import StorageBackend
from lib.cairn.stubs import stub_method

_STUB_MESSAGE = (
    "S3Storage is not yet implemented. " "Install deps with `poetry install --with aws` and implement to use."
)


class S3Storage(StorageBackend):
    """Skeleton for S3-based cloud object storage.

    To implement: initialize a boto3 S3 client using AWS credentials
    from settings, and implement upload/download/delete/exists.
    """

    def __init__(self):
        pass

    upload = stub_method(_STUB_MESSAGE)
    download = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
    exists = stub_method(_STUB_MESSAGE)
