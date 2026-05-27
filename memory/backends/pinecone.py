from lib.cairn.stubs import stub_method
from memory.base import MemoryBackend

_STUB_MESSAGE = "PineconeBackend requires `poetry install --with pinecone`"


class PineconeBackend(MemoryBackend):
    store = stub_method(_STUB_MESSAGE)
    search = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
