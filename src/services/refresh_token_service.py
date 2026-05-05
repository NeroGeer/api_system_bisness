from datetime import UTC, datetime, timedelta
import uuid

from src.logger.logger import logger
from src.core.security import jwt_token
from src.database.config import settings
from src.models.model_jwt import RefreshToken
from src.exceptions import exceptions as c_exp


class RefreshTokenService:
    def __init__(self, repo, context=None):
        self.repo = repo
        self.ctx = context

    async def delete_refresh_token(self, token: str) -> None:
        logger.debug("Attempting to delete refresh token")

        token_obj = await self.repo.get(token=token)

        if token_obj:
            await self.repo.delete(token=token_obj)
            logger.info(f"Refresh token deleted (id={token_obj.id})")

    async def create_refresh_token(self, user_id: int):
        logger.debug(f"Creating refresh token for user_id={user_id}")

        new_refresh = str(uuid.uuid4())
        refresh_obj = RefreshToken(
            user_id=user_id,
            token=new_refresh,
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_expire_days),
        )
        await self.repo.create(refresh_obj)
        logger.info(f"Refresh token created for user_id={user_id}")
        return new_refresh

    async def update_refresh_token(self, refresh_token: str):
        """
        Rotates refresh token and issues new access + refresh tokens.

        Flow:
            1. Validate refresh token exists
            2. Check expiration
            3. Delete old refresh token
            4. Create new refresh token
            5. Issue new access token

        Args:
            refresh_token: current refresh token

        Returns:
            tuple[dict | None, str | None]:
                (tokens, error_code)
                error_code: "invalid" | "expired" | None
        """

        logger.info("Starting refresh token rotation")
        token_in_db = await self.repo.get(token=refresh_token)

        if not token_in_db:
            logger.warning("Refresh token rotation failed: invalid token")
            raise c_exp.InvalidRefreshTokenError()

        if token_in_db.expires_at < datetime.now(UTC):
            logger.warning(f"Refresh token expired: user_id={token_in_db.user_id}")
            raise c_exp.ExpiredRefreshTokenError()

        await self.repo.delete(token=token_in_db)

        logger.debug(f"Old refresh token deleted: user_id={token_in_db.user_id}")

        new_refresh = str(uuid.uuid4())
        new_token_obj = RefreshToken(
            user_id=token_in_db.user_id,
            token=new_refresh,
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_expire_days),
        )

        await self.repo.create(new_token_obj)
        access_token = await jwt_token.create_token({"sub": str(token_in_db.user_id)})

        logger.info(f"Token rotation success: user_id={token_in_db.user_id}")

        return {"access_token": access_token, "refresh_token": new_refresh}
