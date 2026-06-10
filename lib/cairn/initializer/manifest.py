from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lib.cairn.initializer.naming import ProjectIdentity


@dataclass(frozen=True)
class Replacement:
    old: str
    new: str


TEMPLATE_DOCS = (
    Path("db") / "PATTERNS.md",
    Path("docs") / "ADMIN_DEBUG.md",
    Path("docs") / "API_ERRORS.md",
    Path("docs") / "AUTHORIZATION.md",
    Path("docs") / "BACKENDS.md",
    Path("docs") / "DEPLOYMENT.md",
    Path("docs") / "DOCTOR.md",
    Path("docs") / "EXTENSIONS.md",
    Path("docs") / "FRONTEND.md",
    Path("docs") / "GENERATOR.md",
    Path("docs") / "GRAPHS.md",
    Path("docs") / "JOBS.md",
    Path("docs") / "PREFLIGHT.md",
    Path("docs") / "REPOSITORIES_SERVICES.md",
    Path("docs") / "SECURITY_AUTOMATION.md",
    Path("docs") / "TESTING.md",
    Path("docs") / "TOOLS.md",
)


def replacements_for(identity: ProjectIdentity) -> tuple[Replacement, ...]:
    db = identity.db_prefix
    return (
        Replacement("lib/cairn", identity.core_path),
        Replacement("lib.cairn", f"lib.{identity.core_package}"),
        Replacement(
            "from scripts.cli import main as cairn_main",
            f"from scripts.cli import main as {identity.package_name}_main",
        ),
        Replacement(
            'status = cairn_main(["generate", "resource", "project", "name:string", "--dry-run", "--repo-root", str(tmp_path)])',
            (
                f"status = {identity.package_name}_main(\n"
                '        ["generate", "resource", "project", "name:string", "--dry-run", "--repo-root", str(tmp_path)]\n'
                "    )"
            ),
        ),
        Replacement("cairn_main(", f"{identity.package_name}_main("),
        Replacement("test_cairn_", f"test_{identity.package_name}_"),
        Replacement("conventional_cairn_layers", f"conventional_{identity.package_name}_layers"),
        Replacement("exposes_cairn_console_command", f"exposes_{identity.package_name}_console_command"),
        Replacement('name = "cairn"', f'name = "{identity.repo_name}"'),
        Replacement('"name": "cairn-frontend"', f'"name": "{identity.repo_name}-frontend"'),
        Replacement(
            'description = "Reusable FastAPI framework for agentic Python applications with LangGraph"',
            f'description = "{identity.description}"',
        ),
        Replacement('cairn = "scripts.cli:main"', f'{identity.console_command} = "scripts.cli:main"'),
        Replacement('prog="cairn"', f'prog="{identity.console_command}"'),
        Replacement("cairn.authToken", f"{identity.package_name}.authToken"),
        Replacement("Generate Cairn application artifacts", f"Generate {identity.project_name} application artifacts"),
        Replacement("Generate Cairn application resources", f"Generate {identity.project_name} application resources"),
        Replacement("managed by Cairn base models", f"managed by {identity.project_name} base models"),
        Replacement("Generated Cairn resource scaffold.", f"Generated {identity.project_name} resource scaffold."),
        Replacement("FastAPI template", f"{identity.project_name} application"),
        Replacement("template users", f"{identity.project_name} developers"),
        Replacement("TEMPLATE INFRASTRUCTURE: ", ""),
        Replacement("Cairn Logo", f"{identity.project_name} Logo"),
        Replacement("Cairn", identity.project_name),
        Replacement("APP_NAME=cairn", f"APP_NAME={identity.repo_name}"),
        Replacement('APP_NAME: str = "cairn"', f'APP_NAME: str = "{identity.repo_name}"'),
        Replacement("POSTGRES_USER=cairn", f"POSTGRES_USER={identity.db_prefix}"),
        Replacement("POSTGRES_PASSWORD=cairn", f"POSTGRES_PASSWORD={identity.db_prefix}"),
        Replacement("POSTGRES_DB_DEVELOPMENT=cairn_dev", f"POSTGRES_DB_DEVELOPMENT={db}_dev"),
        Replacement("POSTGRES_DB_TEST=cairn_test", f"POSTGRES_DB_TEST={db}_test"),
        Replacement("POSTGRES_DB_PRODUCTION=cairn_prod", f"POSTGRES_DB_PRODUCTION={db}_prod"),
        Replacement("POSTGRES_USER: cairn", f"POSTGRES_USER: {identity.db_prefix}"),
        Replacement("POSTGRES_PASSWORD: cairn", f"POSTGRES_PASSWORD: {identity.db_prefix}"),
        Replacement("POSTGRES_DB: cairn_test", f"POSTGRES_DB: {db}_test"),
        Replacement("POSTGRES_DB_DEVELOPMENT: cairn_dev", f"POSTGRES_DB_DEVELOPMENT: {db}_dev"),
        Replacement("POSTGRES_USER:-cairn", f"POSTGRES_USER:-{identity.db_prefix}"),
        Replacement("POSTGRES_PASSWORD:-cairn", f"POSTGRES_PASSWORD:-{identity.db_prefix}"),
        Replacement("POSTGRES_DB_DEVELOPMENT:-cairn_dev", f"POSTGRES_DB_DEVELOPMENT:-{db}_dev"),
        Replacement("pg_isready -U cairn", f"pg_isready -U {identity.db_prefix}"),
        Replacement(
            "DATABASE_URL_TEST: postgresql+asyncpg://cairn:cairn@localhost:5432/cairn_test",
            f"DATABASE_URL_TEST: postgresql+asyncpg://{identity.db_prefix}:{identity.db_prefix}@localhost:5432/{db}_test",
        ),
        Replacement(
            'assert s.database_url_for("test") == "postgresql+asyncpg://cairn:cairn@localhost:55432/cairn_test"',
            (
                'assert s.database_url_for("test") == (\n'
                f'            "postgresql+asyncpg://{identity.db_prefix}:{identity.db_prefix}@localhost:55432/{db}_test"\n'
                "        )"
            ),
        ),
        Replacement(
            "postgresql+asyncpg://cairn:cairn@localhost:55432/",
            f"postgresql+asyncpg://{identity.db_prefix}:{identity.db_prefix}@localhost:55432/",
        ),
        Replacement('POSTGRES_USER="cairn"', f'POSTGRES_USER="{identity.db_prefix}"'),
        Replacement('POSTGRES_PASSWORD="cairn"', f'POSTGRES_PASSWORD="{identity.db_prefix}"'),
        Replacement('POSTGRES_USER: str = "cairn"', f'POSTGRES_USER: str = "{identity.db_prefix}"'),
        Replacement('POSTGRES_PASSWORD: str = "cairn"', f'POSTGRES_PASSWORD: str = "{identity.db_prefix}"'),
        Replacement('POSTGRES_DB_DEVELOPMENT: str = "cairn_dev"', f'POSTGRES_DB_DEVELOPMENT: str = "{db}_dev"'),
        Replacement('POSTGRES_DB_TEST: str = "cairn_test"', f'POSTGRES_DB_TEST: str = "{db}_test"'),
        Replacement('POSTGRES_DB_PRODUCTION: str = "cairn_prod"', f'POSTGRES_DB_PRODUCTION: str = "{db}_prod"'),
        Replacement("cairn_dev", f"{db}_dev"),
        Replacement("cairn_test", f"{db}_test"),
        Replacement("cairn_prod", f"{db}_prod"),
        Replacement("cairn_memory", f"{db}_memory"),
        Replacement("cairn_job_runs", f"{db}_job_runs"),
        Replacement('f"cairn:{key}"', f'f"{identity.package_name}:{{key}}"'),
        Replacement("cairn:diagnostics:cache", f"{identity.package_name}:diagnostics:cache"),
        Replacement("cairn.audit", f"{identity.package_name}.audit"),
        Replacement("cairn_fake", f"{identity.package_name}_fake"),
        Replacement("cairn-app", f"{identity.repo_name}-app"),
        Replacement("addgroup --system cairn", f"addgroup --system {identity.package_name}"),
        Replacement(
            "adduser --system --ingroup cairn --home /app cairn",
            f"adduser --system --ingroup {identity.package_name} --home /app {identity.package_name}",
        ),
        Replacement("chown -R cairn:cairn", f"chown -R {identity.package_name}:{identity.package_name}"),
        Replacement("USER cairn", f"USER {identity.package_name}"),
        Replacement('pkg_version("cairn")', f'pkg_version("{identity.repo_name}")'),
        Replacement('"app": "cairn"', f'"app": "{identity.repo_name}"'),
        Replacement('logger = get_logger("cairn-test")', f'logger = get_logger("{identity.package_name}-test")'),
        Replacement('assert data["app"] == "cairn"', f'assert data["app"] == "{identity.repo_name}"'),
        Replacement('assert s.APP_NAME == "cairn"', f'assert s.APP_NAME == "{identity.repo_name}"'),
        Replacement('"cairn"', f'"{identity.repo_name}"'),
        Replacement("'cairn'", f"'{identity.repo_name}'"),
        Replacement("`cairn`", f"`{identity.console_command}`"),
        Replacement("cairn ", f"{identity.console_command} "),
    )


def readme_for(identity: ProjectIdentity, *, has_logo: bool) -> str:
    logo = (
        f'<img src="assets/static/logo.svg" alt="{identity.project_name}" width="120" align="left" '
        'style="margin-right: 20px; margin-bottom: 10px;"/>\n\n'
        if has_logo
        else ""
    )
    return (
        f"{logo}# {identity.repo_name}\n\n"
        f"{identity.description}\n\n"
        "## Quick Start\n\n"
        "```sh\n"
        "poetry install\n"
        "poetry run alembic upgrade head\n"
        "poetry run uvicorn src.app:app --reload\n"
        "```\n"
    )


def cli_for(identity: ProjectIdentity) -> str:
    return (
        "import argparse\n"
        "import sys\n\n"
        "from scripts.generate import GenerateScript\n\n\n"
        "def main(argv: list[str] | None = None) -> int:\n"
        f'    parser = argparse.ArgumentParser(prog="{identity.console_command}")\n'
        '    subcommands = parser.add_subparsers(dest="command", required=True)\n'
        f'    subcommands.add_parser("generate", help="Generate {identity.project_name} application artifacts", add_help=False)\n'
        "    args, remainder = parser.parse_known_args(argv if argv is not None else sys.argv[1:])\n\n"
        '    if args.command == "generate":\n'
        "        return GenerateScript().execute(remainder)\n"
        '    raise ValueError(f"Unknown command: {args.command}")\n\n\n'
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n"
    )
