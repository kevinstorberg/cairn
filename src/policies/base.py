from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, Request


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


def has_permission(role: str, permission: Permission) -> bool:
    from src.policies.roles import ROLE_PERMISSIONS, Role

    try:
        resolved_role = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(resolved_role, set())


def require_permission(permission: Permission) -> Callable:
    async def _check(request: Request):
        role = getattr(request.state, "role", None)
        if role is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if not has_permission(role, permission):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions: requires {permission.value}")

    return Depends(_check)
