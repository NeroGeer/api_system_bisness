from datetime import datetime

from sqlalchemy import select

from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_meeting import Meeting, MeetingParticipant


async def check_meeting_conflicts(
    session: SessionDep,
    user_ids: list[int],
    start_time: datetime,
    end_time: datetime,
    exclude_meeting_id: int | None = None,
):
    """
    Checks for scheduling conflicts between users and existing meetings.

    A conflict occurs when a user is already assigned to a meeting
    that overlaps with the provided time range.

    Args:
        session (SessionDep): Database session.
        user_ids (list[int]): List of user IDs to check.
        start_time (datetime): Proposed meeting start time.
        end_time (datetime): Proposed meeting end time.
        exclude_meeting_id (int | None): Meeting ID to exclude from check
            (useful when updating existing meeting).

    Returns:
        dict[int, list[int]]: Mapping of user_id -> list of conflicting meeting IDs.
    """
    logger.debug(
        "Checking meeting conflicts",
        extra={
            "user_ids": user_ids,
            "start_time": start_time,
            "end_time": end_time,
            "exclude_meeting_id": exclude_meeting_id,
        },
    )
    stmt = (
        select(MeetingParticipant.user_id, Meeting.id)
        .join(Meeting)
        .where(
            MeetingParticipant.user_id.in_(user_ids),
            Meeting.start_time < end_time,
            Meeting.end_time > start_time,
        )
    )

    if exclude_meeting_id is not None:
        stmt = stmt.where(Meeting.id != exclude_meeting_id)

    result = await session.execute(stmt)

    conflicts: dict[int, list[int]] = {}

    for user_id, meeting_id in result.all():
        conflicts.setdefault(user_id, []).append(meeting_id)

    if conflicts:
        logger.warning(
            "Meeting conflicts detected",
            extra={"conflicts": conflicts},
        )
    else:
        logger.debug("No meeting conflicts found")

    return conflicts
