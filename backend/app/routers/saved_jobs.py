from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.services.supabase import get_supabase
from app.models.common import MessageResponse
from app.dependencies import require_seeker

router = APIRouter(prefix="/api/saved-jobs", tags=["Saved Jobs"])


@router.post("/{job_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def save_job(
    job_id: str,
    current_user: dict = Depends(require_seeker),
):
    """Save a job for later (seeker only). Idempotent — safe to call multiple times."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Verify job exists
    job_check = supabase.table("jobs").select("id").eq("id", job_id).single().execute()
    if not job_check.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check if already saved, then insert (avoids needing a unique constraint)
    existing = (
        supabase.table("saved_jobs")
        .select("id")
        .eq("user_id", user_id)
        .eq("job_id", job_id)
        .execute()
    )
    if not existing.data:
        try:
            supabase.table("saved_jobs").insert({"user_id": user_id, "job_id": job_id}).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save job: {str(e)}",
            )

    return MessageResponse(message="Job saved successfully", success=True)


@router.get("", response_model=list)
async def list_saved_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(require_seeker),
):
    """List all saved jobs for the current seeker with full job and company data."""
    supabase = get_supabase()
    user_id = current_user["id"]

    offset = (page - 1) * limit
    result = (
        supabase.table("saved_jobs")
        .select(
            "id, saved_at, jobs(id, title, location, job_type, salary_min, salary_max, "
            "experience_min, experience_max, category, status, is_remote, created_at, "
            "companies(id, name, logo_url, industry, location))"
        )
        .eq("user_id", user_id)
        .order("saved_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    saved = result.data or []
    response = []
    for item in saved:
        job_data = item.pop("jobs", None)
        if job_data:
            company_data = job_data.pop("companies", None)
            job_data["company"] = company_data
        response.append({
            "id": item.get("id"),
            "saved_at": item.get("saved_at"),
            "job": job_data,
        })

    return response


@router.delete("/{job_id}", response_model=MessageResponse)
async def unsave_job(
    job_id: str,
    current_user: dict = Depends(require_seeker),
):
    """Remove a job from saved jobs (seeker only)."""
    supabase = get_supabase()
    user_id = current_user["id"]

    existing = (
        supabase.table("saved_jobs")
        .select("id")
        .eq("user_id", user_id)
        .eq("job_id", job_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found",
        )

    supabase.table("saved_jobs").delete().eq("user_id", user_id).eq("job_id", job_id).execute()

    return MessageResponse(message="Job removed from saved list", success=True)
