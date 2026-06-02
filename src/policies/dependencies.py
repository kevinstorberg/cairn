from collections.abc import Callable

from fastapi import Depends, HTTPException, Request

from src.policies.base import Permission, has_permission
from src.security.auth import require_auth


def require_permission(permission: Permission, *, role_claim: str = "role") -> Callable:
    async def _check(claims: dict = Depends(require_auth)) -> dict:
        role = claims.get(role_claim)
        if role is None:
            raise HTTPException(status_code=403, detail=f"Missing role claim: {role_claim}")
        if not has_permission(role, permission):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions: requires {permission.value}")
        return claims

    return _check


def require_state_permission(permission: Permission) -> Callable:
    async def _check(request: Request) -> str:
        role = getattr(request.state, "role", None)
        if role is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if not has_permission(role, permission):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions: requires {permission.value}")
        return role

    return _check
