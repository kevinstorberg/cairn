from cache.base import CacheBackend
from config.loader import load_default_config


def get_cache_backend() -> CacheBackend:
    """Get cache backend instance based on configuration."""
    config = load_default_config()
    backend_name = config.cache.backend.lower()

    if backend_name == "memory":
        from cache.backends.memory import InMemoryCacheBackend

        return InMemoryCacheBackend()
    elif backend_name == "redis":
        from cache.backends.redis import RedisCacheBackend

        return RedisCacheBackend()

    raise ValueError(f"Unknown cache backend: {backend_name}. " f"Valid options: memory, redis")
