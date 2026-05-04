import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges Tailwind CSS classes without conflicts.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formats a salary range into a human-readable string.
 * e.g. formatSalary(500000, 800000, 'INR') => '₹5L – ₹8L'
 */
export function formatSalary(
  min?: number | null,
  max?: number | null,
  currency: string = 'INR',
): string {
  if (min == null && max == null) return 'Not disclosed';

  const symbol = currencySymbol(currency);

  const fmt = (value: number): string => {
    if (currency === 'INR') {
      if (value >= 10_00_000) {
        return `${symbol}${(value / 10_00_000).toFixed(1).replace(/\.0$/, '')}Cr`;
      }
      if (value >= 1_00_000) {
        return `${symbol}${(value / 1_00_000).toFixed(1).replace(/\.0$/, '')}L`;
      }
      if (value >= 1_000) {
        return `${symbol}${(value / 1_000).toFixed(1).replace(/\.0$/, '')}K`;
      }
      return `${symbol}${value}`;
    }
    // Generic formatting for other currencies
    if (value >= 1_000_000) {
      return `${symbol}${(value / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
    }
    if (value >= 1_000) {
      return `${symbol}${(value / 1_000).toFixed(1).replace(/\.0$/, '')}K`;
    }
    return `${symbol}${value}`;
  };

  if (min != null && max != null) {
    return `${fmt(min)} – ${fmt(max)}`;
  }
  if (min != null) {
    return `From ${fmt(min)}`;
  }
  return `Up to ${fmt(max!)}`;
}

function currencySymbol(currency: string): string {
  const map: Record<string, string> = {
    INR: '₹',
    USD: '$',
    EUR: '€',
    GBP: '£',
    AED: 'AED ',
    SGD: 'S$',
  };
  return map[currency] ?? currency + ' ';
}

/**
 * Formats an ISO date string or Date object into a readable format.
 * e.g. '2024-01-15T10:00:00Z' => 'Jan 15, 2024'
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '—';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Returns a relative time string for recent dates.
 * e.g. 'Posted 3 days ago'
 */
export function formatRelativeDate(date: string | Date | null | undefined): string {
  if (!date) return '—';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '—';

  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);

  if (diffSecs < 60) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  if (diffWeeks < 5) return `${diffWeeks} week${diffWeeks !== 1 ? 's' : ''} ago`;
  if (diffMonths < 12) return `${diffMonths} month${diffMonths !== 1 ? 's' : ''} ago`;
  return formatDate(d);
}

/**
 * Returns a human-readable experience label.
 * e.g. getExperienceLabel(2, 5) => '2–5 years'
 */
export function getExperienceLabel(
  min?: number | null,
  max?: number | null,
): string {
  if (min == null && max == null) return 'Any experience';
  if (min === 0 && max == null) return 'Fresher';
  if (min === 0 && max === 0) return 'Fresher';
  if (min != null && max != null) {
    return `${min}–${max} year${max !== 1 ? 's' : ''}`;
  }
  if (min != null) {
    return `${min}+ year${min !== 1 ? 's' : ''}`;
  }
  return `Up to ${max} year${max !== 1 ? 's' : ''}`;
}

/**
 * Returns initials from a full name.
 * e.g. getInitials('John Doe') => 'JD'
 */
export function getInitials(name: string | null | undefined): string {
  if (!name || name.trim() === '') return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

/**
 * Truncates a string to the given length, appending '...' if needed.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + '...';
}

/**
 * Converts a snake_case or SCREAMING_SNAKE_CASE string to Title Case.
 * e.g. 'FULL_TIME' => 'Full Time'
 */
export function toTitleCase(str: string): string {
  return str
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
