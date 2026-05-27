"""Stub backend generator for optional dependencies.

This module provides utilities for creating consistent stub methods across
optional backend implementations.
"""

from typing import Any, Callable


def stub_method(message: str) -> Callable[..., None]:
    """Create a stub method that raises NotImplementedError with a consistent message.

    This provides a single source of truth for stub error messages across all
    optional backend implementations.

    Args:
        message: The error message to raise (e.g., "PineconeBackend requires `poetry install --with pinecone`")

    Returns:
        A function that raises NotImplementedError when called

    Example:
        >>> class PineconeBackend:
        ...     store = stub_method("PineconeBackend requires `poetry install --with pinecone`")
        ...     search = stub_method("PineconeBackend requires `poetry install --with pinecone`")
        ...
        >>> backend = PineconeBackend()
        >>> backend.store()  # Raises NotImplementedError with message
    """

    def _stub(*args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(message)

    return _stub
