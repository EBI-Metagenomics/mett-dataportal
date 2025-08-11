import axios, { AxiosInstance } from "axios";
import { API_BASE_URL } from "../utils/constants";

export class ApiClient {
    private static instance: AxiosInstance | null = null;

    /**
     * Get the Axios instance (singleton).
     */
    public static getInstance(): AxiosInstance {
        if (!this.instance) {
            this.instance = axios.create({
                baseURL: API_BASE_URL,
                headers: {
                    "Content-Type": "application/json",
                },
                timeout: 10000,
            });

            // Add request interceptor
            this.instance.interceptors.request.use(
                (config) => config,
                (error) => Promise.reject(error)
            );

            // Add response interceptor
            this.instance.interceptors.response.use(
                (response) => response,
                (error) => {
                    console.error("API response error:", error);
                    return Promise.reject(error);
                }
            );
        }
        return this.instance;
    }
}

// Export a single instance for use
export default ApiClient.getInstance();
