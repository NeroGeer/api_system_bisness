from sqlalchemy import String, ForeignKey, Column, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column

from typing import List

from src.core.models.model_base import Base
from src.core.models.model_team.models import TeamMember
from src.core.models.model_meeting.models import Meeting, MeetingParticipant

from dataclasses import dataclass


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE")),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE")),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE")),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True)

    team_memberships: Mapped[List["TeamMember"]] = relationship(back_populates="user", lazy="selectin")

    roles: Mapped[List["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )

    created_meetings: Mapped[List["Meeting"]] = relationship(
        back_populates="creator",
        lazy="selectin"
    )

    meeting_participations: Mapped[List["MeetingParticipant"]] = relationship(
        back_populates="user",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.email})"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    users: Mapped[List["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin"
    )

    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Role(name={self.name})"


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    roles: Mapped[List["Role"]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Permission(name={self.name})"


@dataclass
class PermissionResult:
    is_admin: bool
    is_team_role: bool
    is_executor: bool
