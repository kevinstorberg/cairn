import argparse
import sys
from pathlib import Path

from lib.cairn.initializer import LocalRuntimeDefaults, ProjectIdentity, ProjectInitializer, copy_template
from lib.cairn.paths import get_repo_root
from scripts.base import BaseScript


class InitProjectScript(BaseScript):
    name = "cairn"
    description = "Initialize a Cairn template as a named application."

    def configure_args(self, parser: argparse.ArgumentParser) -> None:
        subcommands = parser.add_subparsers(dest="command", required=True)
        self._add_common_options(subcommands.add_parser("init", help="Initialize this repository in place"))
        new = subcommands.add_parser("new", help="Create and initialize a new project directory")
        new.add_argument("target_dir", type=Path, help="directory to create")
        self._add_common_options(new)

    def run(self, args: argparse.Namespace) -> int:
        try:
            identity = ProjectIdentity.from_inputs(
                project_name=args.project_name,
                repo_name=args.repo_name,
                package_name=args.package_name,
                console_command=args.console_command,
                description=args.description,
                db_prefix=args.db_prefix,
            )
            runtime_defaults = LocalRuntimeDefaults(
                app_port=args.app_port,
                frontend_port=args.frontend_port,
                postgres_port=args.postgres_port,
                redis_port=args.redis_port,
            )
            logo_path = args.logo_path.resolve() if args.logo_path else None
            if args.command == "init":
                return self._init_repo(
                    repo_root=args.repo_root or get_repo_root(__file__),
                    identity=identity,
                    runtime_defaults=runtime_defaults,
                    dry_run=args.dry_run,
                    force=args.force,
                    keep_initializer=args.keep_initializer,
                    logo_path=logo_path,
                )
            if args.command == "new":
                source_root = args.repo_root or get_repo_root(__file__)
                target = args.target_dir.resolve()
                if not args.dry_run:
                    copy_template(source_root, target, force=args.force)
                else:
                    print(f"copy: {source_root} -> {target}")
                return self._init_repo(
                    repo_root=target if not args.dry_run else source_root,
                    identity=identity,
                    runtime_defaults=runtime_defaults,
                    dry_run=args.dry_run,
                    force=args.force,
                    keep_initializer=args.keep_initializer,
                    logo_path=logo_path,
                )
            raise ValueError(f"Unknown init command: {args.command}")
        except (FileExistsError, ValueError) as e:
            print(f"{args.command}: {e}", file=sys.stderr)
            return 1

    def _init_repo(
        self,
        *,
        repo_root: Path,
        identity: ProjectIdentity,
        runtime_defaults: LocalRuntimeDefaults,
        dry_run: bool,
        force: bool,
        keep_initializer: bool,
        logo_path: Path | None,
    ) -> int:
        initializer = ProjectInitializer(repo_root)
        plan = initializer.plan(
            identity,
            force=force,
            keep_initializer=keep_initializer,
            logo_path=logo_path,
            runtime_defaults=runtime_defaults,
        )
        label = "Planned" if dry_run else "Applied"
        for line in plan.summary_lines():
            if not dry_run and line.startswith("forbidden-current:"):
                continue
            print(f"{label}: {line}")
        if dry_run:
            return 0
        findings = initializer.apply(plan, logo_path=logo_path, keep_initializer=keep_initializer)
        print(f"Initialized {identity.project_name} in {repo_root}")
        print(f"Forbidden scan passed with {len(findings)} findings")
        print("Next steps:")
        print("  1. poetry install")
        print("  2. poetry run alembic upgrade head")
        print(f"  3. poetry run uvicorn src.app:app --host 127.0.0.1 --port {runtime_defaults.app_port}")
        return 0

    @staticmethod
    def _add_common_options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--project-name", required=True, help='display name, for example "Agent Smith"')
        parser.add_argument("--repo-name", default=None, help="repository/package distribution slug")
        parser.add_argument("--package-name", default=None, help="Python package stem, for example agent_smith")
        parser.add_argument("--console-command", default=None, help="console command name")
        parser.add_argument("--description", default=None, help="project description")
        parser.add_argument("--db-prefix", default=None, help="database name/user prefix")
        parser.add_argument("--app-port", type=int, default=8000, help="local API port")
        parser.add_argument("--frontend-port", type=int, default=5173, help="local Vite frontend port")
        parser.add_argument("--postgres-port", type=int, default=5432, help="local Postgres host port")
        parser.add_argument("--redis-port", type=int, default=6379, help="local Redis host port")
        parser.add_argument("--logo-path", type=Path, default=None, help="replacement SVG logo path")
        parser.add_argument("--dry-run", action="store_true", help="print planned changes without writing")
        parser.add_argument(
            "--force", action="store_true", help="allow initialization of non-empty or customized targets"
        )
        parser.add_argument(
            "--keep-initializer", action="store_true", help="retain initializer internals after rebranding"
        )
        parser.add_argument("--repo-root", type=Path, default=None, help="override source repository root")


def main() -> int:
    return InitProjectScript().execute()


if __name__ == "__main__":
    raise SystemExit(main())
