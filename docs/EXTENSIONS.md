# Extension Apps

Cairn extension apps are optional vertical applications mounted into the main
FastAPI process. They are disabled by default and are not imported unless enabled.

Source of truth:

- Config schema: [../config/models.py](../config/models.py)
- Default config: [../config/default.yaml](../config/default.yaml)
- Runtime env override: [../.env.default](../.env.default)
- Lazy import helper: [../src/extensions/lazy.py](../src/extensions/lazy.py)
- Registry and lifecycle hooks: [../src/extensions/registry.py](../src/extensions/registry.py)
- App wiring: [../src/app.py](../src/app.py)

## Convention

- Add the extension import path under `extensions.apps`.
- Enable it with `extensions.enabled` or `EXTENSIONS_ENABLED`.
- Implement `include_routes(app)` for HTTP/MCP/router mounting.
- Implement optional `startup(app)`, `shutdown(app)`, and `mount_static(app)`
  hooks only when the extension needs them.
- Keep app-specific settings, migrations, and domain code inside the extension;
  Cairn owns only the loading and lifecycle convention.

Disabled extensions must remain import-free. Enabled extensions fail startup if
their import path or lifecycle hooks fail.

