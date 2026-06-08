from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DatabaseInspector = Callable[[str, Sequence[str]], Awaitable[dict[str, Any]]]

_TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class PreflightInput:
    database_url: str
    expected_heads: tuple[str, ...] = ()
    tables: tuple[str, ...] = ()
    write_cutover: bool = False
    cutover_confirmed: bool = False
    backup_path: str = ""
    mode: str = "local"


async def run_preflight(
    preflight: PreflightInput,
    *,
    inspector: DatabaseInspector | None = None,
) -> dict[str, Any]:
    inspector = inspector or inspect_database_state
    errors = _validate_preflight_input(preflight)
    report: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": preflight.mode,
        "write_cutover": preflight.write_cutover,
        "expected_heads": list(preflight.expected_heads),
        "tables": list(preflight.tables),
        "database": {},
        "errors": errors,
    }

    if preflight.database_url and not errors:
        database = await inspector(preflight.database_url, preflight.tables)
        report["database"] = database
        errors.extend(_migration_errors(preflight.expected_heads, database.get("alembic_versions", [])))

    report["status"] = "pass" if not errors else "fail"
    return report


async def inspect_database_state(database_url: str, tables: Sequence[str]) -> dict[str, Any]:
    engine = create_async_engine(_async_database_url(database_url))
    try:
        async with engine.connect() as connection:
            alembic_versions = await _read_alembic_versions(connection)
            row_counts = {}
            for table in tables:
                _validate_table_name(table)
                exists = await connection.execute(text("SELECT to_regclass(:table_name)::text"), {"table_name": table})
                if exists.scalar_one_or_none() is None:
                    row_counts[table] = None
                    continue
                result = await connection.execute(text(f'SELECT count(*) FROM "{table}"'))
                row_counts[table] = int(result.scalar_one())
            return {"alembic_versions": alembic_versions, "row_counts": row_counts}
    finally:
        await engine.dispose()


def _validate_preflight_input(preflight: PreflightInput) -> list[str]:
    errors = []
    if not preflight.database_url:
        errors.append("database_url is required")
    for table in preflight.tables:
        try:
            _validate_table_name(table)
        except ValueError as e:
            errors.append(str(e))
    if preflight.write_cutover:
        if not preflight.cutover_confirmed:
            errors.append("cutover_confirmed=true is required for write-cutover mode")
        if not preflight.backup_path:
            errors.append("backup_path is required for write-cutover mode")
    return errors


def _migration_errors(expected_heads: Sequence[str], actual_heads: Sequence[str]) -> list[str]:
    if not expected_heads:
        return []
    if set(actual_heads) == set(expected_heads):
        return []
    return [f"database revisions {sorted(actual_heads)} do not match expected heads {sorted(expected_heads)}"]


async def _read_alembic_versions(connection) -> list[str]:
    result = await connection.execute(text("SELECT to_regclass('public.alembic_version')::text"))
    if result.scalar_one_or_none() is None:
        return []
    versions = await connection.execute(text("SELECT version_num FROM alembic_version"))
    return [row.version_num for row in versions]


def _validate_table_name(table: str) -> None:
    if not _TABLE_NAME_PATTERN.fullmatch(table):
        raise ValueError(f"Invalid table name for preflight row count: {table!r}")


def _async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url
