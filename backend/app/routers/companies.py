from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.services.supabase import get_supabase
from app.models.company import CompanyCreate, CompanyUpdate, CompanyResponse, ReviewCreate
from app.models.common import MessageResponse
from app.dependencies import get_current_user, require_employer, require_seeker

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.get("", response_model=list)
async def list_companies(
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List companies with optional search and pagination."""
    supabase = get_supabase()

    query = supabase.table("companies").select("*", count="exact")

    if search:
        query = query.or_(
            f"name.ilike.%{search}%,description.ilike.%{search}%,industry.ilike.%{search}%"
        )
    if industry:
        query = query.ilike("industry", f"%{industry}%")

    offset = (page - 1) * limit
    result = query.order("name").range(offset, offset + limit - 1).execute()

    return result.data or []


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_detail(company_id: str):
    """Get company detail including reviews."""
    supabase = get_supabase()

    result = supabase.table("companies").select("*").eq("id", company_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    company = result.data

    # Fetch reviews
    reviews_result = (
        supabase.table("company_reviews")
        .select("*, profiles(full_name, avatar_url)")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    reviews = reviews_result.data or []

    # Calculate average rating
    if reviews:
        avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)
        company["average_rating"] = round(avg_rating, 1)
    else:
        company["average_rating"] = None

    company["total_reviews"] = len(reviews)
    company["reviews"] = reviews

    # Count active jobs
    jobs_result = (
        supabase.table("jobs")
        .select("id", count="exact")
        .eq("company_id", company_id)
        .eq("status", "active")
        .execute()
    )
    company["active_jobs_count"] = jobs_result.count or 0

    return company


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: dict = Depends(require_employer),
):
    """Create a company profile (employer only)."""
    supabase = get_supabase()

    # Check if employer already has a company
    existing = (
        supabase.table("companies")
        .select("id")
        .eq("owner_id", current_user["id"])
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a company profile. Update it instead.",
        )

    insert_data = {
        **company_data.model_dump(exclude_none=True),
        "owner_id": current_user["id"],
    }

    try:
        result = supabase.table("companies").insert(insert_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company: {str(e)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company",
        )

    company = result.data[0]
    company["reviews"] = []
    company["average_rating"] = None
    company["total_reviews"] = 0
    company["active_jobs_count"] = 0
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    current_user: dict = Depends(require_employer),
):
    """Update company (owner only)."""
    supabase = get_supabase()

    existing = supabase.table("companies").select("id, owner_id").eq("id", company_id).single().execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if existing.data["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this company",
        )

    update_data = company_data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided to update",
        )

    result = supabase.table("companies").update(update_data).eq("id", company_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company",
        )

    company = result.data[0]
    company["reviews"] = []
    company["average_rating"] = None
    company["total_reviews"] = 0
    company["active_jobs_count"] = 0
    return company


@router.get("/{company_id}/jobs", response_model=list)
async def get_company_jobs(
    company_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Get all active jobs for a specific company."""
    supabase = get_supabase()

    # Verify company exists
    company_check = supabase.table("companies").select("id").eq("id", company_id).single().execute()
    if not company_check.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    offset = (page - 1) * limit
    result = (
        supabase.table("jobs")
        .select("*")
        .eq("company_id", company_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return result.data or []


@router.post("/{company_id}/reviews", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_company_review(
    company_id: str,
    review_data: ReviewCreate,
    current_user: dict = Depends(require_seeker),
):
    """Add a review for a company (seeker only)."""
    supabase = get_supabase()

    # Verify company exists
    company_check = supabase.table("companies").select("id").eq("id", company_id).single().execute()
    if not company_check.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Prevent duplicate reviews
    existing_review = (
        supabase.table("company_reviews")
        .select("id")
        .eq("company_id", company_id)
        .eq("reviewer_id", current_user["id"])
        .execute()
    )
    if existing_review.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this company",
        )

    # Validate rating
    if not (1 <= review_data.rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be between 1 and 5",
        )

    insert_data = {
        **review_data.model_dump(),
        "company_id": company_id,
        "reviewer_id": current_user["id"],
    }

    try:
        supabase.table("company_reviews").insert(insert_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review: {str(e)}",
        )

    return MessageResponse(message="Review submitted successfully", success=True)
