from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.schema import MetaData

from src.database.config import settings


class Base(DeclarativeBase):
    """base Class"""
    __abstract__ = True

    metadata = MetaData(
        naming_convention=settings.db.naming_convention
    )
