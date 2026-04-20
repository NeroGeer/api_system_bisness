import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(admin_client: AsyncClient, team_with_member):
    payload = {
        "deadline": "2026-01-01",
        "description": "Task description",
        "executor_user_id": None,
    }

    response = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/tasks/create-task",
        json=payload
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Task description"


@pytest.mark.asyncio
async def test_get_all_tasks(admin_client: AsyncClient, team_with_member):
    response = await admin_client.get(
        f"/api/teams/{team_with_member['id']}/tasks"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_task_by_id(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/tasks/create-task",
        json={
            "deadline": "2026-01-01",
            "description": "One Task",
            "executor_user_id": None,
        }
    )
    task_id = create.json()["id"]

    response = await admin_client.get(
        f"/api/teams/{team_with_member['id']}/tasks/{task_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id


@pytest.mark.asyncio
async def test_update_task(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/tasks/create-task",
        json={
            "deadline": "2026-01-01",
            "description": "Old Title",
            "executor_user_id": None,
        }
    )
    task_id = create.json()["id"]

    response = await admin_client.patch(
        f"/api/teams/{team_with_member['id']}/tasks/update-task/{task_id}",
        json={
            "deadline": "2026-01-01",
            "description": "New Title",
            "executor_user_id": None,
        }
    )

    assert response.status_code == 200
    assert response.json()["description"] == "New Title"


@pytest.mark.asyncio
async def test_update_task_status(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/tasks/create-task",
        json={
            "deadline": "2026-01-01",
            "description": "New Title",
            "executor_user_id": None,
        }
    )
    task_id = create.json()["id"]

    response = await admin_client.patch(
        f"/api/teams/{team_with_member['id']}/tasks/update-task/{task_id}/status",
        json={"status": "closed",
              'grade': '4'}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_task(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/tasks/create-task",
        json={
            "deadline": "2026-01-01",
            "description": "To delete",
            "executor_user_id": None,
        }
    )
    task_id = create.json()["id"]

    response = await admin_client.delete(
        f"/api/teams/{team_with_member['id']}/tasks/delete-task/{task_id}"
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_avg_grade(admin_client: AsyncClient, team_with_member):
    response = await admin_client.get(
        f"/api/teams/{team_with_member['id']}/tasks/avg_grade",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-12-31"
        }
    )

    assert response.status_code == 200
    assert "grade" in response.json()
