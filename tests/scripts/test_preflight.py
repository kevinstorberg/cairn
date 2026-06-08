import json

from scripts.preflight import PreflightScript
from src.settings import Settings


def test_preflight_script_emits_json_report(tmp_path, monkeypatch, capsys):
    async def fake_run_preflight(preflight):
        return {
            "status": "pass",
            "mode": preflight.mode,
            "write_cutover": preflight.write_cutover,
            "expected_heads": list(preflight.expected_heads),
            "tables": list(preflight.tables),
            "database": {"alembic_versions": ["head"], "row_counts": {"projects": 2}},
            "errors": [],
        }

    monkeypatch.setattr("scripts.preflight.get_settings", lambda: Settings(APP_ENV="development"))
    monkeypatch.setattr("scripts.preflight.run_preflight", fake_run_preflight)
    output = tmp_path / "preflight.json"

    exit_code = PreflightScript().execute(
        [
            "--database-url",
            "postgresql://readonly@example/db",
            "--expected-head",
            "head",
            "--table",
            "projects",
            "--output",
            str(output),
        ]
    )

    stdout = json.loads(capsys.readouterr().out)
    saved = json.loads(output.read_text())
    assert exit_code == 0
    assert stdout == saved
    assert stdout["database"]["row_counts"] == {"projects": 2}


def test_preflight_script_uses_production_readonly_url(monkeypatch, capsys):
    captured = {}

    async def fake_run_preflight(preflight):
        captured["database_url"] = preflight.database_url
        return {"status": "pass", "errors": [], "database": {}}

    monkeypatch.setenv("PRODUCTION_DATABASE_URL_READONLY", "postgresql://readonly@example/prod")
    monkeypatch.setattr("scripts.preflight.get_settings", lambda: Settings(APP_ENV="development"))
    monkeypatch.setattr("scripts.preflight.run_preflight", fake_run_preflight)

    exit_code = PreflightScript().execute(["--production"])

    assert exit_code == 0
    assert captured["database_url"] == "postgresql://readonly@example/prod"
    assert json.loads(capsys.readouterr().out)["status"] == "pass"
