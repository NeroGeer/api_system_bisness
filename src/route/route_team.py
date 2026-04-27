from typing import Annotated

from fastapi import APIRouter, Depends

from src.repositories.crud import crud_team as c_te
from src.scheme.schemas_team import (
    AddTeamMemberSchema,
    TeamMemberResponseSchema,
    TeamResponseSchema,
    UpdateTeamMemberRoleSchema,
)
from src.core.context.base_context import BaseContext, build_context_with_filters


route_team = APIRouter(
    prefix="/api/teams",
    tags=["Teams"],
)


@route_team.get(
    "/{team_id}/members", status_code=200, response_model=TeamResponseSchema
)
async def get_member_team(
        ctx: Annotated[BaseContext, Depends(build_context_with_filters())],
):
    members = await c_te.get_members_team(ctx=ctx)
    return members


@route_team.post(
    "/{team_id}/members", status_code=201, response_model=TeamMemberResponseSchema
)
async def add_member_team(
        ctx: Annotated[BaseContext, Depends(build_context_with_filters())],
        data: AddTeamMemberSchema,
):
    result = await c_te.add_members_team(
        ctx=ctx, data=data
    )
    return result


@route_team.patch(
    "/{team_id}/members/{user_id}",
    status_code=200,
    response_model=TeamMemberResponseSchema,
)
async def update_member_role_in_team_by_id(
        ctx: Annotated[BaseContext, Depends(build_context_with_filters())],
        data: UpdateTeamMemberRoleSchema,
):
    result = await c_te.update_member_role(
        ctx=ctx, data=data,
    )
    return result


@route_team.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
        ctx: Annotated[BaseContext, Depends(build_context_with_filters())],
):
    await c_te.delete_members_team(
        ctx=ctx
    )
    return {"status": "deleted"}
