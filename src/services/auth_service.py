from datetime import datetime, UTC, timedelta

from src.core.security.jwt_token import create_token
from src.core.security.refresh_token import create_refresh_token
from src.database.database import SessionDep
from src.database.config import settings
from src.logger.logger import logger
from src.models.model_jwt import RefreshToken
from src.repositories.refresh_token_repo import get_refresh_token, delete_refresh_token


async def rotate_refresh_token(session: SessionDep, refresh_token: str):
    """
       Rotates refresh token and issues new access + refresh tokens.

       Flow:
           1. Validate refresh token exists
           2. Check expiration
           3. Delete old refresh token
           4. Create new refresh token
           5. Issue new access token

       Args:
           session: DB session
           refresh_token: current refresh token

       Returns:
           tuple[dict | None, str | None]:
               (tokens, error_code)
               error_code: "invalid" | "expired" | None
       """

    logger.info("Starting refresh token rotation")
    token_in_db = await get_refresh_token(session=session, token=refresh_token)

    if not token_in_db:
        logger.warning("Refresh token rotation failed: invalid token")
        return None, "invalid"

    if token_in_db.expires_at < datetime.now(UTC):
        logger.warning(
            f"Refresh token expired: user_id={token_in_db.user_id}"
        )
        return None, "expired"

    await delete_refresh_token(session=session, token=refresh_token)

    logger.debug(
        f"Old refresh token deleted: user_id={token_in_db.user_id}"
    )

    new_refresh = create_refresh_token()

    new_token_obj = RefreshToken(
        user_id=token_in_db.user_id,
        token=new_refresh,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_expire_days)
    )

    session.add(new_token_obj)

    access_token = create_token({"sub": str(token_in_db.user_id)})

    await session.commit()

    logger.info(
        f"Token rotation success: user_id={token_in_db.user_id}"
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh
    }, None
