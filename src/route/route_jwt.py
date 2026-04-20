from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from starlette.responses import Response

from src.core.security import cookie
from src.database.database import SessionDep
from src.services.auth_service import rotate_refresh_token

route_jwt = APIRouter(prefix="/api/jwt", tags=["jwt"])


@route_jwt.post("/refresh")
async def refresh_token(request: Request, response: Response, session: SessionDep):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(401, detail="Invalid token")

    result, error = await rotate_refresh_token(refresh_token=token, session=session)

    if error:
        raise HTTPException(401, error)

    cookie.set_refresh_cookie(response, result["refresh_token"])

    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "message": "Token refreshed",
    }
