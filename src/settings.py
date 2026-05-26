import os
from pathlib import Path

from pydantic_settings import BaseSettings

_repo_root = Path(__file__).resolve().parent.parent
_env_default = _repo_root / ".env.default"
_env_file = _repo_root / f".env.{os.environ.get('APP_ENV', 'development')}"


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "cairn"
    APP_PORT: int = 8000

    DATABASE_URL_DEVELOPMENT: str = ""
    DATABASE_URL_TEST: str = ""
    DATABASE_URL_PRODUCTION: str = ""

    MEMORY_BACKEND: str = "faiss"
    MEMORY_STORE_PATH: str = "./memory_store"

    CACHE_BACKEND: str = "memory"
    REDIS_URL: str = "redis://localhost:6379/0"

    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-sonnet-4-6"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""

    model_config = {"env_file": [str(_env_default), str(_env_file)], "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def database_url(self) -> str:
        env_upper = self.APP_ENV.upper()
        attr_name = f"DATABASE_URL_{env_upper}"
        url = getattr(self, attr_name, "")
        if not url:
            raise ValueError(f"{attr_name} is not set for APP_ENV={self.APP_ENV}")
        return url


def get_settings() -> Settings:
    return Settings()
