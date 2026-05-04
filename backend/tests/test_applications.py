"""
test_applications.py — Tests for /api/applications/ and /api/jobs/{id}/applicants routes.

Behaviours covered
------------------
Apply for a job
  [A1]  Seeker applies to active job → 201
  [A2]  Seeker applies to non-existent job → 404
  [A3]  Seeker applies to closed/inactive job → 400
  [A4]  Duplicate application → 409
  [A5]  Employer tries to apply → 403 (seeker only)
  [A6]  Unauthenticated apply → 403

My applications
  [A7]  Seeker lists own applications → 200 with results
  [A8]  Employer tries to list seeker applications → 403

View job applicants
  [A9]  Employer views applicants for own job → 200
  [A10] Employer views applicants for other's job → 403
  [A11] Seeker tries to view applicants → 403
  [A12] Job not found → 404

Update application status
  [A13] Employer updates status to shortlisted → 200
  [A14] Employer updates status for app on other's job → 403
  [A15] Application not found → 404
  [A16] Invalid status value → 422

Withdraw application
  [A17] Seeker withdraws own application → 200
  [A18] Seeker withdraws other seeker's application → 403
  [A19] Withdraw decided application (offered/rejected) → 400
  [A20] Application not found → 404
"""

import uuid
from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    SEEKER_PROFILE,
    EMPLOYER_PROFILE,
    SAMPLE_JOB,
    SAMPLE_APPLICATION,
    JOB_ID,
    SEEKER_ID,
    EMPLOYER_ID,
    COMPANY_ID,
    APPLICATION_ID,
    _chain,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _make_job(status="active", posted_by=EMPLOYER_ID):
    return {
        "id": JOB_ID,
        "status": status,
        "posted_by": posted_by,
        "company_id": COMPANY_ID,
        "title": "Senior Python Developer",
    }


# ────────────────────────────────────────────────────────────────────────────
# Apply for job
# ────────────────────────────────────────────────────────────────────────────

class TestApplyForJob:

    @pytest.mark.asyncio
    async def test_seeker_applies_to_active_job_returns_201(self, client, seeker_token):
        """[A1] Valid application from seeker → 201."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=_make_job("active"), count=1)

        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=[], count=0)

        resume_chain = _chain()
        resume_chain.execute.return_value = MagicMock(data={"resume_url": None}, count=1)

        insert_chain = _chain()
        new_app = {**SAMPLE_APPLICATION}
        insert_chain.execute.return_value = MagicMock(data=[new_app], count=1)

        sb.table.side_effect = [
            profile_chain,   # get_current_user profile lookup
            job_chain,       # job existence check
            existing_chain,  # duplicate check
            resume_chain,    # profile resume lookup
            insert_chain,    # insert application
        ]

        response = await client.post(
            f"/api/applications/{JOB_ID}",
            json={"cover_letter": "I am excited about this role."},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == JOB_ID
        assert data["applicant_id"] == SEEKER_ID
        assert data["status"] == "applied"

    @pytest.mark.asyncio
    async def test_apply_to_nonexistent_job_returns_404(self, client, seeker_token):
        """[A2] Job not found → 404."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, job_chain]

        response = await client.post(
            f"/api/applications/{uuid.uuid4()}",
            json={"cover_letter": "Hello"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_to_closed_job_returns_400(self, client, seeker_token):
        """[A3] Closed job → 400."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=_make_job("closed"), count=1)
        sb.table.side_effect = [profile_chain, job_chain]

        response = await client.post(
            f"/api/applications/{JOB_ID}",
            json={"cover_letter": "Hello"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 400
        assert "no longer" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_duplicate_application_returns_409(self, client, seeker_token):
        """[A4] Already applied → 409."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=_make_job("active"), count=1)
        existing_chain = _chain()
        existing_chain.execute.return_value = MagicMock(data=[{"id": APPLICATION_ID}], count=1)
        sb.table.side_effect = [profile_chain, job_chain, existing_chain]

        response = await client.post(
            f"/api/applications/{JOB_ID}",
            json={},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 409
        assert "already applied" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_employer_cannot_apply_returns_403(self, client, employer_token):
        """[A5] Employer role → 403 (seeker only endpoint)."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post(
            f"/api/applications/{JOB_ID}",
            json={},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_apply_returns_403(self, client):
        """[A6] No token → 403."""
        response = await client.post(f"/api/applications/{JOB_ID}", json={})
        assert response.status_code == 403


# ────────────────────────────────────────────────────────────────────────────
# My Applications
# ────────────────────────────────────────────────────────────────────────────

class TestMyApplications:

    @pytest.mark.asyncio
    async def test_seeker_lists_own_applications(self, client, seeker_token):
        """[A7] Seeker gets own applications list → 200."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        apps_chain = _chain()
        apps_chain.execute.return_value = MagicMock(data=[SAMPLE_APPLICATION], count=1)
        sb.table.side_effect = [profile_chain, apps_chain]

        response = await client.get(
            "/api/applications/my",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_employer_cannot_list_seeker_applications(self, client, employer_token):
        """[A8] Employer role → 403 (seeker-only route)."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.get(
            "/api/applications/my",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403


# ────────────────────────────────────────────────────────────────────────────
# View Applicants (employer)
# ────────────────────────────────────────────────────────────────────────────

class TestViewApplicants:

    @pytest.mark.asyncio
    async def test_employer_views_applicants_for_own_job(self, client, employer_token):
        """[A9] Employer can view applicants for their own job."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": EMPLOYER_ID, "title": "Dev Job"}, count=1
        )
        applicants_chain = _chain()
        applicants_chain.execute.return_value = MagicMock(data=[SAMPLE_APPLICATION], count=1)
        sb.table.side_effect = [profile_chain, job_chain, applicants_chain]

        response = await client.get(
            f"/api/jobs/{JOB_ID}/applicants",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_employer_cannot_view_other_employers_applicants(self, client, employer_token):
        """[A10] Employer gets 403 for job they don't own."""
        sb = client._mock_sb
        other_id = str(uuid.uuid4())

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": other_id, "title": "Other Job"}, count=1
        )
        sb.table.side_effect = [profile_chain, job_chain]

        response = await client.get(
            f"/api/jobs/{JOB_ID}/applicants",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_seeker_cannot_view_applicants(self, client, seeker_token):
        """[A11] Seeker role → 403 (employer-only route)."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.get(
            f"/api/jobs/{JOB_ID}/applicants",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_view_applicants_job_not_found(self, client, employer_token):
        """[A12] Non-existent job → 404."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, job_chain]

        response = await client.get(
            f"/api/jobs/{uuid.uuid4()}/applicants",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# Update Application Status
# ────────────────────────────────────────────────────────────────────────────

class TestUpdateApplicationStatus:

    @pytest.mark.asyncio
    async def test_employer_updates_status_to_shortlisted(self, client, employer_token):
        """[A13] Employer successfully changes status to shortlisted."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)

        app_with_job = {
            **SAMPLE_APPLICATION,
            "jobs": {"posted_by": EMPLOYER_ID},
        }
        app_chain = _chain()
        app_chain.execute.return_value = MagicMock(data=app_with_job, count=1)

        updated = {**SAMPLE_APPLICATION, "status": "shortlisted"}
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[updated], count=1)

        sb.table.side_effect = [profile_chain, app_chain, update_chain]

        response = await client.put(
            f"/api/applications/{APPLICATION_ID}/status",
            json={"status": "shortlisted"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "shortlisted"

    @pytest.mark.asyncio
    async def test_employer_cannot_update_other_employers_application(self, client, employer_token):
        """[A14] Application on another employer's job → 403."""
        sb = client._mock_sb
        other_id = str(uuid.uuid4())

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        app_with_job = {
            **SAMPLE_APPLICATION,
            "jobs": {"posted_by": other_id},
        }
        app_chain = _chain()
        app_chain.execute.return_value = MagicMock(data=app_with_job, count=1)
        sb.table.side_effect = [profile_chain, app_chain]

        response = await client.put(
            f"/api/applications/{APPLICATION_ID}/status",
            json={"status": "shortlisted"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_status_application_not_found(self, client, employer_token):
        """[A15] Non-existent application → 404."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        app_chain = _chain()
        app_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, app_chain]

        response = await client.put(
            f"/api/applications/{uuid.uuid4()}/status",
            json={"status": "shortlisted"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_invalid_value_returns_422(self, client, employer_token):
        """[A16] Invalid status value → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.put(
            f"/api/applications/{APPLICATION_ID}/status",
            json={"status": "unknown_status_xyz"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# Withdraw Application
# ────────────────────────────────────────────────────────────────────────────

class TestWithdrawApplication:

    @pytest.mark.asyncio
    async def test_seeker_withdraws_own_application(self, client, seeker_token):
        """[A17] Seeker withdraws their own application → 200."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        app_chain = _chain()
        app_chain.execute.return_value = MagicMock(
            data={"id": APPLICATION_ID, "applicant_id": SEEKER_ID, "job_id": JOB_ID, "status": "applied"},
            count=1,
        )
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, app_chain, delete_chain]

        response = await client.delete(
            f"/api/applications/{APPLICATION_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_seeker_cannot_withdraw_others_application(self, client, seeker_token):
        """[A18] Seeker cannot withdraw another seeker's application → 403."""
        sb = client._mock_sb
        other_seeker_id = str(uuid.uuid4())

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        app_chain = _chain()
        app_chain.execute.return_value = MagicMock(
            data={"id": APPLICATION_ID, "applicant_id": other_seeker_id, "job_id": JOB_ID, "status": "applied"},
            count=1,
        )
        sb.table.side_effect = [profile_chain, app_chain]

        response = await client.delete(
            f"/api/applications/{APPLICATION_ID}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_withdraw_decided_application_returns_400(self, client, seeker_token):
        """[A19] Cannot withdraw offered or rejected application → 400."""
        sb = client._mock_sb

        for decided_status in ("offered", "rejected"):
            profile_chain = _chain()
            profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
            app_chain = _chain()
            app_chain.execute.return_value = MagicMock(
                data={"id": APPLICATION_ID, "applicant_id": SEEKER_ID, "job_id": JOB_ID, "status": decided_status},
                count=1,
            )
            sb.table.side_effect = [profile_chain, app_chain]

            response = await client.delete(
                f"/api/applications/{APPLICATION_ID}",
                headers={"Authorization": f"Bearer {seeker_token}"},
            )
            assert response.status_code == 400, f"Expected 400 for status={decided_status}"

    @pytest.mark.asyncio
    async def test_withdraw_nonexistent_application_returns_404(self, client, seeker_token):
        """[A20] Non-existent application → 404."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        app_chain = _chain()
        app_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, app_chain]

        response = await client.delete(
            f"/api/applications/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404
