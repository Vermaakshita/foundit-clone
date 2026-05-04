from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.services.supabase import get_supabase
from app.models.common import MessageResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/job-alerts", tags=["Job Alerts"])


class JobAlertCreate(BaseModel):
    name: str
    keyword: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    category: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    frequency: str = "daily"  # daily, weekly, instant
    is_active: bool = True


class JobAlertUpdate(BaseModel):
    name: Optional[str] = None
    keyword: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    category: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    frequency: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_job_alert(
    alert_data: JobAlertCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new job alert for the current user."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Validate frequency value
    valid_frequencies = {"daily", "weekly", "instant"}
    if alert_data.frequency not in valid_frequencies:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Frequency must be one of: {', '.join(valid_frequencies)}",
        )

    insert_data = {
        **alert_data.model_dump(exclude_none=True),
        "user_id": user_id,
    }

    try:
        result = supabase.table("job_alerts").insert(insert_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job alert: {str(e)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job alert",
        )

    return result.data[0]


@router.get("", response_model=list)
async def list_job_alerts(current_user: dict = Depends(get_current_user)):
    """List all job alerts for the current user."""
    supabase = get_supabase()
    user_id = current_user["id"]

    result = (
        supabase.table("job_alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []


@router.put("/{alert_id}", response_model=dict)
async def update_job_alert(
    alert_id: str,
    alert_data: JobAlertUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing job alert (owner only)."""
    supabase = get_supabase()
    user_id = current_user["id"]

    existing = (
        supabase.table("job_alerts")
        .select("id, user_id")
        .eq("id", alert_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job alert not found")

    if existing.data["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this alert",
        )

    update_data = alert_data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided to update",
        )

    if "frequency" in update_data:
        valid_frequencies = {"daily", "weekly", "instant"}
        if update_data["frequency"] not in valid_frequencies:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Frequency must be one of: {', '.join(valid_frequencies)}",
            )

    result = supabase.table("job_alerts").update(update_data).eq("id", alert_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job alert",
        )

    return result.data[0]


@router.delete("/{alert_id}", response_model=MessageResponse)
async def delete_job_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a job alert (owner only)."""
    supabase = get_supabase()
    user_id = current_user["id"]

    existing = (
        supabase.table("job_alerts")
        .select("id, user_id")
        .eq("id", alert_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job alert not found")

    if existing.data["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this alert",
        )

    supabase.table("job_alerts").delete().eq("id", alert_id).execute()

    return MessageResponse(message="Job alert deleted successfully", success=True)
