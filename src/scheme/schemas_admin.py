from pydantic import BaseModel, Field, EmailStr

from typing import List, Optional

from src.scheme.schemas_team import TeamSchema


class TeamMemberShortSchema(BaseModel):
    team_id: int
    team_name: str
    role: Optional[str] = None

    class Config:
        from_attributes = True


class AdminScheme(BaseModel):
    id: int
    email: EmailStr
    roles: List[str] = []

    current_team: Optional[TeamSchema] = None
    team_memberships: List[TeamMemberShortSchema] = Field(default_factory=list)


class AdminTeamCrateSchema(BaseModel):
    name: str
    invite_code: str


class OutAdminTeamCrateSchema(BaseModel):
    id: int
    name: str
    invite_code: str
