from pathlib import Path

import pytest
import yaml


@pytest.mark.unit
def test_framework_loads():
    """Verify pytest discovers and runs tests."""
    assert True


@pytest.mark.unit
def test_markers_registered(pytestconfig):
    """Verify custom markers are registered in pyproject.toml."""
    marker_strings = pytestconfig.getini("markers")
    marker_names = {m.split(":")[0].strip() for m in marker_strings}
    assert "unit" in marker_names
    assert "integration" in marker_names
    assert "e2e" in marker_names
    assert "eval" in marker_names


@pytest.mark.unit
def test_src_package_importable():
    """Verify the src package can be imported."""
    import src

    assert src is not None


@pytest.mark.unit
def test_test_database_url_uses_settings(monkeypatch):
    from src.settings import reset_settings
    from tests.conftest import get_test_database_url

    monkeypatch.setenv("DATABASE_URL_TEST", "")
    monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setenv("POSTGRES_PORT", "55432")
    monkeypatch.setenv("POSTGRES_USER", "fixture_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fixture_password")
    monkeypatch.setenv("POSTGRES_DB_TEST", "fixture_test_db")
    reset_settings()

    try:
        assert (
            get_test_database_url()
            == "postgresql+asyncpg://fixture_user:fixture_password@127.0.0.1:55432/fixture_test_db"
        )
    finally:
        reset_settings()


@pytest.mark.unit
def test_docker_compose_database_port_is_configurable():
    compose_path = Path(__file__).parents[1] / "docker-compose.yml"
    compose = yaml.safe_load(compose_path.read_text())

    db_service = compose["services"]["db"]
    app_environment = compose["services"]["app"]["environment"]

    assert db_service["ports"] == ["${POSTGRES_PORT:-5432}:5432"]
    assert app_environment["POSTGRES_HOST"] == "db"
    assert app_environment["POSTGRES_PORT"] == 5432
    assert app_environment["DATABASE_URL_DEVELOPMENT"] == ""


@pytest.mark.unit
def test_ci_enforces_coverage_threshold():
    workflow_path = Path(__file__).parents[1] / ".github" / "workflows" / "test.yml"
    workflow = yaml.safe_load(workflow_path.read_text())
    steps = workflow["jobs"]["test"]["steps"]
    test_step = next(step for step in steps if step.get("name") == "Run tests with coverage")

    assert "--cov-fail-under=85" in test_step["run"]


@pytest.mark.unit
def test_makefile_coverage_target_enforces_threshold():
    makefile = (Path(__file__).parents[1] / "Makefile").read_text()

    assert "--cov-fail-under=85" in makefile


@pytest.mark.unit
def test_dependabot_updates_python_dependencies_and_actions():
    dependabot_path = Path(__file__).parents[1] / ".github" / "dependabot.yml"
    config = yaml.safe_load(dependabot_path.read_text())
    ecosystems = {entry["package-ecosystem"] for entry in config["updates"]}

    assert config["version"] == 2
    assert ecosystems == {"pip", "github-actions"}
    assert all(entry["schedule"]["interval"] == "weekly" for entry in config["updates"])


@pytest.mark.unit
def test_security_workflow_checks_lockfile_vulnerabilities_and_secrets():
    workflow_path = Path(__file__).parents[1] / ".github" / "workflows" / "security.yml"
    workflow = yaml.safe_load(workflow_path.read_text())
    jobs = workflow["jobs"]

    assert {"lockfile-freshness", "dependency-vulnerability-scan", "secret-scan"} <= set(jobs)
    lock_steps = jobs["lockfile-freshness"]["steps"]
    vulnerability_steps = jobs["dependency-vulnerability-scan"]["steps"]
    secret_steps = jobs["secret-scan"]["steps"]

    assert any(step.get("run") == "make lock-check" for step in lock_steps)
    assert any("pip-audit" in step.get("run", "") for step in vulnerability_steps)
    assert any(step.get("uses") == "gitleaks/gitleaks-action@v2" for step in secret_steps)


@pytest.mark.unit
def test_pre_commit_checks_for_private_keys():
    config_path = Path(__file__).parents[1] / ".pre-commit-config.yaml"
    config = yaml.safe_load(config_path.read_text())
    hook_ids = {hook["id"] for repo in config["repos"] for hook in repo["hooks"]}

    assert "detect-private-key" in hook_ids


@pytest.mark.unit
def test_makefile_lock_check_uses_poetry_lock_validation():
    makefile = (Path(__file__).parents[1] / "Makefile").read_text()

    assert "lock-check:" in makefile
    assert "poetry check --lock" in makefile
    assert "check: lock-check lint format-check test" in makefile
