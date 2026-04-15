from datetime import datetime

from sqlalchemy import select

from src.database.database import SessionDep
from src.models.model_meeting import MeetingParticipant, Meeting


async def check_meeting_conflicts(
        session: SessionDep,
        user_ids: list[int],
        start_time: datetime,
        end_time: datetime,
        exclude_meeting_id: int | None = None,
):
    stmt = (
        select(
            MeetingParticipant.user_id,
            Meeting.id
        )
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

    return conflicts
