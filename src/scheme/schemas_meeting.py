from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import List, Optional


class MeetingCreateSchema(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)

    start_time: datetime
    end_time: datetime

    participants: Optional[List[int]] | None = None

    @model_validator(mode="after")
    def validate_time(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class MeetingParticipantOutSchema(BaseModel):
    user_id: int

    class Config:
        from_attributes = True


class MeetingParticipantsDeleteSchema(BaseModel):
    users_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of user IDs to remove from meeting"
    )


class MeetingOutSchema(BaseModel):
    id: int
    team_id: int
    creator_id: int

    title: str
    description: str

    start_time: datetime
    end_time: datetime
    created_at: datetime

    participants: list[MeetingParticipantOutSchema]

    class Config:
        from_attributes = True


class MeetingUpdateSchema(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    participants: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_time(self):
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
        return self
