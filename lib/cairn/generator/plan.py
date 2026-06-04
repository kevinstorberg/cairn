from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from lib.cairn.generator.render import (
    render_migration,
    render_model,
    render_repository,
    render_resource_doc,
    render_router,
    render_router_test,
    render_schema,
    render_schema_test,
    render_service,
)
from lib.cairn.generator.spec import ResourceSpec


@dataclass(frozen=True)
class PlannedFile:
    path: Path
    content: str


@dataclass(frozen=True)
class GenerateResult:
    planned_files: tuple[PlannedFile, ...]
    written_files: tuple[Path, ...]
    dry_run: bool


class ResourceGenerator:
    def __init__(
        self,
        repo_root: Path,
        *,
        revision_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repo_root = repo_root
        self._revision_factory = revision_factory or _default_revision

    def plan(self, spec: ResourceSpec) -> tuple[PlannedFile, ...]:
        revision = self._revision_factory()
        return (
            PlannedFile(Path("db") / "models" / "__init__.py", ""),
            PlannedFile(Path("db") / "models" / f"{spec.name}.py", render_model(spec)),
            PlannedFile(Path("db") / "repositories" / "__init__.py", ""),
            PlannedFile(Path("db") / "repositories" / f"{spec.name}.py", render_repository(spec)),
            PlannedFile(Path("src") / "models" / f"{spec.name}.py", render_schema(spec)),
            PlannedFile(Path("src") / "services" / f"{spec.name}.py", render_service(spec)),
            PlannedFile(Path("src") / "routers" / f"{spec.name}.py", render_router(spec)),
            PlannedFile(
                Path("db") / "migrations" / "versions" / f"{revision}_create_{spec.name}.py",
                render_migration(spec, revision=revision),
            ),
            PlannedFile(Path("tests") / spec.name / "__init__.py", ""),
            PlannedFile(Path("tests") / spec.name / f"test_{spec.name}_schemas.py", render_schema_test(spec)),
            PlannedFile(Path("tests") / spec.name / f"test_{spec.name}_router.py", render_router_test(spec)),
            PlannedFile(Path("docs") / "resources" / f"{spec.name}.md", render_resource_doc(spec)),
        )

    def generate(self, spec: ResourceSpec, *, dry_run: bool = False, force: bool = False) -> GenerateResult:
        planned_files = self.plan(spec)
        conflicts = [file.path for file in planned_files if self._conflicts(file)]
        if conflicts and not force:
            formatted = ", ".join(str(path) for path in conflicts)
            raise FileExistsError(f"Refusing to overwrite existing files: {formatted}")

        if dry_run:
            return GenerateResult(planned_files=planned_files, written_files=(), dry_run=True)

        written: list[Path] = []
        for file in planned_files:
            target = self.repo_root / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_ensure_trailing_newline(file.content))
            written.append(file.path)
        return GenerateResult(planned_files=planned_files, written_files=tuple(written), dry_run=False)

    def _conflicts(self, file: PlannedFile) -> bool:
        target = self.repo_root / file.path
        if not target.exists():
            return False
        return target.read_text() != _ensure_trailing_newline(file.content)


def _default_revision() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _ensure_trailing_newline(content: str) -> str:
    if not content:
        return ""
    return content if content.endswith("\n") else f"{content}\n"
