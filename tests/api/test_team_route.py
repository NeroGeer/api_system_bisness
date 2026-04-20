import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_team_members(admin_client: AsyncClient, team):
    response = await admin_client.get(f"/api/teams/{team['id']}/members")

    assert response.status_code == 200
    assert "members" in response.json()


@pytest.mark.asyncio
async def test_add_member_to_team(admin_client: AsyncClient, team, test_user):
    payload = {
        "user_id": test_user["id"],
        "role": "employee"
    }

    response = await admin_client.post(
        f"/api/teams/{team['id']}/members",
        json=payload
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "employee"


@pytest.mark.asyncio
async def test_update_member_role(admin_client: AsyncClient, team, test_user):
    add = await admin_client.post(
        f"/api/teams/{team['id']}/members",
        json={"user_id": test_user["id"], "role": "employee"}
    )
    assert add.status_code == 201

    response = await admin_client.patch(
        f"/api/teams/{team['id']}/members/{test_user['id']}",
        json={"role": "manager"}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_update_member_role_forbidden(user_client: AsyncClient, team, test_user):
    response = await user_client.patch(
        f"/api/teams/{team['id']}/members/{test_user['id']}",
        json={"role": "manager"}
    )

    assert response.status_code in (403, 401)


@pytest.mark.asyncio
async def test_remove_member(admin_client: AsyncClient, team, test_user):
    await admin_client.post(
        f"/api/teams/{team['id']}/members",
        json={"user_id": test_user["id"], "role": "employee"}
    )

    response = await admin_client.delete(
        f"/api/teams/{team['id']}/members/{test_user['id']}"
    )

    assert response.status_code == 204
