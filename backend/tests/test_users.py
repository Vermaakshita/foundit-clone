"""
test_users.py — Tests for /api/users/ routes.

Behaviours covered
------------------
Get profile
  [U1]  Authenticated user gets own profile → 200 with skills/education/experience
  [U2]  Unauthenticated → 403
  [U3]  Profile not found in DB → 404

Update profile
  [U4]  Valid partial update → 200
  [U5]  Empty body → 422
  [U6]  Unauthenticated → 403

Update skills
  [U7]  Valid skills list → 200
  [U8]  Empty skills list → 200 (clears skills)
  [U9]  Unauthenticated → 403

Update education
  [U10] Valid education records → 200
  [U11] Empty list clears education → 200

Update experience
  [U12] Valid experience records → 200
  [U13] Empty list clears experience → 200

Resume upload
  [U14] Valid PDF upload → 200 with resume_url
  [U15] Non-PDF file → 400
  [U16] File too large → 413

Delete resume
  [U17] Authenticated → 200
"""

import io
import uuid
from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    SEEKER_PROFILE,
    SEEKER_ID,
    _chain,
)


class TestGetProfile:

    @pytest.mark.asyncio
    async def test_get_profile_returns_200_with_full_data(self, client, seeker_token):
        """[U1] Authenticated user gets full profile including related data."""
        sb = client._mock_sb

        # 1. get_current_user: profile lookup
        auth_profile_chain = _chain()
        auth_profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        # 2. /profile route: profile lookup again
        route_profile_chain = _chain()
        route_profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        # 3. Education
        edu_chain = _chain()
        edu_chain.execute.return_value = MagicMock(
            data=[{"id": str(uuid.uuid4()), "institution": "IIT Delhi", "degree": "B.Tech"}],
            count=1,
        )

        # 4. Experience
        exp_chain = _chain()
        exp_chain.execute.return_value = MagicMock(
            data=[{"id": str(uuid.uuid4()), "company_name": "Infosys", "title": "SDE"}],
            count=1,
        )

        # 5. Skills
        skills_chain = _chain()
        skills_chain.execute.return_value = MagicMock(
            data=[{"skill_name": "Python"}, {"skill_name": "FastAPI"}],
            count=2,
        )

        sb.table.side_effect = [
            auth_profile_chain,
            route_profile_chain,
            edu_chain,
            exp_chain,
            skills_chain,
        ]

        response = await client.get(
            "/api/users/profile",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == SEEKER_PROFILE["email"]
        assert isinstance(data["education"], list)
        assert isinstance(data["experience"], list)
        assert isinstance(data["skills"], list)

    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated_returns_403(self, client):
        """[U2] No token → 403."""
        response = await client.get("/api/users/profile")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_profile_not_found_returns_404(self, client, seeker_token):
        """[U3] Profile not found in DB → 404."""
        sb = client._mock_sb

        # Auth lookup succeeds (so JWT validation passes)
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        # Route's own lookup returns nothing
        not_found_chain = _chain()
        not_found_chain.execute.return_value = MagicMock(data=None, count=0)

        sb.table.side_effect = [auth_chain, not_found_chain]

        response = await client.get(
            "/api/users/profile",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 404


class TestUpdateProfile:

    @pytest.mark.asyncio
    async def test_update_profile_valid_fields(self, client, seeker_token):
        """[U4] Valid partial update returns updated profile."""
        sb = client._mock_sb

        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        updated_profile = {**SEEKER_PROFILE, "headline": "Senior Developer", "location": "Hyderabad"}
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[updated_profile], count=1)

        edu_chain = _chain()
        edu_chain.execute.return_value = MagicMock(data=[], count=0)
        exp_chain = _chain()
        exp_chain.execute.return_value = MagicMock(data=[], count=0)

        sb.table.side_effect = [auth_chain, update_chain, edu_chain, exp_chain]

        response = await client.put(
            "/api/users/profile",
            json={"headline": "Senior Developer", "location": "Hyderabad"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["headline"] == "Senior Developer"

    @pytest.mark.asyncio
    async def test_update_profile_empty_body_returns_422(self, client, seeker_token):
        """[U5] Empty JSON body → 422 (no update fields)."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = auth_chain

        response = await client.put(
            "/api/users/profile",
            json={},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated_returns_403(self, client):
        """[U6] No token → 403."""
        response = await client.put(
            "/api/users/profile",
            json={"headline": "New Headline"},
        )
        assert response.status_code == 403


class TestUpdateSkills:

    @pytest.mark.asyncio
    async def test_update_skills_valid_list(self, client, seeker_token):
        """[U7] Valid skills list → 200."""
        sb = client._mock_sb

        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        # delete existing skills
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)

        # insert new skills
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(
            data=[{"user_id": SEEKER_ID, "skill_name": "Python"},
                  {"user_id": SEEKER_ID, "skill_name": "React"}],
            count=2,
        )

        sb.table.side_effect = [auth_chain, delete_chain, insert_chain]

        response = await client.put(
            "/api/users/skills",
            json={"skills": ["Python", "React"]},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_update_skills_empty_list_clears_skills(self, client, seeker_token):
        """[U8] Empty list → 200, clears all skills."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [auth_chain, delete_chain]

        response = await client.put(
            "/api/users/skills",
            json={"skills": []},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_skills_unauthenticated_returns_403(self, client):
        """[U9] No token → 403."""
        response = await client.put("/api/users/skills", json={"skills": ["Python"]})
        assert response.status_code == 403


class TestUpdateEducation:

    @pytest.mark.asyncio
    async def test_upsert_education_valid_records(self, client, seeker_token):
        """[U10] Valid education records → 200."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[{"id": str(uuid.uuid4())}], count=1)
        sb.table.side_effect = [auth_chain, delete_chain, insert_chain]

        response = await client.put(
            "/api/users/education",
            json=[{
                "institution": "IIT Bombay",
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "start_year": 2018,
                "end_year": 2022,
                "is_current": False,
            }],
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_upsert_education_empty_list_clears(self, client, seeker_token):
        """[U11] Empty list clears all education records."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [auth_chain, delete_chain]

        response = await client.put(
            "/api/users/education",
            json=[],
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200


class TestUpdateExperience:

    @pytest.mark.asyncio
    async def test_upsert_experience_valid_records(self, client, seeker_token):
        """[U12] Valid experience records → 200."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        insert_chain = _chain()
        insert_chain.execute.return_value = MagicMock(data=[{"id": str(uuid.uuid4())}], count=1)
        sb.table.side_effect = [auth_chain, delete_chain, insert_chain]

        response = await client.put(
            "/api/users/experience",
            json=[{
                "company_name": "Wipro",
                "title": "Software Engineer",
                "start_date": "2022-01-01",
                "is_current": True,
            }],
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_upsert_experience_empty_list_clears(self, client, seeker_token):
        """[U13] Empty list clears all experience records."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        delete_chain = _chain()
        delete_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.side_effect = [auth_chain, delete_chain]

        response = await client.put(
            "/api/users/experience",
            json=[],
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200


class TestResumeUpload:

    @pytest.mark.asyncio
    async def test_upload_valid_pdf_returns_200(self, client, seeker_token):
        """[U14] Valid PDF upload → 200 with resume_url."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[SEEKER_PROFILE], count=1)
        sb.table.side_effect = [auth_chain, update_chain]

        pdf_content = b"%PDF-1.4 fake pdf content"
        response = await client.post(
            "/api/users/resume/upload",
            files={"file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "resume_url" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_upload_non_pdf_returns_400(self, client, seeker_token):
        """[U15] Non-PDF/Word file → 400."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = auth_chain

        response = await client.post(
            "/api/users/resume/upload",
            files={"file": ("photo.jpg", io.BytesIO(b"fake jpg"), "image/jpeg")},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 400
        assert "pdf" in response.json()["message"].lower() or "word" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_upload_oversized_file_returns_413(self, client, seeker_token):
        """[U16] File > 5MB → 413."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = auth_chain

        # 6 MB of zeros
        large_content = b"0" * (6 * 1024 * 1024)
        response = await client.post(
            "/api/users/resume/upload",
            files={"file": ("big.pdf", io.BytesIO(large_content), "application/pdf")},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 413


class TestDeleteResume:

    @pytest.mark.asyncio
    async def test_delete_resume_returns_200(self, client, seeker_token):
        """[U17] Authenticated user deletes resume → 200."""
        sb = client._mock_sb
        auth_chain = _chain()
        auth_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)

        profile_chain = _chain()
        profile_with_resume = {**SEEKER_PROFILE, "resume_url": "https://storage.example.com/resume.pdf"}
        profile_chain.execute.return_value = MagicMock(data=profile_with_resume, count=1)

        update_chain = _chain()
        update_chain.execute.return_value = MagicMock(data=[SEEKER_PROFILE], count=1)

        sb.table.side_effect = [auth_chain, profile_chain, update_chain]

        response = await client.delete(
            "/api/users/resume",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
