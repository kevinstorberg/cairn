"""Path utilities for resolving module-relative paths.

This module provides utilities for consistently resolving paths relative to
module files, eliminating repeated Path(__file__).resolve().parent patterns.
"""

from pathlib import Path


def get_module_dir(file: str) -> Path:
    """Get directory containing the calling module.

    Args:
        file: The __file__ attribute of the calling module

    Returns:
        Resolved path to the directory containing the module

    Usage:
        >>> # In config/loader.py
        >>> _CONFIG_DIR = get_module_dir(__file__)
    """
    return Path(file).resolve().parent


def get_repo_root(file: str) -> Path:
    """Get repository root from a module file.

    Assumes the calling module is 2 levels deep from repo root
    (e.g., src/settings.py or config/loader.py).

    Args:
        file: The __file__ attribute of the calling module

    Returns:
        Resolved path to the repository root

    Usage:
        >>> # In src/settings.py
        >>> _REPO_ROOT = get_repo_root(__file__)
    """
    return Path(file).resolve().parent.parent
