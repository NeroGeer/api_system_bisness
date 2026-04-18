from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from typing import Annotated

from src.scheme.schemas_user import CreateUserScheme, UpdateUserScheme, LoginUserScheme, OutCreateUserScheme
from src.scheme.schemas_team import InviteTeamSchema

from src.core.security.refresh_token import create_refresh_token
from src.repositories.refresh_token_repo import refresh_token_create_by_bd, delete_refresh_token
from src.core.security import dependencies as jwt, hash_password as hsp, cookie, jwt_token
from src.models.model_user import User
from src.database.database import SessionDep
from src.logger.logger import logger
from src.repositories.crud import crud_user as crud_u

route_user = APIRouter(
    prefix="/api/users",
    tags=["User"],
)


@route_user.get("/me", response_model=LoginUserScheme, status_code=200)
async def get_user_me(user: Annotated[User, Depends(jwt.get_current_user)]):
    return user


@route_user.post("/register", status_code=201, response_model=OutCreateUserScheme)
async def create_user(user: CreateUserScheme, session: SessionDep):
    logger.info(f"Creating new user with name: {user.name}")
    new_user = await crud_u.create_user(session=session, user_create=user)
    logger.debug(f"New user created with ID: {new_user.id}")
    return new_user


@route_user.post('/login', status_code=200)
async def user_login(response: Response, session: SessionDep, form: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"User login with name: {form.username}")
    result = await crud_u.get_user_by_email(session=session, email=form.username)
    if not result or not hsp.verify_password(form.password, result.hashed_password):
        raise HTTPException(403, detail="Invalid password or email")

    access_token = str(await jwt_token.create_token({"sub": str(result.id)}))
    refresh_token = create_refresh_token()
    await refresh_token_create_by_bd(session=session,
                                     token=refresh_token,
                                     current_user=result)

    cookie.set_refresh_cookie(response, refresh_token)
    cookie.set_access_cookie(response, access_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Authorization successful"
    }


@route_user.post("/join-team", status_code=201)
async def user_join_team(
        code: InviteTeamSchema,
        user: Annotated[User, Depends(jwt.get_current_user)],
        session: SessionDep
):
    result = await crud_u.user_team_invite_by_code(
        session=session,
        invite_code=code,
        current_user=user,
    )

    return {"message": f"Joined team {result.team.name}"}


@route_user.patch("/me", status_code=200, response_model=LoginUserScheme)
async def put_user_me(
        update_data: UpdateUserScheme,
        user: Annotated[User, Depends(jwt.get_current_user)],
        session: SessionDep
):
    result = await crud_u.update_user(session=session, current_user=user, update_data=update_data)
    return result


@route_user.delete("/me", status_code=204)
async def delete_user_me(
        user: Annotated[User, Depends(jwt.get_current_user)],
        session: SessionDep
):
    await crud_u.delete_user(session=session, current_user=user)
    return {"message": "User deleted successfully"}


@route_user.post("/logout", status_code=200)
async def logout(
        request: Request,
        response: Response,
        session: SessionDep
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await delete_refresh_token(session, refresh_token)

    cookie.delete_refresh_cookie(response)
    return {"message": "Logged out"}
