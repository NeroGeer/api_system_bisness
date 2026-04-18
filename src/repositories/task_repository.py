from typing import Iterable

from sqlalchemy import select, exists

from src.database.database import SessionDep
from src.models.model_team import TeamMember
from src.models.model_user import User
from src.scheme.schemas_team import TeamRole
from src.logger.logger import logger


async def validate_user_in_team(
        session: SessionDep,
        user_id: int,
        team_id: int,
) -> bool:
    """
    Checks whether a user is a member of a given team.

    Args:
        session (SessionDep): Database session.
        user_id (int): User ID to check.
        team_id (int): Team ID to check.

    Returns:
        bool: True if user belongs to the team, otherwise False.
    """

    logger.debug(
        f"Checking team membership: user_id={user_id}, team_id={team_id}"
    )
    stmt = select(exists().where(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id))

    return await session.scalar(stmt)


async def has_team_role(session: SessionDep, user: User, team_id: int, roles: Iterable[TeamRole]) -> bool:
    """
    Checks whether a user has one of the required roles in a specific team.

    Args:
        session (SessionDep): Database session.
        user (User): User instance.
        team_id (int): Team ID.
        roles (Iterable[TeamRole]): Allowed roles.

    Returns:
        bool: True if user has matching role, otherwise False.
    """

    logger.debug(
        f"Checking team role: user_id={user.id}, team_id={team_id}, required_roles={[r.name for r in roles]}"
    )
    stmt = select(TeamMember.role).where(
        TeamMember.user_id == user.id,
        TeamMember.team_id == team_id
    )

    role = await session.scalar(stmt)
    if role is None:
        logger.debug(
            f"No team role found: user_id={user.id}, team_id={team_id}"
        )
        return False

    try:
        return TeamRole(role) in roles
    except ValueError:
        logger.warning(
            f"Invalid role value in DB: {role} for user_id={user.id}, team_id={team_id}"
        )
        return False
