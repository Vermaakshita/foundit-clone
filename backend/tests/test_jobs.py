"""
test_jobs.py — Tests for /api/jobs/ routes.

Behaviours covered
------------------
Search / List
  [J1]  GET /api/jobs → 200 with paginated list
  [J2]  Filter by keyword (title/description/category)
  [J3]  Filter by location
  [J4]  Filter by job_type
  [J5]  Filter by experience range
  [J6]  Filter by salary range
  [J7]  Filter is_remote=true
  [J8]  Pagination: page=2, limit=5
  [J9]  Pagination limit out of range → 422

Featured / Recommended / Categories
  [J10] GET /api/jobs/featured → 200, list
  [J11] GET /api/jobs/recommended → 200, requires auth
  [J12] GET /api/jobs/recommended without auth → 403
  [J13] GET /api/jobs/categories → 200, list

Get by ID
  [J14] GET /api/jobs/{id} valid → 200 with job + company
  [J15] GET /api/jobs/{id} not found → 404

Create (employer only)
  [J16] POST /api/jobs authenticated employer → 201
  [J17] POST /api/jobs seeker → 403
  [J18] POST /api/jobs unauthenticated → 403
  [J19] POST /api/jobs missing title → 422
  [J20] POST /api/jobs missing description → 422

Update (employer only, must own job)
  [J21] PUT /api/jobs/{id} owner → 200
  [J22] PUT /api/jobs/{id} non-owner employer → 403
  [J23] PUT /api/jobs/{id} not found → 404
  [J24] PUT /api/jobs/{id} no fields → 422

Delete (employer only, must own job)
  [J25] DELETE /api/jobs/{id} owner → 200
  [J26] DELETE /api/jobs/{id} non-owner → 403
  [J27] DELETE /api/jobs/{id} not found → 404

Supabase compliance
  [J28] No raw SQL strings in router source
"""

import uuid
from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    SEEKER_PROFILE,
    EMPLOYER_PROFILE,
    SAMPLE_JOB,
    JOB_ID,
    EMPLOYER_ID,
    COMPANY_ID,
    _chain,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _setup_profile(sb, profile):
    """Configure sb.table(...) to return the given profile for auth checks."""
    chain = _chain()
    chain.execute.return_value = MagicMock(data=profile, count=1)
    sb.table.return_value = chain


def _setup_jobs_list(sb, jobs, total=None):
    """Configure sb.table(...) to return a list of jobs with count."""
    if total is None:
        total = len(jobs)
    chain = _chain()
    chain.execute.return_value = MagicMock(data=jobs, count=total)
    sb.table.return_value = chain


# ────────────────────────────────────────────────────────────────────────────
# Search / List
# ────────────────────────────────────────────────────────────────────────────

class TestJobSearch:

    @pytest.mark.asyncio
    async def test_list_jobs_returns_200(self, client):
        """[J1] Basic job listing returns 200 with pagination wrapper."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [SAMPLE_JOB], total=1)

        response = await client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data

    @pytest.mark.asyncio
    async def test_search_jobs_by_keyword(self, client):
        """[J2] keyword query param is applied."""
        sb = client._mock_sb

        # Router calls table("jobs") first (built as the main query),
        # then table("companies") inline inside the keyword branch.
        jobs_chain = _chain()
        jobs_chain.execute.return_value = MagicMock(data=[SAMPLE_JOB], count=1)
        company_chain = _chain()
        company_chain.execute.return_value = MagicMock(data=[], count=0)

        sb.table.side_effect = [jobs_chain, company_chain]

        response = await client.get("/api/jobs?keyword=Python")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_search_jobs_by_location(self, client):
        """[J3] location filter applied."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [SAMPLE_JOB], total=1)

        response = await client.get("/api/jobs?location=Bangalore")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_jobs_by_job_type(self, client):
        """[J4] job_type filter applied."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [SAMPLE_JOB], total=1)

        response = await client.get("/api/jobs?job_type=full-time")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_jobs_by_experience_range(self, client):
        """[J5] experience_min and experience_max filters applied."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [SAMPLE_JOB], total=1)

        response = await client.get("/api/jobs?experience_min=2&experience_max=6")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_jobs_by_salary_range(self, client):
        """[J6] salary_min and salary_max filters applied."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [SAMPLE_JOB], total=1)

        response = await client.get("/api/jobs?salary_min=500000&salary_max=2000000")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_jobs_is_remote(self, client):
        """[J7] is_remote=true filter applied."""
        sb = client._mock_sb
        remote_job = {**SAMPLE_JOB, "is_remote": True}
        _setup_jobs_list(sb, [remote_job], total=1)

        response = await client.get("/api/jobs?is_remote=true")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_jobs_pagination(self, client):
        """[J8] page=2 and limit=5 reflected in response."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [], total=12)

        response = await client.get("/api/jobs?page=2&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 5
        assert data["total_pages"] == 3  # ceil(12/5)

    @pytest.mark.asyncio
    async def test_search_jobs_limit_exceeds_max_returns_422(self, client):
        """[J9] limit > 100 → 422."""
        response = await client.get("/api/jobs?limit=200")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_jobs_empty_results(self, client):
        """Empty result set handled gracefully."""
        sb = client._mock_sb
        _setup_jobs_list(sb, [], total=0)

        response = await client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []
        assert data["total_pages"] == 0


# ────────────────────────────────────────────────────────────────────────────
# Featured / Recommended / Categories
# ────────────────────────────────────────────────────────────────────────────

class TestJobSpecialEndpoints:

    @pytest.mark.asyncio
    async def test_get_featured_jobs_returns_200(self, client):
        """[J10] /featured returns list of up to 6 jobs."""
        sb = client._mock_sb
        chain = _chain()
        chain.execute.return_value = MagicMock(data=[SAMPLE_JOB], count=1)
        sb.table.return_value = chain

        response = await client.get("/api/jobs/featured")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_recommended_jobs_authenticated(self, client, seeker_token):
        """[J11] /recommended with valid auth → 200."""
        sb = client._mock_sb

        # First call: profile lookup for auth
        # Second call: jobs query
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        jobs_chain = _chain()
        jobs_chain.execute.return_value = MagicMock(data=[SAMPLE_JOB], count=1)
        sb.table.side_effect = [profile_chain, jobs_chain]

        response = await client.get(
            "/api/jobs/recommended",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_recommended_jobs_unauthenticated_returns_403(self, client):
        """[J12] /recommended without auth → 403."""
        response = await client.get("/api/jobs/recommended")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_job_categories_returns_list(self, client):
        """[J13] /categories returns list."""
        sb = client._mock_sb
        chain = _chain()
        chain.execute.return_value = MagicMock(
            data=[
                {"category": "Engineering"},
                {"category": "Engineering"},
                {"category": "Design"},
            ],
            count=3,
        )
        sb.table.return_value = chain

        response = await client.get("/api/jobs/categories")
        assert response.status_code == 200
        cats = response.json()
        assert isinstance(cats, list)
        # Engineering should be first (2 > 1)
        if cats:
            assert cats[0]["category"] == "Engineering"
            assert cats[0]["count"] == 2


# ────────────────────────────────────────────────────────────────────────────
# Get by ID
# ────────────────────────────────────────────────────────────────────────────

class TestGetJobDetail:

    @pytest.mark.asyncio
    async def test_get_job_detail_valid_id_returns_200(self, client):
        """[J14] Valid job ID → 200 with job data."""
        sb = client._mock_sb

        # First call: single job lookup
        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=SAMPLE_JOB, count=1)
        # Second call: views_count update
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[SAMPLE_JOB], count=1)
        sb.table.side_effect = [job_chain, update_chain]

        response = await client.get(f"/api/jobs/{JOB_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == JOB_ID
        assert data["title"] == SAMPLE_JOB["title"]

    @pytest.mark.asyncio
    async def test_get_job_detail_not_found_returns_404(self, client):
        """[J15] Non-existent job ID → 404."""
        sb = client._mock_sb
        chain = _chain()
        chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.return_value = chain

        response = await client.get(f"/api/jobs/{uuid.uuid4()}")
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_get_job_detail_increments_views_count(self, client):
        """[J14b] Views count is incremented on each GET."""
        sb = client._mock_sb
        job_with_views = {**SAMPLE_JOB, "views_count": 5}

        job_chain = _chain()
        job_chain.execute.return_value = MagicMock(data=job_with_views, count=1)
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[{**job_with_views, "views_count": 6}], count=1)
        sb.table.side_effect = [job_chain, update_chain]

        response = await client.get(f"/api/jobs/{JOB_ID}")
        assert response.status_code == 200
        # views_count should be 6 (5 + 1)
        assert response.json()["views_count"] == 6


# ────────────────────────────────────────────────────────────────────────────
# Create Job
# ────────────────────────────────────────────────────────────────────────────

VALID_JOB_PAYLOAD = {
    "title": "Backend Engineer",
    "description": "Build scalable APIs",
    "location": "Remote",
    "job_type": "full-time",
    "category": "Engineering",
}


class TestCreateJob:

    @pytest.mark.asyncio
    async def test_create_job_employer_returns_201(self, client, employer_token):
        """[J16] Employer can create a job → 201."""
        sb = client._mock_sb

        # Call order: profile (auth), job insert
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        insert_chain = _chain()
        new_job = {**SAMPLE_JOB, "id": str(uuid.uuid4()), "company_id": None}
        insert_chain.execute.return_value = MagicMock(data=[new_job], count=1)
        sb.table.side_effect = [profile_chain, insert_chain]

        response = await client.post(
            "/api/jobs",
            json=VALID_JOB_PAYLOAD,
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_job_seeker_returns_403(self, client, seeker_token):
        """[J17] Seeker cannot post a job → 403."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post(
            "/api/jobs",
            json=VALID_JOB_PAYLOAD,
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 403
        assert "employer" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_create_job_unauthenticated_returns_403(self, client):
        """[J18] No token → 403."""
        response = await client.post("/api/jobs", json=VALID_JOB_PAYLOAD)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_job_missing_title_returns_422(self, client, employer_token):
        """[J19] Missing title → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        payload = {**VALID_JOB_PAYLOAD}
        del payload["title"]

        response = await client.post(
            "/api/jobs",
            json=payload,
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_job_missing_description_returns_422(self, client, employer_token):
        """[J20] Missing description → 422."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        payload = {**VALID_JOB_PAYLOAD}
        del payload["description"]

        response = await client.post(
            "/api/jobs",
            json=payload,
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_job_with_company_id_verifies_ownership(self, client, employer_token):
        """Employer with mismatched company_id gets 403."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        # Company ownership check returns no data (not owner)
        company_chain = _chain()
        company_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, company_chain]

        response = await client.post(
            "/api/jobs",
            json={**VALID_JOB_PAYLOAD, "company_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403


# ────────────────────────────────────────────────────────────────────────────
# Update Job
# ────────────────────────────────────────────────────────────────────────────

class TestUpdateJob:

    @pytest.mark.asyncio
    async def test_update_job_owner_returns_200(self, client, employer_token):
        """[J21] Owner can update their job."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)

        ownership_chain = _chain()
        ownership_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": EMPLOYER_ID}, count=1
        )
        updated_job = {**SAMPLE_JOB, "title": "Updated Title"}
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[updated_job], count=1)

        sb.table.side_effect = [profile_chain, ownership_chain, update_chain]

        response = await client.put(
            f"/api/jobs/{JOB_ID}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_job_non_owner_returns_403(self, client, employer_token):
        """[J22] Non-owner employer gets 403."""
        sb = client._mock_sb
        other_employer_id = str(uuid.uuid4())

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        ownership_chain = _chain()
        ownership_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": other_employer_id}, count=1
        )
        sb.table.side_effect = [profile_chain, ownership_chain]

        response = await client.put(
            f"/api/jobs/{JOB_ID}",
            json={"title": "Hijack Title"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_job_not_found_returns_404(self, client, employer_token):
        """[J23] Non-existent job ID → 404."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        not_found_chain = _chain()
        not_found_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, not_found_chain]

        response = await client.put(
            f"/api/jobs/{uuid.uuid4()}",
            json={"title": "New Title"},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_job_no_fields_returns_422(self, client, employer_token):
        """[J24] Empty body → 422 (no update fields provided)."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        ownership_chain = _chain()
        ownership_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": EMPLOYER_ID}, count=1
        )
        sb.table.side_effect = [profile_chain, ownership_chain]

        response = await client.put(
            f"/api/jobs/{JOB_ID}",
            json={},
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# Delete Job
# ────────────────────────────────────────────────────────────────────────────

class TestDeleteJob:

    @pytest.mark.asyncio
    async def test_delete_job_owner_returns_200(self, client, employer_token):
        """[J25] Owner deletes job → 200."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        ownership_chain = _chain()
        ownership_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": EMPLOYER_ID}, count=1
        )
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [profile_chain, ownership_chain, delete_chain]

        response = await client.delete(
            f"/api/jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_delete_job_non_owner_returns_403(self, client, employer_token):
        """[J26] Non-owner employer gets 403."""
        sb = client._mock_sb
        other_id = str(uuid.uuid4())
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        ownership_chain = _chain()
        ownership_chain.execute.return_value = MagicMock(
            data={"id": JOB_ID, "posted_by": other_id}, count=1
        )
        sb.table.side_effect = [profile_chain, ownership_chain]

        response = await client.delete(
            f"/api/jobs/{JOB_ID}",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_job_not_found_returns_404(self, client, employer_token):
        """[J27] Non-existent job ID → 404."""
        sb = client._mock_sb
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=EMPLOYER_PROFILE, count=1)
        not_found_chain = _chain()
        not_found_chain.execute.return_value = MagicMock(data=None, count=0)
        sb.table.side_effect = [profile_chain, not_found_chain]

        response = await client.delete(
            f"/api/jobs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {employer_token}"},
        )
        assert response.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# Supabase compliance
# ────────────────────────────────────────────────────────────────────────────

class TestSupabaseCompliance:

    def test_no_raw_sql_strings_in_jobs_router(self):
        """[J28] jobs.py must not contain raw SQL (execute_sql / text() / raw sql strings)."""
        import pathlib
        router_path = pathlib.Path(__file__).parent.parent / "app" / "routers" / "jobs.py"
        source = router_path.read_text()
        # These patterns indicate raw SQL usage
        forbidden = ["execute_sql", "text(", "raw_sql", "cursor.execute", "db.execute(\""]
        for pattern in forbidden:
            assert pattern not in source, (
                f"Raw SQL pattern '{pattern}' found in jobs.py — violates Supabase client rule"
            )
