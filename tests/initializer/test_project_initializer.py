from __future__ import annotations

from pathlib import Path

import pytest

from lib.cairn.initializer import (
    LocalRuntimeDefaults,
    ProjectIdentity,
    ProjectInitializer,
    copy_template,
    scan_forbidden_tokens,
)
from scripts.cli import main as cairn_main


@pytest.mark.unit
def test_initializer_dry_run_reports_deterministic_plan_without_writing(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")

    initializer = ProjectInitializer(repo)
    plan = initializer.plan(identity)
    lines = plan.summary_lines()

    assert "replace: pyproject.toml" in lines
    assert "replace: docs/GENERATOR.md" in lines
    assert "replace: db/PATTERNS.md" in lines
    assert "write: README.md" in lines
    assert "write: .env.development" in lines
    assert "write: .env.test" in lines
    assert "write: frontend/.env.local" in lines
    assert "delete: docs/GENERATOR.md" not in lines
    assert "delete: assets/static/logo.svg" in lines
    assert "move: lib/cairn -> lib/agent_smith_core" in lines
    assert (repo / "lib" / "cairn").exists()
    assert not (repo / "lib" / "agent_smith_core").exists()


@pytest.mark.unit
def test_initializer_rewrites_identity_and_removes_forbidden_branding(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")
    initializer = ProjectInitializer(repo)

    plan = initializer.plan(identity)
    findings = initializer.apply(plan)

    assert findings == ()
    assert not (repo / "lib" / "cairn").exists()
    assert (repo / "lib" / "agent_smith_core" / "paths.py").exists()
    assert not (repo / "lib" / "agent_smith_core" / "initializer").exists()
    assert not (repo / "scripts" / "init_project.py").exists()
    assert not (repo / "tests" / "initializer").exists()
    assert (repo / "docs" / "GENERATOR.md").exists()
    assert (repo / "db" / "PATTERNS.md").exists()
    assert not (repo / "assets" / "static" / "logo.svg").exists()
    assert 'name = "agent-smith"' in (repo / "pyproject.toml").read_text()
    assert 'agent-smith = "scripts.cli:main"' in (repo / "pyproject.toml").read_text()
    assert "InitProjectScript" not in (repo / "scripts" / "cli.py").read_text()
    assert 'prog="agent-smith"' in (repo / "scripts" / "cli.py").read_text()
    assert "from lib.agent_smith_core.paths import get_repo_root" in (repo / "src" / "settings.py").read_text()
    assert '"app": "agent-smith"' in (repo / "src" / "routers" / "health.py").read_text()
    assert "poetry install" in (repo / "README.md").read_text()
    assert "agent-smith generate resource project name:string" in (repo / "README.md").read_text()
    assert "docs/GENERATOR.md" in (repo / "README.md").read_text()
    generator_doc = (repo / "docs" / "GENERATOR.md").read_text()
    assert "The `agent-smith` console command scaffolds resources" in generator_doc
    assert "lib/agent_smith_core/generator/" in generator_doc
    assert "application source" in (repo / "db" / "PATTERNS.md").read_text()
    assert scan_forbidden_tokens(repo) == ()


@pytest.mark.unit
def test_initializer_writes_local_runtime_env_files(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    identity = ProjectIdentity.from_inputs(project_name="Launch Pad")
    runtime = LocalRuntimeDefaults(app_port=18111, frontend_port=15191, postgres_port=55441, redis_port=56391)

    plan = ProjectInitializer(repo).plan(identity, runtime_defaults=runtime)
    ProjectInitializer(repo).apply(plan)

    development_env = (repo / ".env.development").read_text()
    test_env = (repo / ".env.test").read_text()
    frontend_env = (repo / "frontend" / ".env.local").read_text()

    assert "APP_ENV=development" in development_env
    assert "APP_ENV=test" in test_env
    assert "APP_PORT=18111" in development_env
    assert "APP_PORT=18111" in test_env
    assert "POSTGRES_PORT=55441" in development_env
    assert "POSTGRES_PORT=55441" in test_env
    assert "POSTGRES_DB_TEST=launch_pad_test" in test_env
    assert "REDIS_URL=redis://localhost:56391/0" in development_env
    assert "REDIS_URL=redis://localhost:56391/0" in test_env
    assert "VITE_API_BASE_URL=http://127.0.0.1:18111" in frontend_env
    assert "VITE_APP_NAME=Launch Pad" in frontend_env
    assert "VITE_BASE_PATH=/ui/" in frontend_env


@pytest.mark.unit
def test_initializer_rejects_already_initialized_repo_without_force(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    (repo / "pyproject.toml").write_text('name = "agent-smith"\n', encoding="utf-8")
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")

    with pytest.raises(ValueError, match="already initialized"):
        ProjectInitializer(repo).plan(identity)


@pytest.mark.unit
def test_initializer_rejects_existing_namespace_target(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    (repo / "lib" / "agent_smith_core").mkdir(parents=True)
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")

    with pytest.raises(FileExistsError, match="agent_smith_core"):
        ProjectInitializer(repo).plan(identity, force=True)


@pytest.mark.unit
def test_initializer_keep_initializer_allows_retained_initializer_paths(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")
    initializer = ProjectInitializer(repo)

    plan = initializer.plan(identity, keep_initializer=True)
    findings = initializer.apply(plan, keep_initializer=True)

    assert findings == ()
    assert (repo / "lib" / "agent_smith_core" / "initializer").exists()
    assert (repo / "tests" / "initializer").exists()
    assert (repo / "scripts" / "init_project.py").exists()


@pytest.mark.unit
def test_copy_template_excludes_local_artifacts(tmp_path):
    source = _minimal_template_repo(tmp_path / "source")
    (source / ".git").mkdir()
    (source / ".env.development").write_text("local=true\n", encoding="utf-8")
    (source / "frontend" / "node_modules").mkdir(parents=True)
    (source / "frontend" / "node_modules" / "package").write_text("ignored\n", encoding="utf-8")
    (source / "src" / "__pycache__").mkdir()
    (source / "src" / "__pycache__" / "settings.pyc").write_bytes(b"ignored")
    target = tmp_path / "target"

    copy_template(source, target)

    assert (target / "pyproject.toml").exists()
    assert not (target / ".git").exists()
    assert not (target / ".env.development").exists()
    assert not (target / "frontend" / "node_modules").exists()
    assert not (target / "src" / "__pycache__").exists()


@pytest.mark.unit
def test_cairn_cli_dispatches_init_dry_run(tmp_path, capsys):
    repo = _minimal_template_repo(tmp_path)

    status = cairn_main(["init", "--project-name", "Agent Smith", "--dry-run", "--repo-root", str(repo)])

    output = capsys.readouterr()

    assert status == 0
    assert "Planned: move: lib/cairn -> lib/agent_smith_core" in output.out
    assert (repo / "lib" / "cairn").exists()


@pytest.mark.unit
def test_cairn_cli_new_creates_initialized_project(tmp_path, capsys):
    source = _minimal_template_repo(tmp_path / "source")
    target = tmp_path / "agent-smith"

    status = cairn_main(
        [
            "new",
            str(target),
            "--project-name",
            "Agent Smith",
            "--app-port",
            "18111",
            "--frontend-port",
            "15191",
            "--postgres-port",
            "55441",
            "--redis-port",
            "56391",
            "--repo-root",
            str(source),
        ]
    )

    output = capsys.readouterr()

    assert status == 0
    assert "Initialized Agent Smith" in output.out
    assert "1. poetry install" in output.out
    assert (target / "lib" / "agent_smith_core").exists()
    assert not (target / "lib" / "cairn").exists()
    assert "POSTGRES_PORT=55441" in (target / ".env.test").read_text()
    assert "VITE_API_BASE_URL=http://127.0.0.1:18111" in (target / "frontend" / ".env.local").read_text()
    assert scan_forbidden_tokens(target) == ()
    assert (source / "lib" / "cairn").exists()


@pytest.mark.unit
def test_current_repo_plan_includes_known_identity_surfaces():
    repo = Path(__file__).parents[2]
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")

    plan = ProjectInitializer(repo).plan(identity)
    paths = {replacement.path for replacement in plan.replacements}

    assert Path("pyproject.toml") in paths
    assert Path(".env.default") in paths
    assert Path("Dockerfile") in paths
    assert Path("docker-compose.yml") in paths
    assert Path(".github") / "workflows" / "test.yml" in paths
    assert Path("src") / "settings.py" in paths
    assert Path("src") / "routers" / "health.py" in paths
    assert Path("scripts") / "cli.py" in paths
    assert Path("scripts") / "generate.py" in paths
    assert Path("docs") / "GENERATOR.md" in paths
    assert Path("docs") / "FRONTEND.md" in paths


def _minimal_template_repo(tmp_path: Path) -> Path:
    repo = tmp_path
    _write(
        repo / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "cairn"',
                'description = "Reusable FastAPI framework for agentic Python applications with LangGraph"',
                "[project.scripts]",
                'cairn = "scripts.cli:main"',
            ]
        ),
    )
    _write(repo / "README.md", "# Cairn\n\nFastAPI template for apps.\n")
    _write(
        repo / "docs" / "GENERATOR.md",
        "The `cairn` console command scaffolds resources from lib/cairn/generator/.\n",
    )
    _write(repo / "docs" / "FRONTEND.md", "Cairn frontend docs mention frontend/.env.example.\n")
    _write(repo / "db" / "PATTERNS.md", "Patterns from the template source.\n")
    _write(repo / "assets" / "static" / "logo.svg", "<svg><title>Cairn Logo</title></svg>\n")
    _write(
        repo / ".env.default",
        "\n".join(
            [
                "APP_NAME=cairn",
                "POSTGRES_USER=cairn",
                "POSTGRES_PASSWORD=cairn",
                "POSTGRES_DB_DEVELOPMENT=cairn_dev",
                "POSTGRES_DB_TEST=cairn_test",
                "POSTGRES_DB_PRODUCTION=cairn_prod",
            ]
        ),
    )
    _write(
        repo / "Dockerfile",
        "\n".join(
            [
                "RUN addgroup --system cairn && \\",
                "    adduser --system --ingroup cairn --home /app cairn",
                "RUN chown -R cairn:cairn /app",
                "USER cairn",
            ]
        ),
    )
    _write(
        repo / "docker-compose.yml",
        "\n".join(
            [
                "POSTGRES_USER: cairn",
                "POSTGRES_PASSWORD: cairn",
                "POSTGRES_DB: ${POSTGRES_DB_DEVELOPMENT:-cairn_dev}",
                'test: ["CMD-SHELL", "pg_isready -U cairn"]',
            ]
        ),
    )
    _write(
        repo / ".github" / "workflows" / "test.yml",
        "DATABASE_URL_TEST: postgresql+asyncpg://cairn:cairn@localhost:5432/cairn_test\n",
    )
    _write(repo / "lib" / "cairn" / "__init__.py", '"""Cairn template utilities."""\n')
    _write(
        repo / "lib" / "cairn" / "initializer" / "__init__.py", "from lib.cairn.initializer import ProjectIdentity\n"
    )
    _write(
        repo / "lib" / "cairn" / "paths.py",
        "def get_repo_root(_path):\n    return None\n",
    )
    _write(
        repo / "src" / "settings.py",
        "\n".join(
            [
                "from lib.cairn.paths import get_repo_root",
                'APP_NAME: str = "cairn"',
                'POSTGRES_USER: str = "cairn"',
                'POSTGRES_PASSWORD: str = "cairn"',
                'POSTGRES_DB_TEST: str = "cairn_test"',
            ]
        ),
    )
    _write(
        repo / "src" / "routers" / "health.py",
        "\n".join(['_VERSION = pkg_version("cairn")', 'return {"app": "cairn"}']),
    )
    _write(
        repo / "scripts" / "cli.py",
        'parser = argparse.ArgumentParser(prog="cairn")\n',
    )
    _write(repo / "scripts" / "init_project.py", "from lib.cairn.initializer import ProjectIdentity\n")
    _write(repo / "tests" / "initializer" / "test_init.py", "from lib.cairn.initializer import ProjectIdentity\n")
    _write(
        repo / "scripts" / "generate.py",
        'description = "Generate Cairn application resources."\n',
    )
    _write(
        repo / "tests" / "scripts" / "test_generate.py",
        "\n".join(
            [
                "from scripts.cli import main as cairn_main",
                "def test_cairn_cli_dispatches_generate_resource():",
                "    status = cairn_main(['generate'])",
                "    assert \"generate: Field 'id' is managed by Cairn base models\"",
            ]
        ),
    )
    _write(
        repo / "tests" / "conftest.py",
        "\n".join(
            [
                '"""Pytest fixtures for template users.',
                "NOTE: These fixtures are intentionally unused by the template's own tests.",
                "When you clone this template and build your application, USE THESE FIXTURES.",
                '"""',
            ]
        ),
    )
    return repo


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else f"{content}\n", encoding="utf-8")
