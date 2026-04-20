from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select

from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_team import TeamMember
from src.models.model_user import PermissionResult, User
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
    """
    Validates meeting creation or update rules.

    Ensures:
    - creator belongs to the team (if not admin)
    - participants exist in DB
    - participants belong to the team
    - participants have no meeting conflicts (if time range provided)

    Args:
        session: Database session dependency.
        team_id: Team identifier where meeting is created/updated.
        creator: User creating or updating the meeting.
        result_perm: Permission result (admin/team role/executor flags).
        participants_set: Set of participant user IDs.
        start_time: Meeting start time (optional conflict check).
        end_time: Meeting end time (optional conflict check).

    Raises:
        HTTPException:
            - 403 if creator is not allowed in team
            - 404 if any participant does not exist
            - 400 if participants are not part of the team
            - 400 if participants already have conflicting meetings
    """

    logger.debug(f"Validating meeting data: team_id={team_id},"
                 f" creator_id={creator.id}")

    if not result_perm.is_admin:
        if not await validate_user_in_team(
            session=session, user_id=creator.id, team_id=team_id
        ):
            logger.warning(
                f"Creator not in team: user_id={creator.id}, team_id={team_id}"
            )
            raise HTTPException(
                status_code=403, detail="Creator must be a member of the team"
            )

    if participants_set is None or not participants_set:
        logger.debug("No participants provided for validation")
        return

    stmt = (
        select(User.id, TeamMember.user_id)
        .outerjoin(
            TeamMember,
            (TeamMember.user_id == User.id) & (TeamMember.team_id == team_id),
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
        logger.warning(f"Missing users in system: {missing_users}")
        raise HTTPException(status_code=404, detail=f"Users not found: {missing_users}")

    invalid_users = participants_set - team_users
    if invalid_users:
        logger.warning(f"Users not in team: team_id={team_id}, users={invalid_users}")
        raise HTTPException(
            status_code=400, detail=f"Users not in team: {invalid_users}"
        )

    if start_time and end_time:
        logger.debug(f"Checking meeting conflicts: users={participants_set}")
        conflicted_users = await check_meeting_conflicts(
            session=session,
            user_ids=list(participants_set),
            start_time=start_time,
            end_time=end_time,
        )

        if conflicted_users:
            raise HTTPException(
                status_code=400,
                detail=f"Users already have meetings: {conflicted_users}",
            )

    logger.debug("Meeting validation passed successfully")
