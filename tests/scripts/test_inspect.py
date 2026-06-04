import json

from scripts.inspect import InspectScript
from src.diagnostics.models import DiagnosticResult


def test_inspect_script_outputs_json_for_config(monkeypatch, capsys):
    monkeypatch.setattr(
        "scripts.inspect.inspect_config",
        lambda **kwargs: DiagnosticResult(name="config", status="pass", details={"ok": True}),
    )

    exit_code = InspectScript().execute(["config"])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["name"] == "config"
    assert output["details"] == {"ok": True}
