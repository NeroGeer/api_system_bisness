from typing import Annotated

from fastapi import APIRouter, Depends

from src.services.comment_service import CommentService
from src.repositories.comment_repository import CommentRepository
from src.scheme.schemas_task import CommentCreateSchema, CommentSchema
from src.core.context.base_context import (
    BaseContext,
    build_context_with_filters,
    build_service
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
    serv_fact = build_service(repository_cls=CommentRepository,
                              service_cls=CommentService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.get_task_comments()


@route_comment.post("", status_code=201, response_model=CommentSchema)
async def add_comment(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: CommentCreateSchema,
):
    serv_fact = build_service(repository_cls=CommentRepository,
                              service_cls=CommentService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.add_comments(data=data)


@route_comment.patch("/{comment_id}", status_code=200, response_model=CommentSchema)
async def update_comment_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: CommentCreateSchema,
):
    serv_fact = build_service(repository_cls=CommentRepository,
                              service_cls=CommentService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.update_comments(data=data)


@route_comment.delete("/{comment_id}", status_code=204)
async def delete_comment_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
):
    serv_fact = build_service(repository_cls=CommentRepository,
                              service_cls=CommentService,
                              session=ctx.session, ctx=ctx)
    return await serv_fact.delete_comments()
