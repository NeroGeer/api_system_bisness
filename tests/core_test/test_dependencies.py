import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(admin_client):
    response = await admin_client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_token(anon_client):
    response = await anon_client.get("/api/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_success(admin_client: AsyncClient, admin_auth):
    response = await admin_client.get(
        "/api/users/me",
        headers=admin_auth["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data