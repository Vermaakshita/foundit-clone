import apiClient from './client';
import type { JobAlert, JobType } from '../types';

const BASE = '/api/job-alerts';

export interface CreateJobAlertData {
  name: string;
  keywords?: string;
  location?: string;
  job_type?: JobType;
  salary_min?: number;
  salary_max?: number;
  experience_min?: number;
  experience_max?: number;
  category?: string;
  frequency: 'DAILY' | 'WEEKLY' | 'INSTANT';
}

/**
 * Creates a new job alert for the currently authenticated seeker.
 */
export async function createJobAlert(data: CreateJobAlertData): Promise<JobAlert> {
  const { data: alert } = await apiClient.post<JobAlert>(BASE + '/', data);
  return alert;
}

/**
 * Fetches all job alerts belonging to the current seeker.
 */
export async function getJobAlerts(): Promise<JobAlert[]> {
  const { data } = await apiClient.get<JobAlert[]>(BASE + '/');
  return data;
}

/**
 * Updates an existing job alert.
 */
export async function updateJobAlert(
  alertId: string,
  data: Partial<CreateJobAlertData>,
): Promise<JobAlert> {
  const { data: alert } = await apiClient.patch<JobAlert>(`${BASE}/${alertId}/`, data);
  return alert;
}

/**
 * Deletes a job alert.
 */
export async function deleteJobAlert(alertId: string): Promise<void> {
  await apiClient.delete(`${BASE}/${alertId}/`);
}

/**
 * Toggles the active state of a job alert.
 */
export async function toggleJobAlert(alertId: string, isActive: boolean): Promise<JobAlert> {
  const { data: alert } = await apiClient.patch<JobAlert>(`${BASE}/${alertId}/`, {
    is_active: isActive,
  });
  return alert;
}
