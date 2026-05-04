from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ApplicationStatus(str, Enum):
    applied = "applied"
    under_review = "under_review"
    shortlisted = "shortlisted"
    interview_scheduled = "interview_scheduled"
    offered = "offered"
    rejected = "rejected"
    withdrawn = "withdrawn"


class ApplicationCreate(BaseModel):
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    expected_salary: Optional[float] = None
    notice_period: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    applicant_id: str
    status: str
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    expected_salary: Optional[float] = None
    notice_period: Optional[str] = None
    job: Optional[dict] = None
    company: Optional[dict] = None
    applicant: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    employer_notes: Optional[str] = None
