import pytest

from db.base import Base, TimestampMixin, UUIDMixin


@pytest.mark.unit
class TestBaseModel:
    def test_base_exists(self):
        assert Base is not None

    def test_timestamp_mixin_has_fields(self):
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")

    def test_uuid_mixin_has_id(self):
        assert hasattr(UUIDMixin, "id")


@pytest.mark.unit
class TestConnectionModule:
    def test_get_engine_importable(self):
        from db.connection import get_engine

        assert callable(get_engine)

    def test_get_session_importable(self):
        from db.connection import get_session

        assert callable(get_session)
