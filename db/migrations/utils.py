import importlib
import pkgutil
from pathlib import Path


def import_model_modules(models_dir: Path, *, package_name: str = "db.models") -> None:
    for _, module_name, _ in pkgutil.iter_modules([str(models_dir)]):
        if not module_name.startswith("_"):
            importlib.import_module(f"{package_name}.{module_name}")


def sync_database_url(database_url: str) -> str:
    return database_url.replace("+asyncpg", "")
