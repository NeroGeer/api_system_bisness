from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.core.security import dependencies as jwt
from src.database.database import SessionDep
from src.models.model_user import User
from src.repositories.crud import crud_meeting as c_me
from src.scheme.schemas_meeting import (
    MeetingCreateSchema,
    MeetingOutSchema,
    MeetingUpdateSchema,
)

route_meeting = APIRouter(prefix="/api/teams/{team_id}/meeting", tags=["Meetings"])


@route_meeting.get("", status_code=200, response_model=list[MeetingOutSchema])
async def get_meetings(
    team_id: int,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    only_my_meetings: bool = Query(False),
    participant_user_id: int | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await c_me.get_meeting(
        current_user=current_user,
        team_id=team_id,
        session=session,
        only_my_meetings=only_my_meetings,
        participant_user_id=participant_user_id,
        start_date=start_date,
        end_date=end_date,
    )


@route_meeting.get("/{meeting_id}", status_code=200, response_model=MeetingOutSchema)
async def get_meeting_by_id(
    team_id: int,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    meeting_id: int,
):
    return await c_me.get_meeting(
        current_user=current_user,
        team_id=team_id,
        session=session,
        meeting_id=meeting_id,
    )


@route_meeting.post("", status_code=201, response_model=MeetingOutSchema)
async def create_meeting(
    team_id: int,
    data: MeetingCreateSchema,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
):
    return await c_me.create_meeting(
        current_user=current_user, meeting_data=data, team_id=team_id, session=session
    )


@route_meeting.put("/{meeting_id}", status_code=200, response_model=MeetingOutSchema)
async def update_meeting_by_id(
    team_id: int,
    meeting_id: int,
    data: MeetingUpdateSchema,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
):
    return await c_me.update_meeting(
        current_user=current_user,
        data=data,
        team_id=team_id,
        meeting_id=meeting_id,
        session=session,
    )


@route_meeting.delete("/{meeting_id}/participants", status_code=204)
async def delete_participant_by_meeting_id(
    team_id: int,
    meeting_id: int,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    users_ids: list[int] = Query(...),
):
    return await c_me.delete_meeting_participant(
        current_user=current_user,
        team_id=team_id,
        users_ids=users_ids,
        meeting_id=meeting_id,
        session=session,
    )


@route_meeting.delete("/{meeting_id}", status_code=204)
async def delete_meeting_by_id(
    team_id: int,
    meeting_id: int,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
):
    return await c_me.delete_meeting_by_id(
        current_user=current_user,
        team_id=team_id,
        meeting_id=meeting_id,
        session=session,
    )
