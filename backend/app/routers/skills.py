from fastapi import APIRouter, Query
from typing import Optional
from app.services.supabase import get_supabase

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("", response_model=list)
async def get_skills(q: Optional[str] = Query(None, description="Search query for skill autocomplete")):
    """
    Return all skills for autocomplete.
    Optionally filter by search query using ?q=python.
    """
    supabase = get_supabase()

    query = supabase.table("skills").select("id, name, category").order("name")

    if q:
        query = query.ilike("name", f"%{q}%")

    result = query.limit(50).execute()
    return result.data or []
