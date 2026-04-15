from jose import jwt, JWTError
from fastapi import Depends, HTTPException, APIRouter, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from typing import Annotated, Iterable

from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from src.route.crud.crud_user import get_user_by_id
from src.core.models.model_user.models import User
from src.core.models.model_team.models import TeamMember
from src.core.scheme.scheme_user.schemas_user import UserRole
from src.database.database import SessionDep
from src.core.jwt_hash import cookie, jwt_token

route_jwt = APIRouter(
    prefix="/api/jwt",
    tags=["jwt"]
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def has_role(user: User, roles: Iterable[UserRole]) -> bool:
    user_roles = {UserRole(role.name) for role in user.roles}
    return bool(user_roles.intersection(roles))


def require_role(roles: Iterable[UserRole]):
    async def checker(user: Annotated[User, Depends(get_current_user)]):
        if not has_role(user, roles):
            raise HTTPException(403, detail="Forbidden")
        return user

    return checker


def has_permission(user: User, permission: str) -> bool:
    return any(
        permission_obj.name == permission
        for role in user.roles
        for permission_obj in role.permissions
    )


def require_permission(permission: str):
    async def checker(
            user: Annotated[User, Depends(get_current_user)]
    ):
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail="Missing permission"
            )
        return user

    return checker


async def get_current_user(session: SessionDep, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != "access":
            raise HTTPException(401, detail="Invalid token")

        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(401, detail="Invalid token")

    except JWTError:
        raise HTTPException(401, detail="Invalid token")

    user = await get_user_by_id(session=session, user_id=user_id)

    if not user:
        raise HTTPException(401, detail="User not found")

    return user


def require_team_manager_or_admin():
    async def checker(team_id: int, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):

        if any(role.name == "admin" for role in user.roles):
            return user

        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role.in_(["manager", "owner"]),
        ).exists()

        result = await session.scalar(select(stmt))

        if not result:
            raise HTTPException(403, detail="Forbidden")

        return user

    return checker


@route_jwt.post("/refresh")
async def refresh_token(request: Request, response: Response, session: SessionDep):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(401, detail="Invalid token")

    result, error = await jwt_token.rotate_refresh_token(refresh_token=token, session=session)

    if error:
        raise HTTPException(401, error)

    cookie.set_refresh_cookie(response, result["refresh_token"])

    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "message": "Token refreshed",
    }
