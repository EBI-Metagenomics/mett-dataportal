import apiInstance from "./apiInstance";

type ParamsType = Record<string, any>;

export class ApiService {
    /**
     * Handle generic GET requests with type safety.
     */
    static async get<T = any>(endpoint: string, params: ParamsType = {}): Promise<T> {
        try {
            const response = await apiInstance.get(endpoint, {params});
            return response.data as T;
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
     * Handle generic POST requests with type safety.
     */
    static async post<T = any>(endpoint: string, data: ParamsType): Promise<T> {
        try {
            const response = await apiInstance.post(endpoint, data);
            return response.data as T;
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
     * Handle generic PUT requests with type safety.
     */
    static async put<T = any>(endpoint: string, data: ParamsType): Promise<T> {
        try {
            const response = await apiInstance.put(endpoint, data);
            return response.data as T;
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
     * Handle generic DELETE requests with type safety.
     */
    static async delete<T = any>(endpoint: string): Promise<T> {
        try {
            const response = await apiInstance.delete(endpoint);
            return response.data as T;
        } catch (error) {
            if (error instanceof Error) {
                console.error("Error deleting data:", error.message);
            } else {
                console.error("Error deleting data:", error);
            }
            throw error;
        }
    }
}
