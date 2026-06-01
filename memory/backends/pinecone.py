"""Pinecone memory backend skeleton.

EXTENSION POINT: This is scaffolding for the Pinecone backend.
Install dependencies with `poetry install --with pinecone`, then implement
the methods below to use Pinecone for managed vector search.

See: https://docs.pinecone.io/docs/python-client
"""

from lib.cairn.stubs import stub_method
from memory.base import MemoryBackend

_STUB_MESSAGE = (
    "PineconeBackend is not yet implemented. "
    "Install deps with `poetry install --with pinecone` and implement to use."
)


class PineconeBackend(MemoryBackend):
    """Skeleton for Pinecone-based managed vector search.

    To implement: initialize Pinecone client, create/connect to an index,
    and implement store/search/delete using the Pinecone SDK.
    """

    store = stub_method(_STUB_MESSAGE)
    search = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
