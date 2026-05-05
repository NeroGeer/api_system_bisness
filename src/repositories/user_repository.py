from sqlalchemy import select

from src.logger.logger import logger
from src.database.database import SessionDep
from src.models.model_user import User, Role


class UserRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(
            select(User).where(User.email == email)
        )

    async def get_default_role(self, role_id: int) -> Role:
        return await self.session.scalar(
            select(Role).where(Role.id == role_id)
        )

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        logger.debug(f"New user created with ID: {user.id}")
        return user

    async def update(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        logger.debug(f"Update User success: {user}")
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
