from types import SimpleNamespace

import pytest

import memory.backends as memory_backends
from memory.backends.in_memory import InMemoryVectorBackend
from memory.backends.pgvector import PGVectorBackend
from memory.backends.pinecone import PineconeBackend


@pytest.fixture(autouse=True)
def reset_memory_backend_factory():
    memory_backends.reset_backend()
    yield
    memory_backends.reset_backend()


def _config_for_memory(backend: str):
    return SimpleNamespace(memory=SimpleNamespace(backend=backend))


@pytest.mark.parametrize("backend_name", ["in_memory", "faiss"])
def test_get_backend_returns_in_memory_backend(monkeypatch, backend_name):
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: _config_for_memory(backend_name))

    backend = memory_backends.get_backend()

    assert isinstance(backend, InMemoryVectorBackend)


def test_get_backend_returns_pgvector_stub(monkeypatch):
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: _config_for_memory("pgvector"))

    backend = memory_backends.get_backend()

    assert isinstance(backend, PGVectorBackend)


def test_get_backend_returns_pinecone_stub(monkeypatch):
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: _config_for_memory("pinecone"))

    backend = memory_backends.get_backend()

    assert isinstance(backend, PineconeBackend)


def test_get_backend_rejects_unknown_backend(monkeypatch):
    monkeypatch.setattr(memory_backends, "load_default_config", lambda: _config_for_memory("unknown"))

    with pytest.raises(ValueError, match="Unknown memory backend"):
        memory_backends.get_backend()


def test_pgvector_stub_methods_fail_clearly():
    backend = PGVectorBackend()

    with pytest.raises(NotImplementedError, match="PGVectorBackend is not yet implemented"):
        backend.store("id", "text", {}, [0.1])


def test_pinecone_stub_methods_fail_clearly():
    backend = PineconeBackend()

    with pytest.raises(NotImplementedError, match="PineconeBackend is not yet implemented"):
        backend.search([0.1])
