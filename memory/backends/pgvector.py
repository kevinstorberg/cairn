"""PGVector memory backend skeleton.

EXTENSION POINT: This is scaffolding for the pgvector backend.
Install dependencies with `poetry install --with pgvector`, then implement
the methods below to use PostgreSQL with pgvector for semantic search.

See: https://github.com/pgvector/pgvector-python
"""

from lib.cairn.stubs import stub_method
from memory.base import MemoryBackend

_STUB_MESSAGE = (
    "PGVectorBackend is not yet implemented. "
    "Install deps with `poetry install --with pgvector` and implement to use."
)


class PGVectorBackend(MemoryBackend):
    """Skeleton for pgvector-based semantic search.

    To implement: connect to PostgreSQL, create a table with a vector column,
    and implement store/search/delete using pgvector operations.
    """

    store = stub_method(_STUB_MESSAGE)
    search = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
