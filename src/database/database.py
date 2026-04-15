from typing import Annotated, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from redis.asyncio import Redis
from enum import Enum

from src.logger.logger import logger
from src.database.config import settings

DATABASE_URL = settings.db.url  #"sqlite+aiosqlite:///./app.py.db"

engine = create_async_engine(DATABASE_URL, echo=True)
logger.info(f"Async database engine created for {DATABASE_URL}")

async_session = async_sessionmaker(engine, expire_on_commit=False)
logger.debug("Async session maker initialized")


async def get_session() -> AsyncSession:
    async with async_session() as session:
        logger.debug("New database session opened")
        yield session
        logger.debug("Database session closed")


SessionDep: Type[AsyncSession] = Annotated[AsyncSession, Depends(get_session)]

redis_client = Redis(host=settings.redis.url, port=settings.redis.port, decode_responses=True)


async def get_redis_client() -> Redis:
    yield redis_client


RedisDep: Type[Redis] = Annotated[Redis, Depends(get_redis_client)]


class RedisKeys(str, Enum):
    TASK_COMMENTS = "task:{task_id}:comments"

    def format(self, **kwargs):
        return self.value.format(**kwargs)
