import { ErrorCode } from '../../interfaces/ApiResponse';

/**
 * Generic error handling utility for API errors
 */
export class ErrorHandler {
  /**
   * Get user-friendly error message from error object
   */
  static getErrorMessage(error: any): string {
    if (!error) {
      return 'An unexpected error occurred';
    }

    // Check if it's an API error with error code
    if (error.errorCode) {
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

      return errorMessages[error.errorCode] || error.message || 'An error occurred';
    }

    // Check if it's a network error
    if (error.name === 'NetworkError' || error.message?.includes('Network Error')) {
      return 'Network connection error. Please check your internet connection.';
    }

    // Check if it's a timeout error
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return 'Request timed out. Please try again.';
    }

    // Check if it's an HTTP error
    if (error.response) {
      const status = error.response.status;
      const statusMessages: Record<number, string> = {
        400: 'Bad request. Please check your input parameters.',
        401: 'Authentication required. Please log in again.',
        403: 'Access forbidden. You don\'t have permission to access this resource.',
        404: 'Resource not found.',
        429: 'Too many requests. Please try again later.',
        500: 'Server error. Please try again later.',
        502: 'Bad gateway. Service temporarily unavailable.',
        503: 'Service unavailable. Please try again later.',
        504: 'Gateway timeout. Please try again later.'
      };

      return statusMessages[status] || `HTTP error ${status}. Please try again.`;
    }

    // Default error message
    return error.message || 'An unexpected error occurred';
  }

  /**
   * Check if error is retryable
   */
  static isRetryableError(error: any): boolean {
    if (!error) return false;

    // Network errors are retryable
    if (error.name === 'NetworkError' || error.message?.includes('Network Error')) {
      return true;
    }

    // Timeout errors are retryable
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return true;
    }

    // Server errors (5xx) are retryable
    if (error.response?.status >= 500 && error.response?.status < 600) {
      return true;
    }

    // Rate limit errors are retryable after delay
    if (error.response?.status === 429) {
      return true;
    }

    // Specific error codes that are retryable
    const retryableErrorCodes = [
      ErrorCode.SERVICE_UNAVAILABLE,
      ErrorCode.ELASTICSEARCH_ERROR,
      ErrorCode.DATABASE_ERROR,
      ErrorCode.EXTERNAL_SERVICE_ERROR
    ];

    if (error.errorCode && retryableErrorCodes.includes(error.errorCode)) {
      return true;
    }

    return false;
  }

  /**
   * Get retry delay in milliseconds
   */
  static getRetryDelay(error: any, attempt: number): number {
    // Base delay of 1 second, exponential backoff
    const baseDelay = 1000;
    const maxDelay = 30000; // 30 seconds max
    
    if (error.response?.status === 429) {
      // Rate limit - use Retry-After header if available
      const retryAfter = error.response.headers['retry-after'];
      if (retryAfter) {
        return parseInt(retryAfter) * 1000;
      }
      // Default rate limit delay
      return Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
    }

    // Exponential backoff for other retryable errors
    return Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  }

  /**
   * Log error for debugging
   */
  static logError(error: any, context?: string): void {
    const errorInfo = {
      message: error.message,
      errorCode: error.errorCode,
      requestId: error.requestId,
      status: error.response?.status,
      url: error.config?.url,
      method: error.config?.method,
      context
    };

    console.error('API Error:', errorInfo);
    
    // In development, log full error details
    if (import.meta.env?.MODE === 'development') {
      console.error('Full error:', error);
    }
  }

  /**
   * Create a standardized error object
   */
  static createError(message: string, errorCode?: string, requestId?: string): Error {
    const error = new Error(message);
    (error as any).errorCode = errorCode;
    (error as any).requestId = requestId;
    return error;
  }
} 