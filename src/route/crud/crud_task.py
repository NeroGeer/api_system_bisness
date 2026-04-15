from datetime import datetime, UTC, date, time, timedelta
from fastapi import HTTPException
from sqlalchemy import select, exists

from typing import Iterable

from src.database.database import SessionDep
from src.core.models.model_user.models import User, PermissionResult
from src.core.models.model_tasks.models import Task
from src.core.models.model_team.models import TeamMember, Team
from src.core.scheme.scheme_user.schemas_user import UserRole
from src.core.scheme.scheme_task.schemas_task import TaskCreateSchema, StatusTask, UpdateTaskSchema, \
    UpdateTaskStatusSchema
from src.core.scheme.scheme_team.schemas_team import TeamRole
from src.core.jwt_hash.jwt_auth import has_role


async def make_date_range(start: date, end: date):
    start_dt = datetime.combine(start, time.min, tzinfo=UTC)
    end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC)
    return start_dt, end_dt


async def task_stmt(session: SessionDep, task_id: int, team_id: int) -> Task:
    task = await session.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.team_id == team_id
        )
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def resolve_task_status(executor_user_id: int | None) -> StatusTask:
    return (
        StatusTask.work
        if executor_user_id
        else StatusTask.open
    )


async def validate_user_in_team(
        session: SessionDep,
        user_id: int,
        team_id: int,
) -> bool:
    stmt = select(exists().where(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id))

    return await session.scalar(stmt)


async def require_admin_or_team_manager(
        session: SessionDep,
        current_user,
        team_id: int,
        team_role: set[TeamRole] | None = None,
        check_executor: bool = False,
        task_id: int | None = None,
):
    team_exists = await session.scalar(
        select(exists().where(Team.id == team_id))

    )
    if not team_exists:
        raise HTTPException(status_code=404, detail="Team not found")

    check_roles: set[TeamRole] = team_role if team_role is not None else {TeamRole.manager}

    is_admin = has_role(user=current_user, roles={UserRole.admin})
    is_team_role = await has_team_role(session=session, user=current_user, team_id=team_id, roles=check_roles)
    is_executor = False

    if check_executor:
        if task_id is None:
            raise HTTPException(
                status_code=422,
                detail="task_id is required when check_executor=True"
            )

        is_executor = bool(await session.scalar(
            select(exists().where(
                Task.id == task_id,
                Task.team_id == team_id,
                Task.executor_user_id == current_user.id
            )
            )
        ))

    if not (is_admin or is_team_role or is_executor):
        raise HTTPException(
            status_code=403,
            detail="No permission to perform this action. "
                   "Admin, team manager or task executor required."
        )

    return PermissionResult(
        is_admin=is_admin,
        is_team_role=is_team_role,
        is_executor=is_executor,
    )


async def has_team_role(session: SessionDep, user: User, team_id: int, roles: Iterable[TeamRole]) -> bool:
    stmt = select(TeamMember.role).where(
        TeamMember.user_id == user.id,
        TeamMember.team_id == team_id
    )

    role = await session.scalar(stmt)
    if role is None:
        return False

    try:
        return TeamRole(role) in roles
    except ValueError:
        return False


async def get_tasks_or_task_by_id(
        team_id: int,
        current_user: User,
        session: SessionDep,
        task_id: int | None = None,
        only_my_tasks: bool = False,
        executor_user_id: int | None = None,
):
    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, team_role={TeamRole.manager, TeamRole.employee})

    stmt = select(Task).where(Task.team_id == team_id)

    if task_id is not None:
        stmt = stmt.where(Task.id == task_id)

    if only_my_tasks and executor_user_id is not None:
        raise HTTPException(status_code=400, detail="Conflicting filters: "
                                                    "use only_my_tasks OR executor_user_id")

    if only_my_tasks:
        stmt = stmt.where(Task.executor_user_id == current_user.id)

    if executor_user_id is not None:
        if not await validate_user_in_team(session=session, user_id=executor_user_id, team_id=team_id):
            raise HTTPException(status_code=400, detail="Executor must be a member of the team")
        stmt = stmt.where(Task.executor_user_id == executor_user_id)

    result = await session.execute(stmt)

    if task_id is not None:
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    return result.scalars().all()


async def get_avg_grade_task_make_date_range(
        team_id: int,
        current_user: User,
        session: SessionDep,
        start_date: date,
        end_date: date,
):
    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, team_role={TeamRole.manager, TeamRole.employee})

    start_dt, end_dt = await make_date_range(start=start_date, end=end_date)

    stmt = select(func.avg(Task.grade)).where(
        Task.team_id == team_id,
        Task.executor_user_id == current_user.id,
        Task.close_date >= start_dt,
        Task.close_date < end_dt
    )

    avg_grade = await session.scalar(stmt)

    return avg_grade


async def create_task(
        team_id: int,
        task_data: TaskCreateSchema,
        current_user: User,
        session: SessionDep
):
    await require_admin_or_team_manager(session=session, current_user=current_user, team_id=team_id)

    if task_data.executor_user_id is not None:
        if not await validate_user_in_team(session=session, user_id=task_data.executor_user_id, team_id=team_id):
            raise HTTPException(status_code=400, detail="Executor must be a member of the team")

    new_task = Task(
        team_id=team_id,
        executor_user_id=task_data.executor_user_id,
        description=task_data.description,
        deadline=task_data.deadline,
        status=resolve_task_status(task_data.executor_user_id)
    )

    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    return new_task


async def update_task(
        team_id: int,
        task_id: int,
        task_data: UpdateTaskSchema,
        current_user: User,
        session: SessionDep
):
    if not task_data or task_data is None:
        raise HTTPException(status_code=400, detail="Data task empty")

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, check_executor=True, task_id=task_id)

    task = await task_stmt(session=session, team_id=team_id, task_id=task_id)

    if task_data.executor_user_id is not None:
        if not await validate_user_in_team(session=session, user_id=task_data.executor_user_id, team_id=team_id):
            raise HTTPException(status_code=400, detail="Executor must be a member of the team")
        task.executor_user_id = task_data.executor_user_id
        task.status = resolve_task_status(task_data.executor_user_id)

    if task_data.description is not None:
        task.description = task_data.description

    if task_data.deadline is not None:
        task.deadline = task_data.deadline

    await session.commit()
    await session.refresh(task)

    return task


async def update_task_status(
        team_id: int,
        task_id: int,
        task_data: UpdateTaskStatusSchema,

        current_user: User,
        session: SessionDep
):
    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id)

    task = await task_stmt(session=session, team_id=team_id, task_id=task_id)

    old_status = task.status
    new_status = task_data.status if task_data.status is not None else old_status

    if old_status != StatusTask.closed and new_status == StatusTask.closed:
        if task_data.grade is None:
            raise HTTPException(status_code=400, detail="Grade is required when closing a task.")
        task.grade = task_data.grade
        task.close_date = datetime.now(UTC)

    elif task_data.status == StatusTask.closed or new_status == StatusTask.closed:
        if task_data.grade is None:
            raise HTTPException(status_code=400, detail="Task close. grade task not can empty ")
        task.grade = task_data.grade

    elif old_status == StatusTask.closed and new_status in [StatusTask.open, StatusTask.work]:
        task.grade = None
        task.close_date = None

    if task_data.status is not None:
        task.status = task_data.status

    await session.commit()
    await session.refresh(task)

    return task


async def delete_task(
        team_id: int,
        task_id: int,
        current_user: User,
        session: SessionDep
):
    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id)

    task = await task_stmt(session=session, team_id=team_id, task_id=task_id)

    await session.delete(task)
    await session.commit()

    return {'message': 'Task deleted'}
