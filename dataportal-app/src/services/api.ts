import apiInstance from "./apiInstance";

type ParamsType = Record<string, any>;

export class ApiService {
    /**
     * Handle generic GET requests.
     */
    static async get(endpoint: string, params: ParamsType = {}): Promise<any> {
        try {
            const response = await apiInstance.get(endpoint, {params});
            return response.data;
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
     * Handle generic POST requests.
     */
    static async post(endpoint: string, data: ParamsType): Promise<any> {
        try {
            const response = await apiInstance.post(endpoint, data);
            return response.data;
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
     * Handle generic PUT requests.
     */
    static async put(endpoint: string, data: ParamsType): Promise<any> {
        try {
            const response = await apiInstance.put(endpoint, data);
            return response.data;
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
     * Handle generic DELETE requests.
     */
    static async delete(endpoint: string): Promise<any> {
        try {
            const response = await apiInstance.delete(endpoint);
            return response.data;
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
