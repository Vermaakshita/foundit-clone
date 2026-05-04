from fastapi import APIRouter, Depends
from app.services.supabase import get_supabase
from app.dependencies import require_seeker, require_employer

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/seeker")
async def seeker_dashboard(current_user: dict = Depends(require_seeker)):
    """
    Return seeker dashboard stats:
    total_applications, shortlisted, saved_jobs, profile_views, recent_applications[5]
    """
    supabase = get_supabase()
    user_id = current_user["id"]

    # Total applications
    total_apps_result = (
        supabase.table("applications")
        .select("id", count="exact")
        .eq("applicant_id", user_id)
        .execute()
    )
    total_applications = total_apps_result.count or 0

    # Shortlisted count
    shortlisted_result = (
        supabase.table("applications")
        .select("id", count="exact")
        .eq("applicant_id", user_id)
        .eq("status", "shortlisted")
        .execute()
    )
    shortlisted = shortlisted_result.count or 0

    # Saved jobs count
    saved_result = (
        supabase.table("saved_jobs")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    saved_jobs = saved_result.count or 0

    profile_views = 0

    # Recent applications (last 5)
    recent_apps_result = (
        supabase.table("applications")
        .select(
            "id, job_id, status, applied_at, "
            "jobs(id, title, location, job_type, companies(id, name, logo_url))"
        )
        .eq("applicant_id", user_id)
        .order("applied_at", desc=True)
        .limit(5)
        .execute()
    )

    recent_applications = []
    for app in (recent_apps_result.data or []):
        job_data = app.pop("jobs", None)
        if job_data:
            company_data = job_data.pop("companies", None)
            job_data["company"] = company_data
        app["job"] = job_data
        recent_applications.append(app)

    return {
        "total_applications": total_applications,
        "shortlisted_applications": shortlisted,
        "saved_jobs_count": saved_jobs,
        "profile_views": profile_views,
        "recent_applications": recent_applications,
    }


@router.get("/employer")
async def employer_dashboard(current_user: dict = Depends(require_employer)):
    """
    Return employer dashboard stats:
    total_jobs_posted, total_applicants, active_jobs, recent_applicants[5]
    """
    supabase = get_supabase()
    user_id = current_user["id"]

    # Total jobs posted
    total_jobs_result = (
        supabase.table("jobs")
        .select("id", count="exact")
        .eq("posted_by", user_id)
        .execute()
    )
    total_jobs_posted = total_jobs_result.count or 0

    # Active jobs
    active_jobs_result = (
        supabase.table("jobs")
        .select("id", count="exact")
        .eq("posted_by", user_id)
        .eq("status", "active")
        .execute()
    )
    active_jobs = active_jobs_result.count or 0

    # Total applicants: fetch job ids posted by this employer, then count applications
    employer_jobs_result = (
        supabase.table("jobs").select("id").eq("posted_by", user_id).execute()
    )
    job_ids = [j["id"] for j in (employer_jobs_result.data or [])]
    total_applicants = 0
    if job_ids:
        apps_result = (
            supabase.table("applications")
            .select("id", count="exact")
            .in_("job_id", job_ids)
            .execute()
        )
        total_applicants = apps_result.count or 0

    # Recent applicants (last 5)
    recent_applicants_result = (
        supabase.table("applications")
        .select(
            "id, status, applied_at, "
            "jobs(id, title), "
            "profiles(id, full_name, email, profile_photo_url, headline)"
        )
        .in_("job_id", job_ids if job_ids else ["00000000-0000-0000-0000-000000000000"])
        .order("applied_at", desc=True)
        .limit(5)
        .execute()
    )

    recent_applicants = []
    for app in (recent_applicants_result.data or []):
        applicant_data = app.pop("profiles", None)
        job_data = app.pop("jobs", None)
        app["applicant"] = applicant_data
        app["job"] = job_data
        recent_applicants.append(app)

    return {
        "total_jobs_posted": total_jobs_posted,
        "total_applicants": total_applicants,
        "active_jobs": active_jobs,
        "recent_applicants": recent_applicants,
    }
