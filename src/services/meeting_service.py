from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select

from src.database.database import SessionDep
from src.models.model_team import TeamMember
from src.models.model_user import User, PermissionResult
from src.repositories.meeting_repository import check_meeting_conflicts
from src.repositories.task_repository import validate_user_in_team


async def validate_meeting_data(
        session: SessionDep,
        team_id: int,
        creator: User,
        result_perm: PermissionResult,
        participants_set: set[int] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
):
    if not result_perm.is_admin:
        if not await validate_user_in_team(session=session, user_id=creator.id, team_id=team_id):
            raise HTTPException(status_code=403, detail="Creator must be a member of the team")

    if participants_set is None or not participants_set:
        return

    stmt = (
        select(User.id, TeamMember.user_id)
        .outerjoin(
            TeamMember,
            (TeamMember.user_id == User.id) &
            (TeamMember.team_id == team_id)
        )
        .where(User.id.in_(participants_set))
    )

    rows = await session.execute(stmt)

    existing_users = set()
    team_users = set()

    for user_id, team_user_id in rows:
        existing_users.add(user_id)
        if team_user_id is not None:
            team_users.add(user_id)

    missing_users = participants_set - existing_users
    if missing_users:
        raise HTTPException(status_code=404, detail=f"Users not found: {missing_users}")

    invalid_users = participants_set - team_users
    if invalid_users:
        raise HTTPException(status_code=400, detail=f"Users not in team: {invalid_users}")

    if start_time and end_time:
        conflicted_users = await check_meeting_conflicts(
            session=session,
            user_ids=list(participants_set),
            start_time=start_time,
            end_time=end_time,
        )

        if conflicted_users:
            raise HTTPException(status_code=400, detail=f"Users already have meetings: {conflicted_users}")
