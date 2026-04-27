from typing import Annotated

from fastapi import APIRouter, Depends

from src.repositories.crud import crud_meeting as c_me
from src.scheme.schemas_meeting import (
    MeetingCreateSchema,
    MeetingOutSchema,
    MeetingUpdateSchema,
)
from src.core.context.base_context import (
    BaseContext,
    build_context_with_filters,
    TaskFilter,
    MeetingFilter)

route_meeting = APIRouter(prefix="/api/teams/{team_id}/meeting", tags=["Meetings"])


@route_meeting.get("", status_code=200, response_model=list[MeetingOutSchema])
async def get_meetings(
        ctx: Annotated[
            BaseContext[TaskFilter],
            Depends(build_context_with_filters(TaskFilter))
        ],
):
    return await c_me.get_meeting(
        ctx=ctx
    )


@route_meeting.get("/{meeting_id}", status_code=200, response_model=MeetingOutSchema)
async def get_meeting_by_id(
        ctx: Annotated[
            BaseContext[TaskFilter],
            Depends(build_context_with_filters(TaskFilter))
        ],
):
    return await c_me.get_meeting(
        ctx=ctx
    )


@route_meeting.post("", status_code=201, response_model=MeetingOutSchema)
async def create_meeting(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: MeetingCreateSchema,
):
    return await c_me.create_meeting(
        ctx=ctx, meeting_data=data,
    )


@route_meeting.put("/{meeting_id}", status_code=200, response_model=MeetingOutSchema)
async def update_meeting_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: MeetingUpdateSchema,
):
    return await c_me.update_meeting(
        ctx=ctx,
        data=data,
    )


@route_meeting.delete("/{meeting_id}/participants", status_code=204)
async def delete_participant_by_meeting_id(
        ctx: Annotated[
            BaseContext[MeetingFilter],
            Depends(build_context_with_filters(MeetingFilter))
        ],
):
    return await c_me.delete_meeting_participant(
        ctx=ctx
    )


@route_meeting.delete("/{meeting_id}", status_code=204)
async def delete_meeting_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
):
    return await c_me.delete_meeting_by_id(
        ctx=ctx
    )
