from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import cookie
from src.database.database import SessionDep
from src.repositories.refresh_token_repository import RefreshTokenRepo
from src.repositories.user_repository import UserRepository
from src.services.refresh_token_service import RefreshTokenService
from src.repositories.team_repository import TeamRepository
from src.services.team_service import TeamService
from src.services.user_service import UserService
from src.core.context.base_context import (BaseContext,
                                           build_context_with_filters,
                                           UserFilter, build_service)
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
async def create_user(data: CreateUserScheme, session: SessionDep):
    serv_fact = build_service(repository_cls=UserRepository, service_cls=UserService, session=session)
    return await serv_fact.create_user(data=data)


@route_user.post("/login", status_code=200)
async def user_login(
    response: Response, session: SessionDep, form: OAuth2PasswordRequestForm = Depends()
):
    serv_fact = build_service(service_cls=UserService, repository_cls=UserRepository, session=session)
    access_token, user = await serv_fact.login(form=form)

    serv_token = build_service(service_cls=RefreshTokenService, repository_cls=RefreshTokenRepo, session=session)
    refresh_token = await serv_token.create_refresh_token(user_id=user.id)
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
    serv_fact = build_service(repository_cls=TeamRepository, service_cls=TeamService,
                              session=ctx.session, ctx=ctx)

    team = await serv_fact.get_team_code()
    result = await serv_fact.join_team(team)

    return result


@route_user.patch("/me", status_code=200, response_model=LoginUserScheme)
async def put_user_me(
    update_data: UpdateUserScheme,
    ctx: Annotated[BaseContext, Depends(build_context_with_filters())]
):
    serv_fact = build_service(repository_cls=UserRepository, service_cls=UserService, session=ctx.session, ctx=ctx)
    result = await serv_fact.update_user(data=update_data)
    return result


@route_user.delete("/me", status_code=204)
async def delete_user_me(
        ctx: Annotated[BaseContext, Depends(build_context_with_filters())]
):
    serv_fact = build_service(repository_cls=UserRepository, service_cls=UserService, session=ctx.session, ctx=ctx)
    result = await serv_fact.delete_user()
    return result


@route_user.post("/logout", status_code=200)
async def logout(request: Request, response: Response, session: SessionDep):
    refresh_token = request.cookies.get("refresh_token")
    serv_token = build_service(service_cls=RefreshTokenService, repository_cls=RefreshTokenRepo, session=session)
    if refresh_token:
        await serv_token.delete_refresh_token(token=refresh_token)

    cookie.delete_refresh_cookie(response)
    return {"message": "Logged out"}
