from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from src.core.security import cookie
from src.exceptions import exceptions as c_exp
from src.database.database import SessionDep
from src.repositories.refresh_token_repository import RefreshTokenRepo
from src.services.refresh_token_service import RefreshTokenService
from src.core.context.base_context import build_service

route_jwt = APIRouter(prefix="/api/jwt", tags=["jwt"])


@route_jwt.post("/refresh")
async def refresh_token(request: Request, response: Response, session: SessionDep):
    serv_token = build_service(service_cls=RefreshTokenService, repository_cls=RefreshTokenRepo, session=session)

    token = request.cookies.get("refresh_token")
    if not token:
        raise c_exp.InvalidRefreshTokenError()

    result = await serv_token.update_refresh_token(refresh_token=token)

    cookie.set_refresh_cookie(response, result["refresh_token"])

    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "message": "Token refreshed",
    }
