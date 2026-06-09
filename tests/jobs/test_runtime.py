import asyncio

import pytest

from config.models import DefaultConfig, JobsConfig
from src.jobs.base import BaseJob
from src.jobs.definitions import JobDefinition, LockPolicy, import_path_for
from src.jobs.runtime import create_job_runtime
from src.jobs.stores import JobRunStatus
from src.settings import Settings

_SCHEDULED_EVENT: asyncio.Event | None = None


class RuntimeManualJob(BaseJob):
    name = "runtime_manual"

    async def execute(self):
        return None


class RuntimeScheduledJob(BaseJob):
    name = "runtime_scheduled"

    async def execute(self):
        if _SCHEDULED_EVENT is not None:
            _SCHEDULED_EVENT.set()


def build_runtime_manual_job() -> BaseJob:
    return RuntimeManualJob()


def build_runtime_scheduled_job() -> BaseJob:
    return RuntimeScheduledJob()


def _settings() -> Settings:
    return Settings(_env_file=None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_runtime_disabled_mode_is_noop():
    config = DefaultConfig(jobs=JobsConfig(enabled=False))
    runtime = create_job_runtime(config, _settings())

    await runtime.start()

    assert runtime.running is False
    assert runtime.health()["enabled"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_runtime_starts_and_stops_empty_scheduler():
    config = DefaultConfig(jobs=JobsConfig(auto_discover=False))
    runtime = create_job_runtime(config, _settings())

    await runtime.start()
    try:
        assert runtime.running is True
        assert runtime.health()["job_count"] == 0
    finally:
        await runtime.shutdown()

    assert runtime.running is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_runtime_manual_run_records_status():
    config = DefaultConfig(jobs=JobsConfig(auto_discover=False))
    definition = JobDefinition(
        name="runtime_manual",
        factory=import_path_for(build_runtime_manual_job),
        lock_policy=LockPolicy(enabled=False),
        metadata={"owner": "template"},
    )
    runtime = create_job_runtime(config, _settings(), definitions={definition.name: definition})

    record = await runtime.run_job("runtime_manual")

    assert record.status == JobRunStatus.SUCCESS
    assert (await runtime.list_runs("runtime_manual"))[0].status == JobRunStatus.SUCCESS
    assert runtime.list_jobs()[0]["metadata"] == {"owner": "template"}


@pytest.mark.unit
def test_job_definition_metadata_must_be_dictionary():
    with pytest.raises(ValueError, match="metadata must be a dictionary"):
        JobDefinition(name="bad_metadata", metadata=["not", "a", "dict"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_runtime_schedules_importable_definition():
    global _SCHEDULED_EVENT
    _SCHEDULED_EVENT = asyncio.Event()
    config = DefaultConfig(jobs=JobsConfig(auto_discover=False))
    definition = JobDefinition(
        name="runtime_scheduled",
        factory=import_path_for(build_runtime_scheduled_job),
        trigger_kwargs={"seconds": 0.05, "max_instances": 1, "coalesce": True},
        lock_policy=LockPolicy(enabled=False),
    )
    runtime = create_job_runtime(config, _settings(), definitions={definition.name: definition})

    await runtime.start()
    try:
        await asyncio.wait_for(_SCHEDULED_EVENT.wait(), timeout=1)
    finally:
        await runtime.shutdown()
        _SCHEDULED_EVENT = None

    assert (await runtime.list_runs("runtime_scheduled"))[0].status == JobRunStatus.SUCCESS


@pytest.mark.unit
@pytest.mark.asyncio
async def test_runtime_sync_namespace_adds_updates_and_removes_only_that_namespace():
    config = DefaultConfig(jobs=JobsConfig(auto_discover=False))
    runtime = create_job_runtime(config, _settings())
    template_definition = JobDefinition(
        name="template_job",
        factory=import_path_for(build_runtime_manual_job),
        trigger_kwargs={"seconds": 60, "max_instances": 1, "coalesce": True},
        lock_policy=LockPolicy(enabled=False),
        metadata={"version": 1},
    )
    other_definition = JobDefinition(
        name="other_job",
        factory=import_path_for(build_runtime_manual_job),
        trigger_kwargs={"seconds": 60, "max_instances": 1, "coalesce": True},
        lock_policy=LockPolicy(enabled=False),
    )

    await runtime.start()
    try:
        runtime.sync_namespace("template", {template_definition.name: template_definition})
        runtime.sync_namespace("other", {other_definition.name: other_definition})

        assert runtime.scheduler.get_job("template_job") is not None
        assert runtime.definitions["template_job"].metadata == {"version": 1, "namespace": "template"}
        assert runtime.definitions["other_job"].metadata["namespace"] == "other"

        updated = JobDefinition(
            name="template_job",
            factory=import_path_for(build_runtime_manual_job),
            trigger_kwargs={"seconds": 60, "max_instances": 1, "coalesce": True},
            lock_policy=LockPolicy(enabled=False),
            metadata={"version": 2},
        )
        runtime.sync_namespace("template", {updated.name: updated})

        assert runtime.definitions["template_job"].metadata == {"version": 2, "namespace": "template"}

        runtime.sync_namespace("template", {})

        assert "template_job" not in runtime.definitions
        assert runtime.scheduler.get_job("template_job") is None
        assert "other_job" in runtime.definitions
        assert runtime.scheduler.get_job("other_job") is not None
    finally:
        await runtime.shutdown()


@pytest.mark.unit
def test_runtime_sync_namespace_rejects_blank_namespace():
    runtime = create_job_runtime(DefaultConfig(jobs=JobsConfig(auto_discover=False)), _settings())

    with pytest.raises(ValueError, match="namespace is required"):
        runtime.sync_namespace(" ", {})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_persistent_scheduler_rejects_non_importable_definition_before_starting():
    config = DefaultConfig(jobs=JobsConfig(auto_discover=False, scheduler_store="postgres"))
    definition = JobDefinition(name="missing_factory")
    runtime = create_job_runtime(config, _settings(), definitions={definition.name: definition})

    with pytest.raises(ValueError, match="persistent scheduling"):
        await runtime.start()
