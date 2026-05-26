from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text().strip()
