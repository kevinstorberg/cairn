import logging
import os

from memory.base import MemoryBackend

logger = logging.getLogger(__name__)

_backend_instance: MemoryBackend | None = None


def get_backend() -> MemoryBackend:
    """Get or create singleton memory backend instance."""
    global _backend_instance

    if _backend_instance is None:
        backend_name = os.environ.get("MEMORY_BACKEND", "faiss").lower()
        logger.info(f"Initializing memory backend: {backend_name}")

        if backend_name == "faiss":
            from memory.backends.faiss import FAISSBackend
            _backend_instance = FAISSBackend()
        elif backend_name == "pgvector":
            from memory.backends.pgvector import PGVectorBackend
            _backend_instance = PGVectorBackend()
        elif backend_name == "pinecone":
            from memory.backends.pinecone import PineconeBackend
            _backend_instance = PineconeBackend()
        else:
            raise ValueError(
                f"Unknown memory backend: {backend_name}. "
                f"Valid options: faiss, pgvector, pinecone"
            )

    return _backend_instance


def reset_backend():
    """Reset singleton for testing or environment changes."""
    global _backend_instance
    if _backend_instance is not None:
        logger.info("Resetting memory backend singleton")
    _backend_instance = None
