import pytest
from httpx import AsyncClient


def assert_created(response):
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    return data


@pytest.mark.asyncio
async def test_create_meeting(admin_client: AsyncClient, team_with_member):
    payload = {
        "title": "Test Meeting",
        "description": "Meeting description",
        "start_time": "2026-01-01T10:00:00",
        "end_time": "2026-01-01T11:00:00",
        "participants": []
    }

    response = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/meeting",
        json=payload
    )

    data = assert_created(response)

    assert data["title"] == "Test Meeting"


@pytest.mark.asyncio
async def test_get_meetings(admin_client: AsyncClient, team_with_member):
    response = await admin_client.get(
        f"/api/teams/{team_with_member['id']}/meeting"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_meeting_by_id(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/meeting",
        json={
            "title": "Meeting",
            "description": "desc",
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T11:00:00",
            "participants": []
        }
    )

    data = assert_created(create)
    meeting_id = data["id"]

    response = await admin_client.get(
        f"/api/teams/{team_with_member['id']}/meeting/{meeting_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == meeting_id


@pytest.mark.asyncio
async def test_update_meeting(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/meeting",
        json={
            "title": "Old",
            "description": "desc",
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T11:00:00",
            "participants": []
        }
    )

    data = assert_created(create)
    meeting_id = data["id"]

    response = await admin_client.put(
        f"/api/teams/{team_with_member['id']}/meeting/{meeting_id}",
        json={"title": "New Title"}
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_participants(admin_client: AsyncClient, team_with_member):
    user_id = team_with_member["user_id"]
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/meeting",
        json={
            "title": "Meeting",
            "description": "desc",
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T11:00:00",
            "participants": [user_id]
        }
    )

    data = assert_created(create)
    meeting_id = data["id"]

    assert data["participants"] == [{"user_id": user_id}]

    response = await admin_client.delete(
        f"/api/teams/{team_with_member['id']}/meeting/{meeting_id}/participants",
        params={"users_ids": [user_id]}
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_meeting(admin_client: AsyncClient, team_with_member):
    create = await admin_client.post(
        f"/api/teams/{team_with_member['id']}/meeting",
        json={
            "title": "Meeting",
            "description": "desc",
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T11:00:00",
            "participants": []
        }
    )

    data = assert_created(create)
    meeting_id = data["id"]

    response = await admin_client.delete(
        f"/api/teams/{team_with_member['id']}/meeting/{meeting_id}"
    )

    assert response.status_code == 204