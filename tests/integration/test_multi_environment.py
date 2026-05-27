"""
Integration tests for multi-environment deployment.

Tests:
- .env file loading for different environments
- Config precedence (.env.default → .env.{APP_ENV})
- Environment-specific settings
- Database URL resolution
- Backend switching via environment
- Settings validation
"""

import os

import pytest


@pytest.mark.integration
class TestMultiEnvironment:
    @pytest.mark.asyncio
    async def test_settings_initialization(self):
        """Test Settings can be initialized."""
        from src.settings import Settings

        settings = Settings()
        assert settings is not None
        assert hasattr(settings, "APP_ENV")
        assert hasattr(settings, "database_url")

    @pytest.mark.asyncio
    async def test_default_environment_is_development(self):
        """Test default environment is development."""
        # Remove APP_ENV if set
        original = os.environ.get("APP_ENV")
        if "APP_ENV" in os.environ:
            del os.environ["APP_ENV"]

        try:
            from src.settings import Settings

            # Force reload
            settings = Settings()
            assert settings.APP_ENV == "development"
        finally:
            if original:
                os.environ["APP_ENV"] = original

    @pytest.mark.asyncio
    async def test_env_file_selection_development(self):
        """Test .env.development is loaded for development."""
        os.environ["APP_ENV"] = "development"

        try:
            from src.settings import Settings

            settings = Settings()
            assert settings.APP_ENV == "development"
            assert "cairn_dev" in settings.database_url
        finally:
            os.environ["APP_ENV"] = "test"

    @pytest.mark.asyncio
    async def test_env_file_selection_test(self):
        """Test .env.test is loaded for test."""
        os.environ["APP_ENV"] = "test"

        from src.settings import Settings

        settings = Settings()
        assert settings.APP_ENV == "test"
        assert "cairn_test" in settings.database_url

    @pytest.mark.asyncio
    async def test_env_file_selection_production(self):
        """Test .env.production is loaded for production."""
        # Set environment variable BEFORE importing
        original = os.environ.get("APP_ENV")
        os.environ["APP_ENV"] = "production"

        # Also set the production DB URL directly to test
        os.environ["DATABASE_URL_PRODUCTION"] = "postgresql+asyncpg://prod_user:prod_pass@production-db:5432/cairn_prod"

        try:
            # Force reload by reimporting
            import importlib
            import src.settings
            importlib.reload(src.settings)

            from src.settings import Settings

            settings = Settings()
            assert settings.APP_ENV == "production"
            # Production DB URL should be different
            assert "prod" in settings.database_url.lower() or "production" in settings.database_url.lower()
        finally:
            os.environ["APP_ENV"] = original or "test"
            os.environ.pop("DATABASE_URL_PRODUCTION", None)

    @pytest.mark.asyncio
    async def test_database_url_resolution(self):
        """Test database_url property resolves correctly."""
        from src.settings import Settings

        settings = Settings()
        url = settings.database_url

        assert url is not None
        assert url.startswith("postgresql")
        assert "asyncpg" in url

    @pytest.mark.asyncio
    async def test_database_url_missing_raises_error(self):
        """Test missing DATABASE_URL raises clear error."""
        os.environ["APP_ENV"] = "nonexistent"

        try:
            from src.settings import Settings

            settings = Settings()
            with pytest.raises(ValueError, match="DATABASE_URL_NONEXISTENT"):
                _ = settings.database_url
        finally:
            os.environ["APP_ENV"] = "test"

    @pytest.mark.asyncio
    async def test_env_file_precedence(self):
        """Test .env.{APP_ENV} overrides .env.default."""
        os.environ["APP_ENV"] = "development"

        try:
            from src.settings import Settings

            settings = Settings()

            # Development should override default
            # .env.development has specific DB credentials
            assert "localhost" in settings.DATABASE_URL_DEVELOPMENT or "127.0.0.1" in settings.DATABASE_URL_DEVELOPMENT
        finally:
            os.environ["APP_ENV"] = "test"

    @pytest.mark.asyncio
    async def test_backend_switching_via_env(self):
        """Test backend can be switched via environment variables."""
        from src.settings import Settings

        settings = Settings()

        # Check backends can be configured
        assert settings.MEMORY_BACKEND in ["faiss", "pgvector", "pinecone"]
        assert settings.CACHE_BACKEND in ["memory", "redis"]
        assert settings.LLM_PROVIDER in ["anthropic", "openai"]

    @pytest.mark.asyncio
    async def test_cache_backend_switching(self):
        """Test cache backend switches with environment."""
        original_backend = os.environ.get("CACHE_BACKEND")

        try:
            os.environ["CACHE_BACKEND"] = "redis"
            from cache.backends import get_cache_backend

            # Should create appropriate backend
            # (Can't easily test without Redis running, but factory should work)
            backend = get_cache_backend()
            assert backend is not None

            # Switch back
            os.environ["CACHE_BACKEND"] = "memory"
            backend = get_cache_backend()
            assert backend is not None

        finally:
            if original_backend:
                os.environ["CACHE_BACKEND"] = original_backend

    @pytest.mark.asyncio
    async def test_memory_backend_switching(self):
        """Test memory backend factory respects MEMORY_BACKEND env."""
        from memory.backends import get_backend

        original = os.environ.get("MEMORY_BACKEND")

        try:
            os.environ["MEMORY_BACKEND"] = "faiss"
            backend = get_backend()
            assert backend is not None
            # FAISS backend should be returned
            assert "FAISS" in type(backend).__name__

        finally:
            if original:
                os.environ["MEMORY_BACKEND"] = original

    @pytest.mark.asyncio
    async def test_llm_provider_switching(self):
        """Test LLM builder respects provider environment variable."""
        from src.agents.llm import build_llm

        # Anthropic
        llm = build_llm(provider="anthropic", model="claude-sonnet-4-6")
        assert "Anthropic" in type(llm).__name__

        # Note: OpenAI test would fail without API key, skip it

    @pytest.mark.asyncio
    async def test_settings_singleton(self):
        """Test get_settings returns consistent instance."""
        from src.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Should have same values
        assert settings1.APP_ENV == settings2.APP_ENV
        assert settings1.database_url == settings2.database_url

    @pytest.mark.asyncio
    async def test_environment_variables_override_files(self):
        """Test environment variables override .env files."""
        original = os.environ.get("APP_NAME")

        try:
            os.environ["APP_NAME"] = "custom-app-name"
            from src.settings import Settings

            settings = Settings()
            assert settings.APP_NAME == "custom-app-name"

        finally:
            if original:
                os.environ["APP_NAME"] = original
            else:
                os.environ.pop("APP_NAME", None)

    @pytest.mark.asyncio
    async def test_all_env_files_exist(self):
        """Test all expected .env files exist."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent

        assert (repo_root / ".env.default").exists()
        assert (repo_root / ".env.development").exists()
        assert (repo_root / ".env.test").exists()
        assert (repo_root / ".env.production").exists()

    @pytest.mark.asyncio
    async def test_production_settings_different_from_development(self):
        """Test production settings are properly distinct."""
        # Set prod DB URL
        os.environ["DATABASE_URL_PRODUCTION"] = "postgresql+asyncpg://prod_user:prod_pass@production-db:5432/cairn_prod"
        os.environ["APP_ENV"] = "production"

        try:
            import importlib
            import src.settings
            importlib.reload(src.settings)

            from src.settings import Settings

            prod_settings = Settings()

            os.environ["APP_ENV"] = "development"
            importlib.reload(src.settings)
            dev_settings = Settings()

            # Database URLs should be different
            assert prod_settings.database_url != dev_settings.database_url

            # Production should use more secure defaults
            # (in a real app, would verify JWT expiration is shorter, etc.)

        finally:
            os.environ["APP_ENV"] = "test"
            os.environ.pop("DATABASE_URL_PRODUCTION", None)

    @pytest.mark.asyncio
    async def test_config_yaml_loading(self):
        """Test YAML config loading works."""
        from config.loader import load_default_config

        config = load_default_config()

        assert config is not None
        assert hasattr(config, "llm")
        assert hasattr(config, "cache")
        assert hasattr(config, "memory")

    @pytest.mark.asyncio
    async def test_graph_config_loading(self):
        """Test graph-specific configs load and override defaults."""
        from config.loader import load_graph_config

        breakdown_config = load_graph_config("breakdown")
        categorize_config = load_graph_config("categorize")

        # Both should have base config
        assert breakdown_config.llm is not None
        assert categorize_config.llm is not None

        # Should have different tools
        assert breakdown_config.tools == ["get_todo", "create_subtask"]
        assert categorize_config.tools == ["get_todo", "update_todo"]

        # Cache TTL should be different
        assert breakdown_config.cache.default_ttl != categorize_config.cache.default_ttl
