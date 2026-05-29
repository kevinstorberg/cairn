from assets.base import StorageBackend
from lib.cairn.stubs import stub_method

_STUB_MESSAGE = "S3Storage requires `poetry install --with aws`"


class S3Storage(StorageBackend):
    def __init__(self):
        pass

    upload = stub_method(_STUB_MESSAGE)
    download = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
    exists = stub_method(_STUB_MESSAGE)
