import pytest

import cache.backends as cache_backends
from cache.backends import create_cache_backend
from cache.backends.memory import InMemoryCacheBackend
from cache.backends.redis import RedisCacheBackend
from config.models import CacheConfig, DefaultConfig


@pytest.fixture(autouse=True)
def reset_cache_backend_factory():
    cache_backends.reset_cache_backend()
    yield
    cache_backends.reset_cache_backend()


def test_create_cache_backend_returns_memory_backend():
    backend = create_cache_backend(CacheConfig(backend="memory"))

    assert isinstance(backend, InMemoryCacheBackend)


def test_get_cache_backend_returns_memory_backend(monkeypatch):
    config = DefaultConfig(cache=CacheConfig(backend="memory"))
    monkeypatch.setattr(cache_backends, "load_default_config", lambda: config)

    backend = cache_backends.get_cache_backend()
    assert isinstance(backend, InMemoryCacheBackend)


def test_get_cache_backend_returns_redis_stub(monkeypatch):
    config = DefaultConfig(cache=CacheConfig(backend="redis"))
    monkeypatch.setattr(cache_backends, "load_default_config", lambda: config)

    backend = cache_backends.get_cache_backend()

    assert isinstance(backend, RedisCacheBackend)


def test_create_cache_backend_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unknown cache backend"):
        create_cache_backend(CacheConfig(backend="unknown"))


def test_redis_cache_stub_methods_fail_clearly():
    backend = RedisCacheBackend()

    with pytest.raises(NotImplementedError, match="RedisCacheBackend is not yet implemented"):
        backend.get("key")
