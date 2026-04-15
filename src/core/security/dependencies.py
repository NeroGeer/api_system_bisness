from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.repositories.crud.crud_user import get_user_by_id
from src.database.database import SessionDep
from src.database.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(session: SessionDep, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm])

        if not payload or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = int(user_id)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(session=session, user_id=user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
