import apiClient from './client';
import type { SeekerDashboard, EmployerDashboard } from '../types';

const BASE = '/api/dashboard';

/**
 * Fetches the job seeker's personalised dashboard data:
 * - application stats (total, pending, shortlisted, interview)
 * - profile completion percentage
 * - recent applications
 * - recommended jobs
 * - saved jobs count
 */
export async function getSeekerDashboard(): Promise<SeekerDashboard> {
  const { data } = await apiClient.get<SeekerDashboard>(`${BASE}/seeker/`);
  return data;
}

/**
 * Fetches the employer's dashboard data:
 * - posted job stats (total, active)
 * - application stats (total received, new today)
 * - recent applications
 * - top performing jobs
 * - company info
 */
export async function getEmployerDashboard(): Promise<EmployerDashboard> {
  const { data } = await apiClient.get<EmployerDashboard>(`${BASE}/employer/`);
  return data;
}
