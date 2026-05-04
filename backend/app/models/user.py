from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    seeker = "seeker"
    employer = "employer"


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.seeker

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    experience_years: Optional[int] = None
    profile_photo_url: Optional[str] = None


class EducationRecord(BaseModel):
    id: Optional[str] = None
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: int
    end_year: Optional[int] = None
    is_current: bool = False
    grade: Optional[str] = None


class ExperienceRecord(BaseModel):
    id: Optional[str] = None
    company_name: str
    title: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    profile_photo_url: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    experience_years: Optional[int] = None
    resume_url: Optional[str] = None
    profile_completion_pct: Optional[int] = None
    skills: Optional[List[str]] = []
    education: Optional[List[dict]] = []
    experience: Optional[List[dict]] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class SkillsUpdate(BaseModel):
    skills: List[str]
