from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from src.database.config import settings
from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_jwt import RefreshToken
from src.models.model_user import User


async def refresh_token_create_by_bd(
    token: str, current_user: User, session: SessionDep
):
    """
    Creates and stores a refresh token in the database.

    Args:
        token (str): Raw refresh token string.
        current_user (User): User for whom token is created.
        session (SessionDep): Database session.

    Returns:
        RefreshToken: Created refresh token DB object.
    """

    logger.debug(f"Creating refresh token for user_id={current_user.id}")

    refresh_obj = RefreshToken(
        user_id=current_user.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_expire_days),
    )

    session.add(refresh_obj)
    await session.commit()
    logger.info(f"Refresh token created for user_id={current_user.id}")


async def get_refresh_token(session: SessionDep, token: str) -> RefreshToken | None:
    """
    Retrieves a refresh token from the database.

    Args:
        session (SessionDep): Database session.
        token (str): Refresh token string.

    Returns:
        RefreshToken | None: Token object if found, otherwise None.
    """

    logger.debug("Fetching refresh token from DB")

    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_refresh_token(session: SessionDep, token: str) -> None:
    """
    Deletes a refresh token from the database.

    Args:
        session (SessionDep): Database session.
        token (str): Refresh token string.
    """

    logger.debug("Attempting to delete refresh token")

    token_obj = await get_refresh_token(session=session, token=token)

    if token_obj:
        await session.delete(token_obj)
        await session.commit()

        logger.info(f"Refresh token deleted (id={token_obj.id})")
