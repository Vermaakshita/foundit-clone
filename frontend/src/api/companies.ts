import apiClient from './client';
import type { Company, Job, PaginatedResponse } from '../types';

const BASE = '/api/companies';

// ─── Payload Types ────────────────────────────────────────────────────────────

export interface CreateCompanyData {
  name: string;
  website?: string;
  industry?: string;
  company_size?: string;
  founded_year?: number;
  headquarters?: string;
  description?: string;
  linkedin_url?: string;
  twitter_url?: string;
}

export interface UpdateCompanyData extends Partial<CreateCompanyData> {}

export interface CompanySearchParams {
  q?: string;
  industry?: string;
  company_size?: string;
  is_verified?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}

// ─── Read Operations ──────────────────────────────────────────────────────────

/**
 * Fetches a paginated list of all companies.
 */
export async function getCompanies(
  params: CompanySearchParams = {},
): Promise<PaginatedResponse<Company>> {
  const { data } = await apiClient.get<PaginatedResponse<Company>>(
    BASE + '/',
    { params },
  );
  return data;
}

/**
 * Fetches a single company by ID or slug.
 */
export async function getCompanyById(id: string): Promise<Company> {
  const { data } = await apiClient.get<Company>(`${BASE}/${id}/`);
  return data;
}

/**
 * Fetches all active job listings for a specific company.
 */
export async function getCompanyJobs(
  companyId: string,
  params: { page?: number; page_size?: number; is_active?: boolean } = {},
): Promise<PaginatedResponse<Job>> {
  const { data } = await apiClient.get<PaginatedResponse<Job>>(
    `${BASE}/${companyId}/jobs/`,
    { params },
  );
  return data;
}

/**
 * Fetches the company profile owned by the currently authenticated employer.
 */
export async function getMyCompany(): Promise<Company> {
  const { data } = await apiClient.get<Company>(`${BASE}/me/`);
  return data;
}

/**
 * Fetches featured/top companies for the home page.
 */
export async function getFeaturedCompanies(limit: number = 12): Promise<Company[]> {
  const { data } = await apiClient.get<PaginatedResponse<Company>>(
    BASE + '/',
    { params: { is_verified: true, page_size: limit, ordering: '-job_count' } },
  );
  return data.results;
}

// ─── Write Operations ─────────────────────────────────────────────────────────

/**
 * Creates a new company profile (Employer only).
 * An employer can only own one company.
 */
export async function createCompany(companyData: CreateCompanyData): Promise<Company> {
  const { data } = await apiClient.post<Company>(BASE + '/', companyData);
  return data;
}

/**
 * Updates an existing company's details (Owner / Admin).
 */
export async function updateCompany(
  id: string,
  companyData: UpdateCompanyData,
): Promise<Company> {
  const { data } = await apiClient.patch<Company>(
    `${BASE}/${id}/`,
    companyData,
  );
  return data;
}

/**
 * Uploads a company logo image.
 */
export async function uploadCompanyLogo(
  companyId: string,
  file: File,
): Promise<{ logo_url: string }> {
  const formData = new FormData();
  formData.append('logo', file);

  const { data } = await apiClient.post<{ logo_url: string }>(
    `${BASE}/${companyId}/logo/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

/**
 * Deletes a company profile (Admin only).
 */
export async function deleteCompany(id: string): Promise<void> {
  await apiClient.delete(`${BASE}/${id}/`);
}
