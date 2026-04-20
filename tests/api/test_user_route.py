import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_login_success(ac: AsyncClient):
    response = await ac.post(
        "/api/users/login",
        data={
            "username": "admin@test.com",
            "password": "admin123",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data

    assert "refresh_token" in response.cookies
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_user_login_fail(ac: AsyncClient):

    response = await ac.post(
        "/api/users/login",
        data={
            "username": "admin@test.com",
            "password": "wrong",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_register(ac: AsyncClient):
    payload = {
        "email": "newuser@test.com",
        "password": "Test123!",
    }

    response = await ac.post("/api/users/register", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_user_me(ac: AsyncClient, admin_auth):
    response = await ac.get(
        "/api/users/me",
        headers=admin_auth["headers"],
    )

    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_update_user_me(ac: AsyncClient, test_user):
    login = await ac.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token = login.json()["access_token"]

    response = await ac.patch(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "updated@test.com"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "updated@test.com"


@pytest.mark.asyncio
async def test_delete_user_me(ac: AsyncClient, test_user):
    login = await ac.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token = login.json()["access_token"]

    response = await ac.delete(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_user_logout(ac: AsyncClient, admin_auth):
    ac.cookies.update(admin_auth["cookies"])

    response = await ac.post("/api/users/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out"


@pytest.mark.asyncio
async def test_user_join_team_invalid_code(ac: AsyncClient, admin_auth):
    response = await ac.post(
        "/api/users/join-team",
        headers=admin_auth["headers"],
        json={"invite_code": "invalid"},
    )

    assert response.status_code in (400, 404)

