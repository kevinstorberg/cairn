import pytest

from src.operations.preflight import PreflightInput, run_preflight


async def fake_inspector(database_url: str, tables):
    return {
        "database_url": database_url,
        "alembic_versions": ["head-1"],
        "row_counts": {table: 7 for table in tables},
    }


@pytest.mark.asyncio
async def test_preflight_reports_heads_and_row_counts():
    report = await run_preflight(
        PreflightInput(
            database_url="postgresql://readonly@example/db",
            expected_heads=("head-1",),
            tables=("projects", "tasks"),
            mode="production",
        ),
        inspector=fake_inspector,
    )

    assert report["status"] == "pass"
    assert report["mode"] == "production"
    assert report["database"]["alembic_versions"] == ["head-1"]
    assert report["database"]["row_counts"] == {"projects": 7, "tasks": 7}


@pytest.mark.asyncio
async def test_preflight_fails_for_migration_mismatch():
    report = await run_preflight(
        PreflightInput(database_url="postgresql://readonly@example/db", expected_heads=("expected",)),
        inspector=fake_inspector,
    )

    assert report["status"] == "fail"
    assert "do not match expected heads" in report["errors"][0]


@pytest.mark.asyncio
async def test_write_cutover_fails_closed_without_confirmation_and_backup():
    report = await run_preflight(
        PreflightInput(database_url="postgresql://write@example/db", write_cutover=True),
        inspector=fake_inspector,
    )

    assert report["status"] == "fail"
    assert "cutover_confirmed=true is required for write-cutover mode" in report["errors"]
    assert "backup_path is required for write-cutover mode" in report["errors"]
    assert report["database"] == {}


@pytest.mark.asyncio
async def test_preflight_rejects_invalid_table_names_before_inspection():
    report = await run_preflight(
        PreflightInput(database_url="postgresql://readonly@example/db", tables=("projects; drop table users",)),
        inspector=fake_inspector,
    )

    assert report["status"] == "fail"
    assert "Invalid table name" in report["errors"][0]
    assert report["database"] == {}
