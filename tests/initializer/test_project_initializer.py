from __future__ import annotations

from pathlib import Path

import pytest

from lib.cairn.initializer import ProjectIdentity, ProjectInitializer, copy_template, scan_forbidden_tokens
from scripts.cli import main as cairn_main


@pytest.mark.unit
def test_initializer_dry_run_reports_deterministic_plan_without_writing(tmp_path):
    repo = _minimal_template_repo(tmp_path)
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")

    initializer = ProjectInitializer(repo)
    plan = initializer.plan(identity)
    lines = plan.summary_lines()

    assert "replace: pyproject.toml" in lines
    assert "write: README.md" in lines
    assert "delete: docs/GENERATOR.md" in lines
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
    assert not (repo / "docs" / "GENERATOR.md").exists()
    assert not (repo / "assets" / "static" / "logo.svg").exists()
    assert 'name = "agent-smith"' in (repo / "pyproject.toml").read_text()
    assert 'agent-smith = "scripts.cli:main"' in (repo / "pyproject.toml").read_text()
    assert "InitProjectScript" not in (repo / "scripts" / "cli.py").read_text()
    assert 'prog="agent-smith"' in (repo / "scripts" / "cli.py").read_text()
    assert "from lib.agent_smith_core.paths import get_repo_root" in (repo / "src" / "settings.py").read_text()
    assert '"app": "agent-smith"' in (repo / "src" / "routers" / "health.py").read_text()
    assert scan_forbidden_tokens(repo) == ()


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

    status = cairn_main(["new", str(target), "--project-name", "Agent Smith", "--repo-root", str(source)])

    output = capsys.readouterr()

    assert status == 0
    assert "Initialized Agent Smith" in output.out
    assert (target / "lib" / "agent_smith_core").exists()
    assert not (target / "lib" / "cairn").exists()
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
    _write(repo / "docs" / "GENERATOR.md", "The `cairn` console command scaffolds resources.\n")
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
    return repo


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else f"{content}\n", encoding="utf-8")
