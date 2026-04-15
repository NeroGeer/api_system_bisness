from typing import Iterable, Annotated

from fastapi import Depends, HTTPException

from src.core.security.dependencies import get_current_user
from src.models.model_user import User
from src.scheme.schemas_user import UserRole


def has_role(user: User, roles: Iterable[UserRole]) -> bool:
    user_roles = {UserRole(role.name) for role in user.roles}
    return bool(user_roles.intersection(roles))


def require_role(roles: Iterable[UserRole]):
    async def checker(user: Annotated[User, Depends(get_current_user)]):
        if not has_role(user, roles):
            raise HTTPException(403, detail="Forbidden")
        return user

    return checker


def has_permission(user: User, permission: str) -> bool:
    return any(
        permission_obj.name == permission
        for role in user.roles
        for permission_obj in role.permissions
    )


def require_permission(permission: str):
    async def checker(
            user: Annotated[User, Depends(get_current_user)]
    ):
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail="Missing permission"
            )
        return user

    return checker
