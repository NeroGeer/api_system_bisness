from fastapi import APIRouter, Depends, Query
from datetime import date

from typing import Annotated, List

from src.database.database import SessionDep
from src.repositories.crud import crud_task as c_t
from src.models.model_user import User
from src.scheme.schemas_task import OutAVGGradeTaskSchema, UpdateTaskStatusSchema, UpdateTaskSchema, TaskCreateSchema, \
    TaskSchema
from src.core.security import dependencies as jwt

route_task = APIRouter(
    prefix="/api/teams/{team_id}/tasks",
    tags=["Tasks"]
)


@route_task.get("", status_code=200, response_model=List[TaskSchema], tags=["Get all tasks"])
async def get_all_task(team_id: int, session: SessionDep,
                       current_user: Annotated[User, Depends(jwt.get_current_user)],
                       only_my_tasks: bool = Query(False),
                       executor_user_id: int | None = Query(None),
                       ):
    result = await c_t.get_tasks_or_task_by_id(session=session,
                                               team_id=team_id,
                                               current_user=current_user,
                                               only_my_tasks=only_my_tasks,
                                               executor_user_id=executor_user_id)
    return result


@route_task.get("/{task_id}", status_code=200, response_model=TaskSchema, tags=["Get tasks by id"])
async def get_task_by_id(team_id: int, session: SessionDep,
                         current_user: Annotated[User, Depends(jwt.get_current_user)],
                         task_id: int,
                         only_my_tasks: bool = Query(False),
                         executor_user_id: int | None = Query(None), ):
    result = await c_t.get_tasks_or_task_by_id(session=session,
                                               team_id=team_id,
                                               current_user=current_user,
                                               task_id=task_id,
                                               only_my_tasks=only_my_tasks,
                                               executor_user_id=executor_user_id)
    return result


@route_task.get("", status_code=200, response_model=OutAVGGradeTaskSchema, tags=["Get avg grade tasks by user id"])
async def get_avg_task_grade_by_user_id(team_id: int, session: SessionDep,
                                        current_user: Annotated[User, Depends(jwt.get_current_user)],
                                        start_date: date, end_date: date):
    result = await c_t.get_avg_grade_task_make_date_range(session=session,
                                                          team_id=team_id,
                                                          current_user=current_user,
                                                          start_date=start_date, end_date=end_date)
    return result


@route_task.post("/create-task", status_code=201, response_model=TaskSchema, tags=["Create task"])
async def create_new_task(team_id: int, session: SessionDep,
                          current_user: Annotated[User, Depends(jwt.get_current_user)],
                          data: TaskCreateSchema):
    result = await c_t.create_task(session=session, task_data=data, team_id=team_id, current_user=current_user)
    return result


@route_task.patch("/update-task/{task_id}", status_code=200, response_model=TaskSchema, tags=["Update task"])
async def update_task_by_id(team_id: int, session: SessionDep, task_id: int,
                            current_user: Annotated[User, Depends(jwt.get_current_user)],
                            data: UpdateTaskSchema):
    result = await c_t.update_task(session=session, task_data=data, task_id=task_id, team_id=team_id,
                                   current_user=current_user)
    return result


@route_task.patch("/update-task/{task_id}/status", status_code=200, response_model=TaskSchema,
                  tags=["Update task status"])
async def update_task_by_id(team_id: int, session: SessionDep, task_id: int,
                            current_user: Annotated[User, Depends(jwt.get_current_user)],
                            data: UpdateTaskStatusSchema):
    result = await c_t.update_task_status(session=session, task_data=data, task_id=task_id, team_id=team_id,
                                          current_user=current_user)
    return result


@route_task.delete("/delete-task", status_code=204, tags=["Delete task"])
async def delete_task_by_id(team_id: int, session: SessionDep,
                            task_id: int, current_user: Annotated[User, Depends(jwt.get_current_user)]):
    return await c_t.delete_task(session=session, task_id=task_id, team_id=team_id, current_user=current_user)
