from collections import defaultdict

from sqlalchemy import select

from src.logger.logger import logger
from src.models.model_meeting import Meeting
from src.models.model_tasks import Task
from src.models.model_team import TeamMember
from src.scheme.schemas_calendar import CalendarDaySchema, CalendarEventSchema
from src.utils.utils import make_date_range, normalize_date_range
from src.core.context.base_context import BaseContext, DateFilter


async def get_calendar(
        ctx: BaseContext[DateFilter]
):
    """
    Author: NeroGeer
    GitHub: https://github.com/NeroGeer
    License: MIT
    Retrieves calendar events (meetings and tasks) for a user within a date range.

    This function aggregates:
        - Meetings from user's teams
        - Tasks from user's teams
        - Groups them by day for calendar view

    Args:
        ctx: BaseContext[DateFilter]
        ctx.current_user (User): Authenticated user.
        ctx.session (SessionDep): Database session.
        ctx.filters.start_date (date | None): Start of date range.
        ctx.filters.end_date (date | None): End of date range.

    Returns:
        list[CalendarDaySchema]: List of days with associated events.
    """

    current_user = ctx.current_user
    session = ctx.session
    start_date = ctx.filters.start_date
    end_date = ctx.filters.end_date

    start_date, end_date = await normalize_date_range(start_date=start_date, end_date=end_date)

    logger.debug(
        f"Building calendar for user_id={current_user.id}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    start_dt, end_dt = await make_date_range(start=start_date, end=end_date)

    logger.debug(f"Resolved datetime range: {start_dt} -> {end_dt}")

    team_ids = (
        await session.scalars(
            select(TeamMember.team_id).where(TeamMember.user_id == current_user.id)
        )
    ).all()

    if not team_ids:
        logger.info(f"No teams found for user_id={current_user.id}")
        return []

    logger.debug(f"User belongs to teams: {team_ids}")

    meetings_stmt = select(Meeting).where(
        Meeting.team_id.in_(team_ids),
        Meeting.start_time <= end_dt,
        Meeting.end_time >= start_dt,
    )

    tasks_stmt = select(Task).where(
        Task.team_id.in_(team_ids), Task.deadline >= start_dt, Task.deadline < end_dt
    )

    meetings = (await session.scalars(meetings_stmt)).all()
    tasks = (await session.scalars(tasks_stmt)).all()

    logger.debug(f"Calendar data loaded: meetings={len(meetings)}, tasks={len(tasks)}")

    events = [
        *[CalendarEventSchema.from_task(t) for t in tasks],
        *[CalendarEventSchema.from_meeting(m) for m in meetings],
    ]

    events_by_day = defaultdict(list)

    for e in events:
        events_by_day[e.start.date()].append(e)

    result = [
        CalendarDaySchema(date=day, events=sorted(day_events, key=lambda x: x.start))
        for day, day_events in sorted(events_by_day.items())
    ]

    logger.info(
        f"Calendar generated for user_id={current_user.id}, "
        f"days={len(result)}, events={len(events)}"
    )

    return result
