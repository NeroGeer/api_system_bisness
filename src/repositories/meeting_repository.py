from datetime import datetime, date

from sqlalchemy import select, exists, and_, delete

from src.models.model_team import TeamMember
from sqlalchemy.orm import selectinload

from src.database.database import SessionDep
from src.models.model_meeting import Meeting, MeetingParticipant
from src.models.model_user import User


class MeetingRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    async def validate_conflicts(
            self,
            user_ids: list[int],
            start_time: datetime,
            end_time: datetime,
            exclude_meeting_id: int | None = None,
    ):

        stmt = (
            select(MeetingParticipant.user_id, Meeting.id)
            .join(Meeting)
            .where(
                MeetingParticipant.user_id.in_(user_ids),
                Meeting.start_time < end_time,
                Meeting.end_time > start_time,
            )
        )

        if exclude_meeting_id is not None:
            stmt = stmt.where(Meeting.id != exclude_meeting_id)

        return (await self.session.execute(stmt)).all()

    async def validate_meeting(self, participants_set: set[int], team_id: int):

        stmt = (
            select(User.id, TeamMember.user_id)
            .outerjoin(
                TeamMember,
                (TeamMember.user_id == User.id) & (TeamMember.team_id == team_id),
            )
            .where(User.id.in_(participants_set))
        )

        return await self.session.execute(stmt)

    async def validate_team(
            self,
            user_id: int,
            team_id: int,
    ) -> bool:

        return await self.session.scalar(select(
            exists().where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        ))

    async def get_by_id(
        self, team_id: int, meeting_id: int | None = None
    ) -> Meeting | None:

        stmt = (
            select(Meeting)
            .where(Meeting.team_id == team_id)
            .options(selectinload(Meeting.participants))
        )

        if meeting_id is not None:
            stmt = stmt.where(Meeting.id == meeting_id)

        return await self.session.scalar(stmt)

    async def get(
            self,
            team_id: int,
            participant_user_id: int | None = None,
            start_dt: date | None = None,
            end_dt: date | None = None,
    ):
        stmt = (
            select(Meeting).where(Meeting.team_id == team_id).order_by(Meeting.start_time)
        )
        if start_dt is not None and end_dt is not None:
            stmt = stmt.where(
                and_(Meeting.start_time <= end_dt, Meeting.end_time >= start_dt)
            )

        if participant_user_id is not None:
            stmt = stmt.where(
                Meeting.participants.any(MeetingParticipant.user_id == participant_user_id)
            )

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def create(self, meeting: Meeting, participants_set: set[int]):
        self.session.add(meeting)
        await self.session.flush()

        for user_id in participants_set:
            self.session.add(MeetingParticipant(meeting_id=meeting.id, user_id=user_id))

        await self.session.commit()
        await self.session.refresh(meeting)

    async def update(self, meeting: Meeting, to_add: set[int]):

        if to_add is not None:
            for user_id in to_add:
                self.session.add(MeetingParticipant(
                    meeting_id=meeting.id, user_id=user_id
                )
                )

        await self.session.commit()
        await self.session.refresh(meeting)

    async def delete_participant(self, meeting_id: int, to_remove: set):
        await self.session.execute(
            delete(MeetingParticipant).where(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id.in_(to_remove),
            )
        )
        await self.session.commit()

    async def delete(self, meeting: Meeting):
        await self.session.delete(meeting)
        await self.session.commit()
