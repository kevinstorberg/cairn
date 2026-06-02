import pytest

import memory.backends as memory_backends
from config.models import DefaultConfig, MemoryConfig
from memory.backends import create_memory_backend
from memory.backends.in_memory import InMemoryVectorBackend
from memory.backends.pgvector import PGVectorBackend
from memory.backends.pinecone import PineconeBackend


@pytest.fixture(autouse=True)
def reset_memory_backend_factory():
    memory_backends.reset_backend()
    yield
    memory_backends.reset_backend()


@pytest.mark.parametrize("backend_name", ["in_memory", "faiss"])
def test_create_memory_backend_returns_in_memory_backend(backend_name):
    backend = create_memory_backend(MemoryConfig(backend=backend_name))

    assert isinstance(backend, InMemoryVectorBackend)


def test_get_backend_returns_in_memory_backend(monkeypatch):
    config = DefaultConfig(memory=MemoryConfig(backend="in_memory"))
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: config)

    backend = memory_backends.get_backend()
    assert isinstance(backend, InMemoryVectorBackend)


def test_get_backend_returns_pgvector_stub(monkeypatch):
    config = DefaultConfig(memory=MemoryConfig(backend="pgvector"))
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: config)

    backend = memory_backends.get_backend()

    assert isinstance(backend, PGVectorBackend)


def test_get_backend_returns_pinecone_stub(monkeypatch):
    config = DefaultConfig(memory=MemoryConfig(backend="pinecone"))
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: config)

    backend = memory_backends.get_backend()

    assert isinstance(backend, PineconeBackend)


def test_create_memory_backend_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unknown memory backend"):
        create_memory_backend(MemoryConfig(backend="unknown"))


def test_pgvector_stub_methods_fail_clearly():
    backend = PGVectorBackend()

    with pytest.raises(NotImplementedError, match="PGVectorBackend is not yet implemented"):
        backend.store("id", "text", {}, [0.1])


def test_pinecone_stub_methods_fail_clearly():
    backend = PineconeBackend()

    with pytest.raises(NotImplementedError, match="PineconeBackend is not yet implemented"):
        backend.search([0.1])
