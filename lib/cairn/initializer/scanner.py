from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_TOKENS = (
    "Cairn",
    "cairn",
    "FastAPI template",
    "TEMPLATE INFRASTRUCTURE",
    "template users",
)

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".css",
    ".env",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".lock",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".tsx",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

EXCLUDED_DIRS = {
    ".claude",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "frontend/dist",
    "frontend/node_modules",
    "htmlcov",
    "node_modules",
    "storage",
    "tmp",
}


@dataclass(frozen=True)
class ForbiddenFinding:
    path: Path
    line_number: int
    token: str
    line: str


def scan_forbidden_tokens(
    repo_root: Path,
    *,
    allow_paths: set[Path] | None = None,
) -> tuple[ForbiddenFinding, ...]:
    allowed = allow_paths or set()
    findings: list[ForbiddenFinding] = []
    for path in iter_text_files(repo_root):
        if path in allowed:
            continue
        content = read_text_if_possible(repo_root / path)
        if content is None:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            for token in FORBIDDEN_TOKENS:
                if token in line:
                    findings.append(ForbiddenFinding(path, line_number, token, line.strip()))
    return tuple(findings)


def iter_text_files(repo_root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in _iter_project_files(repo_root) if _is_text_candidate(path)))


def read_text_if_possible(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _iter_project_files(repo_root: Path) -> list[Path]:
    tracked = _git_tracked_files(repo_root)
    if tracked is not None:
        return [path for path in tracked if not _is_excluded(path)]

    files: list[Path] = []
    for path in repo_root.rglob("*"):
        relative = path.relative_to(repo_root)
        if path.is_dir() or _is_excluded(relative):
            continue
        files.append(relative)
    return files


def _git_tracked_files(repo_root: Path) -> list[Path] | None:
    if not (repo_root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return [Path(line) for line in result.stdout.splitlines() if line]


def _is_excluded(path: Path) -> bool:
    parts = path.parts
    for index in range(len(parts)):
        candidate = "/".join(parts[: index + 1])
        if candidate in EXCLUDED_DIRS or parts[index] in EXCLUDED_DIRS:
            return True
    return False


def _is_text_candidate(path: Path) -> bool:
    return (
        path.suffix in TEXT_SUFFIXES
        or path.name in {"Dockerfile", "Makefile", ".dockerignore", ".gitignore"}
        or path.name.startswith(".env")
    )
