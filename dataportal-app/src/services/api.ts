import apiInstance from "./apiInstance";
import { ApiResponse, SuccessApiResponse, PaginatedApiResponse } from "../interfaces/ApiResponse";
import { ApiResponseHandler } from "../utils/apiResponseHandler";

type ParamsType = Record<string, any>;

export class ApiService {
    /**
     * Handle generic GET requests with type safety and standardized response handling.
     */
    static async get<T = any>(endpoint: string, params: ParamsType = {}): Promise<T> {
        try {
            // console.log('ApiService.get called:', { endpoint, params });
            const response = await apiInstance.get(endpoint, {params});
            const responseData = response.data;
            // console.log('ApiService.get raw response:', responseData);
            
            // Handle new standardized response format
            if (ApiResponseHandler.isLegacyResponse(responseData)) {
                // Legacy response - return data directly
                return responseData as T;
            }
            
            // New standardized response format
            const apiResponse = responseData as ApiResponse<T>;
            
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                // For paginated responses, return the data array
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            } else if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                // For success responses, return the data
                return ApiResponseHandler.extractData(apiResponse);
            } else {
                // Error response - throw error
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error fetching data:", error.message);
            } else {
                console.error("Error fetching data:", error);
            }
            throw error;
        }
    }

    /**
     * Handle generic POST requests with type safety and standardized response handling.
     */
    static async post<T = any>(endpoint: string, data: ParamsType): Promise<T> {
        try {
            const response = await apiInstance.post(endpoint, data);
            const responseData = response.data;
            
            // Handle new standardized response format
            if (ApiResponseHandler.isLegacyResponse(responseData)) {
                // Legacy response - return data directly
                return responseData as T;
            }
            
            // New standardized response format
            const apiResponse = responseData as ApiResponse<T>;
            
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                // For paginated responses, return the data array
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            } else if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                // For success responses, return the data
                return ApiResponseHandler.extractData(apiResponse);
            } else {
                // Error response - throw error
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error posting data:", error.message);
            } else {
                console.error("Error posting data:", error);
            }
            throw error;
        }
    }

    /**
     * Handle generic PUT requests with type safety and standardized response handling.
     */
    static async put<T = any>(endpoint: string, data: ParamsType): Promise<T> {
        try {
            const response = await apiInstance.put(endpoint, data);
            const responseData = response.data;
            
            // Handle new standardized response format
            if (ApiResponseHandler.isLegacyResponse(responseData)) {
                // Legacy response - return data directly
                return responseData as T;
            }
            
            // New standardized response format
            const apiResponse = responseData as ApiResponse<T>;
            
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                // For paginated responses, return the data array
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            } else if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                // For success responses, return the data
                return ApiResponseHandler.extractData(apiResponse);
            } else {
                // Error response - throw error
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error putting data:", error.message);
            } else {
                console.error("Error putting data:", error);
            }
            throw error;
        }
    }

    /**
     * Handle generic DELETE requests with type safety and standardized response handling.
     */
    static async delete<T = any>(endpoint: string): Promise<T> {
        try {
            const response = await apiInstance.delete(endpoint);
            const responseData = response.data;
            
            // Handle new standardized response format
            if (ApiResponseHandler.isLegacyResponse(responseData)) {
                // Legacy response - return data directly
                return responseData as T;
            }
            
            // New standardized response format
            const apiResponse = responseData as ApiResponse<T>;
            
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                // For paginated responses, return the data array
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            } else if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                // For success responses, return the data
                return ApiResponseHandler.extractData(apiResponse);
            } else {
                // Error response - throw error
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error deleting data:", error.message);
            } else {
                console.error("Error deleting data:", error);
            }
            throw error;
        }
    }

    /**
     * Get raw API response without processing (useful for debugging)
     */
    static async getRaw<T = any>(endpoint: string, params: ParamsType = {}): Promise<ApiResponse<T>> {
        try {
            const response = await apiInstance.get(endpoint, {params});
            return response.data as ApiResponse<T>;
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error fetching raw data:", error.message);
            } else {
                console.error("Error fetching raw data:", error);
            }
            throw error;
        }
    }

    /**
     * Get paginated response with pagination metadata
     */
    static async getPaginated<T = any>(endpoint: string, params: ParamsType = {}): Promise<{
        data: T[];
        pagination: PaginatedApiResponse<T>['pagination'];
        metadata?: Record<string, any>;
    }> {
        try {
            const response = await apiInstance.get(endpoint, {params});
            const responseData = response.data;
            
            // Handle new standardized response format
            if (ApiResponseHandler.isLegacyResponse(responseData)) {
                // Legacy response - return with default pagination
                return {
                    data: responseData as T[],
                    pagination: {
                        page_number: 1,
                        num_pages: 1,
                        has_previous: false,
                        has_next: false,
                        total_results: (responseData as T[]).length,
                        per_page: (responseData as T[]).length
                    }
                };
            }
            
            // New standardized response format
            const apiResponse = responseData as ApiResponse<T[]>;
            
            if (ApiResponseHandler.isPaginatedResponse(apiResponse)) {
                return {
                    data: ApiResponseHandler.extractPaginatedData(apiResponse),
                    pagination: ApiResponseHandler.extractPagination(apiResponse),
                    metadata: apiResponse.metadata
                };
            } else if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                // Single success response - wrap in pagination format
                const data = ApiResponseHandler.extractData(apiResponse);
                return {
                    data: Array.isArray(data) ? data : [data],
                    pagination: {
                        page_number: 1,
                        num_pages: 1,
                        has_previous: false,
                        has_next: false,
                        total_results: Array.isArray(data) ? data.length : 1,
                        per_page: Array.isArray(data) ? data.length : 1
                    },
                    metadata: apiResponse.metadata
                };
            } else {
                // Error response - throw error
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error fetching paginated data:", error.message);
            } else {
                console.error("Error fetching paginated data:", error);
            }
            throw error;
        }
    }
}
