import json

from fastapi import HTTPException
from sqlalchemy import select

from src.database.database import RedisKeys, SessionDep
from src.logger.logger import logger
from src.models.model_tasks import Task, TaskComment
from src.scheme.schemas_task import CommentCreateSchema, CommentSchema
from src.scheme.schemas_team import TeamRole
from src.core.context.base_context import BaseContext


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
    ctx: BaseContext
):
    """
    Retrieves all comments for a task with Redis caching.

    Args:
        ctx: BaseContex
        ctx.current_user (User): Authenticated user.
        ctx.session (SessionDep): Database session.
        ctx.redis (RedisDep): Redis client.
        ctx.scope.team_id (int): Team ID.
        ctx.scope.task_id (int): Task ID.

    Returns:
        list[CommentSchema]: List of task comments.
    """
    current_user = ctx.current_user
    session = ctx.session
    redis = ctx.redis
    team_id = ctx.scope.team_id
    task_id = ctx.scope.task_id

    logger.debug(
        f"Fetching comments: user_id={current_user.id}, task_id={task_id}, team_id={team_id}"
    )

    await ctx.require_admin_or_team_role_or_executor(team_role={TeamRole.manager, TeamRole.employee})

    if not await session.get(Task, task_id):
        raise HTTPException(status_code=400, detail=f"Task {task_id} not Found")

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
    ctx: BaseContext,
    comment_data: CommentCreateSchema,
):
    """
    Adds a new comment to a task.

    Args:
        ctx: BaseContex
        ctx.current_user (User): Authenticated user.
        ctx.session (SessionDep): Database session.
        ctx.redis (RedisDep): Redis client.
        ctx.scope.task_id (int): Task ID.
        comment_data (CommentCreateSchema): Comment payload.

    Returns:
        TaskComment: Created comment.
    """

    current_user = ctx.current_user
    session = ctx.session
    redis = ctx.redis
    task_id = ctx.scope.task_id

    logger.debug(f"Adding comment: user_id={current_user.id}, task_id={task_id}")

    await ctx.require_admin_or_team_role_or_executor(check_executor=True)

    if not await session.get(Task, task_id):
        raise HTTPException(status_code=400, detail=f"Task {task_id} not Found")

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
    ctx: BaseContext,
    comment_data: CommentCreateSchema,
):
    """
    Updates a comment if user is owner or has admin/team manager rights.

    Args:
        ctx: BaseContex
        ctx.current_user (User): Authenticated user.
        ctx.session (SessionDep): Database session.
        ctx.redis (RedisDep): Redis client.
        ctx.scope.team_id (int): Team ID.
        ctx.scope.task_id (int): Task ID.
        ctx.scope.comment_id (int): Comment ID.
        comment_data (CommentCreateSchema): Updated data.


    Returns:
        TaskComment: Updated comment.
    """

    current_user = ctx.current_user
    session = ctx.session
    redis = ctx.redis
    team_id = ctx.scope.team_id
    task_id = ctx.scope.task_id
    comment_id = ctx.scope.comment_id

    comment = await comment_stmt(
        session=session, team_id=team_id, task_id=task_id, comment_id=comment_id
    )

    if not current_user.id == comment.user_id:
        logger.debug(
            f"Non-owner update attempt: user_id={current_user.id}, comment_id={comment_id}"
        )
        await ctx.require_admin_or_team_role_or_executor()

    comment.text = comment_data.text

    await session.commit()
    await session.refresh(comment)

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)

    logger.info(f"Comment updated: id={comment_id}")

    return comment


async def delete_comments_by_id(
    ctx: BaseContext
):
    """
    Deletes a comment if user is owner or has admin/team manager rights.

    Args:
        ctx: BaseContex
        ctx.current_user (User): Authenticated user.
        ctx.session (SessionDep): Database session.
        ctx.redis (RedisDep): Redis client.
        ctx.scope.team_id (int): Team ID.
        ctx.scope.task_id (int): Task ID.
        ctx.scope.comment_id (int): Comment ID.

    Returns:
        dict: Confirmation message.
    """

    current_user = ctx.current_user
    session = ctx.session
    redis = ctx.redis
    team_id = ctx.scope.team_id
    task_id = ctx.scope.task_id
    comment_id = ctx.scope.comment_id

    comment = await comment_stmt(
        session=session, team_id=team_id, task_id=task_id, comment_id=comment_id
    )

    if not current_user.id == comment.user_id:
        logger.debug(
            f"Non-owner delete attempt: user_id={current_user.id}, comment_id={comment_id}"
        )

        await ctx.require_admin_or_team_role_or_executor()

    await session.delete(comment)
    await session.commit()

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)
    logger.info(f"Comment deleted: id={comment_id}")

    return {"detail": "Comment deleted"}
