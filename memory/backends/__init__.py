import logging

from config.loader import load_default_config
from lib.cairn.singleton import singleton
from memory.base import MemoryBackend

logger = logging.getLogger(__name__)


@singleton
def get_backend() -> MemoryBackend:
    """Get or create singleton memory backend instance."""
    config = load_default_config()
    backend_name = config.memory.backend.lower()
    logger.info(f"Initializing memory backend: {backend_name}")

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
        raise ValueError(f"Unknown memory backend: {backend_name}. " f"Valid options: faiss, pgvector, pinecone")


# Expose reset for testing
reset_backend = get_backend.reset
