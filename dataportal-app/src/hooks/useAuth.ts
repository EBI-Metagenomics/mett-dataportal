import { useState, useEffect, useCallback } from 'react';
import { TokenStorage } from '../utils/auth';
import { ApiClient } from '../services/common/apiInstance';

/**
 * Hook for managing JWT authentication token
 */
export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(TokenStorage.hasToken());
  const [token, setToken] = useState<string | null>(TokenStorage.getToken());

  /**
   * Set the authentication token
   */
  const setAuthToken = useCallback((newToken: string) => {
    try {
      TokenStorage.setToken(newToken);
      setToken(newToken);
      setIsAuthenticated(true);
      // Reset API client instance to ensure new token is used
      ApiClient.resetInstance();
    } catch (error) {
      console.error('Failed to set auth token:', error);
      throw error;
    }
  }, []);

  /**
   * Clear the authentication token
   */
  const clearAuthToken = useCallback(() => {
    TokenStorage.removeToken();
    setToken(null);
    setIsAuthenticated(false);
    // Reset API client instance
    ApiClient.resetInstance();
  }, []);

  /**
   * Check if user is authenticated
   */
  const checkAuth = useCallback(() => {
    const hasToken = TokenStorage.hasToken();
    setIsAuthenticated(hasToken);
    if (hasToken) {
      setToken(TokenStorage.getToken());
    } else {
      setToken(null);
    }
    return hasToken;
  }, []);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return {
    isAuthenticated,
    token,
    setAuthToken,
    clearAuthToken,
    checkAuth,
  };
};

