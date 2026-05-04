"""
test_job_alerts.py — Tests for /api/job-alerts/ routes.

Behaviours covered
------------------
Create alert
  [AL1]  Authenticated user creates alert with valid data → 201
  [AL2]  Unauthenticated → 403
  [AL3]  Invalid frequency value → 422
  [AL4]  Missing name → 422
  [AL5]  Default frequency is 'daily'

List alerts
  [AL6]  Authenticated user lists their alerts → 200
  [AL7]  Unauthenticated → 403
  [AL8]  Empty list returns []

Update alert
  [AL9]  Owner updates their alert → 200
  [AL10] Non-owner gets 403
  [AL11] Alert not found → 404
  [AL12] Empty body → 422
  [AL13] Invalid frequency on update → 422
  [AL14] Toggle is_active → 200

Delete alert
  [AL15] Owner deletes alert → 200
  [AL16] Non-owner gets 403
  [AL17] Alert not found → 404
"""

import uuid
from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    SEEKER_PROFILE,
    EMPLOYER_PROFILE,
    SEEKER_ID,
    ALERT_ID,
    _chain,
)

SAMPLE_ALERT = {
    "id": ALERT_ID,
    "user_id": SEEKER_ID,
    "name": "Python Jobs in Bangalore",
    "keyword": "Python",
    "location": "Bangalore",
    "job_type": "full-time",
    "category": None,
    "experience_min": None,
    "experience_max": None,
    "salary_min": None,
    "salary_max": None,
    "frequency": "daily",
    "is_active": True,
    "created_at": "2024-01-01T00:00:00",
}


class TestCreateJobAlert:

    @pytest.mark.asyncio
    async def test_create_alert_valid_data_returns_201(self, client, seeker_token):
        """[AL1] Valid alert creation → 201."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[SAMPLE_ALERT], count=1)
        sb.table.side_effect = [profile_chain, insert_chain]

        response = await client.post(
            "/api/job-alerts",
            json={
                "name": "Python Jobs in Bangalore",
                "keyword": "Python",
                "location": "Bangalore",
                "frequency": "daily",
            },
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Python Jobs in Bangalore"
        assert data["frequency"] == "daily"

    @pytest.mark.asyncio
    async def test_create_alert_unauthenticated_returns_403(self, client):
        """[AL2] No token → 403."""
        response = await client.post(
            "/api/job-alerts",
            json={"name": "Test Alert", "frequency": "daily"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_alert_invalid_frequency_returns_422(self, client, seeker_token):
        """[AL3] Invalid frequency value → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post(
            "/api/job-alerts",
            json={"name": "Test Alert", "frequency": "hourly"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_missing_name_returns_422(self, client, seeker_token):
        """[AL4] Missing name field → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post(
            "/api/job-alerts",
            json={"frequency": "daily"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_default_frequency_is_daily(self, client, seeker_token):
        """[AL5] Omitting frequency uses 'daily' default."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[SAMPLE_ALERT], count=1)
        sb.table.side_effect = [profile_chain, insert_chain]

        response = await client.post(
            "/api/job-alerts",
            json={"name": "My Alert"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_alert_weekly_frequency(self, client, seeker_token):
        """Weekly frequency is valid."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        weekly_alert = {**SAMPLE_ALERT, "frequency": "weekly"}
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[weekly_alert], count=1)
        sb.table.side_effect = [profile_chain, insert_chain]

        response = await client.post(
            "/api/job-alerts",
            json={"name": "Weekly Alert", "frequency": "weekly"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_alert_instant_frequency(self, client, seeker_token):
        """Instant frequency is valid."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        instant_alert = {**SAMPLE_ALERT, "frequency": "instant"}
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[instant_alert], count=1)
        sb.table.side_effect = [profile_chain, insert_chain]

        response = await client.post(
            "/api/job-alerts",
            json={"name": "Instant Alert", "frequency": "instant"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 201


class TestListJobAlerts:

    @pytest.mark.asyncio
    async def test_list_alerts_returns_200(self, client, seeker_token):
        """[AL6] Authenticated user gets their alerts."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        list_chain = _chain()
        list_chain.execute.return_value = MagicMock(data=[SAMPLE_ALERT], count=1)
        sb.table.side_effect = [profile_chain, list_chain]

        response = await client.get(
            "/api/job-alerts",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_list_alerts_unauthenticated_returns_403(self, client):
        """[AL7] No token → 403."""
        response = await client.get("/api/job-alerts")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_alerts_empty(self, client, seeker_token):
        """[AL8] No alerts → empty list."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        list_chain = _chain()
        list_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, list_chain]

        response = await client.get(
            "/api/job-alerts",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []


class TestUpdateJobAlert:

    @pytest.mark.asyncio
    async def test_owner_updates_alert(self, client, seeker_token):
        """[AL9] Owner can update their alert."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": SEEKER_ID}, count=1
        )
        updated = {**SAMPLE_ALERT, "keyword": "Django"}
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[updated], count=1)
        sb.table.side_effect = [profile_chain, existing_chain, update_chain]

        response = await client.put(
            f"/api/job-alerts/{ALERT_ID}",
            json={"keyword": "Django"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["keyword"] == "Django"

    @pytest.mark.asyncio
    async def test_non_owner_update_returns_403(self, client, seeker_token):
        """[AL10] Non-owner gets 403."""
        sb = client._mock_sb
        other_user_id = str(uuid.uuid4())
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": other_user_id}, count=1
        )
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.put(
            f"/api/job-alerts/{ALERT_ID}",
            json={"keyword": "Django"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_alert_returns_404(self, client, seeker_token):
        """[AL11] Alert not found → 404."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.put(
            f"/api/job-alerts/{uuid.uuid4()}",
            json={"keyword": "Django"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_alert_empty_body_returns_422(self, client, seeker_token):
        """[AL12] No update fields → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": SEEKER_ID}, count=1
        )
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.put(
            f"/api/job-alerts/{ALERT_ID}",
            json={},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_alert_invalid_frequency_returns_422(self, client, seeker_token):
        """[AL13] Invalid frequency on update → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": SEEKER_ID}, count=1
        )
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.put(
            f"/api/job-alerts/{ALERT_ID}",
            json={"frequency": "monthly"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_toggle_is_active(self, client, seeker_token):
        """[AL14] Can toggle is_active to False."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": SEEKER_ID}, count=1
        )
        deactivated = {**SAMPLE_ALERT, "is_active": False}
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[deactivated], count=1)
        sb.table.side_effect = [profile_chain, existing_chain, update_chain]

        response = await client.put(
            f"/api/job-alerts/{ALERT_ID}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestDeleteJobAlert:

    @pytest.mark.asyncio
    async def test_owner_deletes_alert(self, client, seeker_token):
        """[AL15] Owner deletes alert → 200."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": SEEKER_ID}, count=1
        )
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, existing_chain, delete_chain]

        response = await client.delete(
            f"/api/job-alerts/{ALERT_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_non_owner_delete_returns_403(self, client, seeker_token):
        """[AL16] Non-owner gets 403."""
        sb = client._mock_sb
        other_user_id = str(uuid.uuid4())
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(
            data={"id": ALERT_ID, "user_id": other_user_id}, count=1
        )
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.delete(
            f"/api/job-alerts/{ALERT_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_alert_returns_404(self, client, seeker_token):
        """[AL17] Alert not found → 404."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.delete(
            f"/api/job-alerts/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404
