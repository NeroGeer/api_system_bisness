import json

from fastapi import HTTPException
from sqlalchemy import select

from src.database.database import RedisDep, RedisKeys, SessionDep
from src.logger.logger import logger
from src.models.model_tasks import Task, TaskComment
from src.models.model_user import User
from src.scheme.schemas_task import CommentCreateSchema, CommentSchema
from src.scheme.schemas_team import TeamRole
from src.services.task_service import require_admin_or_team_manager


async def comment_stmt(
    session: SessionDep, team_id: int, task_id: int, comment_id: int
) -> CommentSchema:
    """
    Retrieves a specific comment ensuring it belongs to the given task and team.

    Args:
        session (SessionDep): Database session.
        team_id (int): Team ID.
        task_id (int): Task ID.
        comment_id (int): Comment ID.

    Returns:
        TaskComment: Found comment.

    Raises:
        HTTPException: If comment is not found.
    """

    stmt = (
        select(TaskComment)
        .join(Task, TaskComment.task_id == Task.id)
        .where(
            TaskComment.id == comment_id,
            TaskComment.task_id == task_id,
            Task.team_id == team_id,
        )
    )

    comment = await session.scalar(stmt)
    if not comment:
        logger.warning(
            f"Comment not found: comment_id={comment_id}, task_id={task_id}, team_id={team_id}"
        )
        raise HTTPException(status_code=404, detail="Comment not found")

    logger.debug(f"Comment loaded: id={comment_id}")

    return comment


async def get_task_comments(
    current_user: User, team_id: int, task_id: int, session: SessionDep, redis: RedisDep
):
    """
    Retrieves all comments for a task with Redis caching.

    Args:
        current_user (User): Authenticated user.
        team_id (int): Team ID.
        task_id (int): Task ID.
        session (SessionDep): Database session.
        redis (RedisDep): Redis client.

    Returns:
        list[CommentSchema]: List of task comments.
    """

    logger.debug(
        f"Fetching comments: user_id={current_user.id}, task_id={task_id}, team_id={team_id}"
    )

    await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=team_id,
        team_role={TeamRole.manager, TeamRole.employee},
    )

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    cached = await redis.get(key)
    if cached:
        logger.debug(f"Cache hit for task comments: task_id={task_id}")
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            logger.warning(f"Invalid cache JSON for key={key}")
            await redis.delete(key)

    result = await session.execute(
        select(TaskComment)
        .join(Task, TaskComment.task_id == Task.id)
        .where(TaskComment.task_id == task_id, Task.team_id == team_id)
        .order_by(TaskComment.created_at.asc())
    )
    comments = result.scalars().all()

    data = [CommentSchema.model_validate(c).model_dump(mode="json") for c in comments]

    await redis.set(key, json.dumps(data, ensure_ascii=False), ex=300)

    logger.info(f"Comments loaded from DB: task_id={task_id}, count={len(comments)}")

    return comments


async def add_task_comments(
    task_id: int,
    team_id: int,
    current_user: User,
    comment_data: CommentCreateSchema,
    session: SessionDep,
    redis: RedisDep,
):
    """
    Adds a new comment to a task.

    Args:
        task_id (int): Task ID.
        team_id (int): Team ID.
        current_user (User): Authenticated user.
        comment_data (CommentCreateSchema): Comment payload.
        session (SessionDep): Database session.
        redis (RedisDep): Redis client.

    Returns:
        TaskComment: Created comment.
    """

    logger.debug(f"Adding comment: user_id={current_user.id}, task_id={task_id}")

    await require_admin_or_team_manager(
        session=session,
        current_user=current_user,
        team_id=team_id,
        check_executor=True,
        task_id=task_id,
    )

    new_comment = TaskComment(
        task_id=task_id, user_id=current_user.id, text=comment_data.text
    )

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)

    logger.info(f"Comment created: id={new_comment.id}, task_id={task_id}")

    return new_comment


async def update_comments_by_id(
    comment_id: int,
    task_id: int,
    team_id: int,
    current_user: User,
    comment_data: CommentCreateSchema,
    session: SessionDep,
    redis: RedisDep,
):
    """
    Updates a comment if user is owner or has admin/team manager rights.

    Args:
        comment_id (int): Comment ID.
        task_id (int): Task ID.
        team_id (int): Team ID.
        current_user (User): Authenticated user.
        comment_data (CommentCreateSchema): Updated data.
        session (SessionDep): Database session.
        redis (RedisDep): Redis client.

    Returns:
        TaskComment: Updated comment.
    """

    comment = await comment_stmt(
        session=session, team_id=team_id, task_id=task_id, comment_id=comment_id
    )

    if not current_user.id == comment.user_id:
        logger.debug(
            f"Non-owner update attempt: user_id={current_user.id}, comment_id={comment_id}"
        )
        await require_admin_or_team_manager(
            session=session, current_user=current_user, team_id=team_id
        )

    comment.text = comment_data.text

    await session.commit()
    await session.refresh(comment)

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)

    logger.info(f"Comment updated: id={comment_id}")

    return comment


async def delete_comments_by_id(
    comment_id: int,
    task_id: int,
    team_id: int,
    current_user: User,
    session: SessionDep,
    redis: RedisDep,
):
    """
    Deletes a comment if user is owner or has admin/team manager rights.

    Args:
        comment_id (int): Comment ID.
        task_id (int): Task ID.
        team_id (int): Team ID.
        current_user (User): Authenticated user.
        session (SessionDep): Database session.
        redis (RedisDep): Redis client.

    Returns:
        dict: Confirmation message.
    """

    comment = await comment_stmt(
        session=session, team_id=team_id, task_id=task_id, comment_id=comment_id
    )

    if not current_user.id == comment.user_id:
        logger.debug(
            f"Non-owner delete attempt: user_id={current_user.id}, comment_id={comment_id}"
        )

        await require_admin_or_team_manager(
            session=session, current_user=current_user, team_id=team_id
        )

    await session.delete(comment)
    await session.commit()

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)
    logger.info(f"Comment deleted: id={comment_id}")

    return {"detail": "Comment deleted"}
