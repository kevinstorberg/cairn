import os
from functools import lru_cache

from pydantic_settings import BaseSettings

from lib.cairn.paths import get_repo_root

_repo_root = get_repo_root(__file__)
_env_default = _repo_root / ".env.default"
_env_file = _repo_root / f".env.{os.environ.get('APP_ENV', 'development')}"
_DATABASE_ENVS = {"development", "test", "production"}


class Settings(BaseSettings):
    """Secrets and runtime env vars only.

    Structural config (backend selection, model, pool sizes) lives in
    config/default.yaml and is accessed via config.loader.load_default_config().
    """

    APP_ENV: str = "development"
    APP_NAME: str = "cairn"
    APP_PORT: int = 8000
    DEBUG_ERRORS: bool = False

    POSTGRES_HOST: str = "localhost"
    POSTGRES_IMAGE: str = "pgvector/pgvector:pg16"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "cairn"
    POSTGRES_PASSWORD: str = "cairn"
    POSTGRES_DB_DEVELOPMENT: str = "cairn_dev"
    POSTGRES_DB_TEST: str = "cairn_test"
    POSTGRES_DB_PRODUCTION: str = "cairn_prod"

    DATABASE_URL_DEVELOPMENT: str = ""
    DATABASE_URL_TEST: str = ""
    DATABASE_URL_PRODUCTION: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PORT: int = 6379

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    SECRET_KEY: str = "change-me-in-production-use-a-long-random-value"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = ""
    PINECONE_NAMESPACE: str = ""

    DOCUMENTDB_URI: str = ""

    model_config = {"env_file": [str(_env_default), str(_env_file)], "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def database_url(self) -> str:
        return self.database_url_for()

    def database_url_for(self, env: str | None = None) -> str:
        env_name = (env or self.APP_ENV).lower()
        if env_name not in _DATABASE_ENVS:
            valid = ", ".join(sorted(_DATABASE_ENVS))
            raise ValueError(f"Unknown database environment '{env_name}'. Expected one of: {valid}")

        env_upper = env_name.upper()
        attr_name = f"DATABASE_URL_{env_upper}"
        url = getattr(self, attr_name, "")
        if url:
            return url

        database_attr = f"POSTGRES_DB_{env_upper}"
        required_components = {
            "POSTGRES_HOST": self.POSTGRES_HOST,
            "POSTGRES_PORT": self.POSTGRES_PORT,
            "POSTGRES_USER": self.POSTGRES_USER,
            "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
            database_attr: getattr(self, database_attr, ""),
        }
        missing = [name for name, value in required_components.items() if value in (None, "")]
        if missing:
            missing_fields = ", ".join(missing)
            raise ValueError(
                f"Cannot assemble database URL for environment '{env_name}'. "
                f"Set {attr_name} or provide required Postgres settings: {missing_fields}"
            )

        database_name = required_components[database_attr]
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{database_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def reset_settings():
    """Clear settings cache for testing or environment changes."""
    get_settings.cache_clear()
