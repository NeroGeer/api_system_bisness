from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, delete, select
from sqlalchemy.orm import selectinload

from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_meeting import Meeting, MeetingParticipant
from src.models.model_user import User
from src.repositories.meeting_repository import check_meeting_conflicts
from src.scheme.schemas_meeting import MeetingCreateSchema, MeetingUpdateSchema
from src.scheme.schemas_team import TeamRole
from src.services.meeting_service import validate_meeting_data
from src.services.task_service import require_admin_or_team_manager
from src.utils.utils import make_date_range


async def meeting_stmt(
    session: SessionDep, meeting_id: int, team_id: int | None = None
) -> Meeting:
    """
    Fetches a meeting by ID with participants loaded.

    Args:
        session (SessionDep): Database session.
        meeting_id (int): Meeting ID.
        team_id (int | None): Optional team filter.

    Returns:
        Meeting: Meeting instance.

    Raises:
        HTTPException: If meeting not found.
    """

    stmt = (
        select(Meeting)
        .where(Meeting.id == meeting_id)
        .options(selectinload(Meeting.participants))
    )

    if team_id is not None:
        stmt = stmt.where(Meeting.team_id == team_id)

    meeting = await session.scalar(stmt)

    if not meeting:
        logger.warning(f"Meeting not found: meeting_id={meeting_id}")
        raise HTTPException(status_code=404, detail="Meeting not found")

    return meeting


async def get_meeting(
    team_id: int,
    current_user: User,
    session: SessionDep,
    meeting_id: int | None = None,
    only_my_meetings: bool = False,
    participant_user_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """
    Retrieves meetings for a team with optional filters.

    Supports:
        - single meeting fetch
        - date range filtering
        - filtering by participant
        - filtering by current user participation
    """

    logger.debug(f"Fetching meetings: user_id={current_user.id}, team_id={team_id}")

    await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=team_id,
        team_role={TeamRole.manager, TeamRole.employee},
    )
    stmt = (
        select(Meeting).where(Meeting.team_id == team_id).order_by(Meeting.start_time)
    )

    if meeting_id is not None:
        stmt = stmt.where(Meeting.id == meeting_id)

    if start_date and end_date is not None:
        start_dt, end_dt = await make_date_range(start_date, end_date)

        stmt = stmt.where(
            and_(Meeting.start_time <= end_dt, Meeting.end_time >= start_dt)
        )

    if only_my_meetings and participant_user_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Conflicting filters: "
            "use only_my_meetings OR participant_user_id",
        )

    if only_my_meetings:
        stmt = stmt.where(
            Meeting.participants.any(MeetingParticipant.user_id == current_user.id)
        )

    if participant_user_id is not None:
        stmt = stmt.where(
            Meeting.participants.any(MeetingParticipant.user_id == participant_user_id)
        )

    result = await session.execute(stmt)

    if meeting_id is not None:
        meeting = result.scalars().first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return meeting

    return result.scalars().all()


async def create_meeting(
    current_user: User,
    session: SessionDep,
    meeting_data: MeetingCreateSchema,
    team_id: int,
):
    """
    Creates a new meeting and assigns participants.

    Performs:
        - permission validation
        - participant validation
        - conflict checks (via service layer)
    """

    logger.info(f"Create meeting: user_id={current_user.id}, team_id={team_id}")
    result_perm = await require_admin_or_team_manager(
        session=session, current_user=current_user, team_id=team_id
    )

    participants_set: set[int] = set(meeting_data.participants or [])

    await validate_meeting_data(
        session=session,
        team_id=team_id,
        creator=current_user,
        participants_set=participants_set,
        result_perm=result_perm,
    )

    meeting = Meeting(
        creator_id=current_user.id,
        team_id=team_id,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        title=meeting_data.title,
        description=meeting_data.description,
    )

    session.add(meeting)
    await session.flush()

    for user_id in participants_set:
        session.add(MeetingParticipant(meeting_id=meeting.id, user_id=user_id))

    await session.commit()
    logger.info(f"Meeting created: meeting_id={meeting.id}")

    await session.refresh(meeting)

    return meeting


async def update_meeting(
    current_user: User,
    session: SessionDep,
    meeting_id: int,
    data: MeetingUpdateSchema,
    team_id: int,
):
    """
    Updates meeting data including:
        - title
        - description
        - participants
        - time range

    Performs:
        - permission check (admin / team manager / creator)
        - participant validation
        - time conflict validation
    """

    logger.debug(
        f"Updating meeting: meeting_id={meeting_id}, user_id={current_user.id}"
    )
    if not data or data is None:
        raise HTTPException(status_code=400, detail="Data task empty")

    meeting = await meeting_stmt(
        session=session, meeting_id=meeting_id, team_id=team_id
    )

    result_perm = await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=meeting.team_id,
    )

    if not result_perm.is_admin and meeting.creator_id != current_user.id:
        logger.warning(
            f"Unauthorized meeting update attempt: "
            f"user_id={current_user.id}, meeting_id={meeting_id}"
        )
        raise HTTPException(status_code=403, detail="Not allowed to edit meeting")

    if data.title is not None:
        meeting.title = data.title

    if data.description is not None:
        meeting.description = data.description

    if data.participants is not None:

        to_add = set(data.participants) - {p.user_id for p in meeting.participants}
        logger.debug(f"Participants update: meeting_id={meeting_id}, to_add={to_add}")
        if to_add:
            await validate_meeting_data(
                session=session,
                team_id=meeting.team_id,
                creator=current_user,
                result_perm=result_perm,
                participants_set=to_add,
            )

            for user_id in to_add:
                session.add(MeetingParticipant(meeting_id=meeting_id, user_id=user_id))

    new_start = data.start_time or meeting.start_time
    new_end = data.end_time or meeting.end_time

    if data.start_time is not None or data.end_time is not None:
        if new_end <= new_start:
            raise HTTPException(status_code=400, detail="Invalid time range")

        participant_ids = [p.user_id for p in meeting.participants]

        conflicts = await check_meeting_conflicts(
            session=session,
            user_ids=participant_ids,
            start_time=new_start,
            end_time=new_end,
            exclude_meeting_id=meeting.id,
        )

        if conflicts:

            raise HTTPException(
                status_code=400, detail=f"Users already have meetings: {conflicts}"
            )

        meeting.start_time = new_start
        meeting.end_time = new_end

    await session.commit()
    await session.refresh(meeting)

    logger.info(f"Meeting updated: meeting_id={meeting.id}")

    return meeting


async def delete_meeting_participant(
    current_user: User,
    session: SessionDep,
    meeting_id: int,
    team_id: int,
    users_ids: list[int],
):
    """
    Removes participants from a meeting.

    Args:
        current_user (User): Authenticated user performing the action.
        session (SessionDep): Database session.
        meeting_id (int): Target meeting ID.
        team_id (int): Team ID.
        users_ids: list[int]: List of user IDs to remove.

    Returns:
        dict: Meeting ID and removed participants.
    """

    logger.debug(
        f"Removing participants: meeting_id={meeting_id}, user_id={current_user.id}"
    )
    if not users_ids:
        raise HTTPException(status_code=400, detail="No users provided")

    meeting = await meeting_stmt(
        session=session, meeting_id=meeting_id, team_id=team_id
    )

    result_perm = await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=meeting.team_id,
    )

    if not result_perm.is_admin and meeting.creator_id != current_user.id:
        logger.warning(
            f"Unauthorized participant delete attempt: "
            f"user_id={current_user.id}, meeting_id={meeting_id}"
        )
        raise HTTPException(status_code=403, detail="Not allowed to edit meeting")

    to_remove = set(users_ids)
    missing = to_remove - {p.user_id for p in meeting.participants}

    if missing:
        raise HTTPException(
            status_code=400, detail=f"Users not in meeting: {list(missing)}"
        )

    await session.execute(
        delete(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id.in_(to_remove),
        )
    )
    await session.commit()

    logger.info(
        f"Participants removed: meeting_id={meeting_id}, users={list(to_remove)}"
    )

    return {
        "meeting_id": meeting.id,
        "removed_participants": list(to_remove),
    }


async def delete_meeting_by_id(
    team_id: int, current_user: User, session: SessionDep, meeting_id: int
):
    """
    Deletes a meeting and all related participants.

    Args:
        team_id (int): Team ID.
        current_user (User): Authenticated user.
        session (SessionDep): Database session.
        meeting_id (int): Meeting ID.

    Returns:
        dict: Confirmation message and deleted meeting info.
    """

    logger.debug(
        f"Deleting meeting: meeting_id={meeting_id}, user_id={current_user.id}"
    )

    result_perm = await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=team_id,
    )

    meeting = await meeting_stmt(
        session=session, meeting_id=meeting_id, team_id=team_id
    )

    if not result_perm.is_admin and meeting.creator_id != current_user.id:
        logger.warning(
            f"Unauthorized meeting delete attempt: "
            f"user_id={current_user.id}, meeting_id={meeting_id}"
        )
        raise HTTPException(status_code=403, detail="Not allowed to edit meeting")

    await session.delete(meeting)
    await session.commit()

    logger.info(f"Meeting deleted: meeting_id={meeting_id}")

    return {"message": "Meeting deleted"}
