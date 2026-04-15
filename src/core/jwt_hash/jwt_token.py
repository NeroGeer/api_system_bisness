from jose import jwt

from datetime import datetime, timedelta, UTC
import uuid
from sqlalchemy import select

from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_MIN, JWT_REFRESH_EXPIRE_DAYS

from src.core.models.model_user.models import User
from src.core.models.model_jwt.model import RefreshToken
from src.database.database import SessionDep


async def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=JWT_ACCESS_EXPIRE_MIN)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token():
    return str(uuid.uuid4())


async def refresh_token_create_by_bd(
        token: str,
        current_user: User,
        session: SessionDep
):
    refresh_obj = RefreshToken(
        user_id=current_user.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    )

    session.add(refresh_obj)
    await session.commit()


async def get_refresh_token(session: SessionDep, token: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_refresh_token(session: SessionDep, token: str) -> None:
    token_obj = await get_refresh_token(session=session, token=token)

    if token_obj:
        await session.delete(token_obj)


async def rotate_refresh_token(session: SessionDep, refresh_token: str):
    token_in_db = await get_refresh_token(session=session, token=refresh_token)

    if not token_in_db:
        return None, "invalid"

    if token_in_db.expires_at < datetime.now(UTC):
        return None, "expired"

    await delete_refresh_token(session=session, token=refresh_token)

    new_refresh = create_refresh_token()

    new_token_obj = RefreshToken(
        user_id=token_in_db.user_id,
        token=new_refresh,
        expires_at=datetime.now(UTC) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    )

    session.add(new_token_obj)

    access_token = create_token({"sub": str(token_in_db.user_id)})

    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh
    }, None
