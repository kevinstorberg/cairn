"""Redis cache backend skeleton.

EXTENSION POINT: This is scaffolding for the Redis cache backend.
Install dependencies with `poetry install --with redis`, then implement
the methods below for distributed caching.

See: https://redis-py.readthedocs.io/en/stable/
"""

from lib.cairn.stubs import stub_method

_STUB_MESSAGE = (
    "RedisCacheBackend is not yet implemented. " "Install deps with `poetry install --with redis` and implement to use."
)


class RedisCacheBackend:
    """Skeleton for Redis-based distributed caching.

    To implement: initialize an async Redis client using the REDIS_URL
    from settings, and implement get/set/delete/exists with serialization.
    """

    get = stub_method(_STUB_MESSAGE)
    set = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
    exists = stub_method(_STUB_MESSAGE)
