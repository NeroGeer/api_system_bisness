from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from enum import Enum

from src.scheme.schemas_team import TeamMemberSchema, CurrentTeamSchema


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
    password: str = Field(..., min_length=8, max_length=72)


    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain a lowercase letter")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>/?`~" for c in v):
            raise ValueError('Password must contain a special symbol')

        return v


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
