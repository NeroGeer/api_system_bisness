from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.security import dependencies as jwt
from src.database.database import RedisDep, SessionDep
from src.models.model_user import User
from src.repositories.crud import crud_comment as c_ct
from src.scheme.schemas_task import CommentCreateSchema, CommentSchema

route_comment = APIRouter(
    prefix="/api/teams/{team_id}/tasks/{task_id}/comments", tags=["Comments"]
)


@route_comment.get("", status_code=200, response_model=list[CommentSchema])
async def get_comment(
    team_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    redis: RedisDep,
):
    return await c_ct.get_task_comments(
        current_user=current_user,
        team_id=team_id,
        task_id=task_id,
        redis=redis,
        session=session,
    )


@route_comment.post("", status_code=201, response_model=CommentSchema)
async def add_comment(
    team_id: int,
    task_id: int,
    data: CommentCreateSchema,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    redis: RedisDep,
):
    return await c_ct.add_task_comments(
        current_user=current_user,
        comment_data=data,
        team_id=team_id,
        task_id=task_id,
        redis=redis,
        session=session,
    )


@route_comment.patch("/{comment_id}", status_code=200, response_model=CommentSchema)
async def update_comment_by_id(
    team_id: int,
    task_id: int,
    comment_id: int,
    data: CommentCreateSchema,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    redis: RedisDep,
):
    return await c_ct.update_comments_by_id(
        current_user=current_user,
        comment_data=data,
        team_id=team_id,
        task_id=task_id,
        comment_id=comment_id,
        redis=redis,
        session=session,
    )


@route_comment.delete("/{comment_id}", status_code=204)
async def delete_comment_by_id(
    team_id: int,
    task_id: int,
    comment_id: int,
    current_user: Annotated[User, Depends(jwt.get_current_user)],
    session: SessionDep,
    redis: RedisDep,
):
    return await c_ct.delete_comments_by_id(
        current_user=current_user,
        team_id=team_id,
        task_id=task_id,
        comment_id=comment_id,
        redis=redis,
        session=session,
    )
