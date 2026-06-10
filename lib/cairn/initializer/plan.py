from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from lib.cairn.initializer.manifest import TEMPLATE_DOCS, Replacement, cli_for, readme_for, replacements_for
from lib.cairn.initializer.naming import ProjectIdentity
from lib.cairn.initializer.scanner import (
    ForbiddenFinding,
    iter_text_files,
    read_text_if_possible,
    scan_forbidden_tokens,
)


@dataclass(frozen=True)
class PlannedReplacement:
    path: Path
    replacements: tuple[Replacement, ...]


@dataclass(frozen=True)
class PlannedWrite:
    path: Path
    content: str


@dataclass(frozen=True)
class PlannedMove:
    source: Path
    target: Path


@dataclass(frozen=True)
class InitPlan:
    identity: ProjectIdentity
    replacements: tuple[PlannedReplacement, ...]
    writes: tuple[PlannedWrite, ...]
    deletes: tuple[Path, ...]
    delete_trees: tuple[Path, ...]
    moves: tuple[PlannedMove, ...]
    dry_run_findings: tuple[ForbiddenFinding, ...]

    def summary_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        for replacement in self.replacements:
            lines.append(f"replace: {replacement.path}")
        for write in self.writes:
            lines.append(f"write: {write.path}")
        for delete in self.deletes:
            lines.append(f"delete: {delete}")
        for tree in self.delete_trees:
            lines.append(f"delete-tree: {tree}")
        for move in self.moves:
            lines.append(f"move: {move.source} -> {move.target}")
        for finding in self.dry_run_findings:
            lines.append(f"forbidden-current: {finding.path}:{finding.line_number}: {finding.token}")
        return tuple(lines)


class ProjectInitializer:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def plan(
        self,
        identity: ProjectIdentity,
        *,
        force: bool = False,
        keep_initializer: bool = False,
        logo_path: Path | None = None,
    ) -> InitPlan:
        self._validate_can_initialize(identity, force=force)

        replacements = self._planned_replacements(identity)
        writes = [PlannedWrite(Path("README.md"), readme_for(identity, has_logo=logo_path is not None))]
        if not keep_initializer:
            writes.append(PlannedWrite(Path("scripts") / "cli.py", cli_for(identity)))
        deletes = self._planned_deletes(logo_path=logo_path, keep_initializer=keep_initializer)
        moves = (PlannedMove(Path("lib") / "cairn", Path("lib") / identity.core_package),)
        delete_trees = (
            ()
            if keep_initializer
            else (
                Path("lib") / identity.core_package / "initializer",
                Path("tests") / "initializer",
            )
        )
        findings = scan_forbidden_tokens(self.repo_root)
        return InitPlan(
            identity=identity,
            replacements=replacements,
            writes=tuple(writes),
            deletes=deletes,
            delete_trees=delete_trees,
            moves=moves,
            dry_run_findings=findings,
        )

    def apply(
        self,
        plan: InitPlan,
        *,
        logo_path: Path | None = None,
        keep_initializer: bool = False,
    ) -> tuple[ForbiddenFinding, ...]:
        self._validate_move_targets(plan)
        for replacement in plan.replacements:
            self._apply_replacement(replacement)
        for write in plan.writes:
            target = self.repo_root / write.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_ensure_trailing_newline(write.content))
        for delete in plan.deletes:
            target = self.repo_root / delete
            if target.exists():
                target.unlink()
        if logo_path is not None:
            target = self.repo_root / "assets" / "static" / "logo.svg"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo_path, target)
        for move in plan.moves:
            source = self.repo_root / move.source
            target = self.repo_root / move.target
            if source.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
        for tree in plan.delete_trees:
            target = self.repo_root / tree
            if target.exists():
                shutil.rmtree(target)

        allow_paths = set()
        if keep_initializer:
            allow_paths.update(
                path
                for path in iter_text_files(self.repo_root)
                if path.parts[:3] == ("lib", plan.identity.core_package, "initializer")
            )
        findings = scan_forbidden_tokens(self.repo_root, allow_paths=allow_paths)
        if findings:
            formatted = "\n".join(
                f"{finding.path}:{finding.line_number}: {finding.token}: {finding.line}" for finding in findings
            )
            raise ValueError(f"Forbidden branding remains after initialization:\n{formatted}")
        return findings

    def _validate_can_initialize(self, identity: ProjectIdentity, *, force: bool) -> None:
        pyproject = self.repo_root / "pyproject.toml"
        source_core = self.repo_root / "lib" / "cairn"
        target_core = self.repo_root / "lib" / identity.core_package
        if target_core.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing package namespace: {target_core.relative_to(self.repo_root)}"
            )
        if not source_core.exists():
            raise ValueError("This repository does not look like an uninitialized Cairn template: missing lib/cairn")
        if not force and pyproject.exists() and 'name = "cairn"' not in pyproject.read_text():
            raise ValueError(
                "This repository appears to be already initialized. Use --force only if you know this is safe."
            )

    def _validate_move_targets(self, plan: InitPlan) -> None:
        for move in plan.moves:
            target = self.repo_root / move.target
            if target.exists():
                raise FileExistsError(f"Refusing to overwrite existing package namespace: {move.target}")

    def _planned_replacements(self, identity: ProjectIdentity) -> tuple[PlannedReplacement, ...]:
        replacements = replacements_for(identity)
        planned: list[PlannedReplacement] = []
        for path in iter_text_files(self.repo_root):
            if path in TEMPLATE_DOCS or path == Path("README.md"):
                continue
            content = read_text_if_possible(self.repo_root / path)
            if content is None:
                continue
            used = tuple(replacement for replacement in replacements if replacement.old in content)
            if used:
                planned.append(PlannedReplacement(path, used))
        return tuple(planned)

    def _planned_deletes(self, *, logo_path: Path | None, keep_initializer: bool) -> tuple[Path, ...]:
        deletes = [path for path in TEMPLATE_DOCS if (self.repo_root / path).exists()]
        init_script = Path("scripts") / "init_project.py"
        if not keep_initializer and (self.repo_root / init_script).exists():
            deletes.append(init_script)
        logo = Path("assets") / "static" / "logo.svg"
        if logo_path is None and (self.repo_root / logo).exists():
            deletes.append(logo)
        return tuple(sorted(deletes))

    def _apply_replacement(self, planned: PlannedReplacement) -> None:
        target = self.repo_root / planned.path
        content = target.read_text()
        updated = content
        for replacement in planned.replacements:
            updated = updated.replace(replacement.old, replacement.new)
        if updated != content:
            target.write_text(_ensure_trailing_newline(updated))


def _ensure_trailing_newline(content: str) -> str:
    if not content:
        return ""
    return content if content.endswith("\n") else f"{content}\n"
