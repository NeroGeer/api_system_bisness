from typing import Annotated

from fastapi import APIRouter, Depends

from src.repositories.crud import crud_comment as c_ct
from src.scheme.schemas_task import CommentCreateSchema, CommentSchema
from src.core.context.base_context import (
    BaseContext,
    build_context_with_filters
)

route_comment = APIRouter(
    prefix="/api/teams/{team_id}/tasks/{task_id}/comments", tags=["Comments"]
)


@route_comment.get("", status_code=200, response_model=list[CommentSchema])
async def get_comment(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
):
    return await c_ct.get_task_comments(
        ctx=ctx
    )


@route_comment.post("", status_code=201, response_model=CommentSchema)
async def add_comment(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: CommentCreateSchema,
):
    return await c_ct.add_task_comments(
        ctx=ctx,
        comment_data=data,
    )


@route_comment.patch("/{comment_id}", status_code=200, response_model=CommentSchema)
async def update_comment_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: CommentCreateSchema,
):
    return await c_ct.update_comments_by_id(
        ctx=ctx,
        comment_data=data,
    )


@route_comment.delete("/{comment_id}", status_code=204)
async def delete_comment_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
):
    return await c_ct.delete_comments_by_id(
        ctx=ctx
    )
