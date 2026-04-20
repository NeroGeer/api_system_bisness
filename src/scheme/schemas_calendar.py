from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CalendarEventSchema(BaseModel):
    id: int
    type: Literal["task", "meeting"]

    title: str

    start: datetime
    end: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_task(cls, task):
        return cls(
            id=task.id,
            type="task",
            title=(task.description or "").split("\n")[0][:50],
            start=task.deadline,
            end=None,
        )

    @classmethod
    def from_meeting(cls, meeting):
        return cls(
            id=meeting.id,
            type="meeting",
            title=meeting.title,
            start=meeting.start_time,
            end=meeting.end_time,
        )


class CalendarDaySchema(BaseModel):
    date: date
    events: list[CalendarEventSchema]
