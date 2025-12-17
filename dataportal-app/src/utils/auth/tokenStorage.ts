/**
 * Token storage utility for managing JWT tokens in localStorage
 */

const TOKEN_STORAGE_KEY = 'dataportal_jwt_token';

export class TokenStorage {
  /**
   * Store JWT token in localStorage
   */
  static setToken(token: string): void {
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } catch (error) {
      console.error('Failed to store token in localStorage:', error);
      throw new Error('Failed to store authentication token');
    }
  }

  /**
   * Retrieve JWT token from localStorage
   */
  static getToken(): string | null {
    try {
      return localStorage.getItem(TOKEN_STORAGE_KEY);
    } catch (error) {
      console.error('Failed to retrieve token from localStorage:', error);
      return null;
    }
  }

  /**
   * Remove JWT token from localStorage
   */
  static removeToken(): void {
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    } catch (error) {
      console.error('Failed to remove token from localStorage:', error);
    }
  }

  /**
   * Check if token exists
   */
  static hasToken(): boolean {
    return this.getToken() !== null;
  }

  /**
   * Clear all authentication data
   */
  static clear(): void {
    this.removeToken();
  }
}

