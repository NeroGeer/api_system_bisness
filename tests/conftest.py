from collections.abc import AsyncGenerator

import uuid
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.pool import NullPool

from src.main import app
from src.database.insert_perm import insert_rbac_data
from src.models.model_base import Base
from src.database.database import get_session, get_redis_client

TEST_DB_URL = "postgresql+asyncpg://user:password@localhost:5432/test_db"

test_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
test_async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False)


class FakeRedis:
    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None


@pytest_asyncio.fixture(autouse=True)
async def override_redis():
    async def _fake_redis():
        return FakeRedis()

    app.dependency_overrides[get_redis_client] = _fake_redis
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def override_db_session():
    async def _override():
        async with test_async_session() as session:
            try:
                yield session
            finally:
                await session.rollback()

    app.dependency_overrides[get_session] = _override

    yield

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def ensure_test_database():
    admin_url = "postgresql+asyncpg://user:password@localhost:5432/postgres"

    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'test_db'")
            )
            exists = result.scalar() is not None
    except Exception as e:
        raise
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True, scope='session')
async def test_prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        try:
            await insert_rbac_data(conn)
        except Exception:
            raise

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def test_db_session() -> AsyncSession:
    async with test_async_session() as session:
        try:
            yield session
            await session.commit()
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def admin_auth(ac: AsyncClient):
    payload = {
        "email": "admin@test.com",
        "password": "admin123",
    }
    response = await ac.post("/api/users/register", json=payload)

    login = await ac.post(
        "/api/users/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "access_token": token,
        "headers": {"Authorization": f"Bearer {token}"}, "cookies": response.cookies,
    }


@pytest_asyncio.fixture
async def test_user(ac: AsyncClient):
    payload = {
        "email": f"user_{uuid.uuid4()}@test.com",
        "password": "User!@#12345",
    }

    response = await ac.post("/api/users/register", json=payload)
    assert response.status_code == 201

    data = response.json()

    return {
        "email": payload["email"],
        "password": payload["password"],
        "id": data["id"]
    }


@pytest_asyncio.fixture
async def anon_client(ac: AsyncClient):
    return ac


@pytest_asyncio.fixture
async def admin_client(ac: AsyncClient, admin_auth):
    ac.headers.update(admin_auth["headers"])
    ac.cookies.update(admin_auth["cookies"])
    return ac


@pytest_asyncio.fixture
async def user_client(ac: AsyncClient, test_user):
    login = await ac.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token = login.json()["access_token"]

    ac.headers.update({"Authorization": f"Bearer {token}"})
    return ac


@pytest_asyncio.fixture
async def team(admin_auth, ac: AsyncClient):
    payload = {
        "name": f"Test Team {uuid.uuid4()}",
        "invite_code": str(uuid.uuid4()),
    }

    response = await ac.post(
        "/api/admin/create-team",
        json=payload,
        headers=admin_auth["headers"],
    )

    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture
async def team_with_member(admin_client: AsyncClient, test_user):
    team = await admin_client.post(
        "/api/admin/create-team",
        json={"name": f"Test Team {uuid.uuid4()}",
              "invite_code": str(uuid.uuid4()), }
    )
    assert team.status_code == 201
    team_data = team.json()

    add = await admin_client.post(
        f"/api/teams/{team_data['id']}/members",
        json={"user_id": test_user["id"], "role": "manager"}
    )
    assert add.status_code == 201

    return {
        "id": team_data["id"],
        "invite_code": team_data["invite_code"],
        "name": team_data["name"],
        "user_id": test_user["id"],
    }


@pytest_asyncio.fixture
async def task_in_team(admin_client: AsyncClient, team_with_member):
    response = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/tasks/create-task",
        json={
            "deadline": "2026-01-01",
            "description": "Task description",
            "executor_user_id": team_with_member["user_id"],
        }

    )

    assert response.status_code == 201
    task = response.json()
    return {
        "team_id": team_with_member["id"],
        "task_id": task["id"]
    }

