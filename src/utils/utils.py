from datetime import date, datetime, time, UTC, timedelta


async def make_date_range(start: date, end: date):
    start_dt = datetime.combine(start, time.min, tzinfo=UTC)
    end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC)
    return start_dt, end_dt
