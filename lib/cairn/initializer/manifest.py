from __future__ import annotations

from dataclasses import dataclass

from lib.cairn.initializer.naming import ProjectIdentity


@dataclass(frozen=True)
class Replacement:
    old: str
    new: str


@dataclass(frozen=True)
class LocalRuntimeDefaults:
    app_port: int = 8000
    frontend_port: int = 5173
    postgres_port: int = 5432
    redis_port: int = 6379

    def __post_init__(self) -> None:
        for field_name, value in (
            ("app_port", self.app_port),
            ("frontend_port", self.frontend_port),
            ("postgres_port", self.postgres_port),
            ("redis_port", self.redis_port),
        ):
            if not 1 <= value <= 65535:
                raise ValueError(f"{field_name} must be between 1 and 65535")


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
        Replacement("TEMPLATE INFRASTRUCTURE", f"{identity.project_name} infrastructure"),
        Replacement("TEMPLATE EXAMPLE", f"{identity.project_name} example"),
        Replacement("template's own tests", f"{identity.project_name}'s tests"),
        Replacement("template's example routes", f"{identity.project_name}'s application routes"),
        Replacement("template itself", identity.project_name),
        Replacement("template WebSocket route", "application WebSocket route"),
        Replacement("template default", "generated default"),
        Replacement("template source", "application source"),
        Replacement("clone this template", f"clone {identity.project_name}"),
        Replacement("When you clone this template", f"When you develop {identity.project_name}"),
        Replacement("Template fixture", "Application fixture"),
        Replacement("Template utility", "Shared utility"),
        Replacement("Template infrastructure", "Application infrastructure"),
        Replacement("template utilities", "application utilities"),
        Replacement("template tests", "application tests"),
        Replacement("template fixtures", "application fixtures"),
        Replacement("unused by the template", "available to the application"),
        Replacement("unused by default in the template", "available by default in the application"),
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


def development_env_for(identity: ProjectIdentity, runtime: LocalRuntimeDefaults) -> str:
    return _env_for(identity, runtime, app_env="development")


def test_env_for(identity: ProjectIdentity, runtime: LocalRuntimeDefaults) -> str:
    return _env_for(identity, runtime, app_env="test")


def frontend_env_local_for(identity: ProjectIdentity, runtime: LocalRuntimeDefaults) -> str:
    return (
        f"VITE_API_BASE_URL=http://127.0.0.1:{runtime.app_port}\n"
        f"VITE_APP_NAME={identity.project_name}\n"
        "VITE_BASE_PATH=/ui/\n"
    )


def readme_for(identity: ProjectIdentity, *, has_logo: bool, runtime: LocalRuntimeDefaults) -> str:
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
        "Run `poetry install` first. Poetry creates the project virtual environment on first use, "
        "so install dependencies before running the renamed console command or Make targets.\n\n"
        "```sh\n"
        "poetry install\n"
        "npm --prefix frontend ci\n"
        "docker compose --env-file .env.development up -d db redis\n"
        "poetry run alembic upgrade head\n"
        f"poetry run uvicorn src.app:app --host 127.0.0.1 --port {runtime.app_port}\n"
        f"npm --prefix frontend run dev -- --host 127.0.0.1 --port {runtime.frontend_port}\n"
        "```\n"
        "\n"
        "Generate a resource after dependencies are installed:\n\n"
        "```sh\n"
        f"{identity.console_command} generate resource project name:string\n"
        "```\n"
        "\n"
        "If you need non-default local ports, pass them to `init` or `new` with "
        "`--app-port`, `--frontend-port`, `--postgres-port`, and `--redis-port` so "
        "`.env.development`, `.env.test`, and `frontend/.env.local` stay in sync.\n\n"
        "## Source Of Truth\n\n"
        f"- Application command: `{identity.console_command}` in `pyproject.toml` and `scripts/cli.py`\n"
        f"- Python utility namespace: `{identity.core_path}/`\n"
        "- Configuration defaults: `config/default.yaml` and `src/settings.py`\n"
        "- Local runtime env: `.env.development` and `.env.test`\n"
        "- Frontend runtime env: `frontend/.env.example` and `frontend/.env.local`\n"
        "- Resource generator: `scripts/generate.py`, `docs/GENERATOR.md`, and the generator package under the utility namespace\n"
        "- Database conventions: `db/`, `docs/REPOSITORIES_SERVICES.md`, and `db/PATTERNS.md`\n"
        "- API and error conventions: `src/api/errors.py`, `src/routers/`, and `docs/API_ERRORS.md`\n"
        "- Authorization conventions: `src/policies/` and `docs/AUTHORIZATION.md`\n"
        "- Jobs and diagnostics: `src/jobs/`, `src/diagnostics/`, `docs/JOBS.md`, and `docs/ADMIN_DEBUG.md`\n"
        "- Frontend conventions: `frontend/package.json`, `frontend/src/shared/`, and `docs/FRONTEND.md`\n"
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


def _env_for(identity: ProjectIdentity, runtime: LocalRuntimeDefaults, *, app_env: str) -> str:
    return (
        f"APP_ENV={app_env}\n"
        f"APP_NAME={identity.repo_name}\n"
        f"APP_PORT={runtime.app_port}\n"
        "DEBUG_ERRORS=false\n"
        "\n"
        "POSTGRES_HOST=localhost\n"
        "POSTGRES_IMAGE=pgvector/pgvector:pg16\n"
        f"POSTGRES_PORT={runtime.postgres_port}\n"
        f"POSTGRES_USER={identity.db_prefix}\n"
        f"POSTGRES_PASSWORD={identity.db_prefix}\n"
        f"POSTGRES_DB_DEVELOPMENT={identity.db_prefix}_dev\n"
        f"POSTGRES_DB_TEST={identity.db_prefix}_test\n"
        f"POSTGRES_DB_PRODUCTION={identity.db_prefix}_prod\n"
        "\n"
        "DATABASE_URL_DEVELOPMENT=\n"
        "DATABASE_URL_TEST=\n"
        "DATABASE_URL_PRODUCTION=\n"
        "\n"
        f"REDIS_URL=redis://localhost:{runtime.redis_port}/0\n"
        f"REDIS_PORT={runtime.redis_port}\n"
        "\n"
        "ANTHROPIC_API_KEY=\n"
        "OPENAI_API_KEY=\n"
        "\n"
        "SECRET_KEY=change-me-in-production-use-a-long-random-value\n"
        "JWT_ALGORITHM=HS256\n"
        "JWT_EXPIRATION_MINUTES=60\n"
        "TRUSTED_HOSTS=\n"
        "SECURE_HEADERS_HSTS_ENABLED=false\n"
        "\n"
        "AWS_REGION=us-east-1\n"
        "AWS_ACCESS_KEY_ID=\n"
        "AWS_SECRET_ACCESS_KEY=\n"
        "S3_BUCKET=\n"
        "\n"
        "PINECONE_API_KEY=\n"
        "PINECONE_INDEX_NAME=\n"
        "PINECONE_NAMESPACE=\n"
        "\n"
        "DOCUMENTDB_URI=\n"
        "\n"
        "EXTENSIONS_ENABLED=\n"
    )
