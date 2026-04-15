from fastapi import HTTPException
from sqlalchemy import select

import json

from src.database.database import SessionDep, RedisDep, RedisKeys
from src.core.models.model_user.models import User
from src.core.models.model_tasks.models import Task, TaskComment
from src.route.crud.crud_task import require_admin_or_team_manager
from src.core.scheme.scheme_task.schemas_task import CommentSchema, CommentCreateSchema
from src.core.scheme.scheme_team.schemas_team import TeamRole


async def get_task_comments(current_user: User, team_id: int, task_id: int, session: SessionDep, redis: RedisDep):

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, team_role={TeamRole.manager, TeamRole.employee})

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    cached = await redis.get(key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            await redis.delete(key)

    result = await session.execute(
        select(TaskComment)
        .join(Task, TaskComment.task_id == Task.id)
        .where(
            TaskComment.task_id == task_id,
            Task.team_id == team_id
        )
        .order_by(TaskComment.created_at.asc())
    )
    comments = result.scalars().all()

    data = [CommentSchema.model_validate(c).model_dump(mode='json') for c in comments]

    await redis.set(key, json.dumps(data, ensure_ascii=False), ex=300)

    return comments


async def add_task_comments(task_id: int,
                            team_id: int,
                            current_user: User,
                            comment_data: CommentCreateSchema,
                            session: SessionDep, redis: RedisDep):

    await require_admin_or_team_manager(session=session, current_user=current_user,
                                        team_id=team_id, check_executor=True, task_id=task_id)

    new_comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        text=comment_data.text
    )

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)

    return new_comment


async def update_comments_by_id(comment_id: int,
                                task_id: int,
                                team_id: int,
                                current_user: User,
                                comment_data: CommentCreateSchema,
                                session: SessionDep, redis: RedisDep):

    stmt = (
        select(TaskComment)
        .join(Task, TaskComment.task_id == Task.id)
        .where(
            TaskComment.id == comment_id,
            TaskComment.task_id == task_id,
            Task.team_id == team_id
        )
    )

    comment = await session.scalar(stmt)

    if not current_user.id == comment.user_id:
        await require_admin_or_team_manager(session=session, current_user=current_user, team_id=team_id)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.text = comment_data.text

    await session.commit()
    await session.refresh(comment)

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)

    return comment


async def delete_comments_by_id(comment_id: int,
                                task_id: int,
                                team_id: int,
                                current_user: User,
                                session: SessionDep, redis: RedisDep):
    stmt = (
        select(TaskComment)
        .join(Task, TaskComment.task_id == Task.id)
        .where(
            TaskComment.id == comment_id,
            TaskComment.task_id == task_id,
            Task.team_id == team_id
        )
    )

    comment = await session.scalar(stmt)

    if not current_user.id == comment.user_id:
        await require_admin_or_team_manager(session=session, current_user=current_user, team_id=team_id)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await session.delete(comment)
    await session.commit()

    key = RedisKeys.TASK_COMMENTS.format(task_id=task_id)
    await redis.delete(key)

    return {'detail': 'Comment deleted'}



