import subprocess
from pathlib import Path

import pytest

from src.diagnostics.inspectors import inspect_migrations, inspect_registries
from src.jobs.base import BaseJob
from src.jobs.registry import clear_registered_jobs, register_job
from src.services.base import SERVICE_REGISTRY
from src.tools import TOOL_FACTORY, register_tool


class DiagnosticJob(BaseJob):
    name = "diagnostic_job"

    async def execute(self):
        return None


class DiagnosticService:
    pass


def build_diagnostic_job() -> BaseJob:
    return DiagnosticJob()


@pytest.fixture(autouse=True)
def clean_registries():
    SERVICE_REGISTRY.pop("diagnostic", None)
    TOOL_FACTORY.pop("diagnostic_tool", None)
    clear_registered_jobs()
    yield
    SERVICE_REGISTRY.pop("diagnostic", None)
    TOOL_FACTORY.pop("diagnostic_tool", None)
    clear_registered_jobs()


def test_registry_inspector_reports_services_tools_and_jobs():
    SERVICE_REGISTRY["diagnostic"] = DiagnosticService
    register_tool("diagnostic_tool")(lambda context: None)
    register_job(name="diagnostic_job")(build_diagnostic_job)

    result = inspect_registries()

    assert result.status == "pass"
    assert "diagnostic" in result.details["services"]
    assert "diagnostic_tool" in result.details["tools"]
    assert "diagnostic_job" in result.details["jobs"]


def test_migration_inspector_reports_current_and_heads():
    def runner(command, cwd):
        assert cwd == Path("/repo")
        if command[-1] == "current":
            return subprocess.CompletedProcess(command, returncode=0, stdout="abc123\n", stderr="")
        return subprocess.CompletedProcess(command, returncode=0, stdout="head456\n", stderr="")

    result = inspect_migrations(repo_root=Path("/repo"), command_runner=runner)

    assert result.status == "pass"
    assert result.details["current"]["stdout"] == "abc123"
    assert result.details["heads"]["stdout"] == "head456"


def test_migration_inspector_reports_command_failure():
    def runner(command, cwd):
        return subprocess.CompletedProcess(command, returncode=1, stdout="", stderr="db unavailable")

    result = inspect_migrations(repo_root=Path("/repo"), command_runner=runner)

    assert result.status == "fail"
    assert result.details["current"]["stderr"] == "db unavailable"
