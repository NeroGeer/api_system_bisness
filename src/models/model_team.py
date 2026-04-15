from typing import List

from sqlalchemy import String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.model_base import Base
from src.models.model_user import User


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    invite_code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    members: Mapped[List["TeamMember"]] = relationship(back_populates="team", lazy="selectin")


class TeamMember(Base):
    __tablename__ = "team_members"

    __table_args__ = (
        UniqueConstraint("user_id", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))

    role: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None
    )

    user: Mapped["User"] = relationship(back_populates="team_memberships", lazy="selectin")
    team: Mapped["Team"] = relationship(back_populates="members", lazy="selectin")
