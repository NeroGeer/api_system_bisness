from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import cookie
from src.database.database import SessionDep
from src.repositories.crud import crud_user as crud_u
from src.repositories.refresh_token_repo import delete_refresh_token
from src.core.context.base_context import BaseContext, build_context_with_filters, UserFilter
from src.scheme.schemas_user import (
    CreateUserScheme,
    LoginUserScheme,
    OutCreateUserScheme,
    UpdateUserScheme,
)


route_user = APIRouter(
    prefix="/api/users",
    tags=["User"],
)


@route_user.get("/me", response_model=LoginUserScheme, status_code=200)
async def get_user_me(ctx: Annotated[BaseContext, Depends(build_context_with_filters())]):
    return ctx.current_user


@route_user.post("/register", status_code=201, response_model=OutCreateUserScheme)
async def create_user(user: CreateUserScheme, session: SessionDep):
    return await crud_u.create_user(session=session, user_create=user)


@route_user.post("/login", status_code=200)
async def user_login(
    response: Response, session: SessionDep, form: OAuth2PasswordRequestForm = Depends()
):
    access_token, refresh_token = await crud_u.get_user_by_email(
        session=session, form=form
    )

    cookie.set_refresh_cookie(response, refresh_token)
    cookie.set_access_cookie(response, access_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Authorization successful",
    }


@route_user.post("/join-team", status_code=201)
async def user_join_team(
        ctx: Annotated[BaseContext[UserFilter], Depends(build_context_with_filters(UserFilter))]
):
    return await crud_u.user_team_invite_by_code(ctx=ctx)


@route_user.patch("/me", status_code=200, response_model=LoginUserScheme)
async def put_user_me(
    update_data: UpdateUserScheme,
    ctx: Annotated[BaseContext, Depends(build_context_with_filters())]
):
    return await crud_u.update_user(ctx=ctx, update_data=update_data)


@route_user.delete("/me", status_code=204)
async def delete_user_me(
        ctx: Annotated[BaseContext, Depends(build_context_with_filters())]
):
    await crud_u.delete_user(ctx=ctx)
    return {"message": "User deleted successfully"}


@route_user.post("/logout", status_code=200)
async def logout(request: Request, response: Response, session: SessionDep):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await delete_refresh_token(session, refresh_token)

    cookie.delete_refresh_cookie(response)
    return {"message": "Logged out"}
