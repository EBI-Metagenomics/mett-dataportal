const MAX_PATH_SEGMENT_LENGTH = 256;

function isSafePathChar(char: string): boolean {
  if (char.length !== 1) {
    return false;
  }
  const code = char.charCodeAt(0);
  if (code >= 48 && code <= 57) return true; // 0-9
  if (code >= 65 && code <= 90) return true; // A-Z
  if (code >= 97 && code <= 122) return true; // a-z
  return char === '.' || char === '_' || char === '-';
}

/**
 * Validates path segments used in API URLs (isolates, job IDs, ref names, etc.).
 * Uses character checks instead of regex to avoid ReDoS scanner findings.
 */
export function assertSafePathSegment(segment: string, label: string): string {
  if (!segment || segment.length > MAX_PATH_SEGMENT_LENGTH) {
    throw new Error(`Invalid ${label}: must be non-empty and at most ${MAX_PATH_SEGMENT_LENGTH} characters`);
  }

  for (const char of segment) {
    if (!isSafePathChar(char)) {
      throw new Error(
        `Invalid ${label}: must contain only alphanumeric characters, dots, underscores, or hyphens`
      );
    }
  }

  return segment;
}
