import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { TokenStorage } from '../utils/auth';
import { ApiClient } from '../services/common/apiInstance';

export type AuthContextValue = {
  isAuthenticated: boolean;
  token: string | null;
  setAuthToken: (newToken: string) => void;
  clearAuthToken: () => void;
  checkAuth: () => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Provides a single shared auth state for the app. Required so that when one
 * component (e.g. TokenInput) sets a JWT, all other useAuth() consumers
 * (e.g. NetworkView) re-render with isAuthenticated === true.
 */
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => TokenStorage.hasToken());
  const [token, setToken] = useState<string | null>(() => TokenStorage.getToken());

  const setAuthToken = useCallback((newToken: string) => {
    try {
      TokenStorage.setToken(newToken);
      setToken(newToken);
      setIsAuthenticated(true);
      ApiClient.resetInstance();
    } catch (error) {
      console.error('Failed to set auth token:', error);
      throw error;
    }
  }, []);

  const clearAuthToken = useCallback(() => {
    TokenStorage.removeToken();
    setToken(null);
    setIsAuthenticated(false);
    ApiClient.resetInstance();
  }, []);

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

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const value = useMemo(
    () => ({
      isAuthenticated,
      token,
      setAuthToken,
      clearAuthToken,
      checkAuth,
    }),
    [isAuthenticated, token, setAuthToken, clearAuthToken, checkAuth]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
