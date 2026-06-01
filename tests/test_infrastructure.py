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
