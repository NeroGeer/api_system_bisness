from fastapi import APIRouter, Depends

from typing import Annotated

from src.database.database import SessionDep
from src.repositories.crud import crud_admin as c_ad
from src.models.model_user import User
from src.scheme.schemas_admin import AdminScheme, AdminTeamCrateSchema, OutAdminTeamCrateSchema
from src.core.security.rbac import require_permission

route_admin = APIRouter(
    prefix="/api/admin",
    tags=["Admins"],
)


@route_admin.get("", status_code=200, response_model=AdminScheme)
async def admin_panel(current_user: Annotated[User, Depends(require_permission("admin.panel.access"))]):
    return current_user


@route_admin.post("/create-team", status_code=201,
                  response_model=OutAdminTeamCrateSchema)
async def admin_panel_create_team(session: SessionDep,
                                  current_user: Annotated[User, Depends(require_permission("admin.panel.access"))],
                                  data: AdminTeamCrateSchema):
    result = await c_ad.create_team(session=session, data=data)
    return result
