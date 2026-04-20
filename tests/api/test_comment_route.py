import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_comment(admin_client: AsyncClient, task_in_team):
    response = await admin_client.post(
        f"/api/teams/{task_in_team['team_id']}/tasks/{task_in_team['task_id']}/comments",
        json={"text": "My comment"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "My comment"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_comments(admin_client: AsyncClient, team_with_member, task_in_team):
    response = await admin_client.get(
        f"/api/teams/{team_with_member['id']}/tasks/{task_in_team['task_id']}/comments"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_comment(admin_client: AsyncClient, task_in_team):
    create = await admin_client.post(
        f"/api/teams/{task_in_team['team_id']}/tasks/{task_in_team['task_id']}/comments",
        json={"text": "Old comment"}
    )
    comment_id = create.json()["id"]

    response = await admin_client.patch(
        f"/api/teams/{task_in_team['team_id']}/tasks/{task_in_team['task_id']}/comments/{comment_id}",
        json={"text": "Updated comment"}
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Updated comment"


@pytest.mark.asyncio
async def test_delete_comment(admin_client: AsyncClient, task_in_team):
    create = await admin_client.post(
        f"/api/teams/{task_in_team['team_id']}/tasks/{task_in_team['task_id']}/comments",
        json={"text": "To delete"}
    )
    comment_id = create.json()["id"]

    response = await admin_client.delete(
        f"/api/teams/{task_in_team['team_id']}/tasks/{task_in_team['task_id']}/comments/{comment_id}"
    )

    assert response.status_code == 204

