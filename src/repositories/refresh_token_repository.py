from sqlalchemy import select

from src.database.database import SessionDep
from src.models.model_jwt import RefreshToken


class RefreshTokenRepo:
    def __init__(self, session: SessionDep):
        self.session = session

    async def get(self, token: str) -> RefreshToken | None:
        """
        Retrieves a refresh token from the database.

        Args:
            self. session (SessionDep): Database session.
            token (str): Refresh token string.

        Returns:
            RefreshToken | None: Token object if found, otherwise None.
        """
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token == token
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, token: str) -> None:
        """
        Deletes a refresh token from the database.

        Args:
            self. session  (SessionDep): Database session.
            token (str): Refresh token string.
        """
        await self.session.delete(token)
        await self.session.commit()

    async def create(self, token: str):
        """
        Creates and stores a refresh token in the database.

        Args:
            token (str): Raw refresh token string.
            self. session  (SessionDep): Database session.

        Returns:
            RefreshToken: Created refresh token DB object.
        """
        self.session.add(token)
        await self.session.commit()
