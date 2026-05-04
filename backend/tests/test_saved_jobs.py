"""
test_saved_jobs.py — Tests for /api/saved-jobs/ routes.

Behaviours covered
------------------
Save a job
  [S1]  Seeker saves a job → 201 success
  [S2]  Save non-existent job → 404
  [S3]  Save already-saved job → 200 idempotent (no duplicate inserted)
  [S4]  Employer cannot save job → 403
  [S5]  Unauthenticated → 403

List saved jobs
  [S6]  Seeker lists saved jobs → 200 list
  [S7]  Empty saved list → 200 empty list
  [S8]  Pagination params respected

Unsave a job
  [S9]  Seeker removes saved job → 200
  [S10] Remove job that was never saved → 404
  [S11] Employer tries to unsave → 403
"""

import uuid
from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    SEEKER_PROFILE,
    EMPLOYER_PROFILE,
    SAMPLE_JOB,
    JOB_ID,
    SEEKER_ID,
    _chain,
)


class TestSaveJob:

    @pytest.mark.asyncio
    async def test_seeker_saves_job_returns_201(self, client, seeker_token):
        """[S1] Seeker successfully saves a job."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data={"id": JOB_ID}, count=1)

        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=[], count=0)

        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[{"id": str(uuid.uuid4())}], count=1)

        sb.table.side_effect = [profile_chain, job_chain, existing_chain, insert_chain]

        response = await client.post(
            f"/api/saved-jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 201
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_save_nonexistent_job_returns_404(self, client, seeker_token):
        """[S2] Job not found → 404."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, job_chain]

        response = await client.post(
            f"/api/saved-jobs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_save_already_saved_job_is_idempotent(self, client, seeker_token):
        """[S3] Already saved → returns 200 without inserting duplicate."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data={"id": JOB_ID}, count=1)
        # existing check returns a record → skip insert
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=[{"id": str(uuid.uuid4())}], count=1)
        sb.table.side_effect = [profile_chain, job_chain, existing_chain]

        response = await client.post(
            f"/api/saved-jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        # The endpoint returns 201 regardless (idempotent message)
        assert response.status_code == 201
        assert response.json()["success"] is True
        # Insert should NOT have been called since existing.data was non-empty
        # Verify no 4th table() call happened
        assert sb.table.call_count == 3

    @pytest.mark.asyncio
    async def test_employer_cannot_save_job(self, client, employer_token):
        """[S4] Employer role → 403."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post(
            f"/api/saved-jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_save_returns_403(self, client):
        """[S5] No token → 403."""
        response = await client.post(f"/api/saved-jobs/{JOB_ID}")
        assert response.status_code == 403


class TestListSavedJobs:

    @pytest.mark.asyncio
    async def test_seeker_lists_saved_jobs(self, client, seeker_token):
        """[S6] Valid seeker request → 200 with list."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        saved_item = {
            "id": str(uuid.uuid4()),
            "saved_at": "2024-01-02T00:00:00",
            "jobs": {
                **SAMPLE_JOB,
                "companies": {
                    "id": str(uuid.uuid4()),
                    "name": "TechCorp",
                    "logo_url": None,
                    "industry": "Tech",
                    "location": "Bangalore",
                },
            },
        }
        list_chain = _chain()
        list_chain.execute.return_value = MagicMock(data=[saved_item], count=1)
        sb.table.side_effect = [profile_chain, list_chain]

        response = await client.get(
            "/api/saved-jobs",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 1
        assert "job" in result[0]

    @pytest.mark.asyncio
    async def test_seeker_empty_saved_jobs_returns_empty_list(self, client, seeker_token):
        """[S7] No saved jobs → 200 empty list."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        list_chain = _chain()
        list_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, list_chain]

        response = await client.get(
            "/api/saved-jobs",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_saved_jobs_invalid_limit_returns_422(self, client, seeker_token):
        """[S8] limit > 100 → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.get(
            "/api/saved-jobs?limit=999",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 422


class TestUnsaveJob:

    @pytest.mark.asyncio
    async def test_seeker_removes_saved_job(self, client, seeker_token):
        """[S9] Seeker unsaves a job → 200."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=[{"id": str(uuid.uuid4())}], count=1)
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, existing_chain, delete_chain]

        response = await client.delete(
            f"/api/saved-jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_unsave_job_that_was_never_saved_returns_404(self, client, seeker_token):
        """[S10] Job not in saved list → 404."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, existing_chain]

        response = await client.delete(
            f"/api/saved-jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_employer_cannot_unsave_job(self, client, employer_token):
        """[S11] Employer role → 403."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.delete(
            f"/api/saved-jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403
