from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from app.services.supabase import get_supabase
from app.models.user import ProfileUpdate, ProfileResponse, SkillsUpdate, EducationRecord, ExperienceRecord
from app.models.common import MessageResponse
from app.dependencies import get_current_user
import uuid
import mimetypes

router = APIRouter(prefix="/api/users", tags=["Users"])

ALLOWED_RESUME_TYPES = {"application/pdf", "application/msword",
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user full profile including skills, education, experience."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Fetch profile
    profile_result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    if not profile_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    profile = profile_result.data

    # Fetch education records
    education_result = (
        supabase.table("education")
        .select("*")
        .eq("user_id", user_id)
        .order("start_year", desc=True)
        .execute()
    )
    profile["education"] = education_result.data or []

    # Fetch experience records
    experience_result = (
        supabase.table("work_experience")
        .select("*")
        .eq("user_id", user_id)
        .order("start_date", desc=True)
        .execute()
    )
    profile["experience"] = experience_result.data or []

    # Fetch skills from user_skills table
    skills_result = (
        supabase.table("user_skills")
        .select("skill_name")
        .eq("user_id", user_id)
        .execute()
    )
    profile["skills"] = [s["skill_name"] for s in (skills_result.data or [])]

    return profile


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update user profile fields."""
    supabase = get_supabase()
    user_id = current_user["id"]

    update_data = profile_data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided to update",
        )

    result = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )

    profile = result.data[0]

    # Fetch related data
    education_result = supabase.table("education").select("*").eq("user_id", user_id).execute()
    profile["education"] = education_result.data or []

    experience_result = supabase.table("work_experience").select("*").eq("user_id", user_id).execute()
    profile["experience"] = experience_result.data or []

    return profile


@router.post("/resume/upload", response_model=MessageResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF resume to Supabase Storage bucket 'resumes'."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Validate file type
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]
    if content_type not in ALLOWED_RESUME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and Word documents are allowed",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_RESUME_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Resume file size must not exceed 5 MB",
        )

    # Generate unique file path
    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "pdf"
    file_path = f"{user_id}/{uuid.uuid4()}.{extension}"

    try:
        supabase.storage.from_("resumes").upload(
            file_path,
            contents,
            {"content-type": content_type, "upsert": "true"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {str(e)}",
        )

    # Get public URL
    public_url = supabase.storage.from_("resumes").get_public_url(file_path)

    # Update profile with resume URL
    supabase.table("profiles").update({"resume_url": public_url}).eq("id", user_id).execute()

    return MessageResponse(
        message="Resume uploaded successfully",
        success=True,
        data={"resume_url": public_url},
    )


@router.delete("/resume", response_model=MessageResponse)
async def delete_resume(current_user: dict = Depends(get_current_user)):
    """Remove resume URL from user profile."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Get current resume URL to delete from storage
    profile_result = (
        supabase.table("profiles").select("resume_url").eq("id", user_id).single().execute()
    )
    if profile_result.data and profile_result.data.get("resume_url"):
        resume_url: str = profile_result.data["resume_url"]
        # Extract file path from URL
        try:
            bucket_marker = "/object/public/resumes/"
            if bucket_marker in resume_url:
                file_path = resume_url.split(bucket_marker)[-1]
                supabase.storage.from_("resumes").remove([file_path])
        except Exception:
            pass  # Continue even if storage deletion fails

    supabase.table("profiles").update({"resume_url": None}).eq("id", user_id).execute()

    return MessageResponse(message="Resume removed successfully", success=True)


@router.put("/skills", response_model=MessageResponse)
async def update_skills(
    skills_data: SkillsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Replace user skills in the user_skills table."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Delete existing skills then insert new ones
    supabase.table("user_skills").delete().eq("user_id", user_id).execute()

    if skills_data.skills:
        insert_rows = [{"user_id": user_id, "skill_name": s} for s in skills_data.skills]
        try:
            supabase.table("user_skills").insert(insert_rows).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update skills: {str(e)}",
            )

    return MessageResponse(
        message="Skills updated successfully",
        success=True,
        data={"skills": skills_data.skills},
    )


@router.put("/education", response_model=MessageResponse)
async def upsert_education(
    education_records: list[EducationRecord],
    current_user: dict = Depends(get_current_user),
):
    """Upsert education records — replaces all education for the user."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Delete existing records
    supabase.table("education").delete().eq("user_id", user_id).execute()

    if education_records:
        insert_data = []
        for rec in education_records:
            row = {k: v for k, v in rec.model_dump(exclude={"id"}).items() if v is not None and v != ""}
            row["user_id"] = user_id
            insert_data.append(row)

        try:
            supabase.table("education").insert(insert_data).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save education records: {str(e)}",
            )

    return MessageResponse(
        message="Education records updated successfully",
        success=True,
    )


@router.put("/experience", response_model=MessageResponse)
async def upsert_experience(
    experience_records: list[ExperienceRecord],
    current_user: dict = Depends(get_current_user),
):
    """Upsert work experience records — replaces all experience for the user."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Delete existing records
    supabase.table("work_experience").delete().eq("user_id", user_id).execute()

    if experience_records:
        insert_data = []
        for rec in experience_records:
            row = {k: v for k, v in rec.model_dump(exclude={"id"}).items() if v is not None and v != ""}
            row["user_id"] = user_id
            insert_data.append(row)

        try:
            supabase.table("work_experience").insert(insert_data).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save experience records: {str(e)}",
            )

    return MessageResponse(
        message="Work experience records updated successfully",
        success=True,
    )
