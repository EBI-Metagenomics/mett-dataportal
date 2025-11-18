import { 
  ApiResponse, 
  SuccessApiResponse, 
  PaginatedApiResponse, 
  ErrorApiResponse, 
  ErrorCode 
} from '../../interfaces/ApiResponse';

/**
 * Utility class to handle standardized API responses
 */
export class ApiResponseHandler {
  /**
   * Extract data from a success response
   */
  static extractData<T>(response: ApiResponse<T>): T {
    if (this.isSuccessResponse(response)) {
      return response.data;
    }
    throw new Error('Response is not a success response');
  }

  /**
   * Extract data from a paginated response
   */
  static extractPaginatedData<T>(response: ApiResponse<T[]>): T[] {
    if (this.isPaginatedResponse(response)) {
      return response.data;
    }
    throw new Error('Response is not a paginated response');
  }

  /**
   * Extract pagination metadata from a paginated response
   */
  static extractPagination<T>(response: ApiResponse<T[]>): PaginatedApiResponse<T>['pagination'] {
    if (this.isPaginatedResponse(response)) {
      return response.pagination;
    }
    throw new Error('Response is not a paginated response');
  }

  /**
   * Check if response is a success response
   */
  static isSuccessResponse<T>(response: ApiResponse<T>): response is SuccessApiResponse<T> {
    return response.status === 'success' && 'data' in response && !('pagination' in response);
  }

  /**
   * Check if response is a paginated response
   */
  static isPaginatedResponse<T>(response: ApiResponse<T[]>): response is PaginatedApiResponse<T> {
    return response.status === 'success' && 'data' in response && 'pagination' in response;
  }

  /**
   * Check if response is an error response
   */
  static isErrorResponse<T>(response: ApiResponse<T>): response is ErrorApiResponse {
    return response.status === 'error';
  }

  /**
   * Get user-friendly error message from error response
   */
  static getErrorMessage(response: ErrorApiResponse): string {
    const errorMessages: Record<string, string> = {
      [ErrorCode.GENE_NOT_FOUND]: 'Gene not found',
      [ErrorCode.GENOME_NOT_FOUND]: 'Genome not found',
      [ErrorCode.SPECIES_NOT_FOUND]: 'Species not found',
      [ErrorCode.VALIDATION_ERROR]: 'Invalid input parameters',
      [ErrorCode.INVALID_GENOME_ID]: 'Invalid genome ID format',
      [ErrorCode.INVALID_LOCUS_TAG]: 'Invalid locus tag format',
      [ErrorCode.INVALID_SPECIES_ACRONYM]: 'Invalid species acronym',
      [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Too many requests. Please try again later',
      [ErrorCode.ELASTICSEARCH_ERROR]: 'Search service temporarily unavailable',
      [ErrorCode.DATABASE_ERROR]: 'Database service temporarily unavailable',
      [ErrorCode.SERVICE_UNAVAILABLE]: 'Service temporarily unavailable',
      [ErrorCode.UNAUTHORIZED]: 'Authentication required',
      [ErrorCode.FORBIDDEN]: 'Access forbidden',
      [ErrorCode.INTERNAL_SERVER_ERROR]: 'An unexpected error occurred'
    };

    return errorMessages[response.error_code] || response.message || 'An error occurred';
  }

  /**
   * Handle API response and return data or throw error.
   * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
   */
  static handleResponse<T>(response: ApiResponse<T>): T {
    // Validate response structure
    if (!response || typeof response !== 'object' || !('status' in response)) {
      throw new Error(
        'Invalid API response: missing status field. ' +
        'All endpoints now return standardized format with status field.'
      );
    }
    
    // Handle error responses
    if (this.isErrorResponse(response)) {
      const errorMessage = this.getErrorMessage(response);
      const error = new Error(errorMessage);
      (error as any).errorCode = response.error_code;
      (error as any).requestId = response.request_id;
      throw error;
    }
    
    // Handle success responses
    return this.extractData(response);
  }

  /**
   * Handle paginated API response and return data or throw error
   */
  static handlePaginatedResponse<T>(response: ApiResponse<T[]>): T[] {
    if (this.isErrorResponse(response)) {
      const errorMessage = this.getErrorMessage(response);
      const error = new Error(errorMessage);
      (error as any).errorCode = response.error_code;
      (error as any).requestId = response.request_id;
      throw error;
    }
    
    return this.extractPaginatedData(response);
  }

  /**
   * @deprecated Legacy compatibility method - no longer needed.
   * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
   * This method is kept for backward compatibility but should not be used in new code.
   * 
   * @throws Error if called, as legacy responses are no longer supported
   */
  static isLegacyResponse(response: any): boolean {
    console.warn(
      'isLegacyResponse() is deprecated. ' +
      'All API endpoints now return standardized format. ' +
      'Legacy response handling has been removed.'
    );
    // Always return false since all endpoints use standardized format
    return false;
  }

  /**
   * @deprecated Legacy compatibility method - no longer needed.
   * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
   * This method is kept for backward compatibility but should not be used in new code.
   */
  static convertLegacyResponse<T>(response: any): SuccessApiResponse<T> {
    console.warn(
      'convertLegacyResponse() is deprecated. ' +
      'All API endpoints now return standardized format. ' +
      'Legacy response conversion is no longer needed.'
    );
    return {
      status: 'success',
      data: response,
      timestamp: new Date().toISOString()
    };
  }
} 