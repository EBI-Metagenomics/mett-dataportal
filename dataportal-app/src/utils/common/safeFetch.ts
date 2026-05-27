const SAFE_PATH_SEGMENT = /^[a-zA-Z0-9._-]+$/;

/**
 * Validates path segments used in API URLs (isolates, job IDs, ref names, etc.).
 */
export function assertSafePathSegment(segment: string, label: string): string {
  if (!SAFE_PATH_SEGMENT.test(segment)) {
    throw new Error(
      `Invalid ${label}: must contain only alphanumeric characters, dots, underscores, or hyphens`
    );
  }
  return segment;
}
