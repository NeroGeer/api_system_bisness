from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.database import SessionDep
from src.models.model_user import User
from src.models.model_team import TeamMember
from src.scheme.schemas_team import UpdateTeamMemberRoleSchema, AddTeamMemberSchema, TeamRole
from src.logger.logger import logger


async def get_members_team(session: SessionDep, team_id: int):
    logger.info(f"Fetching members by team ID: {team_id}")
    stmt = (select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .options(selectinload(TeamMember.user))
            )

    result = await session.scalars(stmt)
    if result:
        logger.debug(f"TeamMembers found: {result}")
    else:
        logger.warning(f"TeamMembers no found with ID: {team_id}")
    return result.all()


async def add_members_team(
        team_id: int,
        data: AddTeamMemberSchema,
        session: SessionDep,
        user: User
):
    existing = await session.scalar(
        select(TeamMember)
        .where(TeamMember.user_id == data.user_id,
               TeamMember.team_id == team_id
               )
    )

    if existing:
        raise HTTPException(status_code=400, detail="User already in team")

    if not any(role.name == "admin" for role in user.roles):
        data.role = TeamRole.employee

    member = TeamMember(
        user_id=data.user_id,
        team_id=team_id,
        role=data.role
    )

    session.add(member)
    await session.commit()
    await session.refresh(member)

    return member


async def update_member_role(
        team_id: int,
        user_id: int,
        data: UpdateTeamMemberRoleSchema,
        session: SessionDep
):
    stmt = select(TeamMember).where(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id
    )

    member = await session.scalar(stmt)

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = data.role

    await session.commit()
    await session.refresh(member)

    return member


async def delete_members_team(
        team_id: int,
        user_id: int,
        session: SessionDep,
        user: User
):
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself")

    stmt = select(TeamMember).where(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id
    )

    member = await session.scalar(stmt)

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await session.delete(member)
    await session.commit()
