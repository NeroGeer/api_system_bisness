import pytest
from jose import jwt
from datetime import datetime, UTC

from src.core.security.jwt_token import create_token
from src.database.config import settings


@pytest.mark.asyncio
async def test_create_token_contains_required_fields():
    data = {"sub": "123"}

    token = await create_token(data)

    decoded = jwt.decode(
        token,
        settings.jwt.secret_key,
        algorithms=[settings.jwt.algorithm]
    )

    assert decoded["sub"] == "123"
    assert decoded["type"] == "access"
    assert "exp" in decoded


@pytest.mark.asyncio
async def test_create_token_expiration():
    data = {"sub": "1"}

    token = await create_token(data)
    decoded = jwt.decode(
        token,
        settings.jwt.secret_key,
        algorithms=[settings.jwt.algorithm]
    )

    exp = datetime.fromtimestamp(decoded["exp"], UTC)
    now = datetime.now(UTC)

    assert exp > now
