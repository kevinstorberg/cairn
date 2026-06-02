from db.migrations import utils


def test_sync_database_url_removes_asyncpg_driver():
    assert (
        utils.sync_database_url("postgresql+asyncpg://user:pass@localhost:5432/app")
        == "postgresql://user:pass@localhost:5432/app"
    )


def test_sync_database_url_leaves_sync_url_unchanged():
    url = "postgresql://user:pass@localhost:5432/app"

    assert utils.sync_database_url(url) == url


def test_import_model_modules_imports_public_modules_only(tmp_path, monkeypatch):
    imported_modules: list[str] = []

    (tmp_path / "public_model.py").write_text("MODEL = True\n")
    (tmp_path / "_private_model.py").write_text("MODEL = False\n")

    monkeypatch.setattr(utils.importlib, "import_module", imported_modules.append)

    utils.import_model_modules(tmp_path, package_name="example.models")

    assert imported_modules == ["example.models.public_model"]
