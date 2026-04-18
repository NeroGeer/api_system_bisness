from datetime import datetime, UTC, date
from fastapi import HTTPException
from sqlalchemy import select, func, and_

from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_user import User
from src.models.model_tasks import Task
from src.repositories.task_repository import validate_user_in_team
from src.scheme.schemas_task import TaskCreateSchema, StatusTask, UpdateTaskSchema, \
    UpdateTaskStatusSchema
from src.scheme.schemas_team import TeamRole
from src.services.task_service import require_admin_or_team_manager
from src.utils.utils import make_date_range


async def task_stmt(session: SessionDep, task_id: int, team_id: int) -> Task:
    """
    Fetch a task by ID within a specific team.

    Args:
        session: DB session
        task_id: Task ID
        team_id: Team ID

    Returns:
        Task object

    Raises:
        HTTPException(404): if task not found
    """

    task = await session.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.team_id == team_id
        )
    )
    if task is None:
        logger.warning(f"Task not found: task_id={task_id}, team_id={team_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def resolve_task_status(executor_user_id: int | None) -> StatusTask:
    """
    Resolve task status based on executor assignment.
    """
    return (
        StatusTask.work
        if executor_user_id
        else StatusTask.open
    )


async def get_tasks_or_task_by_id(
        team_id: int,
        current_user: User,
        session: SessionDep,
        task_id: int | None = None,
        only_my_tasks: bool = False,
        executor_user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,

):
    """
    Retrieve tasks for a team with optional filters.

    Supports:
        - single task by ID
        - filtering by executor
        - filtering only current user tasks
        - filtering by date range

    Args:
        team_id: Team ID
        current_user: Authenticated user
        session: DB session
        task_id: Optional task ID (returns single task)
        only_my_tasks: Return only tasks assigned to current user
        executor_user_id: Filter by executor
        start_date: Deadline start filter
        end_date: Deadline end filter

    Returns:
        Task | list[Task]
    """
    logger.debug(
        f"Fetching tasks: user_id={current_user.id}, team_id={team_id}, "
        f"task_id={task_id}"
    )

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, team_role={TeamRole.manager, TeamRole.employee})

    stmt = select(Task).where(Task.team_id == team_id)

    if task_id is not None:
        stmt = stmt.where(Task.id == task_id)

    if start_date is not None and end_date is not None:
        start_dt, end_dt = make_date_range(start_date, end_date)

        stmt = stmt.where(
            and_(
                Task.deadline >= start_dt,
                Task.deadline <= end_dt
            )
        )

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
            logger.warning(
                f"Task not found after query: task_id={task_id}, team_id={team_id}"
            )

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
    """
    Returns average grade of tasks closed by current user in a date range.

    Only includes:
        - tasks from selected team
        - tasks assigned to current user
        - tasks with close_date in range
    """

    logger.debug(
        f"Calculating avg grade: user_id={current_user.id}, team_id={team_id}, "
        f"range=({start_date} -> {end_date})"
    )
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

    logger.info(
        f"Avg grade computed: user_id={current_user.id}, value={avg_grade}"
    )

    return avg_grade


async def create_task(
        team_id: int,
        task_data: TaskCreateSchema,
        current_user: User,
        session: SessionDep
):
    """
    Creates a new task in a team.

    Rules:
        - only admin or team manager can create
        - executor must belong to team (if provided)
        - status is auto-resolved
    """

    logger.info(
        f"Creating task: user_id={current_user.id}, team_id={team_id}"
    )

    await require_admin_or_team_manager(session=session, current_user=current_user, team_id=team_id)

    if task_data.executor_user_id is not None:
        if not await validate_user_in_team(session=session, user_id=task_data.executor_user_id, team_id=team_id):
            logger.warning(
                f"Invalid executor assignment: user_id={task_data.executor_user_id}, team_id={team_id}"
            )
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

    logger.info(f"Task created: task_id={new_task.id}")

    return new_task


async def update_task(
        team_id: int,
        task_id: int,
        task_data: UpdateTaskSchema,
        current_user: User,
        session: SessionDep
):
    """
    Updates task fields:
        - executor user
        - description
        - deadline
        - auto status recalculation

    Rules:
        - executor must belong to team
        - status is auto-derived from executor
    """

    if not task_data or task_data is None:
        raise HTTPException(status_code=400, detail="Data task empty")

    logger.debug(
        f"Updating task: task_id={task_id}, user_id={current_user.id}"
    )

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, check_executor=True, task_id=task_id)

    task = await task_stmt(session=session, team_id=team_id, task_id=task_id)

    if task_data.executor_user_id is not None:
        if not await validate_user_in_team(session=session, user_id=task_data.executor_user_id, team_id=team_id):
            logger.warning(
                f"Invalid executor: user_id={task_data.executor_user_id}, team_id={team_id}"
            )
            raise HTTPException(status_code=400, detail="Executor must be a member of the team")
        task.executor_user_id = task_data.executor_user_id
        task.status = resolve_task_status(task_data.executor_user_id)

    if task_data.description is not None:
        task.description = task_data.description

    if task_data.deadline is not None:
        task.deadline = task_data.deadline

    await session.commit()
    await session.refresh(task)

    logger.info(f"Task updated: task_id={task.id}")

    return task


async def update_task_status(
        team_id: int,
        task_id: int,
        task_data: UpdateTaskStatusSchema,

        current_user: User,
        session: SessionDep
):

    """
    Handles task status transitions.

    Rules:
        - closing task requires grade
        - reopening task clears grade and close_date
        - status transitions are validated
    """

    logger.debug(
        f"Updating task status: task_id={task_id}, user_id={current_user.id}"
    )
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

        logger.info(f"Task closed: task_id={task.id}, grade={task.grade}")

    elif task_data.status == StatusTask.closed or new_status == StatusTask.closed:
        if task_data.grade is None:
            raise HTTPException(status_code=400, detail="Task close. grade task not can empty ")
        task.grade = task_data.grade

    elif old_status == StatusTask.closed and new_status in [StatusTask.open, StatusTask.work]:
        task.grade = None
        task.close_date = None
        logger.info(f"Task reopened: task_id={task.id}")

    if task_data.status is not None:
        task.status = task_data.status

    logger.info(
        f"Task status updated: task_id={task.id}, status={task.status}"
    )

    await session.commit()
    await session.refresh(task)

    return task


async def delete_task(
        team_id: int,
        task_id: int,
        current_user: User,
        session: SessionDep
):
    """
    Deletes a task permanently from a team.

    Rules:
        - only admin or team manager can delete tasks
        - task must belong to specified team

    Args:
        team_id: Team ID
        task_id: Task ID
        current_user: Authenticated user
        session: DB session

    Returns:
        dict: Confirmation message
    """

    logger.debug(
        f"Deleting task: task_id={task_id}, team_id={team_id}, user_id={current_user.id}"
    )

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id)

    task = await task_stmt(session=session, team_id=team_id, task_id=task_id)

    await session.delete(task)
    await session.commit()

    logger.info(
        f"Task deleted: task_id={task_id}, team_id={team_id}"
    )

    return {'message': 'Task deleted'}
