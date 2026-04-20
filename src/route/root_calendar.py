from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from src.core.security import dependencies as jwt
from src.database.database import SessionDep
from src.models.model_user import User
from src.repositories.crud import crud_calendar as c_cl
from src.scheme.schemas_calendar import CalendarDaySchema

route_calendar = APIRouter(
    prefix="/api/calendar",
    tags=["Calendar"],
)


@route_calendar.get("", status_code=200, response_model=List[CalendarDaySchema])
async def get_calendar(
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await c_cl.get_calendar(
        session=session,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )
