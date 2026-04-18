from typing import List, TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.model_base import Base
from src.scheme.schemas_team import TeamRole

if TYPE_CHECKING:
    from src.models.model_user import User


class Team(Base):
    """
    Database model representing a team.

    A team is a logical group of users that can collaborate on tasks,
    meetings, and other resources within the system.

    Attributes:
        id (int):
            Primary key identifier of the team.

        name (str):
            Unique team name.

        invite_code (str):
            Unique code used for joining the team.

        members (List[TeamMember]):
            List of users who are members of the team.
    """
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    invite_code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    members: Mapped[List["TeamMember"]] = relationship(back_populates="team", lazy="selectin")

    def __repr__(self):
        return f"Team name - ({self.name})"


class TeamMember(Base):
    """
    Association model representing a user membership in a team.

    This model implements a many-to-many relationship between users and teams,
    with an additional role field defining permissions inside the team.

    Attributes:
        id (int):
            Primary key identifier.

        user_id (int):
            Reference to the user.

        team_id (int):
            Reference to the team.

        role (TeamRole):
            Role of the user within the team (e.g. ADMIN, MEMBER).

        user (User):
            Relationship to the user entity.

        team (Team):
            Relationship to the team entity.
    """
    __tablename__ = "team_members"

    __table_args__ = (
        UniqueConstraint("user_id", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))

    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole),
        nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="team_memberships", lazy="selectin")
    team: Mapped["Team"] = relationship(back_populates="members", lazy="selectin")

    def __repr__(self):
        return f"Email user - {self.user.email}  Team name - ({self.team.name})"
