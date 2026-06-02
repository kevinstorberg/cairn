import pytest

import assets.backends as storage_backends
from assets.backends import create_storage_backend
from assets.backends.local import LocalStorage
from assets.backends.s3 import S3Storage
from config.models import DefaultConfig, StorageConfig


def test_create_storage_backend_returns_local_backend(tmp_path):
    backend = create_storage_backend(StorageConfig(backend="local", local_path=str(tmp_path)))

    assert isinstance(backend, LocalStorage)


def test_get_storage_backend_returns_local_backend(monkeypatch, tmp_path):
    config = DefaultConfig(storage=StorageConfig(backend="local", local_path=str(tmp_path)))
    monkeypatch.setattr(storage_backends, "load_default_config", lambda: config)

    backend = storage_backends.get_storage_backend()
    assert isinstance(backend, LocalStorage)


def test_get_storage_backend_returns_s3_stub(monkeypatch):
    config = DefaultConfig(storage=StorageConfig(backend="s3"))
    monkeypatch.setattr(storage_backends, "load_default_config", lambda: config)

    backend = storage_backends.get_storage_backend()

    assert isinstance(backend, S3Storage)


def test_create_storage_backend_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unknown storage backend"):
        create_storage_backend(StorageConfig(backend="unknown"))


def test_s3_storage_stub_methods_fail_clearly():
    backend = S3Storage()

    with pytest.raises(NotImplementedError, match="S3Storage is not yet implemented"):
        backend.upload("file.txt", b"content")
