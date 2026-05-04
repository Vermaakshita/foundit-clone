from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.services.supabase import get_supabase
from app.models.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
from app.models.common import MessageResponse
from app.dependencies import require_seeker, require_employer

router = APIRouter(prefix="/api", tags=["Applications"])


@router.post("/applications/{job_id}", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    job_id: str,
    application_data: ApplicationCreate,
    current_user: dict = Depends(require_seeker),
):
    """Apply for a job (seeker only). Checks that user hasn't already applied."""
    supabase = get_supabase()
    applicant_id = current_user["id"]

    # Verify job exists and is active
    job_result = (
        supabase.table("jobs")
        .select("id, status, posted_by, company_id, title")
        .eq("id", job_id)
        .single()
        .execute()
    )
    if not job_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job = job_result.data
    if job["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job is no longer accepting applications",
        )

    # Check if already applied
    existing_application = (
        supabase.table("applications")
        .select("id")
        .eq("job_id", job_id)
        .eq("applicant_id", applicant_id)
        .execute()
    )
    if existing_application.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied for this job",
        )

    # Use profile resume if not provided
    resume_url = application_data.resume_url
    if not resume_url:
        profile_result = (
            supabase.table("profiles").select("resume_url").eq("id", applicant_id).single().execute()
        )
        if profile_result.data:
            resume_url = profile_result.data.get("resume_url")

    insert_data = {
        "job_id": job_id,
        "applicant_id": applicant_id,
        "status": "applied",
        "cover_letter": application_data.cover_letter,
        "resume_url": resume_url,
    }

    try:
        result = supabase.table("applications").insert(insert_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application",
        )

    application = result.data[0]
    application["job"] = job
    return application


@router.get("/applications/my")
async def get_my_applications(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(require_seeker),
):
    """List seeker's applications with job and company info."""
    supabase = get_supabase()
    applicant_id = current_user["id"]

    offset = (page - 1) * limit
    result = (
        supabase.table("applications")
        .select("*, jobs(id, title, location, job_type, salary_min, salary_max, company_id, companies(id, name, logo_url))")
        .eq("applicant_id", applicant_id)
        .order("applied_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    applications = result.data or []
    for app in applications:
        job_data = app.pop("jobs", None)
        if job_data:
            company_data = job_data.pop("companies", None)
            job_data["company"] = company_data
            app["job"] = job_data
        else:
            app["job"] = None

    return {
        "count": len(applications),
        "results": applications,
        "total_pages": 1,
        "current_page": page,
        "next": None,
        "previous": None,
    }


@router.get("/jobs/{job_id}/applicants", response_model=list)
async def get_job_applicants(
    job_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_employer),
):
    """List all applicants for a job (employer only, must own job)."""
    supabase = get_supabase()

    # Verify job ownership
    job_result = (
        supabase.table("jobs")
        .select("id, posted_by, title")
        .eq("id", job_id)
        .single()
        .execute()
    )
    if not job_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job_result.data["posted_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view applicants for this job",
        )

    offset = (page - 1) * limit
    result = (
        supabase.table("applications")
        .select("*, profiles(id, full_name, email, phone, profile_photo_url, headline, resume_url, location, experience_years)")
        .eq("job_id", job_id)
        .order("applied_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    applications = result.data or []
    for app in applications:
        applicant_data = app.pop("profiles", None)
        app["applicant"] = applicant_data

    return applications


@router.put("/applications/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    status_update: ApplicationStatusUpdate,
    current_user: dict = Depends(require_employer),
):
    """Update application status (employer only)."""
    supabase = get_supabase()

    # Verify the application belongs to a job owned by this employer
    app_result = (
        supabase.table("applications")
        .select("id, applicant_id, job_id, jobs(posted_by)")
        .eq("id", application_id)
        .single()
        .execute()
    )
    if not app_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    job_info = app_result.data.get("jobs") or {}
    if job_info.get("posted_by") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this application",
        )

    update_data = {"status": status_update.status.value}
    if status_update.employer_notes:
        update_data["employer_notes"] = status_update.employer_notes

    result = (
        supabase.table("applications")
        .update(update_data)
        .eq("id", application_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application status",
        )

    return result.data[0]


@router.delete("/applications/{application_id}", response_model=MessageResponse)
async def withdraw_application(
    application_id: str,
    current_user: dict = Depends(require_seeker),
):
    """Withdraw (delete) an application (seeker only)."""
    supabase = get_supabase()
    applicant_id = current_user["id"]

    app_result = (
        supabase.table("applications")
        .select("id, applicant_id, job_id, status")
        .eq("id", application_id)
        .single()
        .execute()
    )
    if not app_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if app_result.data["applicant_id"] != applicant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to withdraw this application",
        )

    if app_result.data["status"] in ("offered", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot withdraw an application that has been decided",
        )

    supabase.table("applications").delete().eq("id", application_id).execute()

    return MessageResponse(message="Application withdrawn successfully", success=True)
