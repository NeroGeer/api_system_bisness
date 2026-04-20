import pytest
from datetime import date, datetime, UTC

from src.utils.utils import make_date_range


@pytest.mark.asyncio
async def test_make_date_range_basic():
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    start_dt, end_dt = await make_date_range(start, end)

    assert start_dt == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert end_dt == datetime(2026, 1, 4, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_make_date_range_single_day():
    start = date(2026, 5, 10)
    end = date(2026, 5, 10)

    start_dt, end_dt = await make_date_range(start, end)

    assert start_dt == datetime(2026, 5, 10, 0, 0, tzinfo=UTC)
    assert end_dt == datetime(2026, 5, 11, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_make_date_range_end_is_exclusive():
    start = date(2026, 1, 1)
    end = date(2026, 1, 1)

    _, end_dt = await make_date_range(start, end)

    # должно быть начало следующего дня
    assert end_dt == datetime(2026, 1, 2, 0, 0, tzinfo=UTC)