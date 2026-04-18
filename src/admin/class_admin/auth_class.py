from sqladmin.authentication import AuthenticationBackend
from jose import jwt, JWTError
from fastapi import Request, Response, status
from fastapi.responses import RedirectResponse

from src.database.database import async_session, settings
from src.repositories.crud.crud_user import get_user_by_id
from src.core.security.rbac import has_permission
from src.core.security import hash_password as hsp, cookie, jwt_token
from src.repositories.crud import crud_user as crud_u
from src.repositories.refresh_token_repo import delete_refresh_token
from src.logger.logger import logger


class AdminAuth(AuthenticationBackend):
    def __init__(self):
        super().__init__(secret_key=settings.jwt.secret_key)

    async def login(self, request: Request) -> Response:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return RedirectResponse(
                url=request.url_for("admin:login"),
                status_code=status.HTTP_302_FOUND
            )

        async with async_session() as session:
            user = await crud_u.get_user_by_email(session=session, email=email)

            if not user or not hsp.verify_password(password, user.hashed_password):

                return RedirectResponse(request.url_for("admin:login"), status_code=302)

            if not user.is_active or not has_permission(user, "admin.panel.access"):
                return RedirectResponse(request.url_for("admin:login"), status_code=302)

            access_token = str(await jwt_token.create_token({"sub": str(user.id)}))

            response = RedirectResponse(
                url=request.url_for("admin:index"),
                status_code=status.HTTP_302_FOUND
            )

            cookie.set_access_cookie(response, access_token)

            request.session["user_id"] = user.id
            request.session["user_email"] = user.email
        return response

    async def logout(self, request: Request) -> Response:
        refresh_token = request.cookies.get("refresh_token")

        if refresh_token:
            async with async_session() as session:
                await delete_refresh_token(session, refresh_token)

        response = RedirectResponse(
            url=request.url_for("admin:login"),
            status_code=status.HTTP_302_FOUND
        )

        cookie.delete_refresh_cookie(response)
        response.delete_cookie("access_token")

        request.session.clear()

        return response

    async def authenticate(self, request: Request) -> bool:
        token = request.cookies.get("access_token")
        if not token:
            return False

        try:
            payload = jwt.decode(
                token,
                settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm]
            )

            if payload.get("type") != "access":
                return False

            user_id = int(payload.get("sub"))
        except (JWTError, ValueError, TypeError):
            return False

        async with async_session() as session:
            user = await get_user_by_id(session=session, user_id=user_id)

        if not user or not has_permission(user, "admin.panel.access"):
            return False

        request.session["user_id"] = user.id
        request.session["user_email"] = getattr(user, "email", None)

        return True
