from types import SimpleNamespace

import pytest

import assets.backends as storage_backends
from assets.backends.local import LocalStorage
from assets.backends.s3 import S3Storage


def _config_for_storage(backend: str, local_path: str = "./storage"):
    return SimpleNamespace(storage=SimpleNamespace(backend=backend, local_path=local_path))


def test_get_storage_backend_returns_local_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_backends, "load_default_config", lambda: _config_for_storage("local", str(tmp_path)))

    backend = storage_backends.get_storage_backend()

    assert isinstance(backend, LocalStorage)


def test_get_storage_backend_returns_s3_stub(monkeypatch):
    monkeypatch.setattr(storage_backends, "load_default_config", lambda: _config_for_storage("s3"))

    backend = storage_backends.get_storage_backend()

    assert isinstance(backend, S3Storage)


def test_get_storage_backend_rejects_unknown_backend(monkeypatch):
    monkeypatch.setattr(storage_backends, "load_default_config", lambda: _config_for_storage("unknown"))

    with pytest.raises(ValueError, match="Unknown storage backend"):
        storage_backends.get_storage_backend()


def test_s3_storage_stub_methods_fail_clearly():
    backend = S3Storage()

    with pytest.raises(NotImplementedError, match="S3Storage is not yet implemented"):
        backend.upload("file.txt", b"content")
