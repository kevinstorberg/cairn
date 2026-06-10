from __future__ import annotations

import shutil
from pathlib import Path

COPY_EXCLUDED_NAMES = {
    ".claude",
    ".coverage",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "storage",
    "tmp",
}

COPY_EXCLUDED_PATHS = {
    Path("frontend") / "dist",
    Path("frontend") / "node_modules",
}

COPY_EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}

COPY_EXCLUDED_FILES = {
    ".env.development",
    ".env.production",
    ".env.test",
}


def copy_template(source: Path, target: Path, *, force: bool = False) -> None:
    if target.exists() and any(target.iterdir()):
        if not force:
            raise FileExistsError(f"Target directory is not empty: {target}")
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=_ignore)


def _ignore(directory: str, names: list[str]) -> set[str]:
    root = Path(directory)
    ignored: set[str] = set()
    for name in names:
        path = root / name
        relative_parts = path.parts
        if name in COPY_EXCLUDED_NAMES or name in COPY_EXCLUDED_FILES or path.suffix in COPY_EXCLUDED_SUFFIXES:
            ignored.add(name)
            continue
        for excluded_path in COPY_EXCLUDED_PATHS:
            if (
                len(relative_parts) >= len(excluded_path.parts)
                and tuple(relative_parts[-len(excluded_path.parts) :]) == excluded_path.parts
            ):
                ignored.add(name)
                break
    return ignored
