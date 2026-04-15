#import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.core.models import Base
from src.database.database import engine, redis_client
from src.route.route_user import route_user
from src.route.route_tweet import route_tweets
from src.route.route_medias import route_medias
from src.database.insert_perm import insert_rbac_data

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous lifespan context manager for the FastAPI application.

    This function is executed when the application starts and stops.
    It ensures that the database schema is freshly created and populated
    with initial data at startup, and that resources are cleaned up at shutdown.

    Workflow:
    - On startup:
        1. Open a connection to the database engine.
        2. Drop all existing tables (if any).
        3. Recreate all tables defined in SQLAlchemy Base metadata.
        4. Insert initial data into the database.
    - On shutdown:
        - Dispose of the database engine, closing all connections.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Allows FastAPI to run while the lifespan context is active.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await insert_rbac_data(conn)
    yield

    try:
        await redis_client.ping()
    except Exception as e:
        raise

    yield

    await engine.dispose()
    await redis_client.close()


app = FastAPI(lifespan=lifespan)


app.mount("/images", StaticFiles(directory="/usr/share/nginx/static/images"), name="images")



# if __name__ == '__main__':
#     uvicorn.run('main:app', host='127.0.0.1', port=8000)
