// Standardized API Response Interfaces

export interface BaseApiResponse {
  status: 'success' | 'error' | 'warning';
  message?: string;
  timestamp: string;
}

export interface SuccessApiResponse<T> extends BaseApiResponse {
  status: 'success';
  data: T;
  metadata?: Record<string, any>;
}

export interface ErrorApiResponse extends BaseApiResponse {
  status: 'error';
  error_code: string;
  message: string;
  details?: Array<{
    field?: string;
    value?: any;
    message: string;
  }>;
  request_id?: string;
}

export interface PaginationMetadata {
  page_number: number;
  num_pages: number;
  has_previous: boolean;
  has_next: boolean;
  total_results: number;
  per_page: number;
}

export interface PaginatedApiResponse<T> extends BaseApiResponse {
  status: 'success';
  data: T[];
  pagination: PaginationMetadata;
  metadata?: Record<string, any>;
}

// Union type for all possible API responses
export type ApiResponse<T> = SuccessApiResponse<T> | PaginatedApiResponse<T> | ErrorApiResponse;

// Error codes enum (matching backend)
export enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  GENE_NOT_FOUND = 'GENE_NOT_FOUND',
  GENOME_NOT_FOUND = 'GENOME_NOT_FOUND',
  SPECIES_NOT_FOUND = 'SPECIES_NOT_FOUND',
  CONTIG_NOT_FOUND = 'CONTIG_NOT_FOUND',
  INVALID_GENOME_ID = 'INVALID_GENOME_ID',
  INVALID_LOCUS_TAG = 'INVALID_LOCUS_TAG',
  INVALID_SPECIES_ACRONYM = 'INVALID_SPECIES_ACRONYM',
  INVALID_PAGINATION_PARAMS = 'INVALID_PAGINATION_PARAMS',
  ELASTICSEARCH_ERROR = 'ELASTICSEARCH_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
  EXTERNAL_SERVICE_ERROR = 'EXTERNAL_SERVICE_ERROR',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  INVALID_API_KEY = 'INVALID_API_KEY'
} 