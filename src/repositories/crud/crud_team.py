from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_team import Team, TeamMember
from src.models.model_user import User
from src.scheme.schemas_team import (
    AddTeamMemberSchema,
    TeamRole,
    UpdateTeamMemberRoleSchema,
)


async def get_members_team(session: SessionDep, team_id: int):
    """
    Author: NeroGeer
    GitHub: https://github.com/NeroGeer
    License: MIT

    Returns all members of a team.

    Args:
        session: DB session
        team_id: Team ID

    Returns:
        list[TeamMember]: team members with loaded user relation
    """
    logger.info(f"Fetching members by team ID: {team_id}")
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.members).selectinload(TeamMember.user))
    )

    result = await session.scalar(stmt)
    if result:
        logger.debug(f"Team found: {result}")
    else:
        logger.warning(f"Team no found with ID: {team_id}")
    return result


async def add_members_team(
    team_id: int, data: AddTeamMemberSchema, session: SessionDep, user: User
):
    """
    Adds a user to a team.

    Rules:
        - user must not already be in team
        - only admin can assign roles other than employee
        - default role is employee for non-admins
    """
    logger.debug(
        f"Adding member: team_id={team_id}, user_id={data.user_id}, "
        f"actor_user_id={user.id}"
    )
    existing = await session.scalar(
        select(TeamMember).where(
            TeamMember.user_id == data.user_id, TeamMember.team_id == team_id
        )
    )

    if existing:
        logger.warning(
            f"Duplicate team member add attempt: user_id={data.user_id}, team_id={team_id}"
        )
        raise HTTPException(status_code=400, detail="User already in team")

    if not any(role.name == "admin" for role in user.roles):
        data.role = TeamRole.employee

    member = TeamMember(user_id=data.user_id, team_id=team_id, role=data.role)

    session.add(member)
    await session.commit()
    await session.refresh(member)

    logger.info(
        f"Team member added: user_id={data.user_id}, team_id={team_id}, role={member.role}"
    )

    return member


async def update_member_role(
    team_id: int, user_id: int, data: UpdateTeamMemberRoleSchema, session: SessionDep
):
    """
    Updates a team member role.

    Args:
        team_id: Team identifier
        user_id: Target user identifier
        data: New role data
        session: Database session

    Returns:
        TeamMember: Updated member entity

    Raises:
        HTTPException: If member is not found
    """
    logger.debug(
        f"Updating team member role: team_id={team_id}, user_id={user_id}, new_role={data.role}"
    )

    stmt = select(TeamMember).where(
        TeamMember.user_id == user_id, TeamMember.team_id == team_id
    )

    member = await session.scalar(stmt)

    if not member:
        logger.warning(
            f"Team member not found for role update: team_id={team_id}, user_id={user_id}"
        )
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = data.role

    await session.commit()
    await session.refresh(member)

    logger.info(
        f"Team member role updated: team_id={team_id}, user_id={user_id}, role={member.role}"
    )

    return member


async def delete_members_team(
    team_id: int, user_id: int, session: SessionDep, user: User
):
    """
    Removes a user from a team.

    Rules:
        - user cannot remove themselves
        - member must exist in team

    Returns:
        dict: operation result implicitly via HTTP response
    """

    logger.debug(
        f"Deleting team member: team_id={team_id}, target_user_id={user_id}, actor_user_id={user.id}"
    )
    if user.id == user_id:
        logger.warning(
            f"Self-removal attempt blocked: user_id={user_id}, team_id={team_id}"
        )
        raise HTTPException(status_code=400, detail="You cannot remove yourself")

    stmt = select(TeamMember).where(
        TeamMember.user_id == user_id, TeamMember.team_id == team_id
    )

    member = await session.scalar(stmt)

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await session.delete(member)
    await session.commit()

    logger.info(f"Team member deleted: team_id={team_id}, user_id={user_id}")
