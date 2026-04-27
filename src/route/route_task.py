from typing import Annotated, List

from fastapi import APIRouter, Depends

from src.repositories.crud import crud_task as c_t
from src.scheme.schemas_task import (
    OutAVGGradeTaskSchema,
    TaskCreateSchema,
    TaskSchema,
    UpdateTaskSchema,
    UpdateTaskStatusSchema,
)
from src.core.context.base_context import (
    BaseContext,
    build_context_with_filters,
    TaskFilter,
    DateFilter)

route_task = APIRouter(prefix="/api/teams/{team_id}/tasks", tags=["Tasks"])


@route_task.get("", status_code=200, response_model=List[TaskSchema])
async def get_all_task(
        ctx: Annotated[
                BaseContext[TaskFilter],
                Depends(build_context_with_filters(TaskFilter))
            ],
):
    result = await c_t.get_tasks_or_task_by_id(
        ctx=ctx
    )
    return result


@route_task.get("/avg_grade", status_code=200, response_model=OutAVGGradeTaskSchema)
async def get_avg_task_grade_by_user_id(
        ctx: Annotated[
            BaseContext[DateFilter],
            Depends(build_context_with_filters(DateFilter))
        ],
):
    result = await c_t.get_avg_grade_task_make_date_range(
        ctx=ctx
    )
    return result


@route_task.get("/{task_id}", status_code=200, response_model=TaskSchema)
async def get_task_by_id(
        ctx: Annotated[
            BaseContext[TaskFilter],
            Depends(build_context_with_filters(TaskFilter))
        ],
):
    result = await c_t.get_tasks_or_task_by_id(
        ctx=ctx
    )
    return result


@route_task.post("/create-task", status_code=201, response_model=TaskSchema)
async def create_new_task(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: TaskCreateSchema,
):
    result = await c_t.create_task(
        ctx=ctx, task_data=data
    )
    return result


@route_task.patch("/update-task/{task_id}", status_code=200, response_model=TaskSchema)
async def update_task_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: UpdateTaskSchema,
):
    result = await c_t.update_task(
        ctx=ctx,
        task_data=data
    )
    return result


@route_task.patch(
    "/update-task/{task_id}/status", status_code=200, response_model=TaskSchema
)
async def update_task_by_id_status(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
        data: UpdateTaskStatusSchema,
):
    result = await c_t.update_task_status(
        ctx=ctx,
        task_data=data,
    )
    return result


@route_task.delete("/delete-task/{task_id}", status_code=204)
async def delete_task_by_id(
        ctx: Annotated[
            BaseContext,
            Depends(build_context_with_filters())
        ],
):
    return await c_t.delete_task(ctx=ctx)
