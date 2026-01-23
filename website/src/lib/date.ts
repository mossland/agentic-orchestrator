/**
 * Date utility functions for MOSS.AO
 *
 * Backend stores all times in UTC without timezone suffix.
 * These utilities ensure proper conversion to user's local timezone.
 */

/**
 * Parse a UTC datetime string from the backend.
 * Backend returns ISO format without timezone (e.g., "2024-01-20T15:30:00")
 * This function treats such strings as UTC.
 */
export function parseUTCDate(dateString: string | null | undefined): Date | null {
  if (!dateString) return null;

  // If already has timezone info, parse directly
  if (dateString.endsWith('Z') || dateString.includes('+') || dateString.includes('-', 10)) {
    return new Date(dateString);
  }

  // Assume UTC for naive datetime strings from backend
  return new Date(dateString + 'Z');
}

/**
 * Format a UTC date string to local date and time.
 * e.g., "2024년 1월 20일 오후 11:30" (Korean) or "Jan 20, 2024, 11:30 PM" (English)
 */
export function formatLocalDateTime(
  dateString: string | null | undefined,
  locale: string = 'ko-KR'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  return date.toLocaleString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a UTC date string to local date only.
 * e.g., "2024년 1월 20일" (Korean) or "Jan 20, 2024" (English)
 */
export function formatLocalDate(
  dateString: string | null | undefined,
  locale: string = 'ko-KR'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a UTC date string to local time only.
 * e.g., "오후 11:30" (Korean) or "11:30 PM" (English)
 */
export function formatLocalTime(
  dateString: string | null | undefined,
  locale: string = 'ko-KR'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  return date.toLocaleTimeString(locale, {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a UTC date string to relative time.
 * e.g., "5분 전", "2시간 전", "3일 전"
 */
export function formatRelativeTime(
  dateString: string | null | undefined,
  locale: string = 'ko-KR'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Use Intl.RelativeTimeFormat for localized relative time
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  if (diffDays > 0) {
    return rtf.format(-diffDays, 'day');
  } else if (diffHours > 0) {
    return rtf.format(-diffHours, 'hour');
  } else if (diffMins > 0) {
    return rtf.format(-diffMins, 'minute');
  } else {
    return rtf.format(-diffSecs, 'second');
  }
}

/**
 * Format a UTC date string with both date and relative time.
 * e.g., "2024년 1월 20일 (2시간 전)"
 */
export function formatDateWithRelative(
  dateString: string | null | undefined,
  locale: string = 'ko-KR'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  const dateStr = formatLocalDate(dateString, locale);
  const relativeStr = formatRelativeTime(dateString, locale);

  return `${dateStr} (${relativeStr})`;
}
