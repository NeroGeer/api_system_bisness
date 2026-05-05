from typing import Annotated, List

from fastapi import APIRouter, Depends

from src.scheme.schemas_calendar import CalendarDaySchema
from src.core.context.base_context import BaseContext, build_context_with_filters, DateFilter, build_service
from src.services.calendar_service import CalendarService
from src.repositories.calendar_repository import CalendarRepository


route_calendar = APIRouter(
    prefix="/api/calendar",
    tags=["Calendar"],
)


@route_calendar.get("", status_code=200, response_model=List[CalendarDaySchema])
async def get_calendar(
        ctx: Annotated[BaseContext[DateFilter], Depends(build_context_with_filters(DateFilter))]
):
    serv_fact = build_service(repository_cls=CalendarRepository, service_cls=CalendarService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.get_calendar()
