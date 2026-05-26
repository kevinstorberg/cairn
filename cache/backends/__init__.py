import os

from cache.base import CacheBackend


def get_cache_backend() -> CacheBackend:
    backend_name = os.environ.get("CACHE_BACKEND", "memory")
    if backend_name == "memory":
        from cache.backends.memory import InMemoryCacheBackend
        return InMemoryCacheBackend()
    elif backend_name == "redis":
        from cache.backends.redis import RedisCacheBackend
        return RedisCacheBackend()
    raise ValueError(f"Unknown cache backend: {backend_name}")
