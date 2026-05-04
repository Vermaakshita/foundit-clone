from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings
from app.services.supabase import get_supabase
from app.models.user import UserRegister, UserLogin, UserResponse
from app.models.common import TokenResponse, MessageResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def create_access_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user and create their profile."""
    supabase = get_supabase()

    # Check if user already exists
    existing = supabase.table("profiles").select("id").eq("email", user_data.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user in Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user(
            {
                "email": user_data.email,
                "password": user_data.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": user_data.full_name,
                    "role": user_data.role.value,
                },
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user account: {str(e)}",
        )

    if not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user account",
        )

    user_id = auth_response.user.id

    # Upsert profile row (upsert handles the case where a DB trigger already created it)
    try:
        profile_data = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "phone": user_data.phone,
            "role": user_data.role.value,
        }
        supabase.table("profiles").upsert(profile_data, on_conflict="id").execute()
    except Exception as e:
        # Profile creation failed — auth user exists but profile is missing.
        # Don't block registration; the token is still valid and the profile
        # can be completed later. Log the error for debugging.
        print(f"[WARN] Profile upsert failed for {user_id}: {e}")

    token = create_access_token(user_id, user_data.email, user_data.role.value)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user={
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role.value,
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Authenticate user and return JWT token."""
    supabase = get_supabase()

    # Verify credentials via Supabase Auth
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": credentials.email, "password": credentials.password}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = auth_response.user.id
    auth_user = auth_response.user

    # Fetch profile — create a minimal one if it doesn't exist yet
    profile_result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    if not profile_result.data:
        meta = auth_user.user_metadata or {}
        fallback_profile = {
            "id": user_id,
            "email": credentials.email,
            "full_name": meta.get("full_name", ""),
            "role": meta.get("role", "seeker"),
        }
        try:
            supabase.table("profiles").upsert(fallback_profile, on_conflict="id").execute()
        except Exception:
            pass
        profile = fallback_profile
    else:
        profile = profile_result.data

    role = profile.get("role", "seeker")

    token = create_access_token(user_id, credentials.email, role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user={
            "id": user_id,
            "email": credentials.email,
            "full_name": profile.get("full_name"),
            "role": role,
            "avatar_url": profile.get("profile_photo_url"),
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        phone=current_user.get("phone"),
        role=current_user.get("role"),
        avatar_url=current_user.get("profile_photo_url"),
        created_at=str(current_user.get("created_at", "")),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout the current user (JWT is stateless; client should discard the token)."""
    return MessageResponse(message="Successfully logged out", success=True)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: dict):
    """Send a password reset email via Supabase Auth."""
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email is required",
        )

    supabase = get_supabase()

    # Check if user exists (don't reveal if it doesn't for security)
    try:
        supabase.auth.reset_password_email(
            email,
            options={"redirect_to": f"{settings.frontend_url}/reset-password"},
        )
    except Exception:
        # Silently fail to prevent email enumeration attacks
        pass

    return MessageResponse(
        message="If an account with this email exists, a password reset link has been sent",
        success=True,
    )

