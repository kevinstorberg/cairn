import pytest

from src.policies.base import Permission, has_permission, require_permission
from src.policies.roles import ROLE_PERMISSIONS, Role


@pytest.mark.unit
class TestRolePermissions:
    def test_admin_has_all_permissions(self):
        for perm in Permission:
            assert has_permission(Role.ADMIN, perm)

    def test_readonly_only_has_read(self):
        assert has_permission(Role.READONLY, Permission.READ)
        assert not has_permission(Role.READONLY, Permission.WRITE)
        assert not has_permission(Role.READONLY, Permission.DELETE)
        assert not has_permission(Role.READONLY, Permission.ADMIN)

    def test_user_has_read_write_no_admin(self):
        assert has_permission(Role.USER, Permission.READ)
        assert has_permission(Role.USER, Permission.WRITE)
        assert not has_permission(Role.USER, Permission.ADMIN)
        assert not has_permission(Role.USER, Permission.DELETE)

    def test_service_has_read_write(self):
        assert has_permission(Role.SERVICE, Permission.READ)
        assert has_permission(Role.SERVICE, Permission.WRITE)
        assert not has_permission(Role.SERVICE, Permission.ADMIN)

    def test_unknown_role_has_no_permissions(self):
        assert not has_permission("unknown", Permission.READ)
        assert not has_permission("unknown", Permission.WRITE)


@pytest.mark.unit
class TestRolePermissionMapping:
    def test_all_roles_have_mapping(self):
        for role in Role:
            assert role in ROLE_PERMISSIONS

    def test_admin_superset_of_user(self):
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        user_perms = ROLE_PERMISSIONS[Role.USER]
        assert user_perms.issubset(admin_perms)


@pytest.mark.unit
class TestRequirePermission:
    def test_returns_depends_instance(self):
        from fastapi.params import Depends as DependsClass

        dep = require_permission(Permission.READ)
        assert isinstance(dep, DependsClass)
        assert callable(dep.dependency)
