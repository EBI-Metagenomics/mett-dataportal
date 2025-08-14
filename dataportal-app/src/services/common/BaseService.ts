import { ApiService } from './api';
import { ErrorHandler } from '../../utils/api/errorHandler';
import { ApiResponse, SuccessApiResponse, PaginatedApiResponse } from '../../interfaces/ApiResponse';

/**
 * Base service class providing common functionality for all API services
 */
export abstract class BaseService {
  protected static readonly MAX_RETRIES = 3;

  /**
   * Make a GET request with retry logic and error handling
   */
  protected static async getWithRetry<T>(
    endpoint: string, 
    params: Record<string, any> = {}, 
    retries: number = this.MAX_RETRIES
  ): Promise<T> {
    try {
      // console.log('BaseService.getWithRetry called:', { endpoint, params });
      const result = await ApiService.get<T>(endpoint, params);
      // console.log('BaseService.getWithRetry result:', result);
      return result;
    } catch (error) {
      console.error('BaseService.getWithRetry error:', error);
      return this.handleErrorWithRetry(error, () => ApiService.get<T>(endpoint, params), retries);
    }
  }

  /**
   * Make a POST request with retry logic and error handling
   */
  protected static async postWithRetry<T>(
    endpoint: string, 
    data: Record<string, any>, 
    retries: number = this.MAX_RETRIES
  ): Promise<T> {
    try {
      return await ApiService.post<T>(endpoint, data);
    } catch (error) {
      return this.handleErrorWithRetry(error, () => ApiService.post<T>(endpoint, data), retries);
    }
  }

  /**
   * Make a paginated GET request with retry logic and error handling
   */
  protected static async getPaginatedWithRetry<T>(
    endpoint: string, 
    params: Record<string, any> = {}, 
    retries: number = this.MAX_RETRIES
  ): Promise<{
    data: T[];
    pagination: PaginatedApiResponse<T>['pagination'];
    metadata?: Record<string, any>;
  }> {
    try {
      return await ApiService.getPaginated<T>(endpoint, params);
    } catch (error) {
      return this.handleErrorWithRetry(error, () => ApiService.getPaginated<T>(endpoint, params), retries);
    }
  }

  /**
   * Get raw API response for debugging
   */
  protected static async getRawResponse<T>(
    endpoint: string, 
    params: Record<string, any> = {}
  ): Promise<ApiResponse<T>> {
    try {
      return await ApiService.getRaw<T>(endpoint, params);
    } catch (error) {
      ErrorHandler.logError(error, `getRawResponse: ${endpoint}`);
      throw error;
    }
  }

  /**
   * Handle error with retry logic
   */
  private static async handleErrorWithRetry<T>(
    error: any, 
    retryFn: () => Promise<T>, 
    retriesLeft: number
  ): Promise<T> {
    ErrorHandler.logError(error, 'API request');

    // If not retryable or no retries left, throw the error
    if (!ErrorHandler.isRetryableError(error) || retriesLeft <= 0) {
      const message = ErrorHandler.getErrorMessage(error);
      throw ErrorHandler.createError(message, error.errorCode, error.requestId);
    }

    // Calculate delay before retry
    const attempt = this.MAX_RETRIES - retriesLeft + 1;
    const delay = ErrorHandler.getRetryDelay(error, attempt);

    console.warn(`Retrying request in ${delay}ms (attempt ${attempt}/${this.MAX_RETRIES})`);

    // Wait before retrying
    await new Promise(resolve => setTimeout(resolve, delay));

    // Retry the request
    try {
      return await retryFn();
    } catch (retryError) {
      return this.handleErrorWithRetry(retryError, retryFn, retriesLeft - 1);
    }
  }

  /**
   * Build query parameters from an object
   */
  protected static buildParams(params: Record<string, any>): URLSearchParams {
    const searchParams = new URLSearchParams();
    
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          // Handle arrays by joining with commas
          searchParams.append(key, value.join(','));
        } else {
          searchParams.append(key, String(value));
        }
      }
    }
    
    return searchParams;
  }

  /**
   * Build query parameters for filters
   */
  protected static buildFilterParams(
    filters: Record<string, any>,
    operators?: Record<string, 'AND' | 'OR'>
  ): URLSearchParams {
    const params = new URLSearchParams();
    
    // Add filters
    if (filters) {
      const filterParts: string[] = [];
      
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            filterParts.push(`${key}:${value.join(",")}`);
          } else {
            filterParts.push(`${key}:${value}`);
          }
        }
      }
      
      if (filterParts.length > 0) {
        params.append("filter", filterParts.join(";"));
      }
    }
    
    // Add operators
    if (operators) {
      const operatorParts: string[] = [];
      
      for (const [key, value] of Object.entries(operators)) {
        if (value) {
          operatorParts.push(`${key}:${value}`);
        }
      }
      
      if (operatorParts.length > 0) {
        params.append("filter_operators", operatorParts.join(";"));
      }
    }
    
    return params;
  }

  /**
   * Create download URL for file downloads
   */
  protected static createDownloadUrl(
    endpoint: string, 
    params: Record<string, any>
  ): string {
    const searchParams = this.buildParams(params);
    const queryString = searchParams.toString();
    return `${endpoint}${queryString ? '?' + queryString : ''}`;
  }

  /**
   * Trigger file download
   */
  protected static triggerDownload(url: string, filename: string): void {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
} 