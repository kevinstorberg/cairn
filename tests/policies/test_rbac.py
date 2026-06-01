import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from src.policies.base import Permission, has_permission, require_permission, require_state_permission
from src.policies.roles import ROLE_PERMISSIONS, Role
from src.security.auth import create_token


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
    def test_returns_dependency_callable(self):
        dep = require_permission(Permission.READ)
        assert callable(dep)

    def test_admin_token_passes_permission_check(self):
        app = _create_policy_test_app()
        token = create_token("user-1", extra_claims={"role": "admin"})
        client = TestClient(app)

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json() == {"sub": "user-1", "role": "admin"}

    def test_insufficient_jwt_role_returns_403(self):
        app = _create_policy_test_app()
        token = create_token("user-1", extra_claims={"role": "user"})
        client = TestClient(app)

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions: requires admin"

    def test_missing_jwt_returns_401(self):
        app = _create_policy_test_app()
        client = TestClient(app)

        response = client.get("/admin")

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    def test_invalid_jwt_returns_401(self):
        app = _create_policy_test_app()
        client = TestClient(app)

        response = client.get("/admin", headers={"Authorization": "Bearer invalid.token.value"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    def test_missing_role_claim_returns_403(self):
        app = _create_policy_test_app()
        token = create_token("user-1")
        client = TestClient(app)

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Missing role claim: role"

    def test_custom_role_claim_passes(self):
        app = _create_policy_test_app()
        token = create_token("service-1", extra_claims={"app_role": "service"})
        client = TestClient(app)

        response = client.get("/custom-role", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json() == {"sub": "service-1", "role": "service"}

    def test_state_permission_still_supports_request_state_role(self):
        app = _create_policy_test_app()
        client = TestClient(app)

        response = client.get("/state-read", headers={"X-Role": "readonly"})

        assert response.status_code == 200
        assert response.json() == {"role": "readonly"}

    def test_state_permission_missing_role_returns_401(self):
        app = _create_policy_test_app()
        client = TestClient(app)

        response = client.get("/state-read")

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    def test_state_permission_insufficient_role_returns_403(self):
        app = _create_policy_test_app()
        client = TestClient(app)

        response = client.get("/state-delete", headers={"X-Role": "readonly"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions: requires delete"


def _create_policy_test_app() -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def role_middleware(request: Request, call_next):
        role = request.headers.get("X-Role")
        if role:
            request.state.role = role
        return await call_next(request)

    @app.get("/admin")
    async def admin_route(claims: dict = Depends(require_permission(Permission.ADMIN))):
        return {"sub": claims["sub"], "role": claims["role"]}

    @app.get("/custom-role")
    async def custom_role_route(claims: dict = Depends(require_permission(Permission.WRITE, role_claim="app_role"))):
        return {"sub": claims["sub"], "role": claims["app_role"]}

    @app.get("/state-read")
    async def state_read_route(role: str = Depends(require_state_permission(Permission.READ))):
        return {"role": role}

    @app.get("/state-delete")
    async def state_delete_route(role: str = Depends(require_state_permission(Permission.DELETE))):
        return {"role": role}

    return app
