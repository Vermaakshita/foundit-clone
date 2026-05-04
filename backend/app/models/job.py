from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class JobType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"
    freelance = "freelance"
    remote = "remote"


class JobStatus(str, Enum):
    active = "active"
    closed = "closed"
    draft = "draft"
    expired = "expired"


class JobCreate(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    location: str
    job_type: JobType = JobType.full_time
    category: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    skills_required: Optional[List[str]] = []
    education_required: Optional[str] = None
    openings: int = 1
    deadline: Optional[str] = None
    is_remote: bool = False
    company_id: Optional[str] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    category: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    skills_required: Optional[List[str]] = None
    education_required: Optional[str] = None
    openings: Optional[int] = None
    deadline: Optional[str] = None
    is_remote: Optional[bool] = None
    status: Optional[JobStatus] = None


class JobResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    location: str
    job_type: Optional[str] = None
    category: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    skills_required: Optional[List[str]] = []
    education_required: Optional[str] = None
    openings: Optional[int] = None
    deadline: Optional[str] = None
    is_remote: Optional[bool] = False
    status: Optional[str] = None
    views_count: Optional[int] = 0
    applications_count: Optional[int] = 0
    employer_id: Optional[str] = None
    company_id: Optional[str] = None
    company: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    data: List[JobResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class JobSearchParams(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    category: Optional[str] = None
    page: int = 1
    limit: int = 10
