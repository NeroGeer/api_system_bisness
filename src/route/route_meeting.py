from typing import Annotated

from fastapi import APIRouter, Depends

from src.repositories.meeting_repository import MeetingRepository
from src.services.meeting_service import MeetingService
from src.scheme.schemas_meeting import (
    MeetingCreateSchema,
    MeetingOutSchema,
    MeetingUpdateSchema,
)
from src.core.context.base_context import (
    BaseContext,
    build_context_with_filters,
    TaskFilter,
    MeetingFilter,
    build_service
)

route_meeting = APIRouter(prefix="/api/teams/{team_id}/meeting", tags=["Meetings"])


@route_meeting.get("", status_code=200, response_model=list[MeetingOutSchema])
async def get_meetings(
        ctx: Annotated[
            BaseContext[TaskFilter],
            Depends(build_context_with_filters(TaskFilter))
        ],
):
    serv_fact = build_service(repository_cls=MeetingRepository,
                              service_cls=MeetingService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.get_meetings_or_meeting_by_id()


@route_meeting.get("/{meeting_id}", status_code=200, response_model=MeetingOutSchema)
async def get_meeting_by_id(
        ctx: Annotated[
            BaseContext[TaskFilter],
            Depends(build_context_with_filters(TaskFilter))
        ],
):
    serv_fact = build_service(repository_cls=MeetingRepository,
                              service_cls=MeetingService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.get_meetings_or_meeting_by_id()


@route_meeting.post("", status_code=201, response_model=MeetingOutSchema)
async def create_meeting(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: MeetingCreateSchema,
):
    serv_fact = build_service(repository_cls=MeetingRepository,
                              service_cls=MeetingService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.create_meeting(data=data)


@route_meeting.put("/{meeting_id}", status_code=200, response_model=MeetingOutSchema)
async def update_meeting_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: MeetingUpdateSchema,
):
    serv_fact = build_service(repository_cls=MeetingRepository,
                              service_cls=MeetingService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.update_meeting(data=data)


@route_meeting.delete("/{meeting_id}/participants", status_code=204)
async def delete_participant_by_meeting_id(
        ctx: Annotated[
            BaseContext[MeetingFilter],
            Depends(build_context_with_filters(MeetingFilter))
        ],
):
    serv_fact = build_service(repository_cls=MeetingRepository,
                              service_cls=MeetingService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.delete_meeting_participant()


@route_meeting.delete("/{meeting_id}", status_code=204)
async def delete_meeting_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
):
    serv_fact = build_service(repository_cls=MeetingRepository,
                              service_cls=MeetingService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.delete_meeting()
