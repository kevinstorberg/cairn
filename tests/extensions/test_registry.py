import sys

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from config.models import DefaultConfig, ExtensionAppConfig, ExtensionsConfig
from src.extensions.registry import (
    ExtensionError,
    include_extension_routes,
    load_enabled_extensions,
    shutdown_extensions,
    startup_extensions,
)
from src.settings import Settings


def test_disabled_extension_is_not_imported(tmp_path, monkeypatch):
    module = tmp_path / "disabled_extension.py"
    module.write_text("raise RuntimeError('should not import')\n")
    monkeypatch.syspath_prepend(str(tmp_path))

    config = ExtensionsConfig(apps={"disabled": ExtensionAppConfig(import_path="disabled_extension:extension")})

    assert load_enabled_extensions(config, Settings(EXTENSIONS_ENABLED="")) == []
    assert "disabled_extension" not in sys.modules


def test_enabled_extension_with_bad_path_fails_with_extension_name():
    config = ExtensionsConfig(
        enabled=["missing"],
        apps={"missing": ExtensionAppConfig(import_path="missing_extension:extension")},
    )

    with pytest.raises(ExtensionError, match="Extension 'missing'.*missing_extension:extension"):
        load_enabled_extensions(config, Settings())


@pytest.mark.integration
async def test_extension_routes_and_lifecycle_hooks_run(tmp_path, monkeypatch):
    module = tmp_path / "feature_extension.py"
    module.write_text(
        "\n".join(
            [
                "events = []",
                "class Extension:",
                "    def include_routes(self, app):",
                "        events.append('routes')",
                "        @app.get('/extension/ping')",
                "        " + "async def ping():",
                "            return {'ok': True}",
                "    async def startup(self, app):",
                "        events.append('startup')",
                "    async def shutdown(self, app):",
                "        events.append('shutdown')",
                "extension = Extension()",
            ]
        )
        + "\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    config = ExtensionsConfig(
        enabled=["feature"],
        apps={"feature": ExtensionAppConfig(import_path="feature_extension:extension")},
    )
    extensions = load_enabled_extensions(config, Settings())
    app = FastAPI()

    include_extension_routes(app, extensions)
    await startup_extensions(app, extensions)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/extension/ping")

    await shutdown_extensions(app, extensions)

    imported = sys.modules["feature_extension"]
    assert response.json() == {"ok": True}
    assert imported.events == ["routes", "startup", "shutdown"]


@pytest.mark.integration
async def test_create_app_loads_enabled_extension_from_config(tmp_path, monkeypatch):
    module = tmp_path / "app_extension.py"
    module.write_text(
        "\n".join(
            [
                "class Extension:",
                "    def include_routes(self, app):",
                "        @app.get('/extension/status')",
                "        " + "async def status():",
                "            return {'extension': 'enabled'}",
                "extension = Extension()",
            ]
        )
        + "\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    import src.app as app_module

    config = DefaultConfig(
        extensions=ExtensionsConfig(
            enabled=["app"],
            apps={"app": ExtensionAppConfig(import_path="app_extension:extension")},
        )
    )
    monkeypatch.setattr(app_module, "load_default_config", lambda: config)
    monkeypatch.setattr(app_module, "get_settings", lambda: Settings(ANTHROPIC_API_KEY="key"))

    app = app_module.create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/extension/status")

    assert response.status_code == 200
    assert response.json() == {"extension": "enabled"}
