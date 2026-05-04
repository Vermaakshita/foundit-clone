from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None


class ReviewCreate(BaseModel):
    rating: float
    title: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    review_text: Optional[str] = None
    is_anonymous: bool = False


class CompanyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    owner_id: Optional[str] = None
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = 0
    reviews: Optional[List[dict]] = []
    active_jobs_count: Optional[int] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}
