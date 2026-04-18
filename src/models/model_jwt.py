from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column


from datetime import datetime, UTC

from src.models.model_base import Base


class RefreshToken(Base):
    """
    Database model for storing JWT refresh tokens.

    This table is used to persist refresh tokens for user sessions,
    enabling secure token rotation and revocation.

    Attributes:
        id (int):
            Primary key identifier of the refresh token record.

        user_id (int):
            Reference to the user who owns this refresh token.
            Cascades on delete (tokens are removed when user is deleted).

        token (str):
            Unique refresh token string stored in hashed or raw form
            depending on security design.

        expires_at (datetime):
            Expiration timestamp of the refresh token.

        created_at (datetime):
            Timestamp when the token was created.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
