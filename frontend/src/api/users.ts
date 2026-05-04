import apiClient from './client';
import type { Profile, Skill } from '../types';

const BASE = '/api/users';

// ─── Payload Types ────────────────────────────────────────────────────────────

export interface UpdateProfileData {
  headline?: string;
  summary?: string;
  current_location?: string;
  total_experience_years?: number;
  linkedin_url?: string;
  github_url?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
}

export interface EducationData {
  institution: string;
  degree: string;
  field_of_study: string;
  start_year: number;
  end_year?: number;
  is_current?: boolean;
  grade?: string;
  description?: string;
}

export interface ExperienceData {
  company_name: string;
  job_title: string;
  location?: string;
  start_date: string;
  end_date?: string;
  is_current?: boolean;
  description?: string;
  employment_type?: string;
}

// Maps backend profile shape (DB column names) → frontend Profile type
function normalizeProfile(raw: any): Profile {
  const fullName: string = raw.full_name ?? '';
  const spaceIdx = fullName.indexOf(' ');
  const first_name = spaceIdx >= 0 ? fullName.slice(0, spaceIdx) : fullName;
  const last_name = spaceIdx >= 0 ? fullName.slice(spaceIdx + 1) : '';

  return {
    id: raw.id,
    user_id: raw.id,
    user: {
      id: raw.id,
      email: raw.email ?? '',
      role: ((raw.role ?? 'seeker').toUpperCase()) as any,
      first_name,
      last_name,
      phone: raw.phone,
      avatar_url: raw.profile_photo_url ?? raw.avatar_url,
      is_active: true,
      is_verified: true,
      created_at: raw.created_at ?? '',
      updated_at: raw.updated_at ?? '',
    },
    headline: raw.headline,
    summary: raw.bio ?? raw.summary,
    current_location: raw.location ?? raw.current_location,
    preferred_locations: raw.preferred_locations,
    total_experience_years: raw.experience_years ?? raw.total_experience_years,
    resume_url: raw.resume_url,
    linkedin_url: raw.linkedin_url,
    github_url: raw.github_url,
    // skills: backend returns string[], convert to Skill[]
    skills: (raw.skills ?? []).map((s: any) =>
      typeof s === 'string' ? { id: s, name: s } : s
    ),
    // education/experience: backend returns these arrays from joined tables
    educations: (raw.education ?? raw.educations ?? []).map((e: any) => ({
      ...e,
      // backend work_experience has 'title', frontend expects 'job_title'
    })),
    experiences: (raw.experience ?? raw.experiences ?? []).map((e: any) => ({
      ...e,
      job_title: e.job_title ?? e.title,
    })),
    created_at: raw.created_at ?? '',
    updated_at: raw.updated_at ?? '',
  };
}

// ─── Profile ──────────────────────────────────────────────────────────────────

export async function getProfile(): Promise<Profile> {
  const { data } = await apiClient.get<any>(`${BASE}/profile`);
  return normalizeProfile(data);
}

export async function updateProfile(profileData: UpdateProfileData): Promise<Profile> {
  // Map frontend field names → backend DB column names
  const payload: Record<string, unknown> = {};

  if (profileData.first_name !== undefined || profileData.last_name !== undefined) {
    payload.full_name = [profileData.first_name ?? '', profileData.last_name ?? '']
      .filter(Boolean).join(' ').trim();
  }
  if (profileData.phone !== undefined) payload.phone = profileData.phone;
  if (profileData.headline !== undefined) payload.headline = profileData.headline;
  if (profileData.summary !== undefined) payload.bio = profileData.summary;
  if (profileData.current_location !== undefined) payload.location = profileData.current_location;
  if (profileData.linkedin_url !== undefined) payload.linkedin_url = profileData.linkedin_url;
  if (profileData.github_url !== undefined) payload.github_url = profileData.github_url;
  if (profileData.total_experience_years !== undefined) payload.experience_years = profileData.total_experience_years;

  const { data } = await apiClient.put<any>(`${BASE}/profile`, payload);
  return normalizeProfile(data);
}

export async function getUserProfile(userId: string): Promise<Profile> {
  const { data } = await apiClient.get<any>(`${BASE}/${userId}/profile`);
  return normalizeProfile(data);
}

// ─── Resume ───────────────────────────────────────────────────────────────────

export async function uploadResume(file: File): Promise<Profile> {
  const formData = new FormData();
  formData.append('resume', file);
  const { data } = await apiClient.post<any>(
    `${BASE}/resume/upload`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function deleteResume(): Promise<void> {
  await apiClient.delete(`${BASE}/resume`);
}

// ─── Skills ───────────────────────────────────────────────────────────────────

export async function updateSkills(
  skills: Array<{ id?: string; name: string }>,
): Promise<Profile> {
  const skillNames = skills.map((s) => s.name);
  const { data } = await apiClient.put<any>(`${BASE}/skills`, { skills: skillNames });
  return data;
}

export async function searchSkills(query: string): Promise<Skill[]> {
  const { data } = await apiClient.get<Skill[]>('/api/skills', {
    params: { q: query, limit: 20 },
  });
  return data ?? [];
}

// ─── Education ────────────────────────────────────────────────────────────────

export async function addEducation(educationData: EducationData): Promise<any> {
  // Backend replaces all education; fetch current, add new, upsert all
  const profile = await getProfile();
  const existing = (profile.educations ?? []).map((e: any) => ({
    institution: e.institution,
    degree: e.degree,
    field_of_study: e.field_of_study,
    start_year: e.start_year,
    end_year: e.end_year,
    is_current: e.is_current,
    grade: e.grade,
  }));
  const { data } = await apiClient.put<any>(`${BASE}/education`, [...existing, educationData]);
  return data;
}

export async function updateEducation(
  educationId: string,
  educationData: Partial<EducationData>,
): Promise<any> {
  const profile = await getProfile();
  const updated = (profile.educations ?? []).map((e: any) =>
    e.id === educationId ? { ...e, ...educationData } : e
  );
  const { data } = await apiClient.put<any>(`${BASE}/education`, updated);
  return data;
}

export async function deleteEducation(educationId: string): Promise<any> {
  const profile = await getProfile();
  const filtered = (profile.educations ?? [])
    .filter((e: any) => e.id !== educationId)
    .map((e: any) => ({
      institution: e.institution, degree: e.degree,
      field_of_study: e.field_of_study, start_year: e.start_year,
      end_year: e.end_year, is_current: e.is_current,
    }));
  const { data } = await apiClient.put<any>(`${BASE}/education`, filtered);
  return data;
}

// ─── Experience ───────────────────────────────────────────────────────────────

export async function addExperience(experienceData: ExperienceData): Promise<any> {
  const profile = await getProfile();
  const existing = (profile.experiences ?? []).map((e: any) => ({
    company_name: e.company_name,
    title: e.job_title ?? e.title,
    location: e.location, start_date: e.start_date,
    end_date: e.end_date, is_current: e.is_current,
    description: e.description,
  }));
  const payload = {
    company_name: experienceData.company_name,
    title: experienceData.job_title,
    location: experienceData.location,
    start_date: experienceData.start_date,
    end_date: experienceData.end_date,
    is_current: experienceData.is_current,
    description: experienceData.description,
  };
  const { data } = await apiClient.put<any>(`${BASE}/experience`, [...existing, payload]);
  return data;
}

export async function updateExperience(
  experienceId: string,
  experienceData: Partial<ExperienceData>,
): Promise<any> {
  const profile = await getProfile();
  const updated = (profile.experiences ?? []).map((e: any) => {
    if (e.id !== experienceId) return { company_name: e.company_name, title: e.job_title ?? e.title, location: e.location, start_date: e.start_date, end_date: e.end_date, is_current: e.is_current, description: e.description };
    return { company_name: experienceData.company_name ?? e.company_name, title: experienceData.job_title ?? e.job_title ?? e.title, location: experienceData.location ?? e.location, start_date: experienceData.start_date ?? e.start_date, end_date: experienceData.end_date ?? e.end_date, is_current: experienceData.is_current ?? e.is_current, description: experienceData.description ?? e.description };
  });
  const { data } = await apiClient.put<any>(`${BASE}/experience`, updated);
  return data;
}

export async function deleteExperience(experienceId: string): Promise<any> {
  const profile = await getProfile();
  const filtered = (profile.experiences ?? [])
    .filter((e: any) => e.id !== experienceId)
    .map((e: any) => ({
      company_name: e.company_name, title: e.job_title ?? e.title,
      location: e.location, start_date: e.start_date,
      end_date: e.end_date, is_current: e.is_current,
      description: e.description,
    }));
  const { data } = await apiClient.put<any>(`${BASE}/experience`, filtered);
  return data;
}

// ─── Avatar ───────────────────────────────────────────────────────────────────

export async function uploadAvatar(file: File): Promise<{ avatar_url: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<any>(
    `${BASE}/avatar`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function deleteAvatar(): Promise<void> {
  await apiClient.delete(`${BASE}/avatar`);
}

// ─── Notifications ────────────────────────────────────────────────────────────

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

export async function getNotifications(
  params: { page?: number; is_read?: boolean } = {},
): Promise<{ results: NotificationItem[]; unread_count: number }> {
  const { data } = await apiClient.get<{
    results: NotificationItem[];
    unread_count: number;
  }>('/api/notifications', { params });
  return data;
}

export async function markNotificationRead(notificationId: string): Promise<void> {
  await apiClient.post(`/api/notifications/${notificationId}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post('/api/notifications/mark-all-read');
}
