import os

from memory.base import MemoryBackend


def get_backend() -> MemoryBackend:
    backend_name = os.environ.get("MEMORY_BACKEND", "faiss")
    if backend_name == "faiss":
        from memory.backends.faiss import FAISSBackend

        return FAISSBackend()
    elif backend_name == "pgvector":
        from memory.backends.pgvector import PGVectorBackend

        return PGVectorBackend()
    elif backend_name == "pinecone":
        from memory.backends.pinecone import PineconeBackend

        return PineconeBackend()
    else:
        raise ValueError(f"Unknown memory backend: {backend_name!r}. Available: faiss, pgvector, pinecone")
