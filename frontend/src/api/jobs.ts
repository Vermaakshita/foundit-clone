import apiClient from './client';
import type {
  Job,
  JobSearchParams,
  PaginatedResponse,
} from '../types';

const BASE = '/api/jobs';

// ─── Read Operations ──────────────────────────────────────────────────────────

/**
 * Fetches a paginated list of jobs based on search/filter params.
 */
// Frontend uses 'q' and 'page_size'; backend expects 'keyword' and 'limit'
const PARAM_MAP: Partial<Record<string, string>> = { q: 'keyword', page_size: 'limit' };

export async function getJobs(
  params: JobSearchParams = {},
): Promise<PaginatedResponse<Job>> {
  const cleanParams: Record<string, string | number | boolean> = {};

  (Object.keys(params) as Array<keyof JobSearchParams>).forEach((key) => {
    const value = params[key];
    if (value !== undefined && value !== null && value !== '') {
      const mappedKey = PARAM_MAP[key] ?? key;
      if (Array.isArray(value)) {
        cleanParams[mappedKey] = value.join(',');
      } else {
        cleanParams[mappedKey] = value as string | number | boolean;
      }
    }
  });

  const { data } = await apiClient.get<PaginatedResponse<Job>>(BASE, { params: cleanParams });
  return data;
}

/**
 * Fetches featured jobs for the home page hero/highlights section.
 */
export async function getFeaturedJobs(limit: number = 10): Promise<Job[]> {
  const { data } = await apiClient.get<Job[]>(BASE + '/featured', { params: { limit } });
  return data ?? [];
}

/**
 * Fetches personalized recommended jobs for the logged-in seeker.
 */
export async function getRecommendedJobs(limit: number = 10): Promise<Job[]> {
  const { data } = await apiClient.get<Job[]>(BASE + '/recommended', { params: { limit } });
  return data ?? [];
}

/**
 * Fetches a single job by its ID or slug.
 */
export async function getJobById(id: string): Promise<Job> {
  const { data } = await apiClient.get<Job>(`${BASE}/${id}`);
  return data;
}

/**
 * Fetches all available job categories.
 */
export async function getCategories(): Promise<
  Array<{ id: string; name: string; slug: string; job_count: number }>
> {
  const { data } = await apiClient.get<
    Array<{ id: string; name: string; slug: string; job_count: number }>
  >(BASE + '/categories');
  return data ?? [];
}

/**
 * Fetches similar jobs to a given job ID.
 */
export async function getSimilarJobs(jobId: string, limit: number = 6): Promise<Job[]> {
  const { data } = await apiClient.get<Job[]>(`${BASE}/${jobId}/similar/`, {
    params: { limit },
  });
  return data;
}

// ─── Write Operations (Employer / Admin) ─────────────────────────────────────

export interface CreateJobData {
  title: string;
  company_id: string;
  description: string;
  requirements?: string;
  responsibilities?: string;
  job_type: string;
  location: string;
  is_remote?: boolean;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  experience_min?: number;
  experience_max?: number;
  education_required?: string;
  skills_required?: string[];
  category?: string;
  tags?: string[];
  application_deadline?: string;
  is_active?: boolean;
  is_featured?: boolean;
}

/**
 * Creates a new job listing (Employer only).
 */
export async function createJob(jobData: CreateJobData): Promise<Job> {
  const { data } = await apiClient.post<Job>(BASE + '/', jobData);
  return data;
}

/**
 * Updates an existing job listing (Employer / Admin).
 */
export async function updateJob(
  id: string,
  jobData: Partial<CreateJobData>,
): Promise<Job> {
  const { data } = await apiClient.patch<Job>(`${BASE}/${id}/`, jobData);
  return data;
}

/**
 * Soft-deletes / deactivates a job listing (Employer / Admin).
 */
export async function deleteJob(id: string): Promise<void> {
  await apiClient.delete(`${BASE}/${id}/`);
}

/**
 * Toggles the active status of a job listing.
 */
export async function toggleJobStatus(id: string, isActive: boolean): Promise<Job> {
  const { data } = await apiClient.patch<Job>(`${BASE}/${id}/`, {
    is_active: isActive,
  });
  return data;
}

// ─── Saved Jobs ───────────────────────────────────────────────────────────────

export interface SavedJobItem {
  id: string;
  job: Job;
  saved_at: string;
}

/**
 * Saves a job to the seeker's saved list.
 */
export async function saveJob(jobId: string): Promise<void> {
  await apiClient.post(`/api/saved-jobs/${jobId}`);
}

/**
 * Removes a job from the seeker's saved list.
 */
export async function unsaveJob(jobId: string): Promise<void> {
  await apiClient.delete(`/api/saved-jobs/${jobId}`);
}

/**
 * Fetches all jobs saved by the current seeker.
 */
export async function getSavedJobs(): Promise<SavedJobItem[]> {
  const { data } = await apiClient.get<SavedJobItem[]>('/api/saved-jobs');
  return data ?? [];
}
