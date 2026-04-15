from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.database.database import SessionDep
from src.core.models.model_user.models import User, PermissionResult
from src.core.models.model_team.models import TeamMember
from src.core.models.model_meeting.models import Meeting, MeetingParticipant
from src.core.scheme.scheme_meeting.schemas_meeting import MeetingParticipantsDeleteSchema, MeetingCreateSchema, MeetingUpdateSchema
from src.core.scheme.scheme_team.schemas_team import TeamRole
from src.route.crud.crud_task import require_admin_or_team_manager, validate_user_in_team


async def meeting_stmt(session: SessionDep, meeting_id: int, team_id: int | None = None) -> Meeting:
    stmt = await session.scalar(
        select(Meeting)
        .where(Meeting.id == meeting_id)
        .options(selectinload(Meeting.participants))
    )

    if team_id is not None:
        stmt = stmt.where(Meeting.team_id == team_id)

    if not stmt:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return stmt


async def validate_meeting_data(
        session: SessionDep,
        team_id: int,
        creator: User,
        result_perm: PermissionResult,
        participants_set: set[int] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
):
    if not result_perm.is_admin:
        if not await validate_user_in_team(session=session, user_id=creator.id, team_id=team_id):
            raise HTTPException(status_code=403, detail="Creator must be a member of the team")

    if participants_set is None or not participants_set:
        return

    stmt = (
        select(User.id, TeamMember.user_id)
        .outerjoin(
            TeamMember,
            (TeamMember.user_id == User.id) &
            (TeamMember.team_id == team_id)
        )
        .where(User.id.in_(participants_set))
    )

    rows = await session.execute(stmt)

    existing_users = set()
    team_users = set()

    for user_id, team_user_id in rows:
        existing_users.add(user_id)
        if team_user_id is not None:
            team_users.add(user_id)

    missing_users = participants_set - existing_users
    if missing_users:
        raise HTTPException(status_code=404, detail=f"Users not found: {missing_users}")

    invalid_users = participants_set - team_users
    if invalid_users:
        raise HTTPException(status_code=400, detail=f"Users not in team: {invalid_users}")

    if start_time and end_time:
        conflicted_users = await check_meeting_conflicts(
            session=session,
            user_ids=list(participants_set),
            start_time=start_time,
            end_time=end_time,
        )

        if conflicted_users:
            raise HTTPException(status_code=400, detail=f"Users already have meetings: {conflicted_users}")


async def check_meeting_conflicts(
        session: SessionDep,
        user_ids: list[int],
        start_time: datetime,
        end_time: datetime,
        exclude_meeting_id: int | None = None,
):
    stmt = (
        select(
            MeetingParticipant.user_id,
            Meeting.id
        )
        .join(Meeting)
        .where(
            MeetingParticipant.user_id.in_(user_ids),
            Meeting.start_time < end_time,
            Meeting.end_time > start_time,
        )
    )

    if exclude_meeting_id is not None:
        stmt = stmt.where(Meeting.id != exclude_meeting_id)

    result = await session.execute(stmt)

    conflicts: dict[int, list[int]] = {}

    for user_id, meeting_id in result.all():
        conflicts.setdefault(user_id, []).append(meeting_id)

    return conflicts


async def get_meeting(
        team_id: int,
        current_user: User,
        session: SessionDep,
        meeting_id: int | None = None,
        only_my_meetings: bool = False,
        participant_user_id: int | None = None,):

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, team_role={TeamRole.manager, TeamRole.employee})
    stmt = (
        select(Meeting)
        .where(Meeting.team_id == team_id)
        .order_by(Meeting.start_time)
    )

    if meeting_id is not None:
        stmt = stmt.where(Meeting.id == meeting_id)

    if only_my_meetings and participant_user_id is not None:
        raise HTTPException(status_code=400, detail="Conflicting filters: "
                            "use only_my_meetings OR participant_user_id")

    if only_my_meetings:
        stmt = stmt.where(
            Meeting.participants.any(
                MeetingParticipant.user_id == current_user.id
            )
        )

    if participant_user_id is not None:
        stmt = stmt.where(
            Meeting.participants.any(
                MeetingParticipant.user_id == participant_user_id
            )
        )

    result = await session.execute(stmt)

    if meeting_id is not None:
        meeting = result.scalars().first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return meeting

    return result.scalars().all()


async def create_meeting(
        current_user: User,
        session: SessionDep,
        meeting_data: MeetingCreateSchema,
        team_id: int
):
    result_perm = await require_admin_or_team_manager(session=session,
                                                      current_user=current_user,
                                                      team_id=team_id)

    participants_set: set[int] = set(meeting_data.participants or [])

    await validate_meeting_data(session=session,
                                team_id=team_id,
                                creator=current_user,
                                participants_set=participants_set,
                                result_perm=result_perm)

    meeting = Meeting(
        creator_id=current_user.id,
        team_id=team_id,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        title=meeting_data.title,
        description=meeting_data.description,
    )

    session.add(meeting)
    await session.flush()

    for user_id in participants_set:
        session.add(MeetingParticipant(
            meeting_id=meeting.id,
            user_id=user_id
        ))

    await session.commit()
    return meeting


async def update_meeting(
        current_user: User,
        session: SessionDep,
        meeting_id: int,
        data: MeetingUpdateSchema,
        team_id: int,
):
    if not data or data is None:
        raise HTTPException(status_code=400, detail="Data task empty")

    meeting = await meeting_stmt(session=session, meeting_id=meeting_id, team_id=team_id)

    result_perm = await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=meeting.team_id,
    )

    if not result_perm.is_admin and meeting.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to edit meeting")

    if data.title is not None:
        meeting.title = data.title

    if data.description is not None:
        meeting.description = data.description

    if data.participants is not None:
        to_add = set(data.participants) - {p.user_id for p in meeting.participants}

        await validate_meeting_data(
            session=session,
            team_id=meeting.team_id,
            creator=current_user,
            result_perm=result_perm,
            participants_set=to_add,
        )

        for user_id in to_add:
            session.add(MeetingParticipant(
                meeting_id=meeting_id,
                user_id=user_id
            ))

    new_start = data.start_time or meeting.start_time
    new_end = data.end_time or meeting.end_time

    if data.start_time is not None or data.end_time is not None:
        if new_end <= new_start:
            raise HTTPException(status_code=400, detail="Invalid time range")

        participant_ids = [p.user_id for p in meeting.participants]

        conflicts = await check_meeting_conflicts(
            session=session,
            user_ids=participant_ids,
            start_time=new_start,
            end_time=new_end,
            exclude_meeting_id=meeting.id,
        )

        if conflicts:
            raise HTTPException(
                status_code=400,
                detail=f"Users already have meetings: {conflicts}"
            )

        meeting.start_time = new_start
        meeting.end_time = new_end

    await session.commit()
    await session.refresh(meeting)

    return meeting


async def delete_meeting_participant(
        current_user: User,
        session: SessionDep,
        meeting_id: int,
        team_id: int,
        users_ids: MeetingParticipantsDeleteSchema
):
    if not users_ids:
        raise HTTPException(status_code=400, detail="No users provided")

    meeting = await meeting_stmt(session=session, meeting_id=meeting_id, team_id=team_id)

    result_perm = await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=meeting.team_id,
    )

    if not result_perm.is_admin and meeting.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to edit meeting")

    to_remove = set(users_ids)
    missing = to_remove - {p.user_id for p in meeting.participants}

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Users not in meeting: {list(missing)}"
        )

    await session.execute(
        delete(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id.in_(to_remove)
        )
    )

    return {
        "meeting_id": meeting.id,
        "removed_participants": list(to_remove),
    }


async def delete_meeting_by_id(
        team_id: int,
        current_user: User,
        session: SessionDep,
        meeting_id: int):

    result_perm = await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=team_id,
    )

    meeting = await meeting_stmt(session=session, meeting_id=meeting_id, team_id=team_id)

    if not result_perm.is_admin and meeting.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to edit meeting")

    await session.delete(meeting)
    await session.commit()

    return {'message': 'Meeting deleted',
            'detail': meeting}
