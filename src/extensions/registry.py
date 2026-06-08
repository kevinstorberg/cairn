from __future__ import annotations

import inspect
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from fastapi import FastAPI

from config.models import ExtensionsConfig
from src.extensions.lazy import LazyImportError, import_from_path
from src.settings import Settings


class ExtensionError(RuntimeError):
    pass


@runtime_checkable
class ExtensionApp(Protocol):
    def include_routes(self, app: FastAPI) -> None: ...


@dataclass(frozen=True)
class LoadedExtension:
    name: str
    app: ExtensionApp


def enabled_extension_names(config: ExtensionsConfig, settings: Settings) -> list[str]:
    names: list[str] = []
    for name in [*config.enabled, *_csv_names(settings.EXTENSIONS_ENABLED)]:
        if name not in names:
            names.append(name)
    return names


def load_enabled_extensions(config: ExtensionsConfig, settings: Settings) -> list[LoadedExtension]:
    extensions = []
    for name in enabled_extension_names(config, settings):
        app_config = config.apps.get(name)
        if app_config is None:
            raise ExtensionError(f"Extension {name!r} is enabled but not configured in extensions.apps")

        try:
            extension = _coerce_extension(import_from_path(app_config.import_path), name=name)
        except LazyImportError as e:
            raise ExtensionError(f"Extension {name!r} could not be loaded from {app_config.import_path!r}: {e}") from e

        extensions.append(LoadedExtension(name=name, app=extension))
    return extensions


def include_extension_routes(app: FastAPI, extensions: Iterable[LoadedExtension]) -> None:
    for extension in extensions:
        extension.app.include_routes(app)


def mount_extension_static(app: FastAPI, extensions: Iterable[LoadedExtension]) -> None:
    for extension in extensions:
        hook = getattr(extension.app, "mount_static", None)
        if hook is not None:
            hook(app)


async def startup_extensions(app: FastAPI, extensions: Iterable[LoadedExtension]) -> None:
    for extension in extensions:
        await _run_optional_hook(extension, "startup", app)


async def shutdown_extensions(app: FastAPI, extensions: Iterable[LoadedExtension]) -> None:
    for extension in reversed(list(extensions)):
        await _run_optional_hook(extension, "shutdown", app)


def _coerce_extension(value: Any, *, name: str) -> ExtensionApp:
    extension = value
    if not hasattr(extension, "include_routes") and callable(extension):
        extension = extension()

    if not hasattr(extension, "include_routes"):
        raise ExtensionError(f"Extension {name!r} must provide include_routes(app)")

    return extension


async def _run_optional_hook(extension: LoadedExtension, hook_name: str, app: FastAPI) -> None:
    hook = getattr(extension.app, hook_name, None)
    if hook is None:
        return

    try:
        result = hook(app)
        if inspect.isawaitable(result):
            await result
    except Exception as e:
        raise ExtensionError(f"Extension {extension.name!r} {hook_name} hook failed: {e}") from e


def _csv_names(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]
