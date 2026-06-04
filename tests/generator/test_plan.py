import pytest

from lib.cairn.generator import ResourceGenerator, parse_resource_spec


def _project_spec():
    return parse_resource_spec("project", ["name:string", "status:enum[planned,active,done]", "notes?:text"])


@pytest.mark.unit
def test_resource_generator_dry_run_returns_deterministic_file_plan(tmp_path):
    generator = ResourceGenerator(tmp_path, revision_factory=lambda: "202606041234")

    result = generator.generate(_project_spec(), dry_run=True)

    paths = [str(file.path) for file in result.planned_files]
    assert result.dry_run is True
    assert result.written_files == ()
    assert paths == [
        "db/models/__init__.py",
        "db/models/project.py",
        "db/repositories/__init__.py",
        "db/repositories/project.py",
        "src/models/project.py",
        "src/services/project.py",
        "src/routers/project.py",
        "db/migrations/versions/202606041234_create_project.py",
        "tests/project/__init__.py",
        "tests/project/test_project_schemas.py",
        "tests/project/test_project_router.py",
        "docs/resources/project.md",
    ]
    assert not (tmp_path / "src" / "routers" / "project.py").exists()


@pytest.mark.unit
def test_resource_generator_writes_conventional_cairn_layers(tmp_path):
    generator = ResourceGenerator(tmp_path, revision_factory=lambda: "202606041234")

    result = generator.generate(_project_spec())

    assert "src/routers/project.py" in {str(path) for path in result.written_files}
    model = (tmp_path / "db" / "models" / "project.py").read_text()
    repository = (tmp_path / "db" / "repositories" / "project.py").read_text()
    service = (tmp_path / "src" / "services" / "project.py").read_text()
    router = (tmp_path / "src" / "routers" / "project.py").read_text()
    migration = (tmp_path / "db" / "migrations" / "versions" / "202606041234_create_project.py").read_text()
    doc = (tmp_path / "docs" / "resources" / "project.md").read_text()

    assert "class Project(UUIDMixin, TimestampMixin, Base):" in model
    assert 'SQLEnum(ProjectStatus, name="project_status")' in model
    assert "class ProjectRepository(BaseRepository[Project]):" in repository
    assert "class ProjectService(ApplicationService):" in service
    assert "UnitOfWork" in service
    assert "get_unit_of_work" in router
    assert 'router = create_router(prefix="/projects", tags=["projects"])' in router
    assert 'register_router(router, name="projects")' in router
    assert 'op.create_table(\n        "projects"' in migration
    assert "Source of truth:" in doc


@pytest.mark.unit
def test_resource_generator_conflict_detection_fails_closed(tmp_path):
    generator = ResourceGenerator(tmp_path, revision_factory=lambda: "202606041234")
    existing = tmp_path / "src" / "models" / "project.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("# existing app code\n")

    with pytest.raises(FileExistsError, match="Refusing to overwrite existing files"):
        generator.generate(_project_spec())

    assert existing.read_text() == "# existing app code\n"


@pytest.mark.unit
def test_resource_generator_force_overwrites_conflicts(tmp_path):
    generator = ResourceGenerator(tmp_path, revision_factory=lambda: "202606041234")
    existing = tmp_path / "src" / "models" / "project.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("# existing app code\n")

    generator.generate(_project_spec(), force=True)

    assert "class ProjectCreate" in existing.read_text()


@pytest.mark.unit
def test_generated_python_files_compile(tmp_path):
    generator = ResourceGenerator(tmp_path, revision_factory=lambda: "202606041234")
    result = generator.generate(_project_spec(), dry_run=True)

    for file in result.planned_files:
        if file.path.suffix == ".py" and file.content:
            compile(file.content, str(file.path), "exec")
