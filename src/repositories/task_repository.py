from typing import Iterable

from sqlalchemy import select, exists

from src.database.database import SessionDep
from src.models.model_team import TeamMember
from src.models.model_user import User
from src.scheme.schemas_team import TeamRole


async def validate_user_in_team(
        session: SessionDep,
        user_id: int,
        team_id: int,
) -> bool:
    stmt = select(exists().where(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id))

    return await session.scalar(stmt)


async def has_team_role(session: SessionDep, user: User, team_id: int, roles: Iterable[TeamRole]) -> bool:
    stmt = select(TeamMember.role).where(
        TeamMember.user_id == user.id,
        TeamMember.team_id == team_id
    )

    role = await session.scalar(stmt)
    if role is None:
        return False

    try:
        return TeamRole(role) in roles
    except ValueError:
        return False
