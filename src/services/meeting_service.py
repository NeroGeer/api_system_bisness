from datetime import datetime

from src.exceptions import exceptions as c_exp
from src.models.model_user import PermissionResult

from src.logger.logger import logger
from src.models.model_meeting import Meeting
from src.scheme.schemas_meeting import MeetingCreateSchema, MeetingUpdateSchema
from src.scheme.schemas_team import TeamRole
from src.utils.utils import make_date_range


class MeetingService:
    def __init__(self, repo, context=None):
        self.repo = repo
        self.ctx = context

    async def validate_meeting_conflicts(
            self,
            user_ids: list[int],
            start_time: datetime,
            end_time: datetime,
            exclude_meeting_id: int | None = None,
    ):
        """
        Checks for scheduling conflicts between users and existing meetings.

        A conflict occurs when a user is already assigned to a meeting
        that overlaps with the provided time range.

        Returns:
            dict[int, list[int]]: Mapping of user_id -> list of conflicting meeting IDs.
        """
        logger.debug(
            "Checking meeting conflicts",
            extra={
                "user_ids": user_ids,
                "start_time": start_time,
                "end_time": end_time,
                "exclude_meeting_id": exclude_meeting_id,
            },
        )

        result = await self.repo.validate_conflicts(
            user_ids=user_ids,
            start_time=start_time,
            end_time=end_time,
            exclude_meeting_id=exclude_meeting_id,
        )

        conflicts: dict[int, list[int]] = {}

        for user_id, meeting_id in result:
            conflicts.setdefault(user_id, []).append(meeting_id)

        if conflicts:
            logger.warning(
                "Meeting conflicts detected",
                extra={"conflicts": conflicts},
            )
            raise c_exp.MeetingConflictError(f"Users already have meetings: {conflicts}")

    async def validate_meeting_data(
            self,
            team_id: int,
            user_id: int,
            result_perm: PermissionResult,
            participants_set: set[int] | None = None,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
    ):
        """
        Validates meeting creation or update rules.

        Ensures:
        - creator belongs to the team (if not admin)
        - participants exist in DB
        - participants belong to the team
        - participants have no meeting conflicts (if time range provided)
        """

        logger.debug(f"Validating meeting data: team_id={team_id},"
                     f" creator_id={user_id}")

        if not result_perm.is_admin:
            if not await self.validate_user_team(user_id=user_id, team_id=team_id):
                logger.warning(
                    f"Creator not in team: user_id={user_id}, team_id={team_id}"
                )
                raise c_exp.CreatorNotFoundInTeamError()

        if participants_set is None or not participants_set:
            logger.debug("No participants provided for validation")
            return

        rows = await self.repo.validate_meeting(participants_set=participants_set, team_id=team_id)

        existing_users = set()
        team_users = set()

        for user_id, team_user_id in rows:
            existing_users.add(user_id)
            if team_user_id is not None:
                team_users.add(user_id)

        missing_users = participants_set - existing_users
        if missing_users:
            logger.warning(f"Missing users in system: {missing_users}")
            raise c_exp.UserNotFoundError(f"Users not found: {missing_users}")

        invalid_users = participants_set - team_users
        if invalid_users:
            logger.warning(f"Users not in team: team_id={team_id}, users={invalid_users}")
            raise c_exp.MemberNotFoundError(f"Users not in team: {invalid_users}")

        if start_time and end_time:
            logger.debug(f"Checking meeting conflicts: users={participants_set}")
            await self.validate_meeting_conflicts(
                user_ids=list(participants_set),
                start_time=start_time,
                end_time=end_time,
            )

        logger.debug("Meeting validation passed successfully")

    async def validate_user_team(self, user_id: int, team_id: int):
        """
        Checks whether a user is a member of a given team.
        """
        if not await self.repo.validate_team(
                user_id=user_id,
                team_id=team_id
        ):
            raise c_exp.ExecutorNotFoundInTeamError()

    async def get_meeting(
        self, team_id: int, meeting_id: int
    ) -> Meeting | None:
        """
        Fetches a meeting by ID with participants loaded.

        Returns:
            Meeting: Meeting instance.

        Raises:
            HTTPException: If meeting not found.
        """

        meeting = await self.repo.get_by_id(team_id=team_id, meeting_id=meeting_id)

        if meeting is None:
            logger.warning(f"Meeting not found: meeting_id={meeting_id}")
            raise c_exp.MeetingNotFoundError()

        return meeting

    async def get_meetings_or_meeting_by_id(self):
        """
        Retrieves meetings for a team with optional filters.

        Supports:
            - single meeting fetch
            - date range filtering
            - filtering by participant
            - filtering by current user participation
        """

        user_id = self.ctx.current_user.id
        team_id = self.ctx.scope.team_id
        meeting_id = self.ctx.scope.meeting_id
        only_my_meetings = self.ctx.filters.only_my
        participant_user_id = self.ctx.filters.executor_user_id
        start_date = self.ctx.filters.start_date
        end_date = self.ctx.filters.end_date

        logger.debug(f"Fetching meetings: user_id={user_id}, team_id={team_id}")

        await self.ctx.require_admin_or_team_role_or_executor(
            team_role={TeamRole.manager, TeamRole.employee}
        )

        if meeting_id is not None:
            return await self.get_meeting(team_id=team_id, meeting_id=meeting_id)

        if start_date is not None and end_date is not None:
            start_date, end_date = await make_date_range(start_date, end_date)

        if only_my_meetings and participant_user_id is not None:
            raise c_exp.ConflictingFiltersError()

        if only_my_meetings:
            participant_user_id = user_id

        if participant_user_id is not None:
            await self.validate_user_team(
                user_id=participant_user_id,
                team_id=team_id
            )

        result = await self.repo.get(
            team_id=team_id,
            executor_user_id=participant_user_id,
            start_dt=start_date, end_dt=end_date)

        return result

    async def create_meeting(
        self,
        data: MeetingCreateSchema,
    ):
        """
        Creates a new meeting and assigns participants.

        Performs:
            - permission validation
            - participant validation
            - conflict checks (via service layer)
        """

        user_id = self.ctx.current_user.id
        team_id = self.ctx.scope.team_id

        logger.info(f"Create meeting: user_id={user_id}, team_id={team_id}")
        result_perm = await self.ctx.require_admin_or_team_role_or_executor()

        participants_set: set[int] = set(data.participants or [])

        await self.validate_meeting_data(
            team_id=team_id,
            user_id=user_id,
            participants_set=participants_set,
            result_perm=result_perm,
            start_time=data.start_time,
            end_time=data.end_time,
        )

        meeting = Meeting(
            creator_id=user_id,
            team_id=team_id,
            start_time=data.start_time,
            end_time=data.end_time,
            title=data.title,
            description=data.description,
        )

        await self.repo.create(meeting=meeting, participants_set=participants_set)
        return meeting

    async def update_meeting(
        self,
        data: MeetingUpdateSchema,
    ):
        """
        Updates meeting data including:
            - title
            - description
            - participants
            - time range

        Performs:
            - permission check (admin / creator)
            - participant validation
            - time conflict validation
        """

        user_id = self.ctx.current_user
        team_id = self.ctx.scope.team_id
        meeting_id = self.ctx.scope.meeting_id

        result_perm = await self.ctx.require_admin_or_team_role_or_executor()

        logger.debug(
            f"Updating meeting: meeting_id={meeting_id}, user_id={user_id}"
        )
        if not data or data is None:
            raise c_exp.EmptyDataError()

        meeting = await self.repo.get_by_id(meeting_id=meeting_id, team_id=team_id)

        new_start = data.start_time or meeting.start_time
        new_end = data.end_time or meeting.end_time

        if new_end <= new_start:
            raise c_exp.InvalidTimeRangeError()

        if not result_perm.is_admin and meeting.creator_id != user_id:
            logger.warning(
                f"Unauthorized meeting update attempt: "
                f"user_id={user_id}, meeting_id={meeting_id}"
            )
            raise c_exp.PermissionDeniedError()

        if data.title is not None:
            meeting.title = data.title

        if data.description is not None:
            meeting.description = data.description

        if data.participants is not None:

            to_add = set(data.participants) - {p.user_id for p in meeting.participants}
            logger.debug(f"Participants update: meeting_id={meeting_id}, to_add={to_add}")
            if to_add:
                await self.validate_meeting_data(
                    team_id=team_id,
                    user_id=user_id,
                    participants_set=to_add,
                    result_perm=result_perm,
                    start_time=new_start,
                    end_time=new_end,
                )
        else:
            to_add = None

        if data.start_time is not None or data.end_time is not None:
            participant_ids = [p.user_id for p in meeting.participants]

            await self.validate_meeting_conflicts(
                user_ids=participant_ids,
                start_time=new_start,
                end_time=new_end,
                exclude_meeting_id=meeting.id,
            )

            meeting.start_time = new_start
            meeting.end_time = new_end

        await self.repo.update(meeting=meeting, to_add=to_add)

        logger.info(f"Meeting updated: meeting_id={meeting.id}")

        return meeting

    async def delete_meeting_participant(self):
        """
        Removes participants from a meeting.

        Returns:
            dict: Meeting ID and removed participants.
        """

        user_id = self.ctx.current_user.id
        team_id = self.ctx.scope.team_id
        meeting_id = self.ctx.scope.meeting_id
        users_ids = self.ctx.filters.users_ids

        result_perm = await self.ctx.require_admin_or_team_role_or_executor()

        logger.debug(
            f"Removing participants: meeting_id={meeting_id}, user_id={user_id}"
        )

        if not users_ids:
            raise c_exp.EmptyDataError()

        meeting = await self.get_meeting(meeting_id=meeting_id, team_id=team_id)

        if not result_perm.is_admin and meeting.creator_id != user_id:
            logger.warning(
                f"Unauthorized participant delete attempt: "
                f"user_id={user_id}, meeting_id={meeting_id}"
            )
            raise c_exp.PermissionDeniedError()

        to_remove = set(users_ids)
        missing = to_remove - {p.user_id for p in meeting.participants}

        if missing:
            raise c_exp.MemberNotFoundError(f"Users not in TeamMeeting: {missing}")

        await self.repo.delete_participant(meeting_id=meeting_id, to_remove=to_remove)

        logger.warning(
            f"Participants removed: meeting_id={meeting_id}, users={list(to_remove)}"
        )

        return {
            "meeting_id": meeting.id,
            "removed_participants": list(to_remove),
        }

    async def delete_meeting(self):
        """
        Deletes a meeting and all related participants.

        Returns:
            dict: Confirmation message and deleted meeting info.
        """

        user_id = self.ctx.current_user
        team_id = self.ctx.scope.team_id
        meeting_id = self.ctx.scope.meeting_id

        logger.debug(
            f"Deleting meeting: meeting_id={meeting_id}, user_id={user_id}"
        )

        result_perm = await self.ctx.require_admin_or_team_role_or_executor()

        meeting = await self.get_meeting(meeting_id=meeting_id, team_id=team_id)

        if not result_perm.is_admin and meeting.creator_id != user_id:
            logger.warning(
                f"Unauthorized participant delete attempt: "
                f"user_id={user_id}, meeting_id={meeting_id}"
            )
            raise c_exp.PermissionDeniedError()

        await self.repo.delete(meeting=meeting)

        logger.warning(f"Meeting deleted: meeting_id={meeting_id}")

        return {"message": "Meeting deleted"}
