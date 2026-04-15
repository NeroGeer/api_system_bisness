from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum

from src.core.scheme.scheme_user.schemas_user import UserShortSchema


class TeamRole(str, Enum):
    employee = "employee"
    manager = "manager"


class TeamRoleSchema(BaseModel):
    role: Optional[str] = None


class TeamSchema(BaseModel):
    id: int
    name: str


class UpdateTeamMemberRoleSchema(BaseModel):
    role: str


class AddTeamMemberSchema(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.employee


class TeamMemberSchema(BaseModel):
    team: TeamSchema
    role: Optional[str] = None

    class Config:
        from_attributes = True


class CurrentTeamSchema(BaseModel):
    id: int
    name: str
    role: Optional[str] = None


class InviteTeamSchema(BaseModel):
    invite_code: str


class TeamMemberResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    user: UserShortSchema


class TeamResponseSchema(BaseModel):
    id: int
    name: str
    members: list[TeamMemberResponseSchema]
