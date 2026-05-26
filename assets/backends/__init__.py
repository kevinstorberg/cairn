import os

from assets.base import StorageBackend


def get_storage_backend() -> StorageBackend:
    backend = os.environ.get("STORAGE_BACKEND", "local")
    if backend == "local":
        from assets.backends.local import LocalStorage

        base_path = os.environ.get("STORAGE_LOCAL_PATH", "./storage")
        return LocalStorage(base_path=base_path)
    elif backend == "s3":
        from assets.backends.s3 import S3Storage

        return S3Storage()
    else:
        raise ValueError(f"Unknown storage backend: {backend!r}. Available: local, s3")
