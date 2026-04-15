from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum

from src.core.scheme.scheme_team.schemas_team import TeamMemberSchema, CurrentTeamSchema


class UserRole(str, Enum):
    admin = "admin"
    user = "user"

class BaseUserSchema(BaseModel):
    """
    Schema representing the basic user structure.

    Attributes:
        id (int):
            Unique identifier of the user.
    """
    id: int


class CreateUserScheme(BaseModel):

    email: EmailStr
    password: str


class OutCreateUserScheme(BaseUserSchema):

    email: EmailStr
    roles: List[str] = Field(default_factory=list)


class LoginUserScheme(BaseUserSchema):
    email: EmailStr
    roles: List[str] = Field(default_factory=list)

    current_team: Optional[CurrentTeamSchema] = None
    teams: List[TeamMemberSchema] = Field(default_factory=list)


class UpdateUserScheme(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserShortSchema(BaseModel):
    id: int
    email: str
