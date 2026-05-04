import apiClient from './client';
import type { Application, ApplicationStatus, PaginatedResponse } from '../types';

const BASE = '/api/applications';

// ─── Application Payload Types ────────────────────────────────────────────────

export interface ApplyToJobData {
  cover_letter?: string;
  resume_url?: string;
  expected_salary?: number;
  availability_date?: string;
}

export interface ApplicationStatusUpdate {
  status: ApplicationStatus;
  notes?: string;
}

// ─── Seeker Actions ───────────────────────────────────────────────────────────

/**
 * Submits a job application for the currently authenticated seeker.
 */
export async function applyToJob(
  jobId: string,
  applicationData: ApplyToJobData = {},
): Promise<Application> {
  // Backend route is POST /api/applications/{job_id} (job_id as path param)
  const { data } = await apiClient.post<Application>(`${BASE}/${jobId}`, applicationData);
  return data;
}

/**
 * Fetches all applications submitted by the current seeker.
 */
export async function getMyApplications(
  params: { page?: number; page_size?: number; status?: ApplicationStatus } = {},
): Promise<PaginatedResponse<Application>> {
  const { data } = await apiClient.get<PaginatedResponse<Application>>(
    BASE + '/my',
    { params },
  );
  return data;
}

/**
 * Withdraws (cancels) an application submitted by the current seeker.
 */
export async function withdrawApplication(
  applicationId: string,
): Promise<Application> {
  const { data } = await apiClient.delete<Application>(
    `${BASE}/${applicationId}`,
  );
  return data;
}

/**
 * Fetches the details of a single application.
 */
export async function getApplicationById(
  applicationId: string,
): Promise<Application> {
  const { data } = await apiClient.get<Application>(
    `${BASE}/${applicationId}/`,
  );
  return data;
}

// ─── Employer Actions ─────────────────────────────────────────────────────────

/**
 * Fetches all applicants for a specific job (Employer only).
 */
export async function getJobApplicants(
  jobId: string,
  params: {
    page?: number;
    page_size?: number;
    status?: ApplicationStatus;
    ordering?: string;
  } = {},
): Promise<PaginatedResponse<Application>> {
  const { data } = await apiClient.get<PaginatedResponse<Application>>(
    `/api/jobs/${jobId}/applicants`,
    { params },
  );
  return data;
}

/**
 * Updates the status of a job application (Employer only).
 * e.g. move from REVIEWING → SHORTLISTED, or SHORTLISTED → INTERVIEW_SCHEDULED.
 */
export async function updateApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
  notes?: string,
): Promise<Application> {
  const payload: ApplicationStatusUpdate = { status };
  if (notes !== undefined) payload.notes = notes;

  const { data } = await apiClient.put<Application>(
    `${BASE}/${applicationId}/status`,
    payload,
  );
  return data;
}

/**
 * Adds internal notes to an application (Employer only).
 */
export async function addApplicationNotes(
  applicationId: string,
  notes: string,
): Promise<Application> {
  const { data } = await apiClient.patch<Application>(
    `${BASE}/${applicationId}/`,
    { notes },
  );
  return data;
}

/**
 * Bulk updates the status of multiple applications at once (Employer only).
 */
export async function bulkUpdateApplicationStatus(
  applicationIds: string[],
  status: ApplicationStatus,
): Promise<{ updated_count: number }> {
  const { data } = await apiClient.post<{ updated_count: number }>(
    `${BASE}/bulk-update/`,
    { application_ids: applicationIds, status },
  );
  return data;
}
