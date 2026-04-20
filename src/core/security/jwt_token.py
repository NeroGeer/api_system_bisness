from datetime import UTC, datetime, timedelta

from jose import jwt

from src.database.config import settings
from src.logger.logger import logger


async def create_token(data: dict):
    """
    Creates a JWT access token.

    Args:
        data (dict): Payload data to encode into the token (e.g. user id, roles).

    Returns:
        str: Encoded JWT access token.
    """
    logger.debug("Creating JWT token")
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt.access_expire_min)
    to_encode.update({"exp": expire, "type": "access"})
    logger.debug("JWT token successfully created")
    return jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )
