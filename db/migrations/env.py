import importlib
import pkgutil
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from db.base import Base

# Auto-import all model modules so Base.metadata is populated for autogenerate
_models_dir = Path(__file__).resolve().parent.parent / "models"
if _models_dir.exists():
    for _, module_name, _ in pkgutil.iter_modules([str(_models_dir)]):
        if not module_name.startswith("_"):
            importlib.import_module(f"db.models.{module_name}")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    from src.settings import get_settings

    url = get_settings().database_url
    return url.replace("+asyncpg", "")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
