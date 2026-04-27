from typing import Annotated, List

from fastapi import APIRouter, Depends

from src.repositories.crud import crud_calendar as c_cl
from src.scheme.schemas_calendar import CalendarDaySchema
from src.core.context.base_context import BaseContext, build_context_with_filters, DateFilter

route_calendar = APIRouter(
    prefix="/api/calendar",
    tags=["Calendar"],
)


@route_calendar.get("", status_code=200, response_model=List[CalendarDaySchema])
async def get_calendar(
        ctx: Annotated[BaseContext[DateFilter], Depends(build_context_with_filters(DateFilter))]
):
    return await c_cl.get_calendar(
        ctx=ctx
    )
