from datetime import datetime, UTC, timedelta

from sqlalchemy import select

from src.database.database import SessionDep
from src.database.config import settings
from src.models.model_jwt import RefreshToken
from src.models.model_user import User


async def refresh_token_create_by_bd(
        token: str,
        current_user: User,
        session: SessionDep
):
    refresh_obj = RefreshToken(
        user_id=current_user.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_expire_days)
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
