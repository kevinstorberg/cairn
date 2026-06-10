from __future__ import annotations

import re
from dataclasses import dataclass

_PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class ProjectIdentity:
    project_name: str
    repo_name: str
    package_name: str
    console_command: str
    description: str
    db_prefix: str

    @classmethod
    def from_inputs(
        cls,
        *,
        project_name: str,
        repo_name: str | None = None,
        package_name: str | None = None,
        console_command: str | None = None,
        description: str | None = None,
        db_prefix: str | None = None,
    ) -> ProjectIdentity:
        display = _require_non_empty(project_name, "project_name")
        derived_repo = repo_name or _slugify(display)
        derived_package = package_name or derived_repo.replace("-", "_")
        derived_command = console_command or derived_repo
        derived_description = description or f"{display} application"
        derived_db_prefix = db_prefix or derived_package

        _validate_slug(derived_repo, "repo_name")
        _validate_package(derived_package, "package_name")
        _validate_slug(derived_command, "console_command")
        _validate_package(derived_db_prefix, "db_prefix")

        return cls(
            project_name=display,
            repo_name=derived_repo,
            package_name=derived_package,
            console_command=derived_command,
            description=derived_description,
            db_prefix=derived_db_prefix,
        )

    @property
    def core_package(self) -> str:
        return f"{self.package_name}_core"

    @property
    def core_path(self) -> str:
        return f"lib/{self.core_package}"


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _validate_slug(value: str, field_name: str) -> None:
    if not _SLUG_RE.match(value):
        raise ValueError(f"{field_name} must be lowercase kebab-case")


def _validate_package(value: str, field_name: str) -> None:
    if not _PACKAGE_RE.match(value):
        raise ValueError(f"{field_name} must be a valid lowercase Python identifier")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    if not normalized:
        raise ValueError("project_name must contain at least one alphanumeric character")
    if normalized[0].isdigit():
        normalized = f"app-{normalized}"
    return normalized
