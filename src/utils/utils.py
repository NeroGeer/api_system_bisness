from datetime import UTC, date, datetime, time, timedelta


async def normalize_date_range(
    start_date: date | None,
    end_date: date | None,
) -> tuple[date, date]:
    today = date.today()

    if start_date is None and end_date is None:
        return today, today

    if start_date is None:
        return end_date, end_date

    if end_date is None:
        return start_date, start_date

    return start_date, end_date


async def make_date_range(start: date, end: date):
    start_dt = datetime.combine(start, time.min, tzinfo=UTC)
    end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC)
    return start_dt, end_dt
