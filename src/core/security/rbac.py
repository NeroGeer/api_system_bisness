from typing import Iterable

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


def has_permission(user: User, permission: str) -> bool:
    """
    Checks whether a user has a specific permission via assigned roles.

    Args:
        user (User): The user object.
        permission (str): Permission name to check.

    Returns:
        bool: True if permission is found, otherwise False.
    """
    if not hasattr(user, "_permission_cache"):
        user._permission_cache = {
            perm.name
            for role in user.roles
            for perm in role.permissions
        }

    result = permission in user._permission_cache

    if not result:
        logger.debug(
            f"user_id={user.id} missing permission={permission}"
        )

    return result
