from fastapi import APIRouter, Depends

from typing import Annotated

from src.database.database import SessionDep
from src.route.crud import crud_admin as c_ad
from src.core.models.model_user.models import User
from src.core.scheme.admin_scheme.schemas_admin import AdminScheme, AdminTeamCrateSchema, OutAdminTeamCrateSchema
from src.core.jwt_hash.jwt_auth import require_permission

route_admin = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
)


@route_admin.get("", status_code=200, response_model=AdminScheme, tags=["Get Admin"])
async def admin_panel(current_user: Annotated[User, Depends(require_permission("admin.panel.access"))]):
    return current_user


@route_admin.post("/create-team", status_code=201, response_model=OutAdminTeamCrateSchema, tags=["Create Team by Admin"])
async def admin_panel_create_team(session: SessionDep,
                                  current_user: Annotated[User, Depends(require_permission("admin.panel.access"))],
                                  data: AdminTeamCrateSchema):
    result = await c_ad.create_team(session=session, data=data)
    return result


