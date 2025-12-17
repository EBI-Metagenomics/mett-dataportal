/**
 * Utility to set JWT token from environment variable or URL parameter
 * 
 * This can be called in your App.tsx or main.tsx to automatically
 * set the token from environment variables or URL parameters.
 * 
 * Usage:
 *   - Set VITE_JWT_TOKEN environment variable
 *   - Or pass ?token=<your-token> in the URL
 */

import { TokenStorage } from './tokenStorage';

export const setTokenFromEnv = (): string | null => {
  // Check environment variable first
  const tokenFromEnv = import.meta.env.VITE_JWT_TOKEN;
  if (tokenFromEnv) {
    TokenStorage.setToken(tokenFromEnv);
    return tokenFromEnv;
  }

  // Check URL parameter
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    if (tokenFromUrl) {
      TokenStorage.setToken(tokenFromUrl);
      
      // Optionally clean up URL to remove token (for security)
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete('token');
      window.history.replaceState({}, '', newUrl.toString());
      
      return tokenFromUrl;
    }
  }

  return null;
};

