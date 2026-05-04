from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.services.supabase import get_supabase
from app.models.job import JobCreate, JobUpdate, JobResponse, JobListResponse, JobSearchParams
from app.models.common import MessageResponse
from app.dependencies import get_current_user, require_employer

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("", response_model=JobListResponse)
async def search_jobs(
    keyword: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    experience_min: Optional[int] = Query(None),
    experience_max: Optional[int] = Query(None),
    salary_min: Optional[float] = Query(None),
    salary_max: Optional[float] = Query(None),
    category: Optional[str] = Query(None),
    is_remote: Optional[bool] = Query(None),
    ordering: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Search jobs with full filter support."""
    supabase = get_supabase()

    query = supabase.table("jobs").select(
        "*, companies(id, name, logo_url, location, industry)", count="exact"
    ).eq("status", "active")

    if keyword:
        company_result = supabase.table("companies").select("id").ilike("name", f"%{keyword}%").execute()
        company_ids = [c["id"] for c in (company_result.data or [])]
        or_parts = f"title.ilike.%{keyword}%,description.ilike.%{keyword}%,category.ilike.%{keyword}%"
        if company_ids:
            ids_str = ",".join(company_ids)
            or_parts += f",company_id.in.({ids_str})"
        query = query.or_(or_parts)
    if location:
        query = query.ilike("location", f"%{location}%")
    if job_type:
        query = query.eq("job_type", job_type)
    if experience_min is not None:
        query = query.gte("experience_min", experience_min)
    if experience_max is not None:
        query = query.lte("experience_max", experience_max)
    if salary_min is not None:
        query = query.gte("salary_min", salary_min)
    if salary_max is not None:
        query = query.lte("salary_max", salary_max)
    if category:
        query = query.ilike("category", f"%{category}%")
    if is_remote is not None:
        query = query.eq("is_remote", is_remote)

    if ordering:
        try:
            days = int(ordering)
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.gte("created_at", cutoff.isoformat())
        except ValueError:
            pass

    offset = (page - 1) * limit
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    total = result.count or 0
    jobs = result.data or []

    # Normalize company data
    for job in jobs:
        if "companies" in job:
            job["company"] = job.pop("companies")

    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return JobListResponse(
        data=jobs,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/featured", response_model=list)
async def get_featured_jobs():
    """Return 6 active jobs ordered by views_count descending."""
    supabase = get_supabase()

    result = (
        supabase.table("jobs")
        .select("*, companies(id, name, logo_url, location, industry)")
        .eq("status", "active")
        .order("views_count", desc=True)
        .limit(6)
        .execute()
    )

    jobs = result.data or []
    for job in jobs:
        if "companies" in job:
            job["company"] = job.pop("companies")

    return jobs


@router.get("/recommended", response_model=list)
async def get_recommended_jobs(current_user: dict = Depends(get_current_user)):
    """Return jobs matching user skills and location (requires auth)."""
    supabase = get_supabase()

    user_skills: list = current_user.get("skills") or []
    user_location: str = current_user.get("location") or ""

    query = supabase.table("jobs").select(
        "*, companies(id, name, logo_url, location, industry)"
    ).eq("status", "active")

    if user_location:
        query = query.ilike("location", f"%{user_location}%")

    result = query.order("created_at", desc=True).limit(20).execute()
    jobs = result.data or []

    # Score jobs by matching skills
    def score_job(job: dict) -> int:
        job_skills = job.get("skills_required") or []
        return len(set(user_skills) & set(job_skills))

    jobs_scored = sorted(jobs, key=score_job, reverse=True)

    for job in jobs_scored:
        if "companies" in job:
            job["company"] = job.pop("companies")

    return jobs_scored[:10]


@router.get("/categories", response_model=list)
async def get_job_categories():
    """Return distinct categories with job counts."""
    supabase = get_supabase()

    result = (
        supabase.table("jobs")
        .select("category")
        .eq("status", "active")
        .execute()
    )

    jobs = result.data or []
    category_counts: dict = {}
    for job in jobs:
        cat = job.get("category")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    categories = [
        {"category": cat, "count": count}
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    return categories


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_detail(job_id: str):
    """Get job detail with company info and increment views_count."""
    supabase = get_supabase()

    result = (
        supabase.table("jobs")
        .select("*, companies(id, name, logo_url, location, industry, description, website, founded_year, size)")
        .eq("id", job_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job = result.data

    # Increment views_count
    current_views = job.get("views_count", 0) or 0
    supabase.table("jobs").update({"views_count": current_views + 1}).eq("id", job_id).execute()
    job["views_count"] = current_views + 1

    if "companies" in job:
        job["company"] = job.pop("companies")

    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(require_employer),
):
    """Create a new job posting (employer only)."""
    supabase = get_supabase()

    # Verify company belongs to employer if provided
    if job_data.company_id:
        company_check = (
            supabase.table("companies")
            .select("id")
            .eq("id", job_data.company_id)
            .eq("owner_id", current_user["id"])
            .single()
            .execute()
        )
        if not company_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't own this company",
            )

    insert_data = {
        **job_data.model_dump(exclude_none=True),
        "posted_by": current_user["id"],
        "status": "active",
        "views_count": 0,
        "applications_count": 0,
    }
    if "job_type" in insert_data and hasattr(insert_data["job_type"], "value"):
        insert_data["job_type"] = insert_data["job_type"].value

    try:
        result = supabase.table("jobs").insert(insert_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job",
        )

    return result.data[0]


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    current_user: dict = Depends(require_employer),
):
    """Update a job posting (employer only, must own job)."""
    supabase = get_supabase()

    # Verify ownership
    existing = (
        supabase.table("jobs")
        .select("id, posted_by")
        .eq("id", job_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if existing.data["posted_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this job",
        )

    update_data = job_data.model_dump(exclude_none=True)
    if "job_type" in update_data and hasattr(update_data["job_type"], "value"):
        update_data["job_type"] = update_data["job_type"].value
    if "status" in update_data and hasattr(update_data["status"], "value"):
        update_data["status"] = update_data["status"].value

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No update fields provided",
        )

    result = supabase.table("jobs").update(update_data).eq("id", job_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job",
        )

    return result.data[0]


@router.delete("/{job_id}", response_model=MessageResponse)
async def delete_job(
    job_id: str,
    current_user: dict = Depends(require_employer),
):
    """Delete a job posting (employer only, must own job)."""
    supabase = get_supabase()

    existing = (
        supabase.table("jobs")
        .select("id, posted_by")
        .eq("id", job_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if existing.data["posted_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this job",
        )

    supabase.table("jobs").delete().eq("id", job_id).execute()

    return MessageResponse(message="Job deleted successfully", success=True)
