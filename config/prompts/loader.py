from lib.cairn.paths import get_module_dir

_PROMPTS_DIR = get_module_dir(__file__)


def load_prompt(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text().strip()
