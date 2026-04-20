from typing import Annotated, Iterable

from fastapi import Depends, HTTPException

from src.core.security.dependencies import get_current_user
from src.logger.logger import logger
from src.models.model_user import User
from src.scheme.schemas_user import UserRole


def has_role(user: User, roles: Iterable[UserRole]) -> bool:
    """
    Checks whether a user has at least one of the required roles.

    Args:
        user (User): The user object with assigned roles.
        roles (Iterable[UserRole]): Collection of roles to check against.

    Returns:
        bool: True if user has at least one matching role, otherwise False.
    """
    user_roles = {UserRole(role.name) for role in user.roles}
    logger.debug(
        f"Role check for user_id={user.id}: "
        f"user_roles={[r.name for r in user_roles]}, "
        f"required_roles={[r.name for r in roles]}, "
    )
    return bool(user_roles.intersection(roles))


def require_role(roles: Iterable[UserRole]):
    """
    FastAPI dependency that restricts access based on user roles.

    Args:
        roles (Iterable[UserRole]): Required roles to access the endpoint.

    Returns:
        Callable: Dependency function that returns the current user if authorized.
    """

    async def checker(user: Annotated[User, Depends(get_current_user)]):
        if not has_role(user, roles):
            logger.warning(f"Access denied (role mismatch) for user_id={user.id}")
            raise HTTPException(403, detail="Forbidden")
        logger.debug(f"Access granted by role for user_id={user.id}")
        return user

    return checker


def has_permission(user: User, permission: str) -> bool:
    """
    Checks whether a user has a specific permission via assigned roles.

    Args:
        user (User): The user object.
        permission (str): Permission name to check.

    Returns:
        bool: True if permission is found, otherwise False.
    """
    result = any(
        permission_obj.name == permission
        for role in user.roles
        for permission_obj in role.permissions
    )
    logger.debug(
        f"Permission check for user_id={user.id}: "
        f"permission={permission}, result={result}"
    )
    return result


def require_permission(permission: str):
    """
    FastAPI dependency that restricts access based on a specific permission.

    Args:
        permission (str): Required permission name.

    Returns:
        Callable: Dependency function that returns the current user if authorized.
    """

    async def checker(user: Annotated[User, Depends(get_current_user)]):
        if not has_permission(user, permission):
            logger.warning(
                f"Access denied (missing permission={permission}) "
                f"for user_id={user.id}"
            )
            raise HTTPException(status_code=403, detail="Missing permission")
        logger.debug(f"Access granted by permission={permission} for user_id={user.id}")
        return user

    return checker
