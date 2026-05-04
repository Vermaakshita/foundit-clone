from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from app.services.supabase import get_supabase

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Decode and verify the JWT token, then fetch the user profile from Supabase.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    supabase = get_supabase()
    try:
        result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        if not result.data:
            raise credentials_exception
        return result.data
    except Exception:
        raise credentials_exception


async def require_seeker(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require the authenticated user to have the 'seeker' role.
    """
    if current_user.get("role") != "seeker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to job seekers only",
        )
    return current_user


async def require_employer(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require the authenticated user to have the 'employer' role.
    """
    if current_user.get("role") != "employer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to employers only",
        )
    return current_user
