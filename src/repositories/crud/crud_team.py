from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.logger.logger import logger
from src.models.model_team import Team, TeamMember
from src.models.model_user import User
from src.scheme.schemas_team import (
    AddTeamMemberSchema,
    TeamRole,
    UpdateTeamMemberRoleSchema,
)
from src.core.context.base_context import BaseContext


async def get_members_team(ctx: BaseContext):
    """
    Author: NeroGeer
    GitHub: https://github.com/NeroGeer
    License: MIT

    Returns all members of a team.

    Args:
        ctx: BaseContext
        ctx.session: DB session
        ctx.team_id: Team ID

    Returns:
        list[TeamMember]: team members with loaded user relation
    """

    session = ctx.session
    team_id = ctx.scope.team_id

    await ctx.require_admin_or_team_role_or_executor(team_role={TeamRole.manager, TeamRole.employee})

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
    ctx: BaseContext, data: AddTeamMemberSchema
):
    """
    Adds a user to a team.

    Rules:
        - user must not already be in team
        - only admin can assign roles other than employee
        - default role is employee for non-admins

    Args:
        ctx: BaseContext
        ctx.session: DB session
        ctx.team_id: Team ID
        data: AddTeamMemberSchema

    """

    session = ctx.session
    team_id = ctx.scope.team_id

    await ctx.require_admin_or_team_role_or_executor()

    if not await session.get(User, data.user_id):
        raise HTTPException(status_code=400, detail=f"User {data.user_id} not Found")

    logger.debug(
        f"Adding member: team_id={team_id}, user_id={data.user_id}"
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
    ctx: BaseContext, data: UpdateTeamMemberRoleSchema,
):
    """
    Updates a team member role.

    Args:
        ctx: BaseContext
        ctx.scope.team_id: Team identifier
        ctx.scope.user_id: Target user identifier
        ctx.session: Database session
        data: New role data

    Returns:
        TeamMember: Updated member entity

    Raises:
        HTTPException: If member is not found
    """

    session = ctx.session
    team_id = ctx.scope.team_id
    user_id = ctx.scope.user_id

    ctx.require_admin()

    if not await session.get(User, user_id):
        raise HTTPException(status_code=400, detail=f"User {user_id} not Found")

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
    ctx: BaseContext,
):
    """
    Removes a user from a team.

    Rules:
        - user cannot remove themselves
        - member must exist in team

    Args:
        ctx: BaseContext
        ctx.scope.team_id: Team identifier
        ctx.scope.user_id: Target user identifier
        ctx.session: Database session

    Returns:
        dict: operation result implicitly via HTTP response
    """
    current_user = ctx.current_user
    session = ctx.session
    team_id = ctx.scope.team_id
    user_id = ctx.scope.user_id

    await ctx.require_admin_or_team_role_or_executor()

    logger.debug(
        f"Deleting team member: team_id={team_id}, target_user_id={user_id}, "
        f"actor_user_id={current_user.id}"
    )
    if current_user.id == user_id:
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
