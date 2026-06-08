import importlib
from typing import Any


class LazyImportError(RuntimeError):
    pass


def import_from_path(import_path: str) -> Any:
    module_name, separator, attribute = import_path.partition(":")
    if not separator or not module_name or not attribute:
        raise LazyImportError(f"Import path must use 'module:attribute' format: {import_path!r}")

    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        raise LazyImportError(f"Could not import module {module_name!r} from {import_path!r}: {e}") from e

    try:
        value: Any = module
        for part in attribute.split("."):
            value = getattr(value, part)
    except AttributeError as e:
        raise LazyImportError(f"Could not resolve attribute {attribute!r} from {import_path!r}") from e

    return value
