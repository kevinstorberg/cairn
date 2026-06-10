import pytest

from lib.cairn.initializer import ProjectIdentity


@pytest.mark.unit
def test_project_identity_derives_defaults_from_display_name():
    identity = ProjectIdentity.from_inputs(project_name="Agent Smith")

    assert identity.project_name == "Agent Smith"
    assert identity.repo_name == "agent-smith"
    assert identity.package_name == "agent_smith"
    assert identity.console_command == "agent-smith"
    assert identity.db_prefix == "agent_smith"
    assert identity.core_package == "agent_smith_core"


@pytest.mark.unit
def test_project_identity_validates_names():
    with pytest.raises(ValueError, match="package_name"):
        ProjectIdentity.from_inputs(project_name="Agent Smith", package_name="Agent-Smith")

    with pytest.raises(ValueError, match="repo_name"):
        ProjectIdentity.from_inputs(project_name="Agent Smith", repo_name="Agent Smith")

    with pytest.raises(ValueError, match="project_name"):
        ProjectIdentity.from_inputs(project_name=" ")
