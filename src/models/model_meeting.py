from sqlalchemy import String, ForeignKey, DateTime, event, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from typing import List, TYPE_CHECKING

from datetime import datetime, UTC

from src.models.model_base import Base

if TYPE_CHECKING:
    from src.models.model_user import User


class Meeting(Base):
    """
    Database model representing a team meeting.

    A meeting belongs to a team and is created by a user.
    It can have multiple participants, including the creator.

    Attributes:
        id (int):
            Primary key identifier of the meeting.

        team_id (int):
            Reference to the team where the meeting is created.

        creator_id (int):
            User who created the meeting.

        title (str):
            Title of the meeting.

        description (str):
            Detailed description of the meeting.

        start_time (datetime):
            Meeting start timestamp (timezone-aware).

        end_time (datetime):
            Meeting end timestamp (timezone-aware).

        created_at (datetime):
            Timestamp when the meeting was created.

        creator (User):
            Relationship to the user who created the meeting.

        participants (List[MeetingParticipant]):
            List of users participating in the meeting.
    """
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_meetings",
        lazy="selectin"
    )
    participants: Mapped[List["MeetingParticipant"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"Meeting {self.title} time:({self.start_time})"


class MeetingParticipant(Base):
    """
    Association table for users participating in meetings.

    Represents many-to-many relationship between users and meetings.

    Constraints:
        - A user can join a meeting only once (unique constraint).
    """
    __tablename__ = "meeting_participants"

    __table_args__ = (
        UniqueConstraint("meeting_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE")
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(
        back_populates="meeting_participations",
        lazy="selectin"
    )

    def __repr__(self):
        return f"User email{self.user.email} -> Meeting - {self.meeting.title}"


@event.listens_for(Meeting, "before_insert")
def set_team_id(mapper, connection, target):
    """
    Automatically assigns a team to the meeting based on creator membership
    if team_id is not explicitly provided.
    """
    if target.team_id is not None:
        return

    result = connection.execute(
        """
        SELECT team_id 
        FROM team_members 
        WHERE user_id = :user_id 
        LIMIT 1
        """,
        {"user_id": target.creator_id},
    ).fetchone()

    if result:
        target.team_id = result[0]
