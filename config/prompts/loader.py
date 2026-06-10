"""Prompt template loader for application prompts.

When you build your application and need to load LLM prompts from files,
use this utility to load them from config/prompts/*.txt files.

Example usage:
    from config.prompts.loader import load_prompt

    system_prompt = load_prompt("system_instructions")
    user_prompt = load_prompt("task_template")
"""

from pathlib import Path

from lib.cairn.paths import get_module_dir

_PROMPTS_DIR = get_module_dir(__file__)


def load_prompt(name: str) -> str:
    """Load a prompt template from a .txt file.

    Add prompt .txt files to config/prompts/ and load them by basename or filename.

    Args:
        name: Filename with or without .txt extension (for example, "system_instructions")

    Returns:
        The prompt text as a string with whitespace stripped

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    path = _PROMPTS_DIR / _prompt_filename(name)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text().strip()


def _prompt_filename(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Prompt name must be non-empty")
    if normalized in {".", ".."} or "\\" in normalized:
        raise ValueError(f"Prompt name must be a single .txt file name, got {name!r}")

    filename = normalized if normalized.endswith(".txt") else f"{normalized}.txt"
    path = Path(filename)
    if path.name != filename or path.is_absolute() or filename == ".txt":
        raise ValueError(f"Prompt name must be a single .txt file name, got {name!r}")
    return filename
