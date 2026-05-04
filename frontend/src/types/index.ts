// ─── Enums (as const objects — compatible with erasableSyntaxOnly) ────────────

export const JobType = {
  FULL_TIME: 'full-time',
  PART_TIME: 'part-time',
  CONTRACT: 'contract',
  FREELANCE: 'freelance',
  INTERNSHIP: 'internship',
  TEMPORARY: 'temporary',
} as const;
export type JobType = (typeof JobType)[keyof typeof JobType];

export const ApplicationStatus = {
  PENDING: 'PENDING',
  REVIEWING: 'REVIEWING',
  SHORTLISTED: 'SHORTLISTED',
  INTERVIEW_SCHEDULED: 'INTERVIEW_SCHEDULED',
  OFFERED: 'OFFERED',
  HIRED: 'HIRED',
  REJECTED: 'REJECTED',
  WITHDRAWN: 'WITHDRAWN',
} as const;
export type ApplicationStatus = (typeof ApplicationStatus)[keyof typeof ApplicationStatus];

export const UserRole = {
  SEEKER: 'SEEKER',
  EMPLOYER: 'EMPLOYER',
  ADMIN: 'ADMIN',
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

// ─── Core Models ─────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  phone?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  name: string;
  category?: string;
}

export interface Education {
  id: string;
  institution: string;
  degree: string;
  field_of_study: string;
  start_year: number;
  end_year?: number;
  is_current: boolean;
  grade?: string;
  description?: string;
}

export interface Experience {
  id: string;
  company_name: string;
  job_title: string;
  location?: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
  employment_type?: JobType;
}

export interface Profile {
  id: string;
  user_id: string;
  user: User;
  headline?: string;
  summary?: string;
  current_location?: string;
  preferred_locations?: string[];
  total_experience_years?: number;
  current_salary?: number;
  expected_salary?: number;
  salary_currency?: string;
  notice_period_days?: number;
  resume_url?: string;
  resume_filename?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  skills: Skill[];
  educations: Education[];
  experiences: Experience[];
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  founded_year?: number;
  headquarters?: string;
  description?: string;
  linkedin_url?: string;
  twitter_url?: string;
  is_verified: boolean;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  title: string;
  slug: string;
  company_id: string;
  company: Company;
  posted_by_id: string;
  description: string;
  requirements?: string;
  responsibilities?: string;
  job_type: JobType;
  location: string;
  is_remote: boolean;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  experience_min?: number;
  experience_max?: number;
  education_required?: string;
  skills_required: Skill[];
  category?: string;
  tags?: string[];
  application_deadline?: string;
  is_active: boolean;
  is_featured: boolean;
  views_count: number;
  applications_count: number;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  job_id: string;
  job: Job;
  applicant_id: string;
  applicant: User;
  status: ApplicationStatus;
  cover_letter?: string;
  resume_url?: string;
  resume_filename?: string;
  expected_salary?: number;
  availability_date?: string;
  notes?: string;
  reviewed_at?: string;
  applied_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SavedJob {
  id: string;
  user_id: string;
  job_id: string;
  job: Job;
  created_at: string;
}

export interface JobAlert {
  id: string;
  user_id: string;
  name: string;
  keywords?: string;
  location?: string;
  job_type?: JobType;
  salary_min?: number;
  experience_min?: number;
  experience_max?: number;
  category?: string;
  frequency: 'DAILY' | 'WEEKLY' | 'INSTANT';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'APPLICATION_UPDATE' | 'JOB_ALERT' | 'SYSTEM' | 'PROFILE' | 'MESSAGE';
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

// ─── Request / Response Types ─────────────────────────────────────────────────

export interface JobSearchParams {
  q?: string;
  location?: string;
  job_type?: JobType;
  salary_min?: number;
  salary_max?: number;
  experience_min?: number;
  experience_max?: number;
  category?: string;
  company_id?: string;
  skills?: string[];
  is_remote?: boolean;
  is_featured?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
  total_pages: number;
  current_page: number;
}

export interface ApiError {
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
  status_code?: number;
}

// ─── Auth Types ───────────────────────────────────────────────────────────────

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

// ─── Dashboard Types ──────────────────────────────────────────────────────────

export interface SeekerDashboard {
  total_applications: number;
  pending_applications: number;
  shortlisted_applications: number;
  interview_applications: number;
  profile_completion_percentage: number;
  recent_applications: Application[];
  recommended_jobs: Job[];
  saved_jobs_count: number;
}

export interface EmployerDashboard {
  total_jobs_posted: number;
  active_jobs: number;
  total_applications_received: number;
  new_applications_today: number;
  recent_applications: Application[];
  top_performing_jobs: Job[];
  company: Company | null;
}
