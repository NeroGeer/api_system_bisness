from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.context.base_context import BaseContext, build_context_with_filters
from src.repositories.crud import crud_admin as c_ad
from src.scheme.schemas_admin import (
    AdminScheme,
    AdminTeamCrateSchema,
    OutAdminTeamCrateSchema,
)

route_admin = APIRouter(
    prefix="/api/admin",
    tags=["Admins"],
)


@route_admin.get("", status_code=200, response_model=AdminScheme)
async def admin_panel(
    ctx: Annotated[BaseContext, Depends(build_context_with_filters())],
):
    ctx.require_permission(permission="admin.panel.access")
    return ctx.current_user


@route_admin.post(
    "/create-team", status_code=201, response_model=OutAdminTeamCrateSchema
)
async def admin_panel_create_team(
    ctx: Annotated[BaseContext, Depends(build_context_with_filters())],
    data: AdminTeamCrateSchema,
):
    result = await c_ad.create_team(ctx=ctx, data=data)
    return result
