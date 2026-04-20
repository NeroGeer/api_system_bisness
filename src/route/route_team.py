from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.security.rbac import require_role
from src.database.database import SessionDep
from src.models.model_user import User
from src.repositories.crud import crud_team as c_te
from src.scheme.schemas_team import (
    AddTeamMemberSchema,
    TeamMemberResponseSchema,
    TeamResponseSchema,
    UpdateTeamMemberRoleSchema,
)
from src.scheme.schemas_user import UserRole
from src.services.team_service import require_team_manager_or_admin

route_team = APIRouter(
    prefix="/api/teams",
    tags=["Teams"],
)


@route_team.get(
    "/{team_id}/members", status_code=200, response_model=TeamResponseSchema
)
async def get_member_team(
    session: SessionDep,
    team_id: int,
    current_user: Annotated[User, Depends(require_team_manager_or_admin())],
):
    members = await c_te.get_members_team(session=session, team_id=team_id)
    return members


@route_team.post(
    "/{team_id}/members", status_code=201, response_model=TeamMemberResponseSchema
)
async def add_member_team(
    team_id: int,
    data: AddTeamMemberSchema,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_team_manager_or_admin())],
):
    result = await c_te.add_members_team(
        session=session, team_id=team_id, data=data, user=current_user
    )
    return result


@route_team.patch(
    "/{team_id}/members/{user_id}",
    status_code=200,
    response_model=TeamMemberResponseSchema,
)
async def update_member_role_in_team_by_id(
    team_id: int,
    user_id: int,
    data: UpdateTeamMemberRoleSchema,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_role({UserRole.admin}))],
):
    result = await c_te.update_member_role(
        session=session, team_id=team_id, data=data, user_id=user_id
    )
    return result


@route_team.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
    team_id: int,
    user_id: int,
    session: SessionDep,
    user: Annotated[User, Depends(require_team_manager_or_admin())],
):
    await c_te.delete_members_team(
        session=session, user=user, team_id=team_id, user_id=user_id
    )
    return {"status": "deleted"}
