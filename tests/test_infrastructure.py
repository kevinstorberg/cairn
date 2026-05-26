import pytest


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
