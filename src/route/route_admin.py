from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.context.base_context import BaseContext, build_context_with_filters, build_service
from src.repositories.team_repository import TeamRepository
from src.services.team_service import TeamService
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
    ctx.require_permission(permission="admin.panel.access")
    serv_fact = build_service(repository_cls=TeamRepository, service_cls=TeamService,
                              session=ctx.session, ctx=ctx)
    result = await serv_fact.create_team(data=data)

    return result
