import pytest


@pytest.mark.unit
class TestDeepMerge:
    def test_merges_nested_dicts(self):
        from config.loader import _deep_merge

        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"c": 99}, "e": 5}
        _deep_merge(base, override)
        assert base == {"a": {"b": 1, "c": 99}, "d": 3, "e": 5}

    def test_override_replaces_non_dict(self):
        from config.loader import _deep_merge

        base = {"a": {"b": 1}}
        override = {"a": "replaced"}
        _deep_merge(base, override)
        assert base == {"a": "replaced"}

    def test_empty_override_noop(self):
        from config.loader import _deep_merge

        base = {"a": 1}
        _deep_merge(base, {})
        assert base == {"a": 1}

    def test_adds_new_nested_keys(self):
        from config.loader import _deep_merge

        base = {"a": {"b": 1}}
        override = {"a": {"c": 2, "d": {"e": 3}}}
        _deep_merge(base, override)
        assert base == {"a": {"b": 1, "c": 2, "d": {"e": 3}}}


@pytest.mark.unit
class TestLoadDefaultConfig:
    def test_loads_successfully(self):
        from config.loader import load_default_config

        config = load_default_config()
        assert config.llm.provider is not None
        assert config.llm.model is not None
        assert config.llm.max_tokens > 0

    def test_caching_returns_same_instance(self):
        from config.loader import load_default_config

        c1 = load_default_config()
        c2 = load_default_config()
        assert c1 is c2


@pytest.mark.unit
class TestLoadGraphConfig:
    def test_nonexistent_graph_returns_defaults(self):
        from config.loader import load_graph_config

        config = load_graph_config("nonexistent_graph_xyz")
        assert config.llm is not None
        assert config.tools == []


@pytest.mark.unit
class TestSettings:
    def test_loads_app_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("DATABASE_URL_TEST", "postgresql+asyncpg://localhost/cairn_test")
        from src.settings import Settings

        s = Settings()
        assert s.APP_ENV == "test"

    def test_database_url_property(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("DATABASE_URL_TEST", "postgresql+asyncpg://localhost/cairn_test")
        from src.settings import Settings

        s = Settings()
        assert s.database_url == "postgresql+asyncpg://localhost/cairn_test"

    def test_missing_database_url_raises(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("DATABASE_URL_PRODUCTION", raising=False)
        from src.settings import Settings

        s = Settings()
        with pytest.raises(ValueError, match="DATABASE_URL_PRODUCTION"):
            _ = s.database_url
