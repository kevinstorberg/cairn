from types import SimpleNamespace

import pytest

import cache.backends as cache_backends
from cache.backends.memory import InMemoryCacheBackend
from cache.backends.redis import RedisCacheBackend


@pytest.fixture(autouse=True)
def reset_cache_backend_factory():
    cache_backends.reset_cache_backend()
    yield
    cache_backends.reset_cache_backend()


def _config_for_cache(backend: str):
    return SimpleNamespace(cache=SimpleNamespace(backend=backend))


def test_get_cache_backend_returns_memory_backend(monkeypatch):
    monkeypatch.setattr(cache_backends, "load_default_config", lambda: _config_for_cache("memory"))

    backend = cache_backends.get_cache_backend()

    assert isinstance(backend, InMemoryCacheBackend)


def test_get_cache_backend_returns_redis_stub(monkeypatch):
    monkeypatch.setattr(cache_backends, "load_default_config", lambda: _config_for_cache("redis"))

    backend = cache_backends.get_cache_backend()

    assert isinstance(backend, RedisCacheBackend)


def test_get_cache_backend_rejects_unknown_backend(monkeypatch):
    monkeypatch.setattr(cache_backends, "load_default_config", lambda: _config_for_cache("unknown"))

    with pytest.raises(ValueError, match="Unknown cache backend"):
        cache_backends.get_cache_backend()


def test_redis_cache_stub_methods_fail_clearly():
    backend = RedisCacheBackend()

    with pytest.raises(NotImplementedError, match="RedisCacheBackend is not yet implemented"):
        backend.get("key")
