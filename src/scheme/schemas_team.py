from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeamRole(str, Enum):
    employee = "employee"
    manager = "manager"


class TeamSchema(BaseModel):
    id: int
    name: str


class UpdateTeamMemberRoleSchema(BaseModel):
    role: TeamRole


class AddTeamMemberSchema(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.employee


class TeamMemberSchema(BaseModel):
    team: TeamSchema
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CurrentTeamSchema(BaseModel):
    id: int
    name: str
    role: Optional[str] = None


class TeamUserShortSchema(BaseModel):
    id: int
    email: str


class TeamMemberResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    user: TeamUserShortSchema


class TeamResponseSchema(BaseModel):
    id: int
    name: str
    members: list[TeamMemberResponseSchema]

    model_config = ConfigDict(from_attributes=True)
