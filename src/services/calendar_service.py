from collections import defaultdict

from src.logger.logger import logger
from src.scheme.schemas_calendar import CalendarDaySchema, CalendarEventSchema
from src.utils.utils import make_date_range, normalize_date_range


class CalendarService:
    def __init__(self, repo, context=None):
        self.repo = repo
        self.ctx = context

    async def get_calendar(self):
        """
        Author: NeroGeer
        GitHub: https://github.com/NeroGeer
        License: MIT
        Retrieves calendar events (meetings and tasks) for a user within a date range.

        This function aggregates:
            - Meetings from user's teams
            - Tasks from user's teams
            - Groups them by day for calendar view
        Returns:
            list[CalendarDaySchema]: List of days with associated events.
        """

        user_id = self.ctx.current_user.id
        start_date = self.ctx.filters.start_date
        end_date = self.ctx.filters.end_date

        logger.debug(
            f"Building calendar for user_id={user_id}, "
            f"start_date={start_date}, end_date={end_date}"
        )

        start_date, end_date = await normalize_date_range(start_date=start_date, end_date=end_date)
        start_dt, end_dt = await make_date_range(start=start_date, end=end_date)

        logger.debug(f"Resolved datetime range: {start_dt} -> {end_dt}")

        teams_ids = await self.repo.get_teams_ids(user_id=user_id)

        if not teams_ids:
            logger.info(f"No teams found for user_id={user_id}")
            return teams_ids

        logger.debug(f"User belongs to teams: {teams_ids}")

        meetings = await self.repo.get_meetings(teams_ids=teams_ids, start_dt=start_dt, end_dt=end_dt)
        tasks = await self.repo.get_tasks(teams_ids=teams_ids, start_dt=start_dt, end_dt=end_dt)

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

        logger.debug(
            f"Calendar generated for user_id={user_id}, "
            f"days={len(result)}, events={len(events)}"
        )

        return result
