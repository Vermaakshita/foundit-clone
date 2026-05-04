"""
test_auth.py — Tests for /api/auth/ routes.

Behaviours covered
------------------
Register
  [R1] Happy path seeker registration → 201, returns token + user dict
  [R2] Happy path employer registration → 201, role=employer in response
  [R3] Duplicate email → 409 Conflict
  [R4] Password too short (< 8 chars) → 422 Validation error
  [R5] Missing required fields → 422
  [R6] Invalid email format → 422
  [R7] Empty full_name → 422

Login
  [L1] Valid credentials → 200, returns token
  [L2] Wrong password → 401 Unauthorised
  [L3] Missing email → 422

Get /me
  [M1] Valid token → 200 with profile data
  [M2] No token → 401 (FastAPI HTTPBearer raises 403 for missing auth)
  [M3] Expired token → 401

Logout
  [O1] Valid token → 200 success message

Forgot-password
  [F1] Existing email → 200 (neutral message)
  [F2] Missing email payload → 422
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import (
    SEEKER_PROFILE,
    EMPLOYER_PROFILE,
    SEEKER_ID,
    _chain,
    make_supabase_mock,
    make_token,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _auth_user(user_id: str, email: str, role: str = "seeker"):
    """Build a mock auth.User object returned by Supabase Auth calls."""
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.user_metadata = {"full_name": "Test User", "role": role}
    return user


# ────────────────────────────────────────────────────────────────────────────
# REGISTER
# ────────────────────────────────────────────────────────────────────────────

class TestRegister:

    @pytest.mark.asyncio
    async def test_register_seeker_returns_201_with_token(self, client):
        """[R1] Seeker registration happy path."""
        sb = client._mock_sb
        new_id = str(uuid.uuid4())
        auth_user = _auth_user(new_id, "new@example.com", "seeker")

        # profiles table: no existing user (empty data)
        profiles_chain = _chain()
        profiles_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.return_value = profiles_chain

        # Auth admin create_user succeeds
        auth_response = MagicMock()
        auth_response.user = auth_user
        sb.auth.admin.create_user.return_value = auth_response

        response = await client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "SecurePass1",
            "full_name": "New User",
            "role": "seeker",
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "seeker"
        assert data["user"]["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_register_employer_returns_employer_role(self, client):
        """[R2] Employer registration returns role=employer."""
        sb = client._mock_sb
        new_id = str(uuid.uuid4())
        auth_user = _auth_user(new_id, "employer_new@example.com", "employer")

        profiles_chain = _chain()
        profiles_chain.execute.return_value = MagicMock(data=[], count=0)
        sb.table.return_value = profiles_chain

        auth_response = MagicMock()
        auth_response.user = auth_user
        sb.auth.admin.create_user.return_value = auth_response

        response = await client.post("/api/auth/register", json={
            "email": "employer_new@example.com",
            "password": "SecurePass1",
            "full_name": "New Employer",
            "role": "employer",
        })

        assert response.status_code == 201
        assert response.json()["user"]["role"] == "employer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client):
        """[R3] Registering with an existing email returns 409."""
        sb = client._mock_sb

        # Simulate existing profile found
        profiles_chain = _chain()
        profiles_chain.execute.return_value = MagicMock(data=[{"id": SEEKER_ID}], count=1)
        sb.table.return_value = profiles_chain

        response = await client.post("/api/auth/register", json={
            "email": "existing@example.com",
            "password": "SecurePass1",
            "full_name": "Existing User",
        })

        assert response.status_code == 409
        assert "already exists" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_register_short_password_returns_422(self, client):
        """[R4] Password shorter than 8 chars → 422."""
        response = await client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "short",
            "full_name": "User",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_email_returns_422(self, client):
        """[R5] Missing email field → 422."""
        response = await client.post("/api/auth/register", json={
            "password": "SecurePass1",
            "full_name": "User",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email_format_returns_422(self, client):
        """[R6] Non-email string → 422."""
        response = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "SecurePass1",
            "full_name": "User",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_empty_full_name_returns_422(self, client):
        """[R7] Whitespace-only full_name → 422."""
        response = await client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "SecurePass1",
            "full_name": "   ",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_full_name_returns_422(self, client):
        """[R5b] Missing full_name → 422."""
        response = await client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "SecurePass1",
        })
        assert response.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# LOGIN
# ────────────────────────────────────────────────────────────────────────────

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_valid_credentials_returns_200_with_token(self, client):
        """[L1] Valid credentials → 200 with access_token."""
        sb = client._mock_sb
        auth_user = _auth_user(SEEKER_ID, "seeker@example.com", "seeker")

        # sign_in_with_password returns a session-like object
        sign_in_resp = MagicMock()
        sign_in_resp.user = auth_user
        sb.auth.sign_in_with_password.return_value = sign_in_resp

        # Profile fetch returns SEEKER_PROFILE
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post("/api/auth/login", json={
            "email": "seeker@example.com",
            "password": "SecurePass1",
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "seeker"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client):
        """[L2] Wrong credentials → 401."""
        sb = client._mock_sb
        sb.auth.sign_in_with_password.side_effect = Exception("Invalid login")

        response = await client.post("/api/auth/login", json={
            "email": "seeker@example.com",
            "password": "WrongPass!",
        })

        assert response.status_code == 401
        assert "invalid" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_login_missing_email_returns_422(self, client):
        """[L3] Missing email → 422."""
        response = await client.post("/api/auth/login", json={
            "password": "SecurePass1",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_password_returns_422(self, client):
        """[L3b] Missing password → 422."""
        response = await client.post("/api/auth/login", json={
            "email": "seeker@example.com",
        })
        assert response.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# GET /me
# ────────────────────────────────────────────────────────────────────────────

class TestGetMe:

    @pytest.mark.asyncio
    async def test_get_me_with_valid_token_returns_profile(self, client, seeker_token):
        """[M1] Valid token → 200 with user profile."""
        sb = client._mock_sb

        # Mock profile lookup in dependencies.py get_current_user
        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "seeker@example.com"
        assert data["role"] == "seeker"

    @pytest.mark.asyncio
    async def test_get_me_without_token_returns_403(self, client):
        """[M2] No auth header → 403 (HTTPBearer rejects missing credentials)."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_me_with_expired_token_returns_401(self, client, expired_token):
        """[M3] Expired token → 401."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token_returns_401(self, client):
        """[M3b] Garbage token → 401."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert response.status_code == 401


# ────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ────────────────────────────────────────────────────────────────────────────

class TestLogout:

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_returns_200(self, client, seeker_token):
        """[O1] Valid token → 200 success."""
        sb = client._mock_sb

        profile_chain = _chain()
        profile_chain.execute.return_value = MagicMock(data=SEEKER_PROFILE, count=1)
        sb.table.return_value = profile_chain

        response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True


# ────────────────────────────────────────────────────────────────────────────
# FORGOT PASSWORD
# ────────────────────────────────────────────────────────────────────────────

class TestForgotPassword:

    @pytest.mark.asyncio
    async def test_forgot_password_returns_200_neutral_message(self, client):
        """[F1] Valid email payload → 200 with neutral message."""
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "anyone@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Message must not reveal if email exists (security requirement)
        assert "if an account" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_forgot_password_missing_email_returns_422(self, client):
        """[F2] No email key → 422."""
        response = await client.post(
            "/api/auth/forgot-password",
            json={},
        )
        assert response.status_code == 422
