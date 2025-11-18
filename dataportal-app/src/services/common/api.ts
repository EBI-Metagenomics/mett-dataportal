import apiInstance from "./apiInstance";
import { ApiResponse, PaginatedApiResponse } from "../../interfaces/ApiResponse";
import { ApiResponseHandler } from "../../utils/api/apiResponseHandler";

type ParamsType = Record<string, any>;

export class ApiService {
    /**
     * Handle generic GET requests with type safety and standardized response handling.
     * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
     */
    static async get<T = any>(endpoint: string, params: ParamsType = {}): Promise<T> {
        try {
            const response = await apiInstance.get(endpoint, {params});
            const responseData = response.data;
            
            // Validate response structure
            if (!responseData || typeof responseData !== 'object' || !('status' in responseData)) {
                throw new Error(
                    `Invalid API response format from ${endpoint}. ` +
                    `Expected standardized response with 'status' field. ` +
                    `Received: ${typeof responseData}`
                );
            }
            
            const apiResponse = responseData as ApiResponse<T>;
            
            // Handle paginated responses
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            }
            
            // Handle success responses
            if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                return ApiResponseHandler.extractData(apiResponse);
            }
            
            // Handle error responses
            if (ApiResponseHandler.isErrorResponse(apiResponse)) {
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
            
            // Unknown response format
            throw new Error(
                `Unexpected response format from ${endpoint}. ` +
                `Expected standardized API response with status 'success' or 'error'. ` +
                `Received status: ${apiResponse.status}`
            );
        } catch (error) {
            if (error instanceof Error) {
                console.error(`Error fetching data from ${endpoint}:`, error.message);
            } else {
                console.error(`Error fetching data from ${endpoint}:`, error);
            }
            throw error;
        }
    }

    /**
     * Handle generic POST requests with type safety and standardized response handling.
     * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
     */
    static async post<T = any>(endpoint: string, data: ParamsType): Promise<T> {
        try {
            const response = await apiInstance.post(endpoint, data);
            const responseData = response.data;
            
            // Validate response structure
            if (!responseData || typeof responseData !== 'object' || !('status' in responseData)) {
                throw new Error(
                    `Invalid API response format from ${endpoint}. ` +
                    `Expected standardized response with 'status' field. ` +
                    `Received: ${typeof responseData}`
                );
            }
            
            const apiResponse = responseData as ApiResponse<T>;
            
            // Handle paginated responses
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            }
            
            // Handle success responses
            if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                return ApiResponseHandler.extractData(apiResponse);
            }
            
            // Handle error responses
            if (ApiResponseHandler.isErrorResponse(apiResponse)) {
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
            
            // Unknown response format
            throw new Error(
                `Unexpected response format from ${endpoint}. ` +
                `Expected standardized API response with status 'success' or 'error'. ` +
                `Received status: ${apiResponse.status}`
            );
        } catch (error) {
            if (error instanceof Error) {
                console.error(`Error posting data to ${endpoint}:`, error.message);
            } else {
                console.error(`Error posting data to ${endpoint}:`, error);
            }
            throw error;
        }
    }

    /**
     * Handle generic PUT requests with type safety and standardized response handling.
     * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
     */
    static async put<T = any>(endpoint: string, data: ParamsType): Promise<T> {
        try {
            const response = await apiInstance.put(endpoint, data);
            const responseData = response.data;
            
            // Validate response structure
            if (!responseData || typeof responseData !== 'object' || !('status' in responseData)) {
                throw new Error(
                    `Invalid API response format from ${endpoint}. ` +
                    `Expected standardized response with 'status' field. ` +
                    `Received: ${typeof responseData}`
                );
            }
            
            const apiResponse = responseData as ApiResponse<T>;
            
            // Handle paginated responses
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            }
            
            // Handle success responses
            if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                return ApiResponseHandler.extractData(apiResponse);
            }
            
            // Handle error responses
            if (ApiResponseHandler.isErrorResponse(apiResponse)) {
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
            
            // Unknown response format
            throw new Error(
                `Unexpected response format from ${endpoint}. ` +
                `Expected standardized API response with status 'success' or 'error'. ` +
                `Received status: ${apiResponse.status}`
            );
        } catch (error) {
            if (error instanceof Error) {
                console.error(`Error putting data to ${endpoint}:`, error.message);
            } else {
                console.error(`Error putting data to ${endpoint}:`, error);
            }
            throw error;
        }
    }

    /**
     * Handle generic DELETE requests with type safety and standardized response handling.
     * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., ... }
     */
    static async delete<T = any>(endpoint: string): Promise<T> {
        try {
            const response = await apiInstance.delete(endpoint);
            const responseData = response.data;
            
            // Validate response structure
            if (!responseData || typeof responseData !== 'object' || !('status' in responseData)) {
                throw new Error(
                    `Invalid API response format from ${endpoint}. ` +
                    `Expected standardized response with 'status' field. ` +
                    `Received: ${typeof responseData}`
                );
            }
            
            const apiResponse = responseData as ApiResponse<T>;
            
            // Handle paginated responses
            if (ApiResponseHandler.isPaginatedResponse(apiResponse as any)) {
                return ApiResponseHandler.extractPaginatedData(apiResponse as any) as T;
            }
            
            // Handle success responses
            if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
                return ApiResponseHandler.extractData(apiResponse);
            }
            
            // Handle error responses
            if (ApiResponseHandler.isErrorResponse(apiResponse)) {
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
            
            // Unknown response format
            throw new Error(
                `Unexpected response format from ${endpoint}. ` +
                `Expected standardized API response with status 'success' or 'error'. ` +
                `Received status: ${apiResponse.status}`
            );
        } catch (error) {
            if (error instanceof Error) {
                console.error(`Error deleting data from ${endpoint}:`, error.message);
            } else {
                console.error(`Error deleting data from ${endpoint}:`, error);
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
     * Get paginated response with pagination metadata.
     * All API endpoints now return standardized format: { status: 'success'|'error', data: ..., pagination: ..., ... }
     */
    static async getPaginated<T = any>(endpoint: string, params: ParamsType = {}): Promise<{
        data: T[];
        pagination: PaginatedApiResponse<T>['pagination'];
        metadata?: Record<string, any>;
    }> {
        try {
            const response = await apiInstance.get(endpoint, {params});
            const responseData = response.data;
            
            // Validate response structure
            if (!responseData || typeof responseData !== 'object' || !('status' in responseData)) {
                throw new Error(
                    `Invalid API response format from ${endpoint}. ` +
                    `Expected standardized response with 'status' field. ` +
                    `Received: ${typeof responseData}`
                );
            }
            
            const apiResponse = responseData as ApiResponse<T[]>;
            
            // Handle paginated responses (preferred)
            if (ApiResponseHandler.isPaginatedResponse(apiResponse)) {
                return {
                    data: ApiResponseHandler.extractPaginatedData(apiResponse),
                    pagination: ApiResponseHandler.extractPagination(apiResponse),
                    metadata: apiResponse.metadata
                };
            }
            
            // Handle success responses (convert to pagination format)
            if (ApiResponseHandler.isSuccessResponse(apiResponse)) {
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
            }
            
            // Handle error responses
            if (ApiResponseHandler.isErrorResponse(apiResponse)) {
                ApiResponseHandler.handleResponse(apiResponse);
                throw new Error('Unexpected response format');
            }
            
            // Unknown response format
            throw new Error(
                `Unexpected response format from ${endpoint}. ` +
                `Expected paginated or success response. ` +
                `Received status: ${apiResponse.status}`
            );
        } catch (error) {
            if (error instanceof Error) {
                console.error(`Error fetching paginated data from ${endpoint}:`, error.message);
            } else {
                console.error(`Error fetching paginated data from ${endpoint}:`, error);
            }
            throw error;
        }
    }
}
