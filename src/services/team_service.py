from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select, exists

from src.core.security.dependencies import get_current_user
from src.database.database import SessionDep
from src.models.model_team import TeamMember
from src.models.model_user import User
from src.scheme.schemas_team import TeamRole


def require_team_manager_or_admin():
    """
    Dependency that allows access only to:
    - global admin users
    - team members with role: manager or owner
    """
    async def checker(team_id: int, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):

        if any(role.name == "admin" for role in user.roles):
            return user

        stmt = select(
            exists().where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role.in_([TeamRole.manager,]),
            )
        )

        result = await session.scalar(stmt)

        if not result:
            raise HTTPException(403, detail="Forbidden")

        return user

    return checker
