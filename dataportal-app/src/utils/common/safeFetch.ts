import { API_BASE_URL } from './constants';

const SAFE_PATH_SEGMENT = /^[a-zA-Z0-9._-]+$/;

function resolveApiBase(): URL {
  return new URL(API_BASE_URL, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
}

/**
 * Ensures a URL targets the configured API origin and path prefix (SSRF guard).
 */
export function assertAllowedApiUrl(url: string): URL {
  const parsed = new URL(url, resolveApiBase().origin);
  const base = resolveApiBase();

  if (parsed.origin !== base.origin) {
    throw new Error(`Blocked request to disallowed origin: ${parsed.origin}`);
  }

  const basePath = base.pathname.replace(/\/$/, '') || '';
  const path = parsed.pathname.replace(/\/$/, '') || '';
  if (basePath && !path.startsWith(basePath)) {
    throw new Error(`Blocked request outside API path prefix: ${parsed.pathname}`);
  }

  return parsed;
}

export function assertSafePathSegment(segment: string, label: string): string {
  if (!SAFE_PATH_SEGMENT.test(segment)) {
    throw new Error(`Invalid ${label}: must contain only alphanumeric characters, dots, underscores, or hyphens`);
  }
  return segment;
}

export async function fetchAllowedApi(url: string, init?: RequestInit): Promise<Response> {
  assertAllowedApiUrl(url);
  return fetch(url, init);
}
