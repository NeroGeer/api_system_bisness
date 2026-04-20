from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.database.config import settings
from src.database.database import SessionDep
from src.logger.logger import logger
from src.repositories.crud.crud_user import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


async def get_current_user(session: SessionDep, token: str = Depends(oauth2_scheme)):
    """
    Gets the current user by JWT access token.

    Args:
        session (SessionDep): Асинхронная сессия БД.
        token (str): JWT токен, полученный из Authorization header.

    Returns:
        User: Объект пользователя из базы данных.

    Raises:
        HTTPException (401): Если токен невалидный, просрочен или пользователь не найден.
    """
    logger.debug("Attempting to decode access token")
    try:
        payload = jwt.decode(
            token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
        )

        logger.debug("Token successfully decoded")

        if not payload or payload.get("type") != "access":
            logger.warning("Invalid token type")
            raise HTTPException(status_code=401, detail="Invalid token, no have access")

        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing subject (sub)")
            raise HTTPException(status_code=401, detail="Invalid token, no have sub")

        user_id = int(user_id)
        logger.debug(f"Token belongs to user_id={user_id}")

    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token, no have access")

    user = await get_user_by_id(session=session, user_id=user_id)

    if not user:
        logger.warning(f"User not found for user_id={user_id}")
        raise HTTPException(status_code=401, detail="User not found")

    logger.info(f"Authenticated user_id={user_id}")
    return user
